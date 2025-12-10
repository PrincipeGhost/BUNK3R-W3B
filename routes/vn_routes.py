"""
Virtual Numbers Routes - Endpoints de Numeros Virtuales
Agente: Frontend-User / Backend-API
Rama: feature/frontend-user

Este archivo contiene los endpoints de numeros virtuales migrados desde app.py
Migracion: 10 Diciembre 2025

Endpoints migrados:
- /api/vn/providers (GET) - Proveedores disponibles
- /api/vn/countries (GET) - Paises disponibles
- /api/vn/services (GET) - Servicios por pais
- /api/vn/purchase (POST) - Comprar numero virtual
- /api/vn/check/<id> (GET) - Verificar SMS
- /api/vn/cancel/<id> (POST) - Cancelar orden
- /api/vn/history (GET) - Historial de ordenes
- /api/vn/active (GET) - Ordenes activas
- /api/admin/vn/stats (GET) - Stats admin
- /api/admin/vn/settings (GET/POST) - Config admin
- /api/admin/vn/inventory (GET/POST/DELETE) - Inventario admin
- /api/admin/vn/orders (GET) - Ordenes admin
"""

import logging
import psycopg2.extras

from flask import Blueprint, jsonify, request

from tracking.decorators import require_telegram_auth, require_telegram_user, require_owner, is_owner
from tracking.services import get_db_manager, get_vn_manager
from tracking.utils import rate_limit

logger = logging.getLogger(__name__)

vn_bp = Blueprint('vn', __name__, url_prefix='/api')


@vn_bp.route('/vn/health', methods=['GET'])
def vn_health():
    """Health check del modulo virtual numbers."""
    return jsonify({
        'success': True,
        'module': 'vn_routes',
        'status': 'active',
        'endpoints_migrated': [
            '/api/vn/providers',
            '/api/vn/countries',
            '/api/vn/services',
            '/api/vn/purchase',
            '/api/vn/check/<id>',
            '/api/vn/cancel/<id>',
            '/api/vn/history',
            '/api/vn/active',
            '/api/admin/vn/stats',
            '/api/admin/vn/settings',
            '/api/admin/vn/inventory',
            '/api/admin/vn/orders'
        ]
    })


@vn_bp.route('/vn/providers', methods=['GET'])
@require_telegram_user
def get_vn_providers():
    """Get available virtual number providers (balance hidden for non-admins)"""
    try:
        vn_manager = get_vn_manager()
        db_manager = get_db_manager()
        
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


@vn_bp.route('/vn/countries', methods=['GET'])
@require_telegram_user
def get_vn_countries():
    """Get available countries for virtual numbers"""
    try:
        vn_manager = get_vn_manager()
        db_manager = get_db_manager()
        
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


@vn_bp.route('/vn/services', methods=['GET'])
@require_telegram_user
def get_vn_services():
    """Get available services for a country with prices"""
    try:
        vn_manager = get_vn_manager()
        db_manager = get_db_manager()
        
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


@vn_bp.route('/vn/purchase', methods=['POST'])
@require_telegram_user
@rate_limit('vn_purchase')
def purchase_vn():
    """Purchase a virtual number"""
    try:
        vn_manager = get_vn_manager()
        
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
        
        db_manager = get_db_manager()
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


@vn_bp.route('/vn/check/<order_id>', methods=['GET'])
@require_telegram_user
def check_vn_sms(order_id):
    """Check if SMS has been received for an order"""
    try:
        vn_manager = get_vn_manager()
        
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


@vn_bp.route('/vn/cancel/<order_id>', methods=['POST'])
@require_telegram_user
def cancel_vn_order(order_id):
    """Cancel a virtual number order"""
    try:
        vn_manager = get_vn_manager()
        
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


@vn_bp.route('/vn/history', methods=['GET'])
@require_telegram_user
def get_vn_history():
    """Get user's virtual number order history"""
    try:
        vn_manager = get_vn_manager()
        
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


@vn_bp.route('/vn/active', methods=['GET'])
@require_telegram_user
def get_vn_active():
    """Get user's active virtual number orders"""
    try:
        db_manager = get_db_manager()
        
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
# ADMIN ENDPOINTS PARA NUMEROS VIRTUALES
# ============================================================

@vn_bp.route('/admin/vn/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_stats():
    """Admin: Get virtual number statistics"""
    try:
        db_manager = get_db_manager()
        vn_manager = get_vn_manager()
        
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


@vn_bp.route('/admin/vn/settings', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_settings():
    """Admin: Get virtual number settings"""
    try:
        db_manager = get_db_manager()
        
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


@vn_bp.route('/admin/vn/settings', methods=['POST'])
@require_telegram_auth
@require_owner
def update_admin_vn_settings():
    """Admin: Update virtual number settings"""
    try:
        db_manager = get_db_manager()
        
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


@vn_bp.route('/admin/vn/inventory', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_inventory():
    """Admin: Get Legit SMS inventory"""
    try:
        db_manager = get_db_manager()
        
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


@vn_bp.route('/admin/vn/inventory', methods=['POST'])
@require_telegram_auth
@require_owner
def add_admin_vn_inventory():
    """Admin: Add number to Legit SMS inventory"""
    try:
        db_manager = get_db_manager()
        
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


@vn_bp.route('/admin/vn/inventory/<inventory_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def delete_admin_vn_inventory(inventory_id):
    """Admin: Delete number from Legit SMS inventory"""
    try:
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        success = db_manager.remove_from_legitsms_inventory(inventory_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error deleting from admin VN inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@vn_bp.route('/admin/vn/orders', methods=['GET'])
@require_telegram_auth
@require_owner
def get_admin_vn_orders():
    """Admin: Get all virtual number orders with filters"""
    try:
        db_manager = get_db_manager()
        
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
                        'country': row['country_name'] or row['country_code'],
                        'service': row['service_name'] or row['service_code'],
                        'phoneNumber': row['phone_number'],
                        'smsCode': row['sms_code'],
                        'status': row['status'],
                        'costUsd': float(row['cost_usd']) if row.get('cost_usd') else 0,
                        'costBunkercoin': float(row['bunkercoin_charged']) if row.get('bunkercoin_charged') else 0,
                        'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
                        'expiresAt': row['expires_at'].isoformat() if row.get('expires_at') else None
                    })
        
        return jsonify({
            'success': True,
            'orders': orders,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        logger.error(f"Error getting admin VN orders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
