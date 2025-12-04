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
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs, unquote

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracking.database import DatabaseManager
from tracking.models import Tracking
from tracking.email_service import EmailService, prepare_tracking_email_data, send_tracking_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('ADMIN_TOKEN', 'dev-secret-key')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '')
OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '')

try:
    db_manager = DatabaseManager()
    logger.info("Database connection established")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    db_manager = None

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
    except:
        return False


def require_telegram_auth(f):
    """Decorador para requerir autenticación de Telegram o modo demo."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_demo_mode = request.headers.get('X-Demo-Mode') == 'true'
        demo_allowed = not BOT_TOKEN
        
        if is_demo_mode and demo_allowed:
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
        
        if not is_owner(user_id):
            return jsonify({'error': 'Solo el owner puede acceder', 'code': 'NOT_OWNER'}), 403
        
        request.telegram_user = user
        request.telegram_data = validated_data
        request.is_owner = True
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
        is_demo_mode = request.headers.get('X-Demo-Mode') == 'true'
        
        if is_demo_mode:
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


@app.route('/')
def index():
    """Página principal - siempre carga, la validación se hace en el frontend con el SDK de Telegram."""
    return render_template('index.html')


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
    
    if not owner_status:
        return jsonify({
            'valid': False,
            'error': 'Solo el owner puede acceder a esta aplicación',
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
        'isOwner': True
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
        logger.error(f"Error fetching trackings: {e}")
        return jsonify({'error': str(e)}), 500


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
        logger.error(f"Error fetching tracking {tracking_id}: {e}")
        return jsonify({'error': str(e)}), 500


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
        
        user = request.telegram_user
        
        now = datetime.now()
        date_time = data.get('dateTime') or now.strftime('%d/%m/%Y %H:%M')
        
        tracking = Tracking(
            tracking_id=data['trackingId'],
            recipient_name=data['recipientName'],
            product_name=data['productName'],
            product_price=data.get('productPrice', '0'),
            status=data.get('status', 'RETENIDO'),
            delivery_address=data.get('deliveryAddress', ''),
            sender_address=data.get('senderAddress', ''),
            date_time=date_time,
            package_weight=data.get('packageWeight', '0.5 kg'),
            estimated_delivery_date=data.get('estimatedDelivery', ''),
            recipient_postal_code=data.get('recipientPostalCode', ''),
            recipient_province=data.get('recipientProvince', ''),
            recipient_country=data.get('recipientCountry', ''),
            sender_postal_code=data.get('senderPostalCode', ''),
            sender_province=data.get('senderProvince', ''),
            sender_country=data.get('senderCountry', ''),
            user_telegram_id=user.get('id'),
            username=user.get('username', '')
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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        caption = data.get('caption', '')
        
        if content_type == 'text' and not caption:
            return jsonify({'error': 'El texto es requerido para posts de tipo texto'}), 400
        
        if content_type in ['image', 'video'] and not content_url:
            return jsonify({'error': 'La URL del contenido es requerida'}), 400
        
        db_manager.get_or_create_user(
            user_id=user_id,
            username=user.get('username'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
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
        logger.error(f"Error creating post: {e}")
        return jsonify({'error': str(e)}), 500


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
        logger.error(f"Error getting posts feed: {e}")
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@require_telegram_user
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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'posts': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting user posts {user_id}: {e}")
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/follow', methods=['POST'])
@require_telegram_user
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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


@app.route('/api/bots/my', methods=['GET'])
@require_telegram_user
def get_my_bots():
    """Obtener mis bots activos."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        bots = db_manager.get_user_bots(user_id)
        
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
        return jsonify({'error': str(e)}), 500


@app.route('/api/bots/available', methods=['GET'])
@require_telegram_user
def get_available_bots():
    """Obtener bots disponibles para comprar."""
    try:
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        bots = db_manager.get_available_bots(user_id)
        
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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
