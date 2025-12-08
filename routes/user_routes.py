"""
User Routes - Endpoints de Usuario (perfil, publicaciones, social)
Agente: Frontend-User
Rama: feature/frontend-user

Este archivo contiene los endpoints de usuario.
Los endpoints estan siendo migrados gradualmente desde app.py

Endpoints que pertenecen a este modulo:
- /api/users/* - Perfil, follow, stats
- /api/publications/* - CRUD publicaciones, reacciones, comentarios
- /api/stories/* - Stories de usuario
- /api/messages/* - Chat privado
- /api/notifications/* - Notificaciones
- /api/search/* - Busqueda
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/health', methods=['GET'])
def user_health():
    """Health check del modulo user."""
    return jsonify({
        'success': True,
        'module': 'user_routes',
        'status': 'active',
        'message': 'Endpoints de usuario funcionando. Migracion en progreso.'
    })
