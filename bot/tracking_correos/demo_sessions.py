"""
Funciones de gestion de sesion demo.
Utilidades puras para manejo de sesiones demo usando Flask-Session.
"""

import logging
from datetime import datetime
from flask import session

logger = logging.getLogger(__name__)


def verify_demo_session(token: str = None, client_ip: str = None) -> bool:
    """Verifica si una sesion demo es valida usando Flask-Session."""
    if not session.get('demo_2fa_valid'):
        return False
    
    stored_ip = session.get('demo_2fa_ip')
    if stored_ip and client_ip:
        primary_stored_ip = stored_ip.split(',')[0].strip()
        primary_client_ip = client_ip.split(',')[0].strip()
        if primary_stored_ip != primary_client_ip:
            logger.warning(f"Demo session IP mismatch: stored={primary_stored_ip}, current={primary_client_ip}")
            return False
    
    created_at_str = session.get('demo_2fa_created_at')
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str)
            if (datetime.now() - created_at).total_seconds() > 7200:
                invalidate_demo_session()
                return False
        except Exception:
            pass
    
    if token and session.get('demo_2fa_token') != token:
        return False
    
    return True


def create_demo_session(client_ip: str, duration_hours: int = 2) -> str:
    """Crea una nueva sesion demo usando Flask-Session."""
    import secrets
    token = secrets.token_urlsafe(32)
    session['demo_2fa_token'] = token
    session['demo_2fa_ip'] = client_ip
    session['demo_2fa_created_at'] = datetime.now().isoformat()
    session['demo_2fa_valid'] = True
    session.permanent = True
    return token


def invalidate_demo_session():
    """Invalida la sesion 2FA demo actual."""
    session.pop('demo_2fa_token', None)
    session.pop('demo_2fa_ip', None)
    session.pop('demo_2fa_created_at', None)
    session.pop('demo_2fa_valid', None)


get_demo_session_token = create_demo_session
