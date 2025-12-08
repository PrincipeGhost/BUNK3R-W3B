"""
Utilidades compartidas para rutas y endpoints.
Este modulo contiene funciones y clases que son usadas por multiples blueprints.
"""

import html
import re
import time
import threading
import logging
from functools import wraps
from collections import defaultdict
from urllib.parse import urlparse

from flask import request, jsonify

logger = logging.getLogger(__name__)


def sanitize_error(error, context=""):
    """Sanitiza mensajes de error para no exponer detalles internos."""
    error_str = str(error).lower()
    
    error_map = {
        'connection': 'Error de conexión con el servicio',
        'timeout': 'La operación tardó demasiado',
        'permission': 'No tienes permisos para esta acción',
        'not found': 'Recurso no encontrado',
        'duplicate': 'Este registro ya existe',
        'invalid': 'Datos inválidos',
        'decrypt': 'Error al procesar contenido cifrado',
        'database': 'Error temporal del servidor',
        'psycopg2': 'Error temporal del servidor',
        'json': 'Error en el formato de datos'
    }
    
    for key, friendly_msg in error_map.items():
        if key in error_str:
            logger.error(f"[{context}] {error}")
            return friendly_msg
    
    logger.error(f"[{context}] {error}")
    return 'Ha ocurrido un error. Intenta de nuevo.'


class InputValidator:
    """Validador y sanitizador de inputs para prevenir ataques."""
    
    MAX_TEXT_LENGTH = 5000
    MAX_NAME_LENGTH = 100
    MAX_URL_LENGTH = 2048
    MAX_CAPTION_LENGTH = 2200
    
    ALLOWED_URL_SCHEMES = {'http', 'https'}
    ALLOWED_URL_HOSTS_TELEGRAM = {'t.me', 'telegram.org', 'api.telegram.org'}
    ALLOWED_URL_HOSTS_CLOUDINARY = {'res.cloudinary.com', 'cloudinary.com'}
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escapa HTML para prevenir XSS."""
        if not text:
            return ''
        return html.escape(str(text))
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """Sanitiza texto removiendo caracteres peligrosos y limitando longitud."""
        if not text:
            return ''
        
        text = str(text).strip()
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        max_len = max_length or InputValidator.MAX_TEXT_LENGTH
        if len(text) > max_len:
            text = text[:max_len]
        
        return text
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitiza nombres (personas, productos, etc.)."""
        if not name:
            return ''
        name = InputValidator.sanitize_text(name, InputValidator.MAX_NAME_LENGTH)
        name = re.sub(r'[<>"\'\\/;`]', '', name)
        return name
    
    @staticmethod
    def validate_url(url: str, allowed_hosts: set = None) -> tuple:
        """Valida una URL para prevenir SSRF."""
        if not url:
            return False, "URL vacía"
        
        if len(url) > InputValidator.MAX_URL_LENGTH:
            return False, "URL demasiado larga"
        
        try:
            parsed = urlparse(url)
            
            if parsed.scheme not in InputValidator.ALLOWED_URL_SCHEMES:
                return False, f"Esquema no permitido: {parsed.scheme}"
            
            if not parsed.netloc:
                return False, "URL sin host"
            
            host = parsed.netloc.lower().split(':')[0]
            
            private_patterns = [
                r'^localhost$',
                r'^127\.',
                r'^10\.',
                r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
                r'^192\.168\.',
                r'^0\.',
                r'\.local$',
                r'^169\.254\.',
                r'^::1$',
                r'^fc00:',
                r'^fe80:'
            ]
            
            for pattern in private_patterns:
                if re.match(pattern, host):
                    return False, "URL a dirección privada no permitida"
            
            if allowed_hosts and host not in allowed_hosts:
                return False, f"Host no permitido: {host}"
            
            return True, None
            
        except Exception as e:
            return False, f"URL inválida: {str(e)}"
    
    @staticmethod
    def validate_telegram_url(url: str) -> tuple:
        """Valida URLs de Telegram específicamente."""
        return InputValidator.validate_url(url, InputValidator.ALLOWED_URL_HOSTS_TELEGRAM)
    
    @staticmethod
    def validate_cloudinary_url(url: str) -> tuple:
        """Valida URLs de Cloudinary específicamente."""
        return InputValidator.validate_url(url, InputValidator.ALLOWED_URL_HOSTS_CLOUDINARY)
    
    @staticmethod
    def validate_file_content(file_content: bytes, expected_type: str) -> tuple:
        """Valida el contenido real del archivo usando magic bytes."""
        MAGIC_BYTES = {
            'image/jpeg': [b'\xff\xd8\xff'],
            'image/png': [b'\x89PNG\r\n\x1a\n'],
            'image/gif': [b'GIF87a', b'GIF89a'],
            'image/webp': [b'RIFF'],
            'video/mp4': [b'\x00\x00\x00\x18ftyp', b'\x00\x00\x00\x1cftyp', b'\x00\x00\x00\x20ftyp', b'ftyp'],
            'video/webm': [b'\x1a\x45\xdf\xa3']
        }
        
        if not file_content or len(file_content) < 8:
            return False, "Archivo vacío o muy pequeño"
        
        for mime_type, signatures in MAGIC_BYTES.items():
            for sig in signatures:
                if file_content[:len(sig)] == sig:
                    if expected_type and not mime_type.startswith(expected_type.split('/')[0]):
                        return False, f"Tipo esperado {expected_type} pero encontrado {mime_type}"
                    return True, mime_type
        
        return False, "Tipo de archivo no reconocido"
    
    @staticmethod
    def validate_tracking_id(tracking_id: str) -> tuple:
        """Valida formato de tracking ID."""
        if not tracking_id:
            return False, "Tracking ID vacío"
        
        tracking_id = str(tracking_id).strip().upper()
        
        if not re.match(r'^[A-Z0-9\-_]{5,50}$', tracking_id):
            return False, "Formato de tracking ID inválido"
        
        return True, tracking_id
    
    @staticmethod
    def validate_caption(caption: str) -> str:
        """Valida y sanitiza caption de publicaciones."""
        if not caption:
            return ''
        caption = InputValidator.sanitize_text(caption, InputValidator.MAX_CAPTION_LENGTH)
        return caption


input_validator = InputValidator()


class RateLimiter:
    """Sistema de rate limiting para proteger endpoints críticos."""
    
    def __init__(self):
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
        self._cleanup_interval = 60
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Limpia entradas antiguas del registro."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        keys_to_delete = []
        
        for key, timestamps in list(self._requests.items()):
            self._requests[key] = [t for t in timestamps if current_time - t < 3600]
            if not self._requests[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._requests[key]
    
    def is_rate_limited(self, key: str, limit: int, window: int) -> tuple:
        """Verifica si una clave está rate-limited."""
        current_time = time.time()
        
        with self._lock:
            self._cleanup_old_entries()
            
            timestamps = self._requests[key]
            valid_timestamps = [t for t in timestamps if current_time - t < window]
            self._requests[key] = valid_timestamps
            
            if len(valid_timestamps) >= limit:
                oldest = min(valid_timestamps) if valid_timestamps else current_time
                reset_time = int(oldest + window - current_time)
                return True, 0, reset_time
            
            self._requests[key].append(current_time)
            remaining = limit - len(self._requests[key])
            return False, remaining, window
    
    def get_usage(self, key: str, window: int) -> int:
        """Obtiene el número de requests actuales para una clave."""
        current_time = time.time()
        
        with self._lock:
            timestamps = self._requests.get(key, [])
            valid_timestamps = [t for t in timestamps if current_time - t < window]
            return len(valid_timestamps)


rate_limiter = RateLimiter()

RATE_LIMITS = {
    'posts_create': {'limit': 10, 'window': 60},
    'posts_like': {'limit': 60, 'window': 60},
    'comments_create': {'limit': 30, 'window': 60},
    'follow': {'limit': 30, 'window': 60},
    'payment_verify': {'limit': 20, 'window': 60},
    '2fa_verify': {'limit': 5, 'window': 300},
    'vn_purchase': {'limit': 5, 'window': 60},
    'login': {'limit': 10, 'window': 300},
    'price_check': {'limit': 60, 'window': 60},
    'balance_check': {'limit': 60, 'window': 60},
    'calculate': {'limit': 30, 'window': 60},
    'exchange': {'limit': 30, 'window': 60},
    'b3c_verify': {'limit': 10, 'window': 60},
    'default': {'limit': 100, 'window': 60}
}


def rate_limit(action: str = 'default', use_ip: bool = False):
    """Decorador de rate limiting para endpoints Flask."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limits = RATE_LIMITS.get(action, RATE_LIMITS['default'])
            limit = limits['limit']
            window = limits['window']
            
            if use_ip:
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                if client_ip:
                    client_ip = client_ip.split(',')[0].strip()
                key = f"{action}:{client_ip}"
            else:
                user = getattr(request, 'telegram_user', None)
                if user:
                    user_id = str(user.get('id', 'anonymous'))
                else:
                    user_id = request.headers.get('X-Forwarded-For', request.remote_addr)
                    if user_id:
                        user_id = user_id.split(',')[0].strip()
                key = f"{action}:{user_id}"
            
            is_limited, remaining, reset_time = rate_limiter.is_rate_limited(key, limit, window)
            
            if is_limited:
                response = jsonify({
                    'error': 'Demasiadas solicitudes. Intenta de nuevo más tarde.',
                    'retry_after': reset_time
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(reset_time)
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + reset_time)
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
