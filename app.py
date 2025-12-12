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

from routes import auth_bp, blockchain_bp, admin_bp, user_bp, tracking_bp, bots_bp, vn_bp

app.register_blueprint(auth_bp)
app.register_blueprint(blockchain_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(tracking_bp)
app.register_blueprint(bots_bp)
app.register_blueprint(vn_bp)

logger.info("Blueprints registered: auth, blockchain, admin, user, tracking, bots, vn")

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

from tracking import services as shared_services

try:
    db_manager = DatabaseManager()
    logger.info("Database connection established")
    shared_services.set_db_manager(db_manager)
    security_manager = SecurityManager(db_manager)
    security_manager.initialize_tables()
    logger.info("Security manager initialized")
    shared_services.set_security_manager(security_manager)
    db_manager.initialize_virtual_numbers_tables()
    logger.info("Virtual numbers tables initialized")
    db_manager.initialize_payments_tables()
    logger.info("Payments tables initialized")
    db_manager.initialize_b3c_tables()
    logger.info("B3C tables initialized")
    vn_manager = VirtualNumbersManager(db_manager)
    logger.info("Virtual numbers manager initialized")
    shared_services.set_vn_manager(vn_manager)
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
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-CH-UA-Mobile': '?1',
            'Sec-CH-UA-Platform': '"iOS"',
            'Sec-CH-UA': '"Safari";v="17", "Mobile";v="17"',
        }
        
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        content_type = resp.headers.get('Content-Type', 'text/html')
        
        if 'text/html' in content_type:
            content = resp.text
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            import re
            content = re.sub(r'<meta[^>]*name=["\']viewport["\'][^>]*>', '', content, flags=re.IGNORECASE)
            
            base_tag = f'<base href="{base_url}/">'
            viewport_tag = '<meta name="viewport" content="width=375, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
            mobile_style = '<style>html,body{max-width:375px!important;overflow-x:hidden!important;width:375px!important;}</style>'
            inject_tags = f'{base_tag}{viewport_tag}{mobile_style}'
            if '<head>' in content:
                content = content.replace('<head>', f'<head>{inject_tags}', 1)
            elif '<HEAD>' in content:
                content = content.replace('<HEAD>', f'<HEAD>{inject_tags}', 1)
            else:
                content = inject_tags + content
            
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


@app.route('/api/mobile-screenshot')
def mobile_screenshot():
    """Captura screenshot de página web renderizada como dispositivo móvil usando Playwright."""
    url = request.args.get('url', '')
    session_id = request.args.get('session', 'default')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL requerida'}), 400
    
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc or '.' not in parsed.netloc:
            return jsonify({'success': False, 'error': 'URL inválida'}), 400
        
        from playwright_service import capture_mobile_screenshot
        result = capture_mobile_screenshot(url, session_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Mobile screenshot error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS PARA NAVEGADOR INTERACTIVO (noVNC)
# ============================================================

@app.route('/api/interactive-browser/create', methods=['POST'])
def create_interactive_browser():
    """Crear una nueva sesión de navegador interactivo con noVNC."""
    try:
        data = request.get_json() or {}
        url = data.get('url', 'https://www.google.com')
        
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        from novnc_service import create_interactive_session
        result = create_interactive_session(url)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Interactive browser create error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/interactive-browser/stop', methods=['POST'])
def stop_interactive_browser():
    """Detener una sesión de navegador interactivo."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id requerido'}), 400
        
        from novnc_service import stop_interactive_session
        success = stop_interactive_session(session_id)
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Interactive browser stop error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/interactive-browser/session/<session_id>')
def get_interactive_browser_session(session_id):
    """Obtener información de una sesión de navegador."""
    try:
        from novnc_service import get_interactive_session
        session = get_interactive_session(session_id)
        
        if session:
            return jsonify({'success': True, **session})
        else:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
    except Exception as e:
        logger.error(f"Interactive browser session error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/interactive-browser/list')
def list_interactive_browsers():
    """Listar todas las sesiones de navegador activas."""
    try:
        from novnc_service import list_interactive_sessions
        sessions = list_interactive_sessions()
        return jsonify({'success': True, 'sessions': sessions})
        
    except Exception as e:
        logger.error(f"Interactive browser list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS PARA 2FA (Two-Factor Authentication)
# ============================================================

# MIGRADO A routes/auth_routes.py: /api/demo/2fa/verify, /api/demo/2fa/logout


# ELIMINADO: /api/admin/2fa/verify POST - Migrado a admin_bp (admin_routes.py línea 5871)


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


# MIGRADO A routes/auth_routes.py: /api/2fa/status, /api/2fa/setup, /api/2fa/verify, /api/2fa/session, /api/2fa/refresh, /api/2fa/disable, /api/validate


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


# ============================================================
# ENDPOINTS MIGRADOS A routes/admin_routes.py (9-10 Diciembre 2025)
# Ver archivo routes/admin_routes.py para la implementacion activa
# - /api/admin/dashboard/*, /api/admin/users/*, /api/admin/stats/*
# - /api/admin/security/*, /api/admin/users/<id>/* (risk-score, etc)
# - /api/admin/fraud/*, /api/admin/sessions/*, /api/admin/stats/*
# - /api/admin/financial/*, /api/admin/content/*, /api/admin/hashtags/*
# - /api/admin/stories/*, /api/admin/vn/*, /api/admin/config/*
# ============================================================


# NOTA: Los siguientes endpoints fueron eliminados porque ya existen en admin_routes.py:
# - /api/admin/users/<id>/balance, note, logout, notify, risk-score, related-accounts
# - /api/admin/anomalies, fraud/*, realtime/online, sessions/*
# - /api/admin/stats/*, security/*, users, exports, financial/*
# - /api/admin/content/*, hashtags/*, stories/*



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


# ELIMINADO: /api/admin/products GET/POST/DELETE - Migrado a admin_bp
# ELIMINADO: /api/admin/transactions GET - Migrado a admin_bp
# ELIMINADO: /api/admin/transactions/<tx_id> GET - Migrado a admin_bp
# ELIMINADO: /api/admin/purchases GET - Migrado a admin_bp
# ELIMINADO: /api/admin/purchases/<purchase_id> GET - Migrado a admin_bp
# ELIMINADO: /api/admin/purchases/<purchase_id>/credit POST - Migrado a admin_bp
# ELIMINADO: /api/admin/activity GET - Migrado a admin_bp
# ELIMINADO: /api/admin/lockouts GET - Migrado a admin_bp
# ELIMINADO: /api/admin/unlock-user POST - Migrado a admin_bp
# ELIMINADO: /api/admin/settings GET/POST - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications GET - Migrado a admin_bp (duplicado interno también)
# ELIMINADO: /api/admin/notifications/mark-read POST - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications/delete POST - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications/<id>/read POST - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications/read-all POST - Migrado a admin_bp
# ELIMINADO: /api/admin/system-status GET - Migrado a admin_bp

# Ver routes/admin_routes.py para estos endpoints


# Bloque duplicado eliminado - todos migrados a routes/admin_routes.py


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


# ELIMINADO: /api/admin/system-status - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications GET - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications/<id>/read - Migrado a admin_bp
# ELIMINADO: /api/admin/notifications/read-all - Migrado a admin_bp


# ELIMINADO: /api/admin/risk-scores GET - Migrado a admin_bp
# ELIMINADO: /api/admin/risk-scores/adjust POST - Migrado a admin_bp
# ELIMINADO: /api/admin/related-accounts GET - Migrado a admin_bp
# ELIMINADO: /api/admin/related-accounts/scan POST - Migrado a admin_bp
# ELIMINADO: /api/admin/anomalies GET - Migrado a admin_bp
# ELIMINADO: /api/admin/tags GET/POST - Migrado a admin_bp
# ELIMINADO: /api/admin/tags/<tag_id>/users GET - Migrado a admin_bp
# ELIMINADO: /api/admin/users/<user_id>/tags POST - Migrado a admin_bp


@app.route('/api/admin/verifications', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_verifications():
    """Admin: Obtener cola de verificaciones."""
    try:
        verifications = []
        return jsonify({'success': True, 'verifications': verifications})
        
    except Exception as e:
        logger.error(f"Error getting verifications: {e}")
        return jsonify({'success': False, 'error': str(e), 'verifications': []}), 500


@app.route('/api/admin/shadow-sessions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_shadow_sessions():
    """Admin: Obtener historial de sesiones shadow."""
    try:
        sessions = []
        return jsonify({'success': True, 'sessions': sessions})
        
    except Exception as e:
        logger.error(f"Error getting shadow sessions: {e}")
        return jsonify({'success': False, 'error': str(e), 'sessions': []}), 500


@app.route('/api/admin/shadow-sessions/start', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_start_shadow_session():
    """Admin: Iniciar sesion shadow para un usuario."""
    try:
        data = request.get_json() or {}
        telegram_id = data.get('telegramId')
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Usuario requerido'}), 400
        
        session_url = f"/?shadow_user={telegram_id}"
        
        return jsonify({
            'success': True,
            'sessionUrl': session_url
        })
        
    except Exception as e:
        logger.error(f"Error starting shadow session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/marketplace', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_marketplace():
    """Admin: Obtener datos del marketplace."""
    try:
        listings = []
        sales = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT l.id, l.title, l.price, l.currency, l.status,
                           l.created_at as "createdAt", u.username as "sellerUsername"
                    FROM marketplace_listings l
                    LEFT JOIN users u ON l.seller_id = u.telegram_id
                    ORDER BY l.created_at DESC
                    LIMIT 100
                """)
                listings = [dict(l) for l in cur.fetchall()]
                
                for listing in listings:
                    if listing.get('createdAt'):
                        listing['createdAt'] = listing['createdAt'].isoformat()
                
        return jsonify({
            'success': True,
            'listings': listings,
            'sales': sales
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace: {e}")
        return jsonify({'success': False, 'error': str(e), 'listings': [], 'sales': []}), 500


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
# MIGRADO A routes/user_routes.py - 10 Diciembre 2025
# (Excepto /api/publications/create que requiere cloudinary y encryption)
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



# ELIMINADO: /api/admin/reports GET/PUT - Migrado a admin_bp (admin_routes.py líneas 5959, 5985)


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


# ELIMINADO: /api/admin/config GET/POST - Migrado a admin_bp (admin_routes.py líneas 2740, 2771)


# ELIMINADO: /api/admin/blocked-ips GET/POST/DELETE - Migrado a admin_bp
# ELIMINADO: /api/admin/wallet-pool/stats - Migrado a admin_bp
# ELIMINADO: /api/admin/secrets-status - Migrado a admin_bp



# ==================== ENDPOINTS MIGRADOS ====================
# Los siguientes endpoints han sido migrados a rutas modulares:
# 
# MIGRADO A routes/admin_routes.py - 10 Diciembre 2025:
# - /api/admin/wallets/hot (GET)
# - /api/admin/wallets/deposits (GET)
# - /api/admin/wallets/fill-pool (POST)
# - /api/admin/wallets/consolidate (POST)
# - /api/admin/blockchain/history (GET)
# - /api/admin/wallets/pool-config (GET, POST)
# - /api/admin/wallets/<id>/consolidate (POST)
# - /api/admin/analytics/users (GET)
# - /api/admin/analytics/usage (GET)
# - /api/admin/analytics/conversion (GET)
# - /api/admin/support/tickets (GET)
# - /api/admin/support/tickets/<id> (GET, PUT)
# - /api/admin/support/tickets/<id>/reply (POST)
# - /api/admin/support/templates (GET, POST)
# - /api/admin/faq (GET, POST)
# - /api/admin/faq/<id> (PUT, DELETE)
# - /api/admin/messages (GET, POST)
# - /api/admin/messages/scheduled (GET)
# - /api/admin/messages/<id>/cancel (POST)
#
# MIGRADO A routes/user_routes.py - 10 Diciembre 2025:
# - /api/faq (GET) - FAQ público
# ==================== FIN ENDPOINTS MIGRADOS ====================







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
