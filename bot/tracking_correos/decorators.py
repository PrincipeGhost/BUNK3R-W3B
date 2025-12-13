"""
Decoradores de autenticacion y autorizacion para endpoints Flask.
Este modulo contiene los decoradores compartidos entre blueprints.
"""

import os
import hmac
import hashlib
import json
import logging
import time
from functools import wraps
from urllib.parse import parse_qs, unquote, urlparse

from flask import request, jsonify, session

logger = logging.getLogger(__name__)

IS_PRODUCTION = os.environ.get('REPL_DEPLOYMENT', '') == '1'
BOT_TOKEN = os.environ.get('BOT_TOKEN', '') or os.environ.get('TELEGRAM_BOT_TOKEN', '')
OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '')
USER_TELEGRAM_ID = os.environ.get('USER_TELEGRAM_ID', '')


def validate_telegram_webapp_data(init_data: str):
    """Valida los datos de Telegram Web App segun la documentacion oficial."""
    if not init_data or not BOT_TOKEN:
        return None
    
    try:
        parsed_data = dict(parse_qs(init_data))
        parsed_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
        
        if 'hash' not in parsed_data:
            logger.warning("No hash in init_data")
            return None
        
        received_hash = parsed_data.pop('hash')
        
        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            logger.warning("Hash mismatch in Telegram validation")
            return None
        
        if 'user' in parsed_data:
            user_str = parsed_data['user']
            if isinstance(user_str, str):
                user_data = json.loads(unquote(user_str))
                parsed_data['user'] = user_data
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        return None


def is_owner(user_id: int) -> bool:
    """Verifica si el usuario es el owner."""
    try:
        owner_id = int(OWNER_TELEGRAM_ID) if OWNER_TELEGRAM_ID else 0
        return user_id == owner_id
    except (ValueError, TypeError) as e:
        logger.debug(f"Error checking owner: {e}")
        return False


def is_test_user(user_id: int) -> bool:
    """Verifica si el usuario es el usuario de prueba."""
    try:
        test_user_id = int(USER_TELEGRAM_ID) if USER_TELEGRAM_ID else 0
        return user_id == test_user_id
    except (ValueError, TypeError) as e:
        logger.debug(f"Error checking test user: {e}")
        return False


def is_allowed_user(user_id: int) -> bool:
    """Verifica si el usuario tiene permiso de acceso (owner o usuario de prueba)."""
    return is_owner(user_id) or is_test_user(user_id)


from bot.tracking_correos.demo_sessions import (
    verify_demo_session,
    create_demo_session,
    invalidate_demo_session
)


def require_telegram_auth(f):
    """Decorador para requerir autenticacion de Telegram o modo demo con 2FA."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        demo_header_present = request.headers.get('X-Demo-Mode') == 'true'
        
        if demo_header_present and IS_PRODUCTION:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            logger.warning(f"SECURITY: Demo mode attempt blocked in production from IP: {client_ip}")
            return jsonify({'error': 'Modo demo no disponible', 'code': 'DEMO_DISABLED'}), 403
        
        if demo_header_present and not IS_PRODUCTION:
            demo_session_token = request.headers.get('X-Demo-Session')
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if not verify_demo_session(demo_session_token, client_ip):
                return jsonify({
                    'error': 'Se requiere autenticacion para modo demo',
                    'code': 'DEMO_2FA_REQUIRED',
                    'requiresDemo2FA': True
                }), 401
            
            request.telegram_user = {'id': 0, 'first_name': 'Demo', 'username': 'demo_user'}
            request.telegram_data = {}
            request.is_owner = True
            request.is_demo = True
            return f(*args, **kwargs)
        
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram invalidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado', 'code': 'NO_USER'}), 401
        
        if not is_allowed_user(user_id):
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NOT_ALLOWED'}), 403
        
        request.telegram_user = user
        request.telegram_data = validated_data
        request.is_owner = is_owner(user_id)
        request.is_test_user = is_test_user(user_id)
        request.is_demo = False
        
        return f(*args, **kwargs)
    return decorated_function


def require_owner(f):
    """Decorador para funciones que solo el owner puede usar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(request, 'is_owner', False):
            return jsonify({'error': 'Funcion solo disponible para el owner'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_telegram_user(f):
    """Decorador para funciones que cualquier usuario autenticado de Telegram puede usar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        demo_header_present = request.headers.get('X-Demo-Mode') == 'true'
        
        if demo_header_present and IS_PRODUCTION:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            logger.warning(f"SECURITY: Demo mode attempt blocked in production from IP: {client_ip}")
            return jsonify({'error': 'Modo demo no disponible', 'code': 'DEMO_DISABLED'}), 403
        
        if demo_header_present and not IS_PRODUCTION:
            demo_session_token = request.headers.get('X-Demo-Session')
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if not verify_demo_session(demo_session_token, client_ip):
                return jsonify({
                    'error': 'Se requiere autenticacion para modo demo',
                    'code': 'DEMO_2FA_REQUIRED',
                    'requiresDemo2FA': True
                }), 401
            
            request.telegram_user = {'id': 0, 'first_name': 'Demo', 'username': 'demo_user'}
            request.telegram_data = {}
            request.is_owner = True
            request.is_demo = True
            return f(*args, **kwargs)
        
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram invalidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado', 'code': 'NO_USER'}), 401
        
        request.telegram_user = user
        request.telegram_data = validated_data
        request.is_owner = is_owner(user_id)
        request.is_demo = False
        
        return f(*args, **kwargs)
    return decorated_function


def verify_origin_referer() -> tuple:
    """
    Verifica Origin/Referer para proteccion CSRF.
    Returns: (is_valid: bool, error_message: str or None)
    """
    if not IS_PRODUCTION:
        return True, None
    
    origin = request.headers.get('Origin', '')
    referer = request.headers.get('Referer', '')
    host = request.host_url.rstrip('/')
    
    allowed_origins = {
        host,
        'https://web.telegram.org',
        'https://telegram.org'
    }
    
    if origin:
        origin_base = origin.rstrip('/')
        if origin_base not in allowed_origins and not origin_base.endswith('.telegram.org'):
            return False, f"Origin no permitido: {origin}"
    
    if referer:
        referer_host = urlparse(referer).netloc
        host_only = request.host.split(':')[0]
        if referer_host not in [host_only, 'web.telegram.org', 'telegram.org'] and not referer_host.endswith('.telegram.org'):
            return False, f"Referer no permitido: {referer_host}"
    
    return True, None


def csrf_protect(f):
    """
    Decorador para proteccion CSRF en endpoints POST/PUT/DELETE.
    Verifica Origin/Referer y requiere autenticacion valida.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            is_valid, error = verify_origin_referer()
            if not is_valid:
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                logger.warning(f"CSRF: Blocked request from IP {client_ip}: {error}")
                return jsonify({
                    'error': 'Solicitud no autorizada',
                    'code': 'CSRF_FAILED'
                }), 403
        
        return f(*args, **kwargs)
    return decorated_function


CSRF_EXEMPT_ENDPOINTS = {
    'static',
    'index',
    'health_check',
    'tonconnect_manifest',
    'get_b3c_price',
    'get_b3c_network',
    'api_b3c_calculate',
    'calculate_b3c_sell',
    'public_posts_feed',
    'public_user_profile',
    'public_comments'
}


def get_current_web_user():
    """Obtiene el usuario actual de la sesion web.
    
    Returns:
        dict: Datos del usuario o None si no hay sesion
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    return {
        'id': user_id,
        'username': session.get('username'),
        'email': session.get('email'),
        'email_verified': session.get('email_verified', False),
        'is_admin': session.get('is_admin', False),
        'two_factor_enabled': session.get('two_factor_enabled', False)
    }


def create_web_session(user_data: dict, client_ip: str = None):
    """Crea una sesion web para el usuario.
    
    Args:
        user_data: Diccionario con datos del usuario desde BD
        client_ip: IP del cliente para tracking
    """
    session['user_id'] = user_data.get('id')
    session['username'] = user_data.get('username')
    session['email'] = user_data.get('email')
    session['email_verified'] = user_data.get('email_verified', False)
    session['is_admin'] = user_data.get('is_admin', False)
    session['two_factor_enabled'] = user_data.get('two_factor_enabled', False)
    session['login_ip'] = client_ip
    session['login_time'] = time.time()
    session.permanent = True


def invalidate_web_session():
    """Invalida la sesion web actual."""
    keys_to_remove = ['user_id', 'username', 'email', 'email_verified', 
                      'is_admin', 'two_factor_enabled', 'login_ip', 'login_time']
    for key in keys_to_remove:
        session.pop(key, None)


def require_web_auth(f):
    """Decorador para requerir autenticacion web (usuario logueado con 2FA verificado)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_web_user()
        
        if not user or not user.get('id'):
            return jsonify({
                'error': 'Sesion no valida',
                'code': 'NOT_AUTHENTICATED',
                'redirect': '/login'
            }), 401
        
        if not user.get('email_verified'):
            return jsonify({
                'error': 'Email no verificado',
                'code': 'EMAIL_NOT_VERIFIED',
                'redirect': '/verificar-email'
            }), 403
        
        if not user.get('two_factor_enabled'):
            return jsonify({
                'error': '2FA no configurado',
                'code': '2FA_NOT_SETUP',
                'redirect': '/setup-2fa'
            }), 403
        
        request.web_user = user
        request.is_admin = user.get('is_admin', False)
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorador para funciones que solo el admin/owner puede usar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_web_user()
        
        if not user or not user.get('id'):
            return jsonify({
                'error': 'Sesion no valida',
                'code': 'NOT_AUTHENTICATED',
                'redirect': '/login'
            }), 401
        
        if not user.get('is_admin'):
            logger.warning(f"Admin access denied for user {user.get('id')}")
            return jsonify({
                'error': 'Acceso denegado',
                'code': 'NOT_ADMIN'
            }), 403
        
        request.web_user = user
        request.is_admin = True
        
        return f(*args, **kwargs)
    return decorated_function


def require_email_verified(f):
    """Decorador para requerir que el email este verificado."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_web_user()
        
        if not user or not user.get('id'):
            return jsonify({
                'error': 'Sesion no valida',
                'code': 'NOT_AUTHENTICATED',
                'redirect': '/login'
            }), 401
        
        if not user.get('email_verified'):
            return jsonify({
                'error': 'Debes verificar tu email primero',
                'code': 'EMAIL_NOT_VERIFIED',
                'redirect': '/verificar-email'
            }), 403
        
        request.web_user = user
        
        return f(*args, **kwargs)
    return decorated_function
