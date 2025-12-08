"""
Admin Routes - Endpoints del Panel de Administracion
Agente: Frontend-Admin
Rama: feature/frontend-admin

Este archivo contiene los endpoints del panel de administracion.
Los endpoints estan siendo migrados gradualmente desde app.py

Endpoints que pertenecen a este modulo:
- /api/admin/dashboard/* - Stats y actividad
- /api/admin/users/* - Gestion de usuarios
- /api/admin/stats/* - Estadisticas
- /api/admin/security/* - Seguridad
- /api/admin/financial/* - Finanzas
- /api/admin/content/* - Contenido
- /api/admin/fraud/* - Deteccion de fraude
- /api/admin/sessions/* - Sesiones
- /api/admin/anomalies/* - Anomalias
- /api/admin/risk-score/* - Puntuacion de riesgo
- /api/admin/support/* - Tickets y soporte
- /api/admin/config/* - Configuracion del sistema
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """Health check del modulo admin."""
    return jsonify({
        'success': True,
        'module': 'admin_routes',
        'status': 'active',
        'message': 'Endpoints de admin funcionando. Migracion en progreso.'
    })
