"""
SMSPool API Service for Virtual Numbers
Integrates with SMSPool.net API for purchasing virtual numbers and receiving SMS
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SMSPoolService:
    """Client for SMSPool API integration"""
    
    BASE_URL = "https://api.smspool.net"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('SMSPOOL_API_KEY')
        if not self.api_key:
            logger.warning("SMSPOOL_API_KEY not configured")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = 'GET') -> Dict:
        """Make request to SMSPool API"""
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}
        
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['key'] = self.api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            else:
                response = requests.post(url, data=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {'success': True, 'data': data}
                except:
                    return {'success': True, 'data': response.text}
            else:
                logger.error(f"SMSPool API error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error("SMSPool API timeout")
            return {'success': False, 'error': 'Connection timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"SMSPool API request error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_balance(self) -> Dict:
        """Get current account balance"""
        result = self._make_request('request/balance')
        if result['success']:
            try:
                balance = float(result['data'].get('balance', 0))
                return {'success': True, 'balance': balance}
            except (ValueError, TypeError, AttributeError):
                if isinstance(result['data'], (int, float)):
                    return {'success': True, 'balance': float(result['data'])}
                return {'success': True, 'balance': 0.0}
        return result
    
    def get_countries(self) -> Dict:
        """Get list of available countries"""
        result = self._make_request('country/retrieve_all')
        if result['success']:
            countries = []
            data = result['data']
            
            if isinstance(data, list):
                for country in data:
                    countries.append({
                        'id': country.get('ID') or country.get('id'),
                        'name': country.get('name', ''),
                        'short_name': country.get('short_name', ''),
                        'flag': self._get_flag_emoji(country.get('short_name', ''))
                    })
            elif isinstance(data, dict):
                for key, country in data.items():
                    if isinstance(country, dict):
                        countries.append({
                            'id': country.get('ID') or country.get('id') or key,
                            'name': country.get('name', key),
                            'short_name': country.get('short_name', ''),
                            'flag': self._get_flag_emoji(country.get('short_name', ''))
                        })
            
            return {'success': True, 'countries': countries}
        return result
    
    def get_services(self, country_id: Optional[str] = None) -> Dict:
        """Get list of available services/apps"""
        params = {}
        if country_id:
            params['country'] = country_id
        
        result = self._make_request('service/retrieve_all', params)
        if result['success']:
            services = []
            data = result['data']
            
            if isinstance(data, list):
                for service in data:
                    services.append({
                        'id': service.get('ID') or service.get('id'),
                        'name': service.get('name', ''),
                        'short_name': service.get('short_name', ''),
                        'price': float(service.get('price', 0)),
                        'icon': self._get_service_icon(service.get('name', ''))
                    })
            elif isinstance(data, dict):
                for key, service in data.items():
                    if isinstance(service, dict):
                        services.append({
                            'id': service.get('ID') or service.get('id') or key,
                            'name': service.get('name', key),
                            'short_name': service.get('short_name', ''),
                            'price': float(service.get('price', 0)),
                            'icon': self._get_service_icon(service.get('name', key))
                        })
            
            return {'success': True, 'services': services}
        return result
    
    def get_price(self, country_id: str, service_id: str) -> Dict:
        """Get price for specific country and service combination"""
        result = self._make_request('request/price', {
            'country': country_id,
            'service': service_id
        })
        
        if result['success']:
            data = result['data']
            if isinstance(data, dict):
                price = float(data.get('price', 0))
            else:
                try:
                    price = float(data)
                except:
                    price = 0.0
            return {'success': True, 'price': price}
        return result
    
    def purchase_number(self, country_id: str, service_id: str, pool: Optional[int] = None) -> Dict:
        """Purchase a virtual number for receiving SMS"""
        params = {
            'country': country_id,
            'service': service_id
        }
        if pool:
            params['pool'] = pool
        
        result = self._make_request('purchase/sms', params)
        
        if result['success']:
            data = result['data']
            if isinstance(data, dict):
                if data.get('success') == 0 or 'error' in data:
                    return {'success': False, 'error': data.get('message', data.get('error', 'Purchase failed'))}
                
                return {
                    'success': True,
                    'order_id': str(data.get('order_id', '')),
                    'phone_number': data.get('phonenumber', data.get('number', '')),
                    'country': data.get('country', country_id),
                    'service': data.get('service', service_id),
                    'cost': float(data.get('cost', data.get('price', 0))),
                    'expires_at': data.get('expiry', None)
                }
            return {'success': False, 'error': 'Unexpected response format'}
        return result
    
    def check_sms(self, order_id: str) -> Dict:
        """Check if SMS has been received for an order"""
        result = self._make_request('sms/check', {'orderid': order_id})
        
        if result['success']:
            data = result['data']
            if isinstance(data, dict):
                status = data.get('status', 0)
                
                if status == 3 or data.get('sms'):
                    return {
                        'success': True,
                        'status': 'received',
                        'sms_code': data.get('sms', ''),
                        'full_sms': data.get('full_sms', data.get('sms', '')),
                        'sender': data.get('sender', '')
                    }
                elif status == 2:
                    return {
                        'success': True,
                        'status': 'cancelled',
                        'sms_code': None
                    }
                elif status == 6:
                    return {
                        'success': True,
                        'status': 'refunded',
                        'sms_code': None
                    }
                else:
                    return {
                        'success': True,
                        'status': 'pending',
                        'sms_code': None
                    }
            
            if isinstance(data, str) and data:
                return {
                    'success': True,
                    'status': 'received',
                    'sms_code': data,
                    'full_sms': data
                }
            
            return {'success': True, 'status': 'pending', 'sms_code': None}
        return result
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order and request refund"""
        result = self._make_request('sms/cancel', {'orderid': order_id})
        
        if result['success']:
            data = result['data']
            if isinstance(data, dict):
                if data.get('success') == 1:
                    return {'success': True, 'refunded': True}
                return {'success': False, 'error': data.get('message', 'Cancel failed')}
            return {'success': True, 'refunded': True}
        return result
    
    def resend_sms(self, order_id: str) -> Dict:
        """Request SMS to be resent"""
        result = self._make_request('sms/resend', {'orderid': order_id})
        
        if result['success']:
            return {'success': True, 'message': 'SMS resend requested'}
        return result
    
    def _get_flag_emoji(self, country_code: str) -> str:
        """Convert country code to flag emoji"""
        country_flags = {
            'US': '🇺🇸', 'MX': '🇲🇽', 'ES': '🇪🇸', 'GB': '🇬🇧', 'UK': '🇬🇧',
            'CA': '🇨🇦', 'DE': '🇩🇪', 'FR': '🇫🇷', 'IT': '🇮🇹', 'BR': '🇧🇷',
            'AR': '🇦🇷', 'CO': '🇨🇴', 'CL': '🇨🇱', 'PE': '🇵🇪', 'VE': '🇻🇪',
            'RU': '🇷🇺', 'CN': '🇨🇳', 'IN': '🇮🇳', 'ID': '🇮🇩', 'PH': '🇵🇭',
            'TH': '🇹🇭', 'VN': '🇻🇳', 'MY': '🇲🇾', 'SG': '🇸🇬', 'AU': '🇦🇺',
            'NZ': '🇳🇿', 'JP': '🇯🇵', 'KR': '🇰🇷', 'NL': '🇳🇱', 'BE': '🇧🇪',
            'PL': '🇵🇱', 'PT': '🇵🇹', 'AT': '🇦🇹', 'CH': '🇨🇭', 'SE': '🇸🇪',
            'NO': '🇳🇴', 'DK': '🇩🇰', 'FI': '🇫🇮', 'IE': '🇮🇪', 'ZA': '🇿🇦',
            'EG': '🇪🇬', 'NG': '🇳🇬', 'KE': '🇰🇪', 'UA': '🇺🇦', 'PK': '🇵🇰',
            'BD': '🇧🇩', 'TR': '🇹🇷', 'SA': '🇸🇦', 'AE': '🇦🇪', 'IL': '🇮🇱',
            'HK': '🇭🇰', 'TW': '🇹🇼', 'RO': '🇷🇴', 'CZ': '🇨🇿', 'HU': '🇭🇺',
            'GR': '🇬🇷', 'EC': '🇪🇨', 'BO': '🇧🇴', 'UY': '🇺🇾', 'PY': '🇵🇾'
        }
        code = country_code.upper() if country_code else ''
        return country_flags.get(code, '🌍')
    
    def _get_service_icon(self, service_name: str) -> str:
        """Get icon emoji for service"""
        service_icons = {
            'whatsapp': '💬',
            'telegram': '✈️',
            'instagram': '📷',
            'facebook': '👤',
            'twitter': '🐦',
            'google': '🔍',
            'gmail': '📧',
            'microsoft': '🪟',
            'amazon': '📦',
            'tiktok': '🎵',
            'snapchat': '👻',
            'uber': '🚗',
            'lyft': '🚕',
            'paypal': '💳',
            'netflix': '🎬',
            'spotify': '🎧',
            'discord': '🎮',
            'steam': '🎮',
            'twitch': '📺',
            'linkedin': '💼',
            'apple': '🍎',
            'yahoo': '📧',
            'binance': '💰',
            'coinbase': '🪙',
            'openai': '🤖',
            'chatgpt': '🤖',
            'tinder': '❤️',
            'bumble': '🐝',
            'wechat': '💬',
            'line': '💬',
            'viber': '💬',
            'signal': '🔒',
            'airbnb': '🏠',
            'ebay': '🛒',
            'aliexpress': '🛍️',
            'wish': '⭐',
            'shopee': '🛒',
            'lazada': '🛒',
            'grab': '🚗',
            'bolt': '⚡',
            'doordash': '🍔',
            'ubereats': '🍕',
            'deliveroo': '🚴'
        }
        
        name_lower = service_name.lower() if service_name else ''
        for key, icon in service_icons.items():
            if key in name_lower:
                return icon
        return '📱'


class VirtualNumbersManager:
    """Manager for virtual numbers business logic"""
    
    COMMISSION_PERCENT = 30
    USD_TO_BUNKERCOIN = 10
    DEFAULT_EXPIRY_MINUTES = 20
    
    def __init__(self, db_manager, smspool_service: Optional[SMSPoolService] = None):
        self.db = db_manager
        self.smspool = smspool_service or SMSPoolService()
    
    def calculate_user_price(self, provider_price_usd: float, commission_percent: Optional[float] = None) -> Dict:
        """Calculate final price for user including commission"""
        commission = commission_percent if commission_percent is not None else self.COMMISSION_PERCENT
        
        price_with_commission = provider_price_usd * (1 + commission / 100)
        bunkercoin_price = price_with_commission * self.USD_TO_BUNKERCOIN
        
        return {
            'original_usd': round(provider_price_usd, 4),
            'with_commission_usd': round(price_with_commission, 4),
            'bunkercoin': round(bunkercoin_price, 2),
            'commission_percent': commission
        }
    
    def get_user_balance(self, user_id: str) -> float:
        """Get user's BUNK3RCO1N balance"""
        try:
            import psycopg2.extras
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(SUM(amount), 0) as balance
                        FROM wallet_transactions
                        WHERE user_id = %s
                    """, (user_id,))
                    result = cur.fetchone()
                    return float(result[0]) if result else 0.0
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return 0.0
    
    def deduct_balance(self, user_id: str, amount: float, description: str, reference_id: str) -> bool:
        """Deduct BUNK3RCO1N from user's wallet"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO wallet_transactions (user_id, transaction_type, amount, description, reference_id)
                        VALUES (%s, 'virtual_number_purchase', %s, %s, %s)
                    """, (user_id, -abs(amount), description, reference_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error deducting balance: {e}")
            return False
    
    def refund_balance(self, user_id: str, amount: float, description: str, reference_id: str) -> bool:
        """Refund BUNK3RCO1N to user's wallet"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO wallet_transactions (user_id, transaction_type, amount, description, reference_id)
                        VALUES (%s, 'virtual_number_refund', %s, %s, %s)
                    """, (user_id, abs(amount), description, reference_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error refunding balance: {e}")
            return False
    
    def get_smspool_balance(self) -> Dict:
        """Get SMSPool account balance"""
        return self.smspool.get_balance()
    
    def get_available_countries(self) -> Dict:
        """Get countries available for virtual numbers"""
        return self.smspool.get_countries()
    
    def get_available_services(self, country_id: str, commission_percent: Optional[float] = None) -> Dict:
        """Get services available for a country with calculated prices"""
        result = self.smspool.get_services(country_id)
        
        if result['success']:
            services_with_prices = []
            for service in result['services']:
                price_info = self.calculate_user_price(
                    service['price'], 
                    commission_percent
                )
                services_with_prices.append({
                    **service,
                    'original_price_usd': price_info['original_usd'],
                    'price_usd': price_info['with_commission_usd'],
                    'price_bunkercoin': price_info['bunkercoin']
                })
            
            result['services'] = services_with_prices
        
        return result
    
    def purchase_virtual_number(self, user_id: str, country_id: str, service_id: str,
                                 country_name: str = '', service_name: str = '',
                                 commission_percent: Optional[float] = None) -> Dict:
        """Purchase a virtual number for a user with atomic transaction"""
        try:
            if not self.smspool.api_key:
                return {'success': False, 'error': 'Servicio no disponible'}
            
            price_result = self.smspool.get_price(country_id, service_id)
            if not price_result['success']:
                return {'success': False, 'error': 'No se pudo obtener el precio'}
            
            provider_price = price_result['price']
            if provider_price <= 0:
                return {'success': False, 'error': 'Precio invalido del proveedor'}
            
            price_info = self.calculate_user_price(provider_price, commission_percent)
            bunkercoin_cost = price_info['bunkercoin']
            
            user_balance = self.get_user_balance(user_id)
            if user_balance < bunkercoin_cost:
                return {
                    'success': False, 
                    'error': 'Saldo insuficiente',
                    'required': bunkercoin_cost,
                    'available': user_balance
                }
            
            import uuid
            internal_order_id = str(uuid.uuid4())
            
            with self.db.get_connection() as conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO virtual_number_orders (
                                id, user_id, provider, country_code, country_name,
                                service_code, service_name, provider_order_id,
                                cost_usd, cost_with_commission, bunkercoin_charged,
                                status, expires_at
                            ) VALUES (
                                %s, %s, 'smspool', %s, %s, %s, %s, NULL,
                                %s, %s, %s, 'pending', NOW() + INTERVAL '%s minutes'
                            )
                        """, (
                            internal_order_id, user_id, country_id, country_name,
                            service_id, service_name,
                            price_info['original_usd'], price_info['with_commission_usd'],
                            bunkercoin_cost, self.DEFAULT_EXPIRY_MINUTES
                        ))
                        
                        cur.execute("""
                            INSERT INTO wallet_transactions 
                            (user_id, transaction_type, amount, description, reference_id)
                            VALUES (%s, 'virtual_number_purchase', %s, %s, %s)
                        """, (user_id, -abs(bunkercoin_cost), 
                              f"Numero virtual {service_name} ({country_name})", 
                              internal_order_id))
                        
                        conn.commit()
                    
                    purchase_result = self.smspool.purchase_number(country_id, service_id)
                    
                    if purchase_result['success']:
                        order_id = purchase_result['order_id']
                        phone_number = purchase_result['phone_number']
                        
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE virtual_number_orders 
                                SET provider_order_id = %s, phone_number = %s, status = 'active'
                                WHERE id = %s
                            """, (order_id, phone_number, internal_order_id))
                            conn.commit()
                        
                        return {
                            'success': True,
                            'order_id': internal_order_id,
                            'provider_order_id': order_id,
                            'phone_number': phone_number,
                            'cost_bunkercoin': bunkercoin_cost,
                            'expires_in_minutes': self.DEFAULT_EXPIRY_MINUTES
                        }
                    else:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE virtual_number_orders 
                                SET status = 'failed'
                                WHERE id = %s
                            """, (internal_order_id,))
                            
                            cur.execute("""
                                INSERT INTO wallet_transactions 
                                (user_id, transaction_type, amount, description, reference_id)
                                VALUES (%s, 'virtual_number_refund', %s, %s, %s)
                            """, (user_id, abs(bunkercoin_cost), 
                                  f"Reembolso - Error al obtener numero", 
                                  internal_order_id))
                            conn.commit()
                        
                        return {'success': False, 'error': purchase_result.get('error', 'Error al comprar numero')}
                        
                except Exception as inner_e:
                    conn.rollback()
                    logger.error(f"Transaction error: {inner_e}")
                    raise
            
        except Exception as e:
            logger.error(f"Error purchasing virtual number: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_sms_status(self, order_id: str, user_id: str) -> Dict:
        """Check SMS status for an order"""
        try:
            import psycopg2.extras
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM virtual_number_orders
                        WHERE id = %s AND user_id = %s
                    """, (order_id, user_id))
                    order = cur.fetchone()
                    
                    if not order:
                        return {'success': False, 'error': 'Order not found'}
                    
                    if order['status'] == 'received':
                        return {
                            'success': True,
                            'status': 'received',
                            'sms_code': order['sms_code'],
                            'full_sms': order['sms_full_text'],
                            'phone_number': order['phone_number']
                        }
                    
                    if order['status'] in ['cancelled', 'expired', 'refunded']:
                        return {
                            'success': True,
                            'status': order['status'],
                            'sms_code': None
                        }
                    
                    sms_result = self.smspool.check_sms(order['provider_order_id'])
                    
                    if sms_result['success'] and sms_result['status'] == 'received':
                        cur.execute("""
                            UPDATE virtual_number_orders
                            SET status = 'received', sms_code = %s, sms_full_text = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (sms_result['sms_code'], sms_result.get('full_sms', ''), order_id))
                        conn.commit()
                        
                        return {
                            'success': True,
                            'status': 'received',
                            'sms_code': sms_result['sms_code'],
                            'full_sms': sms_result.get('full_sms', ''),
                            'phone_number': order['phone_number']
                        }
                    
                    return {
                        'success': True,
                        'status': 'pending',
                        'phone_number': order['phone_number'],
                        'sms_code': None
                    }
                    
        except Exception as e:
            logger.error(f"Error checking SMS status: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str, user_id: str) -> Dict:
        """Cancel an order and process refund"""
        try:
            import psycopg2.extras
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM virtual_number_orders
                        WHERE id = %s AND user_id = %s AND status = 'active'
                    """, (order_id, user_id))
                    order = cur.fetchone()
                    
                    if not order:
                        return {'success': False, 'error': 'Order not found or already processed'}
                    
                    cancel_result = self.smspool.cancel_order(order['provider_order_id'])
                    
                    if cancel_result['success']:
                        refund_amount = order['bunkercoin_charged'] * 0.8
                        
                        cur.execute("""
                            UPDATE virtual_number_orders
                            SET status = 'cancelled', updated_at = NOW()
                            WHERE id = %s
                        """, (order_id,))
                        conn.commit()
                        
                        self.refund_balance(
                            user_id, 
                            refund_amount, 
                            f"Reembolso por cancelacion de numero virtual",
                            order_id
                        )
                        
                        return {
                            'success': True,
                            'refunded_amount': refund_amount,
                            'message': 'Order cancelled and refund processed'
                        }
                    else:
                        return {'success': False, 'error': 'Could not cancel order with provider'}
                    
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_history(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict:
        """Get user's virtual number order history"""
        try:
            import psycopg2.extras
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, provider, country_code, country_name, service_code,
                               service_name, phone_number, sms_code, status,
                               bunkercoin_charged, created_at, updated_at
                        FROM virtual_number_orders
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                    
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
                            'cost': float(row['bunkercoin_charged']),
                            'createdAt': row['created_at'].isoformat() if row['created_at'] else None
                        })
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM virtual_number_orders WHERE user_id = %s
                    """, (user_id,))
                    total = cur.fetchone()[0]
                    
                    return {
                        'success': True,
                        'orders': orders,
                        'total': total
                    }
                    
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return {'success': False, 'error': str(e)}


smspool_service = SMSPoolService()
