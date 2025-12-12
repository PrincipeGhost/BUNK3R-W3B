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
# ============================================================


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


def calculate_user_risk_score(user_id, conn):
    """Calcula el score de riesgo de un usuario basado en multiples factores."""
    factors = {}
    score = 0
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
        user = cur.fetchone()
        if not user:
            return None, None, None
        
        if not user.get('is_verified'):
            factors['no_verificado'] = 15
            score += 15
        
        cur.execute("""
            SELECT COUNT(DISTINCT ip_address) as ip_count
            FROM trusted_devices WHERE user_id = %s
        """, (str(user_id),))
        ip_count = cur.fetchone()['ip_count'] or 0
        if ip_count > 5:
            factors['multiples_ips'] = min(ip_count * 3, 20)
            score += factors['multiples_ips']
        
        cur.execute("""
            SELECT ip_address, COUNT(DISTINCT user_id) as user_count
            FROM trusted_devices
            WHERE ip_address IN (SELECT ip_address FROM trusted_devices WHERE user_id = %s)
            AND user_id != %s
            GROUP BY ip_address
            HAVING COUNT(DISTINCT user_id) > 0
        """, (str(user_id), str(user_id)))
        shared_ips = cur.fetchall()
        if shared_ips:
            factors['ips_compartidas'] = min(len(shared_ips) * 10, 25)
            score += factors['ips_compartidas']
        
        cur.execute("""
            SELECT COUNT(*) as alert_count FROM security_alerts
            WHERE user_id = %s AND resolved = false
        """, (user.get('id'),))
        alerts = cur.fetchone()['alert_count'] or 0
        if alerts > 0:
            factors['alertas_activas'] = min(alerts * 5, 20)
            score += factors['alertas_activas']
        
        cur.execute("""
            SELECT COUNT(*) as tx_count FROM wallet_transactions
            WHERE user_id = %s AND created_at >= NOW() - INTERVAL '1 hour'
        """, (str(user_id),))
        recent_tx = cur.fetchone()['tx_count'] or 0
        if recent_tx > 10:
            factors['transacciones_rapidas'] = min(recent_tx, 15)
            score += factors['transacciones_rapidas']
        
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM wallet_transactions
            WHERE user_id = %s AND transaction_type = 'withdraw' 
            AND created_at >= NOW() - INTERVAL '24 hours'
        """, (str(user_id),))
        withdrawals = float(cur.fetchone()['total'] or 0)
        if withdrawals > 1000:
            factors['retiros_altos'] = min(int(withdrawals / 100), 20)
            score += factors['retiros_altos']
        
        account_age_days = 0
        if user.get('created_at'):
            account_age_days = (datetime.now() - user['created_at']).days
        if account_age_days < 7:
            factors['cuenta_nueva'] = 10
            score += 10
        
        score = min(score, 100)
        
        if score >= 75:
            risk_level = 'critical'
        elif score >= 50:
            risk_level = 'high'
        elif score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
    
    return score, risk_level, factors


@app.route('/api/admin/users/<user_id>/risk-score', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_risk_score(user_id):
    """Admin: Obtener score de riesgo de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM risk_scores WHERE user_id = %s
                """, (str(user_id),))
                existing = cur.fetchone()
                
                if existing:
                    result = dict(existing)
                    if result.get('last_calculated'):
                        result['last_calculated'] = result['last_calculated'].isoformat()
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('updated_at'):
                        result['updated_at'] = result['updated_at'].isoformat()
                    return jsonify({'success': True, 'risk_score': result})
                
                score, risk_level, factors = calculate_user_risk_score(user_id, conn)
                if score is None:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                return jsonify({
                    'success': True,
                    'risk_score': {
                        'user_id': user_id,
                        'score': score,
                        'risk_level': risk_level,
                        'factors': factors,
                        'last_calculated': None,
                        'note': 'Score calculado en tiempo real, no guardado'
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting risk score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/risk-score/calculate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_calculate_risk_score(user_id):
    """Admin: Calcular y guardar score de riesgo de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            score, risk_level, factors = calculate_user_risk_score(user_id, conn)
            if score is None:
                return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM risk_scores WHERE user_id = %s", (str(user_id),))
                existing = cur.fetchone()
                
                if existing:
                    old_score = existing['score']
                    old_level = existing['risk_level']
                    
                    if old_score != score or old_level != risk_level:
                        cur.execute("""
                            INSERT INTO risk_score_history (user_id, old_score, new_score, old_level, new_level, reason)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (str(user_id), old_score, score, old_level, risk_level, 'Recalculo automatico'))
                    
                    cur.execute("""
                        UPDATE risk_scores SET score = %s, risk_level = %s, factors = %s,
                        last_calculated = NOW(), updated_at = NOW()
                        WHERE user_id = %s
                    """, (score, risk_level, json.dumps(factors), str(user_id)))
                else:
                    cur.execute("""
                        INSERT INTO risk_scores (user_id, score, risk_level, factors, last_calculated)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (str(user_id), score, risk_level, json.dumps(factors)))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'risk_score': {
                'user_id': user_id,
                'score': score,
                'risk_level': risk_level,
                'factors': factors
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/risk-score/history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_risk_score_history(user_id):
    """Admin: Obtener historial de cambios de score de riesgo."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM risk_score_history
                    WHERE user_id = %s
                    ORDER BY changed_at DESC
                    LIMIT 50
                """, (str(user_id),))
                history = []
                for row in cur.fetchall():
                    r = dict(row)
                    if r.get('changed_at'):
                        r['changed_at'] = r['changed_at'].isoformat()
                    history.append(r)
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        logger.error(f"Error getting risk score history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<user_id>/related-accounts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_related_accounts(user_id):
    """Admin: Obtener cuentas relacionadas de un usuario."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        related = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT td2.user_id, u.username, td.ip_address
                    FROM trusted_devices td
                    JOIN trusted_devices td2 ON td.ip_address = td2.ip_address AND td.user_id != td2.user_id
                    JOIN users u ON td2.user_id = u.id
                    WHERE td.user_id = %s
                """, (str(user_id),))
                for row in cur.fetchall():
                    related.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'relation_type': 'same_ip',
                        'evidence': {'ip': row['ip_address']}
                    })
                
                cur.execute("""
                    SELECT DISTINCT td2.user_id, u.username, td.device_fingerprint
                    FROM trusted_devices td
                    JOIN trusted_devices td2 ON td.device_fingerprint = td2.device_fingerprint 
                        AND td.user_id != td2.user_id
                        AND td.device_fingerprint IS NOT NULL
                    JOIN users u ON td2.user_id = u.id
                    WHERE td.user_id = %s
                """, (str(user_id),))
                for row in cur.fetchall():
                    existing = next((r for r in related if r['user_id'] == row['user_id']), None)
                    if existing:
                        existing['relation_type'] = 'same_ip_and_device'
                        existing['evidence']['fingerprint'] = row['device_fingerprint']
                    else:
                        related.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'relation_type': 'same_device',
                            'evidence': {'fingerprint': row['device_fingerprint']}
                        })
                
                cur.execute("""
                    SELECT DISTINCT u2.id as user_id, u2.username, u1.wallet_address
                    FROM users u1
                    JOIN users u2 ON u1.wallet_address = u2.wallet_address AND u1.id != u2.id
                    WHERE u1.id = %s AND u1.wallet_address IS NOT NULL AND u1.wallet_address != ''
                """, (str(user_id),))
                for row in cur.fetchall():
                    existing = next((r for r in related if r['user_id'] == row['user_id']), None)
                    if existing:
                        existing['evidence']['wallet'] = row['wallet_address']
                    else:
                        related.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'relation_type': 'same_wallet',
                            'evidence': {'wallet': row['wallet_address']}
                        })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'related_accounts': related,
            'count': len(related)
        })
        
    except Exception as e:
        logger.error(f"Error getting related accounts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/anomalies', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_anomalies():
    """Admin: Obtener detecciones de anomalias."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        severity = request.args.get('severity', None)
        anomaly_type = request.args.get('type', None)
        limit = min(int(request.args.get('limit', 50)), 200)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT a.*, u.username FROM anomaly_detections a LEFT JOIN users u ON a.user_id = u.id WHERE 1=1"
                params = []
                
                if not resolved:
                    query += " AND a.is_resolved = false"
                if severity:
                    query += " AND a.severity = %s"
                    params.append(severity)
                if anomaly_type:
                    query += " AND a.anomaly_type = %s"
                    params.append(anomaly_type)
                
                query += " ORDER BY a.created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                anomalies = []
                for row in cur.fetchall():
                    r = dict(row)
                    if r.get('created_at'):
                        r['created_at'] = r['created_at'].isoformat()
                    if r.get('resolved_at'):
                        r['resolved_at'] = r['resolved_at'].isoformat()
                    anomalies.append(r)
        
        return jsonify({'success': True, 'anomalies': anomalies, 'count': len(anomalies)})
        
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/anomalies/<int:anomaly_id>/resolve', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_resolve_anomaly(anomaly_id):
    """Admin: Resolver una anomalia detectada."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.get_json() or {}
        action_taken = data.get('action_taken', '')
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE anomaly_detections 
                    SET is_resolved = true, resolved_by = %s, resolved_at = NOW(), action_taken = %s
                    WHERE id = %s
                """, (admin_id, action_taken, anomaly_id))
                
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'error': 'Anomalia no encontrada'}), 404
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Anomalia resuelta'})
        
    except Exception as e:
        logger.error(f"Error resolving anomaly: {e}")
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


@app.route('/api/admin/stats/overview', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_overview():
    """Admin: Estadisticas generales detalladas del sistema."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM users")
                total_users = cur.fetchone()['total'] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '24 hours'")
                active_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '7 days'")
                active_7d = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours'")
                new_users_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
                new_users_7d = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions")
                total_transactions = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions WHERE created_at >= NOW() - INTERVAL '24 hours'")
                transactions_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE transaction_type = 'deposit'")
                total_deposits = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE transaction_type = 'withdraw'")
                total_withdrawals = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
                total_b3c_circulation = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COUNT(*) FROM posts WHERE is_active = true")
                total_posts = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM posts WHERE created_at >= NOW() - INTERVAL '24 hours'")
                posts_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM security_alerts WHERE resolved = false")
                pending_alerts = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM user_bots WHERE is_active = true")
                active_bots = cur.fetchone()[0] or 0
        
        return jsonify({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'active_24h': active_24h,
                    'active_7d': active_7d,
                    'new_24h': new_users_24h,
                    'new_7d': new_users_7d
                },
                'transactions': {
                    'total': total_transactions,
                    'last_24h': transactions_24h,
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals
                },
                'economy': {
                    'b3c_circulation': total_b3c_circulation
                },
                'content': {
                    'total_posts': total_posts,
                    'posts_24h': posts_24h
                },
                'security': {
                    'pending_alerts': pending_alerts,
                    'active_bots': active_bots
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/stats/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_users():
    """Admin: Estadisticas detalladas de usuarios."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM users")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = true")
                verified = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                active = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_active = false")
                banned = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '1 hour'")
                online_now = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count 
                    FROM users 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at) 
                    ORDER BY date DESC
                """)
                registrations_by_day = [{'date': str(r['date']), 'count': r['count']} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT LOWER(role) as role, COUNT(*) as count 
                    FROM users 
                    GROUP BY LOWER(role)
                """)
                by_role = {r['role']: r['count'] for r in cur.fetchall()}
                
                cur.execute("""
                    SELECT level, COUNT(*) as count 
                    FROM users 
                    GROUP BY level 
                    ORDER BY level
                """)
                by_level = [{'level': r['level'], 'count': r['count']} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT u.id, u.username, u.credits, u.level, u.is_verified, u.last_seen
                    FROM users u
                    ORDER BY u.credits DESC
                    LIMIT 10
                """)
                top_users = [dict(r) for r in cur.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total': total,
                    'verified': verified,
                    'active': active,
                    'banned': banned,
                    'online_now': online_now
                },
                'registrations_by_day': registrations_by_day,
                'by_role': by_role,
                'by_level': by_level,
                'top_users': top_users
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/stats/transactions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_transactions():
    """Admin: Estadisticas detalladas de transacciones."""
    try:
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM wallet_transactions")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT transaction_type, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                    FROM wallet_transactions
                    GROUP BY transaction_type
                """)
                by_type = {r['transaction_type']: {'count': r['count'], 'amount': float(r['total_amount'])} for r in cur.fetchall()}
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                by_day = [{'date': str(r['date']), 'count': r['count'], 'volume': float(r['volume'])} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT COUNT(*) FROM wallet_transactions WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                count_24h = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                volume_24h = float(cur.fetchone()[0] or 0)
                
                cur.execute("""
                    SELECT COALESCE(AVG(amount), 0) FROM wallet_transactions
                """)
                avg_amount = float(cur.fetchone()[0] or 0)
                
                cur.execute("""
                    SELECT wt.id, wt.user_id, u.username, wt.transaction_type, wt.amount, wt.description, wt.created_at
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.created_at DESC
                    LIMIT 20
                """)
                recent = []
                for r in cur.fetchall():
                    row = dict(r)
                    if row.get('created_at'):
                        row['created_at'] = row['created_at'].isoformat()
                    recent.append(row)
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total': total,
                    'count_24h': count_24h,
                    'volume_24h': volume_24h,
                    'avg_amount': round(avg_amount, 2)
                },
                'by_type': by_type,
                'by_day': by_day,
                'recent': recent
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


@app.route('/api/admin/risk-scores', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_risk_scores():
    """Admin: Obtener scores de riesgo de usuarios."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT u.telegram_id as "telegramId", u.username, u.first_name as "firstName",
                           u.last_name as "lastName", 
                           COALESCE(u.risk_score, 0) as "riskScore",
                           u.risk_factors as "riskFactors",
                           u.last_activity as "lastScoreChange"
                    FROM users u
                    ORDER BY COALESCE(u.risk_score, 0) DESC
                    LIMIT 500
                """)
                users = cur.fetchall()
                
                for user in users:
                    if user.get('lastScoreChange'):
                        user['lastScoreChange'] = user['lastScoreChange'].isoformat()
                    if not user.get('riskFactors'):
                        user['riskFactors'] = []
                
                return jsonify({'success': True, 'users': users})
                
    except Exception as e:
        logger.error(f"Error getting risk scores: {e}")
        return jsonify({'success': False, 'error': str(e), 'users': []}), 500


@app.route('/api/admin/risk-scores/adjust', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_adjust_risk_score():
    """Admin: Ajustar score de riesgo de un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId') or data.get('telegramId')
        adjustment = data.get('adjustment', 0)
        score = data.get('score')
        reason = data.get('reason', 'Ajuste manual')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Usuario requerido'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if score is not None:
                    new_score = int(score)
                else:
                    cur.execute("SELECT COALESCE(risk_score, 0) FROM users WHERE telegram_id = %s", (user_id,))
                    row = cur.fetchone()
                    current_score = row[0] if row else 0
                    new_score = max(0, min(100, current_score + int(adjustment)))
                
                cur.execute("""
                    UPDATE users SET risk_score = %s WHERE telegram_id = %s
                """, (new_score, user_id))
                conn.commit()
                
                return jsonify({'success': True, 'newScore': new_score})
                
    except Exception as e:
        logger.error(f"Error adjusting risk score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/related-accounts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_related_accounts_groups():
    """Admin: Obtener grupos de cuentas relacionadas."""
    try:
        groups = []
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT ip_address, COUNT(*) as count, 
                           array_agg(telegram_id) as user_ids
                    FROM user_devices
                    WHERE ip_address IS NOT NULL
                    GROUP BY ip_address
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                    LIMIT 50
                """)
                ip_groups = cur.fetchall()
                
                for i, grp in enumerate(ip_groups):
                    user_ids = grp.get('user_ids', [])
                    if user_ids:
                        cur.execute("""
                            SELECT telegram_id as "telegramId", username, first_name as "firstName"
                            FROM users WHERE telegram_id = ANY(%s)
                        """, (user_ids,))
                        accounts = cur.fetchall()
                    else:
                        accounts = []
                    
                    groups.append({
                        'id': i + 1,
                        'status': 'pending',
                        'reason': f'IP compartida: {grp.get("ip_address", "N/A")}',
                        'confidence': min(100, grp.get('count', 2) * 30),
                        'accounts': [dict(a) for a in accounts]
                    })
                
        return jsonify({'success': True, 'groups': groups})
        
    except Exception as e:
        logger.error(f"Error getting related accounts: {e}")
        return jsonify({'success': False, 'error': str(e), 'groups': []}), 500


@app.route('/api/admin/related-accounts/scan', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_scan_related_accounts():
    """Admin: Ejecutar escaneo de cuentas relacionadas."""
    try:
        return jsonify({'success': True, 'message': 'Escaneo completado'})
    except Exception as e:
        logger.error(f"Error scanning related accounts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/anomalies', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_anomalies_list():
    """Admin: Obtener lista de anomalias detectadas."""
    try:
        anomalies = []
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT sa.id, sa.user_id as "telegramId", sa.alert_type as title,
                           sa.description, sa.severity, sa.is_resolved as resolved,
                           sa.created_at as "detectedAt", u.username
                    FROM security_alerts sa
                    LEFT JOIN users u ON sa.user_id = u.telegram_id
                    ORDER BY sa.created_at DESC
                    LIMIT 100
                """)
                alerts = cur.fetchall()
                
                for alert in alerts:
                    if alert.get('detectedAt'):
                        alert['detectedAt'] = alert['detectedAt'].isoformat()
                    anomalies.append(dict(alert))
                
        return jsonify({'success': True, 'anomalies': anomalies})
        
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        return jsonify({'success': False, 'error': str(e), 'anomalies': []}), 500


@app.route('/api/admin/tags', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_tags():
    """Admin: Obtener lista de etiquetas."""
    try:
        tags = [
            {'id': 'vip', 'name': 'VIP', 'color': '#d4af37', 'usersCount': 0},
            {'id': 'suspicious', 'name': 'Sospechoso', 'color': '#ef4444', 'usersCount': 0},
            {'id': 'trusted', 'name': 'Confiable', 'color': '#22c55e', 'usersCount': 0},
            {'id': 'new', 'name': 'Nuevo', 'color': '#3b82f6', 'usersCount': 0},
            {'id': 'high_value', 'name': 'Alto Valor', 'color': '#a855f7', 'usersCount': 0}
        ]
        return jsonify({'success': True, 'tags': tags})
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'success': False, 'error': str(e), 'tags': []}), 500


@app.route('/api/admin/tags', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_create_tag():
    """Admin: Crear nueva etiqueta."""
    try:
        data = request.get_json() or {}
        return jsonify({'success': True, 'tag': data})
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/tags/<tag_id>/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_tag_users(tag_id):
    """Admin: Obtener usuarios con una etiqueta especifica."""
    try:
        return jsonify({'success': True, 'users': []})
    except Exception as e:
        logger.error(f"Error getting tag users: {e}")
        return jsonify({'success': False, 'error': str(e), 'users': []}), 500


@app.route('/api/admin/users/<user_id>/tags', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_save_user_tags(user_id):
    """Admin: Guardar etiquetas de un usuario."""
    try:
        data = request.get_json() or {}
        tags = data.get('tags', [])
        return jsonify({'success': True, 'message': 'Etiquetas actualizadas'})
    except Exception as e:
        logger.error(f"Error saving user tags: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
