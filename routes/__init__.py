"""
Routes Module - Blueprints para organizar endpoints por dominio

Este modulo contiene los blueprints separados por responsabilidad:
- admin_routes: Endpoints del panel de administracion
- user_routes: Endpoints de usuario (perfil, publicaciones, social)
- blockchain_routes: Endpoints de B3C, wallets, transacciones
- auth_routes: Endpoints de autenticacion y 2FA
"""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
user_bp = Blueprint('user', __name__, url_prefix='/api')
blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api')
auth_bp = Blueprint('auth', __name__, url_prefix='/api')
