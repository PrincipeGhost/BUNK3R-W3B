"""
Blockchain Routes - Endpoints de B3C, Wallets, Transacciones TON
Agente: Blockchain-Services
Rama: feature/blockchain-services

Este archivo contiene los endpoints relacionados con blockchain y wallets.
Los endpoints estan siendo migrados gradualmente desde app.py

Endpoints que pertenecen a este modulo:
- /api/b3c/* - Compra, venta, balance, transacciones
- /api/wallet/* - Conexion wallet, balance, creditos
- /api/deposits/*
- /api/withdrawals/*
- /api/ton/*
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api/blockchain')


@blockchain_bp.route('/health', methods=['GET'])
def blockchain_health():
    """Health check del modulo blockchain."""
    return jsonify({
        'success': True,
        'module': 'blockchain_routes',
        'status': 'active',
        'message': 'Endpoints de blockchain funcionando. Migracion en progreso.'
    })
