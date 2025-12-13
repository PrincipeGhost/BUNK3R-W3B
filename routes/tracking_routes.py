"""
Tracking Routes - Endpoints de seguimiento de paquetes
Agente: Backend-API
Rama: feature/backend-api

Este archivo contiene los endpoints de tracking migrados desde app.py
Migracion: 10 Diciembre 2025

Endpoints migrados:
- /api/trackings (GET) - Listar trackings
- /api/tracking (POST) - Crear tracking
- /api/tracking/<id> (GET/PUT/DELETE) - CRUD tracking
- /api/tracking/<id>/status (PUT) - Actualizar estado
- /api/tracking/<id>/delay (POST) - Agregar retraso
- /api/tracking/<id>/email (POST) - Enviar email
- /api/stats (GET) - Estadisticas
- /api/delay-reasons (GET) - Razones de retraso
- /api/statuses (GET) - Estados disponibles
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from bot.tracking_correos.decorators import require_telegram_auth, require_owner
from bot.tracking_correos.services import get_db_manager
from bot.tracking_correos.utils import InputValidator
from bot.tracking_correos.email_service import EmailService
from bot.tracking_correos.models import Tracking

logger = logging.getLogger(__name__)

tracking_bp = Blueprint('tracking', __name__, url_prefix='/api')

STATUS_MAP = {
    'RETENIDO': {'icon': '📦', 'label': 'Retenido', 'color': '#f39c12'},
    'EN_TRANSITO': {'icon': '🚚', 'label': 'En Camino', 'color': '#3498db'},
    'ENTREGADO': {'icon': '✅', 'label': 'Entregado', 'color': '#27ae60'},
    'PAGO_CONFIRMADO': {'icon': '💰', 'label': 'Pago Confirmado', 'color': '#e74c3c'}
}

# Descripciones automáticas para estados
STATUS_DESCRIPTIONS = {
    'RETENIDO': 'Paquete retenido',
    'EN_TRANSITO': 'Paquete en camino',
    'ENTREGADO': 'Paquete entregado',
    'PAGO_CONFIRMADO': 'Pago confirmado'
}

DELAY_REASONS = [
    {"id": "customs", "text": "Problemas en aduana", "days": 3},
    {"id": "high_demand", "text": "Alta demanda", "days": 2},
    {"id": "weather", "text": "Condiciones climaticas adversas", "days": 1},
    {"id": "logistics", "text": "Problemas logisticos", "days": 2},
    {"id": "documentation", "text": "Documentacion pendiente", "days": 3},
    {"id": "verification", "text": "Verificacion de seguridad", "days": 1},
    {"id": "other", "text": "Otro motivo", "days": 1}
]

input_validator = InputValidator()


def sanitize_error(error, error_type='api_error'):
    """Sanitiza errores para no exponer informacion sensible."""
    logger.error(f"Error in {error_type}: {error}")
    return f"Error en operacion ({error_type})"


def is_owner(user_id):
    """Verifica si el usuario es owner."""
    import os
    owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
    return str(user_id) == str(owner_id) if owner_id else False


@tracking_bp.route('/tracking/health', methods=['GET'])
def tracking_health():
    """Health check del modulo tracking."""
    return jsonify({
        'success': True,
        'module': 'tracking_routes',
        'status': 'active',
        'message': 'Endpoints de tracking funcionando.',
        'endpoints_migrated': [
            '/api/trackings (GET)',
            '/api/tracking (POST)',
            '/api/tracking/<id> (GET/PUT/DELETE)',
            '/api/tracking/<id>/status (PUT)',
            '/api/tracking/<id>/delay (POST)',
            '/api/tracking/<id>/email (POST)',
            '/api/stats (GET)',
            '/api/delay-reasons (GET)',
            '/api/statuses (GET)'
        ]
    })


@tracking_bp.route('/trackings', methods=['GET'])
@require_telegram_auth
def get_trackings():
    """Obtener lista de trackings."""
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    try:
        db_manager = get_db_manager()
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


@tracking_bp.route('/tracking/<tracking_id>', methods=['GET'])
@require_telegram_auth
def get_tracking(tracking_id):
    """Obtener detalles de un tracking especifico."""
    try:
        db_manager = get_db_manager()
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


@tracking_bp.route('/tracking', methods=['POST'])
@require_telegram_auth
def create_tracking():
    """Crear nuevo tracking."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        
        required_fields = ['recipientName', 'productName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        import random
        import string
        characters = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(characters, k=21))
        tracking_id = f"TRK{random_part}"
        
        recipient_name = input_validator.sanitize_name(data['recipientName'])
        product_name = input_validator.sanitize_name(data['productName'])
        
        if not recipient_name or not product_name:
            return jsonify({'error': 'Nombre de destinatario y producto son requeridos'}), 400
        
        user = request.telegram_user
        
        now = datetime.now()
        entry_datetime = data.get('entryDatetime', '')
        if entry_datetime:
            try:
                parsed_dt = datetime.fromisoformat(entry_datetime.replace('T', ' '))
                date_time = parsed_dt.strftime('%d/%m/%Y %H:%M')
            except:
                date_time = now.strftime('%d/%m/%Y %H:%M')
        else:
            date_time = now.strftime('%d/%m/%Y %H:%M')
        
        tracking = Tracking(
            tracking_id=tracking_id,
            recipient_name=recipient_name,
            product_name=product_name,
            product_price=input_validator.sanitize_text(data.get('productPrice', '0'), 20),
            status='RETENIDO',
            delivery_address=input_validator.sanitize_text(data.get('deliveryAddress', ''), 500),
            sender_address=input_validator.sanitize_text(data.get('senderAddress', ''), 500),
            date_time=date_time,
            package_weight=input_validator.sanitize_text(data.get('packageWeight', '0.5 kg'), 20),
            estimated_delivery_date=input_validator.sanitize_text(entry_datetime, 50),
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


@tracking_bp.route('/tracking/<tracking_id>/status', methods=['PUT'])
@require_telegram_auth
def update_tracking_status(tracking_id):
    """Actualizar estado de un tracking."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'error': 'Estado requerido'}), 400
        
        if new_status not in STATUS_MAP:
            return jsonify({'error': 'Estado invalido'}), 400
        
        # Si no hay notas, usar la descripción automática del estado
        if not notes:
            notes = STATUS_DESCRIPTIONS.get(new_status, STATUS_MAP[new_status]["label"])
        
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


@tracking_bp.route('/tracking/<tracking_id>/delay', methods=['POST'])
@require_telegram_auth
def add_delay(tracking_id):
    """Agregar retraso a un tracking."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        delay_days = data.get('days', 1)
        reason = data.get('reason', 'Retraso no especificado')
        
        success = db_manager.add_delay_to_tracking(tracking_id, delay_days, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Retraso de {delay_days} dias agregado'
            })
        else:
            return jsonify({'error': 'Error al agregar retraso'}), 500
            
    except Exception as e:
        logger.error(f"Error adding delay: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@tracking_bp.route('/tracking/<tracking_id>', methods=['PUT'])
@require_telegram_auth
def update_tracking(tracking_id):
    """Actualizar informacion de un tracking."""
    try:
        db_manager = get_db_manager()
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
                    'entryDatetime': 'estimated_delivery_date',
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


@tracking_bp.route('/tracking/<tracking_id>', methods=['DELETE'])
@require_telegram_auth
def delete_tracking(tracking_id):
    """Eliminar un tracking."""
    try:
        db_manager = get_db_manager()
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


@tracking_bp.route('/tracking/<tracking_id>/email', methods=['POST'])
@require_telegram_auth
@require_owner
def send_email(tracking_id):
    """Enviar email para un tracking (solo owner)."""
    try:
        db_manager = get_db_manager()
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


@tracking_bp.route('/stats', methods=['GET'])
@require_telegram_auth
def get_stats():
    """Obtener estadisticas de trackings."""
    try:
        db_manager = get_db_manager()
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
            'pagoConfirmado': 0
        }
        
        for t in trackings:
            if t.status == 'RETENIDO':
                stats['retenido'] += 1
            elif t.status == 'EN_TRANSITO':
                stats['enTransito'] += 1
            elif t.status == 'ENTREGADO':
                stats['entregado'] += 1
            elif t.status == 'PAGO_CONFIRMADO':
                stats['pagoConfirmado'] += 1
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@tracking_bp.route('/delay-reasons', methods=['GET'])
@require_telegram_auth
def get_delay_reasons():
    """Obtener razones de retraso disponibles."""
    return jsonify({
        'success': True,
        'reasons': DELAY_REASONS
    })


@tracking_bp.route('/statuses', methods=['GET'])
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
