"""
Bots Routes - Endpoints de Bots de Usuario
Agente: Frontend-User
Rama: feature/frontend-user

Este archivo contiene los endpoints de bots migrados desde app.py
Migracion: 10 Diciembre 2025

Endpoints migrados:
- /api/bots/init (POST) - Inicializar tipos de bots
- /api/bots/my (GET) - Obtener mis bots
- /api/bots/available (GET) - Bots disponibles para comprar
- /api/bots/purchase (POST) - Comprar un bot
- /api/bots/<id>/remove (POST) - Desactivar un bot
- /api/bots/<id>/toggle (POST) - Toggle activacion
- /api/bots/<id>/config (GET/POST) - Configuracion de bot
"""

import os
import logging

from flask import Blueprint, jsonify, request

from tracking.decorators import require_telegram_auth, require_telegram_user, is_owner
from tracking.services import get_db_manager

logger = logging.getLogger(__name__)

bots_bp = Blueprint('bots', __name__, url_prefix='/api/bots')

OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '')


@bots_bp.route('/health', methods=['GET'])
def bots_health():
    """Health check del modulo bots."""
    return jsonify({
        'success': True,
        'module': 'bots_routes',
        'status': 'active',
        'endpoints_migrated': [
            '/api/bots/init',
            '/api/bots/my',
            '/api/bots/available',
            '/api/bots/purchase',
            '/api/bots/<id>/remove',
            '/api/bots/<id>/toggle',
            '/api/bots/<id>/config'
        ]
    })


@bots_bp.route('/init', methods=['POST'])
@require_telegram_auth
def init_bots():
    """Inicializar tabla de tipos de bots (solo owner)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        success = db_manager.initialize_bot_types()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Tipos de bots inicializados correctamente'
            })
        else:
            return jsonify({'error': 'Error al inicializar bots'}), 500
            
    except Exception as e:
        logger.error(f"Error initializing bots: {e}")
        return jsonify({'error': 'Error al inicializar bots'}), 500


@bots_bp.route('/my', methods=['GET'])
@require_telegram_user
def get_my_bots():
    """Obtener mis bots activos."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        is_demo = getattr(request, 'is_demo', False)
        
        if is_demo and OWNER_TELEGRAM_ID:
            user_id = str(OWNER_TELEGRAM_ID)
            user_is_owner = True
        else:
            user_id = str(user.get('id'))
            user_is_owner = is_owner(user.get('id'))
        
        bots = db_manager.get_user_bots(user_id, is_owner=user_is_owner)
        
        result = []
        for bot in bots:
            result.append({
                'id': bot.get('id'),
                'botName': bot.get('bot_name'),
                'botType': bot.get('bot_type'),
                'isActive': bot.get('is_active', True),
                'icon': bot.get('icon', '🤖'),
                'description': bot.get('description', ''),
                'config': bot.get('config'),
                'createdAt': bot.get('created_at').isoformat() if bot.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'bots': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting user bots: {e}")
        return jsonify({'error': 'Error al obtener bots'}), 500


@bots_bp.route('/available', methods=['GET'])
@require_telegram_user
def get_available_bots():
    """Obtener bots disponibles para comprar."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        is_demo = getattr(request, 'is_demo', False)
        
        if is_demo and OWNER_TELEGRAM_ID:
            user_id = str(OWNER_TELEGRAM_ID)
            user_is_owner = True
        else:
            user_id = str(user.get('id'))
            user_is_owner = is_owner(user.get('id'))
        
        bots = db_manager.get_available_bots(user_id, is_owner=user_is_owner)
        
        result = []
        for bot in bots:
            result.append({
                'id': bot.get('id'),
                'botName': bot.get('bot_name'),
                'botType': bot.get('bot_type'),
                'description': bot.get('description', ''),
                'icon': bot.get('icon', '🤖'),
                'price': bot.get('price', 0)
            })
        
        return jsonify({
            'success': True,
            'bots': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting available bots: {e}")
        return jsonify({'error': 'Error al obtener bots disponibles'}), 500


@bots_bp.route('/purchase', methods=['POST'])
@require_telegram_user
def purchase_bot():
    """Comprar un bot."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        data = request.get_json()
        bot_type = data.get('botType')
        
        if not bot_type:
            return jsonify({'error': 'Tipo de bot requerido'}), 400
        
        result = db_manager.purchase_bot(user_id, bot_type)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'botName': result.get('bot_name'),
                'creditsRemaining': result.get('credits_remaining')
            })
        else:
            error = result.get('error', 'Error desconocido')
            status_code = 400 if 'insuficientes' in error.lower() or 'ya tienes' in error.lower() else 500
            return jsonify({
                'success': False,
                'error': error,
                'required': result.get('required'),
                'current': result.get('current')
            }), status_code
            
    except Exception as e:
        logger.error(f"Error purchasing bot: {e}")
        return jsonify({'error': 'Error al comprar bot'}), 500


@bots_bp.route('/<int:bot_id>/remove', methods=['POST'])
@require_telegram_user
def remove_bot(bot_id):
    """Desactivar un bot."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        success = db_manager.remove_user_bot(user_id, bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bot desactivado correctamente'
            })
        else:
            return jsonify({'error': 'Error al desactivar bot'}), 500
            
    except Exception as e:
        logger.error(f"Error removing bot {bot_id}: {e}")
        return jsonify({'error': 'Error al desactivar bot'}), 500


@bots_bp.route('/<int:bot_id>/toggle', methods=['POST'])
@require_telegram_user
def toggle_bot(bot_id):
    """Toggle bot activation status."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.toggle_bot_activation(user_id, bot_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'isActive': result.get('is_active'),
                'message': 'Bot activado' if result.get('is_active') else 'Bot desactivado'
            })
        else:
            return jsonify({'error': result.get('error', 'Error al cambiar estado')}), 500
            
    except Exception as e:
        logger.error(f"Error toggling bot {bot_id}: {e}")
        return jsonify({'error': 'Error al cambiar estado del bot'}), 500


@bots_bp.route('/<int:bot_id>/config', methods=['GET', 'POST'])
@require_telegram_user
def bot_config(bot_id):
    """Get or update bot configuration."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if request.method == 'GET':
            result = db_manager.get_bot_config(user_id, bot_id)
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'config': result.get('config', {}),
                    'botType': result.get('bot_type'),
                    'botName': result.get('bot_name')
                })
            else:
                return jsonify({'error': result.get('error', 'Bot no encontrado')}), 404
        else:
            data = request.get_json() or {}
            config = data.get('config', {})
            result = db_manager.update_bot_config(user_id, bot_id, config)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Configuracion guardada'
                })
            else:
                return jsonify({'error': result.get('error', 'Error al guardar')}), 500
            
    except Exception as e:
        logger.error(f"Error with bot config {bot_id}: {e}")
        return jsonify({'error': 'Error con configuracion del bot'}), 500
