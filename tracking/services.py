"""
Servicios compartidos para blueprints.
Este modulo proporciona acceso a servicios singleton que son usados por multiples blueprints.
"""

import os
import logging
from datetime import datetime
from flask import session

logger = logging.getLogger(__name__)

_db_manager = None
_security_manager = None
_vn_manager = None

def get_db_manager():
    """Obtiene la instancia del DatabaseManager."""
    global _db_manager
    if _db_manager is None:
        from tracking.database import DatabaseManager
        _db_manager = DatabaseManager()
    return _db_manager

def set_db_manager(manager):
    """Establece la instancia del DatabaseManager (para inyeccion desde app.py)."""
    global _db_manager
    _db_manager = manager

def get_security_manager():
    """Obtiene la instancia del SecurityManager."""
    global _security_manager
    return _security_manager

def set_security_manager(manager):
    """Establece la instancia del SecurityManager."""
    global _security_manager
    _security_manager = manager

def get_vn_manager():
    """Obtiene la instancia del VirtualNumbersManager."""
    global _vn_manager
    return _vn_manager

def set_vn_manager(manager):
    """Establece la instancia del VirtualNumbersManager."""
    global _vn_manager
    _vn_manager = manager


IS_PRODUCTION = os.environ.get('REPL_DEPLOYMENT', '') == '1'


def get_demo_session_token(client_ip: str) -> str:
    """Genera un token de sesion para el modo demo usando Flask-Session persistente."""
    import secrets
    token = secrets.token_urlsafe(32)
    session['demo_2fa_token'] = token
    session['demo_2fa_ip'] = client_ip
    session['demo_2fa_created_at'] = datetime.now().isoformat()
    session['demo_2fa_valid'] = True
    session.permanent = True
    return token


def verify_demo_session(token: str = None, client_ip: str = None) -> bool:
    """Verifica si la sesion demo es valida usando Flask-Session persistente."""
    if session.get('demo_2fa_valid'):
        stored_token = session.get('demo_2fa_token')
        stored_ip = session.get('demo_2fa_ip')
        
        if client_ip and stored_ip and client_ip != stored_ip:
            logger.warning(f"Demo session IP mismatch: {client_ip} vs {stored_ip}")
            return False
        
        if token and stored_token and token != stored_token:
            return False
        
        return True
    
    return False


def invalidate_demo_session():
    """Invalida la sesion 2FA demo actual."""
    session.pop('demo_2fa_token', None)
    session.pop('demo_2fa_ip', None)
    session.pop('demo_2fa_created_at', None)
    session.pop('demo_2fa_valid', None)
