"""
Auth Routes - Endpoints de Autenticacion, 2FA, Sesiones
Agente: Backend-API
Rama: feature/backend-api

Este archivo contiene los endpoints relacionados con autenticacion y 2FA.
Endpoints migrados desde app.py.

Endpoints en este modulo:
- /api/2fa/* - Setup, verify, status, disable
- /api/demo/2fa/* - Modo demo 2FA
- /api/validate - Validacion de usuario Telegram
"""

import os
import io
import base64
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, session
import pyotp
import qrcode

from tracking.decorators import (
    require_telegram_auth,
    require_telegram_user,
    require_owner,
    validate_telegram_webapp_data,
    is_owner,
    is_test_user
)
from tracking.utils import rate_limit
from tracking.services import get_db_manager, IS_PRODUCTION
from tracking.demo_sessions import get_demo_session_token, invalidate_demo_session

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/auth/health', methods=['GET'])
def auth_health():
    """Health check del modulo auth."""
    return jsonify({
        'success': True,
        'module': 'auth_routes',
        'status': 'active',
        'endpoints_migrated': [
            '/api/demo/2fa/verify',
            '/api/demo/2fa/logout',
            '/api/2fa/status',
            '/api/2fa/setup',
            '/api/2fa/verify',
            '/api/2fa/session',
            '/api/2fa/refresh',
            '/api/2fa/disable',
            '/api/validate'
        ]
    })


def ensure_user_exists(user_data, db_mgr):
    """Asegura que el usuario exista en la base de datos"""
    user_id = str(user_data.get('id'))
    try:
        db_mgr.get_or_create_user(
            user_id=user_id,
            username=user_data.get('username', 'demo_user'),
            first_name=user_data.get('first_name', 'Demo'),
            last_name=user_data.get('last_name', ''),
            telegram_id=int(user_id) if user_id.isdigit() else 0
        )
        return True
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return False


@auth_bp.route('/demo/2fa/verify', methods=['POST'])
def verify_demo_2fa():
    """Verificar contrasena para modo demo."""
    if IS_PRODUCTION:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        data = request.get_json() or {}
        password = data.get('code', '').strip() or data.get('password', '').strip()
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Contrasena requerida'
            }), 400
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        demo_password = os.environ.get('ADMIN_TOKEN', '110917')
        
        if password == demo_password:
            session_token = get_demo_session_token(client_ip)
            logger.info(f"Demo login successful from IP: {client_ip}")
            return jsonify({
                'success': True,
                'sessionToken': session_token,
                'message': 'Acceso concedido'
            })
        else:
            logger.warning(f"Demo login failed from IP: {client_ip}")
            return jsonify({
                'success': False,
                'error': 'Contrasena incorrecta'
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying demo password: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


@auth_bp.route('/demo/2fa/logout', methods=['POST'])
def demo_2fa_logout():
    """Cerrar sesion del modo demo 2FA."""
    if IS_PRODUCTION:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if session.get('demo_2fa_valid'):
            invalidate_demo_session()
            logger.info(f"Demo 2FA session closed from IP: {client_ip}")
            return jsonify({
                'success': True,
                'message': 'Sesion demo cerrada correctamente'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No hay sesion activa'
            })
            
    except Exception as e:
        logger.error(f"Error closing demo 2FA session: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


@auth_bp.route('/2fa/status', methods=['POST'])
@require_telegram_user
def get_2fa_status():
    """Obtener estado de 2FA del usuario"""
    user_id = str(request.telegram_user.get('id'))
    
    if getattr(request, 'is_demo', False) or user_id == '0':
        return jsonify({
            'success': True,
            'enabled': False,
            'configured': False,
            'sessionValid': True,
            'requiresVerification': False
        })
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    ensure_user_exists(request.telegram_user, db_manager)
    
    status = db_manager.get_user_2fa_status(user_id)
    session_valid = False
    
    if status['enabled']:
        session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    return jsonify({
        'success': True,
        'enabled': status['enabled'],
        'configured': status['has_secret'],
        'sessionValid': session_valid,
        'requiresVerification': status['enabled'] and not session_valid
    })


@auth_bp.route('/2fa/setup', methods=['POST'])
@require_telegram_user
def setup_2fa():
    """Configurar 2FA - genera secreto TOTP y codigo QR"""
    user_id = str(request.telegram_user.get('id'))
    username = request.telegram_user.get('username', 'user')
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    existing_secret = db_manager.get_user_totp_secret(user_id)
    
    if existing_secret:
        secret = existing_secret
    else:
        secret = pyotp.random_base32()
        if not db_manager.setup_2fa(user_id, secret):
            return jsonify({'error': 'Failed to setup 2FA'}), 500
    
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=f"@{username}",
        issuer_name="BUNK3R"
    )
    
    img = qrcode.make(provisioning_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'secret': secret,
        'qrCode': f"data:image/png;base64,{qr_base64}",
        'message': 'Escanea el codigo QR con Google Authenticator'
    })


@auth_bp.route('/2fa/verify', methods=['POST'])
@require_telegram_user
@rate_limit('2fa_verify')
def verify_2fa():
    """Verificar codigo TOTP"""
    user_id = str(request.telegram_user.get('id'))
    data = request.get_json()
    code = data.get('code', '').strip()
    enable_2fa = data.get('enable', False)
    
    if not code or len(code) != 6:
        return jsonify({
            'success': False,
            'error': 'Codigo invalido. Debe ser de 6 digitos.'
        }), 400
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    secret = db_manager.get_user_totp_secret(user_id)
    
    if not secret:
        return jsonify({
            'success': False,
            'error': '2FA no esta configurado. Configure primero.'
        }), 400
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)
    
    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Codigo incorrecto. Intenta de nuevo.'
        }), 401
    
    if enable_2fa:
        db_manager.enable_2fa(user_id)
    else:
        db_manager.update_2fa_verified_time(user_id)
    
    return jsonify({
        'success': True,
        'message': '2FA habilitado correctamente' if enable_2fa else 'Verificacion exitosa',
        'verified': True
    })


@auth_bp.route('/2fa/session', methods=['POST'])
@require_telegram_user
def check_2fa_session():
    """Verificar si la sesion 2FA sigue activa"""
    user_id = str(request.telegram_user.get('id'))
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    status = db_manager.get_user_2fa_status(user_id)
    
    if not status['enabled']:
        return jsonify({
            'success': True,
            'sessionValid': True,
            'requiresVerification': False
        })
    
    session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    return jsonify({
        'success': True,
        'sessionValid': session_valid,
        'requiresVerification': not session_valid
    })


@auth_bp.route('/2fa/refresh', methods=['POST'])
@require_telegram_user
def refresh_2fa_session():
    """Actualizar timestamp de sesion 2FA"""
    user_id = str(request.telegram_user.get('id'))
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    status = db_manager.get_user_2fa_status(user_id)
    
    if not status['enabled']:
        return jsonify({'success': True, 'message': '2FA not enabled'})
    
    session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    if session_valid:
        db_manager.update_2fa_verified_time(user_id)
        return jsonify({'success': True, 'sessionExtended': True})
    
    return jsonify({
        'success': False,
        'sessionExpired': True,
        'requiresVerification': True
    })


@auth_bp.route('/2fa/disable', methods=['POST'])
@require_telegram_user
def disable_2fa():
    """Desactivar 2FA (requiere codigo valido)"""
    user_id = str(request.telegram_user.get('id'))
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code or len(code) != 6:
        return jsonify({
            'success': False,
            'error': 'Se requiere codigo de 6 digitos para desactivar 2FA'
        }), 400
    
    db_manager = get_db_manager()
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    secret = db_manager.get_user_totp_secret(user_id)
    
    if not secret:
        return jsonify({
            'success': False,
            'error': '2FA no esta configurado'
        }), 400
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)
    
    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Codigo incorrecto'
        }), 401
    
    if db_manager.disable_2fa(user_id):
        return jsonify({
            'success': True,
            'message': '2FA desactivado correctamente'
        })
    
    return jsonify({
        'success': False,
        'error': 'Error al desactivar 2FA'
    }), 500


@auth_bp.route('/validate', methods=['POST'])
def validate_user():
    """Valida el usuario de Telegram y verifica permisos."""
    data = request.get_json()
    init_data = data.get('initData', '')
    
    if not init_data:
        return jsonify({
            'valid': False,
            'error': 'No se proporcionaron datos de Telegram'
        }), 400
    
    validated_data = validate_telegram_webapp_data(init_data)
    
    if not validated_data:
        return jsonify({
            'valid': False,
            'error': 'Datos de Telegram invalidos'
        }), 401
    
    user = validated_data.get('user', {})
    user_id = user.get('id')
    
    if not user_id:
        return jsonify({
            'valid': False,
            'error': 'Usuario no identificado'
        }), 401
    
    owner_status = is_owner(user_id)
    test_user_status = is_test_user(user_id)
    
    if not owner_status and not test_user_status:
        return jsonify({
            'valid': False,
            'error': 'Acceso no autorizado',
            'isOwner': False
        }), 403
    
    db_manager = get_db_manager()
    if db_manager:
        try:
            db_manager.get_or_create_user(
                user_id=str(user_id),
                username=user.get('username', ''),
                first_name=user.get('first_name', ''),
                last_name=user.get('last_name', ''),
                telegram_id=user_id
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
    
    return jsonify({
        'valid': True,
        'isOwner': owner_status,
        'isTestUser': test_user_status,
        'user': {
            'id': user_id,
            'firstName': user.get('first_name', ''),
            'lastName': user.get('last_name', ''),
            'username': user.get('username', ''),
            'languageCode': user.get('language_code', 'es')
        }
    })
