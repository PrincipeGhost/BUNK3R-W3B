"""
Servicios compartidos para blueprints.
Este modulo proporciona acceso a servicios singleton que son usados por multiples blueprints.
Solo maneja managers (db, security, vn) - para sesiones demo usar tracking.demo_sessions.
"""

import os
import logging

logger = logging.getLogger(__name__)

_db_manager = None
_security_manager = None
_vn_manager = None


def get_db_manager():
    """Obtiene la instancia del DatabaseManager."""
    global _db_manager
    if _db_manager is None:
        from bot.tracking_correos.database import DatabaseManager
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
