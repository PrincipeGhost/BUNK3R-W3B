"""
Security module for device trust and wallet management
Sistema de Seguridad de Dispositivos y Wallet para BUNK3RCO1N
"""

import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import requests

logger = logging.getLogger(__name__)

CREATE_SECURITY_TABLES_SQL = """
-- Tabla de dispositivos de confianza
CREATE TABLE IF NOT EXISTS trusted_devices (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255) DEFAULT 'Dispositivo desconocido',
    device_type VARCHAR(100) DEFAULT 'unknown',
    user_agent TEXT,
    ip_address VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(user_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_trusted_devices_user ON trusted_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_trusted_devices_device ON trusted_devices(device_id);

-- Tabla de intentos fallidos de wallet
CREATE TABLE IF NOT EXISTS wallet_failed_attempts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    attempted_wallet VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallet_attempts_user ON wallet_failed_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_attempts_time ON wallet_failed_attempts(created_at);

-- Tabla de bloqueos por intentos fallidos
CREATE TABLE IF NOT EXISTS user_lockouts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    reason VARCHAR(100) NOT NULL,
    locked_until TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, reason)
);

CREATE INDEX IF NOT EXISTS idx_lockouts_user ON user_lockouts(user_id);

-- Tabla de historial de actividad de seguridad
CREATE TABLE IF NOT EXISTS security_activity_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    device_id VARCHAR(255),
    ip_address VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_log_user ON security_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_log_type ON security_activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_security_log_time ON security_activity_log(created_at DESC);

-- Tabla de alertas de seguridad para admin
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON security_alerts(is_resolved, created_at DESC);

-- Agregar columnas a users para wallet primaria y de respaldo
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='primary_wallet_address') THEN
        ALTER TABLE users ADD COLUMN primary_wallet_address VARCHAR(255);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='backup_wallet_address') THEN
        ALTER TABLE users ADD COLUMN backup_wallet_address VARCHAR(255);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='wallet_registered_at') THEN
        ALTER TABLE users ADD COLUMN wallet_registered_at TIMESTAMP;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='security_score') THEN
        ALTER TABLE users ADD COLUMN security_score INTEGER DEFAULT 0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_primary_wallet ON users(primary_wallet_address);
"""

class SecurityManager:
    """Manages device trust, wallet validation, and security operations"""
    
    MAX_TRUSTED_DEVICES = 2
    LOCKOUT_DURATION_MINUTES = 15
    MAX_FAILED_ATTEMPTS = 3
    DEVICE_EXPIRY_DAYS = 60
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.bot_token = os.environ.get('BOT_TOKEN', '')
    
    def initialize_tables(self) -> bool:
        """Create security tables if they don't exist"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(CREATE_SECURITY_TABLES_SQL)
                    conn.commit()
            logger.info("Security tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing security tables: {e}")
            return False
    
    def get_user_primary_wallet(self, user_id: str) -> Optional[str]:
        """Get user's registered primary wallet address"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT primary_wallet_address FROM users WHERE telegram_id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting primary wallet for user {user_id}: {e}")
            return None
    
    def register_primary_wallet(self, user_id: str, wallet_address: str) -> Dict:
        """Register a wallet as the user's primary wallet (first time only)"""
        try:
            existing = self.get_user_primary_wallet(user_id)
            if existing:
                return {
                    'success': False,
                    'error': 'Ya tienes una wallet registrada',
                    'registered_wallet': existing[:8] + '...' + existing[-4:]
                }
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users 
                        SET primary_wallet_address = %s, 
                            wallet_address = %s,
                            wallet_registered_at = NOW()
                        WHERE telegram_id = %s
                    """, (wallet_address, wallet_address, user_id))
                    conn.commit()
            
            self.log_security_activity(
                user_id, 'WALLET_REGISTERED',
                f'Wallet primaria registrada: {wallet_address[:8]}...{wallet_address[-4:]}'
            )
            
            return {'success': True, 'message': 'Wallet registrada correctamente'}
        except Exception as e:
            logger.error(f"Error registering wallet for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_wallet_connection(self, user_id: str, wallet_address: str, device_id: str = None, ip_address: str = None) -> Dict:
        """Validate that the connecting wallet matches the registered one"""
        try:
            if self.is_user_locked_out(user_id, 'wallet_attempts'):
                lockout_until = self.get_lockout_time(user_id, 'wallet_attempts')
                return {
                    'success': False,
                    'error': 'Cuenta bloqueada temporalmente por intentos fallidos',
                    'locked_until': lockout_until.isoformat() if lockout_until else None,
                    'is_locked': True
                }
            
            primary_wallet = self.get_user_primary_wallet(user_id)
            
            if not primary_wallet:
                result = self.register_primary_wallet(user_id, wallet_address)
                if result['success']:
                    return {
                        'success': True,
                        'is_new_wallet': True,
                        'message': 'Wallet registrada por primera vez'
                    }
                return result
            
            if primary_wallet.lower() == wallet_address.lower():
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE users SET wallet_address = %s WHERE telegram_id = %s
                        """, (wallet_address, user_id))
                        conn.commit()
                return {
                    'success': True,
                    'is_registered_wallet': True,
                    'message': 'Wallet verificada correctamente'
                }
            
            self.record_failed_wallet_attempt(user_id, wallet_address, device_id, ip_address)
            
            attempts = self.get_recent_failed_attempts(user_id)
            remaining = self.MAX_FAILED_ATTEMPTS - attempts
            
            if attempts >= self.MAX_FAILED_ATTEMPTS:
                self.lock_user(user_id, 'wallet_attempts', self.LOCKOUT_DURATION_MINUTES)
                self.create_security_alert(
                    user_id, 'MULTIPLE_WRONG_WALLETS', 'high',
                    f'Usuario bloqueado por {self.MAX_FAILED_ATTEMPTS} intentos de wallet incorrecta'
                )
                self.send_telegram_notification(
                    user_id,
                    f"⚠️ Alerta de seguridad: Alguien intento acceder a tu cuenta con una wallet diferente.\n"
                    f"Tu cuenta ha sido bloqueada por {self.LOCKOUT_DURATION_MINUTES} minutos."
                )
            
            return {
                'success': False,
                'error': 'Esta no es tu wallet registrada. Debes usar la wallet asociada a tu cuenta.',
                'is_wrong_wallet': True,
                'attempts_remaining': max(0, remaining),
                'registered_wallet_hint': primary_wallet[:8] + '...' + primary_wallet[-4:]
            }
            
        except Exception as e:
            logger.error(f"Error validating wallet for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def record_failed_wallet_attempt(self, user_id: str, wallet_address: str, device_id: str = None, ip_address: str = None):
        """Record a failed wallet connection attempt"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO wallet_failed_attempts (user_id, attempted_wallet, device_id, ip_address)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, wallet_address, device_id, ip_address))
                    conn.commit()
            
            self.log_security_activity(
                user_id, 'WALLET_FAILED_ATTEMPT',
                f'Intento de conexion con wallet incorrecta: {wallet_address[:8]}...',
                device_id, ip_address
            )
        except Exception as e:
            logger.error(f"Error recording failed wallet attempt: {e}")
    
    def get_recent_failed_attempts(self, user_id: str, minutes: int = 15) -> int:
        """Get count of failed wallet attempts in recent minutes"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM wallet_failed_attempts 
                        WHERE user_id = %s AND created_at > NOW() - INTERVAL '%s minutes'
                    """, (user_id, minutes))
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting failed attempts: {e}")
            return 0
    
    def lock_user(self, user_id: str, reason: str, minutes: int):
        """Lock user for specified duration"""
        try:
            locked_until = datetime.now() + timedelta(minutes=minutes)
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_lockouts (user_id, reason, locked_until)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, reason) 
                        DO UPDATE SET locked_until = EXCLUDED.locked_until
                    """, (user_id, reason, locked_until))
                    conn.commit()
            
            self.log_security_activity(user_id, 'USER_LOCKED', f'Usuario bloqueado: {reason} por {minutes} minutos')
        except Exception as e:
            logger.error(f"Error locking user {user_id}: {e}")
    
    def is_user_locked_out(self, user_id: str, reason: str) -> bool:
        """Check if user is currently locked out"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT locked_until FROM user_lockouts 
                        WHERE user_id = %s AND reason = %s AND locked_until > NOW()
                    """, (user_id, reason))
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Error checking lockout: {e}")
            return False
    
    def get_lockout_time(self, user_id: str, reason: str) -> Optional[datetime]:
        """Get the time when lockout expires"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT locked_until FROM user_lockouts 
                        WHERE user_id = %s AND reason = %s AND locked_until > NOW()
                    """, (user_id, reason))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting lockout time: {e}")
            return None
    
    def is_device_trusted(self, user_id: str, device_id: str) -> Dict:
        """Check if a device is trusted for the user"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, device_name, device_type, last_used_at, expires_at
                        FROM trusted_devices 
                        WHERE user_id = %s AND device_id = %s AND is_active = TRUE
                    """, (user_id, device_id))
                    result = cur.fetchone()
                    
                    if result:
                        expires_at = result[4]
                        if expires_at and expires_at < datetime.now():
                            cur.execute("""
                                UPDATE trusted_devices SET is_active = FALSE
                                WHERE id = %s
                            """, (result[0],))
                            conn.commit()
                            return {'is_trusted': False, 'expired': True}
                        
                        cur.execute("""
                            UPDATE trusted_devices SET last_used_at = NOW()
                            WHERE id = %s
                        """, (result[0],))
                        conn.commit()
                        
                        return {
                            'is_trusted': True,
                            'device_name': result[1],
                            'device_type': result[2],
                            'last_used': result[3].isoformat() if result[3] else None
                        }
                    
                    return {'is_trusted': False}
        except Exception as e:
            logger.error(f"Error checking trusted device: {e}")
            return {'is_trusted': False, 'error': str(e)}
    
    def get_trusted_devices_count(self, user_id: str) -> int:
        """Get count of active trusted devices for user"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM trusted_devices 
                        WHERE user_id = %s AND is_active = TRUE
                    """, (user_id,))
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting trusted devices: {e}")
            return 0
    
    def add_trusted_device(self, user_id: str, device_id: str, device_name: str, 
                          device_type: str, user_agent: str = None, ip_address: str = None) -> Dict:
        """Add a new trusted device for the user"""
        try:
            current_count = self.get_trusted_devices_count(user_id)
            if current_count >= self.MAX_TRUSTED_DEVICES:
                return {
                    'success': False,
                    'error': f'Has alcanzado el limite de {self.MAX_TRUSTED_DEVICES} dispositivos de confianza. Elimina uno para agregar otro.',
                    'max_reached': True
                }
            
            expires_at = datetime.now() + timedelta(days=self.DEVICE_EXPIRY_DAYS)
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trusted_devices 
                        (user_id, device_id, device_name, device_type, user_agent, ip_address, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, device_id) 
                        DO UPDATE SET 
                            device_name = EXCLUDED.device_name,
                            is_active = TRUE,
                            last_used_at = NOW(),
                            expires_at = EXCLUDED.expires_at
                        RETURNING id
                    """, (user_id, device_id, device_name, device_type, user_agent, ip_address, expires_at))
                    result = cur.fetchone()
                    conn.commit()
            
            self.log_security_activity(
                user_id, 'DEVICE_ADDED',
                f'Nuevo dispositivo de confianza: {device_name} ({device_type})',
                device_id, ip_address
            )
            
            self.send_telegram_notification(
                user_id,
                f"🔐 Se agrego un nuevo dispositivo de confianza:\n"
                f"📱 {device_name}\n"
                f"🌐 IP: {ip_address or 'Desconocida'}"
            )
            
            return {
                'success': True,
                'device_id': result[0] if result else None,
                'message': 'Dispositivo agregado correctamente',
                'expires_at': expires_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error adding trusted device: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_trusted_device(self, user_id: str, device_id: str) -> Dict:
        """Remove a trusted device"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE trusted_devices 
                        SET is_active = FALSE
                        WHERE user_id = %s AND device_id = %s
                        RETURNING device_name
                    """, (user_id, device_id))
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        self.log_security_activity(
                            user_id, 'DEVICE_REMOVED',
                            f'Dispositivo eliminado: {result[0]}'
                        )
                        return {'success': True, 'message': 'Dispositivo eliminado correctamente'}
                    return {'success': False, 'error': 'Dispositivo no encontrado'}
        except Exception as e:
            logger.error(f"Error removing trusted device: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_all_devices_except_current(self, user_id: str, current_device_id: str) -> Dict:
        """Remove all trusted devices except the current one"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE trusted_devices 
                        SET is_active = FALSE
                        WHERE user_id = %s AND device_id != %s AND is_active = TRUE
                    """, (user_id, current_device_id))
                    removed_count = cur.rowcount
                    conn.commit()
            
            self.log_security_activity(
                user_id, 'ALL_DEVICES_REMOVED',
                f'Cerrada sesion en {removed_count} dispositivos'
            )
            
            return {'success': True, 'removed_count': removed_count}
        except Exception as e:
            logger.error(f"Error removing all devices: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_trusted_devices(self, user_id: str) -> List[Dict]:
        """Get list of all trusted devices for user"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, device_id, device_name, device_type, ip_address, 
                               created_at, last_used_at, expires_at
                        FROM trusted_devices 
                        WHERE user_id = %s AND is_active = TRUE
                        ORDER BY last_used_at DESC
                    """, (user_id,))
                    rows = cur.fetchall()
                    
                    devices = []
                    for row in rows:
                        devices.append({
                            'id': row[0],
                            'device_id': row[1],
                            'device_name': row[2],
                            'device_type': row[3],
                            'ip_address': row[4],
                            'created_at': row[5].isoformat() if row[5] else None,
                            'last_used_at': row[6].isoformat() if row[6] else None,
                            'expires_at': row[7].isoformat() if row[7] else None
                        })
                    return devices
        except Exception as e:
            logger.error(f"Error getting trusted devices: {e}")
            return []
    
    def register_backup_wallet(self, user_id: str, backup_wallet: str) -> Dict:
        """Register a backup wallet for emergency recovery"""
        try:
            primary = self.get_user_primary_wallet(user_id)
            if not primary:
                return {'success': False, 'error': 'Debes tener una wallet primaria registrada primero'}
            
            if primary.lower() == backup_wallet.lower():
                return {'success': False, 'error': 'La wallet de respaldo debe ser diferente a la primaria'}
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users 
                        SET backup_wallet_address = %s
                        WHERE telegram_id = %s
                    """, (backup_wallet, user_id))
                    conn.commit()
            
            self.log_security_activity(
                user_id, 'BACKUP_WALLET_REGISTERED',
                f'Wallet de respaldo registrada: {backup_wallet[:8]}...{backup_wallet[-4:]}'
            )
            
            return {'success': True, 'message': 'Wallet de respaldo registrada correctamente'}
        except Exception as e:
            logger.error(f"Error registering backup wallet: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_security_status(self, user_id: str) -> Dict:
        """Get comprehensive security status for user"""
        try:
            primary_wallet = self.get_user_primary_wallet(user_id)
            devices_count = self.get_trusted_devices_count(user_id)
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT backup_wallet_address, two_factor_enabled 
                        FROM users WHERE telegram_id = %s
                    """, (user_id,))
                    user_data = cur.fetchone()
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM security_activity_log 
                        WHERE user_id = %s AND created_at > NOW() - INTERVAL '24 hours'
                    """, (user_id,))
                    recent_activity = cur.fetchone()[0]
            
            has_backup = bool(user_data[0]) if user_data else False
            has_2fa = bool(user_data[1]) if user_data else False
            
            score = 0
            if primary_wallet:
                score += 30
            if has_2fa:
                score += 40
            if devices_count > 0:
                score += 20
            if has_backup:
                score += 10
            
            return {
                'success': True,
                'wallet_connected': bool(primary_wallet),
                'wallet_hint': f"{primary_wallet[:8]}...{primary_wallet[-4:]}" if primary_wallet else None,
                'has_backup_wallet': has_backup,
                'two_factor_enabled': has_2fa,
                'trusted_devices_count': devices_count,
                'max_devices': self.MAX_TRUSTED_DEVICES,
                'recent_activity_count': recent_activity,
                'security_score': score,
                'security_level': 'alto' if score >= 80 else ('medio' if score >= 50 else 'bajo')
            }
        except Exception as e:
            logger.error(f"Error getting security status: {e}")
            return {'success': False, 'error': str(e)}
    
    def log_security_activity(self, user_id: str, activity_type: str, description: str, 
                              device_id: str = None, ip_address: str = None, metadata: dict = None):
        """Log a security-related activity"""
        try:
            import json
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO security_activity_log 
                        (user_id, activity_type, description, device_id, ip_address, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user_id, activity_type, description, device_id, ip_address, 
                          json.dumps(metadata) if metadata else None))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error logging security activity: {e}")
    
    def get_security_activity(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent security activity for user"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT activity_type, description, device_id, ip_address, created_at
                        FROM security_activity_log 
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                    rows = cur.fetchall()
                    
                    activities = []
                    for row in rows:
                        activities.append({
                            'type': row[0],
                            'description': row[1],
                            'device_id': row[2],
                            'ip_address': row[3],
                            'created_at': row[4].isoformat() if row[4] else None
                        })
                    return activities
        except Exception as e:
            logger.error(f"Error getting security activity: {e}")
            return []
    
    def create_security_alert(self, user_id: str, alert_type: str, severity: str, description: str):
        """Create a security alert for admin review"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO security_alerts (user_id, alert_type, severity, description)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, alert_type, severity, description))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error creating security alert: {e}")
    
    def send_telegram_notification(self, user_id: str, message: str):
        """Send security notification to user via Telegram"""
        if not self.bot_token:
            logger.warning("BOT_TOKEN not configured, skipping Telegram notification")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to send Telegram notification: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def cleanup_expired_devices(self) -> int:
        """Remove expired trusted devices (run periodically)"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE trusted_devices 
                        SET is_active = FALSE
                        WHERE is_active = TRUE 
                        AND (
                            expires_at < NOW() 
                            OR last_used_at < NOW() - INTERVAL '%s days'
                        )
                    """, (self.DEVICE_EXPIRY_DAYS,))
                    removed = cur.rowcount
                    conn.commit()
            logger.info(f"Cleaned up {removed} expired devices")
            return removed
        except Exception as e:
            logger.error(f"Error cleaning up devices: {e}")
            return 0
    
    def get_all_users_devices_admin(self) -> List[Dict]:
        """Admin function: Get all users with their devices"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            u.id, u.telegram_id, u.username, u.first_name,
                            u.primary_wallet_address, u.two_factor_enabled,
                            COUNT(td.id) as devices_count,
                            MAX(td.last_used_at) as last_device_activity
                        FROM users u
                        LEFT JOIN trusted_devices td ON u.telegram_id::text = td.user_id AND td.is_active = TRUE
                        GROUP BY u.id, u.telegram_id, u.username, u.first_name, 
                                 u.primary_wallet_address, u.two_factor_enabled
                        ORDER BY last_device_activity DESC NULLS LAST
                    """)
                    rows = cur.fetchall()
                    
                    users = []
                    for row in rows:
                        users.append({
                            'id': row[0],
                            'telegram_id': row[1],
                            'username': row[2],
                            'first_name': row[3],
                            'wallet': row[4][:8] + '...' + row[4][-4:] if row[4] else None,
                            'has_2fa': bool(row[5]),
                            'devices_count': row[6],
                            'last_activity': row[7].isoformat() if row[7] else None
                        })
                    return users
        except Exception as e:
            logger.error(f"Error getting admin users list: {e}")
            return []
    
    def get_security_alerts_admin(self, unresolved_only: bool = True) -> List[Dict]:
        """Admin function: Get security alerts"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    if unresolved_only:
                        cur.execute("""
                            SELECT sa.id, sa.user_id, u.username, sa.alert_type, 
                                   sa.severity, sa.description, sa.created_at
                            FROM security_alerts sa
                            LEFT JOIN users u ON sa.user_id = u.telegram_id::text
                            WHERE sa.is_resolved = FALSE
                            ORDER BY 
                                CASE sa.severity 
                                    WHEN 'critical' THEN 1 
                                    WHEN 'high' THEN 2 
                                    WHEN 'medium' THEN 3 
                                    ELSE 4 
                                END,
                                sa.created_at DESC
                        """)
                    else:
                        cur.execute("""
                            SELECT sa.id, sa.user_id, u.username, sa.alert_type,
                                   sa.severity, sa.description, sa.created_at
                            FROM security_alerts sa
                            LEFT JOIN users u ON sa.user_id = u.telegram_id::text
                            ORDER BY sa.created_at DESC
                            LIMIT 100
                        """)
                    
                    rows = cur.fetchall()
                    alerts = []
                    for row in rows:
                        alerts.append({
                            'id': row[0],
                            'user_id': row[1],
                            'username': row[2],
                            'type': row[3],
                            'severity': row[4],
                            'description': row[5],
                            'created_at': row[6].isoformat() if row[6] else None
                        })
                    return alerts
        except Exception as e:
            logger.error(f"Error getting security alerts: {e}")
            return []
    
    def resolve_alert_admin(self, alert_id: int, resolved_by: str) -> bool:
        """Admin function: Resolve a security alert"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE security_alerts 
                        SET is_resolved = TRUE, resolved_at = NOW(), resolved_by = %s
                        WHERE id = %s
                    """, (resolved_by, alert_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    def admin_remove_user_device(self, user_id: str, device_id: str, admin_id: str) -> Dict:
        """Admin function: Remove a user's trusted device"""
        try:
            result = self.remove_trusted_device(user_id, device_id)
            if result['success']:
                self.log_security_activity(
                    user_id, 'ADMIN_DEVICE_REMOVED',
                    f'Dispositivo eliminado por administrador {admin_id}',
                    device_id
                )
                self.send_telegram_notification(
                    user_id,
                    "⚠️ Un administrador ha eliminado uno de tus dispositivos de confianza. "
                    "Si no reconoces esta accion, contacta a soporte."
                )
            return result
        except Exception as e:
            logger.error(f"Error in admin device removal: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_device_statistics_admin(self) -> Dict:
        """Admin function: Get device statistics"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM trusted_devices WHERE is_active = TRUE")
                    total_devices = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(DISTINCT user_id) FROM trusted_devices WHERE is_active = TRUE")
                    users_with_devices = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT device_type, COUNT(*) 
                        FROM trusted_devices 
                        WHERE is_active = TRUE
                        GROUP BY device_type
                    """)
                    device_types = dict(cur.fetchall())
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM security_alerts 
                        WHERE is_resolved = FALSE
                    """)
                    pending_alerts = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM wallet_failed_attempts 
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                    recent_failed_attempts = cur.fetchone()[0]
                    
                    return {
                        'success': True,
                        'total_devices': total_devices,
                        'users_with_devices': users_with_devices,
                        'device_types': device_types,
                        'pending_alerts': pending_alerts,
                        'recent_failed_attempts': recent_failed_attempts
                    }
        except Exception as e:
            logger.error(f"Error getting device statistics: {e}")
            return {'success': False, 'error': str(e)}
