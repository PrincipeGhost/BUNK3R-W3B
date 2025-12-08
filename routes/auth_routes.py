"""
Auth Routes - Endpoints de Autenticacion, 2FA, Sesiones
Agente: Backend-API
Rama: feature/backend-api

Este archivo contiene los endpoints relacionados con autenticacion y 2FA.
Los endpoints estan siendo migrados gradualmente desde app.py

Endpoints que pertenecen a este modulo:
- /api/2fa/* - Setup, verify, status, disable
- /api/auth/* - Login, logout, refresh token
- /api/demo/* - Modo demo 2FA
- /api/health - Health check
- /api/telegram/* - Validacion Telegram WebApp
"""

from flask import Blueprint, jsonify, request

import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """Health check del modulo auth."""
    return jsonify({
        'success': True,
        'module': 'auth_routes',
        'status': 'active',
        'message': 'Endpoints de auth funcionando. Migracion en progreso.'
    })
