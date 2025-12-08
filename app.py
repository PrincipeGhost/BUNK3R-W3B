"""
Telegram Web App para Sistema de Tracking de Paquetes
Backend Flask con validación de Telegram Web Apps
"""

import os
import sys
import hmac
import hashlib
import json
import logging
import uuid
import base64
import io
import re
import html
import time
import threading
import requests
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import parse_qs, unquote, urlparse
from collections import defaultdict

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response, session
from flask_session import Session
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
import psycopg2.extensions
import pyotp
import qrcode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracking.database import DatabaseManager
from tracking.models import Tracking
from tracking.email_service import EmailService, prepare_tracking_email_data, send_tracking_email
from tracking.security import SecurityManager
from tracking.encryption import encryption_manager
from tracking.cloudinary_service import cloudinary_service
from tracking.smspool_service import SMSPoolService, VirtualNumbersManager
from tracking.telegram_service import telegram_service

from logging.handlers import RotatingFileHandler
from flask import g

LOGS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_FOLDER, exist_ok=True)

class RequestContextFilter(logging.Filter):
    """Inyecta request_id, user_id e ip en cada log record."""
    def filter(self, record):
        try:
            from flask import request, has_request_context
            if has_request_context():
                record.request_id = getattr(request, 'request_id', '-')
                record.client_ip = getattr(request, 'client_ip', request.headers.get('X-Forwarded-For', request.remote_addr))
                record.user_id = getattr(request, 'telegram_user', {}).get('id', '-') if hasattr(request, 'telegram_user') else '-'
            else:
                record.request_id = '-'
                record.client_ip = '-'
                record.user_id = '-'
        except Exception:
            record.request_id = '-'
            record.client_ip = '-'
            record.user_id = '-'
        return True

class JSONFormatter(logging.Formatter):
    """Formato JSON estructurado para logs."""
    def format(self, record):
        log_obj = {
            'time': datetime.now().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', '-'),
            'ip': getattr(record, 'client_ip', '-'),
            'user_id': str(getattr(record, 'user_id', '-'))
        }
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

context_filter = RequestContextFilter()

file_handler = RotatingFileHandler(
    os.path.join(LOGS_FOLDER, 'app.log'),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(JSONFormatter())
file_handler.setLevel(logging.INFO)
file_handler.addFilter(context_filter)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
))
console_handler.setLevel(logging.INFO)
console_handler.addFilter(context_filter)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

app = Flask(__name__)

IS_PRODUCTION = os.environ.get('REPL_DEPLOYMENT', '') == '1'
IS_DEPLOYED = os.environ.get('REPL_SLUG', '') != '' and os.environ.get('REPL_OWNER', '') != ''

admin_token = os.environ.get('ADMIN_TOKEN', '')
if IS_PRODUCTION and not admin_token:
    logger.critical("SECURITY ERROR: ADMIN_TOKEN must be set in production. Server cannot start securely.")
    raise ValueError("ADMIN_TOKEN environment variable is required in production deployment")
elif not admin_token:
    admin_token = 'dev-secret-key-only-for-development'
    if IS_DEPLOYED:
        logger.warning("Using development secret key. Set ADMIN_TOKEN for production.")
    
app.secret_key = admin_token

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

SESSION_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.flask_sessions')
os.makedirs(SESSION_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_FOLDER
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'bunk3r_session:'
app.config['SESSION_FILE_THRESHOLD'] = 500

app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION or IS_DEPLOYED
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if (IS_PRODUCTION or IS_DEPLOYED) else 'Lax'

server_session = Session(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_telegram_photo(photo_url: str) -> str:
    """Descarga la foto de Telegram y la convierte a base64 con validación SSRF."""
    try:
        if 'input_validator' in globals():
            is_valid, error = input_validator.validate_url(photo_url)
            if not is_valid:
                logger.warning(f"Invalid Telegram photo URL blocked: {error}")
                return None
        
        import requests
        response = requests.get(photo_url, timeout=10, allow_redirects=False)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'image/jpeg')
            if 'image' in content_type:
                if 'input_validator' in globals():
                    is_valid_content, detected_type = input_validator.validate_file_content(
                        response.content[:1024], 'image'
                    )
                    if not is_valid_content:
                        logger.warning(f"Invalid file content in Telegram photo: {detected_type}")
                        return None
                
                image_data = base64.b64encode(response.content).decode('utf-8')
                return f"data:{content_type};base64,{image_data}"
        return None
    except Exception as e:
        logger.error(f"Error downloading Telegram photo: {e}")
        return None

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '')
OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '')
USER_TELEGRAM_ID = os.environ.get('USER_TELEGRAM_ID', '')

DEMO_2FA_SECRET = os.environ.get('DEMO_2FA_SECRET', pyotp.random_base32())

def get_demo_2fa_code():
    """Genera y devuelve el código 2FA actual para modo demo."""
    totp = pyotp.TOTP(DEMO_2FA_SECRET, interval=60)
    return totp.now()

HIDE_2FA_LOGS = os.environ.get('HIDE_2FA_LOGS', 'false').lower() == 'true'

def log_demo_2fa_code(code: str, client_ip: str, extra_msg: str = None):
    """Loguea el código 2FA de forma segura (oculto en producción)."""
    if IS_PRODUCTION or HIDE_2FA_LOGS:
        logger.info(f"🔐 Demo 2FA code generated for IP: {client_ip}")
    else:
        logger.info(f"═══════════════════════════════════════════════")
        logger.info(f"🔐 DEMO 2FA CODE: {code}")
        logger.info(f"   Valid for 60 seconds | IP: {client_ip}")
        if extra_msg:
            logger.info(f"   {extra_msg}")
        logger.info(f"═══════════════════════════════════════════════")

def verify_demo_2fa_code(code: str) -> bool:
    """Verifica el código 2FA para modo demo."""
    totp = pyotp.TOTP(DEMO_2FA_SECRET, interval=60)
    return totp.verify(code, valid_window=1)

def get_demo_session_token(client_ip: str) -> str:
    """Genera un token de sesión para el modo demo usando Flask-Session persistente."""
    import secrets
    token = secrets.token_urlsafe(32)
    session['demo_2fa_token'] = token
    session['demo_2fa_ip'] = client_ip
    session['demo_2fa_created_at'] = datetime.now().isoformat()
    session['demo_2fa_valid'] = True
    session.permanent = True
    return token

def verify_demo_session(token: str = None, client_ip: str = None) -> bool:
    """Verifica si la sesión demo es válida usando Flask-Session persistente.
    
    La validación funciona de dos formas:
    1. Si hay una sesión Flask válida, se valida directamente desde la cookie
    2. Si se proporciona un token, se compara con el almacenado en la sesión
    
    Args:
        token: Token opcional desde header X-Demo-Session (para compatibilidad)
        client_ip: IP del cliente para validación de seguridad
    """
    stored_token = session.get('demo_2fa_token')
    if not stored_token:
        return False
    
    if not session.get('demo_2fa_valid', False):
        return False
    
    if token and token != stored_token:
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
        created_at = datetime.fromisoformat(created_at_str)
        if (datetime.now() - created_at).total_seconds() > 7200:
            invalidate_demo_session()
            return False
    
    return True

def invalidate_demo_session():
    """Invalida la sesión 2FA demo actual."""
    session.pop('demo_2fa_token', None)
    session.pop('demo_2fa_ip', None)
    session.pop('demo_2fa_created_at', None)
    session.pop('demo_2fa_valid', None)

try:
    db_manager = DatabaseManager()
    logger.info("Database connection established")
    security_manager = SecurityManager(db_manager)
    security_manager.initialize_tables()
    logger.info("Security manager initialized")
    db_manager.initialize_virtual_numbers_tables()
    logger.info("Virtual numbers tables initialized")
    db_manager.initialize_payments_tables()
    logger.info("Payments tables initialized")
    db_manager.initialize_b3c_tables()
    logger.info("B3C tables initialized")
    vn_manager = VirtualNumbersManager(db_manager)
    logger.info("Virtual numbers manager initialized")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    db_manager = None
    security_manager = None
    vn_manager = None

STATUS_MAP = {
    'RETENIDO': {'icon': '📦', 'label': 'Retenido', 'color': '#f39c12'},
    'EN_TRANSITO': {'icon': '🚚', 'label': 'En Camino', 'color': '#3498db'},
    'ENTREGADO': {'icon': '✅', 'label': 'Entregado', 'color': '#27ae60'},
    'CONFIRMAR_PAGO': {'icon': '💰', 'label': 'Confirmar Pago', 'color': '#e74c3c'}
}

DELAY_REASONS = [
    {"id": "customs", "text": "Problemas en aduana", "days": 3},
    {"id": "high_demand", "text": "Alta demanda", "days": 2},
    {"id": "weather", "text": "Condiciones climáticas adversas", "days": 1},
    {"id": "logistics", "text": "Problemas logísticos", "days": 2},
    {"id": "documentation", "text": "Documentación pendiente", "days": 3},
    {"id": "verification", "text": "Verificación de seguridad", "days": 1},
    {"id": "address", "text": "Dirección incorrecta", "days": 2},
    {"id": "recipient_absent", "text": "Destinatario ausente", "days": 1}
]


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
        """
        Valida una URL para prevenir SSRF.
        Returns: (is_valid: bool, error_message: str)
        """
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
        """
        Valida el contenido real del archivo usando magic bytes.
        Returns: (is_valid: bool, detected_type: str)
        """
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
        """
        Verifica si una clave está rate-limited.
        
        Args:
            key: Identificador único (user_id, IP, etc.)
            limit: Número máximo de requests permitidos
            window: Ventana de tiempo en segundos
            
        Returns:
            (is_limited: bool, remaining: int, reset_time: int)
        """
        import time
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
        import time
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
    'default': {'limit': 100, 'window': 60}
}


def rate_limit(action: str = 'default', use_ip: bool = False):
    """
    Decorador de rate limiting para endpoints Flask.
    
    Args:
        action: Tipo de acción para determinar límites
        use_ip: Si usar IP en lugar de user_id como identificador
    """
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
                logger.warning(f"Rate limit exceeded for {key}")
                return response
            
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            
            return response
        return decorated_function
    return decorator


def verify_origin_referer() -> tuple:
    """
    Verifica Origin/Referer para protección CSRF.
    Returns: (is_valid: bool, error_message: str or None)
    """
    if not IS_PRODUCTION:
        return True, None
    
    origin = request.headers.get('Origin', '')
    referer = request.headers.get('Referer', '')
    host = request.host_url.rstrip('/')
    
    allowed_origins = {
        host,
        'https://web.telegram.org',
        'https://telegram.org'
    }
    
    if origin:
        origin_base = origin.rstrip('/')
        if origin_base not in allowed_origins and not origin_base.endswith('.telegram.org'):
            return False, f"Origin no permitido: {origin}"
    
    if referer:
        referer_host = urlparse(referer).netloc
        host_only = request.host.split(':')[0]
        if referer_host not in [host_only, 'web.telegram.org', 'telegram.org'] and not referer_host.endswith('.telegram.org'):
            return False, f"Referer no permitido: {referer_host}"
    
    return True, None


def csrf_protect(f):
    """
    Decorador para protección CSRF en endpoints POST/PUT/DELETE.
    Verifica Origin/Referer y requiere autenticación válida.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            is_valid, error = verify_origin_referer()
            if not is_valid:
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                logger.warning(f"CSRF: Blocked request from IP {client_ip}: {error}")
                return jsonify({
                    'error': 'Solicitud no autorizada',
                    'code': 'CSRF_FAILED'
                }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def validate_telegram_webapp_data(init_data: str):
    """Valida los datos de Telegram Web App segun la documentacion oficial."""
    if not init_data or not BOT_TOKEN:
        return None
    
    try:
        parsed_data = dict(parse_qs(init_data))
        parsed_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
        
        if 'hash' not in parsed_data:
            logger.warning("No hash in init_data")
            return None
        
        received_hash = parsed_data.pop('hash')
        
        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            logger.warning("Hash mismatch in Telegram validation")
            return None
        
        if 'user' in parsed_data:
            user_str = parsed_data['user']
            if isinstance(user_str, str):
                user_data = json.loads(unquote(user_str))
                parsed_data['user'] = user_data
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        return None


def is_owner(user_id: int) -> bool:
    """Verifica si el usuario es el owner."""
    try:
        owner_id = int(OWNER_TELEGRAM_ID) if OWNER_TELEGRAM_ID else 0
        return user_id == owner_id
    except (ValueError, TypeError) as e:
        logger.debug(f"Error checking owner: {e}")
        return False

def is_test_user(user_id: int) -> bool:
    """Verifica si el usuario es el usuario de prueba."""
    try:
        test_user_id = int(USER_TELEGRAM_ID) if USER_TELEGRAM_ID else 0
        return user_id == test_user_id
    except (ValueError, TypeError) as e:
        logger.debug(f"Error checking test user: {e}")
        return False

def is_allowed_user(user_id: int) -> bool:
    """Verifica si el usuario tiene permiso de acceso (owner o usuario de prueba)."""
    return is_owner(user_id) or is_test_user(user_id)


def require_telegram_auth(f):
    """Decorador para requerir autenticación de Telegram o modo demo con 2FA."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        demo_header_present = request.headers.get('X-Demo-Mode') == 'true'
        
        if demo_header_present and IS_PRODUCTION:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            logger.warning(f"SECURITY: Demo mode attempt blocked in production from IP: {client_ip}")
            return jsonify({'error': 'Modo demo no disponible', 'code': 'DEMO_DISABLED'}), 403
        
        if demo_header_present and not IS_PRODUCTION:
            demo_session_token = request.headers.get('X-Demo-Session')
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if not verify_demo_session(demo_session_token, client_ip):
                return jsonify({
                    'error': 'Se requiere autenticación para modo demo',
                    'code': 'DEMO_2FA_REQUIRED',
                    'requiresDemo2FA': True
                }), 401
            
            request.telegram_user = {'id': 0, 'first_name': 'Demo', 'username': 'demo_user'}
            request.telegram_data = {}
            request.is_owner = True
            request.is_demo = True
            return f(*args, **kwargs)
        
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram inválidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado', 'code': 'NO_USER'}), 401
        
        if not is_allowed_user(user_id):
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NOT_ALLOWED'}), 403
        
        request.telegram_user = user
        request.telegram_data = validated_data
        request.is_owner = is_owner(user_id)
        request.is_test_user = is_test_user(user_id)
        request.is_demo = False
        
        return f(*args, **kwargs)
    return decorated_function


def require_owner(f):
    """Decorador para funciones que solo el owner puede usar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(request, 'is_owner', False):
            return jsonify({'error': 'Función solo disponible para el owner'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_telegram_user(f):
    """Decorador para funciones que cualquier usuario autenticado de Telegram puede usar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        demo_header_present = request.headers.get('X-Demo-Mode') == 'true'
        
        if demo_header_present and IS_PRODUCTION:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            logger.warning(f"SECURITY: Demo mode attempt blocked in production from IP: {client_ip}")
            return jsonify({'error': 'Modo demo no disponible', 'code': 'DEMO_DISABLED'}), 403
        
        if demo_header_present and not IS_PRODUCTION:
            demo_session_token = request.headers.get('X-Demo-Session')
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if not verify_demo_session(demo_session_token, client_ip):
                return jsonify({
                    'error': 'Se requiere autenticación para modo demo',
                    'code': 'DEMO_2FA_REQUIRED',
                    'requiresDemo2FA': True
                }), 401
            
            request.telegram_user = {'id': 0, 'first_name': 'Demo', 'username': 'demo_user'}
            request.telegram_data = {}
            request.is_owner = True
            request.is_demo = True
            return f(*args, **kwargs)
        
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Acceso no autorizado', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram inválidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado', 'code': 'NO_USER'}), 401
        
        request.telegram_user = user
        request.telegram_data = validated_data
        request.is_owner = is_owner(user_id)
        request.is_demo = False
        
        return f(*args, **kwargs)
    return decorated_function


CSRF_EXEMPT_ENDPOINTS = {
    'static',
    'index',
    'health_check',
    'tonconnect_manifest',
    'get_b3c_price',
    'get_b3c_network',
    'api_b3c_calculate',
    'calculate_b3c_sell',
    'public_posts_feed',
    'public_user_profile',
    'public_comments'
}


@app.before_request
def add_request_id():
    """Añade un request_id único a cada petición para trazabilidad."""
    request.request_id = str(uuid.uuid4())[:8]
    request.client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)


@app.before_request
def csrf_middleware():
    """Middleware global para verificación CSRF en métodos que modifican datos."""
    if request.method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
        return None
    
    if request.endpoint in CSRF_EXEMPT_ENDPOINTS:
        return None
    
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    
    is_valid, error = verify_origin_referer()
    if not is_valid:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        logger.warning(f"CSRF Middleware: Blocked {request.method} to {request.path} from IP {client_ip}: {error}")
        return jsonify({
            'error': 'Solicitud no autorizada',
            'code': 'CSRF_FAILED'
        }), 403
    
    return None


CSP_ENABLED = os.environ.get('CSP_ENABLED', 'true').lower() == 'true'
CSP_REPORT_ONLY = os.environ.get('CSP_REPORT_ONLY', 'false').lower() == 'true'
CSP_EXTRA_SOURCES = os.environ.get('CSP_EXTRA_SOURCES', '')

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://telegram.org https://*.telegram.org; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: https: blob:; "
    "connect-src 'self' https://api.telegram.org https://*.ton.org https://*.toncenter.com https://toncenter.com wss://* https://api.coingecko.com https://api.ston.fi https://*.cloudinary.com https://bridge.tonapi.io; "
    "frame-src 'self' https://telegram.org https://*.telegram.org; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

@app.after_request
def add_security_headers(response):
    """Agregar headers de seguridad a todas las respuestas."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    if CSP_ENABLED:
        csp = os.environ.get('CSP_POLICY', DEFAULT_CSP)
        if CSP_EXTRA_SOURCES:
            csp = csp.rstrip(';') + ' ' + CSP_EXTRA_SOURCES + ';'
        
        header_name = 'Content-Security-Policy-Report-Only' if CSP_REPORT_ONLY else 'Content-Security-Policy'
        response.headers[header_name] = csp
    
    if IS_PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    if request.endpoint and not request.endpoint.startswith('static'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    
    return response


@app.route('/static/tonconnect-manifest.json')
def tonconnect_manifest():
    """Generate TON Connect manifest dynamically based on current host."""
    host = request.host_url.rstrip('/')
    manifest = {
        "url": host,
        "name": "BUNK3R",
        "iconUrl": f"{host}/static/images/logo.png",
        "termsOfUseUrl": f"{host}/terms",
        "privacyPolicyUrl": f"{host}/privacy"
    }
    return jsonify(manifest)


@app.route('/')
def index():
    """Página principal - siempre carga, la validación se hace en el frontend con el SDK de Telegram."""
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    """Endpoint para verificar que el servidor está listo (útil para monitoreo externo)."""
    db_ready = False
    
    if db_manager:
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            db_ready = True
        except Exception as e:
            logger.error(f"Health check database error: {e}")
            db_ready = False
    
    if not db_ready:
        return jsonify({
            'ready': False,
            'database': False,
            'timestamp': datetime.now().isoformat()
        }), 503
    
    return jsonify({
        'ready': True,
        'database': True,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/proxy')
def browser_proxy():
    """Proxy para cargar páginas externas en el multi-browser evitando X-Frame-Options."""
    url = request.args.get('url', '')
    if not url:
        return '<html><body style="background:#1a1a1a;color:#888;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;text-align:center;padding:20px;"><p>Ingresa una URL para navegar<br><small style="color:#666;">Ejemplo: github.com, wikipedia.org</small></p></body></html>', 200
    
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc or '.' not in parsed.netloc:
            return f'<html><body style="background:#1a1a1a;color:#f44;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;text-align:center;padding:20px;"><p>URL incompleta<br><small style="color:#888;">Escribe la URL completa, ejemplo:<br>github.com, wikipedia.org</small></p></body></html>', 400
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        content_type = resp.headers.get('Content-Type', 'text/html')
        
        if 'text/html' in content_type:
            content = resp.text
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            base_tag = f'<base href="{base_url}/">'
            if '<head>' in content:
                content = content.replace('<head>', f'<head>{base_tag}', 1)
            elif '<HEAD>' in content:
                content = content.replace('<HEAD>', f'<HEAD>{base_tag}', 1)
            else:
                content = base_tag + content
            
            response = Response(content, status=resp.status_code)
            response.headers['Content-Type'] = content_type
        else:
            response = Response(resp.content, status=resp.status_code)
            response.headers['Content-Type'] = content_type
        
        return response
        
    except requests.exceptions.Timeout:
        return '<html><body style="background:#1a1a1a;color:#f44;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;text-align:center;padding:20px;"><p>Tiempo de espera agotado<br><small style="color:#888;">El sitio tardó demasiado en responder</small></p></body></html>', 504
    except requests.exceptions.ConnectionError:
        return f'<html><body style="background:#1a1a1a;color:#f44;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;text-align:center;padding:20px;"><p>No se pudo conectar<br><small style="color:#888;">Verifica que la URL esté completa<br>Ejemplo: github.com (no solo github)</small></p></body></html>', 502
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return f'<html><body style="background:#1a1a1a;color:#f44;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;text-align:center;padding:20px;"><p>Error al cargar<br><small style="color:#888;">{str(e)}</small></p></body></html>', 500


# ============================================================
# ENDPOINTS PARA 2FA (Two-Factor Authentication)
# ============================================================

@app.route('/api/demo/2fa/verify', methods=['POST'])
def verify_demo_2fa():
    """Verificar contraseña para modo demo."""
    if IS_PRODUCTION:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        data = request.get_json() or {}
        password = data.get('code', '').strip() or data.get('password', '').strip()
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Contraseña requerida'
            }), 400
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        demo_password = os.environ.get('ADMIN_TOKEN', '110917')
        
        if password == demo_password:
            session_token = get_demo_session_token(client_ip)
            logger.info(f"✅ Demo login successful from IP: {client_ip}")
            return jsonify({
                'success': True,
                'sessionToken': session_token,
                'message': 'Acceso concedido'
            })
        else:
            logger.warning(f"❌ Demo login failed from IP: {client_ip}")
            return jsonify({
                'success': False,
                'error': 'Contraseña incorrecta'
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying demo password: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


@app.route('/api/demo/2fa/logout', methods=['POST'])
def demo_2fa_logout():
    """Cerrar sesión del modo demo 2FA."""
    if IS_PRODUCTION:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if session.get('demo_2fa_valid'):
            invalidate_demo_session()
            logger.info(f"🚪 Demo 2FA session closed from IP: {client_ip}")
            return jsonify({
                'success': True,
                'message': 'Sesión demo cerrada correctamente'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No hay sesión activa'
            })
            
    except Exception as e:
        logger.error(f"Error closing demo 2FA session: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


@app.route('/api/admin/2fa/verify', methods=['POST'])
def verify_admin_2fa():
    """Verificar código 2FA para el owner que accede desde Telegram al panel admin."""
    try:
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Se requieren datos de Telegram', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram inválidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado'}), 401
        
        if not is_owner(user_id):
            return jsonify({'error': 'Solo disponible para el administrador'}), 403
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6:
            return jsonify({
                'success': False,
                'error': 'Código debe ser de 6 dígitos'
            }), 400
        
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        secret = db_manager.get_user_totp_secret(str(user_id))
        
        if not secret:
            return jsonify({
                'success': False,
                'error': '2FA no está configurado para esta cuenta'
            }), 400
        
        totp = pyotp.TOTP(secret, interval=30)
        is_valid = totp.verify(code, valid_window=1)
        
        if not is_valid:
            totp_60 = pyotp.TOTP(secret, interval=60)
            is_valid = totp_60.verify(code, valid_window=1)
        
        if is_valid:
            import secrets as sec_module
            admin_session_token = sec_module.token_urlsafe(32)
            session['admin_2fa_token'] = admin_session_token
            session['admin_2fa_user_id'] = str(user_id)
            session['admin_2fa_created_at'] = datetime.now().isoformat()
            session['admin_2fa_valid'] = True
            session.permanent = True
            
            db_manager.update_2fa_verified_time(str(user_id))
            
            logger.info(f"✅ Admin 2FA verified for owner {user_id}")
            return jsonify({
                'success': True,
                'sessionToken': admin_session_token,
                'message': 'Verificación exitosa'
            })
        else:
            logger.warning(f"❌ Admin 2FA failed for owner {user_id}")
            return jsonify({
                'success': False,
                'error': 'Código incorrecto'
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying admin 2FA: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


def ensure_user_exists(user_data, db_mgr):
    """Asegura que el usuario exista en la base de datos"""
    user_id = str(user_data.get('id'))
    try:
        db_mgr.get_or_create_user(
            user_id=user_id,
            username=user_data.get('username', 'demo_user'),
            first_name=user_data.get('first_name', 'Demo'),
            last_name=user_data.get('last_name', ''),
            telegram_id=int(user_id) if user_id.isdigit() else 0
        )
        return True
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return False


@app.route('/api/2fa/status', methods=['POST'])
@require_telegram_user
def get_2fa_status():
    """Obtener estado de 2FA del usuario"""
    user_id = str(request.telegram_user.get('id'))
    
    # En modo demo, no requerir verificación 2FA
    if getattr(request, 'is_demo', False) or user_id == '0':
        return jsonify({
            'success': True,
            'enabled': False,
            'configured': False,
            'sessionValid': True,
            'requiresVerification': False
        })
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    ensure_user_exists(request.telegram_user, db_manager)
    
    status = db_manager.get_user_2fa_status(user_id)
    session_valid = False
    
    if status['enabled']:
        session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    return jsonify({
        'success': True,
        'enabled': status['enabled'],
        'configured': status['has_secret'],
        'sessionValid': session_valid,
        'requiresVerification': status['enabled'] and not session_valid
    })


@app.route('/api/2fa/setup', methods=['POST'])
@require_telegram_user
def setup_2fa():
    """Configurar 2FA - genera secreto TOTP y código QR"""
    user_id = str(request.telegram_user.get('id'))
    username = request.telegram_user.get('username', 'user')
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    existing_secret = db_manager.get_user_totp_secret(user_id)
    
    if existing_secret:
        secret = existing_secret
    else:
        secret = pyotp.random_base32()
        if not db_manager.setup_2fa(user_id, secret):
            return jsonify({'error': 'Failed to setup 2FA'}), 500
    
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=f"@{username}",
        issuer_name="BUNK3R"
    )
    
    img = qrcode.make(provisioning_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'secret': secret,
        'qrCode': f"data:image/png;base64,{qr_base64}",
        'message': 'Escanea el código QR con Google Authenticator'
    })


@app.route('/api/2fa/verify', methods=['POST'])
@require_telegram_user
@rate_limit('2fa_verify')
def verify_2fa():
    """Verificar código TOTP"""
    user_id = str(request.telegram_user.get('id'))
    data = request.get_json()
    code = data.get('code', '').strip()
    enable_2fa = data.get('enable', False)
    
    if not code or len(code) != 6:
        return jsonify({
            'success': False,
            'error': 'Código inválido. Debe ser de 6 dígitos.'
        }), 400
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    secret = db_manager.get_user_totp_secret(user_id)
    
    if not secret:
        return jsonify({
            'success': False,
            'error': '2FA no está configurado. Configure primero.'
        }), 400
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)
    
    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Código incorrecto. Intenta de nuevo.'
        }), 401
    
    if enable_2fa:
        db_manager.enable_2fa(user_id)
    else:
        db_manager.update_2fa_verified_time(user_id)
    
    return jsonify({
        'success': True,
        'message': '2FA habilitado correctamente' if enable_2fa else 'Verificación exitosa',
        'verified': True
    })


@app.route('/api/2fa/session', methods=['POST'])
@require_telegram_user
def check_2fa_session():
    """Verificar si la sesión 2FA sigue activa (para mantener sesión con actividad)"""
    user_id = str(request.telegram_user.get('id'))
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    status = db_manager.get_user_2fa_status(user_id)
    
    if not status['enabled']:
        return jsonify({
            'success': True,
            'sessionValid': True,
            'requiresVerification': False
        })
    
    session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    return jsonify({
        'success': True,
        'sessionValid': session_valid,
        'requiresVerification': not session_valid
    })


@app.route('/api/2fa/refresh', methods=['POST'])
@require_telegram_user
def refresh_2fa_session():
    """Actualizar timestamp de sesión 2FA (llamar con actividad del usuario)"""
    user_id = str(request.telegram_user.get('id'))
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    status = db_manager.get_user_2fa_status(user_id)
    
    if not status['enabled']:
        return jsonify({'success': True, 'message': '2FA not enabled'})
    
    session_valid = db_manager.check_2fa_session_valid(user_id, timeout_minutes=10)
    
    if session_valid:
        db_manager.update_2fa_verified_time(user_id)
        return jsonify({'success': True, 'sessionExtended': True})
    
    return jsonify({
        'success': False,
        'sessionExpired': True,
        'requiresVerification': True
    })


@app.route('/api/2fa/disable', methods=['POST'])
@require_telegram_user
def disable_2fa():
    """Desactivar 2FA (requiere código válido)"""
    user_id = str(request.telegram_user.get('id'))
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code or len(code) != 6:
        return jsonify({
            'success': False,
            'error': 'Se requiere código de 6 dígitos para desactivar 2FA'
        }), 400
    
    if not db_manager:
        return jsonify({'error': 'Database not available'}), 500
    
    secret = db_manager.get_user_totp_secret(user_id)
    
    if not secret:
        return jsonify({
            'success': False,
            'error': '2FA no está configurado'
        }), 400
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)
    
    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Código incorrecto'
        }), 401
    
    if db_manager.disable_2fa(user_id):
        return jsonify({
            'success': True,
            'message': '2FA desactivado correctamente'
        })
    
    return jsonify({
        'success': False,
        'error': 'Error al desactivar 2FA'
    }), 500


@app.route('/api/validate', methods=['POST'])
def validate_user():
    """Valida el usuario de Telegram y verifica permisos."""
    data = request.get_json()
    init_data = data.get('initData', '')
    
    if not init_data:
        return jsonify({
            'valid': False,
            'error': 'No se proporcionaron datos de Telegram'
        }), 400
    
    validated_data = validate_telegram_webapp_data(init_data)
    
    if not validated_data:
        return jsonify({
            'valid': False,
            'error': 'Datos de Telegram inválidos'
        }), 401
    
    user = validated_data.get('user', {})
    user_id = user.get('id')
    
    if not user_id:
        return jsonify({
            'valid': False,
            'error': 'Usuario no identificado'
        }), 401
    
    owner_status = is_owner(user_id)
    test_user_status = is_test_user(user_id)
    
    if not owner_status and not test_user_status:
        return jsonify({
            'valid': False,
            'error': 'Acceso no autorizado',
            'isOwner': False
        }), 403
    
    photo_url = user.get('photo_url')
    
    if db_manager:
        try:
            logger.info(f"Creating/updating user {user_id} in database")
            created_user = db_manager.get_or_create_user(
                user_id=str(user_id),
                username=user.get('username'),
                first_name=user.get('first_name'),
                last_name=user.get('last_name'),
                telegram_id=user_id
            )
            logger.info(f"User created/updated: {created_user}")
            
            if photo_url:
                avatar_data = download_telegram_photo(photo_url)
                if avatar_data:
                    db_manager.update_user_avatar_data(str(user_id), avatar_data)
                    local_avatar_url = f"/api/avatar/{user_id}"
                    db_manager.update_user_profile(str(user_id), avatar_url=local_avatar_url)
                    logger.info(f"Downloaded and saved Telegram photo for user {user_id}")
                else:
                    db_manager.update_user_profile(str(user_id), avatar_url=photo_url)
                    logger.info(f"Using direct Telegram URL for user {user_id}: {photo_url}")
            
            if owner_status:
                db_manager.initialize_bot_types()
                db_manager.assign_owner_bots(user_id)
                logger.info(f"Assigned owner bots to user {user_id}")
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
    
    return jsonify({
        'valid': True,
        'user': {
            'id': user_id,
            'firstName': user.get('first_name', ''),
            'lastName': user.get('last_name', ''),
            'username': user.get('username', ''),
            'languageCode': user.get('language_code', 'es'),
            'photoUrl': photo_url
        },
        'isOwner': owner_status,
        'isTestUser': test_user_status
    })


@app.route('/api/trackings', methods=['GET'])
@require_telegram_auth
def get_trackings():
    """Obtener lista de trackings."""
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = request.telegram_user.get('id')
        owner = is_owner(user_id)
        
        if status_filter:
            trackings = db_manager.get_trackings_by_status(status_filter, user_id, owner)
        else:
            trackings = db_manager.get_all_trackings(admin_id=user_id, is_owner=owner)
        
        if search_query:
            search_upper = search_query.upper()
            trackings = [
                t for t in trackings 
                if search_upper in t.tracking_id.upper() or
                   search_upper in (t.recipient_name or '').upper() or
                   search_upper in (t.product_name or '').upper()
            ]
        
        result = []
        for t in trackings:
            status_info = STATUS_MAP.get(t.status, {'icon': '📦', 'label': t.status, 'color': '#666'})
            result.append({
                'trackingId': t.tracking_id,
                'recipientName': t.recipient_name or 'Sin nombre',
                'productName': t.product_name,
                'productPrice': t.product_price,
                'status': t.status,
                'statusLabel': status_info['label'],
                'statusIcon': status_info['icon'],
                'statusColor': status_info['color'],
                'deliveryAddress': t.delivery_address,
                'estimatedDelivery': t.estimated_delivery_date,
                'delayDays': t.actual_delay_days,
                'createdAt': t.created_at.isoformat() if t.created_at else None,
                'updatedAt': t.updated_at.isoformat() if t.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'trackings': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': sanitize_error(e, 'get_trackings')}), 500


@app.route('/api/tracking/<tracking_id>', methods=['GET'])
@require_telegram_auth
def get_tracking(tracking_id):
    """Obtener detalles de un tracking específico."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        tracking = db_manager.get_tracking(tracking_id)
        
        if not tracking:
            return jsonify({'error': 'Tracking no encontrado'}), 404
        
        history = db_manager.get_tracking_history(tracking_id, include_future=False)
        history_list = []
        for h in history:
            history_list.append({
                'status': h.new_status,
                'notes': h.notes,
                'changedAt': h.changed_at.isoformat() if h.changed_at else None
            })
        
        status_info = STATUS_MAP.get(tracking.status, {'icon': '📦', 'label': tracking.status, 'color': '#666'})
        
        return jsonify({
            'success': True,
            'tracking': {
                'trackingId': tracking.tracking_id,
                'recipientName': tracking.recipient_name,
                'productName': tracking.product_name,
                'productPrice': tracking.product_price,
                'status': tracking.status,
                'statusLabel': status_info['label'],
                'statusIcon': status_info['icon'],
                'statusColor': status_info['color'],
                'deliveryAddress': tracking.delivery_address,
                'senderAddress': tracking.sender_address,
                'senderCountry': tracking.sender_country,
                'senderProvince': tracking.sender_province,
                'senderPostalCode': tracking.sender_postal_code,
                'recipientCountry': tracking.recipient_country,
                'recipientProvince': tracking.recipient_province,
                'recipientPostalCode': tracking.recipient_postal_code,
                'packageWeight': tracking.package_weight,
                'estimatedDelivery': tracking.estimated_delivery_date,
                'delayDays': tracking.actual_delay_days,
                'createdAt': tracking.created_at.isoformat() if tracking.created_at else None,
                'updatedAt': tracking.updated_at.isoformat() if tracking.updated_at else None,
                'dateTime': tracking.date_time
            },
            'history': history_list
        })
        
    except Exception as e:
        return jsonify({'error': sanitize_error(e, f'get_tracking:{tracking_id}')}), 500


@app.route('/api/tracking', methods=['POST'])
@require_telegram_auth
def create_tracking():
    """Crear nuevo tracking."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        
        required_fields = ['trackingId', 'recipientName', 'productName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        is_valid, tracking_id = input_validator.validate_tracking_id(data['trackingId'])
        if not is_valid:
            return jsonify({'error': tracking_id}), 400
        
        recipient_name = input_validator.sanitize_name(data['recipientName'])
        product_name = input_validator.sanitize_name(data['productName'])
        
        if not recipient_name or not product_name:
            return jsonify({'error': 'Nombre de destinatario y producto son requeridos'}), 400
        
        user = request.telegram_user
        
        now = datetime.now()
        date_time = data.get('dateTime') or now.strftime('%d/%m/%Y %H:%M')
        
        tracking = Tracking(
            tracking_id=tracking_id,
            recipient_name=recipient_name,
            product_name=product_name,
            product_price=input_validator.sanitize_text(data.get('productPrice', '0'), 20),
            status=data.get('status', 'RETENIDO') if data.get('status') in STATUS_MAP else 'RETENIDO',
            delivery_address=input_validator.sanitize_text(data.get('deliveryAddress', ''), 500),
            sender_address=input_validator.sanitize_text(data.get('senderAddress', ''), 500),
            date_time=date_time,
            package_weight=input_validator.sanitize_text(data.get('packageWeight', '0.5 kg'), 20),
            estimated_delivery_date=input_validator.sanitize_text(data.get('estimatedDelivery', ''), 50),
            recipient_postal_code=input_validator.sanitize_text(data.get('recipientPostalCode', ''), 20),
            recipient_province=input_validator.sanitize_text(data.get('recipientProvince', ''), 100),
            recipient_country=input_validator.sanitize_text(data.get('recipientCountry', ''), 100),
            sender_postal_code=input_validator.sanitize_text(data.get('senderPostalCode', ''), 20),
            sender_province=input_validator.sanitize_text(data.get('senderProvince', ''), 100),
            sender_country=input_validator.sanitize_text(data.get('senderCountry', ''), 100),
            user_telegram_id=user.get('id'),
            username=input_validator.sanitize_name(user.get('username', ''))
        )
        
        success = db_manager.save_tracking(tracking, created_by_admin_id=user.get('id'))
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Tracking creado correctamente',
                'trackingId': tracking.tracking_id
            })
        else:
            return jsonify({'error': 'Error al guardar el tracking'}), 500
            
    except Exception as e:
        logger.error(f"Error creating tracking: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/tracking/<tracking_id>/status', methods=['PUT'])
@require_telegram_auth
def update_tracking_status(tracking_id):
    """Actualizar estado de un tracking."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'error': 'Estado requerido'}), 400
        
        if new_status not in STATUS_MAP:
            return jsonify({'error': 'Estado inválido'}), 400
        
        success = db_manager.update_tracking_status(tracking_id, new_status, notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Estado actualizado a {STATUS_MAP[new_status]["label"]}'
            })
        else:
            return jsonify({'error': 'Error al actualizar estado'}), 500
            
    except Exception as e:
        logger.error(f"Error updating tracking status: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/tracking/<tracking_id>/delay', methods=['POST'])
@require_telegram_auth
def add_delay(tracking_id):
    """Agregar retraso a un tracking."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        delay_days = data.get('days', 1)
        reason = data.get('reason', 'Retraso no especificado')
        
        success = db_manager.add_delay_to_tracking(tracking_id, delay_days, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Retraso de {delay_days} días agregado'
            })
        else:
            return jsonify({'error': 'Error al agregar retraso'}), 500
            
    except Exception as e:
        logger.error(f"Error adding delay: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/tracking/<tracking_id>', methods=['PUT'])
@require_telegram_auth
def update_tracking(tracking_id):
    """Actualizar información de un tracking."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                updates = []
                values = []
                
                field_mapping = {
                    'recipientName': 'recipient_name',
                    'productName': 'product_name',
                    'productPrice': 'product_price',
                    'deliveryAddress': 'delivery_address',
                    'senderAddress': 'sender_address',
                    'packageWeight': 'package_weight',
                    'estimatedDelivery': 'estimated_delivery_date',
                    'recipientPostalCode': 'recipient_postal_code',
                    'recipientProvince': 'recipient_province',
                    'recipientCountry': 'recipient_country',
                    'senderPostalCode': 'sender_postal_code',
                    'senderProvince': 'sender_province',
                    'senderCountry': 'sender_country'
                }
                
                for js_field, db_field in field_mapping.items():
                    if js_field in data:
                        updates.append(f"{db_field} = %s")
                        values.append(data[js_field])
                
                if not updates:
                    return jsonify({'error': 'No hay campos para actualizar'}), 400
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(tracking_id)
                
                sql = f"UPDATE trackings SET {', '.join(updates)} WHERE tracking_id = %s"
                cur.execute(sql, values)
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tracking actualizado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error updating tracking: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/tracking/<tracking_id>', methods=['DELETE'])
@require_telegram_auth
def delete_tracking(tracking_id):
    """Eliminar un tracking."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM status_history WHERE tracking_id = %s", (tracking_id,))
                cur.execute("DELETE FROM trackings WHERE tracking_id = %s", (tracking_id,))
                deleted = cur.rowcount > 0
                conn.commit()
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Tracking eliminado correctamente'
            })
        else:
            return jsonify({'error': 'Tracking no encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting tracking: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/tracking/<tracking_id>/email', methods=['POST'])
@require_telegram_auth
@require_owner
def send_email(tracking_id):
    """Enviar email para un tracking (solo owner)."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        recipient_email = data.get('email')
        bank_entity = data.get('bankEntity')
        iban = data.get('iban')
        
        if not recipient_email:
            return jsonify({'error': 'Email del destinatario requerido'}), 400
        
        if not bank_entity or not iban:
            return jsonify({'error': 'Datos bancarios requeridos'}), 400
        
        tracking = db_manager.get_tracking(tracking_id)
        if not tracking:
            return jsonify({'error': 'Tracking no encontrado'}), 404
        
        result = EmailService.send_email_with_bank_data(
            recipient_email, 
            tracking, 
            bank_entity, 
            iban
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Email enviado correctamente',
                'messageId': result.get('messageId')
            })
        else:
            return jsonify({
                'error': result.get('error', 'Error al enviar email')
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/stats', methods=['GET'])
@require_telegram_auth
def get_stats():
    """Obtener estadísticas de trackings."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = request.telegram_user.get('id')
        owner = is_owner(user_id)
        
        trackings = db_manager.get_all_trackings(admin_id=user_id, is_owner=owner)
        
        stats = {
            'total': len(trackings),
            'retenido': 0,
            'enTransito': 0,
            'entregado': 0,
            'confirmarPago': 0
        }
        
        for t in trackings:
            if t.status == 'RETENIDO':
                stats['retenido'] += 1
            elif t.status == 'EN_TRANSITO':
                stats['enTransito'] += 1
            elif t.status == 'ENTREGADO':
                stats['entregado'] += 1
            elif t.status == 'CONFIRMAR_PAGO':
                stats['confirmarPago'] += 1
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/delay-reasons', methods=['GET'])
@require_telegram_auth
def get_delay_reasons():
    """Obtener razones de retraso disponibles."""
    return jsonify({
        'success': True,
        'reasons': DELAY_REASONS
    })


@app.route('/api/statuses', methods=['GET'])
@require_telegram_auth
def get_statuses():
    """Obtener estados disponibles."""
    statuses = [
        {'value': key, **value}
        for key, value in STATUS_MAP.items()
    ]
    return jsonify({
        'success': True,
        'statuses': statuses
    })


# ============================================================
# ENDPOINTS DE RED SOCIAL - POSTS
# ============================================================

@app.route('/api/posts', methods=['POST'])
@require_telegram_user
@rate_limit('posts_create')
def create_post():
    """Crear una nueva publicación."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        content_type = data.get('contentType', 'text')
        if content_type not in ['text', 'image', 'video']:
            return jsonify({'error': 'Tipo de contenido inválido'}), 400
        
        content_url = data.get('contentUrl')
        caption = input_validator.validate_caption(data.get('caption', ''))
        
        if content_type == 'text' and not caption:
            return jsonify({'error': 'El texto es requerido para posts de tipo texto'}), 400
        
        if content_type in ['image', 'video']:
            if not content_url:
                return jsonify({'error': 'La URL del contenido es requerida'}), 400
            is_valid, error = input_validator.validate_cloudinary_url(content_url)
            if not is_valid:
                is_valid, error = input_validator.validate_url(content_url)
                if not is_valid:
                    return jsonify({'error': 'URL de contenido inválida'}), 400
        
        db_manager.get_or_create_user(
            user_id=user_id,
            username=input_validator.sanitize_name(user.get('username', '')),
            first_name=input_validator.sanitize_name(user.get('first_name', '')),
            last_name=input_validator.sanitize_name(user.get('last_name', '')),
            telegram_id=user.get('id')
        )
        
        post_id = db_manager.create_post(
            user_id=user_id,
            content_type=content_type,
            content_url=content_url,
            caption=caption
        )
        
        if post_id:
            return jsonify({
                'success': True,
                'message': 'Publicación creada correctamente',
                'postId': post_id
            })
        else:
            return jsonify({'error': 'Error al crear la publicación'}), 500
            
    except Exception as e:
        return jsonify({'error': sanitize_error(e, 'create_post')}), 500


@app.route('/api/posts', methods=['GET'])
@require_telegram_user
def get_posts_feed():
    """Obtener feed de publicaciones."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 50)
        
        posts = db_manager.get_posts_feed(user_id=user_id, limit=limit, offset=offset)
        
        result = []
        for post in posts:
            result.append({
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': post.get('caption'),
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'userLiked': post.get('user_liked', False),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'posts': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': sanitize_error(e, 'get_posts_feed')}), 500


@app.route('/api/posts/<int:post_id>', methods=['GET'])
@require_telegram_user
def get_post_detail(post_id):
    """Obtener detalles de una publicación."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        post = db_manager.get_post(post_id)
        
        if not post:
            return jsonify({'error': 'Publicación no encontrada'}), 404
        
        return jsonify({
            'success': True,
            'post': {
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': post.get('caption'),
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@require_telegram_user
def delete_post(post_id):
    """Eliminar una publicación."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        success = db_manager.delete_post(post_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Publicación eliminada correctamente'
            })
        else:
            return jsonify({'error': 'No se pudo eliminar la publicación'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@require_telegram_user
@rate_limit('posts_like')
def like_post(post_id):
    """Dar like a una publicación."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.like_post(post_id, user_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Like agregado' if result.get('message') == 'liked' else 'Ya habías dado like'
            })
        elif result.get('error') == 'post_not_found':
            return jsonify({'error': 'Publicación no encontrada'}), 404
        else:
            return jsonify({'error': 'Error al agregar like'}), 500
            
    except Exception as e:
        logger.error(f"Error liking post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/posts/<int:post_id>/like', methods=['DELETE'])
@require_telegram_user
def unlike_post(post_id):
    """Quitar like de una publicación."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.unlike_post(post_id, user_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Like removido' if result.get('message') == 'unliked' else 'No habías dado like'
            })
        elif result.get('error') == 'post_not_found':
            return jsonify({'error': 'Publicación no encontrada'}), 404
        else:
            return jsonify({'error': 'Error al quitar like'}), 500
            
    except Exception as e:
        logger.error(f"Error unliking post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


# ============================================================
# ENDPOINTS DE RED SOCIAL - USUARIOS Y SEGUIDORES
# ============================================================

@app.route('/api/users/<user_id>/profile', methods=['GET'])
@require_telegram_user
def get_user_profile(user_id):
    """Obtener perfil de un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        viewer = request.telegram_user
        viewer_id = str(viewer.get('id'))
        
        profile = db_manager.get_user_profile(user_id, viewer_id)
        
        if not profile:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'profile': {
                'id': profile.get('id'),
                'username': profile.get('username'),
                'firstName': profile.get('first_name'),
                'lastName': profile.get('last_name'),
                'avatarUrl': profile.get('avatar_url'),
                'bio': profile.get('bio'),
                'level': profile.get('level', 1),
                'credits': profile.get('credits', 0),
                'isVerified': profile.get('is_verified', False),
                'followersCount': profile.get('followers_count', 0),
                'followingCount': profile.get('following_count', 0),
                'postsCount': profile.get('posts_count', 0),
                'isFollowing': profile.get('is_following', False),
                'createdAt': profile.get('created_at').isoformat() if profile.get('created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/posts', methods=['GET'])
@require_telegram_user
def get_user_posts(user_id):
    """Obtener publicaciones de un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 50)
        
        posts = db_manager.get_user_posts(user_id, limit=limit, offset=offset)
        
        result = []
        for post in posts:
            caption = post.get('caption')
            if post.get('is_encrypted') and caption and post.get('encryption_key') and post.get('encryption_iv'):
                try:
                    decrypted = encryption_manager.decrypt_text(
                        caption,
                        post['encryption_key'],
                        post['encryption_iv']
                    )
                    if decrypted.get('success'):
                        caption = decrypted.get('text', caption)
                except Exception as e:
                    logger.warning(f"Failed to decrypt caption for post {post.get('id')}: {e}")
            
            result.append({
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': caption,
                'media': post.get('media') or [],
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'posts': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting user posts {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/me/avatar', methods=['POST'])
@require_telegram_user
def upload_avatar():
    """Subir foto de perfil."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'No se envio ninguna imagen'}), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({'error': 'No se selecciono ninguna imagen'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Usa PNG, JPG, JPEG, GIF o WEBP'}), 400
        
        db_manager.get_or_create_user(
            user_id=user_id,
            username=user.get('username'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
            telegram_id=user.get('id')
        )
        
        file_content = file.read()
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        content_type = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }.get(ext, 'image/png')
        
        avatar_data = f"data:{content_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
        
        success = db_manager.update_user_avatar_data(user_id, avatar_data)
        
        avatar_url = f"/api/avatar/{user_id}"
        
        if success:
            db_manager.update_user_profile(user_id, avatar_url=avatar_url)
            return jsonify({
                'success': True,
                'message': 'Foto de perfil actualizada',
                'avatarUrl': avatar_url
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/avatar/<user_id>')
def serve_avatar(user_id):
    """Servir avatar desde la base de datos."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        avatar_data = db_manager.get_user_avatar_data(user_id)
        
        if not avatar_data:
            return jsonify({'error': 'Avatar not found'}), 404
        
        if avatar_data.startswith('data:'):
            header, encoded = avatar_data.split(',', 1)
            content_type = header.split(':')[1].split(';')[0]
            image_data = base64.b64decode(encoded)
            return Response(image_data, mimetype=content_type)
        else:
            return jsonify({'error': 'Invalid avatar format'}), 500
            
    except Exception as e:
        logger.error(f"Error serving avatar: {e}")
        return jsonify({'error': 'Avatar not found'}), 404


@app.route('/api/users/me', methods=['GET'])
@require_telegram_user
def get_my_profile():
    """Obtener mi perfil actual con avatar."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        user_profile = db_manager.get_user_profile(user_id, user_id)
        
        if user_profile:
            return jsonify({
                'success': True,
                'profile': {
                    'id': user_profile.get('id'),
                    'username': user_profile.get('username'),
                    'firstName': user_profile.get('first_name'),
                    'lastName': user_profile.get('last_name'),
                    'avatarUrl': user_profile.get('avatar_url'),
                    'bio': user_profile.get('bio'),
                    'level': user_profile.get('level'),
                    'credits': user_profile.get('credits'),
                    'isVerified': user_profile.get('is_verified'),
                    'followersCount': user_profile.get('followers_count', 0),
                    'followingCount': user_profile.get('following_count', 0),
                    'postsCount': user_profile.get('posts_count', 0)
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Perfil no encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Error getting my profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/me/profile', methods=['PUT'])
@require_telegram_user
def update_my_profile():
    """Actualizar mi perfil."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        data = request.get_json()
        
        bio = data.get('bio')
        avatar_url = data.get('avatarUrl')
        
        success = db_manager.update_user_profile(user_id, bio=bio, avatar_url=avatar_url)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado correctamente'
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/follow', methods=['POST'])
@require_telegram_user
@rate_limit('follow')
def follow_user(user_id):
    """Seguir a un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        follower = request.telegram_user
        follower_id = str(follower.get('id'))
        
        if follower_id == user_id:
            return jsonify({'error': 'No puedes seguirte a ti mismo'}), 400
        
        db_manager.get_or_create_user(
            user_id=follower_id,
            username=follower.get('username'),
            first_name=follower.get('first_name'),
            last_name=follower.get('last_name'),
            telegram_id=follower.get('id')
        )
        
        success = db_manager.follow_user(follower_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Ahora sigues a este usuario'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Ya sigues a este usuario'
            })
            
    except Exception as e:
        logger.error(f"Error following user {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/follow', methods=['DELETE'])
@require_telegram_user
def unfollow_user(user_id):
    """Dejar de seguir a un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        follower = request.telegram_user
        follower_id = str(follower.get('id'))
        
        success = db_manager.unfollow_user(follower_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Has dejado de seguir a este usuario'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No seguías a este usuario'
            })
            
    except Exception as e:
        logger.error(f"Error unfollowing user {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/followers', methods=['GET'])
@require_telegram_user
def get_user_followers(user_id):
    """Obtener lista de seguidores de un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 100)
        
        followers = db_manager.get_followers(user_id, limit=limit, offset=offset)
        
        result = []
        for follower in followers:
            result.append({
                'id': follower.get('id'),
                'username': follower.get('username'),
                'firstName': follower.get('first_name'),
                'lastName': follower.get('last_name'),
                'avatarUrl': follower.get('avatar_url'),
                'bio': follower.get('bio'),
                'isVerified': follower.get('is_verified', False),
                'followedAt': follower.get('followed_at').isoformat() if follower.get('followed_at') else None
            })
        
        return jsonify({
            'success': True,
            'followers': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting followers for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/following', methods=['GET'])
@require_telegram_user
def get_user_following(user_id):
    """Obtener lista de usuarios que sigue."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 100)
        
        following = db_manager.get_following(user_id, limit=limit, offset=offset)
        
        result = []
        for user in following:
            result.append({
                'id': user.get('id'),
                'username': user.get('username'),
                'firstName': user.get('first_name'),
                'lastName': user.get('last_name'),
                'avatarUrl': user.get('avatar_url'),
                'bio': user.get('bio'),
                'isVerified': user.get('is_verified', False),
                'followedAt': user.get('followed_at').isoformat() if user.get('followed_at') else None
            })
        
        return jsonify({
            'success': True,
            'following': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting following for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/stats', methods=['GET'])
@require_telegram_user
def get_user_stats(user_id):
    """Obtener estadisticas del perfil de un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        posts_count = db_manager.count_user_publications(user_id)
        followers = db_manager.get_followers(user_id, limit=1000)
        following = db_manager.get_following(user_id, limit=1000)
        
        return jsonify({
            'success': True,
            'stats': {
                'posts': posts_count,
                'followers': len(followers) if followers else 0,
                'following': len(following) if following else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/<user_id>/profile', methods=['PUT'])
@require_telegram_user
def update_user_profile(user_id):
    """Actualizar perfil de un usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        current_user = request.telegram_user
        current_user_id = str(current_user.get('id'))
        
        if current_user_id != user_id:
            return jsonify({'error': 'No autorizado'}), 403
        
        data = request.get_json()
        bio = data.get('bio')
        
        success = db_manager.update_user_profile(user_id, bio=bio)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado correctamente'
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/users/avatar', methods=['POST'])
@require_telegram_user
def upload_user_avatar():
    """Subir avatar de usuario."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'No se envio archivo'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'Archivo vacio'}), 400
        
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
            filename = secure_filename(f"avatar_{user_id}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
            
            avatars_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(avatars_folder, exist_ok=True)
            
            file_path = os.path.join(avatars_folder, filename)
            file.save(file_path)
            
            avatar_url = f"/static/uploads/avatars/{filename}"
            
            success = db_manager.update_user_profile(user_id, avatar_url=avatar_url)
            
            if success:
                return jsonify({
                    'success': True,
                    'avatar_url': avatar_url
                })
            else:
                return jsonify({'error': 'Error al guardar avatar'}), 500
        else:
            return jsonify({'error': 'Formato de archivo no permitido'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


# ============================================================
# ENDPOINTS DE BOTS DE USUARIO
# ============================================================

@app.route('/api/bots/init', methods=['POST'])
@require_telegram_auth
def init_bots():
    """Inicializar tabla de tipos de bots (solo owner)."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        success = db_manager.initialize_bot_types()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Tipos de bots inicializados correctamente'
            })
        else:
            return jsonify({'error': 'Error al inicializar bots'}), 500
            
    except Exception as e:
        logger.error(f"Error initializing bots: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/my', methods=['GET'])
@require_telegram_user
def get_my_bots():
    """Obtener mis bots activos."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        is_demo = getattr(request, 'is_demo', False)
        
        if is_demo and OWNER_TELEGRAM_ID:
            user_id = str(OWNER_TELEGRAM_ID)
            user_is_owner = True
        else:
            user_id = str(user.get('id'))
            user_is_owner = is_owner(user.get('id'))
        
        bots = db_manager.get_user_bots(user_id, is_owner=user_is_owner)
        
        result = []
        for bot in bots:
            result.append({
                'id': bot.get('id'),
                'botName': bot.get('bot_name'),
                'botType': bot.get('bot_type'),
                'isActive': bot.get('is_active', True),
                'icon': bot.get('icon', '🤖'),
                'description': bot.get('description', ''),
                'config': bot.get('config'),
                'createdAt': bot.get('created_at').isoformat() if bot.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'bots': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting user bots: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/available', methods=['GET'])
@require_telegram_user
def get_available_bots():
    """Obtener bots disponibles para comprar."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        is_demo = getattr(request, 'is_demo', False)
        
        if is_demo and OWNER_TELEGRAM_ID:
            user_id = str(OWNER_TELEGRAM_ID)
            user_is_owner = True
        else:
            user_id = str(user.get('id'))
            user_is_owner = is_owner(user.get('id'))
        
        bots = db_manager.get_available_bots(user_id, is_owner=user_is_owner)
        
        result = []
        for bot in bots:
            result.append({
                'id': bot.get('id'),
                'botName': bot.get('bot_name'),
                'botType': bot.get('bot_type'),
                'description': bot.get('description', ''),
                'icon': bot.get('icon', '🤖'),
                'price': bot.get('price', 0)
            })
        
        return jsonify({
            'success': True,
            'bots': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting available bots: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/purchase', methods=['POST'])
@require_telegram_user
def purchase_bot():
    """Comprar un bot."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        data = request.get_json()
        bot_type = data.get('botType')
        
        if not bot_type:
            return jsonify({'error': 'Tipo de bot requerido'}), 400
        
        result = db_manager.purchase_bot(user_id, bot_type)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'botName': result.get('bot_name'),
                'creditsRemaining': result.get('credits_remaining')
            })
        else:
            error = result.get('error', 'Error desconocido')
            status_code = 400 if 'insuficientes' in error.lower() or 'ya tienes' in error.lower() else 500
            return jsonify({
                'success': False,
                'error': error,
                'required': result.get('required'),
                'current': result.get('current')
            }), status_code
            
    except Exception as e:
        logger.error(f"Error purchasing bot: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/<int:bot_id>/remove', methods=['POST'])
@require_telegram_user
def remove_bot(bot_id):
    """Desactivar un bot."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        success = db_manager.remove_user_bot(user_id, bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bot desactivado correctamente'
            })
        else:
            return jsonify({'error': 'Error al desactivar bot'}), 500
            
    except Exception as e:
        logger.error(f"Error removing bot {bot_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/<int:bot_id>/toggle', methods=['POST'])
@require_telegram_user
def toggle_bot(bot_id):
    """Toggle bot activation status."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.toggle_bot_activation(user_id, bot_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'isActive': result.get('is_active'),
                'message': 'Bot activado' if result.get('is_active') else 'Bot desactivado'
            })
        else:
            return jsonify({'error': result.get('error', 'Error al cambiar estado')}), 500
            
    except Exception as e:
        logger.error(f"Error toggling bot {bot_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@app.route('/api/bots/<int:bot_id>/config', methods=['GET', 'POST'])
@require_telegram_user
def bot_config(bot_id):
    """Get or update bot configuration."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if request.method == 'GET':
            result = db_manager.get_bot_config(user_id, bot_id)
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'config': result.get('config', {}),
                    'botType': result.get('bot_type'),
                    'botName': result.get('bot_name')
                })
            else:
                return jsonify({'error': result.get('error', 'Bot no encontrado')}), 404
        else:
            data = request.get_json() or {}
            config = data.get('config', {})
            result = db_manager.update_bot_config(user_id, bot_id, config)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Configuracion guardada'
                })
            else:
                return jsonify({'error': result.get('error', 'Error al guardar')}), 500
            
    except Exception as e:
        logger.error(f"Error with bot config {bot_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


CHANGENOW_API_KEY = os.environ.get('CHANGENOW_API_KEY', '')
CHANGENOW_BASE_URL = 'https://api.changenow.io/v1'

@app.route('/api/exchange/currencies', methods=['GET'])
@require_telegram_user
@rate_limit('exchange')
def get_exchange_currencies():
    """Obtener lista de criptomonedas disponibles."""
    try:
        if not CHANGENOW_API_KEY:
            return jsonify({'error': 'API key no configurada'}), 500
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/currencies',
            params={'active': 'true', 'fixedRate': 'true'},
            timeout=10
        )
        
        if response.status_code == 200:
            currencies = response.json()
            popular = ['btc', 'eth', 'usdt', 'ltc', 'xrp', 'doge', 'bnb', 'sol', 'trx', 'matic']
            sorted_currencies = sorted(currencies, key=lambda x: (x['ticker'].lower() not in popular, x['ticker'].lower()))
            return jsonify({'success': True, 'currencies': sorted_currencies})
        else:
            return jsonify({'error': 'Error al obtener monedas'}), 500
            
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500

@app.route('/api/exchange/min-amount', methods=['GET'])
@require_telegram_user
def get_min_amount():
    """Obtener monto minimo para intercambio."""
    try:
        from_currency = request.args.get('from', '').lower()
        to_currency = request.args.get('to', '').lower()
        
        if not from_currency or not to_currency:
            return jsonify({'error': 'Monedas requeridas'}), 400
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/min-amount/{from_currency}_{to_currency}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({'success': True, 'minAmount': data.get('minAmount')})
        else:
            return jsonify({'error': 'Error al obtener monto minimo'}), 500
            
    except Exception as e:
        logger.error(f"Error getting min amount: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500

@app.route('/api/exchange/estimate', methods=['GET'])
@require_telegram_user
def get_exchange_estimate():
    """Obtener estimacion de intercambio."""
    try:
        from_currency = request.args.get('from', '').lower()
        to_currency = request.args.get('to', '').lower()
        amount = request.args.get('amount', '')
        
        if not from_currency or not to_currency or not amount:
            return jsonify({'error': 'Parametros requeridos'}), 400
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/exchange-amount/{amount}/{from_currency}_{to_currency}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'estimatedAmount': data.get('estimatedAmount'),
                'transactionSpeedForecast': data.get('transactionSpeedForecast'),
                'warningMessage': data.get('warningMessage')
            })
        else:
            error_data = response.json() if response.content else {}
            return jsonify({'error': error_data.get('message', 'Error al estimar')}), 400
            
    except Exception as e:
        logger.error(f"Error getting estimate: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500

@app.route('/api/exchange/create', methods=['POST'])
@require_telegram_user
def create_exchange():
    """Crear una transaccion de intercambio."""
    try:
        data = request.get_json()
        
        from_currency = data.get('from', '').lower()
        to_currency = data.get('to', '').lower()
        amount = data.get('amount')
        address = data.get('address')
        refund_address = data.get('refundAddress', '')
        
        if not all([from_currency, to_currency, amount, address]):
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        payload = {
            'from': from_currency,
            'to': to_currency,
            'amount': float(amount),
            'address': address,
            'refundAddress': refund_address,
            'api_key': CHANGENOW_API_KEY
        }
        
        response = requests.post(
            f'{CHANGENOW_BASE_URL}/transactions',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            tx_data = response.json()
            return jsonify({
                'success': True,
                'id': tx_data.get('id'),
                'payinAddress': tx_data.get('payinAddress'),
                'payoutAddress': tx_data.get('payoutAddress'),
                'fromCurrency': tx_data.get('fromCurrency'),
                'toCurrency': tx_data.get('toCurrency'),
                'amount': tx_data.get('amount'),
                'payinExtraId': tx_data.get('payinExtraId')
            })
        else:
            error_data = response.json() if response.content else {}
            return jsonify({'error': error_data.get('message', 'Error al crear transaccion')}), 400
            
    except Exception as e:
        logger.error(f"Error creating exchange: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500

@app.route('/api/exchange/status/<tx_id>', methods=['GET'])
@require_telegram_user
def get_exchange_status(tx_id):
    """Obtener estado de una transaccion."""
    try:
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/transactions/{tx_id}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'status': data.get('status'),
                'payinHash': data.get('payinHash'),
                'payoutHash': data.get('payoutHash'),
                'amountFrom': data.get('amountFrom'),
                'amountTo': data.get('amountTo'),
                'fromCurrency': data.get('fromCurrency'),
                'toCurrency': data.get('toCurrency')
            })
        else:
            return jsonify({'error': 'Transaccion no encontrada'}), 404
            
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


TONCENTER_API_URL = 'https://toncenter.com/api/v3'
MERCHANT_TON_WALLET = os.environ.get('TON_WALLET_ADDRESS', 'UQA5l6-8ka5wsyOhn8S7qcXWESgvPJgOBC3wsOVBnxm87Bck')

TON_CREDIT_RATES = {
    1: 10,
    2: 22,
    5: 60,
    10: 130,
    20: 280,
    50: 750,
}

def calculate_credits_from_ton(ton_amount):
    """Calcula BUNK3RCO1N basado en TON con tasa del servidor."""
    ton_amount = float(ton_amount)
    if ton_amount in TON_CREDIT_RATES:
        return TON_CREDIT_RATES[ton_amount]
    credits = int(ton_amount * 10)
    if ton_amount >= 10:
        credits = int(credits * 1.3)
    elif ton_amount >= 5:
        credits = int(credits * 1.2)
    elif ton_amount >= 2:
        credits = int(credits * 1.1)
    return max(credits, 1)


@app.route('/api/ton/payment/create', methods=['POST'])
@require_telegram_user
def create_ton_payment():
    """Crear una solicitud de pago pendiente."""
    try:
        data = request.get_json()
        ton_amount = data.get('tonAmount', 0)
        
        if not ton_amount or float(ton_amount) <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        ton_amount = float(ton_amount)
        if ton_amount < 0.5:
            return jsonify({'success': False, 'error': 'Monto minimo: 0.5 TON'}), 400
        if ton_amount > 1000:
            return jsonify({'success': False, 'error': 'Monto maximo: 1000 TON'}), 400
        
        credits = calculate_credits_from_ton(ton_amount)
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        payment_id = str(uuid.uuid4())[:8].upper()
        
        if not db_manager:
            return jsonify({
                'success': True, 
                'paymentId': payment_id,
                'merchantWallet': MERCHANT_TON_WALLET,
                'tonAmount': ton_amount,
                'credits': credits,
                'message': 'Demo mode'
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pending_payments (payment_id, user_id, credits, ton_amount)
                    VALUES (%s, %s, %s, %s)
                """, (payment_id, user_id, credits, ton_amount))
                conn.commit()
        
        return jsonify({
            'success': True,
            'paymentId': payment_id,
            'merchantWallet': MERCHANT_TON_WALLET,
            'tonAmount': ton_amount,
            'credits': credits,
            'comment': f'BUNK3R-{payment_id}'
        })
        
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ton/payment/<payment_id>/verify', methods=['POST'])
@require_telegram_user
@rate_limit('payment_verify')
def verify_ton_payment(payment_id):
    """Verificar si un pago fue recibido en la blockchain."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'status': 'confirmed', 'message': 'Demo mode'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM pending_payments 
                    WHERE payment_id = %s AND user_id = %s
                """, (payment_id, user_id))
                payment = cur.fetchone()
                
                if not payment:
                    return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
                
                if payment['status'] == 'confirmed':
                    return jsonify({'success': True, 'status': 'confirmed', 'message': 'Pago ya confirmado'})
                
                expected_comment = f'BUNK3R-{payment_id}'
                expected_amount = float(payment['ton_amount'])
                
                try:
                    response = requests.get(
                        f'{TONCENTER_API_URL}/transactions',
                        params={
                            'account': MERCHANT_TON_WALLET,
                            'limit': 50,
                            'sort': 'desc'
                        },
                        timeout=15
                    )
                    
                    if response.status_code != 200:
                        return jsonify({
                            'success': True, 
                            'status': 'pending',
                            'message': 'Esperando confirmacion en la blockchain...'
                        })
                    
                    tx_data = response.json()
                    transactions = tx_data.get('transactions', [])
                    
                    for tx in transactions:
                        in_msg = tx.get('in_msg', {})
                        
                        if not in_msg or in_msg.get('msg_type') != 'int_msg':
                            continue
                        
                        msg_value = int(in_msg.get('value', 0))
                        msg_amount_ton = msg_value / 1e9
                        
                        if msg_amount_ton < expected_amount * 0.99:
                            continue
                        
                        decoded = in_msg.get('decoded_body', {})
                        comment = decoded.get('text', '') if decoded else ''
                        
                        if not comment:
                            raw_body = in_msg.get('message', '')
                            if raw_body:
                                try:
                                    comment = bytes.fromhex(raw_body).decode('utf-8', errors='ignore')
                                except (ValueError, UnicodeDecodeError) as e:
                                    logger.debug(f"Error decoding message body: {e}")
                        
                        if expected_comment.lower() in comment.lower():
                            tx_hash = tx.get('hash', '')
                            
                            cur.execute("""
                                UPDATE pending_payments 
                                SET status = 'confirmed', tx_hash = %s, confirmed_at = NOW()
                                WHERE payment_id = %s
                            """, (tx_hash, payment_id))
                            
                            credits = calculate_credits_from_ton(expected_amount)
                            cur.execute("""
                                INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id, created_at)
                                VALUES (%s, %s, 'credit', %s, %s, NOW())
                            """, (user_id, credits, f'Recarga TON - {expected_amount} TON', tx_hash))
                            
                            conn.commit()
                            
                            cur.execute("""
                                SELECT COALESCE(SUM(amount), 0) as balance
                                FROM wallet_transactions
                                WHERE user_id = %s
                            """, (user_id,))
                            result = cur.fetchone()
                            new_balance = float(result['balance']) if result else credits
                            
                            db_manager.create_transaction_notification(
                                user_id=user_id,
                                amount=credits,
                                transaction_type='credit',
                                new_balance=new_balance
                            )
                            
                            return jsonify({
                                'success': True,
                                'status': 'confirmed',
                                'txHash': tx_hash,
                                'creditsAdded': credits,
                                'newBalance': new_balance,
                                'message': f'+{credits} BUNK3RCO1N agregados!'
                            })
                    
                    return jsonify({
                        'success': True,
                        'status': 'pending',
                        'message': 'Transaccion no encontrada aun. Espera unos segundos...'
                    })
                    
                except requests.RequestException as e:
                    logger.error(f"TonCenter API error: {e}")
                    return jsonify({
                        'success': True,
                        'status': 'pending',
                        'message': 'Verificando en la blockchain...'
                    })
                    
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ton/payment/<payment_id>/status', methods=['GET'])
@require_telegram_user
def get_payment_status(payment_id):
    """Obtener el estado de un pago pendiente."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'status': 'pending'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT status, tx_hash, credits FROM pending_payments 
                    WHERE payment_id = %s AND user_id = %s
                """, (payment_id, user_id))
                payment = cur.fetchone()
                
                if not payment:
                    return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
                
                return jsonify({
                    'success': True,
                    'status': payment['status'],
                    'txHash': payment.get('tx_hash'),
                    'credits': payment['credits']
                })
                
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ton/wallet-info', methods=['GET'])
@require_telegram_user
def get_ton_wallet_info():
    """Obtener informacion de la wallet del comerciante."""
    return jsonify({
        'success': True,
        'merchantWallet': MERCHANT_TON_WALLET,
        'currency': 'TON',
        'network': 'mainnet'
    })


@app.route('/api/wallet/merchant', methods=['GET'])
@require_telegram_user
def get_merchant_wallet():
    """Obtener la wallet del comerciante para pagos."""
    return jsonify({
        'success': True,
        'merchantWallet': MERCHANT_TON_WALLET
    })


@app.route('/api/wallet/balance', methods=['GET'])
@require_telegram_user
def get_wallet_balance():
    """Obtener el saldo de BUNK3RCO1N del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'balance': 0})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                balance = result[0] if result else 0
                
        return jsonify({'success': True, 'balance': float(balance)})
        
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return jsonify({'success': True, 'balance': 0})

@app.route('/api/wallet/credit', methods=['POST'])
@require_telegram_user
def credit_wallet():
    """Agregar BUNK3RCO1N a la billetera del usuario."""
    try:
        data = request.get_json()
        credits = data.get('credits', 0)
        usdt_amount = data.get('usdtAmount', 0)
        transaction_boc = data.get('transactionBoc', '')
        user_id = str(data.get('userId') or (request.telegram_user.get('id', 0) if hasattr(request, 'telegram_user') else 0))
        
        if not credits or credits <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if not db_manager:
            return jsonify({'success': True, 'newBalance': credits, 'message': 'Demo mode'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'credit', %s, %s, NOW())
                """, (user_id, credits, f'Recarga de {usdt_amount} USDT', transaction_boc))
                conn.commit()
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                new_balance = result[0] if result else credits
        
        db_manager.create_transaction_notification(
            user_id=user_id,
            amount=credits,
            transaction_type='credit',
            new_balance=float(new_balance)
        )
                
        return jsonify({
            'success': True,
            'newBalance': float(new_balance),
            'creditsAdded': credits
        })
        
    except Exception as e:
        logger.error(f"Error crediting wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wallet/transactions', methods=['GET'])
@require_telegram_auth
def get_wallet_transactions():
    """Obtener historial de transacciones del usuario con filtros."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        filter_type = request.args.get('filter', 'all')
        from_date = request.args.get('from_date', None)
        
        if not db_manager:
            return jsonify({'success': True, 'transactions': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, amount, transaction_type, description, created_at
                    FROM wallet_transactions
                    WHERE user_id = %s
                """
                params = [user_id]
                
                if filter_type == 'credit':
                    query += " AND amount > 0"
                elif filter_type == 'debit':
                    query += " AND amount < 0"
                
                if from_date:
                    query += " AND created_at >= %s"
                    params.append(from_date)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                transactions = cur.fetchall()
                
        return jsonify({
            'success': True,
            'transactions': [dict(t) for t in transactions] if transactions else []
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'success': True, 'transactions': []})


@app.route('/api/wallet/connect', methods=['POST'])
@require_telegram_user
def save_wallet_address():
    """Guardar la direccion de wallet TON del usuario."""
    try:
        data = request.get_json()
        wallet_address = data.get('address', '')
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Direccion de wallet requerida'}), 400
        
        if not db_manager:
            return jsonify({'success': True, 'message': 'Demo mode'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET wallet_address = %s, updated_at = NOW()
                    WHERE telegram_id = %s
                """, (wallet_address, user_id))
                conn.commit()
                
        logger.info(f"Wallet conectada para usuario {user_id}: {wallet_address[:10]}...")
        return jsonify({'success': True, 'message': 'Wallet guardada correctamente'})
        
    except Exception as e:
        logger.error(f"Error saving wallet address: {e}")
        return jsonify({'success': False, 'error': 'Error al guardar wallet'}), 500


@app.route('/api/wallet/address', methods=['GET'])
@require_telegram_user
def get_wallet_address():
    """Obtener la direccion de wallet guardada del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'address': None})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT wallet_address FROM users WHERE telegram_id = %s
                """, (user_id,))
                result = cur.fetchone()
                address = result[0] if result else None
                
        return jsonify({'success': True, 'address': address})
        
    except Exception as e:
        logger.error(f"Error getting wallet address: {e}")
        return jsonify({'success': True, 'address': None})


@app.route('/api/b3c/price', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_price():
    """Obtener precio actual del token B3C."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        price_data = b3c.get_b3c_price()
        return jsonify(price_data)
    except Exception as e:
        logger.error(f"Error getting B3C price: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener precio'}), 500


@app.route('/api/b3c/calculate/buy', methods=['POST'])
@rate_limit('calculate', use_ip=True)
def calculate_b3c_buy():
    """Calcular cuantos B3C recibe el usuario por X TON."""
    try:
        data = request.get_json()
        ton_amount = float(data.get('tonAmount', 0))
        
        if ton_amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if ton_amount < 0.1:
            return jsonify({'success': False, 'error': 'Minimo 0.1 TON'}), 400
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        result = b3c.calculate_b3c_from_ton(ton_amount)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calculating B3C: {e}")
        return jsonify({'success': False, 'error': 'Error en calculo'}), 500


@app.route('/api/b3c/calculate/sell', methods=['POST'])
@rate_limit('calculate', use_ip=True)
def calculate_b3c_sell():
    """Calcular cuantos TON recibe el usuario por X B3C."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        
        if b3c_amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        result = b3c.calculate_ton_from_b3c(b3c_amount)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calculating TON: {e}")
        return jsonify({'success': False, 'error': 'Error en calculo'}), 500


@app.route('/api/b3c/balance', methods=['GET'])
@rate_limit('balance_check', use_ip=True)
def get_b3c_balance():
    """Obtener balance de B3C del usuario desde compras confirmadas y retiros."""
    try:
        user_id = '0'
        if hasattr(request, 'telegram_user') and request.telegram_user:
            user_id = str(request.telegram_user.get('id', 0))
        elif request.headers.get('X-Demo-Mode') == 'true' and not IS_PRODUCTION:
            user_id = '0'
        else:
            init_data = request.headers.get('X-Telegram-Init-Data', '')
            if init_data:
                from urllib.parse import parse_qs
                parsed = parse_qs(init_data)
                if 'user' in parsed:
                    import json
                    user_data = json.loads(parsed['user'][0])
                    user_id = str(user_data.get('id', 0))
        
        b3c_balance = 0.0
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(SUM(b3c_amount), 0) as total_purchased
                        FROM b3c_purchases 
                        WHERE user_id = %s AND status = 'confirmed'
                    """, (user_id,))
                    purchased = cur.fetchone()
                    total_purchased = float(purchased[0]) if purchased and purchased[0] else 0
                    
                    cur.execute("""
                        SELECT COALESCE(SUM(b3c_amount), 0) as total_withdrawn
                        FROM b3c_withdrawals 
                        WHERE user_id = %s AND status = 'completed'
                    """, (user_id,))
                    withdrawn = cur.fetchone()
                    total_withdrawn = float(withdrawn[0]) if withdrawn and withdrawn[0] else 0
                    
                    b3c_balance = total_purchased - total_withdrawn
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        price_data = b3c.get_b3c_price()
        
        price_ton = price_data.get('price_ton', 0.001)
        price_usd = price_data.get('price_usd', 0.005)
        
        return jsonify({
            'success': True,
            'balance': b3c_balance,
            'balance_formatted': f"{b3c_balance:,.2f}",
            'value_ton': b3c_balance * price_ton,
            'value_usd': b3c_balance * price_usd,
            'price_per_b3c_ton': price_ton,
            'price_per_b3c_usd': price_usd,
            'is_testnet': b3c.use_testnet
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C balance: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener balance', 'balance': 0}), 500


@app.route('/api/b3c/config', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_config():
    """Obtener configuracion del servicio B3C."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify({
            'success': True,
            'config': b3c.get_service_config()
        })
    except Exception as e:
        logger.error(f"Error getting B3C config: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener configuracion'}), 500


@app.route('/api/b3c/network', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_network_status():
    """Verificar estado de la red TON."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify(b3c.get_network_status())
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar red'}), 500


@app.route('/api/b3c/testnet/guide', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_testnet_setup_guide():
    """Obtener guia de configuracion para testnet."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify({
            'success': True,
            'guide': b3c.get_testnet_setup_guide()
        })
    except Exception as e:
        logger.error(f"Error getting testnet guide: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener guia'}), 500


@app.route('/api/b3c/buy/create', methods=['POST'])
@require_telegram_user
def create_b3c_purchase():
    """Crear solicitud de compra de B3C con wallet única de depósito."""
    try:
        data = request.get_json()
        ton_amount = float(data.get('tonAmount', 0))
        
        if ton_amount < 0.1:
            return jsonify({'success': False, 'error': 'Minimo 0.1 TON'}), 400
        if ton_amount > 1000:
            return jsonify({'success': False, 'error': 'Maximo 1000 TON'}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        purchase_id = str(uuid.uuid4())[:8].upper()
        
        from tracking.b3c_service import get_b3c_service
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        b3c = get_b3c_service()
        calculation = b3c.calculate_b3c_from_ton(ton_amount)
        
        if not db_manager:
            return jsonify({
                'success': True,
                'purchaseId': purchase_id,
                'calculation': calculation,
                'depositAddress': 'DEMO_WALLET_ADDRESS',
                'message': 'Demo mode'
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO b3c_purchases (purchase_id, user_id, ton_amount, b3c_amount, 
                                               commission_ton, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
                """, (purchase_id, user_id, ton_amount, calculation['b3c_amount'], 
                      calculation['commission_ton']))
                conn.commit()
        
        wallet_pool = get_wallet_pool_service(db_manager)
        wallet_assignment = wallet_pool.assign_wallet_for_purchase(user_id, ton_amount, purchase_id)
        
        if not wallet_assignment or not wallet_assignment.get('success'):
            return jsonify({
                'success': False,
                'error': 'No hay wallets disponibles. Intenta de nuevo.'
            }), 503
        
        return jsonify({
            'success': True,
            'purchaseId': purchase_id,
            'calculation': calculation,
            'depositAddress': wallet_assignment['deposit_address'],
            'amountToSend': wallet_assignment['amount_to_send'],
            'expiresAt': wallet_assignment['expires_at'],
            'expiresInMinutes': wallet_assignment['expires_in_minutes'],
            'useUniqueWallet': True,
            'instructions': [
                f"Envía exactamente {ton_amount} TON a la dirección indicada",
                "Esta dirección es única para esta compra",
                f"Tienes {wallet_assignment['expires_in_minutes']} minutos para completar el pago",
                "Los B3C se acreditarán automáticamente al detectar el pago"
            ]
        })
        
    except Exception as e:
        logger.error(f"Error creating B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al crear compra'}), 500


@app.route('/api/b3c/buy/<purchase_id>/verify', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_verify')
def verify_b3c_purchase(purchase_id):
    """Verificar si un pago de compra B3C fue recibido usando wallet única."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'status': 'confirmed', 'message': 'Demo mode'})
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_purchases 
                    WHERE purchase_id = %s AND user_id = %s
                """, (purchase_id, user_id))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                if purchase['status'] == 'confirmed':
                    return jsonify({'success': True, 'status': 'confirmed', 
                                    'b3c_credited': float(purchase['b3c_amount'])})
        
        wallet_pool = get_wallet_pool_service(db_manager)
        deposit_check = wallet_pool.check_deposit(purchase_id)
        
        if not deposit_check.get('success'):
            return jsonify({
                'success': False,
                'error': deposit_check.get('error', 'Error verificando depósito')
            }), 500
        
        status = deposit_check.get('status')
        
        if status == 'confirmed':
            return jsonify({
                'success': True,
                'status': 'confirmed',
                'b3c_credited': float(purchase['b3c_amount']),
                'tx_hash': deposit_check.get('tx_hash'),
                'amount_received': deposit_check.get('amount_received')
            })
        
        if status == 'expired':
            return jsonify({
                'success': True,
                'status': 'expired',
                'message': 'El tiempo para esta compra expiró. Crea una nueva compra.'
            })
        
        return jsonify({
            'success': True,
            'status': 'pending',
            'message': 'Esperando confirmación de depósito',
            'deposit_address': deposit_check.get('deposit_address'),
            'expected_amount': deposit_check.get('expected_amount'),
            'expires_at': deposit_check.get('expires_at')
        })
                
    except Exception as e:
        logger.error(f"Error verifying B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar compra'}), 500


@app.route('/api/b3c/transactions', methods=['GET'])
@require_telegram_user
def get_b3c_transactions():
    """Obtener historial de transacciones B3C del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        if not db_manager:
            return jsonify({'success': True, 'transactions': [], 'total': 0})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, amount, transaction_type, description, reference_id, created_at
                    FROM wallet_transactions 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))
                transactions = cur.fetchall()
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions WHERE user_id = %s", (user_id,))
                total = cur.fetchone()['count']
                
        return jsonify({
            'success': True,
            'transactions': [{
                'id': tx['id'],
                'amount': float(tx['amount']),
                'type': tx['transaction_type'],
                'description': tx['description'],
                'reference': tx['reference_id'],
                'date': tx['created_at'].isoformat() if tx['created_at'] else None
            } for tx in transactions],
            'total': total,
            'has_more': offset + limit < total
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C transactions: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener transacciones'}), 500


@app.route('/api/b3c/transfer', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_transfer')
def transfer_b3c():
    """Transferir B3C a otro usuario."""
    try:
        data = request.get_json()
        to_username = data.get('toUsername', '').strip().lstrip('@')
        to_user_id = data.get('toUserId', '').strip()
        b3c_amount = float(data.get('amount', 0))
        note = data.get('note', '').strip()[:255]
        
        if b3c_amount < 1:
            return jsonify({'success': False, 'error': 'Minimo 1 B3C para transferir'}), 400
        if b3c_amount > 1000000:
            return jsonify({'success': False, 'error': 'Maximo 1,000,000 B3C por transferencia'}), 400
        
        from_user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        from_username = request.telegram_user.get('username', '') if hasattr(request, 'telegram_user') else ''
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if to_username and not to_user_id:
                    cur.execute("""
                        SELECT user_id, username, first_name FROM users WHERE LOWER(username) = LOWER(%s)
                    """, (to_username,))
                    to_user = cur.fetchone()
                    if not to_user:
                        return jsonify({'success': False, 'error': f'Usuario @{to_username} no encontrado'}), 404
                    to_user_id = to_user['user_id']
                    to_display_name = to_user['username'] or to_user['first_name']
                elif to_user_id:
                    cur.execute("""
                        SELECT user_id, username, first_name FROM users WHERE user_id = %s
                    """, (to_user_id,))
                    to_user = cur.fetchone()
                    if not to_user:
                        return jsonify({'success': False, 'error': 'Usuario destino no encontrado'}), 404
                    to_display_name = to_user['username'] or to_user['first_name']
                else:
                    return jsonify({'success': False, 'error': 'Debes especificar usuario destino'}), 400
                
                if str(from_user_id) == str(to_user_id):
                    return jsonify({'success': False, 'error': 'No puedes transferirte a ti mismo'}), 400
                
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (from_user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    conn.rollback()
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                transfer_id = str(uuid.uuid4())[:8].upper()
                
                cur.execute("""
                    INSERT INTO b3c_transfers (transfer_id, from_user_id, to_user_id, b3c_amount, note, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'completed', NOW())
                """, (transfer_id, from_user_id, to_user_id, b3c_amount, note))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (from_user_id, b3c_amount, f'Enviado a @{to_display_name}', transfer_id))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'credit', %s, %s, NOW())
                """, (to_user_id, b3c_amount, f'Recibido de @{from_username}', transfer_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'transfer_id': transfer_id,
                    'amount': b3c_amount,
                    'to_user': to_display_name,
                    'message': f'Transferencia exitosa de {b3c_amount} B3C a @{to_display_name}'
                })
                
    except Exception as e:
        logger.error(f"Error transferring B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al transferir B3C'}), 500


@app.route('/api/b3c/sell', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_sell')
def sell_b3c():
    """Vender B3C por TON. El usuario recibe TON menos comision."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        destination_wallet = data.get('destinationWallet', '').strip()
        
        if b3c_amount < 100:
            return jsonify({'success': False, 'error': 'Minimo 100 B3C para vender'}), 400
        if b3c_amount > 1000000:
            return jsonify({'success': False, 'error': 'Maximo 1,000,000 B3C por venta'}), 400
        
        is_valid, error_msg = validate_ton_address(destination_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                from tracking.b3c_service import get_b3c_service
                b3c = get_b3c_service()
                calculation = b3c.calculate_ton_from_b3c(b3c_amount)
                
                sell_id = str(uuid.uuid4())[:8].upper()
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (user_id, b3c_amount, f'Venta B3C - {calculation["net_ton"]:.4f} TON', sell_id))
                
                cur.execute("""
                    INSERT INTO b3c_commissions 
                    (user_id, operation_type, b3c_amount, ton_amount, commission_ton, reference_id, created_at)
                    VALUES (%s, 'sell', %s, %s, %s, %s, NOW())
                """, (user_id, b3c_amount, calculation['net_ton'], calculation['commission_ton'], sell_id))
                
                conn.commit()
                
        return jsonify({
            'success': True,
            'sellId': sell_id,
            'b3cSold': b3c_amount,
            'tonReceived': calculation['net_ton'],
            'commission': calculation['commission_ton'],
            'destinationWallet': destination_wallet,
            'status': 'processing',
            'message': f'Venta procesada. Recibiras {calculation["net_ton"]:.4f} TON en tu wallet.'
        })
        
    except Exception as e:
        logger.error(f"Error selling B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al procesar venta'}), 500


@app.route('/api/b3c/withdraw', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_withdraw')
def withdraw_b3c():
    """Retirar B3C a una wallet externa."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        destination_wallet = data.get('destinationWallet', '').strip()
        
        if b3c_amount < 100:
            return jsonify({'success': False, 'error': 'Minimo 100 B3C para retirar'}), 400
        if b3c_amount > 100000:
            return jsonify({'success': False, 'error': 'Maximo 100,000 B3C por retiro diario'}), 400
        
        is_valid, error_msg = validate_ton_address(destination_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                cur.execute("""
                    SELECT COUNT(*) as count FROM b3c_withdrawals 
                    WHERE user_id = %s AND created_at > NOW() - INTERVAL '1 hour'
                """, (user_id,))
                recent = cur.fetchone()
                if recent and recent['count'] >= 3:
                    return jsonify({
                        'success': False, 
                        'error': 'Limite de retiros alcanzado. Espera 1 hora.'
                    }), 429
                
                withdrawal_id = str(uuid.uuid4())[:8].upper()
                withdrawal_fee = 0.5
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (user_id, b3c_amount, f'Retiro B3C a {destination_wallet[:8]}...', withdrawal_id))
                
                cur.execute("""
                    INSERT INTO b3c_withdrawals 
                    (withdrawal_id, user_id, b3c_amount, destination_wallet, status, created_at)
                    VALUES (%s, %s, %s, %s, 'pending', NOW())
                """, (withdrawal_id, user_id, b3c_amount, destination_wallet))
                
                cur.execute("""
                    INSERT INTO b3c_commissions 
                    (user_id, operation_type, b3c_amount, ton_amount, commission_ton, reference_id, created_at)
                    VALUES (%s, 'withdraw', %s, 0, %s, %s, NOW())
                """, (user_id, b3c_amount, withdrawal_fee, withdrawal_id))
                
                conn.commit()
                
        return jsonify({
            'success': True,
            'withdrawalId': withdrawal_id,
            'b3cAmount': b3c_amount,
            'destinationWallet': destination_wallet,
            'networkFee': withdrawal_fee,
            'status': 'pending',
            'estimatedTime': '5-15 minutos',
            'message': f'Retiro de {b3c_amount:,.0f} B3C iniciado. Llegara a tu wallet en 5-15 minutos.'
        })
        
    except Exception as e:
        logger.error(f"Error withdrawing B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al procesar retiro'}), 500


@app.route('/api/b3c/withdraw/<withdrawal_id>/status', methods=['GET'])
@require_telegram_user
def get_withdrawal_status(withdrawal_id):
    """Obtener estado de un retiro."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_withdrawals 
                    WHERE withdrawal_id = %s AND user_id = %s
                """, (withdrawal_id, user_id))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
                
        return jsonify({
            'success': True,
            'withdrawal': {
                'id': withdrawal['withdrawal_id'],
                'amount': float(withdrawal['b3c_amount']),
                'destination': withdrawal['destination_wallet'],
                'status': withdrawal['status'],
                'txHash': withdrawal.get('tx_hash'),
                'createdAt': withdrawal['created_at'].isoformat() if withdrawal['created_at'] else None,
                'processedAt': withdrawal['processed_at'].isoformat() if withdrawal.get('processed_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting withdrawal status: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estado'}), 500


@app.route('/api/b3c/deposit/address', methods=['GET'])
@require_telegram_user
def get_deposit_address():
    """Crear depósito externo con wallet única del pool (reemplaza wallet maestra)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        purchase_id = str(uuid.uuid4())[:8].upper()
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        if not db_manager:
            hot_wallet = os.environ.get('TON_WALLET_ADDRESS', '')
            return jsonify({
                'success': True,
                'depositAddress': hot_wallet,
                'depositMemo': f'DEP-{user_id[:8]}',
                'instructions': ['Demo mode - deposito simulado'],
                'minimumDeposit': 0.1,
                'notice': 'Modo demo'
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO b3c_purchases (purchase_id, user_id, ton_amount, b3c_amount, 
                                               commission_ton, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
                """, (purchase_id, user_id, 0, 0, 0))
                conn.commit()
        
        wallet_pool = get_wallet_pool_service(db_manager)
        wallet_assignment = wallet_pool.assign_wallet_for_purchase(user_id, 0, purchase_id)
        
        if not wallet_assignment or not wallet_assignment.get('success'):
            return jsonify({
                'success': False,
                'error': 'No hay wallets disponibles. Intenta de nuevo.'
            }), 503
        
        return jsonify({
            'success': True,
            'depositAddress': wallet_assignment['deposit_address'],
            'depositMemo': f'EXT-{purchase_id}',
            'purchaseId': purchase_id,
            'expiresAt': wallet_assignment['expires_at'],
            'expiresInMinutes': wallet_assignment['expires_in_minutes'],
            'instructions': [
                'Envia TON a la direccion indicada',
                'Esta direccion es unica para este deposito',
                f"Tienes {wallet_assignment['expires_in_minutes']} minutos para completar",
                'El deposito se detectara automaticamente',
                'Minimo: 0.1 TON'
            ],
            'minimumDeposit': 0.1,
            'notice': 'Esta wallet es unica para ti. Los fondos se acreditaran automaticamente.'
        })
        
    except Exception as e:
        logger.error(f"Error getting deposit address: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener direccion'}), 500


@app.route('/api/b3c/commissions', methods=['GET'])
@require_telegram_user
def get_b3c_commissions():
    """Obtener resumen de comisiones B3C (solo admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': True, 'commissions': [], 'totals': {}})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        operation_type,
                        COUNT(*) as count,
                        SUM(b3c_amount) as total_b3c,
                        SUM(ton_amount) as total_ton,
                        SUM(commission_ton) as total_commission
                    FROM b3c_commissions
                    GROUP BY operation_type
                """)
                by_type = cur.fetchall()
                
                cur.execute("""
                    SELECT SUM(commission_ton) as total FROM b3c_commissions
                """)
                total_result = cur.fetchone()
                total_commissions = float(total_result['total']) if total_result and total_result['total'] else 0
                
                cur.execute("""
                    SELECT * FROM b3c_commissions 
                    ORDER BY created_at DESC LIMIT 50
                """)
                recent = cur.fetchall()
                
        return jsonify({
            'success': True,
            'totals': {
                'totalCommissionsTon': total_commissions,
                'byType': [{
                    'type': row['operation_type'],
                    'count': row['count'],
                    'totalB3c': float(row['total_b3c']) if row['total_b3c'] else 0,
                    'totalTon': float(row['total_ton']) if row['total_ton'] else 0,
                    'totalCommission': float(row['total_commission']) if row['total_commission'] else 0
                } for row in by_type]
            },
            'recentTransactions': [{
                'id': row['id'],
                'userId': row['user_id'],
                'type': row['operation_type'],
                'b3c': float(row['b3c_amount']) if row['b3c_amount'] else 0,
                'ton': float(row['ton_amount']) if row['ton_amount'] else 0,
                'commission': float(row['commission_ton']) if row['commission_ton'] else 0,
                'date': row['created_at'].isoformat() if row['created_at'] else None
            } for row in recent]
        })
        
    except Exception as e:
        logger.error(f"Error getting commissions: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener comisiones'}), 500


@app.route('/api/b3c/scheduler/status', methods=['GET'])
@require_telegram_user
def get_scheduler_status():
    """Obtener estado del scheduler de depósitos automáticos (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        global deposit_scheduler
        if deposit_scheduler:
            return jsonify({
                'success': True,
                'scheduler': deposit_scheduler.get_status(),
                'message': 'Scheduler de depósitos automáticos activo'
            })
        else:
            return jsonify({
                'success': True,
                'scheduler': {'running': False},
                'message': 'Scheduler no inicializado'
            })
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/b3c/wallet-pool/stats', methods=['GET'])
@require_telegram_user
def get_wallet_pool_stats():
    """Obtener estadísticas del pool de wallets de depósito (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': True, 'stats': {'available': 0, 'total': 0}})
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        return jsonify(wallet_pool.get_pool_stats())
        
    except Exception as e:
        logger.error(f"Error getting wallet pool stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadísticas'}), 500


@app.route('/api/b3c/wallet-pool/fill', methods=['POST'])
@require_telegram_user
def fill_wallet_pool():
    """Rellenar el pool de wallets de depósito (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        data = request.get_json() or {}
        min_size = int(data.get('minSize', 10))
        
        added = wallet_pool.ensure_minimum_pool_size(min_size)
        stats = wallet_pool.get_pool_stats()
        
        return jsonify({
            'success': True,
            'walletsAdded': added,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error filling wallet pool: {e}")
        return jsonify({'success': False, 'error': 'Error al rellenar pool'}), 500


@app.route('/api/b3c/wallet-pool/consolidate', methods=['POST'])
@require_telegram_user
def consolidate_wallets():
    """Consolidar fondos de wallets con depósitos a hot wallet (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        consolidated = wallet_pool.consolidate_confirmed_deposits()
        released = wallet_pool.release_expired_wallets()
        
        return jsonify({
            'success': True,
            'walletsConsolidated': consolidated,
            'expiredReleased': released,
            'message': f'Consolidados: {consolidated}, Liberados: {released}'
        })
        
    except Exception as e:
        logger.error(f"Error consolidating wallets: {e}")
        return jsonify({'success': False, 'error': 'Error en consolidación'}), 500


@app.route('/api/b3c/admin/force-verify/<purchase_id>', methods=['POST'])
@require_telegram_user
def admin_force_verify_purchase(purchase_id):
    """Forzar verificación de una compra específica (admin) - ignora expiración."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT dw.id, dw.wallet_address, dw.expected_amount, dw.status,
                           dw.assigned_to_user_id, bp.purchase_id
                    FROM deposit_wallets dw
                    JOIN b3c_purchases bp ON bp.purchase_id = dw.assigned_to_purchase_id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                wallet_data = cur.fetchone()
                
                if not wallet_data:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                logger.info(f"[ADMIN FORCE VERIFY] Purchase {purchase_id}: wallet={wallet_data['wallet_address']}")
                
                deposit = wallet_pool._check_wallet_for_deposit(
                    wallet_data['wallet_address'], 
                    float(wallet_data['expected_amount'])
                )
                
                if deposit.get('found'):
                    cur.execute("""
                        UPDATE deposit_wallets 
                        SET status = 'deposit_confirmed',
                            deposit_detected_at = NOW(),
                            deposit_tx_hash = %s,
                            deposit_amount = %s
                        WHERE id = %s
                    """, (deposit['tx_hash'], deposit['amount'], wallet_data['id']))
                    
                    wallet_pool._credit_b3c_to_user(
                        wallet_data['assigned_to_user_id'], 
                        float(wallet_data['expected_amount']), 
                        purchase_id
                    )
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'status': 'confirmed',
                        'tx_hash': deposit['tx_hash'],
                        'amount_received': deposit['amount'],
                        'purchase_id': purchase_id,
                        'message': 'Depósito confirmado y B3C acreditados'
                    })
                
                return jsonify({
                    'success': False,
                    'status': 'not_found',
                    'message': 'No se encontró depósito en la blockchain',
                    'wallet': wallet_data['wallet_address'],
                    'expected': float(wallet_data['expected_amount']),
                    'api_response': deposit
                })
        
    except Exception as e:
        logger.error(f"Error in admin force verify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/b3c/deposits/check', methods=['POST'])
@require_telegram_user
def check_b3c_deposits():
    """Verificar y procesar depósitos B3C pendientes (admin)."""
    try:
        if not hasattr(request, 'telegram_user') or not request.telegram_user:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401
        
        user_id = str(request.telegram_user.get('id', 0))
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if not owner_id or user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        from tracking.b3c_service import get_b3c_service
        b3c_service = get_b3c_service()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(MAX(last_processed_lt), 0) as last_lt
                    FROM b3c_deposit_cursor
                    WHERE wallet_address = %s
                """, (os.environ.get('TON_WALLET_ADDRESS', ''),))
                cursor_result = cur.fetchone()
                last_lt = int(cursor_result['last_lt']) if cursor_result and cursor_result['last_lt'] else 0
        
        token_configured = bool(os.environ.get('B3C_TOKEN_ADDRESS', ''))
        
        if token_configured:
            poll_result = b3c_service.poll_jetton_deposits(last_lt)
        else:
            poll_result = b3c_service.poll_hot_wallet_deposits(last_lt)
        
        if not poll_result['success']:
            return jsonify({
                'success': False,
                'error': poll_result.get('error', 'Error al consultar blockchain')
            }), 500
        
        processed_deposits = []
        new_deposits = poll_result.get('deposits', [])
        
        for deposit in new_deposits:
            is_valid, user_prefix = b3c_service.validate_deposit_memo(deposit.get('memo', ''))
            
            if not is_valid or not user_prefix:
                logger.warning(f"Depósito sin memo válido: {deposit.get('tx_hash')}")
                continue
            
            tx_hash = deposit.get('tx_hash', '')
            if not tx_hash:
                logger.warning("Depósito sin tx_hash, omitiendo")
                continue
            
            with db_manager.get_connection() as conn:
                raw_conn = conn._conn if hasattr(conn, '_conn') else conn
                try:
                    raw_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
                    with raw_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT user_id FROM users 
                            WHERE user_id LIKE %s
                            LIMIT 1
                        """, (user_prefix + '%',))
                        user_match = cur.fetchone()
                        
                        if not user_match:
                            logger.warning(f"Usuario no encontrado para prefix: {user_prefix}")
                            raw_conn.rollback()
                            continue
                        
                        target_user_id = user_match['user_id']
                        deposit_id = f"DEP-{tx_hash[:16]}"
                        
                        cur.execute("""
                            INSERT INTO b3c_deposits 
                            (deposit_id, user_id, b3c_amount, source_wallet, tx_hash, status, created_at, confirmed_at)
                            VALUES (%s, %s, %s, %s, %s, 'confirmed', NOW(), NOW())
                            ON CONFLICT (tx_hash) DO NOTHING
                        """, (
                            deposit_id,
                            target_user_id,
                            deposit.get('amount', 0),
                            deposit.get('source_wallet', ''),
                            tx_hash
                        ))
                        
                        if cur.rowcount == 1:
                            cur.execute("""
                                UPDATE users SET credits = credits + %s
                                WHERE user_id = %s
                            """, (deposit.get('amount', 0), target_user_id))
                            
                            processed_deposits.append({
                                'depositId': deposit_id,
                                'userId': target_user_id,
                                'amount': deposit.get('amount', 0),
                                'txHash': tx_hash
                            })
                            
                            raw_conn.commit()
                        else:
                            logger.info(f"Depósito {tx_hash} ya procesado, omitiendo")
                            raw_conn.rollback()
                except Exception as tx_error:
                    raw_conn.rollback()
                    logger.error(f"Error procesando depósito {tx_hash}: {tx_error}")
                finally:
                    raw_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        
        if poll_result.get('latest_lt', 0) > last_lt:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO b3c_deposit_cursor (wallet_address, last_processed_lt, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (wallet_address) 
                        DO UPDATE SET last_processed_lt = %s, updated_at = NOW()
                    """, (
                        os.environ.get('TON_WALLET_ADDRESS', ''),
                        poll_result['latest_lt'],
                        poll_result['latest_lt']
                    ))
                    conn.commit()
        
        return jsonify({
            'success': True,
            'checked': len(new_deposits),
            'processed': len(processed_deposits),
            'deposits': processed_deposits,
            'lastLt': poll_result.get('latest_lt', 0),
            'checkedAt': poll_result.get('checked_at')
        })
        
    except Exception as e:
        logger.error(f"Error checking B3C deposits: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar depósitos'}), 500


@app.route('/api/b3c/deposits/history', methods=['GET'])
@require_telegram_user
def get_b3c_deposit_history():
    """Obtener historial de depósitos B3C del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        if not db_manager:
            return jsonify({'success': True, 'deposits': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_deposits 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_id,))
                deposits = cur.fetchall()
                
        return jsonify({
            'success': True,
            'deposits': [{
                'id': d['deposit_id'],
                'amount': float(d['b3c_amount']),
                'status': d['status'],
                'txHash': d.get('tx_hash'),
                'sourceWallet': d.get('source_wallet'),
                'createdAt': d['created_at'].isoformat() if d['created_at'] else None,
                'confirmedAt': d['confirmed_at'].isoformat() if d.get('confirmed_at') else None
            } for d in deposits]
        })
        
    except Exception as e:
        logger.error(f"Error getting deposit history: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener historial'}), 500


@app.route('/api/b3c/deposits/pending', methods=['GET'])
@require_telegram_user
def get_pending_deposits():
    """Obtener depósitos pendientes (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if not db_manager:
            return jsonify({'success': True, 'deposits': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT d.*, u.username, u.first_name
                    FROM b3c_deposits d
                    LEFT JOIN users u ON d.user_id = u.id
                    WHERE d.status = 'pending'
                    ORDER BY d.created_at DESC
                """)
                deposits = cur.fetchall()
                
        return jsonify({
            'success': True,
            'deposits': [{
                'id': d['deposit_id'],
                'userId': d['user_id'],
                'username': d.get('username'),
                'firstName': d.get('first_name'),
                'amount': float(d['b3c_amount']),
                'status': d['status'],
                'txHash': d.get('tx_hash'),
                'sourceWallet': d.get('source_wallet'),
                'createdAt': d['created_at'].isoformat() if d['created_at'] else None
            } for d in deposits]
        })
        
    except Exception as e:
        logger.error(f"Error getting pending deposits: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener pendientes'}), 500


@app.route('/api/b3c/last-purchase', methods=['GET'])
@require_telegram_auth
@require_owner
@rate_limit('price_check', use_ip=True)
def get_last_b3c_purchase():
    """Obtener logs de la última compra de B3C con información del usuario (admin only)."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        bp.purchase_id,
                        bp.user_id,
                        bp.ton_amount,
                        bp.b3c_amount,
                        bp.commission_ton,
                        bp.status,
                        bp.tx_hash,
                        bp.created_at,
                        bp.confirmed_at,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.avatar_url,
                        dw.wallet_address as deposit_wallet,
                        dw.expected_amount as wallet_expected_amount,
                        dw.status as wallet_status,
                        dw.assigned_at as wallet_assigned_at
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    ORDER BY bp.created_at DESC
                    LIMIT 1
                """)
                last_purchase = cur.fetchone()
                
                if not last_purchase:
                    logger.info("[B3C LOGS] No hay compras registradas en el sistema")
                    return jsonify({
                        'success': True,
                        'message': 'No hay compras registradas',
                        'lastPurchase': None
                    })
                
                logger.info(f"[B3C LOGS] ========== ÚLTIMA COMPRA DE B3C ==========")
                logger.info(f"[B3C LOGS] ID de Compra: {last_purchase['purchase_id']}")
                logger.info(f"[B3C LOGS] Usuario ID: {last_purchase['user_id']}")
                logger.info(f"[B3C LOGS] Username: @{last_purchase['username'] or 'N/A'}")
                logger.info(f"[B3C LOGS] Nombre: {last_purchase['first_name'] or 'N/A'} {last_purchase['last_name'] or ''}")
                logger.info(f"[B3C LOGS] TON enviados: {float(last_purchase['ton_amount']):.4f} TON")
                logger.info(f"[B3C LOGS] B3C recibidos: {float(last_purchase['b3c_amount']):.4f} B3C")
                logger.info(f"[B3C LOGS] Comisión: {float(last_purchase['commission_ton']):.4f} TON")
                logger.info(f"[B3C LOGS] Estado: {last_purchase['status']}")
                logger.info(f"[B3C LOGS] Fecha: {last_purchase['created_at']}")
                if last_purchase.get('deposit_wallet'):
                    logger.info(f"[B3C LOGS] Wallet de Depósito: {last_purchase['deposit_wallet']}")
                    logger.info(f"[B3C LOGS] Monto Esperado: {float(last_purchase['wallet_expected_amount'] or 0):.4f} TON")
                    logger.info(f"[B3C LOGS] Estado Wallet: {last_purchase['wallet_status']}")
                if last_purchase['tx_hash']:
                    logger.info(f"[B3C LOGS] TX Hash: {last_purchase['tx_hash']}")
                logger.info(f"[B3C LOGS] =============================================")
                
        return jsonify({
            'success': True,
            'lastPurchase': {
                'purchaseId': last_purchase['purchase_id'],
                'userId': last_purchase['user_id'],
                'username': last_purchase['username'],
                'firstName': last_purchase['first_name'],
                'lastName': last_purchase['last_name'],
                'avatarUrl': last_purchase['avatar_url'],
                'tonAmount': float(last_purchase['ton_amount']),
                'b3cAmount': float(last_purchase['b3c_amount']),
                'commissionTon': float(last_purchase['commission_ton']),
                'status': last_purchase['status'],
                'txHash': last_purchase['tx_hash'],
                'depositWallet': last_purchase.get('deposit_wallet'),
                'walletExpectedAmount': float(last_purchase['wallet_expected_amount']) if last_purchase.get('wallet_expected_amount') else None,
                'walletStatus': last_purchase.get('wallet_status'),
                'createdAt': last_purchase['created_at'].isoformat() if last_purchase['created_at'] else None,
                'confirmedAt': last_purchase['confirmed_at'].isoformat() if last_purchase.get('confirmed_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting last B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener última compra'}), 500


@app.route('/api/devices/trusted', methods=['GET'])
@require_telegram_user
def get_trusted_devices():
    """Obtener lista de dispositivos de confianza del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({'success': True, 'devices': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, device_id, device_name, device_type, created_at, last_used_at, is_active
                    FROM trusted_devices 
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY last_used_at DESC
                """, (user_id,))
                rows = cur.fetchall()
                devices = []
                for row in rows:
                    devices.append({
                        'id': row[0],
                        'deviceId': row[1],
                        'deviceName': row[2],
                        'deviceType': row[3],
                        'createdAt': row[4].isoformat() if row[4] else None,
                        'lastUsedAt': row[5].isoformat() if row[5] else None,
                        'isActive': row[6]
                    })
                    
        return jsonify({'success': True, 'devices': devices})
        
    except Exception as e:
        logger.error(f"Error getting trusted devices: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener dispositivos'}), 500


@app.route('/api/devices/trusted/check', methods=['POST'])
@require_telegram_user
def check_trusted_device():
    """Verificar si el dispositivo actual es de confianza."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id or not db_manager:
            return jsonify({'success': True, 'isTrusted': False})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, device_name FROM trusted_devices 
                    WHERE user_id = %s AND device_id = %s AND is_active = TRUE
                """, (user_id, device_id))
                result = cur.fetchone()
                
                if result:
                    cur.execute("""
                        UPDATE trusted_devices SET last_used_at = NOW()
                        WHERE id = %s
                    """, (result[0],))
                    conn.commit()
                    return jsonify({
                        'success': True, 
                        'isTrusted': True,
                        'deviceName': result[1]
                    })
                    
        return jsonify({'success': True, 'isTrusted': False})
        
    except Exception as e:
        logger.error(f"Error checking trusted device: {e}")
        return jsonify({'success': True, 'isTrusted': False})


@app.route('/api/devices/trusted/add', methods=['POST'])
@require_telegram_user
def add_trusted_device():
    """Agregar un dispositivo de confianza."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        device_name = data.get('deviceName', 'Dispositivo desconocido')
        device_type = data.get('deviceType', 'unknown')
        user_agent = request.headers.get('User-Agent', '')[:500]
        ip_address = request.remote_addr or ''
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trusted_devices (user_id, device_id, device_name, device_type, user_agent, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, device_id) 
                    DO UPDATE SET 
                        device_name = EXCLUDED.device_name,
                        is_active = TRUE,
                        last_used_at = NOW()
                    RETURNING id
                """, (user_id, device_id, device_name, device_type, user_agent, ip_address))
                result = cur.fetchone()
                conn.commit()
                
        logger.info(f"Dispositivo de confianza agregado para usuario {user_id}: {device_name}")
        return jsonify({'success': True, 'message': 'Dispositivo agregado correctamente', 'deviceId': result[0] if result else None})
        
    except Exception as e:
        logger.error(f"Error adding trusted device: {e}")
        return jsonify({'success': False, 'error': 'Error al agregar dispositivo'}), 500


@app.route('/api/devices/trusted/remove', methods=['POST'])
@require_telegram_user
def remove_trusted_device():
    """Eliminar un dispositivo de confianza."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.remove_trusted_device(user_id, device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing trusted device: {e}")
        return jsonify({'success': False, 'error': 'Error al eliminar dispositivo'}), 500


# ============================================================
# ENDPOINTS DE SEGURIDAD - SISTEMA COMPLETO
# ============================================================

@app.route('/api/security/wallet/validate', methods=['POST'])
@require_telegram_user
def validate_wallet_security():
    """Validar que la wallet conectada es la registrada del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        wallet_address = data.get('walletAddress', '')
        device_id = data.get('deviceId', '')
        
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Direccion de wallet requerida'}), 400
        
        if not security_manager:
            return jsonify({'success': True, 'message': 'Demo mode'})
        
        ip_address = request.remote_addr or ''
        result = security_manager.validate_wallet_connection(user_id, wallet_address, device_id, ip_address)
        
        if result.get('is_locked'):
            return jsonify(result), 423
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/wallet/primary', methods=['GET'])
@require_telegram_user
def get_primary_wallet():
    """Obtener la wallet primaria registrada del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({'success': True, 'wallet': None})
        
        wallet = security_manager.get_user_primary_wallet(user_id)
        return jsonify({
            'success': True,
            'hasWallet': wallet is not None,
            'walletHint': f"{wallet[:8]}...{wallet[-4:]}" if wallet else None
        })
        
    except Exception as e:
        logger.error(f"Error getting primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/wallet/backup', methods=['POST'])
@require_telegram_user
def register_backup_wallet():
    """Registrar una wallet de respaldo para emergencias."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        backup_wallet = data.get('backupWallet', '')
        
        is_valid, error_msg = validate_ton_address(backup_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.register_backup_wallet(user_id, backup_wallet.strip())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error registering backup wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/wallet/primary/check', methods=['GET'])
@require_telegram_user
def check_primary_wallet():
    """Verificar si el usuario ya tiene wallet primaria registrada."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({'success': True, 'hasPrimaryWallet': False})
        
        wallet = security_manager.get_user_primary_wallet(user_id)
        return jsonify({
            'success': True,
            'hasPrimaryWallet': wallet is not None,
            'walletHint': f"{wallet[:8]}...{wallet[-4:]}" if wallet else None
        })
        
    except Exception as e:
        logger.error(f"Error checking primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def validate_ton_address(address):
    """Validate TON wallet address format server-side."""
    if not address or not isinstance(address, str):
        return False, 'Direccion de wallet requerida'
    
    address = address.strip()
    
    if len(address) != 48:
        return False, 'La direccion debe tener 48 caracteres'
    
    prefix = address[:2]
    if prefix not in ['EQ', 'UQ']:
        return False, 'Direccion invalida. Debe empezar con EQ o UQ'
    
    import re
    if not re.match(r'^[A-Za-z0-9_-]+$', address):
        return False, 'La direccion contiene caracteres invalidos'
    
    return True, None


@app.route('/api/security/wallet/primary/register', methods=['POST'])
@require_telegram_user
def register_primary_wallet_endpoint():
    """Registrar wallet como primaria (solo si no tiene una)."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        wallet_address = data.get('walletAddress', '')
        
        is_valid, error_msg = validate_ton_address(wallet_address)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.register_primary_wallet(user_id, wallet_address.strip())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error registering primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wallet/debit', methods=['POST'])
@require_telegram_user
def debit_wallet():
    """
    Realizar un debito de BUNK3RCO1N.
    
    Request body:
    {
        "amount": 100,
        "type": "bot_purchase",
        "description": "Compra de Bot X",
        "reference_id": "bot_123"
    }
    """
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        amount = data.get('amount', 0)
        transaction_type = data.get('type', 'purchase')
        description = data.get('description', 'Gasto')
        reference_id = data.get('reference_id', '')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result[0]) if result else 0
                
                if current_balance < amount:
                    return jsonify({
                        'success': False,
                        'error': 'insufficient_balance',
                        'message': 'Saldo insuficiente',
                        'currentBalance': current_balance,
                        'required': amount
                    }), 402
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (user_id, -amount, transaction_type, description, reference_id))
                conn.commit()
                
                new_balance = current_balance - amount
        
        db_manager.create_transaction_notification(
            user_id=user_id,
            amount=amount,
            transaction_type='debit',
            new_balance=new_balance
        )
        
        if amount > 100 and security_manager:
            security_manager.send_telegram_notification(
                user_id,
                f"💸 <b>Gasto registrado</b>\n\n"
                f"📦 {description}\n"
                f"💰 -{amount} BUNK3RCO1N\n"
                f"📊 Saldo restante: {new_balance:.2f} B3C"
            )
        
        logger.info(f"Debito de {amount} B3C para usuario {user_id}: {description}")
        return jsonify({
            'success': True,
            'newBalance': new_balance,
            'amountDebited': amount
        })
        
    except Exception as e:
        logger.error(f"Error debiting wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/status', methods=['GET'])
@require_telegram_user
def get_security_status():
    """Obtener estado de seguridad completo del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({
                'success': True,
                'wallet_connected': False,
                'two_factor_enabled': False,
                'trusted_devices_count': 0,
                'max_devices': 2,
                'security_score': 0,
                'security_level': 'bajo'
            })
        
        status = security_manager.get_security_status(user_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/devices', methods=['GET'])
@require_telegram_user
def get_security_devices():
    """Obtener lista de dispositivos de confianza con info completa."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({'success': True, 'devices': [], 'count': 0, 'max': 2})
        
        devices = security_manager.get_trusted_devices(user_id)
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices),
            'max': security_manager.MAX_TRUSTED_DEVICES
        })
        
    except Exception as e:
        logger.error(f"Error getting security devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/devices/check', methods=['POST'])
@require_telegram_user
def check_device_trust():
    """Verificar si el dispositivo actual es de confianza."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': True, 'isTrusted': False})
        
        if not security_manager:
            return jsonify({'success': True, 'isTrusted': False})
        
        result = security_manager.is_device_trusted(user_id, device_id)
        return jsonify({
            'success': True,
            'isTrusted': result.get('is_trusted', False),
            'deviceName': result.get('device_name'),
            'deviceType': result.get('device_type'),
            'expired': result.get('expired', False)
        })
        
    except Exception as e:
        logger.error(f"Error checking device trust: {e}")
        return jsonify({'success': True, 'isTrusted': False})


@app.route('/api/security/devices/add', methods=['POST'])
@require_telegram_user
def add_security_device():
    """Agregar un dispositivo de confianza (requiere wallet + 2FA)."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        device_name = data.get('deviceName', 'Dispositivo')
        device_type = data.get('deviceType', 'unknown')
        wallet_verified = data.get('walletVerified', False)
        twofa_verified = data.get('twofaVerified', False)
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not wallet_verified:
            return jsonify({'success': False, 'error': 'Debes conectar tu wallet primero', 'requiresWallet': True}), 400
        
        if not twofa_verified:
            return jsonify({'success': False, 'error': 'Debes verificar 2FA primero', 'requires2FA': True}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        user_agent = request.headers.get('User-Agent', '')[:500]
        ip_address = request.remote_addr or ''
        
        result = security_manager.add_trusted_device(
            user_id, device_id, device_name, device_type, user_agent, ip_address
        )
        
        if result.get('max_reached'):
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding security device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/devices/remove', methods=['POST'])
@require_telegram_user
def remove_security_device():
    """Eliminar un dispositivo de confianza (requiere 2FA)."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        twofa_code = data.get('twofaCode', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        if db_manager:
            status = db_manager.get_user_2fa_status(user_id)
            if status['enabled']:
                if not twofa_code or len(twofa_code) != 6:
                    return jsonify({'success': False, 'error': 'Codigo 2FA requerido', 'requires2FA': True}), 400
                
                secret = db_manager.get_user_totp_secret(user_id)
                if secret:
                    import pyotp
                    totp = pyotp.TOTP(secret)
                    if not totp.verify(twofa_code, valid_window=1):
                        return jsonify({'success': False, 'error': 'Codigo 2FA incorrecto'}), 401
        
        result = security_manager.remove_trusted_device(user_id, device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing security device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/devices/remove-all', methods=['POST'])
@require_telegram_user
def remove_all_devices():
    """Cerrar sesion en todos los dispositivos excepto el actual."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        current_device_id = data.get('currentDeviceId', '')
        twofa_code = data.get('twofaCode', '')
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        if db_manager:
            status = db_manager.get_user_2fa_status(user_id)
            if status['enabled']:
                if not twofa_code or len(twofa_code) != 6:
                    return jsonify({'success': False, 'error': 'Codigo 2FA requerido', 'requires2FA': True}), 400
                
                secret = db_manager.get_user_totp_secret(user_id)
                if secret:
                    import pyotp
                    totp = pyotp.TOTP(secret)
                    if not totp.verify(twofa_code, valid_window=1):
                        return jsonify({'success': False, 'error': 'Codigo 2FA incorrecto'}), 401
        
        result = security_manager.remove_all_devices_except_current(user_id, current_device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing all devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/activity', methods=['GET'])
@require_telegram_user
def get_security_activity():
    """Obtener historial de actividad de seguridad."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 50)
        
        if not security_manager:
            return jsonify({'success': True, 'activities': []})
        
        activities = security_manager.get_security_activity(user_id, limit)
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error getting security activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/lockout/check', methods=['GET'])
@require_telegram_user
def check_user_lockout():
    """Verificar si el usuario esta bloqueado."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({'success': True, 'isLocked': False})
        
        is_locked = security_manager.is_user_locked_out(user_id, 'wallet_attempts')
        lockout_time = None
        if is_locked:
            lockout_time = security_manager.get_lockout_time(user_id, 'wallet_attempts')
        
        return jsonify({
            'success': True,
            'isLocked': is_locked,
            'lockedUntil': lockout_time.isoformat() if lockout_time else None
        })
        
    except Exception as e:
        logger.error(f"Error checking lockout: {e}")
        return jsonify({'success': True, 'isLocked': False})


# ============================================================
# ADMIN PANEL - PÁGINA PRINCIPAL Y DASHBOARD
# ============================================================

@app.route('/admin')
def admin_page():
    """Servir la página del panel de administración."""
    # En desarrollo, permitir acceso para modo demo
    if not IS_PRODUCTION:
        return render_template('admin.html')
    
    # En producción, requerir autenticación real
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    if not init_data:
        return jsonify({'error': 'Acceso no autorizado', 'code': 'NO_INIT_DATA'}), 401
    
    validated_data = validate_telegram_webapp_data(init_data)
    if not validated_data:
        return jsonify({'error': 'Datos inválidos'}), 401
    
    user = validated_data.get('user', {})
    if not is_owner(user.get('id')):
        return jsonify({'error': 'Solo para administradores'}), 403
    
    return render_template('admin.html')


@app.route('/api/admin/dashboard/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_stats():
    """Obtener estadísticas del dashboard admin."""
    try:
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'totalUsers': 0,
                    'activeToday': 0,
                    'totalB3C': 0,
                    'hotWalletBalance': 0,
                    'transactions24h': 0,
                    'revenueToday': 0,
                    'usersChange': 0
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_seen >= NOW() - INTERVAL '24 hours'
                """)
                active_today = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
                total_b3c = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM wallet_transactions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                tx_24h = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions 
                    WHERE transaction_type = 'deposit'
                    AND created_at >= NOW() - INTERVAL '24 hours'
                """)
                revenue_today = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                new_users_week = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= NOW() - INTERVAL '14 days'
                    AND created_at < NOW() - INTERVAL '7 days'
                """)
                prev_users_week = cur.fetchone()[0] or 0
                
                users_change = 0
                if prev_users_week > 0:
                    users_change = round(((new_users_week - prev_users_week) / prev_users_week) * 100, 1)
                
                hot_wallet_balance = 0
                try:
                    cur.execute("""
                        SELECT COALESCE(SUM(deposit_amount), 0) 
                        FROM deposit_wallets 
                        WHERE deposit_amount > 0 AND consolidated_at IS NULL
                    """)
                    hot_wallet_balance = float(cur.fetchone()[0] or 0)
                except Exception as hw_err:
                    logger.warning(f"Could not get hot wallet balance: {hw_err}")
                    hot_wallet_balance = 0
        
        return jsonify({
            'success': True,
            'data': {
                'totalUsers': total_users,
                'activeToday': active_today,
                'totalB3C': float(total_b3c),
                'hotWalletBalance': hot_wallet_balance,
                'transactions24h': tx_24h,
                'revenueToday': float(revenue_today),
                'usersChange': users_change
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadísticas'}), 500


@app.route('/api/admin/dashboard/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_activity():
    """Obtener actividad reciente para el dashboard."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'data': []})
        
        activities = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, first_name, username, created_at, 'user_register' as type
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                for row in cur.fetchall():
                    activities.append({
                        'type': 'user',
                        'message': f"Nuevo usuario: {row['first_name'] or row['username'] or row['id']}",
                        'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                cur.execute("""
                    SELECT wt.user_id, wt.amount, wt.transaction_type, wt.created_at, u.first_name
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.created_at DESC
                    LIMIT 5
                """)
                for row in cur.fetchall():
                    tx_type = 'depósito' if row['transaction_type'] == 'deposit' else 'retiro' if row['transaction_type'] == 'withdrawal' else row['transaction_type']
                    activities.append({
                        'type': 'transaction',
                        'message': f"{row['first_name'] or 'Usuario'}: {tx_type} de {row['amount']} TON",
                        'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                    })
        
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        activities = activities[:10]
        
        return jsonify({'success': True, 'data': activities})
        
    except Exception as e:
        logger.error(f"Error getting dashboard activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/dashboard/alerts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_alerts():
    """Obtener alertas del sistema para el dashboard."""
    try:
        alerts = []
        
        if db_manager:
            try:
                with db_manager.get_connection() as conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT id, alert_type, description, created_at, is_resolved
                            FROM security_alerts
                            WHERE is_resolved = false
                            ORDER BY created_at DESC
                            LIMIT 10
                        """)
                        for row in cur.fetchall():
                            alerts.append({
                                'id': row['id'],
                                'level': 'warning' if row['alert_type'] == 'warning' else 'danger',
                                'message': row['description'],
                                'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                            })
                        
                        try:
                            cur.execute("""
                                SELECT COUNT(*) FROM wallet_transactions 
                                WHERE transaction_type = 'withdrawal' 
                                AND created_at >= NOW() - INTERVAL '24 hours'
                            """)
                            recent_withdrawals = cur.fetchone()[0] or 0
                            if recent_withdrawals > 0:
                                alerts.insert(0, {
                                    'id': 'recent_withdrawals',
                                    'level': 'info',
                                    'message': f'{recent_withdrawals} retiros en las últimas 24h',
                                    'timestamp': datetime.now().isoformat()
                                })
                        except Exception as e:
                            logger.debug(f"Error checking withdrawals: {e}")
                        
                        try:
                            cur.execute("""
                                SELECT COUNT(*) FROM posts 
                                WHERE is_reported = true AND is_hidden = false
                            """)
                            pending_reports = cur.fetchone()[0] or 0
                            if pending_reports > 0:
                                alerts.insert(0, {
                                    'id': 'pending_reports',
                                    'level': 'danger',
                                    'message': f'{pending_reports} reportes de contenido sin revisar',
                                    'timestamp': datetime.now().isoformat()
                                })
                        except psycopg2.errors.UndefinedColumn as e:
                            logger.debug(f"Column is_reported not found: {e}")
                        
                        cur.execute("""
                            SELECT COALESCE(SUM(deposit_amount), 0) 
                            FROM deposit_wallets 
                            WHERE deposit_amount > 0 AND consolidated_at IS NULL
                        """)
                        hot_wallet = float(cur.fetchone()[0] or 0)
                        if hot_wallet < 1.0:
                            alerts.insert(0, {
                                'id': 'low_balance',
                                'level': 'danger',
                                'message': f'Balance bajo en Hot Wallet: {hot_wallet:.4f} TON',
                                'timestamp': datetime.now().isoformat()
                            })
            except psycopg2.errors.UndefinedTable:
                logger.info("security_alerts table not found - returning empty alerts")
                alerts = []
        
        return jsonify({'success': True, 'data': alerts})
        
    except Exception as e:
        logger.error(f"Error getting dashboard alerts: {e}")
        return jsonify({'success': True, 'data': []})


@app.route('/api/admin/dashboard/charts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_charts():
    """Obtener datos para gráficos del dashboard."""
    try:
        period = request.args.get('period', '30')
        try:
            days = int(period)
            if days not in [7, 30, 90]:
                days = 30
        except (ValueError, TypeError):
            days = 30
        
        users_data = []
        transactions_data = []
        
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as count
                        FROM users
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    users_by_date = {row['date'].isoformat(): row['count'] for row in cur.fetchall()}
                    
                    cur.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as count
                        FROM wallet_transactions
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    tx_by_date = {row['date'].isoformat(): row['count'] for row in cur.fetchall()}
                    
                    cur.execute("""
                        SELECT DATE(created_at) as date, COALESCE(SUM(amount * 0.02), 0) as revenue
                        FROM wallet_transactions
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        AND transaction_type = 'deposit'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    revenue_by_date = {row['date'].isoformat(): float(row['revenue']) for row in cur.fetchall()}
        else:
            users_by_date = {}
            tx_by_date = {}
            revenue_by_date = {}
        
        from datetime import timedelta
        today = datetime.now().date()
        
        revenue_data = []
        
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            users_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'count': users_by_date.get(date_str, 0)
            })
            transactions_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'count': tx_by_date.get(date_str, 0)
            })
            revenue_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': revenue_by_date.get(date_str, 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'transactions': transactions_data,
                'revenue': revenue_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/ban', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_ban_user(user_id):
    """Banear o desbanear un usuario."""
    try:
        data = request.get_json() or {}
        should_ban = data.get('banned', True)
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET is_banned = %s WHERE id = %s OR telegram_id::text = %s
                    RETURNING is_banned
                """, (should_ban, str(user_id), str(user_id)))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                conn.commit()
        
        action = 'baneado' if should_ban else 'desbaneado'
        return jsonify({'success': True, 'message': f'Usuario {action} correctamente', 'banned': should_ban})
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/detail', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_detail(user_id):
    """Admin: Obtener detalle completo de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, credits,
                           level, is_active, is_verified, wallet_address, created_at, last_seen,
                           COALESCE(is_banned, false) as is_banned
                    FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                user = cur.fetchone()
                
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    SELECT DISTINCT ip_address, device_name, device_type, user_agent, 
                           last_used_at, created_at, is_active
                    FROM trusted_devices WHERE user_id = %s
                    ORDER BY last_used_at DESC NULLS LAST LIMIT 20
                """, (str(user.get('telegram_id', user_id)),))
                devices = cur.fetchall()
                
                cur.execute("""
                    SELECT DISTINCT ip_address, activity_type, created_at
                    FROM security_activity_log 
                    WHERE user_id = %s AND ip_address IS NOT NULL AND ip_address != ''
                    ORDER BY created_at DESC LIMIT 50
                """, (str(user.get('telegram_id', user_id)),))
                ip_history = cur.fetchall()
                
                cur.execute("""
                    SELECT id, transaction_type as type, amount, description, created_at
                    FROM wallet_transactions WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 50
                """, (str(user.get('telegram_id', user_id)),))
                transactions = cur.fetchall()
                
                cur.execute("""
                    SELECT id, content_type, caption, created_at, is_active
                    FROM posts WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 20
                """, (str(user.get('telegram_id', user_id)),))
                publications = cur.fetchall()
                
                cur.execute("""
                    SELECT id, note, created_by, created_at
                    FROM admin_user_notes WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (str(user_id),))
                notes = cur.fetchall()
                
                cur.execute("""
                    SELECT id, activity_type, description, ip_address, created_at
                    FROM security_activity_log WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 30
                """, (str(user.get('telegram_id', user_id)),))
                activity_log = cur.fetchall()
                
                ips_from_devices = [d['ip_address'] for d in devices if d.get('ip_address')]
                ips_from_history = [ip['ip_address'] for ip in ip_history if ip.get('ip_address')]
                all_ips = list(set(ips_from_devices + ips_from_history))
                
                fraud_alerts = []
                if all_ips:
                    cur.execute("""
                        SELECT DISTINCT user_id, ip_address 
                        FROM trusted_devices 
                        WHERE ip_address = ANY(%s) AND user_id != %s
                    """, (all_ips, str(user.get('telegram_id', user_id))))
                    other_users_same_ip = cur.fetchall()
                    if other_users_same_ip:
                        fraud_alerts.append({
                            'type': 'multiple_accounts',
                            'message': f'IP compartida con {len(set([u["user_id"] for u in other_users_same_ip]))} otros usuarios',
                            'ips': list(set([u['ip_address'] for u in other_users_same_ip]))
                        })
        
        ips_used = all_ips if all_ips else []
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user['id']),
                'telegram_id': user['telegram_id'],
                'username': user.get('username'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'credits': float(user.get('credits', 0)),
                'level': user.get('level', 1),
                'is_active': user.get('is_active', True),
                'is_verified': user.get('is_verified', False),
                'is_banned': user.get('is_banned', False),
                'wallet_address': user.get('wallet_address'),
                'created_at': str(user.get('created_at', '')),
                'last_seen': str(user.get('last_seen', ''))
            },
            'devices': [{
                'ip': d['ip_address'],
                'device': d['device_name'],
                'device_type': d.get('device_type'),
                'user_agent': d.get('user_agent'),
                'is_active': d.get('is_active', True),
                'last_used': str(d['last_used_at']) if d.get('last_used_at') else None,
                'created_at': str(d['created_at']) if d.get('created_at') else None
            } for d in devices],
            'ips': ips_used,
            'activity_log': [{
                'id': a['id'],
                'type': a['activity_type'],
                'description': a.get('description', ''),
                'ip': a.get('ip_address'),
                'date': str(a['created_at'])
            } for a in activity_log],
            'fraud_alerts': fraud_alerts,
            'transactions': [{
                'id': t['id'],
                'type': t['type'],
                'amount': float(t['amount']) if t.get('amount') else 0,
                'description': t.get('description', ''),
                'date': str(t['created_at'])
            } for t in transactions],
            'publications': [{
                'id': p['id'],
                'type': p['content_type'],
                'caption': p.get('caption', '')[:100] if p.get('caption') else '',
                'date': str(p['created_at']),
                'active': p.get('is_active', True)
            } for p in publications],
            'notes': [{
                'id': n['id'],
                'note': n['note'],
                'created_by': n.get('created_by'),
                'date': str(n['created_at'])
            } for n in notes]
        })
        
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/balance', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_adjust_user_balance(user_id):
    """Admin: Ajustar balance B3C de un usuario."""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        reason = data.get('reason', 'Ajuste manual por admin')
        
        if amount == 0:
            return jsonify({'success': False, 'error': 'El monto no puede ser 0'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE users SET credits = credits + %s
                    WHERE id = %s OR telegram_id::text = %s
                    RETURNING id, credits
                """, (amount, str(user_id), str(user_id)))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, description)
                    VALUES (%s, 'admin_adjustment', %s, %s)
                """, (str(user_id), amount, f'{reason} (Admin: {admin_id})'))
                
                conn.commit()
        
        action = 'agregados' if amount > 0 else 'deducidos'
        return jsonify({
            'success': True,
            'message': f'{abs(amount)} B3C {action} correctamente',
            'new_balance': float(result['credits'])
        })
        
    except Exception as e:
        logger.error(f"Error adjusting balance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/note', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_user_note(user_id):
    """Admin: Agregar nota interna sobre un usuario."""
    try:
        data = request.get_json() or {}
        note = data.get('note', '').strip()
        
        if not note:
            return jsonify({'success': False, 'error': 'La nota no puede estar vacía'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_user_notes (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        note TEXT NOT NULL,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO admin_user_notes (user_id, note, created_by)
                    VALUES (%s, %s, %s) RETURNING id
                """, (str(user_id), note, admin_id))
                note_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Nota agregada', 'note_id': note_id})
        
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/logout', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_logout_user(user_id):
    """Admin: Cerrar todas las sesiones de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE trusted_devices SET is_active = false
                    WHERE user_id = %s
                """, (str(user_id),))
                devices_closed = cur.rowcount
                
                cur.execute("""
                    INSERT INTO security_activity_log (user_id, activity_type, description)
                    VALUES (%s, 'ADMIN_LOGOUT', %s)
                """, (str(user_id), f'Sesiones cerradas por admin {admin_id}'))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'{devices_closed} sesiones cerradas',
            'sessions_closed': devices_closed
        })
        
    except Exception as e:
        logger.error(f"Error closing user sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/notify', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_notify_user(user_id):
    """Admin: Enviar notificación a un usuario."""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        notification_type = data.get('type', 'admin')
        
        if not message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    INSERT INTO notifications (user_id, type, message, is_read, created_at)
                    VALUES (%s, %s, %s, false, NOW())
                    RETURNING id
                """, (str(user_id), notification_type, f'[Admin] {message}'))
                notification_id = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO admin_user_notes (user_id, note, created_by)
                    VALUES (%s, %s, %s)
                """, (str(user_id), f'[NOTIFICACIÓN ENVIADA] {message}', admin_id))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notificación enviada',
            'notification_id': notification_id
        })
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/fraud/multiple-accounts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_fraud_multiple_accounts():
    """Admin: Detectar múltiples cuentas usando misma IP."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'suspicious': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT ip_address, COUNT(DISTINCT user_id) as user_count,
                           ARRAY_AGG(DISTINCT user_id) as user_ids
                    FROM trusted_devices
                    WHERE ip_address IS NOT NULL AND ip_address != ''
                    GROUP BY ip_address
                    HAVING COUNT(DISTINCT user_id) > 1
                    ORDER BY user_count DESC
                    LIMIT 50
                """)
                results = cur.fetchall()
        
        suspicious = []
        for r in results:
            suspicious.append({
                'ip': r['ip_address'],
                'user_count': r['user_count'],
                'user_ids': r['user_ids']
            })
        
        return jsonify({'success': True, 'suspicious': suspicious, 'count': len(suspicious)})
        
    except Exception as e:
        logger.error(f"Error detecting multiple accounts: {e}")
        return jsonify({'success': True, 'suspicious': []})


@app.route('/api/admin/fraud/ip-blacklist', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_ip_blacklist():
    """Admin: Obtener lista de IPs bloqueadas."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'blacklist': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ip_blacklist (
                        id SERIAL PRIMARY KEY,
                        ip_address TEXT UNIQUE NOT NULL,
                        reason TEXT,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    SELECT id, ip_address, reason, created_by, created_at
                    FROM ip_blacklist ORDER BY created_at DESC
                """)
                ips = cur.fetchall()
                conn.commit()
        
        return jsonify({
            'success': True,
            'blacklist': [{
                'id': ip['id'],
                'ip': ip['ip_address'],
                'reason': ip.get('reason'),
                'created_by': ip.get('created_by'),
                'date': str(ip['created_at'])
            } for ip in ips]
        })
        
    except Exception as e:
        logger.error(f"Error getting IP blacklist: {e}")
        return jsonify({'success': True, 'blacklist': []})


@app.route('/api/admin/fraud/ip-blacklist', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_ip_blacklist():
    """Admin: Agregar IP a la blacklist."""
    try:
        data = request.get_json() or {}
        ip = data.get('ip', '').strip()
        reason = data.get('reason', 'Sin razón especificada')
        
        if not ip:
            return jsonify({'success': False, 'error': 'IP requerida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ip_blacklist (ip_address, reason, created_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET reason = EXCLUDED.reason
                    RETURNING id
                """, (ip, reason, admin_id))
                conn.commit()
        
        return jsonify({'success': True, 'message': f'IP {ip} agregada a blacklist'})
        
    except Exception as e:
        logger.error(f"Error adding IP to blacklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/fraud/ip-blacklist/<int:ip_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_remove_ip_blacklist(ip_id):
    """Admin: Remover IP de la blacklist."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ip_blacklist WHERE id = %s RETURNING ip_address", (ip_id,))
                result = cur.fetchone()
                if not result:
                    return jsonify({'success': False, 'error': 'IP no encontrada'}), 404
                conn.commit()
        
        return jsonify({'success': True, 'message': f'IP {result[0]} removida de blacklist'})
        
    except Exception as e:
        logger.error(f"Error removing IP from blacklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/realtime/online', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_realtime_online():
    """Obtener usuarios online en tiempo real."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'count': 0, 'users': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, username, first_name, last_seen
                    FROM users
                    WHERE last_seen >= NOW() - INTERVAL '5 minutes'
                    ORDER BY last_seen DESC
                    LIMIT 50
                """)
                users = cur.fetchall()
                
                users_list = []
                for u in users:
                    users_list.append({
                        'user_id': u['id'],
                        'username': u['username'],
                        'first_name': u['first_name'],
                        'last_seen': u['last_seen'].isoformat() if u['last_seen'] else None
                    })
        
        return jsonify({'success': True, 'count': len(users_list), 'users': users_list})
        
    except Exception as e:
        logger.error(f"Error getting online users: {e}")
        return jsonify({'success': True, 'count': 0, 'users': []})


@app.route('/api/admin/sessions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_sessions():
    """Obtener sesiones activas."""
    try:
        if not security_manager:
            return jsonify({'success': True, 'sessions': []})
        
        sessions = []
        
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT td.user_id, td.device_name, td.last_used_at, td.ip_address,
                               u.first_name, u.username
                        FROM trusted_devices td
                        LEFT JOIN users u ON td.user_id = u.id
                        WHERE td.last_used_at >= NOW() - INTERVAL '24 hours'
                        ORDER BY td.last_used_at DESC
                        LIMIT 100
                    """)
                    for row in cur.fetchall():
                        sessions.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'first_name': row['first_name'],
                            'device': row['device_name'],
                            'ip': row['ip_address'],
                            'last_activity': row['last_used_at'].isoformat() if row['last_used_at'] else None
                        })
        
        return jsonify({'success': True, 'sessions': sessions})
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({'success': True, 'sessions': []})


@app.route('/api/admin/sessions/terminate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_terminate_session():
    """Admin: Terminar sesion especifica de un dispositivo."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        data = request.json or {}
        user_id = data.get('user_id')
        device_name = data.get('device_name')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id requerido'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if device_name:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id = %s AND device_name = %s
                    """, (user_id, device_name))
                else:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id = %s
                    """, (user_id,))
                
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'{deleted} sesion(es) terminada(s)',
                    'deleted': deleted
                })
                
    except Exception as e:
        logger.error(f"Error terminating session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/sessions/terminate-all/<user_id>', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_terminate_all_user_sessions(user_id):
    """Admin: Terminar todas las sesiones de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM trusted_devices WHERE user_id = %s
                """, (user_id,))
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Todas las sesiones de usuario {user_id} terminadas ({deleted})',
                    'deleted': deleted
                })
                
    except Exception as e:
        logger.error(f"Error terminating all user sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/sessions/logout-all', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_logout_all_users():
    """Admin: Cerrar todas las sesiones de todos los usuarios (excepto admins)."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        data = request.json or {}
        exclude_admins = data.get('exclude_admins', True)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if exclude_admins:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id NOT IN (
                            SELECT id FROM users WHERE LOWER(role) IN ('owner', 'admin')
                        )
                    """)
                else:
                    cur.execute("DELETE FROM trusted_devices")
                
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Todas las sesiones cerradas ({deleted} dispositivos)',
                    'deleted': deleted
                })
                
    except Exception as e:
        logger.error(f"Error logging out all users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE ADMIN - SEGURIDAD
# ============================================================

@app.route('/api/admin/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_stats():
    """Admin: Obtener estadisticas generales del sistema (solo owner)."""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({
                'success': True,
                'total_users': 0,
                'active_bots': 0,
                'total_transactions': 0,
                'security_alerts': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM user_bots WHERE is_active = true")
                active_bots = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions")
                total_transactions = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM security_alerts WHERE resolved = false")
                security_alerts = cur.fetchone()[0] or 0
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'active_bots': active_bots,
            'total_transactions': total_transactions,
            'security_alerts': security_alerts
        })
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener estadisticas'
        }), 500


@app.route('/api/admin/security/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_users_devices():
    """Admin: Obtener todos los usuarios con sus dispositivos."""
    try:
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        users = security_manager.get_all_users_devices_admin()
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/user/<user_id>/devices', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_devices(user_id):
    """Admin: Obtener dispositivos de un usuario especifico."""
    try:
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        devices = security_manager.get_trusted_devices(user_id)
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get user devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/user/<user_id>/device/remove', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_remove_user_device(user_id):
    """Admin: Eliminar dispositivo de un usuario."""
    try:
        admin_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.admin_remove_user_device(user_id, device_id, admin_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in admin remove device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/alerts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_alerts():
    """Admin: Obtener alertas de seguridad."""
    try:
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        unresolved_only = request.args.get('unresolved', 'true').lower() == 'true'
        alerts = security_manager.get_security_alerts_admin(unresolved_only)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/alerts/<int:alert_id>/resolve', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_resolve_alert(alert_id):
    """Admin: Resolver una alerta de seguridad."""
    try:
        admin_id = str(request.telegram_user.get('id', 0))
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        success = security_manager.resolve_alert_admin(alert_id, admin_id)
        return jsonify({
            'success': success,
            'message': 'Alerta resuelta' if success else 'No se pudo resolver la alerta'
        })
        
    except Exception as e:
        logger.error(f"Error in admin resolve alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/statistics', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_stats():
    """Admin: Obtener estadisticas de seguridad."""
    try:
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        stats = security_manager.get_device_statistics_admin()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in admin get stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/security/user/<user_id>/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_activity(user_id):
    """Admin: Obtener actividad de seguridad de un usuario."""
    try:
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        activities = security_manager.get_security_activity(user_id, limit)
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error in admin get user activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_all_users():
    """Admin: Obtener todos los usuarios con paginación, búsqueda y filtros."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, username, first_name, last_name, telegram_id, 
                           credits, level, is_active, is_verified, wallet_address,
                           created_at, last_seen,
                           COALESCE(is_banned, false) as is_banned
                    FROM users 
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
                params = []
                count_params = []
                
                if search:
                    search_pattern = f"%{search}%"
                    query += " AND (username ILIKE %s OR first_name ILIKE %s OR CAST(telegram_id AS TEXT) ILIKE %s OR CAST(id AS TEXT) = %s)"
                    count_query += " AND (username ILIKE %s OR first_name ILIKE %s OR CAST(telegram_id AS TEXT) ILIKE %s OR CAST(id AS TEXT) = %s)"
                    params.extend([search_pattern, search_pattern, search_pattern, search])
                    count_params.extend([search_pattern, search_pattern, search_pattern, search])
                
                if status == 'active':
                    query += " AND (is_banned IS NULL OR is_banned = false)"
                    count_query += " AND (is_banned IS NULL OR is_banned = false)"
                elif status == 'banned':
                    query += " AND is_banned = true"
                    count_query += " AND is_banned = true"
                elif status == 'verified':
                    query += " AND is_verified = true"
                    count_query += " AND is_verified = true"
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['total'] or 0
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                users = cur.fetchall()
        
        pages = max(1, (total + limit - 1) // limit)
        
        return jsonify({
            'success': True,
            'users': [{
                'user_id': str(u['id']),
                'id': u['id'],
                'telegram_id': u.get('telegram_id'),
                'username': u.get('username'),
                'first_name': u.get('first_name'),
                'last_name': u.get('last_name'),
                'credits': float(u.get('credits', 0)),
                'level': u.get('level', 1),
                'is_active': u.get('is_active', True),
                'is_verified': u.get('is_verified', False),
                'is_banned': u.get('is_banned', False),
                'wallet_address': u.get('wallet_address'),
                'created_at': str(u.get('created_at', '')),
                'last_seen': str(u.get('last_seen', ''))
            } for u in users],
            'total': total,
            'page': page,
            'pages': pages,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_export_users():
    """Admin: Exportar usuarios a CSV."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, 
                           credits, is_active, is_verified, wallet_address,
                           created_at, last_seen
                    FROM users 
                    ORDER BY created_at DESC
                """)
                users = cur.fetchall()
        
        csv_lines = ['ID,Telegram ID,Username,Nombre,Apellido,Credits,Activo,Verificado,Wallet,Registro,Ultima Conexion']
        for u in users:
            csv_lines.append(','.join([
                str(u.get('id', '')),
                str(u.get('telegram_id', '')),
                str(u.get('username', '') or ''),
                str(u.get('first_name', '') or ''),
                str(u.get('last_name', '') or ''),
                str(u.get('credits', 0)),
                'Si' if u.get('is_active') else 'No',
                'Si' if u.get('is_verified') else 'No',
                str(u.get('wallet_address', '') or ''),
                str(u.get('created_at', '') or ''),
                str(u.get('last_seen', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines)
        })
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/transactions/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_export_transactions():
    """Admin: Exportar transacciones a CSV."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.id, wt.user_id, wt.transaction_type, wt.amount, 
                           wt.status, wt.tx_hash, wt.created_at,
                           u.username, u.first_name
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.created_at DESC
                    LIMIT 10000
                """)
                transactions = cur.fetchall()
        
        csv_lines = ['ID,Usuario ID,Username,Nombre,Tipo,Monto,Estado,TX Hash,Fecha']
        for tx in transactions:
            csv_lines.append(','.join([
                str(tx.get('id', '')),
                str(tx.get('user_id', '')),
                str(tx.get('username', '') or ''),
                str(tx.get('first_name', '') or ''),
                str(tx.get('transaction_type', '')),
                str(tx.get('amount', 0)),
                str(tx.get('status', '')),
                str(tx.get('tx_hash', '') or ''),
                str(tx.get('created_at', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines)
        })
        
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/financial/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_stats():
    """Admin: Dashboard financiero con métricas de B3C, TON y comisiones."""
    try:
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'totalB3CSold': 0,
                    'totalTONReceived': 0,
                    'totalCommissions': 0,
                    'monthVolume': 0,
                    'lastMonthVolume': 0,
                    'volumeChange': 0,
                    'pendingWithdrawals': 0,
                    'pendingWithdrawalsAmount': 0,
                    'dailyRevenue': [],
                    'dailyVolume': []
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END), 0) as total_b3c_sold,
                           COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount * 0.1 ELSE 0 END), 0) as total_ton_received,
                           COALESCE(SUM(CASE WHEN transaction_type IN ('deposit', 'withdrawal') THEN amount * 0.02 ELSE 0 END), 0) as total_commissions
                    FROM wallet_transactions
                """)
                totals = cur.fetchone()
                total_b3c_sold = float(totals['total_b3c_sold']) if totals else 0
                total_ton_received = float(totals['total_ton_received']) if totals else 0
                total_commissions = float(totals['total_commissions']) if totals else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                month_vol = cur.fetchone()
                month_volume = float(month_vol['month_volume']) if month_vol else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as last_month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                    AND created_at < DATE_TRUNC('month', CURRENT_DATE)
                """)
                last_month_vol = cur.fetchone()
                last_month_volume = float(last_month_vol['last_month_volume']) if last_month_vol else 0
                
                volume_change = 0
                if last_month_volume > 0:
                    volume_change = round(((month_volume - last_month_volume) / last_month_volume) * 100, 1)
                
                try:
                    cur.execute("""
                        SELECT COUNT(*) as count, COALESCE(SUM(amount_ton), 0) as total
                        FROM b3c_withdrawals
                        WHERE status = 'pending'
                    """)
                    pending = cur.fetchone()
                    pending_withdrawals = int(pending['count']) if pending else 0
                    pending_withdrawals_amount = float(pending['total']) if pending else 0
                except psycopg2.errors.UndefinedTable as e:
                    logger.debug(f"b3c_withdrawals table not found: {e}")
                    pending_withdrawals = 0
                    pending_withdrawals_amount = 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount * 0.02), 0) as revenue
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                revenue_data = cur.fetchall()
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                volume_data = cur.fetchall()
        
        from datetime import datetime, timedelta
        
        daily_revenue = []
        daily_volume = []
        revenue_dict = {row['date'].isoformat(): float(row['revenue']) for row in revenue_data} if revenue_data else {}
        volume_dict = {row['date'].isoformat(): float(row['volume']) for row in volume_data} if volume_data else {}
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date()
            date_str = date.isoformat()
            daily_revenue.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': revenue_dict.get(date_str, 0)
            })
            daily_volume.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': volume_dict.get(date_str, 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': total_b3c_sold,
                'totalTONReceived': total_ton_received,
                'totalCommissions': total_commissions,
                'monthVolume': month_volume,
                'lastMonthVolume': last_month_volume,
                'volumeChange': volume_change,
                'pendingWithdrawals': pending_withdrawals,
                'pendingWithdrawalsAmount': pending_withdrawals_amount,
                'dailyRevenue': daily_revenue,
                'dailyVolume': daily_volume
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting financial stats: {e}")
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': 0,
                'totalTONReceived': 0,
                'totalCommissions': 0,
                'monthVolume': 0,
                'lastMonthVolume': 0,
                'volumeChange': 0,
                'pendingWithdrawals': 0,
                'pendingWithdrawalsAmount': 0,
                'dailyRevenue': [],
                'dailyVolume': []
            }
        })


@app.route('/api/admin/financial/period-stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats():
    """Admin: Estadísticas financieras por período personalizado."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'txCount': 0,
                    'b3cVolume': 0,
                    'purchases': {'count': 0, 'tonAmount': 0, 'b3cAmount': 0},
                    'withdrawals': {'count': 0, 'b3cAmount': 0},
                    'transfers': {'count': 0, 'b3cAmount': 0},
                    'commissions': 0,
                    'dailyVolume': [],
                    'typeBreakdown': {'purchases': 0, 'withdrawals': 0, 'transfers': 0}
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                tx_totals = cur.fetchone()
                tx_count = int(tx_totals['count']) if tx_totals else 0
                b3c_volume = float(tx_totals['volume']) if tx_totals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, 
                           COALESCE(SUM(amount), 0) as b3c_amount,
                           COALESCE(SUM(amount * 0.1), 0) as ton_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'deposit' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                purchases = cur.fetchone()
                purchases_count = int(purchases['count']) if purchases else 0
                purchases_b3c = float(purchases['b3c_amount']) if purchases else 0
                purchases_ton = float(purchases['ton_amount']) if purchases else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'withdrawal' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                withdrawals = cur.fetchone()
                withdrawals_count = int(withdrawals['count']) if withdrawals else 0
                withdrawals_b3c = float(withdrawals['b3c_amount']) if withdrawals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'transfer' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                transfers = cur.fetchone()
                transfers_count = int(transfers['count']) if transfers else 0
                transfers_b3c = float(transfers['b3c_amount']) if transfers else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount * 0.02), 0) as commissions
                    FROM wallet_transactions
                    WHERE transaction_type IN ('deposit', 'withdrawal')
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                comm = cur.fetchone()
                commissions = float(comm['commissions']) if comm else 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (date_from, date_to))
                daily_data = cur.fetchall()
        
        daily_volume = []
        if daily_data:
            for row in daily_data:
                daily_volume.append({
                    'date': row['date'].isoformat(),
                    'label': row['date'].strftime('%d/%m'),
                    'amount': float(row['volume'])
                })
        
        return jsonify({
            'success': True,
            'data': {
                'txCount': tx_count,
                'b3cVolume': b3c_volume,
                'purchases': {
                    'count': purchases_count,
                    'tonAmount': purchases_ton,
                    'b3cAmount': purchases_b3c
                },
                'withdrawals': {
                    'count': withdrawals_count,
                    'b3cAmount': withdrawals_b3c
                },
                'transfers': {
                    'count': transfers_count,
                    'b3cAmount': transfers_b3c
                },
                'commissions': commissions,
                'dailyVolume': daily_volume,
                'typeBreakdown': {
                    'purchases': purchases_count,
                    'withdrawals': withdrawals_count,
                    'transfers': transfers_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadísticas'}), 500


@app.route('/api/admin/financial/period-stats/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats_export():
    """Admin: Exportar estadísticas por período a CSV."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        if not db_manager:
            return jsonify({'success': True, 'csv': 'No hay datos disponibles'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.id, u.telegram_id, u.username, u.first_name,
                           wt.transaction_type, wt.amount, wt.status, wt.tx_hash, wt.created_at
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    WHERE wt.created_at >= %s AND wt.created_at <= %s::date + INTERVAL '1 day'
                    ORDER BY wt.created_at DESC
                """, (date_from, date_to))
                transactions = cur.fetchall()
        
        csv_lines = ['ID,Telegram ID,Username,Nombre,Tipo,Monto,Estado,TX Hash,Fecha']
        for tx in transactions:
            csv_lines.append(','.join([
                str(tx.get('id', '')),
                str(tx.get('telegram_id', '')),
                str(tx.get('username', '') or ''),
                str(tx.get('first_name', '') or ''),
                str(tx.get('transaction_type', '')),
                str(tx.get('amount', 0)),
                str(tx.get('status', '')),
                str(tx.get('tx_hash', '') or ''),
                str(tx.get('created_at', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines),
            'filename': f'estadisticas_{date_from}_{date_to}.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al exportar'}), 500


@app.route('/api/admin/content/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_content_stats():
    """Admin: Estadísticas de contenido."""
    try:
        if not db_manager:
            return jsonify({
                'success': True,
                'totalPosts': 0,
                'postsToday': 0,
                'totalMedia': 0,
                'totalStories': 0,
                'reportedPosts': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM posts WHERE is_active = true")
                total_posts = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM posts 
                    WHERE is_active = true AND created_at >= NOW() - INTERVAL '24 hours'
                """)
                posts_today = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM posts 
                    WHERE is_active = true AND content_type IN ('image', 'video')
                """)
                total_media = cur.fetchone()[0] or 0
                
                total_stories = 0
                try:
                    cur.execute("""
                        SELECT COUNT(*) FROM stories 
                        WHERE is_active = true AND expires_at > NOW()
                    """)
                    total_stories = cur.fetchone()[0] or 0
                except psycopg2.errors.UndefinedTable as e:
                    logger.debug(f"stories table not found: {e}")
                
                reported_posts = 0
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT post_id) FROM reports 
                        WHERE status = 'pending' AND post_id IS NOT NULL
                    """)
                    reported_posts = cur.fetchone()[0] or 0
                except psycopg2.errors.UndefinedTable as e:
                    logger.debug(f"reports table not found: {e}")
        
        return jsonify({
            'success': True,
            'totalPosts': total_posts,
            'postsToday': posts_today,
            'totalMedia': total_media,
            'totalStories': total_stories,
            'reportedPosts': reported_posts
        })
        
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        return jsonify({
            'success': True,
            'totalPosts': 0,
            'postsToday': 0,
            'totalMedia': 0,
            'totalStories': 0,
            'reportedPosts': 0
        })


@app.route('/api/admin/content/posts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_content_posts():
    """Admin: Listar publicaciones para moderación con filtros."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'posts': [], 'total': 0})
        
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '').strip()
        content_type = request.args.get('content_type', '').strip()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT p.id, p.user_id, p.content_type, p.caption, p.content_url,
                           p.likes_count, p.comments_count, p.shares_count,
                           p.is_active, p.created_at,
                           u.username, u.first_name
                    FROM posts p
                    LEFT JOIN users u ON p.user_id = u.telegram_id::text
                    WHERE 1=1
                """
                params = []
                
                if search:
                    query += " AND (LOWER(p.caption) LIKE LOWER(%s) OR LOWER(u.username) LIKE LOWER(%s))"
                    search_pattern = f"%{search}%"
                    params.extend([search_pattern, search_pattern])
                
                if content_type:
                    query += " AND p.content_type = %s"
                    params.append(content_type)
                
                query += " ORDER BY p.created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                posts = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM posts p LEFT JOIN users u ON p.user_id = u.telegram_id::text WHERE 1=1"
                count_params = []
                
                if search:
                    count_query += " AND (LOWER(p.caption) LIKE LOWER(%s) OR LOWER(u.username) LIKE LOWER(%s))"
                    count_params.extend([f"%{search}%", f"%{search}%"])
                
                if content_type:
                    count_query += " AND p.content_type = %s"
                    count_params.append(content_type)
                
                cur.execute(count_query, count_params)
                total_row = cur.fetchone()
                total = total_row['total'] if total_row else 0
        
        result = []
        for p in posts:
            p_dict = dict(p)
            if p_dict.get('created_at'):
                p_dict['created_at'] = p_dict['created_at'].isoformat()
            result.append(p_dict)
        
        return jsonify({
            'success': True,
            'posts': result,
            'total': total
        })
        
    except Exception as e:
        logger.error(f"Error getting content posts: {e}")
        return jsonify({'success': True, 'posts': [], 'total': 0})


@app.route('/api/admin/content/posts/<int:post_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_post(post_id):
    """Admin: Eliminar una publicación."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE posts SET is_active = false WHERE id = %s", (post_id,))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Publicación eliminada'})
        
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/content/posts/<int:post_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_post_detail(post_id):
    """Admin: Obtener detalle de una publicación."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.*, u.username, u.first_name, u.last_name, u.avatar_url,
                           u.is_banned as user_banned
                    FROM posts p
                    LEFT JOIN users u ON p.user_id = u.telegram_id::text
                    WHERE p.id = %s
                """, (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicación no encontrada'}), 404
                
                cur.execute("""
                    SELECT COUNT(*) as report_count FROM content_reports 
                    WHERE content_type = 'post' AND content_id = %s
                """, (post_id,))
                report_count = cur.fetchone()['report_count'] or 0
                
                cur.execute("""
                    SELECT id, reporter_id, reason, description, status, created_at 
                    FROM content_reports 
                    WHERE content_type = 'post' AND content_id = %s
                    ORDER BY created_at DESC
                """, (post_id,))
                reports = cur.fetchall()
        
        post_data = dict(post)
        post_data['report_count'] = report_count
        post_data['reports'] = [dict(r) for r in reports]
        
        if post_data.get('created_at'):
            post_data['created_at'] = post_data['created_at'].isoformat()
        
        return jsonify({'success': True, 'post': post_data})
        
    except Exception as e:
        logger.error(f"Error getting post detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/content/posts/<int:post_id>/warn', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_warn_post_author(post_id):
    """Admin: Advertir al autor de una publicación."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Contenido inapropiado')
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicación no encontrada'}), 404
                
                user_id = post['user_id']
                
                cur.execute("""
                    INSERT INTO admin_warnings (user_id, admin_id, reason, post_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (user_id, admin_id, reason, post_id))
                
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                    VALUES (%s, 'warn_user', 'post', %s, %s, NOW())
                """, (admin_id, str(post_id), reason))
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Advertencia enviada al usuario'})
        
    except Exception as e:
        logger.error(f"Error warning post author: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/content/posts/<int:post_id>/ban-author', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_ban_post_author(post_id):
    """Admin: Banear al autor de una publicación por contenido inapropiado."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Contenido inapropiado')
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicación no encontrada'}), 404
                
                user_id = post['user_id']
                
                cur.execute("""
                    UPDATE users SET is_banned = true, ban_reason = %s, banned_at = NOW()
                    WHERE telegram_id::text = %s
                """, (reason, user_id))
                
                cur.execute("""
                    UPDATE posts SET is_active = false WHERE user_id = %s
                """, (user_id,))
                
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                    VALUES (%s, 'ban_user_content', 'user', %s, %s, NOW())
                """, (admin_id, user_id, reason))
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario baneado y contenido eliminado'})
        
    except Exception as e:
        logger.error(f"Error banning post author: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/content/reported', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_reported_content():
    """Admin: Obtener publicaciones reportadas con prioridad."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'posts': []})
        
        limit = request.args.get('limit', 50, type=int)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.id, p.user_id, p.content_type, p.caption, p.content_url,
                           p.likes_count, p.comments_count, p.is_active, p.created_at,
                           u.username, u.first_name,
                           COUNT(cr.id) as report_count,
                           ARRAY_AGG(DISTINCT cr.reason) as report_reasons
                    FROM posts p
                    LEFT JOIN users u ON p.user_id = u.telegram_id::text
                    INNER JOIN content_reports cr ON cr.content_type = 'post' AND cr.content_id = p.id
                    WHERE p.is_active = true AND cr.status = 'pending'
                    GROUP BY p.id, p.user_id, p.content_type, p.caption, p.content_url,
                             p.likes_count, p.comments_count, p.is_active, p.created_at,
                             u.username, u.first_name
                    ORDER BY report_count DESC, p.created_at DESC
                    LIMIT %s
                """, (limit,))
                posts = cur.fetchall()
        
        result = []
        for p in posts:
            post_dict = dict(p)
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            result.append(post_dict)
        
        return jsonify({'success': True, 'posts': result})
        
    except Exception as e:
        logger.error(f"Error getting reported content: {e}")
        return jsonify({'success': True, 'posts': []})


@app.route('/api/admin/hashtags', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_hashtags():
    """Admin: Obtener lista de hashtags con estadísticas y filtros."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'hashtags': [], 'total': 0})
        
        limit = request.args.get('limit', 50, type=int)
        sort = request.args.get('sort', 'posts_count')
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                order_by = 'posts_count DESC' if sort == 'posts_count' else 'created_at DESC'
                
                query = """
                    SELECT h.id, h.tag, h.posts_count, h.created_at,
                           COALESCE(h.is_blocked, false) as is_blocked,
                           COALESCE(h.is_promoted, false) as is_promoted
                    FROM hashtags h
                    WHERE 1=1
                """
                params = []
                
                if search:
                    query += " AND LOWER(h.tag) LIKE LOWER(%s)"
                    params.append(f"%{search}%")
                
                if status == 'blocked':
                    query += " AND COALESCE(h.is_blocked, false) = true"
                elif status == 'promoted':
                    query += " AND COALESCE(h.is_promoted, false) = true"
                elif status == 'active':
                    query += " AND COALESCE(h.is_blocked, false) = false"
                
                query += f" ORDER BY {order_by} LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                hashtags = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM hashtags h WHERE 1=1"
                count_params = []
                
                if search:
                    count_query += " AND LOWER(h.tag) LIKE LOWER(%s)"
                    count_params.append(f"%{search}%")
                
                if status == 'blocked':
                    count_query += " AND COALESCE(h.is_blocked, false) = true"
                elif status == 'promoted':
                    count_query += " AND COALESCE(h.is_promoted, false) = true"
                elif status == 'active':
                    count_query += " AND COALESCE(h.is_blocked, false) = false"
                
                cur.execute(count_query, count_params)
                total_row = cur.fetchone()
                total = total_row['total'] if total_row else 0
        
        result = []
        for h in hashtags:
            h_dict = dict(h)
            if h_dict.get('created_at'):
                h_dict['created_at'] = h_dict['created_at'].isoformat()
            result.append(h_dict)
        
        return jsonify({'success': True, 'hashtags': result, 'total': total})
        
    except Exception as e:
        logger.error(f"Error getting hashtags: {e}")
        return jsonify({'success': True, 'hashtags': [], 'total': 0})


@app.route('/api/admin/hashtags/<int:hashtag_id>/block', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_block_hashtag(hashtag_id):
    """Admin: Bloquear un hashtag inapropiado."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE hashtags ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE
                """)
                cur.execute("""
                    UPDATE hashtags SET is_blocked = true WHERE id = %s
                """, (hashtag_id,))
                
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                    VALUES (%s, 'block_hashtag', 'hashtag', %s, 'Hashtag bloqueado', NOW())
                """, (admin_id, str(hashtag_id)))
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Hashtag bloqueado'})
        
    except Exception as e:
        logger.error(f"Error blocking hashtag: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/hashtags/<int:hashtag_id>/unblock', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_unblock_hashtag(hashtag_id):
    """Admin: Desbloquear un hashtag."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE hashtags SET is_blocked = false WHERE id = %s
                """, (hashtag_id,))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Hashtag desbloqueado'})
        
    except Exception as e:
        logger.error(f"Error unblocking hashtag: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/hashtags/<int:hashtag_id>/promote', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_promote_hashtag(hashtag_id):
    """Admin: Promover un hashtag manualmente."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE hashtags ADD COLUMN IF NOT EXISTS is_promoted BOOLEAN DEFAULT FALSE
                """)
                cur.execute("""
                    UPDATE hashtags SET is_promoted = true WHERE id = %s
                """, (hashtag_id,))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Hashtag promovido'})
        
    except Exception as e:
        logger.error(f"Error promoting hashtag: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/stories', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_stories():
    """Admin: Obtener stories para moderación con filtros."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'stories': [], 'total': 0})
        
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status', 'active').strip()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT s.id, s.user_id, s.media_type, s.media_url, s.views_count,
                           s.is_active, s.expires_at, s.created_at,
                           u.username, u.first_name
                    FROM stories s
                    LEFT JOIN users u ON s.user_id = u.telegram_id::text
                    WHERE 1=1
                """
                params = []
                
                if status == 'active':
                    query += " AND s.is_active = true AND s.expires_at > NOW()"
                elif status == 'expired':
                    query += " AND (s.is_active = false OR s.expires_at <= NOW())"
                
                query += " ORDER BY s.created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                stories = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM stories s WHERE 1=1"
                count_params = []
                
                if status == 'active':
                    count_query += " AND s.is_active = true AND s.expires_at > NOW()"
                elif status == 'expired':
                    count_query += " AND (s.is_active = false OR s.expires_at <= NOW())"
                
                cur.execute(count_query, count_params)
                total_row = cur.fetchone()
                total = total_row['total'] if total_row else 0
        
        result = []
        for s in stories:
            s_dict = dict(s)
            if s_dict.get('created_at'):
                s_dict['created_at'] = s_dict['created_at'].isoformat()
            if s_dict.get('expires_at'):
                s_dict['expires_at'] = s_dict['expires_at'].isoformat()
            result.append(s_dict)
        
        return jsonify({'success': True, 'stories': result, 'total': total})
        
    except Exception as e:
        logger.error(f"Error getting stories: {e}")
        return jsonify({'success': True, 'stories': [], 'total': 0})


@app.route('/api/admin/stories/<int:story_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_story(story_id):
    """Admin: Eliminar una story."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE stories SET is_active = false WHERE id = %s", (story_id,))
                
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                    VALUES (%s, 'delete_story', 'story', %s, 'Story eliminada por moderación', NOW())
                """, (admin_id, str(story_id)))
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Story eliminada'})
        
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/user/<user_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_basic(user_id):
    """Admin: Obtener detalle básico de un usuario (legacy endpoint)."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, username, first_name, last_name, telegram_id, 
                           credits, level, is_active, is_verified, wallet_address,
                           created_at, last_seen, bio, avatar_url,
                           COALESCE(is_banned, false) as is_banned,
                           two_factor_enabled, security_score
                    FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                user = cur.fetchone()
                
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("SELECT COUNT(*) as total FROM wallet_transactions WHERE user_id = %s", (user_id,))
                total_tx = cur.fetchone()['total'] or 0
                
                user_data = {
                    'user_id': str(user['id']),
                    'id': user['id'],
                    'telegram_id': user.get('telegram_id'),
                    'username': user.get('username'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'bio': user.get('bio'),
                    'avatar_url': user.get('avatar_url'),
                    'credits': float(user.get('credits', 0)),
                    'level': user.get('level', 1),
                    'is_active': user.get('is_active', True),
                    'is_verified': user.get('is_verified', False),
                    'is_banned': user.get('is_banned', False),
                    'wallet_address': user.get('wallet_address'),
                    'two_factor_enabled': user.get('two_factor_enabled', False),
                    'security_score': user.get('security_score', 0),
                    'created_at': str(user.get('created_at', '')),
                    'last_seen': str(user.get('last_seen', '')),
                    'total_transactions': total_tx,
                    'language_code': 'es'
                }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/user/credits', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_credits():
    """Admin: Agregar creditos a un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        amount = data.get('amount', 0)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not amount or amount == 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    UPDATE users SET credits = credits + %s 
                    WHERE id = %s RETURNING credits
                """, (amount, user_id))
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'newCredits': result[0] if result else 0,
                    'message': f'{amount} creditos agregados'
                })
        
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/user/toggle-status', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_toggle_user_status():
    """Admin: Cambiar estado activo/inactivo de un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, is_active FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    UPDATE users SET is_active = NOT is_active 
                    WHERE id = %s RETURNING is_active
                """, (user_id,))
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'isActive': result[0] if result else not user[1]
                })
        
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/user/verify', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_verify_user():
    """Admin: Cambiar estado de verificación de un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        is_verified = data.get('isVerified', False)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.set_user_verified(user_id, is_verified)
        
        if success:
            return jsonify({
                'success': True,
                'isVerified': is_verified,
                'message': 'Usuario verificado' if is_verified else 'Verificación removida'
            })
        else:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
    except Exception as e:
        logger.error(f"Error verifying user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_manage_bots():
    """Admin: Gestionar bots del sistema."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        if request.method == 'GET':
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT bt.*, 
                               (SELECT COUNT(*) FROM user_bots ub WHERE ub.bot_type = bt.bot_type) as users_count
                        FROM bot_types bt
                        ORDER BY bt.created_at DESC
                    """)
                    bots = cur.fetchall()
            
            return jsonify({
                'success': True,
                'bots': [dict(b) for b in bots]
            })
        
        else:
            data = request.get_json() or {}
            name = data.get('name')
            bot_type = data.get('type', 'general')
            description = data.get('description', '')
            price = data.get('price', 0)
            icon = data.get('icon', '🤖')
            
            if not name:
                return jsonify({'success': False, 'error': 'Nombre requerido'}), 400
            
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO bot_types (bot_name, bot_type, description, price, icon)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (name, bot_type, description, price, icon))
                    new_id = cur.fetchone()[0]
                    conn.commit()
            
            return jsonify({
                'success': True,
                'botId': new_id,
                'message': 'Bot creado correctamente'
            })
        
    except Exception as e:
        logger.error(f"Error managing bots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/<int:bot_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_bot(bot_id):
    """Admin: Eliminar un bot."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM bot_types WHERE id = %s", (bot_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                cur.execute("DELETE FROM bot_types WHERE id = %s", (bot_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                
                if deleted:
                    return jsonify({'success': True, 'message': 'Bot eliminado'})
                else:
                    return jsonify({'success': False, 'error': 'No se pudo eliminar el bot'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/<int:bot_id>/toggle', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_toggle_bot(bot_id):
    """Admin: Activar/desactivar un bot."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, is_available FROM bot_types WHERE id = %s", (bot_id,))
                bot = cur.fetchone()
                
                if not bot:
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                new_status = not bot['is_available']
                cur.execute("UPDATE bot_types SET is_available = %s WHERE id = %s", (new_status, bot_id))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'isAvailable': new_status,
                    'message': 'Bot activado' if new_status else 'Bot desactivado'
                })
        
    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/<int:bot_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def admin_update_bot(bot_id):
    """Admin: Actualizar un bot."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM bot_types WHERE id = %s", (bot_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                updates = []
                params = []
                
                if 'name' in data:
                    updates.append("bot_name = %s")
                    params.append(data['name'])
                if 'description' in data:
                    updates.append("description = %s")
                    params.append(data['description'])
                if 'price' in data:
                    updates.append("price = %s")
                    params.append(int(data['price']))
                if 'icon' in data:
                    updates.append("icon = %s")
                    params.append(data['icon'])
                if 'isAvailable' in data:
                    updates.append("is_available = %s")
                    params.append(bool(data['isAvailable']))
                
                if updates:
                    params.append(bot_id)
                    cur.execute(f"UPDATE bot_types SET {', '.join(updates)} WHERE id = %s", params)
                    conn.commit()
                
                return jsonify({'success': True, 'message': 'Bot actualizado'})
        
    except Exception as e:
        logger.error(f"Error updating bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_stats():
    """Admin: Obtener estadísticas de bots."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        bt.id,
                        bt.bot_name,
                        bt.bot_type,
                        bt.icon,
                        bt.price,
                        bt.is_available,
                        COUNT(ub.id) as total_users,
                        COUNT(CASE WHEN ub.is_active THEN 1 END) as active_users,
                        COALESCE(bt.price * COUNT(ub.id), 0) as total_revenue
                    FROM bot_types bt
                    LEFT JOIN user_bots ub ON ub.bot_type = bt.bot_type
                    GROUP BY bt.id, bt.bot_name, bt.bot_type, bt.icon, bt.price, bt.is_available
                    ORDER BY total_users DESC
                """)
                bot_stats = [dict(row) for row in cur.fetchall()]
                
                cur.execute("SELECT COUNT(*) as total FROM bot_types")
                total_bots = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as total FROM bot_types WHERE is_available = true")
                active_bots = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as total FROM user_bots")
                total_users_using_bots = cur.fetchone()['total']
                
                return jsonify({
                    'success': True,
                    'summary': {
                        'totalBots': total_bots,
                        'activeBots': active_bots,
                        'totalUsersUsingBots': total_users_using_bots
                    },
                    'botStats': bot_stats
                })
        
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/usage', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_usage():
    """Admin: Obtener datos de uso de bots en el tiempo."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        days = int(request.args.get('days', 30))
        days = min(days, 90)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        TO_CHAR(created_at, 'YYYY-MM-DD') as date,
                        COUNT(*) as count
                    FROM user_bots
                    WHERE created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')
                    GROUP BY TO_CHAR(created_at, 'YYYY-MM-DD')
                    ORDER BY date
                """, (days,))
                usage_data = [dict(row) for row in cur.fetchall()]
                
                from datetime import datetime, timedelta
                today = datetime.now().date()
                date_set = {d['date'] for d in usage_data}
                
                complete_data = []
                for i in range(days, -1, -1):
                    date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                    existing = next((d for d in usage_data if d['date'] == date_str), None)
                    if existing:
                        complete_data.append(existing)
                    else:
                        complete_data.append({'date': date_str, 'count': 0})
                
                return jsonify({
                    'success': True,
                    'data': complete_data
                })
        
    except Exception as e:
        logger.error(f"Error getting bots usage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/revenue', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_revenue():
    """Admin: Obtener ingresos por bots."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                """)
                total_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                month_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                week_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        bt.id,
                        bt.bot_name as name,
                        bt.icon,
                        bt.price,
                        COUNT(ub.id) as count,
                        COALESCE(bt.price * COUNT(ub.id), 0) as revenue
                    FROM bot_types bt
                    LEFT JOIN user_bots ub ON ub.bot_type = bt.bot_type
                    GROUP BY bt.id, bt.bot_name, bt.icon, bt.price
                    ORDER BY revenue DESC
                """)
                breakdown = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'data': {
                        'total': total_revenue,
                        'month': month_revenue,
                        'week': week_revenue,
                        'breakdown': breakdown
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting bots revenue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/purchases', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_purchases():
    """Admin: Obtener historial de compras de bots."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        per_page = min(per_page, 50)
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM user_bots")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        ub.id,
                        ub.user_id,
                        ub.bot_type,
                        ub.created_at,
                        bt.bot_name,
                        bt.icon,
                        bt.price,
                        u.username
                    FROM user_bots ub
                    LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    LEFT JOIN users u ON ub.user_id::bigint = u.telegram_id
                    ORDER BY ub.created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                purchases = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'data': purchases,
                    'total': total,
                    'page': page,
                    'per_page': per_page
                })
        
    except Exception as e:
        logger.error(f"Error getting bots purchases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/bots/<int:bot_id>/logs', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bot_logs(bot_id):
    """Admin: Obtener logs de actividad de un bot específico."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT bot_type FROM bot_types WHERE id = %s", (bot_id,))
                bot = cur.fetchone()
                if not bot:
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                bot_type = bot['bot_type']
                
                cur.execute("""
                    SELECT COUNT(*) as total FROM user_bots WHERE bot_type = %s
                """, (bot_type,))
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        ub.id,
                        ub.user_id,
                        ub.bot_type,
                        ub.bot_name,
                        ub.is_active,
                        ub.created_at,
                        ub.config,
                        u.username,
                        u.first_name,
                        bt.price,
                        bt.icon
                    FROM user_bots ub
                    LEFT JOIN users u ON ub.user_id::bigint = u.telegram_id
                    LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.bot_type = %s
                    ORDER BY ub.created_at DESC
                    LIMIT %s OFFSET %s
                """, (bot_type, per_page, offset))
                logs = [dict(row) for row in cur.fetchall()]
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                cur.execute("""
                    SELECT COUNT(*) as active_count 
                    FROM user_bots 
                    WHERE bot_type = %s AND is_active = TRUE
                """, (bot_type,))
                active_count = cur.fetchone()['active_count'] or 0
                
                cur.execute("""
                    SELECT COUNT(*) as today_count 
                    FROM user_bots 
                    WHERE bot_type = %s AND created_at >= CURRENT_DATE
                """, (bot_type,))
                today_count = cur.fetchone()['today_count'] or 0
                
                return jsonify({
                    'success': True,
                    'data': logs,
                    'total': total,
                    'active_count': active_count,
                    'today_count': today_count,
                    'page': page,
                    'per_page': per_page
                })
        
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/products', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_products():
    """Admin: Obtener todos los productos."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'products': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM products ORDER BY created_at DESC")
                products = cur.fetchall()
        
        return jsonify({
            'success': True,
            'products': [dict(p) for p in products] if products else []
        })
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({'success': True, 'products': []})


@app.route('/api/admin/products', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_create_product():
    """Admin: Crear nuevo producto."""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        price = float(data.get('price', 0))
        category = data.get('category', 'general').strip()
        stock = int(data.get('stock', 1))
        icon = data.get('icon', '')
        
        if not title:
            return jsonify({'success': False, 'error': 'El titulo es requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        user_id = get_user_id()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products (user_id, title, description, price, category, stock, image_url, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                """, (user_id, title, description, price, category, stock, icon))
                product_id = cur.fetchone()[0]
                conn.commit()
        
        logger.info(f"Product created: {title} (ID: {product_id})")
        return jsonify({'success': True, 'product_id': product_id, 'message': 'Producto creado correctamente'})
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_product(product_id):
    """Admin: Eliminar producto."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
                conn.commit()
        
        logger.info(f"Product deleted: ID {product_id}")
        return jsonify({'success': True, 'message': 'Producto eliminado'})
        
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/transactions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_transactions():
    """Admin: Obtener todas las transacciones."""
    try:
        filter_type = request.args.get('filter', 'all')
        tx_type = request.args.get('type', '')
        status = request.args.get('status', '')
        period = request.args.get('period', 'all')
        user_id = request.args.get('user_id', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        if not db_manager:
            return jsonify({
                'success': True,
                'transactions': [],
                'total': 0,
                'page': 1,
                'pages': 1,
                'totalVolume': 0,
                'totalFees': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT wt.*, u.username, u.telegram_id
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON CAST(wt.user_id AS INTEGER) = u.id
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) FROM wallet_transactions wt WHERE 1=1"
                params = []
                count_params = []
                
                if filter_type != 'all':
                    query += " AND wt.transaction_type = %s"
                    count_query += " AND wt.transaction_type = %s"
                    params.append(filter_type)
                    count_params.append(filter_type)
                
                if tx_type:
                    query += " AND wt.transaction_type = %s"
                    count_query += " AND wt.transaction_type = %s"
                    params.append(tx_type)
                    count_params.append(tx_type)
                
                if user_id:
                    query += " AND wt.user_id = %s"
                    count_query += " AND wt.user_id = %s"
                    params.append(str(user_id))
                    count_params.append(str(user_id))
                
                if period == 'today':
                    query += " AND wt.created_at >= CURRENT_DATE"
                    count_query += " AND wt.created_at >= CURRENT_DATE"
                elif period == 'week':
                    query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '7 days'"
                    count_query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '7 days'"
                elif period == 'month':
                    query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '30 days'"
                    count_query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '30 days'"
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()[0] or 0
                
                query += " ORDER BY wt.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                transactions = cur.fetchall()
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as volume,
                           COALESCE(SUM(CASE WHEN transaction_type IN ('buy', 'sell') THEN amount * 0.01 ELSE 0 END), 0) as fees
                    FROM wallet_transactions
                """)
                totals = cur.fetchone()
        
        pages = max(1, (total + limit - 1) // limit)
        
        return jsonify({
            'success': True,
            'transactions': [{
                'id': t['id'],
                'user_id': t.get('user_id', ''),
                'type': t.get('transaction_type', 'unknown'),
                'amount': float(t.get('amount', 0)),
                'currency': 'B3C',
                'status': 'completed',
                'username': t.get('username') or f"User {t.get('user_id', 'N/A')}",
                'description': t.get('description', ''),
                'reference_id': t.get('reference_id', ''),
                'tx_hash': t.get('reference_id', ''),
                'created_at': str(t.get('created_at', ''))
            } for t in transactions],
            'total': total,
            'page': page,
            'pages': pages,
            'totalVolume': float(totals['volume']) if totals else 0,
            'totalFees': float(totals['fees']) if totals else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({
            'success': True,
            'transactions': [],
            'totalDeposits': 0,
            'totalWithdrawals': 0
        })


@app.route('/api/admin/transactions/<int:tx_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_transaction_detail(tx_id):
    """Admin: Obtener detalle de una transacción específica."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.*, u.username, u.telegram_id, u.first_name, u.last_name
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON CAST(wt.user_id AS INTEGER) = u.id
                    WHERE wt.id = %s
                """, (tx_id,))
                tx = cur.fetchone()
                
                if not tx:
                    return jsonify({'success': False, 'error': 'Transacción no encontrada'})
                
                tx_type = tx.get('transaction_type', 'unknown')
                tx_types_labels = {
                    'buy': 'Compra B3C',
                    'sell': 'Venta B3C',
                    'transfer_in': 'Transferencia Recibida',
                    'transfer_out': 'Transferencia Enviada',
                    'withdrawal': 'Retiro',
                    'deposit': 'Depósito',
                    'reward': 'Recompensa',
                    'fee': 'Comisión'
                }
                
                return jsonify({
                    'success': True,
                    'transaction': {
                        'id': tx['id'],
                        'user_id': tx.get('user_id', ''),
                        'username': tx.get('username') or f"User {tx.get('user_id', 'N/A')}",
                        'user_name': f"{tx.get('first_name', '')} {tx.get('last_name', '')}".strip() or 'N/A',
                        'telegram_id': tx.get('telegram_id', ''),
                        'type': tx_type,
                        'type_label': tx_types_labels.get(tx_type, tx_type.capitalize()),
                        'amount': float(tx.get('amount', 0)),
                        'currency': 'B3C',
                        'status': 'completed',
                        'description': tx.get('description', ''),
                        'reference_id': tx.get('reference_id', ''),
                        'tx_hash': tx.get('reference_id', ''),
                        'created_at': str(tx.get('created_at', '')),
                        'balance_before': float(tx.get('balance_before', 0)) if tx.get('balance_before') else None,
                        'balance_after': float(tx.get('balance_after', 0)) if tx.get('balance_after') else None
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting transaction detail: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/purchases', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_purchases():
    """Admin: Obtener todas las compras de B3C."""
    try:
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        if not db_manager:
            return jsonify({
                'success': True,
                'purchases': [],
                'total': 0,
                'page': 1,
                'pages': 1
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT 
                        bp.id,
                        bp.purchase_id,
                        bp.user_id,
                        bp.ton_amount,
                        bp.b3c_amount,
                        bp.commission_ton,
                        bp.status,
                        bp.tx_hash,
                        bp.created_at,
                        bp.confirmed_at,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.telegram_id,
                        dw.wallet_address as deposit_wallet,
                        dw.expected_amount as expected_amount
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) FROM b3c_purchases WHERE 1=1"
                params = []
                count_params = []
                
                if status_filter:
                    query += " AND bp.status = %s"
                    count_query += " AND status = %s"
                    params.append(status_filter)
                    count_params.append(status_filter)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()[0] or 0
                
                query += " ORDER BY bp.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                purchases = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_purchases,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed_count,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                        COUNT(*) FILTER (WHERE status = 'expired') as expired_count,
                        COALESCE(SUM(ton_amount) FILTER (WHERE status = 'confirmed'), 0) as total_ton,
                        COALESCE(SUM(b3c_amount) FILTER (WHERE status = 'confirmed'), 0) as total_b3c
                    FROM b3c_purchases
                """)
                stats = cur.fetchone()
        
        pages = max(1, (total + limit - 1) // limit)
        
        status_labels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmada',
            'failed': 'Fallida',
            'expired': 'Expirada'
        }
        
        return jsonify({
            'success': True,
            'purchases': [{
                'id': p['id'],
                'purchaseId': p['purchase_id'],
                'userId': p['user_id'],
                'username': p['username'] or f"User {p['user_id']}",
                'userFullName': f"{p['first_name'] or ''} {p['last_name'] or ''}".strip() or 'N/A',
                'telegramId': p['telegram_id'],
                'tonAmount': float(p['ton_amount']),
                'b3cAmount': float(p['b3c_amount']),
                'commissionTon': float(p['commission_ton']),
                'status': p['status'],
                'statusLabel': status_labels.get(p['status'], p['status']),
                'txHash': p['tx_hash'],
                'depositWallet': p['deposit_wallet'],
                'expectedAmount': float(p['expected_amount']) if p['expected_amount'] else None,
                'createdAt': p['created_at'].isoformat() if p['created_at'] else None,
                'confirmedAt': p['confirmed_at'].isoformat() if p['confirmed_at'] else None
            } for p in purchases],
            'total': total,
            'page': page,
            'pages': pages,
            'stats': {
                'totalPurchases': stats['total_purchases'] or 0,
                'pendingCount': stats['pending_count'] or 0,
                'confirmedCount': stats['confirmed_count'] or 0,
                'failedCount': stats['failed_count'] or 0,
                'expiredCount': stats['expired_count'] or 0,
                'totalTon': float(stats['total_ton'] or 0),
                'totalB3C': float(stats['total_b3c'] or 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting purchases: {e}")
        return jsonify({
            'success': True,
            'purchases': [],
            'total': 0,
            'page': 1,
            'pages': 1
        })


@app.route('/api/admin/purchases/<purchase_id>/credit', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_credit_purchase(purchase_id):
    """Admin: Acreditar manualmente una compra de B3C pendiente."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        admin_user = request.telegram_user
        admin_user_id = str(admin_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT bp.*, u.username, u.first_name
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                if purchase['status'] == 'confirmed':
                    return jsonify({'success': False, 'error': 'Esta compra ya fue acreditada'}), 400
                
                user_id = purchase['user_id']
                b3c_amount = float(purchase['b3c_amount'])
                
                cur.execute("""
                    SELECT b3c_balance FROM users WHERE id = %s
                """, (int(user_id),))
                user_row = cur.fetchone()
                balance_before = float(user_row['b3c_balance']) if user_row and user_row['b3c_balance'] else 0
                balance_after = balance_before + b3c_amount
                
                cur.execute("""
                    UPDATE users 
                    SET b3c_balance = b3c_balance + %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (b3c_amount, int(user_id)))
                
                cur.execute("""
                    UPDATE b3c_purchases 
                    SET status = 'confirmed',
                        confirmed_at = NOW()
                    WHERE purchase_id = %s
                """, (purchase_id,))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, transaction_type, amount, balance_before, balance_after, description, reference_id)
                    VALUES (%s, 'buy', %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    b3c_amount,
                    balance_before,
                    balance_after,
                    f'Compra B3C acreditada manualmente por admin',
                    purchase_id
                ))
                
                cur.execute("""
                    UPDATE deposit_wallets 
                    SET status = 'used'
                    WHERE assigned_to_purchase_id = %s
                """, (purchase_id,))
                
                conn.commit()
                
                logger.info(f"[ADMIN] Compra {purchase_id} acreditada manualmente por admin {admin_user_id}. Usuario {user_id} recibió {b3c_amount} B3C")
                
                if security_manager:
                    security_manager.log_activity(
                        admin_user_id,
                        'admin_credit_purchase',
                        f'Acreditó compra {purchase_id}: {b3c_amount} B3C a usuario {user_id}',
                        request.remote_addr
                    )
                
        return jsonify({
            'success': True,
            'message': f'Compra acreditada correctamente. {b3c_amount} B3C fueron añadidos al usuario.',
            'credited': {
                'purchaseId': purchase_id,
                'userId': user_id,
                'username': purchase['username'],
                'b3cAmount': b3c_amount,
                'balanceBefore': balance_before,
                'balanceAfter': balance_after
            }
        })
        
    except Exception as e:
        logger.error(f"Error crediting purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al acreditar la compra'}), 500


@app.route('/api/admin/purchases/<purchase_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_purchase_detail(purchase_id):
    """Admin: Obtener detalle de una compra específica."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        bp.*,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.telegram_id,
                        u.b3c_balance,
                        dw.wallet_address as deposit_wallet,
                        dw.expected_amount,
                        dw.deposit_amount,
                        dw.status as wallet_status
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
        
        status_labels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmada',
            'failed': 'Fallida',
            'expired': 'Expirada'
        }
        
        return jsonify({
            'success': True,
            'purchase': {
                'id': purchase['id'],
                'purchaseId': purchase['purchase_id'],
                'userId': purchase['user_id'],
                'username': purchase['username'] or f"User {purchase['user_id']}",
                'userFullName': f"{purchase['first_name'] or ''} {purchase['last_name'] or ''}".strip() or 'N/A',
                'telegramId': purchase['telegram_id'],
                'userBalance': float(purchase['b3c_balance']) if purchase['b3c_balance'] else 0,
                'tonAmount': float(purchase['ton_amount']),
                'b3cAmount': float(purchase['b3c_amount']),
                'commissionTon': float(purchase['commission_ton']),
                'status': purchase['status'],
                'statusLabel': status_labels.get(purchase['status'], purchase['status']),
                'txHash': purchase['tx_hash'],
                'depositWallet': purchase['deposit_wallet'],
                'expectedAmount': float(purchase['expected_amount']) if purchase['expected_amount'] else None,
                'depositAmount': float(purchase['deposit_amount']) if purchase['deposit_amount'] else None,
                'walletStatus': purchase['wallet_status'],
                'createdAt': purchase['created_at'].isoformat() if purchase['created_at'] else None,
                'confirmedAt': purchase['confirmed_at'].isoformat() if purchase['confirmed_at'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting purchase detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_activity():
    """Admin: Obtener actividad del sistema."""
    try:
        type_filter = request.args.get('type', 'all')
        
        if not security_manager:
            return jsonify({'success': True, 'activities': []})
        
        activities = security_manager.get_all_activity_admin(type_filter)
        
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': True, 'activities': []})


@app.route('/api/admin/lockouts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_lockouts():
    """Admin: Obtener usuarios bloqueados."""
    try:
        if not security_manager:
            return jsonify({'success': True, 'lockouts': []})
        
        lockouts = security_manager.get_locked_users_admin()
        
        return jsonify({
            'success': True,
            'lockouts': lockouts
        })
        
    except Exception as e:
        logger.error(f"Error getting lockouts: {e}")
        return jsonify({'success': True, 'lockouts': []})


@app.route('/api/admin/unlock-user', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_unlock_user():
    """Admin: Desbloquear un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        success = security_manager.unlock_user_admin(user_id)
        
        return jsonify({
            'success': success,
            'message': 'Usuario desbloqueado' if success else 'Error al desbloquear'
        })
        
    except Exception as e:
        logger.error(f"Error unlocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/settings', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_system_settings():
    """Admin: Configuracion del sistema."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if request.method == 'GET':
                    cur.execute("SELECT key, value, category FROM system_settings")
                    rows = cur.fetchall()
                    settings = {row['key']: row['value'] for row in rows}
                    
                    return jsonify({
                        'success': True,
                        'maintenanceMode': settings.get('maintenance_mode', 'false') == 'true',
                        'maintenanceMessage': settings.get('maintenance_message', ''),
                        'registrationOpen': settings.get('registration_open', 'true') == 'true',
                        'merchantWallet': os.environ.get('TON_WALLET_ADDRESS', 'No configurada'),
                        'minDeposit': float(settings.get('min_deposit', '1')),
                        'minWithdrawal': float(settings.get('min_withdrawal', '0.5')),
                        'withdrawalFee': float(settings.get('withdrawal_fee', '0.05')),
                        'transactionFeePercent': float(settings.get('transaction_fee_percent', '2')),
                        'emailAlerts': settings.get('email_alerts', 'true') == 'true',
                        'telegramAlerts': settings.get('telegram_alerts', 'true') == 'true',
                        'largeTransactionThreshold': float(settings.get('large_transaction_threshold', '100'))
                    })
                else:
                    data = request.json or {}
                    updates = []
                    
                    setting_mappings = {
                        'maintenanceMode': ('maintenance_mode', lambda v: 'true' if v else 'false'),
                        'maintenanceMessage': ('maintenance_message', str),
                        'registrationOpen': ('registration_open', lambda v: 'true' if v else 'false'),
                        'minDeposit': ('min_deposit', str),
                        'minWithdrawal': ('min_withdrawal', str),
                        'withdrawalFee': ('withdrawal_fee', str),
                        'transactionFeePercent': ('transaction_fee_percent', str),
                        'emailAlerts': ('email_alerts', lambda v: 'true' if v else 'false'),
                        'telegramAlerts': ('telegram_alerts', lambda v: 'true' if v else 'false'),
                        'largeTransactionThreshold': ('large_transaction_threshold', str)
                    }
                    
                    for key, value in data.items():
                        if key in setting_mappings:
                            db_key, transform = setting_mappings[key]
                            cur.execute("""
                                INSERT INTO system_settings (key, value, updated_at)
                                VALUES (%s, %s, NOW())
                                ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                            """, (db_key, transform(value), transform(value)))
                            updates.append(db_key)
                    
                    conn.commit()
                    return jsonify({
                        'success': True,
                        'message': 'Configuracion guardada',
                        'updated': updates
                    })
        
    except Exception as e:
        logger.error(f"Error with settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_notifications():
    """Admin: Obtener notificaciones del panel."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, type, title, message, data, is_read, created_at
                    FROM admin_notifications
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                notifications = cur.fetchall()
                
                cur.execute("SELECT COUNT(*) FROM admin_notifications WHERE is_read = false")
                unread_count = cur.fetchone()['count']
                
                for n in notifications:
                    if n.get('created_at'):
                        n['created_at'] = n['created_at'].isoformat()
                    if n.get('data'):
                        try:
                            n['data'] = json.loads(n['data']) if isinstance(n['data'], str) else n['data']
                        except:
                            pass
                
                return jsonify({
                    'success': True,
                    'notifications': notifications,
                    'unread_count': unread_count
                })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications/mark-read', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_mark_notification_read():
    """Admin: Marcar notificacion como leida."""
    try:
        data = request.get_json() or {}
        notification_id = data.get('id')
        mark_all = data.get('all', False)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if mark_all:
                    cur.execute("UPDATE admin_notifications SET is_read = true WHERE is_read = false")
                elif notification_id:
                    cur.execute("UPDATE admin_notifications SET is_read = true WHERE id = %s", (notification_id,))
                conn.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications/delete', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_delete_notification():
    """Admin: Eliminar notificacion."""
    try:
        data = request.get_json() or {}
        notification_id = data.get('id')
        delete_all = data.get('all', False)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if delete_all:
                    cur.execute("DELETE FROM admin_notifications")
                elif notification_id:
                    cur.execute("DELETE FROM admin_notifications WHERE id = %s", (notification_id,))
                conn.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/telegram/settings', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_telegram_settings():
    """Admin: Obtener configuracion de Telegram."""
    try:
        settings = telegram_service.get_settings()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT key, value FROM system_settings WHERE key LIKE 'telegram_%'")
                db_settings = {row['key']: row['value'] for row in cur.fetchall()}
        
        for key in settings['notification_types']:
            db_key = f"telegram_{key}_enabled"
            if db_key in db_settings:
                settings['notification_types'][key]['enabled'] = db_settings[db_key] == 'true'
            
            threshold_key = f"telegram_{key}_threshold"
            if threshold_key in db_settings:
                try:
                    settings['notification_types'][key]['threshold'] = float(db_settings[threshold_key])
                except:
                    pass
        
        if 'telegram_enabled' in db_settings:
            settings['enabled'] = db_settings['telegram_enabled'] == 'true'
        
        return jsonify({
            'success': True,
            **settings
        })
    except Exception as e:
        logger.error(f"Error getting telegram settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/telegram/settings', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_update_telegram_settings():
    """Admin: Actualizar configuracion de Telegram."""
    try:
        data = request.get_json() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if 'enabled' in data:
                    cur.execute("""
                        INSERT INTO system_settings (key, value, updated_at)
                        VALUES ('telegram_enabled', %s, NOW())
                        ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                    """, ('true' if data['enabled'] else 'false', 'true' if data['enabled'] else 'false'))
                
                if 'notification_types' in data:
                    for key, settings in data['notification_types'].items():
                        if isinstance(settings, dict):
                            if 'enabled' in settings:
                                db_key = f"telegram_{key}_enabled"
                                val = 'true' if settings['enabled'] else 'false'
                                cur.execute("""
                                    INSERT INTO system_settings (key, value, updated_at)
                                    VALUES (%s, %s, NOW())
                                    ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                                """, (db_key, val, val))
                            
                            if 'threshold' in settings:
                                threshold_key = f"telegram_{key}_threshold"
                                cur.execute("""
                                    INSERT INTO system_settings (key, value, updated_at)
                                    VALUES (%s, %s, NOW())
                                    ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                                """, (threshold_key, str(settings['threshold']), str(settings['threshold'])))
                
                conn.commit()
        
        telegram_service.update_settings(data)
        
        return jsonify({
            'success': True,
            'message': 'Configuracion guardada'
        })
    except Exception as e:
        logger.error(f"Error updating telegram settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/telegram/test', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_test_telegram():
    """Admin: Enviar mensaje de prueba por Telegram."""
    try:
        result = telegram_service.send_test_message()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/telegram/verify', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_verify_telegram():
    """Admin: Verificar conexion del bot de Telegram."""
    try:
        result = telegram_service.verify_bot()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error verifying telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/telegram/send', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_send_telegram():
    """Admin: Enviar mensaje personalizado por Telegram."""
    try:
        data = request.get_json() or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Mensaje requerido'}), 400
        
        result = telegram_service.send_custom_message(message)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error sending telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/system-status', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_system_status():
    """Admin: Estado del sistema y APIs externas."""
    try:
        status = {
            'database': {'status': 'unknown', 'message': ''},
            'toncenter': {'status': 'unknown', 'message': ''},
            'smspool': {'status': 'unknown', 'message': ''},
            'cloudinary': {'status': 'unknown', 'message': ''}
        }
        
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    status['database'] = {'status': 'ok', 'message': 'Conectada'}
        except Exception as e:
            status['database'] = {'status': 'error', 'message': str(e)}
        
        toncenter_key = os.environ.get('TONCENTER_API_KEY', '')
        if toncenter_key:
            status['toncenter'] = {'status': 'ok', 'message': 'API Key configurada'}
        else:
            status['toncenter'] = {'status': 'warning', 'message': 'API Key no configurada'}
        
        smspool_key = os.environ.get('SMSPOOL_API_KEY', '')
        if smspool_key:
            status['smspool'] = {'status': 'ok', 'message': 'API Key configurada'}
        else:
            status['smspool'] = {'status': 'warning', 'message': 'API Key no configurada'}
        
        cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
        if cloudinary_url:
            status['cloudinary'] = {'status': 'ok', 'message': 'Configurado'}
        else:
            status['cloudinary'] = {'status': 'warning', 'message': 'No configurado'}
        
        secrets_status = {
            'DATABASE_URL': bool(os.environ.get('DATABASE_URL')),
            'TONCENTER_API_KEY': bool(os.environ.get('TONCENTER_API_KEY')),
            'SMSPOOL_API_KEY': bool(os.environ.get('SMSPOOL_API_KEY')),
            'CLOUDINARY_URL': bool(os.environ.get('CLOUDINARY_URL')),
            'TON_WALLET_ADDRESS': bool(os.environ.get('TON_WALLET_ADDRESS')),
            'GROQ_API_KEY': bool(os.environ.get('GROQ_API_KEY')),
            'GEMINI_API_KEY': bool(os.environ.get('GEMINI_API_KEY'))
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'secrets': secrets_status,
            'uptime': 'Running'
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_notifications():
    """Admin: Obtener notificaciones del panel."""
    try:
        unread_only = request.args.get('unread', 'false') == 'true'
        limit = min(int(request.args.get('limit', 50)), 100)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause = "WHERE is_read = false" if unread_only else ""
                cur.execute(f"""
                    SELECT * FROM admin_notifications
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                notifications = cur.fetchall()
                
                cur.execute("SELECT COUNT(*) as count FROM admin_notifications WHERE is_read = false")
                unread_count = cur.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'notifications': [dict(n) for n in notifications],
                    'unreadCount': unread_count
                })
                
    except Exception as e:
        logger.error(f"Error getting admin notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications/<int:notification_id>/read', methods=['POST'])
@require_telegram_auth
@require_owner
def mark_notification_read(notification_id):
    """Admin: Marcar notificacion como leida."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE admin_notifications
                    SET is_read = true, read_at = NOW()
                    WHERE id = %s
                """, (notification_id,))
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error marking notification read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications/read-all', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_mark_all_notifications_read():
    """Admin: Marcar todas las notificaciones como leidas."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE admin_notifications
                    SET is_read = true, read_at = NOW()
                    WHERE is_read = false
                """)
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error marking all notifications read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/client/log', methods=['POST'])
def receive_client_log():
    """Recibir logs del cliente (frontend) para monitoreo."""
    try:
        data = request.get_json() or {}
        
        user_id = '0'
        if hasattr(request, 'telegram_user') and request.telegram_user:
            user_id = str(request.telegram_user.get('id', 0))
        
        log_type = data.get('type', 'info')
        action = data.get('action', 'unknown')
        details = data.get('details', {})
        session_id = data.get('sessionId', '')
        
        user_agent = request.headers.get('User-Agent', '')
        is_mobile = any(x in user_agent.lower() for x in ['mobile', 'android', 'iphone', 'ipad'])
        is_telegram = 'telegram' in user_agent.lower() or data.get('isTelegram', False)
        platform = data.get('platform', 'unknown')
        
        logger.info(f"[CLIENT LOG] user={user_id} action={action} type={log_type} mobile={is_mobile} telegram={is_telegram} details={details}")
        
        if db_manager:
            try:
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO client_logs (user_id, session_id, log_type, action, details, 
                                                    user_agent, platform, is_mobile, is_telegram)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (user_id, session_id, log_type, action, 
                              psycopg2.extras.Json(details), user_agent, platform, is_mobile, is_telegram))
                        conn.commit()
            except Exception as db_err:
                logger.error(f"Error saving client log: {db_err}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error receiving client log: {e}")
        return jsonify({'success': True})


@app.route('/api/admin/client-logs', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_client_logs():
    """Admin: Obtener logs de cliente para monitoreo de depositos."""
    try:
        action_filter = request.args.get('action', 'all')
        limit = min(int(request.args.get('limit', 100)), 500)
        mobile_only = request.args.get('mobile', 'false') == 'true'
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'DB no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, user_id, session_id, log_type, action, details,
                           platform, is_mobile, is_telegram, created_at
                    FROM client_logs
                    WHERE 1=1
                """
                params = []
                
                if action_filter != 'all':
                    query += " AND action LIKE %s"
                    params.append(f"%{action_filter}%")
                
                if mobile_only:
                    query += " AND is_mobile = true"
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                logs = cur.fetchall()
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'count': len(logs)
                })
        
    except Exception as e:
        logger.error(f"Error getting client logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/logs', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_logs():
    """Admin: Obtener logs del sistema (redirige a client-logs)."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT log_type as level, action as message, 
                           TO_CHAR(created_at, 'HH24:MI:SS') as time,
                           is_mobile, is_telegram, details
                    FROM client_logs
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                logs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'logs': logs
                })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'success': True, 'logs': []})


@app.route('/api/admin/b3c/withdrawals', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_b3c_withdrawals():
    """Admin: Obtener lista de retiros B3C pendientes y procesados."""
    try:
        status_filter = request.args.get('status', 'all')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if status_filter == 'all':
                    cur.execute("""
                        SELECT w.*, u.username, u.first_name 
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        ORDER BY w.created_at DESC
                        LIMIT 100
                    """)
                else:
                    cur.execute("""
                        SELECT w.*, u.username, u.first_name 
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        WHERE w.status = %s
                        ORDER BY w.created_at DESC
                        LIMIT 100
                    """, (status_filter,))
                
                withdrawals = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending,
                        COUNT(*) FILTER (WHERE status = 'completed') as processed,
                        COALESCE(SUM(b3c_amount), 0) as total_b3c
                    FROM b3c_withdrawals
                """)
                stats_row = cur.fetchone()
        
        result = []
        for w in withdrawals:
            result.append({
                'id': w['withdrawal_id'],
                'userId': w['user_id'],
                'username': w.get('username', 'Unknown'),
                'firstName': w.get('first_name', 'Unknown'),
                'amount': float(w['b3c_amount']),
                'destination': w['destination_wallet'],
                'status': w['status'],
                'txHash': w.get('tx_hash'),
                'createdAt': w['created_at'].isoformat() if w['created_at'] else None,
                'processedAt': w['processed_at'].isoformat() if w.get('processed_at') else None
            })
        
        return jsonify({
            'success': True,
            'withdrawals': result,
            'count': len(result),
            'stats': {
                'totalWithdrawals': stats_row['total'] if stats_row else 0,
                'pendingCount': stats_row['pending'] if stats_row else 0,
                'processedCount': stats_row['processed'] if stats_row else 0,
                'totalB3C': float(stats_row['total_b3c']) if stats_row else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C withdrawals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/b3c/withdrawals/<withdrawal_id>/process', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_process_b3c_withdrawal(withdrawal_id):
    """Admin: Procesar un retiro B3C (marcar como completado con hash de transaccion)."""
    try:
        data = request.get_json()
        tx_hash = data.get('txHash', '').strip()
        action = data.get('action', 'complete')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_withdrawals WHERE withdrawal_id = %s
                """, (withdrawal_id,))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
                
                if action == 'complete':
                    if not tx_hash:
                        return jsonify({'success': False, 'error': 'Se requiere el hash de transaccion'}), 400
                    
                    cur.execute("""
                        UPDATE b3c_withdrawals 
                        SET status = 'completed', tx_hash = %s, processed_at = NOW()
                        WHERE withdrawal_id = %s
                    """, (tx_hash, withdrawal_id))
                    
                elif action == 'reject':
                    reason = data.get('reason', 'Rechazado por admin')
                    cur.execute("""
                        UPDATE b3c_withdrawals 
                        SET status = 'rejected', processed_at = NOW()
                        WHERE withdrawal_id = %s
                    """, (withdrawal_id,))
                    
                    cur.execute("""
                        INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id)
                        VALUES (%s, %s, 'credit', %s, %s)
                    """, (withdrawal['user_id'], withdrawal['b3c_amount'], 
                          f'Retiro rechazado: {reason}', withdrawal_id))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Retiro {action}d exitosamente',
            'withdrawalId': withdrawal_id
        })
        
    except Exception as e:
        logger.error(f"Error processing B3C withdrawal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/b3c/withdrawals/<withdrawal_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_b3c_withdrawal_detail(withdrawal_id):
    """Admin: Obtener detalle de un retiro B3C."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT w.*, u.username, u.first_name, u.telegram_id
                    FROM b3c_withdrawals w
                    LEFT JOIN users u ON w.user_id = u.id
                    WHERE w.withdrawal_id = %s
                """, (withdrawal_id,))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'withdrawal': {
                'id': withdrawal['withdrawal_id'],
                'withdrawalId': withdrawal['withdrawal_id'],
                'userId': withdrawal['user_id'],
                'username': withdrawal.get('username', 'Unknown'),
                'userFullName': withdrawal.get('first_name', 'Unknown'),
                'telegramId': withdrawal.get('telegram_id'),
                'b3cAmount': float(withdrawal['b3c_amount']),
                'tonAmount': float(withdrawal.get('ton_amount', 0) or 0),
                'commission': float(withdrawal.get('commission', 0) or 0),
                'destinationWallet': withdrawal['destination_wallet'],
                'status': withdrawal['status'],
                'txHash': withdrawal.get('tx_hash'),
                'rejectionReason': withdrawal.get('rejection_reason'),
                'createdAt': withdrawal['created_at'].isoformat() if withdrawal['created_at'] else None,
                'processedAt': withdrawal['processed_at'].isoformat() if withdrawal.get('processed_at') else None,
                'userBalance': float(withdrawal.get('b3c_balance', 0) or 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C withdrawal detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/transfers', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_p2p_transfers():
    """Admin: Obtener lista de transferencias P2P."""
    try:
        filter_type = request.args.get('filter', 'all')
        search = request.args.get('search', '').strip()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                base_query = """
                    SELECT t.*, 
                           u1.username as from_username, u1.first_name as from_name, u1.telegram_id as from_telegram_id,
                           u2.username as to_username, u2.first_name as to_name, u2.telegram_id as to_telegram_id
                    FROM wallet_transactions t
                    LEFT JOIN users u1 ON t.user_id = u1.user_id
                    LEFT JOIN users u2 ON t.recipient_id = u2.user_id
                    WHERE t.transaction_type = 'transfer'
                """
                
                params = []
                
                if search:
                    base_query += " AND (u1.username ILIKE %s OR u2.username ILIKE %s)"
                    params.extend([f'%{search}%', f'%{search}%'])
                
                if filter_type == 'suspicious':
                    base_query += " AND t.is_suspicious = TRUE"
                elif filter_type == 'today':
                    base_query += " AND t.created_at >= CURRENT_DATE"
                
                base_query += " ORDER BY t.created_at DESC LIMIT 100"
                
                cur.execute(base_query, params)
                transfers = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today,
                        COUNT(*) FILTER (WHERE is_suspicious = TRUE) as suspicious,
                        COALESCE(SUM(ABS(amount)), 0) as total_b3c
                    FROM wallet_transactions
                    WHERE transaction_type = 'transfer'
                """)
                stats_row = cur.fetchone()
        
        result = []
        for t in transfers:
            result.append({
                'id': t['transaction_id'],
                'transferId': t['transaction_id'],
                'fromUsername': t.get('from_username', 'Unknown'),
                'fromUserName': t.get('from_name', ''),
                'fromTelegramId': t.get('from_telegram_id'),
                'toUsername': t.get('to_username', 'Unknown'),
                'toUserName': t.get('to_name', ''),
                'toTelegramId': t.get('to_telegram_id'),
                'amount': abs(float(t['amount'])),
                'note': t.get('description', ''),
                'isSuspicious': t.get('is_suspicious', False),
                'suspiciousReason': t.get('suspicious_reason'),
                'createdAt': t['created_at'].isoformat() if t['created_at'] else None
            })
        
        return jsonify({
            'success': True,
            'transfers': result,
            'stats': {
                'totalTransfers': stats_row['total'] if stats_row else 0,
                'todayCount': stats_row['today'] if stats_row else 0,
                'suspiciousCount': stats_row['suspicious'] if stats_row else 0,
                'totalB3C': float(stats_row['total_b3c']) if stats_row else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting P2P transfers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/transfers/<transfer_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_p2p_transfer_detail(transfer_id):
    """Admin: Obtener detalle de una transferencia P2P."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT t.*, 
                           u1.username as from_username, u1.first_name as from_name, u1.telegram_id as from_telegram_id,
                           u2.username as to_username, u2.first_name as to_name, u2.telegram_id as to_telegram_id
                    FROM wallet_transactions t
                    LEFT JOIN users u1 ON t.user_id = u1.user_id
                    LEFT JOIN users u2 ON t.recipient_id = u2.user_id
                    WHERE t.transaction_id = %s AND t.transaction_type = 'transfer'
                """, (transfer_id,))
                transfer = cur.fetchone()
                
                if not transfer:
                    return jsonify({'success': False, 'error': 'Transferencia no encontrada'}), 404
        
        return jsonify({
            'success': True,
            'transfer': {
                'id': transfer['transaction_id'],
                'transferId': transfer['transaction_id'],
                'fromUsername': transfer.get('from_username', 'Unknown'),
                'fromUserName': transfer.get('from_name', ''),
                'fromTelegramId': transfer.get('from_telegram_id'),
                'toUsername': transfer.get('to_username', 'Unknown'),
                'toUserName': transfer.get('to_name', ''),
                'toTelegramId': transfer.get('to_telegram_id'),
                'amount': abs(float(transfer['amount'])),
                'note': transfer.get('description', ''),
                'isSuspicious': transfer.get('is_suspicious', False),
                'suspiciousReason': transfer.get('suspicious_reason'),
                'createdAt': transfer['created_at'].isoformat() if transfer['created_at'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting P2P transfer detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENCRYPTED PUBLICATIONS SYSTEM - API ENDPOINTS
# ============================================================

@app.route('/api/publications/create', methods=['POST'])
@require_telegram_auth
def create_publication():
    """Create a new encrypted publication with media carousel support"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if 'files' not in request.files and 'media' not in request.files:
            caption = request.form.get('caption', '')
            content_type = 'text'
            
            encrypted_caption = encryption_manager.encrypt_text(caption)
            
            if encrypted_caption['success']:
                post_id = db_manager.create_encrypted_post(
                    user_id=user_id,
                    content_type=content_type,
                    caption=encrypted_caption.get('encrypted_data'),
                    encryption_key=encrypted_caption.get('key'),
                    encryption_iv=encrypted_caption.get('nonce'),
                    is_encrypted=True
                )
            else:
                post_id = db_manager.create_encrypted_post(
                    user_id=user_id,
                    content_type=content_type,
                    caption=caption,
                    encryption_key=None,
                    encryption_iv=None,
                    is_encrypted=False
                )
            
            if not post_id:
                return jsonify({'success': False, 'error': 'Error creating post'}), 500
            
            if caption:
                db_manager.process_hashtags(post_id, caption)
                db_manager.process_mentions(post_id, caption)
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'message': 'Publicación creada exitosamente'
            })
        
        files = request.files.getlist('files') or request.files.getlist('media')
        caption = request.form.get('caption', '')
        
        if len(files) > 10:
            return jsonify({'success': False, 'error': 'Máximo 10 archivos permitidos'}), 400
        
        has_video = any(f.content_type.startswith('video/') for f in files)
        content_type = 'video' if has_video else 'image'
        if len(files) > 1:
            content_type = 'carousel'
        
        encryption_meta = encryption_manager.generate_content_key()
        
        post_id = db_manager.create_encrypted_post(
            user_id=user_id,
            content_type=content_type,
            caption=caption,
            encryption_key=encryption_meta['key'],
            encryption_iv=encryption_meta['iv'],
            is_encrypted=True
        )
        
        if not post_id:
            return jsonify({'success': False, 'error': 'Error creating post'}), 500
        
        media_results = []
        for i, file in enumerate(files):
            file_data = file.read()
            
            upload_result = cloudinary_service.upload_encrypted_media(
                file_data=file_data,
                content_type=file.content_type,
                folder=f"encrypted_posts/{user_id}"
            )
            
            if not upload_result['success']:
                logger.error(f"Failed to upload file {i}: {upload_result.get('error')}")
                continue
            
            media_id = db_manager.add_post_media(
                post_id=post_id,
                media_type=upload_result['resource_type'],
                media_url=upload_result['url'],
                encrypted_url=upload_result['url'],
                encryption_key=upload_result['encryption_key'],
                encryption_iv=upload_result['encryption_iv'],
                media_order=i
            )
            
            media_results.append({
                'id': media_id,
                'url': upload_result['url'],
                'type': upload_result['resource_type']
            })
        
        if caption:
            db_manager.process_hashtags(post_id, caption)
            db_manager.process_mentions(post_id, caption)
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'media_count': len(media_results),
            'message': 'Publicación creada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error creating publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/feed', methods=['GET'])
@require_telegram_auth
def get_feed():
    """Get user's feed with decrypted content for viewing"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_feed_posts(user_id, limit, offset)
        
        for post in posts:
            if not post.get('avatar_url') and post.get('user_id'):
                avatar_data = db_manager.get_user_avatar_data(str(post.get('user_id')))
                if avatar_data:
                    post['avatar_url'] = f"/api/avatar/{post.get('user_id')}"
            
            if post.get('is_encrypted') and post.get('caption') and post.get('encryption_key') and post.get('encryption_iv'):
                try:
                    logger.info(f"Attempting to decrypt post {post.get('id')}: key={post.get('encryption_key')[:20]}..., iv={post.get('encryption_iv')}")
                    decrypted = encryption_manager.decrypt_text(
                        post['caption'],
                        post['encryption_key'],
                        post['encryption_iv']
                    )
                    logger.info(f"Decrypt result for post {post.get('id')}: success={decrypted.get('success')}, text={decrypted.get('text', '')[:50] if decrypted.get('text') else 'None'}")
                    if decrypted.get('success'):
                        post['caption'] = decrypted.get('text', post['caption'])
                    else:
                        logger.warning(f"Decryption failed for post {post.get('id')}: {decrypted.get('error')}")
                except Exception as decrypt_error:
                    logger.warning(f"Could not decrypt caption for post {post.get('id')}: {decrypt_error}")
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/check-new', methods=['GET'])
@require_telegram_auth
def check_new_posts():
    """Check for new posts since a given post ID"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        since_id = request.args.get('since_id', type=int)
        
        if not since_id:
            return jsonify({'success': True, 'new_count': 0})
        
        new_count = db_manager.count_new_posts(user_id, since_id)
        
        return jsonify({
            'success': True,
            'new_count': new_count
        })
        
    except Exception as e:
        logger.error(f"Error checking new posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>', methods=['GET'])
@require_telegram_auth
def get_publication(post_id):
    """Get a single publication with all details"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        post = db_manager.get_post_with_media(post_id, user_id)
        
        if not post:
            return jsonify({'success': False, 'error': 'Publicación no encontrada'}), 404
        
        db_manager.record_post_view(post_id, user_id)
        
        return jsonify({
            'success': True,
            'post': post
        })
        
    except Exception as e:
        logger.error(f"Error getting publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>', methods=['PUT'])
@require_telegram_auth
def update_publication(post_id):
    """Update a publication (caption, comments enabled)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        success = db_manager.update_post(
            post_id=post_id,
            user_id=user_id,
            caption=data.get('caption'),
            comments_enabled=data.get('comments_enabled')
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo actualizar'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Publicación actualizada'
        })
        
    except Exception as e:
        logger.error(f"Error updating publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>', methods=['DELETE'])
@require_telegram_auth
def delete_publication(post_id):
    """Delete a publication"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.delete_post(post_id, user_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo eliminar'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Publicación eliminada'
        })
        
    except Exception as e:
        logger.error(f"Error deleting publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/gallery/<user_id>', methods=['GET'])
@require_telegram_auth
def get_user_gallery(user_id):
    """Get user's gallery (grid of posts)"""
    try:
        viewer_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_user_gallery(user_id, viewer_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting gallery: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/react', methods=['POST'])
@require_telegram_auth
def react_to_post(post_id):
    """Add or change reaction to a post"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction_type = data.get('reaction', 'like')
        
        success = db_manager.add_reaction(user_id, post_id, reaction_type)
        
        return jsonify({
            'success': success,
            'reaction': reaction_type
        })
        
    except Exception as e:
        logger.error(f"Error reacting to post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/unreact', methods=['POST'])
@require_telegram_auth
def unreact_to_post(post_id):
    """Remove reaction from a post"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.remove_reaction(user_id, post_id)
        
        return jsonify({
            'success': success
        })
        
    except Exception as e:
        logger.error(f"Error unreacting to post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/comments', methods=['GET'])
@require_telegram_auth
def get_post_comments(post_id):
    """Get comments for a post"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        comments = db_manager.get_post_comments(post_id, limit, offset)
        
        return jsonify({
            'success': True,
            'comments': comments
        })
        
    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/comments', methods=['POST'])
@require_telegram_auth
@rate_limit('comments_create')
def add_comment(post_id):
    """Add a comment to a post"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return jsonify({'success': False, 'error': 'Contenido requerido'}), 400
        
        comment_id = db_manager.add_comment(user_id, post_id, content, parent_id)
        
        if comment_id:
            db_manager.process_mentions(post_id, content, 'comment')
        
        return jsonify({
            'success': comment_id is not None,
            'comment_id': comment_id
        })
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@require_telegram_auth
def like_comment(comment_id):
    """Like a comment"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.like_comment(user_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error liking comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/unlike', methods=['POST'])
@require_telegram_auth
def unlike_comment(comment_id):
    """Unlike a comment"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.unlike_comment(user_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unliking comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>', methods=['PUT'])
@require_telegram_auth
@rate_limit('comments_create')
def update_comment(comment_id):
    """Update a comment - only author can edit within time limit"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Contenido requerido'}), 400
        
        if len(content) > 2000:
            return jsonify({'success': False, 'error': 'Comentario muy largo (máximo 2000 caracteres)'}), 400
        
        result = db_manager.update_comment(user_id, comment_id, content)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>', methods=['GET'])
@require_telegram_auth
def get_comment(comment_id):
    """Get a single comment by ID"""
    try:
        comment = db_manager.get_comment_by_id(comment_id)
        
        if comment:
            return jsonify({'success': True, 'comment': comment})
        else:
            return jsonify({'success': False, 'error': 'Comentario no encontrado'}), 404
        
    except Exception as e:
        logger.error(f"Error getting comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/react', methods=['POST'])
@require_telegram_auth
def add_comment_reaction(comment_id):
    """Add or update reaction to a comment"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction_type = data.get('reaction_type', '').strip()
        
        if not reaction_type:
            return jsonify({'success': False, 'error': 'Tipo de reacción requerido'}), 400
        
        result = db_manager.add_comment_reaction(user_id, comment_id, reaction_type)
        
        if result.get('success'):
            reactions = db_manager.get_comment_reactions(comment_id)
            return jsonify({
                'success': True,
                'reactions': reactions.get('reactions', {}),
                'total': reactions.get('total', 0),
                'user_reaction': reaction_type
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error adding comment reaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/react', methods=['DELETE'])
@require_telegram_auth
def remove_comment_reaction(comment_id):
    """Remove reaction from a comment"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        result = db_manager.remove_comment_reaction(user_id, comment_id)
        
        if result.get('success'):
            reactions = db_manager.get_comment_reactions(comment_id)
            return jsonify({
                'success': True,
                'reactions': reactions.get('reactions', {}),
                'total': reactions.get('total', 0),
                'user_reaction': None
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error removing comment reaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/reactions', methods=['GET'])
@require_telegram_auth
def get_comment_reactions_api(comment_id):
    """Get reactions for a comment"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        reactions = db_manager.get_comment_reactions(comment_id)
        user_reaction = db_manager.get_user_comment_reaction(user_id, comment_id)
        
        return jsonify({
            'success': True,
            'reactions': reactions.get('reactions', {}),
            'total': reactions.get('total', 0),
            'user_reaction': user_reaction
        })
        
    except Exception as e:
        logger.error(f"Error getting comment reactions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/pin-comment', methods=['POST'])
@require_telegram_auth
def pin_comment(post_id):
    """Pin a comment (post owner only)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        comment_id = data.get('comment_id')
        
        if not comment_id:
            return jsonify({'success': False, 'error': 'ID de comentario requerido'}), 400
        
        success = db_manager.pin_comment(user_id, post_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error pinning comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/save', methods=['POST'])
@require_telegram_auth
def save_post(post_id):
    """Save a post to favorites"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.save_post(user_id, post_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error saving post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/unsave', methods=['POST'])
@require_telegram_auth
def unsave_post(post_id):
    """Remove post from favorites"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.unsave_post(user_id, post_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unsaving post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/saved', methods=['GET'])
@require_telegram_auth
def get_saved_posts():
    """Get user's saved posts"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_saved_posts(user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting saved posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/share', methods=['POST'])
@require_telegram_auth
def share_post(post_id):
    """Share/repost a publication"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        share_type = data.get('type', 'repost')
        quote_text = data.get('quote')
        recipient_id = data.get('recipient_id')
        
        share_id = db_manager.share_post(user_id, post_id, share_type, quote_text, recipient_id)
        
        return jsonify({
            'success': share_id is not None,
            'share_id': share_id
        })
        
    except Exception as e:
        logger.error(f"Error sharing post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publications/<int:post_id>/share-count', methods=['POST'])
@require_telegram_auth
def increment_share_count(post_id):
    """Increment share count for external shares (copy link, Telegram share)"""
    try:
        db_manager.increment_share_count(post_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error incrementing share count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# STORIES SYSTEM
# ============================================================

@app.route('/api/stories/create', methods=['POST'])
@require_telegram_auth
def create_story():
    """Create a new story (24h expiry)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Archivo requerido'}), 400
        
        file = request.files['file']
        file_data = file.read()
        
        if file.content_type.startswith('video/'):
            pass
        
        upload_result = cloudinary_service.upload_story_media(
            file_data=file_data,
            content_type=file.content_type
        )
        
        if not upload_result['success']:
            return jsonify({'success': False, 'error': upload_result.get('error')}), 500
        
        story_id = db_manager.create_story(
            user_id=user_id,
            media_type=upload_result['resource_type'],
            media_url=upload_result['url'],
            encrypted_url=upload_result['url'],
            encryption_key=upload_result['encryption_key'],
            encryption_iv=upload_result['encryption_iv']
        )
        
        return jsonify({
            'success': story_id is not None,
            'story_id': story_id
        })
        
    except Exception as e:
        logger.error(f"Error creating story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/feed', methods=['GET'])
@require_telegram_auth
def get_stories_feed():
    """Get stories from followed users"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        stories = db_manager.get_stories_feed(user_id)
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        logger.error(f"Error getting stories feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/user/<target_user_id>', methods=['GET'])
@require_telegram_auth
def get_user_stories(target_user_id):
    """Get all stories from a specific user"""
    try:
        viewer_id = str(request.telegram_user.get('id', 0))
        
        stories = db_manager.get_user_stories(target_user_id, viewer_id)
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        logger.error(f"Error getting user stories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/<int:story_id>/view', methods=['POST'])
@require_telegram_auth
def view_story(story_id):
    """Mark a story as viewed"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.view_story(story_id, user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error viewing story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/<int:story_id>/viewers', methods=['GET'])
@require_telegram_auth
def get_story_viewers(story_id):
    """Get list of users who viewed a story (owner only)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        viewers = db_manager.get_story_viewers(story_id, user_id)
        
        return jsonify({
            'success': True,
            'viewers': viewers
        })
        
    except Exception as e:
        logger.error(f"Error getting story viewers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/<int:story_id>', methods=['DELETE'])
@require_telegram_auth
def delete_story(story_id):
    """Delete a story (owner only)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.delete_story(story_id, user_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo eliminar la historia'}), 400
        
        return jsonify({'success': True, 'message': 'Historia eliminada'})
        
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stories/<int:story_id>/react', methods=['POST'])
@require_telegram_auth
def react_to_story(story_id):
    """React to a story with an emoji"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction = data.get('reaction', '❤️')
        
        success = db_manager.react_to_story(story_id, user_id, reaction)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error reacting to story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# EXPLORE & SEARCH
# ============================================================

@app.route('/api/explore', methods=['GET'])
@require_telegram_auth
def explore_posts():
    """Get trending/popular posts for explore page"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_explore_posts(user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting explore posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search/posts', methods=['GET'])
@require_telegram_auth
def search_posts():
    """Search posts by caption text"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({'success': True, 'posts': []})
        
        posts = db_manager.search_posts(query, user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search/users', methods=['GET'])
@require_telegram_auth
def search_users():
    """Search users by username or name"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify({'success': True, 'users': []})
        
        users = db_manager.search_users(query, user_id, limit)
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/hashtag/<hashtag>', methods=['GET'])
@require_telegram_auth
def get_hashtag_posts(hashtag):
    """Get posts by hashtag"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_posts_by_hashtag(hashtag, user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'hashtag': hashtag,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting hashtag posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trending/hashtags', methods=['GET'])
@require_telegram_auth
def get_trending_hashtags():
    """Get trending hashtags"""
    try:
        limit = int(request.args.get('limit', 10))
        
        hashtags = db_manager.get_trending_hashtags(limit)
        
        return jsonify({
            'success': True,
            'hashtags': hashtags
        })
        
    except Exception as e:
        logger.error(f"Error getting trending hashtags: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/suggested/users', methods=['GET'])
@require_telegram_auth
def get_suggested_users():
    """Get suggested users to follow"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 10))
        
        users = db_manager.get_suggested_users(user_id, limit)
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        logger.error(f"Error getting suggested users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route('/api/notifications', methods=['GET'])
@require_telegram_auth
def get_notifications():
    """Get user notifications"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        filter_type = request.args.get('filter', 'all')
        
        notifications = db_manager.get_notifications(
            user_id, limit, offset, unread_only, filter_type
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/count', methods=['GET'])
@require_telegram_auth
def get_notifications_count():
    """Get unread notifications count"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        count = db_manager.get_unread_notifications_count(user_id)
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/read', methods=['POST'])
@require_telegram_auth
def mark_notifications_read():
    """Mark notifications as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        notification_ids = data.get('ids')
        
        success = db_manager.mark_notifications_read(user_id, notification_ids)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error marking notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/unread-count', methods=['GET'])
@require_telegram_auth
def get_unread_notifications_count():
    """Get unread notifications count (alias)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        count = db_manager.get_unread_notifications_count(user_id)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/mark-all-read', methods=['POST'])
@require_telegram_auth
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        success = db_manager.mark_notifications_read(user_id, None)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error marking all notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@require_telegram_auth
def mark_single_notification_read(notification_id):
    """Mark single notification as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        success = db_manager.mark_notifications_read(user_id, [notification_id])
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/preferences', methods=['GET'])
@require_telegram_auth
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        preferences = db_manager.get_notification_preferences(user_id)
        return jsonify({'success': True, 'preferences': preferences})
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/preferences', methods=['POST'])
@require_telegram_auth
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        preferences = data.get('preferences', {})
        
        valid_keys = ['likes', 'comments', 'follows', 'mentions', 'transactions', 'stories', 'push_enabled']
        clean_prefs = {k: bool(v) for k, v in preferences.items() if k in valid_keys}
        
        success = db_manager.update_notification_preferences(user_id, clean_prefs)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# BLOCK & REPORT SYSTEM
# ============================================================

@app.route('/api/users/<blocked_user_id>/block', methods=['POST'])
@require_telegram_auth
def block_user(blocked_user_id):
    """Block a user"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        if user_id == blocked_user_id:
            return jsonify({'success': False, 'error': 'No puedes bloquearte a ti mismo'}), 400
        
        success = db_manager.block_user(user_id, blocked_user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<blocked_user_id>/unblock', methods=['POST'])
@require_telegram_auth
def unblock_user(blocked_user_id):
    """Unblock a user"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.unblock_user(user_id, blocked_user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/blocked', methods=['GET'])
@require_telegram_auth
def get_blocked_users():
    """Get list of blocked users"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        
        blocked = db_manager.get_blocked_users(user_id)
        
        return jsonify({
            'success': True,
            'blocked_users': blocked
        })
        
    except Exception as e:
        logger.error(f"Error getting blocked users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report', methods=['POST'])
@require_telegram_auth
def create_report():
    """Create a content report"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        reason = data.get('reason')
        description = data.get('description')
        
        if not all([content_type, content_id, reason]):
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        report_id = db_manager.create_report(
            user_id, content_type, content_id, reason, description
        )
        
        return jsonify({
            'success': report_id is not None,
            'report_id': report_id
        })
        
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/reports', methods=['GET'])
@require_telegram_auth
@require_owner
def get_reports():
    """Admin: Get content reports"""
    try:
        status = request.args.get('status', 'pending')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        reports = db_manager.get_reports(status, limit, offset)
        
        return jsonify({
            'success': True,
            'reports': reports
        })
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/reports/<int:report_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_report(report_id):
    """Admin: Update report status"""
    try:
        admin_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        status = data.get('status')
        notes = data.get('notes')
        
        if not status:
            return jsonify({'success': False, 'error': 'Estado requerido'}), 400
        
        success = db_manager.update_report_status(report_id, status, admin_id, notes)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error updating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENCRYPTION KEY ENDPOINTS (for client-side decryption)
# ============================================================

@app.route('/api/encryption/key', methods=['GET'])
@require_telegram_auth
def get_content_encryption_key():
    """Get encryption key for decrypting content"""
    try:
        content_type = request.args.get('type')
        content_id = request.args.get('id')
        
        if not content_type or not content_id:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        if content_type == 'post':
            post = db_manager.get_post_with_media(int(content_id))
            if post:
                return jsonify({
                    'success': True,
                    'key': post.get('encryption_key'),
                    'iv': post.get('encryption_iv'),
                    'media_keys': [{
                        'id': m['id'],
                        'key': m.get('encryption_key'),
                        'iv': m.get('encryption_iv')
                    } for m in post.get('media', [])]
                })
        
        return jsonify({'success': False, 'error': 'Content not found'}), 404
        
    except Exception as e:
        logger.error(f"Error getting encryption key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cloudinary/status', methods=['GET'])
@require_telegram_auth
def check_cloudinary_status():
    """Check if Cloudinary is properly configured"""
    try:
        return jsonify({
            'success': True,
            'configured': cloudinary_service.is_configured()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS PARA NUMEROS VIRTUALES
# ============================================================

@app.route('/api/vn/providers', methods=['GET'])
@require_telegram_user
def get_vn_providers():
    """Get available virtual number providers (balance hidden for non-admins)"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Servicio no disponible'}), 503
        
        settings = db_manager.get_all_virtual_number_settings()
        user_id = str(request.telegram_user.get('id'))
        is_admin = is_owner(user_id)
        
        providers = []
        
        if settings.get('smspool_enabled', 'true') == 'true':
            provider_info = {
                'id': 'smspool',
                'name': 'SMSPool',
                'enabled': True,
                'type': 'api'
            }
            if is_admin:
                balance_result = vn_manager.get_smspool_balance()
                provider_info['balance'] = balance_result.get('balance', 0) if balance_result.get('success') else 0
            providers.append(provider_info)
        
        if settings.get('legitsms_enabled', 'true') == 'true':
            inventory = db_manager.get_legitsms_inventory(available_only=True)
            providers.append({
                'id': 'legitsms',
                'name': 'Legit SMS',
                'enabled': True,
                'available_numbers': len(inventory),
                'type': 'inventory'
            })
        
        return jsonify({
            'success': True,
            'providers': providers
        })
        
    except Exception as e:
        logger.error(f"Error getting VN providers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/countries', methods=['GET'])
@require_telegram_user
def get_vn_countries():
    """Get available countries for virtual numbers"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Servicio no disponible'}), 503
        
        provider = request.args.get('provider', 'smspool')
        
        if provider == 'smspool':
            if not vn_manager.smspool.api_key:
                return jsonify({'success': False, 'error': 'Servicio no configurado'}), 503
            result = vn_manager.get_available_countries()
            if result['success']:
                return jsonify({
                    'success': True,
                    'countries': result['countries']
                })
            return jsonify({'success': False, 'error': result.get('error', 'Error al obtener paises')}), 500
        
        elif provider == 'legitsms':
            inventory = db_manager.get_legitsms_inventory(available_only=True)
            countries = {}
            for item in inventory:
                code = item['country_code']
                if code not in countries:
                    countries[code] = {
                        'id': code,
                        'name': item.get('country_name', code),
                        'short_name': code,
                        'flag': vn_manager.smspool._get_flag_emoji(code)
                    }
            return jsonify({
                'success': True,
                'countries': list(countries.values())
            })
        
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400
        
    except Exception as e:
        logger.error(f"Error getting VN countries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/services', methods=['GET'])
@require_telegram_user
def get_vn_services():
    """Get available services for a country with prices"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Servicio no disponible'}), 503
        
        provider = request.args.get('provider', 'smspool')
        country = request.args.get('country')
        
        if not country:
            return jsonify({'success': False, 'error': 'Pais requerido'}), 400
        
        settings = db_manager.get_all_virtual_number_settings()
        commission = float(settings.get('commission_percent', 30))
        
        if provider == 'smspool':
            if not vn_manager.smspool.api_key:
                return jsonify({'success': False, 'error': 'Servicio no configurado'}), 503
            result = vn_manager.get_available_services(country, commission)
            if result['success']:
                return jsonify({
                    'success': True,
                    'services': result['services']
                })
            return jsonify({'success': False, 'error': result.get('error', 'Failed to get services')}), 500
        
        elif provider == 'legitsms':
            inventory = db_manager.get_legitsms_inventory(available_only=True)
            services = {}
            for item in inventory:
                if item['country_code'] == country:
                    code = item['service_code']
                    if code not in services:
                        price_info = vn_manager.calculate_user_price(
                            float(item.get('cost_usd', 0)), 
                            commission
                        )
                        services[code] = {
                            'id': code,
                            'name': item.get('service_name', code),
                            'short_name': code,
                            'price': float(item.get('cost_usd', 0)),
                            'original_price_usd': price_info['original_usd'],
                            'price_usd': price_info['with_commission_usd'],
                            'price_bunkercoin': price_info['bunkercoin'],
                            'icon': vn_manager.smspool._get_service_icon(item.get('service_name', ''))
                        }
            return jsonify({
                'success': True,
                'services': list(services.values())
            })
        
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400
        
    except Exception as e:
        logger.error(f"Error getting VN services: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/purchase', methods=['POST'])
@require_telegram_user
@rate_limit('vn_purchase')
def purchase_vn():
    """Purchase a virtual number"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Service not available'}), 503
        
        user_id = str(request.telegram_user.get('id'))
        data = request.get_json() or {}
        
        provider = data.get('provider', 'smspool')
        country = data.get('country')
        service = data.get('service')
        country_name = data.get('countryName', '')
        service_name = data.get('serviceName', '')
        
        if not country or not service:
            return jsonify({'success': False, 'error': 'Country and service required'}), 400
        
        settings = db_manager.get_all_virtual_number_settings()
        commission = float(settings.get('commission_percent', 30))
        
        if provider == 'smspool':
            result = vn_manager.purchase_virtual_number(
                user_id, country, service, 
                country_name, service_name, 
                commission
            )
            return jsonify(result)
        
        elif provider == 'legitsms':
            return jsonify({'success': False, 'error': 'Legit SMS not yet implemented'}), 501
        
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400
        
    except Exception as e:
        logger.error(f"Error purchasing VN: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/check/<order_id>', methods=['GET'])
@require_telegram_user
def check_vn_sms(order_id):
    """Check if SMS has been received for an order"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Servicio no disponible'}), 503
        
        if not vn_manager.smspool.api_key:
            return jsonify({'success': False, 'error': 'Servicio no configurado'}), 503
        
        user_id = str(request.telegram_user.get('id'))
        result = vn_manager.check_sms_status(order_id, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking VN SMS: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/cancel/<order_id>', methods=['POST'])
@require_telegram_user
def cancel_vn_order(order_id):
    """Cancel a virtual number order"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Servicio no disponible'}), 503
        
        if not vn_manager.smspool.api_key:
            return jsonify({'success': False, 'error': 'Servicio no configurado'}), 503
        
        user_id = str(request.telegram_user.get('id'))
        result = vn_manager.cancel_order(order_id, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error cancelling VN order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/history', methods=['GET'])
@require_telegram_user
def get_vn_history():
    """Get user's virtual number order history"""
    try:
        if not vn_manager:
            return jsonify({'success': False, 'error': 'Service not available'}), 503
        
        user_id = str(request.telegram_user.get('id'))
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        result = vn_manager.get_user_history(user_id, limit, offset)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting VN history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vn/active', methods=['GET'])
@require_telegram_user
def get_vn_active():
    """Get user's active virtual number orders"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        user_id = str(request.telegram_user.get('id'))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, provider, country_code, country_name, service_code,
                           service_name, phone_number, sms_code, status,
                           bunkercoin_charged, expires_at, created_at
                    FROM virtual_number_orders
                    WHERE user_id = %s AND status IN ('pending', 'active')
                    ORDER BY created_at DESC
                """, (user_id,))
                
                orders = []
                for row in cur.fetchall():
                    orders.append({
                        'id': str(row['id']),
                        'provider': row['provider'],
                        'country': row['country_name'] or row['country_code'],
                        'service': row['service_name'] or row['service_code'],
                        'phoneNumber': row['phone_number'],
                        'smsCode': row['sms_code'],
                        'status': row['status'],
                        'cost': float(row['bunkercoin_charged']) if row['bunkercoin_charged'] else 0,
                        'expiresAt': row['expires_at'].isoformat() if row['expires_at'] else None,
                        'createdAt': row['created_at'].isoformat() if row['created_at'] else None
                    })
        
        return jsonify({
            'success': True,
            'orders': orders
        })
        
    except Exception as e:
        logger.error(f"Error getting active VN orders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS ADMIN PARA NUMEROS VIRTUALES
# ============================================================

@app.route('/api/admin/vn/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_stats():
    """Admin: Get virtual number statistics"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        days = int(request.args.get('days', 30))
        stats = db_manager.get_virtual_number_stats(days)
        
        balance_result = vn_manager.get_smspool_balance() if vn_manager else {'success': False}
        
        return jsonify({
            'success': True,
            'stats': stats,
            'smspoolBalance': balance_result.get('balance', 0) if balance_result.get('success') else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting admin VN stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/settings', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_settings():
    """Admin: Get virtual number settings"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        settings = db_manager.get_all_virtual_number_settings()
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        logger.error(f"Error getting admin VN settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/settings', methods=['POST'])
@require_telegram_auth
@require_owner
def update_admin_vn_settings():
    """Admin: Update virtual number settings"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        data = request.get_json() or {}
        
        allowed_keys = ['commission_percent', 'smspool_enabled', 'legitsms_enabled', 'default_expiry_minutes']
        
        for key, value in data.items():
            if key in allowed_keys:
                db_manager.set_virtual_number_setting(key, str(value))
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating admin VN settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/inventory', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_inventory():
    """Admin: Get Legit SMS inventory"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        available_only = request.args.get('available_only', 'true').lower() == 'true'
        inventory = db_manager.get_legitsms_inventory(available_only)
        
        return jsonify({
            'success': True,
            'inventory': inventory
        })
        
    except Exception as e:
        logger.error(f"Error getting admin VN inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/inventory', methods=['POST'])
@require_telegram_auth
@require_owner
def add_admin_vn_inventory():
    """Admin: Add number to Legit SMS inventory"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        data = request.get_json() or {}
        
        country_code = data.get('countryCode')
        country_name = data.get('countryName')
        service_code = data.get('serviceCode')
        service_name = data.get('serviceName')
        phone_number = data.get('phoneNumber')
        cost_usd = float(data.get('costUsd', 0))
        
        if not all([country_code, service_code, phone_number]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        success = db_manager.add_to_legitsms_inventory(
            country_code, country_name, service_code, service_name, phone_number, cost_usd
        )
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error adding to admin VN inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/inventory/<inventory_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def delete_admin_vn_inventory(inventory_id):
    """Admin: Delete number from Legit SMS inventory"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        success = db_manager.remove_from_legitsms_inventory(inventory_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error deleting from admin VN inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vn/orders', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_orders():
    """Admin: Get all virtual number orders with filters"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        status = request.args.get('status', '')
        provider = request.args.get('provider', '')
        country = request.args.get('country', '')
        service = request.args.get('service', '')
        user_id = request.args.get('user_id', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT vno.*, u.username, u.first_name, u.last_name
                    FROM virtual_number_orders vno
                    LEFT JOIN users u ON vno.user_id = u.telegram_id::text
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) FROM virtual_number_orders vno WHERE 1=1"
                params = []
                count_params = []
                
                if status:
                    query += " AND vno.status = %s"
                    count_query += " AND vno.status = %s"
                    params.append(status)
                    count_params.append(status)
                
                if provider:
                    query += " AND vno.provider = %s"
                    count_query += " AND vno.provider = %s"
                    params.append(provider)
                    count_params.append(provider)
                
                if country:
                    query += " AND (vno.country_code ILIKE %s OR vno.country_name ILIKE %s)"
                    count_query += " AND (vno.country_code ILIKE %s OR vno.country_name ILIKE %s)"
                    params.extend([f'%{country}%', f'%{country}%'])
                    count_params.extend([f'%{country}%', f'%{country}%'])
                
                if service:
                    query += " AND (vno.service_code ILIKE %s OR vno.service_name ILIKE %s)"
                    count_query += " AND (vno.service_code ILIKE %s OR vno.service_name ILIKE %s)"
                    params.extend([f'%{service}%', f'%{service}%'])
                    count_params.extend([f'%{service}%', f'%{service}%'])
                
                if user_id:
                    query += " AND vno.user_id = %s"
                    count_query += " AND vno.user_id = %s"
                    params.append(user_id)
                    count_params.append(user_id)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY vno.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                orders = []
                
                for row in cur.fetchall():
                    orders.append({
                        'id': str(row['id']),
                        'userId': row['user_id'],
                        'username': row.get('username') or row.get('first_name') or 'Unknown',
                        'provider': row['provider'],
                        'countryCode': row['country_code'],
                        'countryName': row['country_name'],
                        'serviceCode': row['service_code'],
                        'serviceName': row['service_name'],
                        'phoneNumber': row['phone_number'],
                        'providerOrderId': row['provider_order_id'],
                        'costUsd': float(row['cost_usd']) if row['cost_usd'] else 0,
                        'costWithCommission': float(row['cost_with_commission']) if row['cost_with_commission'] else 0,
                        'bunkercoinCharged': float(row['bunkercoin_charged']) if row['bunkercoin_charged'] else 0,
                        'smsCode': row['sms_code'],
                        'status': row['status'],
                        'expiresAt': row['expires_at'].isoformat() if row['expires_at'] else None,
                        'createdAt': row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                return jsonify({
                    'success': True,
                    'orders': orders,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1
                })
    
    except Exception as e:
        logger.error(f"Error getting admin VN orders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/virtual-numbers')
@require_telegram_auth
def virtual_numbers_page():
    """Render virtual numbers page"""
    return render_template('virtual_numbers.html')


def log_admin_action(admin_id, admin_name, action_type, target_type=None, target_id=None, description=None, metadata=None):
    """Helper function to log admin actions."""
    try:
        if not db_manager:
            return
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent', '')[:500] if request else None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, admin_name, action_type, target_type, target_id, description, ip_address, user_agent, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (admin_id, admin_name, action_type, target_type, target_id, description, ip_address, user_agent, json.dumps(metadata) if metadata else None))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")


@app.route('/api/admin/logs/admin', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_admin_logs():
    """Admin: Obtener logs de acciones de administradores."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0, 'actionTypes': []})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', request.args.get('limit', 50))), 100)
        action_type = request.args.get('action_type', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM admin_logs WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM admin_logs WHERE 1=1"
                params = []
                count_params = []
                
                if action_type:
                    query += " AND action_type = %s"
                    count_query += " AND action_type = %s"
                    params.append(action_type)
                    count_params.append(action_type)
                
                if search:
                    query += " AND (admin_name ILIKE %s OR description ILIKE %s OR target_id::text ILIKE %s)"
                    count_query += " AND (admin_name ILIKE %s OR description ILIKE %s OR target_id::text ILIKE %s)"
                    search_pattern = f'%{search}%'
                    params.extend([search_pattern, search_pattern, search_pattern])
                    count_params.extend([search_pattern, search_pattern, search_pattern])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + INTERVAL '1 day'"
                    count_query += " AND created_at <= %s::date + INTERVAL '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = cur.fetchall()
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                cur.execute("""
                    SELECT action_type, COUNT(*) as count
                    FROM admin_logs
                    GROUP BY action_type
                    ORDER BY count DESC
                """)
                action_types = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'actionTypes': action_types
                })
    
    except Exception as e:
        logger.error(f"Error getting admin logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0, 'actionTypes': []})


@app.route('/api/admin/logs/security', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_logs():
    """Admin: Obtener logs de seguridad (intentos de login, actividad sospechosa)."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        activity_type = request.args.get('activity_type', '')
        user_id = request.args.get('user_id', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM security_activity_log WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM security_activity_log WHERE 1=1"
                params = []
                count_params = []
                
                if activity_type:
                    query += " AND activity_type = %s"
                    count_query += " AND activity_type = %s"
                    params.append(activity_type)
                    count_params.append(activity_type)
                
                if user_id:
                    query += " AND user_id = %s"
                    count_query += " AND user_id = %s"
                    params.append(user_id)
                    count_params.append(user_id)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM security_activity_log
                    GROUP BY activity_type
                    ORDER BY count DESC
                """)
                activity_types = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'activityTypes': activity_types
                })
    
    except Exception as e:
        logger.error(f"Error getting security logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@app.route('/api/admin/logs/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_export_logs():
    """Admin: Exportar logs a CSV o JSON."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        log_type = request.args.get('type', 'admin')
        export_format = request.args.get('format', 'csv')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        days = int(request.args.get('days', 30))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if log_type == 'admin':
                    query = """
                        SELECT id, admin_id, admin_name, action_type, target_type, 
                               target_id, description, ip_address, created_at
                        FROM admin_logs WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'security':
                    query = """
                        SELECT id, user_id, activity_type, description, 
                               device_id, ip_address, created_at
                        FROM security_activity_log WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'client':
                    query = """
                        SELECT id, user_id, log_type, action, is_mobile, 
                               is_telegram, ip, created_at
                        FROM client_logs WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'errors':
                    query = """
                        SELECT id, error_level, endpoint, error_message, 
                               user_id, ip_address, is_resolved, created_at
                        FROM system_errors WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'logins':
                    query = """
                        SELECT id, user_id, activity_type, description, 
                               device_id, ip_address, created_at
                        FROM security_activity_log 
                        WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED') 
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'config':
                    query = """
                        SELECT id, config_key, old_value, new_value, 
                               changed_by_name, ip_address, description, created_at
                        FROM config_history WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                else:
                    return jsonify({'success': False, 'error': 'Tipo de log inválido'}), 400
                
                logs = [dict(row) for row in cur.fetchall()]
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                if export_format == 'json':
                    return Response(
                        json.dumps(logs, indent=2, ensure_ascii=False),
                        mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename={log_type}_logs.json'}
                    )
                else:
                    if not logs:
                        return Response(
                            '',
                            mimetype='text/csv',
                            headers={'Content-Disposition': f'attachment; filename={log_type}_logs.csv'}
                        )
                    
                    output = io.StringIO()
                    headers = list(logs[0].keys())
                    output.write(','.join(headers) + '\n')
                    
                    for log in logs:
                        row_values = []
                        for h in headers:
                            value = log.get(h, '')
                            if isinstance(value, str) and (',' in value or '"' in value or '\n' in value):
                                value = '"' + value.replace('"', '""') + '"'
                            row_values.append(str(value) if value is not None else '')
                        output.write(','.join(row_values) + '\n')
                    
                    return Response(
                        output.getvalue(),
                        mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment; filename={log_type}_logs.csv'}
                    )
    
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def log_system_error(error_level, endpoint, error_message, stack_trace=None, user_id=None, metadata=None):
    """Helper function to log system errors."""
    try:
        if not db_manager:
            return
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent', '')[:500] if request else None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_errors (error_level, endpoint, error_message, stack_trace, user_id, ip_address, user_agent, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (error_level, endpoint, error_message, stack_trace, user_id, ip_address, user_agent, json.dumps(metadata) if metadata else None))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging system error: {e}")


@app.route('/api/admin/logs/errors', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_error_logs():
    """Admin: Obtener logs de errores del sistema."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        error_level = request.args.get('level', '')
        is_resolved = request.args.get('resolved', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM system_errors WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM system_errors WHERE 1=1"
                params = []
                count_params = []
                
                if error_level:
                    query += " AND error_level = %s"
                    count_query += " AND error_level = %s"
                    params.append(error_level)
                    count_params.append(error_level)
                
                if is_resolved != '':
                    resolved_bool = is_resolved.lower() == 'true'
                    query += " AND is_resolved = %s"
                    count_query += " AND is_resolved = %s"
                    params.append(resolved_bool)
                    count_params.append(resolved_bool)
                
                if search:
                    query += " AND (error_message ILIKE %s OR endpoint ILIKE %s)"
                    count_query += " AND (error_message ILIKE %s OR endpoint ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    if log_entry.get('resolved_at'):
                        log_entry['resolved_at'] = log_entry['resolved_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT error_level, COUNT(*) as count
                    FROM system_errors
                    GROUP BY error_level
                    ORDER BY count DESC
                """)
                error_levels = [dict(row) for row in cur.fetchall()]
                
                cur.execute("SELECT COUNT(*) FROM system_errors WHERE is_resolved = FALSE")
                unresolved_count = cur.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'errorLevels': error_levels,
                    'unresolvedCount': unresolved_count
                })
    
    except Exception as e:
        logger.error(f"Error getting error logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@app.route('/api/admin/logs/errors/<int:error_id>/resolve', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_resolve_error(error_id):
    """Admin: Marcar error como resuelto."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 503
        
        user_id = getattr(request, 'user_id', '0')
        user_data = getattr(request, 'user_data', {})
        admin_name = user_data.get('first_name', 'Admin')
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE system_errors
                    SET is_resolved = TRUE, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s
                """, (admin_name, error_id))
            conn.commit()
        
        log_admin_action(user_id, admin_name, 'error_resolve', 'system_error', str(error_id), 'Marked error as resolved')
        
        return jsonify({'success': True, 'message': 'Error marcado como resuelto'})
    
    except Exception as e:
        logger.error(f"Error resolving system error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/logs/logins', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_login_logs():
    """Admin: Obtener logs de intentos de login."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """SELECT * FROM security_activity_log 
                           WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                                   'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')"""
                count_query = """SELECT COUNT(*) FROM security_activity_log 
                                WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                                        'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')"""
                params = []
                count_params = []
                
                if status == 'success':
                    query += " AND activity_type IN ('LOGIN_SUCCESS', 'WALLET_ACCESS')"
                    count_query += " AND activity_type IN ('LOGIN_SUCCESS', 'WALLET_ACCESS')"
                elif status == 'failed':
                    query += " AND activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')"
                    count_query += " AND activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')"
                elif status == 'blocked':
                    query += " AND activity_type IN ('WALLET_LOCKOUT', 'IP_BLOCKED')"
                    count_query += " AND activity_type IN ('WALLET_LOCKOUT', 'IP_BLOCKED')"
                
                if search:
                    query += " AND (user_id ILIKE %s OR ip_address ILIKE %s)"
                    count_query += " AND (user_id ILIKE %s OR ip_address ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM security_activity_log
                    WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                           'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')
                    GROUP BY activity_type
                    ORDER BY count DESC
                """)
                login_stats = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT ip_address, COUNT(*) as attempts
                    FROM security_activity_log
                    WHERE activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')
                    AND created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY ip_address
                    HAVING COUNT(*) >= 5
                    ORDER BY attempts DESC
                    LIMIT 10
                """)
                suspicious_ips = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'loginStats': login_stats,
                    'suspiciousIPs': suspicious_ips
                })
    
    except Exception as e:
        logger.error(f"Error getting login logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@app.route('/api/admin/logs/config-history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_config_history():
    """Admin: Obtener historial de cambios de configuración."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        config_key = request.args.get('key', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM config_history WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM config_history WHERE 1=1"
                params = []
                count_params = []
                
                if config_key:
                    query += " AND config_key = %s"
                    count_query += " AND config_key = %s"
                    params.append(config_key)
                    count_params.append(config_key)
                
                if search:
                    query += " AND (config_key ILIKE %s OR changed_by_name ILIKE %s)"
                    count_query += " AND (config_key ILIKE %s OR changed_by_name ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT config_key, COUNT(*) as count
                    FROM config_history
                    GROUP BY config_key
                    ORDER BY count DESC
                """)
                config_keys = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'configKeys': config_keys
                })
    
    except Exception as e:
        logger.error(f"Error getting config history: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


def log_config_change(config_key, old_value, new_value, changed_by_id, changed_by_name, description=None):
    """Helper function to log configuration changes."""
    try:
        if not db_manager:
            return
        ip_address = request.remote_addr if request else None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO config_history (config_key, old_value, new_value, changed_by_id, changed_by_name, ip_address, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (config_key, str(old_value) if old_value is not None else None, str(new_value), changed_by_id, changed_by_name, ip_address, description))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging config change: {e}")


@app.route('/api/admin/config', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_config():
    """Admin: Obtener configuración del sistema."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'config': {}})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT config_key, config_value, config_type FROM system_config")
                rows = cur.fetchall()
                
                config = {}
                for row in rows:
                    value = row['config_value']
                    if row['config_type'] == 'number':
                        value = float(value) if '.' in str(value) else int(value)
                    elif row['config_type'] == 'boolean':
                        value = value.lower() == 'true'
                    config[row['config_key']] = value
                
                return jsonify({'success': True, 'config': config})
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'success': True, 'config': {}})


@app.route('/api/admin/config', methods=['POST'])
@require_telegram_auth
@require_owner  
def admin_update_config():
    """Admin: Actualizar configuración del sistema."""
    try:
        data = request.get_json()
        user_id = getattr(request, 'user_id', '0')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                for key, value in data.items():
                    cur.execute("""
                        UPDATE system_config 
                        SET config_value = %s, updated_at = NOW(), updated_by = %s
                        WHERE config_key = %s
                    """, (str(value), user_id, key))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'config_update', 'system_config', None, 
                        f"Updated config: {list(data.keys())}", {'changes': data})
        
        return jsonify({'success': True, 'message': 'Configuración actualizada'})
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/blocked-ips', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_blocked_ips():
    """Admin: Obtener lista de IPs bloqueadas."""
    try:
        if not db_manager:
            return jsonify({'success': True, 'ips': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blocked_ips 
                    WHERE is_active = true
                    ORDER BY blocked_at DESC
                """)
                ips = cur.fetchall()
                
                for ip in ips:
                    if ip.get('blocked_at'):
                        ip['blocked_at'] = ip['blocked_at'].isoformat()
                    if ip.get('expires_at'):
                        ip['expires_at'] = ip['expires_at'].isoformat()
                
                return jsonify({'success': True, 'ips': ips})
    
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return jsonify({'success': True, 'ips': []})


@app.route('/api/admin/blocked-ips', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_block_ip():
    """Admin: Bloquear una IP."""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address', '').strip()
        reason = data.get('reason', '')
        is_permanent = data.get('is_permanent', False)
        user_id = getattr(request, 'user_id', '0')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP requerida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO blocked_ips (ip_address, reason, blocked_by, is_permanent)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (ip_address, reason, user_id, is_permanent))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'ip_block', 'blocked_ips', ip_address, 
                        f"Blocked IP: {ip_address}", {'reason': reason, 'permanent': is_permanent})
        
        return jsonify({'success': True, 'message': f'IP {ip_address} bloqueada'})
    
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/blocked-ips/<int:ip_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_unblock_ip(ip_id):
    """Admin: Desbloquear una IP."""
    try:
        user_id = getattr(request, 'user_id', '0')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT ip_address FROM blocked_ips WHERE id = %s", (ip_id,))
                row = cur.fetchone()
                ip_address = row['ip_address'] if row else 'Unknown'
                
                cur.execute("UPDATE blocked_ips SET is_active = false WHERE id = %s", (ip_id,))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'ip_unblock', 'blocked_ips', str(ip_id), 
                        f"Unblocked IP: {ip_address}")
        
        return jsonify({'success': True, 'message': 'IP desbloqueada'})
    
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallet-pool/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_wallet_pool_stats():
    """Admin: Obtener estadísticas del pool de wallets."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM deposit_wallets")
                total = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as available FROM deposit_wallets WHERE status = 'available'")
                available = cur.fetchone()['available']
                
                cur.execute("SELECT COUNT(*) as assigned FROM deposit_wallets WHERE status = 'assigned'")
                assigned = cur.fetchone()['assigned']
                
                cur.execute("SELECT COUNT(*) as used FROM deposit_wallets WHERE status = 'used'")
                used = cur.fetchone()['used']
                
                cur.execute("SELECT COALESCE(SUM(deposit_amount), 0) as pending_balance FROM deposit_wallets WHERE deposit_amount > 0 AND consolidated_at IS NULL")
                pending_balance = float(cur.fetchone()['pending_balance'] or 0)
                
                return jsonify({
                    'success': True,
                    'stats': {
                        'total': total,
                        'available': available,
                        'assigned': assigned,
                        'used': used,
                        'pendingBalance': pending_balance
                    }
                })
    
    except Exception as e:
        logger.error(f"Error getting wallet pool stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/secrets-status', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_secrets_status():
    """Admin: Verificar qué secrets están configurados."""
    secrets_to_check = [
        'BOT_TOKEN',
        'ADMIN_TOKEN',
        'OWNER_TELEGRAM_ID',
        'TONCENTER_API_KEY',
        'B3C_HOT_WALLET_MNEMONIC',
        'WALLET_MASTER_KEY',
        'SMSPOOL_API_KEY',
        'CLOUDINARY_URL',
        'RESEND_API_KEY'
    ]
    
    status = {}
    for secret in secrets_to_check:
        status[secret] = bool(os.environ.get(secret))
    
    return jsonify({'success': True, 'secrets': status})


@app.route('/api/admin/wallets/hot', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_hot_wallet():
    """Admin: Obtener información del hot wallet."""
    try:
        hot_wallet_address = os.environ.get('TON_WALLET_ADDRESS', '')
        
        balance = 0
        if hot_wallet_address:
            try:
                from tracking.wallet_pool_service import get_wallet_pool_service
                wallet_svc = get_wallet_pool_service(db_manager)
                if wallet_svc:
                    balance = wallet_svc.get_wallet_balance(hot_wallet_address)
            except Exception as e:
                logger.warning(f"Could not get hot wallet balance: {e}")
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'address': hot_wallet_address,
            'balance': balance,
            'status': 'ok' if balance > 0.1 else 'low',
            'explorerUrl': explorer_url
        })
    
    except Exception as e:
        logger.error(f"Error getting hot wallet info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallets/deposits', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_deposit_wallets():
    """Admin: Obtener lista de wallets de depósito."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        status_filter = request.args.get('status', '')
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM deposit_wallets WHERE 1=1"
                params = []
                
                if status_filter:
                    query += " AND status = %s"
                    params.append(status_filter)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                wallets = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM deposit_wallets WHERE 1=1"
                if status_filter:
                    cur.execute(count_query + " AND status = %s", (status_filter,))
                else:
                    cur.execute(count_query)
                total = cur.fetchone()['total']
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'explorerUrl': explorer_url,
            'wallets': [{
                'id': w['id'],
                'wallet_address': w.get('wallet_address', ''),
                'status': w.get('status', 'unknown'),
                'assigned_to_user_id': w.get('assigned_to_user_id'),
                'deposit_amount': float(w.get('deposit_amount', 0) or 0),
                'created_at': str(w.get('created_at', '')),
                'consolidated_at': str(w.get('consolidated_at', '')) if w.get('consolidated_at') else None
            } for w in wallets],
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit
        })
    
    except Exception as e:
        logger.error(f"Error getting deposit wallets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallets/fill-pool', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_fill_wallet_pool():
    """Admin: Llenar el pool de wallets."""
    try:
        data = request.get_json() or {}
        count = min(int(data.get('count', 10)), 50)
        
        try:
            from tracking.wallet_pool_service import get_wallet_pool_service
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                created = wallet_svc.fill_pool(count)
                
                user_id = getattr(request, 'user_id', '0')
                log_admin_action(user_id, 'Admin', 'fill_wallet_pool', 'deposit_wallets', 
                               None, f"Created {created} new deposit wallets")
                
                return jsonify({
                    'success': True,
                    'created': created,
                    'message': f'{created} wallets creadas'
                })
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error filling wallet pool: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in fill wallet pool: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallets/consolidate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_consolidate_wallets():
    """Admin: Consolidar fondos de wallets de depósito al hot wallet."""
    try:
        try:
            from tracking.wallet_pool_service import get_wallet_pool_service
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                result = wallet_svc.consolidate_all_balances()
                
                user_id = getattr(request, 'user_id', '0')
                log_admin_action(user_id, 'Admin', 'consolidate_wallets', 'deposit_wallets', 
                               None, f"Consolidated {result.get('count', 0)} wallets, total: {result.get('total', 0)} TON")
                
                return jsonify({
                    'success': True,
                    'consolidated': result.get('count', 0),
                    'totalAmount': result.get('total', 0),
                    'message': f"Consolidados {result.get('count', 0)} wallets"
                })
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error consolidating wallets: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in consolidate wallets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/blockchain/history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_blockchain_history():
    """Admin: Obtener historial de transacciones blockchain."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        tx_type = request.args.get('type', '')
        limit = min(int(request.args.get('limit', 50)), 200)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                transactions = []
                
                if tx_type in ['', 'deposits', 'all']:
                    cur.execute("""
                        SELECT 'deposit' as tx_type, dw.deposit_tx_hash as tx_hash, 
                               dw.deposit_amount as amount, dw.wallet_address as from_address,
                               (SELECT wallet_address FROM deposit_wallets WHERE status = 'hot_wallet' LIMIT 1) as to_address,
                               dw.deposit_detected_at as created_at, 'confirmed' as status,
                               u.username
                        FROM deposit_wallets dw
                        LEFT JOIN users u ON dw.assigned_to_user_id = u.id
                        WHERE dw.deposit_tx_hash IS NOT NULL
                        ORDER BY dw.deposit_detected_at DESC
                        LIMIT %s
                    """, (limit,))
                    deposits = cur.fetchall()
                    transactions.extend(deposits)
                
                if tx_type in ['', 'consolidations', 'all']:
                    cur.execute("""
                        SELECT 'consolidation' as tx_type, consolidation_tx_hash as tx_hash,
                               deposit_amount as amount, wallet_address as from_address,
                               %s as to_address, consolidated_at as created_at, 'confirmed' as status,
                               NULL as username
                        FROM deposit_wallets
                        WHERE consolidation_tx_hash IS NOT NULL
                        ORDER BY consolidated_at DESC
                        LIMIT %s
                    """, (os.environ.get('TON_WALLET_ADDRESS', ''), limit))
                    consolidations = cur.fetchall()
                    transactions.extend(consolidations)
                
                if tx_type in ['', 'withdrawals', 'all']:
                    cur.execute("""
                        SELECT 'withdrawal' as tx_type, tx_hash, amount_ton as amount,
                               %s as from_address, wallet_address as to_address,
                               processed_at as created_at, status, u.username
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        WHERE tx_hash IS NOT NULL
                        ORDER BY processed_at DESC
                        LIMIT %s
                    """, (os.environ.get('TON_WALLET_ADDRESS', ''), limit))
                    withdrawals = cur.fetchall()
                    transactions.extend(withdrawals)
                
                transactions.sort(key=lambda x: x['created_at'] or datetime.min, reverse=True)
                transactions = transactions[:limit]
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'explorerUrl': explorer_url,
            'transactions': [{
                'tx_type': tx['tx_type'],
                'tx_hash': tx.get('tx_hash', ''),
                'amount': float(tx.get('amount', 0) or 0),
                'from_address': tx.get('from_address', '')[:20] + '...' if tx.get('from_address') else '-',
                'to_address': tx.get('to_address', '')[:20] + '...' if tx.get('to_address') else '-',
                'created_at': str(tx.get('created_at', '')),
                'status': tx.get('status', 'unknown'),
                'username': tx.get('username', '')
            } for tx in transactions],
            'total': len(transactions)
        })
    
    except Exception as e:
        logger.error(f"Error getting blockchain history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallets/pool-config', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_pool_config():
    """Admin: Obtener o guardar configuración del pool de wallets."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        config_key VARCHAR(100) PRIMARY KEY,
                        config_value TEXT,
                        config_type VARCHAR(50),
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by VARCHAR(100)
                    )
                """)
                conn.commit()
                
                if request.method == 'GET':
                    cur.execute("SELECT config_key, config_value FROM system_config WHERE config_key LIKE 'pool_%' OR config_key LIKE 'wallet_%'")
                    rows = cur.fetchall()
                    config = {row['config_key']: row['config_value'] for row in rows}
                    
                    return jsonify({
                        'success': True,
                        'config': {
                            'minPoolSize': int(config.get('pool_min_size', 10)),
                            'autoFillThreshold': int(config.get('pool_auto_fill_threshold', 5)),
                            'lowBalanceThreshold': float(config.get('wallet_low_balance_threshold', 1.0))
                        }
                    })
                
                else:
                    data = request.get_json() or {}
                    
                    min_pool_size = int(data.get('minPoolSize', 10))
                    auto_fill_threshold = int(data.get('autoFillThreshold', 5))
                    low_balance_threshold = float(data.get('lowBalanceThreshold', 1.0))
                    
                    if min_pool_size < 1 or min_pool_size > 1000:
                        return jsonify({'success': False, 'error': 'Tamaño mínimo del pool debe ser entre 1 y 1000'}), 400
                    if auto_fill_threshold < 0 or auto_fill_threshold > min_pool_size:
                        return jsonify({'success': False, 'error': 'Umbral de auto-rellenado debe ser entre 0 y el tamaño mínimo'}), 400
                    if low_balance_threshold < 0 or low_balance_threshold > 100:
                        return jsonify({'success': False, 'error': 'Umbral de balance bajo debe ser entre 0 y 100'}), 400
                    
                    configs = [
                        ('pool_min_size', str(min_pool_size)),
                        ('pool_auto_fill_threshold', str(auto_fill_threshold)),
                        ('wallet_low_balance_threshold', str(low_balance_threshold))
                    ]
                    
                    for key, value in configs:
                        cur.execute("""
                            INSERT INTO system_config (config_key, config_value, updated_at) 
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (config_key) DO UPDATE SET config_value = %s, updated_at = CURRENT_TIMESTAMP
                        """, (key, value, value))
                    
                    conn.commit()
                    
                    try:
                        from tracking.wallet_pool_service import get_wallet_pool_service
                        wallet_svc = get_wallet_pool_service(db_manager)
                        if wallet_svc:
                            wallet_svc.reload_config()
                    except Exception as reload_err:
                        logger.warning(f"Could not reload wallet pool config: {reload_err}")
                    
                    user_id = getattr(request, 'user_id', '0')
                    log_admin_action(user_id, 'Admin', 'update_pool_config', 'system_config', 
                                   None, f"Updated pool config: {data}")
                    
                    return jsonify({'success': True, 'message': 'Configuración guardada y aplicada'})
    
    except Exception as e:
        logger.error(f"Error with pool config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/wallets/<int:wallet_id>/consolidate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_consolidate_single_wallet(wallet_id):
    """Admin: Consolidar una wallet individual."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        try:
            from tracking.wallet_pool_service import get_wallet_pool_service
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                with db_manager.get_connection() as conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("SELECT * FROM deposit_wallets WHERE id = %s", (wallet_id,))
                        wallet = cur.fetchone()
                        
                        if not wallet:
                            return jsonify({'success': False, 'error': 'Wallet no encontrada'}), 404
                        
                        if wallet.get('consolidated_at'):
                            return jsonify({'success': False, 'error': 'Wallet ya consolidada'}), 400
                
                result = wallet_svc.consolidate_wallet(wallet_id)
                
                if result.get('success'):
                    user_id = getattr(request, 'user_id', '0')
                    log_admin_action(user_id, 'Admin', 'consolidate_single_wallet', 'deposit_wallets', 
                                   str(wallet_id), f"Consolidated wallet {wallet_id}")
                    
                    return jsonify({
                        'success': True,
                        'amount': result.get('amount', 0),
                        'tx_hash': result.get('tx_hash', ''),
                        'message': 'Wallet consolidada exitosamente'
                    })
                else:
                    return jsonify({'success': False, 'error': result.get('error', 'Error desconocido')})
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error consolidating single wallet: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in consolidate single wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ANALYTICS ENDPOINTS ====================

@app.route('/api/admin/analytics/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_users():
    """Admin: Estadísticas de usuarios para analytics."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Usuarios activos hoy
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE
                """)
                active_today = cur.fetchone()['count'] or 0
                
                # Usuarios activos esta semana
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                active_week = cur.fetchone()['count'] or 0
                
                # Usuarios activos este mes
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                active_month = cur.fetchone()['count'] or 0
                
                # Total usuarios registrados
                cur.execute("SELECT COUNT(*) as count FROM users")
                total_users = cur.fetchone()['count'] or 0
                
                # Usuarios nuevos últimos 30 días (gráfico)
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                new_users_chart = [{'date': row['date'].isoformat(), 'count': row['count']} for row in cur.fetchall()]
                
                # Tasa de retención (usuarios que volvieron en los últimos 7 días)
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    AND user_id IN (
                        SELECT DISTINCT user_id FROM security_activity_log
                        WHERE created_at < CURRENT_DATE - INTERVAL '7 days'
                        AND created_at >= CURRENT_DATE - INTERVAL '14 days'
                    )
                """)
                returning_users = cur.fetchone()['count'] or 0
                retention_rate = round((returning_users / max(active_week, 1)) * 100, 1)
                
                users_by_country = [{'country': 'No disponible', 'count': total_users}]
                
                # Usuarios por dispositivo (basado en user_agent)
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN user_agent ILIKE '%android%' THEN 'Android'
                            WHEN user_agent ILIKE '%iphone%' OR user_agent ILIKE '%ipad%' THEN 'iOS'
                            WHEN user_agent ILIKE '%windows%' THEN 'Windows'
                            WHEN user_agent ILIKE '%macintosh%' THEN 'Mac'
                            WHEN user_agent ILIKE '%linux%' THEN 'Linux'
                            ELSE 'Otro'
                        END as device,
                        COUNT(DISTINCT user_id) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY device
                    ORDER BY count DESC
                """)
                users_by_device = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'activeToday': active_today,
                    'activeWeek': active_week,
                    'activeMonth': active_month,
                    'totalUsers': total_users,
                    'newUsersChart': new_users_chart,
                    'retentionRate': retention_rate,
                    'returningUsers': returning_users,
                    'usersByCountry': users_by_country,
                    'usersByDevice': users_by_device
                })
    
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/analytics/usage', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_usage():
    """Admin: Estadísticas de uso de la app."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Secciones más visitadas (basado en activity_type)
                cur.execute("""
                    SELECT activity_type as section, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY activity_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_sections = [dict(row) for row in cur.fetchall()]
                
                # Horarios pico de actividad (24h)
                cur.execute("""
                    SELECT EXTRACT(HOUR FROM created_at)::int as hour, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY hour
                    ORDER BY hour ASC
                """)
                hourly_activity = [{'hour': row['hour'], 'count': row['count']} for row in cur.fetchall()]
                
                # Días más activos
                cur.execute("""
                    SELECT TO_CHAR(created_at, 'Day') as day_name, 
                           EXTRACT(DOW FROM created_at)::int as day_num,
                           COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY day_name, day_num
                    ORDER BY day_num ASC
                """)
                daily_activity = [{'day': row['day_name'].strip(), 'count': row['count']} for row in cur.fetchall()]
                
                # Actividad por día últimos 30 días
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                activity_chart = [{'date': row['date'].isoformat(), 'count': row['count']} for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'topSections': top_sections,
                    'hourlyActivity': hourly_activity,
                    'dailyActivity': daily_activity,
                    'activityChart': activity_chart
                })
    
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/analytics/conversion', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_conversion():
    """Admin: Métricas de conversión."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Total usuarios
                cur.execute("SELECT COUNT(*) as count FROM users")
                total_users = cur.fetchone()['count'] or 0
                
                # Usuarios que compraron B3C
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM b3c_purchases
                    WHERE status = 'completed'
                """)
                users_purchased_b3c = cur.fetchone()['count'] or 0
                
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as count
                        FROM virtual_number_orders
                    """)
                    users_used_vn = cur.fetchone()['count'] or 0
                except psycopg2.errors.UndefinedTable as e:
                    logger.debug(f"virtual_number_orders table not found: {e}")
                    users_used_vn = 0
                
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as count
                        FROM posts
                        WHERE is_hidden = false
                    """)
                    users_published = cur.fetchone()['count'] or 0
                except psycopg2.errors.UndefinedTable as e:
                    logger.debug(f"posts table not found: {e}")
                    users_published = 0
                
                # Usuarios con wallet conectada
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM users
                    WHERE wallet_address IS NOT NULL AND wallet_address != ''
                """)
                users_with_wallet = cur.fetchone()['count'] or 0
                
                # Calcular tasas de conversión
                b3c_rate = round((users_purchased_b3c / max(total_users, 1)) * 100, 1)
                vn_rate = round((users_used_vn / max(total_users, 1)) * 100, 1)
                publish_rate = round((users_published / max(total_users, 1)) * 100, 1)
                wallet_rate = round((users_with_wallet / max(total_users, 1)) * 100, 1)
                
                # Funnel de conversión
                funnel = [
                    {'stage': 'Registrados', 'count': total_users, 'rate': 100},
                    {'stage': 'Wallet conectada', 'count': users_with_wallet, 'rate': wallet_rate},
                    {'stage': 'Compraron B3C', 'count': users_purchased_b3c, 'rate': b3c_rate},
                    {'stage': 'Publicaron contenido', 'count': users_published, 'rate': publish_rate},
                    {'stage': 'Usaron VN', 'count': users_used_vn, 'rate': vn_rate}
                ]
                
                # Ingresos totales
                cur.execute("""
                    SELECT COALESCE(SUM(amount_ton), 0) as total_ton
                    FROM b3c_purchases
                    WHERE status = 'completed'
                """)
                total_revenue_ton = float(cur.fetchone()['total_ton'] or 0)
                
                return jsonify({
                    'success': True,
                    'totalUsers': total_users,
                    'usersPurchasedB3C': users_purchased_b3c,
                    'usersUsedVN': users_used_vn,
                    'usersPublished': users_published,
                    'usersWithWallet': users_with_wallet,
                    'b3cConversionRate': b3c_rate,
                    'vnConversionRate': vn_rate,
                    'publishRate': publish_rate,
                    'walletRate': wallet_rate,
                    'funnel': funnel,
                    'totalRevenueTON': total_revenue_ton
                })
    
    except Exception as e:
        logger.error(f"Error getting conversion analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SUPPORT SECTION API ENDPOINTS ====================

# -------------------- TICKETS API --------------------

@app.route('/api/admin/support/tickets', methods=['GET'])
@require_telegram_auth
@require_owner
def get_support_tickets():
    """Get all support tickets with filters and pagination"""
    try:
        if not db_manager:
            return jsonify({
                'success': True,
                'tickets': [],
                'total': 0,
                'page': 1,
                'per_page': 20,
                'pages': 0,
                'stats': {'new_count': 0, 'in_progress_count': 0, 'resolved_count': 0, 'urgent_count': 0}
            })
        
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if status:
                    where_clauses.append("t.status = %s")
                    params.append(status)
                
                if priority:
                    where_clauses.append("t.priority = %s")
                    params.append(priority)
                
                if search:
                    where_clauses.append("(t.subject ILIKE %s OR u.username ILIKE %s)")
                    params.extend([f'%{search}%', f'%{search}%'])
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                cur.execute(f"""
                    SELECT t.*, u.username, u.first_name, u.last_name,
                           (SELECT COUNT(*) FROM ticket_messages WHERE ticket_id = t.id) as message_count
                    FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE {where_sql}
                    ORDER BY 
                        CASE t.priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            ELSE 4 
                        END,
                        t.created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [per_page, offset])
                tickets = cur.fetchall()
                
                cur.execute(f"""
                    SELECT COUNT(*) as total FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE {where_sql}
                """, params)
                total = cur.fetchone()['total']
                
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE status = 'new') as new_count,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_count,
                        COUNT(*) FILTER (WHERE priority = 'urgent' AND status NOT IN ('closed', 'resolved')) as urgent_count
                    FROM support_tickets
                """)
                stats = cur.fetchone()
                
                return jsonify({
                    'success': True,
                    'tickets': [dict(t) for t in tickets],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'stats': dict(stats)
                })
                
    except Exception as e:
        logger.error(f"Error getting support tickets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def get_ticket_detail(ticket_id):
    """Get single ticket with messages"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT t.*, u.username, u.first_name, u.last_name, u.telegram_id
                    FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE t.id = %s
                """, (ticket_id,))
                ticket = cur.fetchone()
                
                if not ticket:
                    return jsonify({'success': False, 'error': 'Ticket not found'}), 404
                
                cur.execute("""
                    SELECT tm.*, 
                           CASE WHEN tm.is_admin THEN 'Admin' ELSE u.username END as sender_name
                    FROM ticket_messages tm
                    LEFT JOIN users u ON tm.sender_id = u.id
                    WHERE tm.ticket_id = %s
                    ORDER BY tm.created_at ASC
                """, (ticket_id,))
                messages = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'ticket': dict(ticket),
                    'messages': [dict(m) for m in messages]
                })
                
    except Exception as e:
        logger.error(f"Error getting ticket detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_ticket(ticket_id):
    """Update ticket status or priority"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        status = data.get('status')
        priority = data.get('priority')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                updates = []
                params = []
                
                if status:
                    updates.append("status = %s")
                    params.append(status)
                    if status == 'closed':
                        updates.append("closed_at = NOW()")
                
                if priority:
                    updates.append("priority = %s")
                    params.append(priority)
                
                updates.append("updated_at = NOW()")
                params.append(ticket_id)
                
                cur.execute(f"""
                    UPDATE support_tickets
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING *
                """, params)
                ticket = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'ticket': dict(ticket)
                })
                
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>/reply', methods=['POST'])
@require_telegram_auth
@require_owner
def reply_to_ticket(ticket_id):
    """Send reply to ticket"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        message = data.get('message', '').strip()
        attachment_url = data.get('attachment_url')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        admin_id = session.get('admin_id', 0)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO ticket_messages (ticket_id, sender_id, message, is_admin, attachment_url)
                    VALUES (%s, %s, %s, true, %s)
                    RETURNING *
                """, (ticket_id, admin_id, message, attachment_url))
                new_message = cur.fetchone()
                
                cur.execute("""
                    UPDATE support_tickets
                    SET status = CASE WHEN status = 'new' THEN 'in_progress' ELSE status END,
                        updated_at = NOW()
                    WHERE id = %s
                """, (ticket_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': dict(new_message)
                })
                
    except Exception as e:
        logger.error(f"Error replying to ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/support/templates', methods=['GET'])
@require_telegram_auth
@require_owner
def get_response_templates():
    """Get response templates"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM response_templates
                    WHERE is_active = true
                    ORDER BY name ASC
                """)
                templates = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'templates': [dict(t) for t in templates]
                })
                
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/support/templates', methods=['POST'])
@require_telegram_auth
@require_owner
def create_response_template():
    """Create new response template"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        content = data.get('content', '').strip()
        
        if not name or not content:
            return jsonify({'success': False, 'error': 'Name and content are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO response_templates (name, content)
                    VALUES (%s, %s)
                    RETURNING *
                """, (name, content))
                template = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'template': dict(template)
                })
                
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -------------------- FAQ API --------------------

@app.route('/api/admin/faq', methods=['GET'])
@require_telegram_auth
@require_owner
def get_faqs():
    """Get all FAQs with filters"""
    try:
        if not db_manager:
            return jsonify({'success': True, 'faqs': []})
        
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                
                if status == 'published':
                    where_clauses.append("is_published = true")
                elif status == 'draft':
                    where_clauses.append("is_published = false")
                
                if search:
                    where_clauses.append("(question ILIKE %s OR answer ILIKE %s)")
                    params.extend([f'%{search}%', f'%{search}%'])
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                cur.execute(f"""
                    SELECT * FROM faqs
                    WHERE {where_sql}
                    ORDER BY display_order ASC, created_at DESC
                """, params)
                faqs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'faqs': [dict(f) for f in faqs]
                })
                
    except Exception as e:
        logger.error(f"Error getting FAQs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/faq', methods=['POST'])
@require_telegram_auth
@require_owner
def create_faq():
    """Create new FAQ"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'general')
        display_order = data.get('display_order', 0)
        is_published = data.get('is_published', True)
        
        if not question or not answer:
            return jsonify({'success': False, 'error': 'Question and answer are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO faqs (question, answer, category, display_order, is_published)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (question, answer, category, display_order, is_published))
                faq = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'faq': dict(faq)
                })
                
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/faq/<int:faq_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_faq(faq_id):
    """Update FAQ"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'general')
        display_order = data.get('display_order', 0)
        is_published = data.get('is_published', True)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE faqs
                    SET question = %s, answer = %s, category = %s, 
                        display_order = %s, is_published = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                """, (question, answer, category, display_order, is_published, faq_id))
                faq = cur.fetchone()
                conn.commit()
                
                if not faq:
                    return jsonify({'success': False, 'error': 'FAQ not found'}), 404
                
                return jsonify({
                    'success': True,
                    'faq': dict(faq)
                })
                
    except Exception as e:
        logger.error(f"Error updating FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/faq/<int:faq_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def delete_faq(faq_id):
    """Delete FAQ"""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM faqs WHERE id = %s", (faq_id,))
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error deleting FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -------------------- MASS MESSAGES API --------------------

@app.route('/api/admin/messages', methods=['GET'])
@require_telegram_auth
@require_owner
def get_mass_messages():
    """Get mass messages history"""
    try:
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause = ""
                params = []
                
                if status == 'sent':
                    where_clause = "WHERE status = 'sent'"
                elif status == 'scheduled':
                    where_clause = "WHERE status = 'scheduled'"
                elif status == 'draft':
                    where_clause = "WHERE status = 'draft'"
                
                cur.execute(f"""
                    SELECT m.*,
                           (SELECT COUNT(*) FROM mass_message_recipients WHERE message_id = m.id) as recipient_count,
                           (SELECT COUNT(*) FROM mass_message_recipients WHERE message_id = m.id AND is_delivered = true) as delivered_count
                    FROM mass_messages m
                    {where_clause}
                    ORDER BY m.created_at DESC
                    LIMIT %s OFFSET %s
                """, [per_page, offset])
                messages = cur.fetchall()
                
                cur.execute(f"SELECT COUNT(*) as total FROM mass_messages {where_clause}")
                total = cur.fetchone()['total']
                
                return jsonify({
                    'success': True,
                    'messages': [dict(m) for m in messages],
                    'total': total,
                    'page': page,
                    'per_page': per_page
                })
                
    except Exception as e:
        logger.error(f"Error getting mass messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/messages', methods=['POST'])
@require_telegram_auth
@require_owner
def send_mass_message():
    """Create and send mass message"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        recipient_type = data.get('recipient_type', 'all')
        specific_users = data.get('specific_users', '')
        send_type = data.get('send_type', 'now')
        scheduled_at = data.get('scheduled_at')
        msg_type = data.get('msg_type', 'info')
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
        
        admin_id = session.get('admin_id', 0)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                status = 'scheduled' if send_type == 'scheduled' else 'sent'
                sent_at = None if send_type == 'scheduled' else 'NOW()'
                
                cur.execute(f"""
                    INSERT INTO mass_messages (title, content, message_type, recipient_filter, 
                                               status, scheduled_at, sent_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, {'NOW()' if send_type == 'now' else 'NULL'}, %s)
                    RETURNING *
                """, (title, content, msg_type, recipient_type, status, 
                      scheduled_at if send_type == 'scheduled' else None, admin_id))
                message = cur.fetchone()
                message_id = message['id']
                
                if send_type == 'now':
                    user_ids = []
                    if recipient_type == 'all':
                        cur.execute("SELECT id FROM users WHERE is_banned = false")
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'active':
                        cur.execute("""
                            SELECT id FROM users 
                            WHERE is_banned = false AND last_active > NOW() - INTERVAL '7 days'
                        """)
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'premium':
                        cur.execute("""
                            SELECT id FROM users 
                            WHERE is_banned = false AND is_premium = true
                        """)
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'specific' and specific_users:
                        specific_ids = [int(x.strip()) for x in specific_users.split(',') if x.strip().isdigit()]
                        if specific_ids:
                            cur.execute("""
                                SELECT id FROM users WHERE id = ANY(%s) AND is_banned = false
                            """, (specific_ids,))
                            user_ids = [row['id'] for row in cur.fetchall()]
                    
                    for user_id in user_ids:
                        cur.execute("""
                            INSERT INTO mass_message_recipients (message_id, user_id, is_delivered)
                            VALUES (%s, %s, true)
                        """, (message_id, user_id))
                        
                        cur.execute("""
                            INSERT INTO user_notifications (user_id, title, message, notification_type, is_read)
                            VALUES (%s, %s, %s, %s, false)
                        """, (user_id, title, content, msg_type))
                    
                    cur.execute("""
                        UPDATE mass_messages SET recipients_count = %s WHERE id = %s
                    """, (len(user_ids), message_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': dict(message),
                    'recipients_count': len(user_ids) if send_type == 'now' else 0
                })
                
    except Exception as e:
        logger.error(f"Error sending mass message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/messages/scheduled', methods=['GET'])
@require_telegram_auth
@require_owner
def get_scheduled_messages():
    """Get scheduled messages"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM mass_messages
                    WHERE status = 'scheduled' AND scheduled_at > NOW()
                    ORDER BY scheduled_at ASC
                """)
                messages = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'messages': [dict(m) for m in messages]
                })
                
    except Exception as e:
        logger.error(f"Error getting scheduled messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/messages/<int:message_id>/cancel', methods=['POST'])
@require_telegram_auth
@require_owner
def cancel_scheduled_message(message_id):
    """Cancel scheduled message"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE mass_messages
                    SET status = 'cancelled'
                    WHERE id = %s AND status = 'scheduled'
                    RETURNING *
                """, (message_id,))
                message = cur.fetchone()
                conn.commit()
                
                if not message:
                    return jsonify({'success': False, 'error': 'Message not found or already sent'}), 404
                
                return jsonify({
                    'success': True,
                    'message': dict(message)
                })
                
    except Exception as e:
        logger.error(f"Error cancelling message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -------------------- USER FAQ API (Public) --------------------

@app.route('/api/faq', methods=['GET'])
def get_public_faqs():
    """Get published FAQs for users"""
    try:
        category = request.args.get('category', '')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause = "is_published = true"
                params = []
                
                if category:
                    where_clause += " AND category = %s"
                    params.append(category)
                
                cur.execute(f"""
                    SELECT id, question, answer, category FROM faqs
                    WHERE {where_clause}
                    ORDER BY display_order ASC
                """, params)
                faqs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'faqs': [dict(f) for f in faqs]
                })
                
    except Exception as e:
        logger.error(f"Error getting public FAQs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -------------------- USER NOTIFICATIONS API --------------------

@app.route('/api/user/notifications', methods=['GET'])
@require_telegram_auth
def get_user_notifications():
    """Get notifications for logged in user"""
    try:
        user_id = request.telegram_user.get('id')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_id,))
                notifications = cur.fetchall()
                
                cur.execute("""
                    SELECT COUNT(*) as unread FROM user_notifications
                    WHERE user_id = %s AND is_read = false
                """, (user_id,))
                unread_count = cur.fetchone()['unread']
                
                return jsonify({
                    'success': True,
                    'notifications': [dict(n) for n in notifications],
                    'unread_count': unread_count
                })
                
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/notifications/read', methods=['POST'])
@require_telegram_auth
def mark_support_notifications_read():
    """Mark support notifications as read"""
    try:
        user_id = request.telegram_user.get('id')
        data = request.json
        notification_ids = data.get('notification_ids', [])
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if notification_ids:
                    cur.execute("""
                        UPDATE user_notifications
                        SET is_read = true
                        WHERE user_id = %s AND id = ANY(%s)
                    """, (user_id, notification_ids))
                else:
                    cur.execute("""
                        UPDATE user_notifications
                        SET is_read = true
                        WHERE user_id = %s
                    """, (user_id,))
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error marking notifications read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== END SUPPORT SECTION ====================




deposit_scheduler = None

def init_deposit_scheduler():
    """Inicializar el scheduler de depósitos en background."""
    global deposit_scheduler
    if db_manager:
        try:
            from tracking.deposit_scheduler import start_deposit_scheduler
            deposit_scheduler = start_deposit_scheduler(db_manager)
            logger.info("Deposit scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start deposit scheduler: {e}")

init_deposit_scheduler()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
