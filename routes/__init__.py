"""
Routes Module - Blueprints para organizar endpoints por dominio

Este modulo contiene los blueprints separados por responsabilidad:
- admin_bp: Endpoints del panel de administracion (/api/admin/*)
- user_bp: Endpoints de usuario (/api/user/*)
- blockchain_bp: Endpoints de B3C, wallets (/api/blockchain/*)
- auth_bp: Endpoints de autenticacion y 2FA (/api/auth/*)

ESTADO DE MIGRACION:
- Los endpoints principales siguen en app.py
- Los blueprints estan preparados para migracion gradual
- Cada blueprint tiene un endpoint /health para verificar estado

USO:
    from routes import admin_bp, user_bp, blockchain_bp, auth_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(auth_bp)
"""

from routes.admin_routes import admin_bp
from routes.user_routes import user_bp
from routes.blockchain_routes import blockchain_bp
from routes.auth_routes import auth_bp

__all__ = ['admin_bp', 'user_bp', 'blockchain_bp', 'auth_bp']
