"""
Legit SMS API Service for Virtual Numbers
Integrates with legit-sms.com API for purchasing virtual numbers and receiving SMS
Provides fallback to SMSPool if Legit SMS fails
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LegitSMSService:
    """Client for Legit SMS API integration"""
    
    BASE_URL = "https://legit-sms.com/api"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('LEGITSMS_API_KEY')
        if not self.api_key:
            logger.warning("LEGITSMS_API_KEY not configured")
    
    def is_configured(self) -> bool:
        """Check if service is configured"""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = 'GET') -> Dict:
        """Make request to Legit SMS API"""
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}
        
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            else:
                response = requests.post(url, data=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and data.get('status') == 'error':
                        return {'success': False, 'error': data.get('message', 'Unknown error')}
                    return {'success': True, 'data': data}
                except (ValueError, json.JSONDecodeError) as e:
                    text = response.text.strip()
                    if text.startswith('ACCESS_'):
                        return {'success': True, 'data': {'order_id': text}}
                    if 'ERROR' in text.upper():
                        return {'success': False, 'error': text}
                    return {'success': True, 'data': text}
            else:
                logger.error(f"Legit SMS API error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error("Legit SMS API timeout")
            return {'success': False, 'error': 'Connection timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Legit SMS API request error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_balance(self) -> Dict:
        """Get current account balance"""
        result = self._make_request('getBalance')
        if result['success']:
            try:
                if isinstance(result['data'], dict):
                    balance = float(result['data'].get('balance', 0))
                else:
                    balance = float(result['data'])
                return {'success': True, 'balance': balance}
            except (ValueError, TypeError):
                return {'success': True, 'balance': 0.0}
        return result
    
    def get_countries(self) -> Dict:
        """Get list of available countries"""
        result = self._make_request('getCountries')
        if result['success']:
            countries = []
            data = result['data']
            
            if isinstance(data, list):
                for country in data:
                    countries.append({
                        'id': country.get('id') or country.get('code'),
                        'name': country.get('name', ''),
                        'code': country.get('code', ''),
                        'flag': self._get_flag_emoji(country.get('code', ''))
                    })
            elif isinstance(data, dict):
                for key, country in data.items():
                    if isinstance(country, dict):
                        countries.append({
                            'id': country.get('id') or key,
                            'name': country.get('name', key),
                            'code': country.get('code', key),
                            'flag': self._get_flag_emoji(country.get('code', key))
                        })
            
            return {'success': True, 'countries': countries}
        return result
    
    def _get_flag_emoji(self, country_code: str) -> str:
        """Convert country code to flag emoji"""
        flag_map = {
            'US': '🇺🇸', 'UK': '🇬🇧', 'GB': '🇬🇧', 'CA': '🇨🇦', 
            'RU': '🇷🇺', 'DE': '🇩🇪', 'FR': '🇫🇷', 'ES': '🇪🇸',
            'IT': '🇮🇹', 'BR': '🇧🇷', 'MX': '🇲🇽', 'AR': '🇦🇷',
            'IN': '🇮🇳', 'CN': '🇨🇳', 'JP': '🇯🇵', 'KR': '🇰🇷',
            'AU': '🇦🇺', 'NZ': '🇳🇿', 'PH': '🇵🇭', 'ID': '🇮🇩',
            'TH': '🇹🇭', 'VN': '🇻🇳', 'MY': '🇲🇾', 'SG': '🇸🇬',
            'NL': '🇳🇱', 'PL': '🇵🇱', 'UA': '🇺🇦', 'TR': '🇹🇷',
            'EG': '🇪🇬', 'ZA': '🇿🇦', 'NG': '🇳🇬', 'KE': '🇰🇪',
            'CO': '🇨🇴', 'CL': '🇨🇱', 'PE': '🇵🇪', 'VE': '🇻🇪',
            'SE': '🇸🇪', 'NO': '🇳🇴', 'FI': '🇫🇮', 'DK': '🇩🇰',
            'AT': '🇦🇹', 'CH': '🇨🇭', 'BE': '🇧🇪', 'PT': '🇵🇹',
            'GR': '🇬🇷', 'CZ': '🇨🇿', 'RO': '🇷🇴', 'HU': '🇭🇺'
        }
        return flag_map.get(country_code.upper(), '🌐')
    
    def get_services(self, country_id: Optional[str] = None) -> Dict:
        """Get list of available services with prices"""
        params = {}
        if country_id:
            params['country'] = country_id
        
        result = self._make_request('getServices', params)
        if result['success']:
            services = []
            data = result['data']
            
            if isinstance(data, list):
                for service in data:
                    services.append({
                        'id': service.get('id') or service.get('code'),
                        'name': self._get_service_name(service.get('name', '')),
                        'code': service.get('code', ''),
                        'price': float(service.get('price', 0)),
                        'icon': self._get_service_icon(service.get('name', ''))
                    })
            elif isinstance(data, dict):
                for key, service in data.items():
                    if isinstance(service, dict):
                        services.append({
                            'id': key,
                            'name': self._get_service_name(service.get('name', key)),
                            'code': key,
                            'price': float(service.get('price', 0)),
                            'icon': self._get_service_icon(service.get('name', key))
                        })
            
            services.sort(key=lambda x: x['name'].lower())
            return {'success': True, 'services': services}
        return result
    
    def _get_service_name(self, raw_name: str) -> str:
        """Get readable service name"""
        service_names = {
            'whatsapp': 'WhatsApp', 'telegram': 'Telegram',
            'instagram': 'Instagram', 'facebook': 'Facebook',
            'twitter': 'Twitter / X', 'google': 'Google',
            'tiktok': 'TikTok', 'snapchat': 'Snapchat',
            'discord': 'Discord', 'netflix': 'Netflix',
            'spotify': 'Spotify', 'uber': 'Uber',
            'amazon': 'Amazon', 'paypal': 'PayPal',
            'binance': 'Binance', 'coinbase': 'Coinbase',
            'openai': 'OpenAI', 'chatgpt': 'ChatGPT'
        }
        name_lower = raw_name.lower().strip()
        return service_names.get(name_lower, raw_name.title() if raw_name else 'Unknown')
    
    def _get_service_icon(self, name: str) -> str:
        """Get icon for service"""
        icon_map = {
            'whatsapp': '💬', 'telegram': '📱', 'instagram': '📷',
            'facebook': '👤', 'twitter': '🐦', 'google': '🔍',
            'tiktok': '🎵', 'snapchat': '👻', 'discord': '🎮',
            'netflix': '🎬', 'spotify': '🎧', 'uber': '🚗',
            'amazon': '📦', 'paypal': '💳', 'binance': '💰',
            'coinbase': '🪙', 'openai': '🤖', 'chatgpt': '💭'
        }
        return icon_map.get(name.lower(), '📱')
    
    def get_price(self, country_id: str, service_id: str) -> Dict:
        """Get price for specific country and service"""
        result = self._make_request('getPrice', {
            'country': country_id,
            'service': service_id
        })
        if result['success']:
            try:
                if isinstance(result['data'], dict):
                    price = float(result['data'].get('price', 0))
                else:
                    price = float(result['data'])
                return {'success': True, 'price': price}
            except (ValueError, TypeError):
                return {'success': True, 'price': 0.0}
        return result
    
    def purchase_number(self, country_id: str, service_id: str) -> Dict:
        """Purchase a virtual number for receiving SMS"""
        result = self._make_request('getNumber', {
            'country': country_id,
            'service': service_id
        })
        
        if result['success']:
            data = result['data']
            
            if isinstance(data, str):
                if data.startswith('ACCESS_'):
                    parts = data.split(':')
                    return {
                        'success': True,
                        'order_id': parts[0].replace('ACCESS_', '') if len(parts) > 0 else data,
                        'phone_number': parts[1] if len(parts) > 1 else '',
                        'country': country_id,
                        'service': service_id
                    }
                return {'success': False, 'error': data}
            
            if isinstance(data, dict):
                if data.get('error'):
                    return {'success': False, 'error': data['error']}
                return {
                    'success': True,
                    'order_id': str(data.get('id', data.get('order_id', ''))),
                    'phone_number': data.get('number', data.get('phone', '')),
                    'country': data.get('country', country_id),
                    'service': data.get('service', service_id),
                    'cost': float(data.get('cost', data.get('price', 0))),
                    'expires_at': data.get('expires_at')
                }
            
            return {'success': False, 'error': 'Unexpected response format'}
        return result
    
    def check_sms(self, order_id: str) -> Dict:
        """Check if SMS has been received for an order"""
        result = self._make_request('getStatus', {'id': order_id})
        
        if result['success']:
            data = result['data']
            
            if isinstance(data, str):
                if data.startswith('STATUS_'):
                    status_map = {
                        'STATUS_WAIT_CODE': {'status': 'pending', 'sms_code': None},
                        'STATUS_WAIT_RETRY': {'status': 'pending', 'sms_code': None},
                        'STATUS_CANCEL': {'status': 'cancelled', 'sms_code': None}
                    }
                    if data in status_map:
                        return {'success': True, **status_map[data]}
                    
                    if data.startswith('STATUS_OK:'):
                        code = data.replace('STATUS_OK:', '').strip()
                        return {
                            'success': True,
                            'status': 'received',
                            'sms_code': code,
                            'full_sms': code
                        }
                
                return {'success': True, 'status': 'pending', 'sms_code': None}
            
            if isinstance(data, dict):
                status = data.get('status', '')
                if data.get('sms') or data.get('code'):
                    return {
                        'success': True,
                        'status': 'received',
                        'sms_code': data.get('sms') or data.get('code'),
                        'full_sms': data.get('full_sms', data.get('sms', ''))
                    }
                if status in ['pending', 'waiting', 'wait']:
                    return {'success': True, 'status': 'pending', 'sms_code': None}
                if status in ['cancelled', 'cancel', 'refunded']:
                    return {'success': True, 'status': 'cancelled', 'sms_code': None}
            
            return {'success': True, 'status': 'pending', 'sms_code': None}
        return result
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order and request refund"""
        result = self._make_request('cancelOrder', {'id': order_id})
        
        if result['success']:
            data = result['data']
            if isinstance(data, str):
                if 'SUCCESS' in data.upper() or 'CANCEL' in data.upper():
                    return {'success': True, 'refunded': True}
                return {'success': False, 'error': data}
            if isinstance(data, dict):
                if data.get('success') or data.get('status') == 'cancelled':
                    return {'success': True, 'refunded': True}
                return {'success': False, 'error': data.get('message', 'Cancel failed')}
            return {'success': True, 'refunded': True}
        return result
    
    def finish_order(self, order_id: str) -> Dict:
        """Mark order as finished after receiving SMS"""
        result = self._make_request('setStatus', {
            'id': order_id,
            'status': 6  # Standard status code for "finished"
        })
        return {'success': result['success']}
    
    def ban_number(self, order_id: str) -> Dict:
        """Report a number as not working"""
        result = self._make_request('setStatus', {
            'id': order_id,
            'status': 8  # Standard status code for "ban"
        })
        return {'success': result['success']}
    
    def calculate_user_price(self, provider_price: float, commission_percent: Optional[float] = None) -> Dict:
        """Calculate final price for user including commission"""
        if commission_percent is None:
            commission_percent = float(os.environ.get('SMS_COMMISSION_PERCENT', '30'))
        
        commission = provider_price * (commission_percent / 100)
        user_price = provider_price + commission
        
        return {
            'provider_price': round(provider_price, 2),
            'commission': round(commission, 2),
            'commission_percent': commission_percent,
            'user_price': round(user_price, 2)
        }


_legitsms_service: Optional[LegitSMSService] = None


def get_legitsms_service() -> LegitSMSService:
    """Get or create singleton instance of LegitSMSService"""
    global _legitsms_service
    if _legitsms_service is None:
        _legitsms_service = LegitSMSService()
    return _legitsms_service


class SMSProviderFallback:
    """
    Manages multiple SMS providers with automatic fallback.
    Primary: Legit SMS, Fallback: SMSPool
    """
    
    def __init__(self):
        self.legitsms = get_legitsms_service()
        try:
            from .smspool_service import SMSPoolService
            self.smspool = SMSPoolService()
        except ImportError:
            self.smspool = None
            logger.warning("SMSPool service not available for fallback")
    
    def get_provider_status(self) -> Dict:
        """Check which providers are available"""
        return {
            'legitsms': {
                'configured': self.legitsms.is_configured(),
                'primary': True
            },
            'smspool': {
                'configured': self.smspool is not None and self.smspool.api_key is not None,
                'primary': False
            }
        }
    
    def get_balance(self) -> Dict:
        """Get balance from primary provider, fallback if needed"""
        if self.legitsms.is_configured():
            result = self.legitsms.get_balance()
            if result['success']:
                result['provider'] = 'legitsms'
                return result
        
        if self.smspool and self.smspool.api_key:
            result = self.smspool.get_balance()
            if result['success']:
                result['provider'] = 'smspool'
                return result
        
        return {'success': False, 'error': 'No SMS provider configured'}
    
    def purchase_number(self, country_id: str, service_id: str) -> Dict:
        """Purchase number from primary provider, fallback if needed"""
        result = None
        
        if self.legitsms.is_configured():
            result = self.legitsms.purchase_number(country_id, service_id)
            if result['success']:
                result['provider'] = 'legitsms'
                return result
            logger.warning(f"Legit SMS purchase failed: {result.get('error')}, trying fallback")
        
        if self.smspool and self.smspool.api_key:
            result = self.smspool.purchase_number(country_id, service_id)
            if result['success']:
                result['provider'] = 'smspool'
                return result
        
        return result or {'success': False, 'error': 'No SMS provider available'}
    
    def check_sms(self, order_id: str, provider: str = 'legitsms') -> Dict:
        """Check SMS status from specified provider"""
        if provider == 'legitsms' and self.legitsms.is_configured():
            return self.legitsms.check_sms(order_id)
        if provider == 'smspool' and self.smspool:
            return self.smspool.check_sms(order_id)
        return {'success': False, 'error': 'Provider not available'}
    
    def cancel_order(self, order_id: str, provider: str = 'legitsms') -> Dict:
        """Cancel order from specified provider"""
        if provider == 'legitsms' and self.legitsms.is_configured():
            return self.legitsms.cancel_order(order_id)
        if provider == 'smspool' and self.smspool:
            return self.smspool.cancel_order(order_id)
        return {'success': False, 'error': 'Provider not available'}


_sms_fallback: Optional[SMSProviderFallback] = None


def get_sms_provider_fallback() -> SMSProviderFallback:
    """Get or create singleton instance of SMSProviderFallback"""
    global _sms_fallback
    if _sms_fallback is None:
        _sms_fallback = SMSProviderFallback()
    return _sms_fallback
