"""
Routes Module - Blueprints para organizar endpoints por dominio

Este modulo contiene los blueprints separados por responsabilidad:
- admin_bp: Endpoints del panel de administracion (/api/admin/*)
- user_bp: Endpoints de usuario (/api/user/*)
- blockchain_bp: Endpoints de B3C, wallets (/api/blockchain/*)
- auth_bp: Endpoints de autenticacion y 2FA (/api/auth/*)
- tracking_bp: Endpoints de seguimiento de paquetes (/api/tracking/*)
- bots_bp: Endpoints de bots de usuario (/api/bots/*)
- vn_bp: Endpoints de numeros virtuales (/api/vn/*)

ESTADO DE MIGRACION (10 Diciembre 2025):
- Migrados 287+ endpoints de app.py a blueprints modulares
- admin_bp: 99+ endpoints admin
- user_bp: 93+ endpoints usuario
- blockchain_bp: 42+ endpoints blockchain/wallets
- auth_bp: 10 endpoints auth/2FA
- tracking_bp: 9+ endpoints tracking
- bots_bp: 7 endpoints bots (NUEVO)
- vn_bp: 12 endpoints virtual numbers (NUEVO)

USO:
    from routes import (admin_bp, user_bp, blockchain_bp, auth_bp, 
                       tracking_bp, bots_bp, vn_bp)
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(bots_bp)
    app.register_blueprint(vn_bp)
"""

from routes.admin_routes import admin_bp
from routes.user_routes import user_bp
from routes.blockchain_routes import blockchain_bp
from routes.auth_routes import auth_bp
from routes.tracking_routes import tracking_bp
from routes.bots_routes import bots_bp
from routes.vn_routes import vn_bp

__all__ = ['admin_bp', 'user_bp', 'blockchain_bp', 'auth_bp', 'tracking_bp', 'bots_bp', 'vn_bp']
