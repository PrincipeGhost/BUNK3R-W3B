"""
BUNK3R Telegram Notification Service
Servicio para enviar notificaciones al admin via Telegram Bot
"""

import os
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Servicio de notificaciones por Telegram para el panel admin."""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.environ.get('TELEGRAM_ADMIN_CHAT_ID')
        self._enabled = True
        self._notification_settings = {
            'large_purchase': {'enabled': True, 'threshold': 10.0},
            'pending_withdrawal': {'enabled': True, 'threshold': 0},
            'system_error': {'enabled': True, 'threshold': 0},
            'content_report': {'enabled': True, 'threshold': 0},
            'user_banned': {'enabled': True, 'threshold': 0},
            'low_balance': {'enabled': True, 'threshold': 50.0},
            'new_user': {'enabled': False, 'threshold': 0},
            'new_ticket': {'enabled': True, 'threshold': 0}
        }
    
    @property
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente."""
        return bool(self.bot_token and self.admin_chat_id)
    
    def _send_message(self, text: str, parse_mode: str = 'HTML') -> Dict[str, Any]:
        """Envía un mensaje a través del bot de Telegram."""
        if not self.is_configured:
            logger.warning("Telegram not configured - BOT_TOKEN or ADMIN_CHAT_ID missing")
            return {'success': False, 'error': 'Telegram not configured'}
        
        if not self._enabled:
            return {'success': False, 'error': 'Notifications disabled'}
        
        try:
            url = f"{self.BASE_URL}{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.admin_chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get('ok'):
                logger.info(f"Telegram notification sent successfully")
                return {'success': True, 'message_id': data['result']['message_id']}
            else:
                logger.error(f"Telegram API error: {data.get('description')}")
                return {'success': False, 'error': data.get('description', 'Unknown error')}
                
        except requests.exceptions.Timeout:
            logger.error("Telegram API timeout")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Telegram notification error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _should_notify(self, notification_type: str, value: float = 0) -> bool:
        """Verifica si debe enviarse la notificación según la configuración."""
        settings = self._notification_settings.get(notification_type, {})
        if not settings.get('enabled', False):
            return False
        threshold = settings.get('threshold', 0)
        if threshold > 0 and value < threshold:
            return False
        return True
    
    def notify_large_purchase(self, user_id: int, username: str, amount: float, currency: str = 'TON') -> Dict[str, Any]:
        """Notifica sobre una compra grande."""
        if not self._should_notify('large_purchase', amount):
            return {'success': False, 'error': 'Notification type disabled or below threshold'}
        
        message = f"""
💰 <b>COMPRA GRANDE</b>

👤 Usuario: <code>{username}</code> (ID: {user_id})
💵 Monto: <b>{amount:.2f} {currency}</b>
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔗 <a href="/admin#users">Ver en Panel Admin</a>
"""
        return self._send_message(message)
    
    def notify_pending_withdrawal(self, user_id: int, username: str, amount: float, currency: str = 'TON') -> Dict[str, Any]:
        """Notifica sobre un retiro pendiente de aprobación."""
        if not self._should_notify('pending_withdrawal'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        message = f"""
⏳ <b>RETIRO PENDIENTE</b>

👤 Usuario: <code>{username}</code> (ID: {user_id})
💵 Monto: <b>{amount:.2f} {currency}</b>
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ Requiere aprobación manual

🔗 <a href="/admin#transactions">Ver en Panel Admin</a>
"""
        return self._send_message(message)
    
    def notify_system_error(self, error_type: str, description: str, details: str = '') -> Dict[str, Any]:
        """Notifica sobre un error crítico del sistema."""
        if not self._should_notify('system_error'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        message = f"""
🚨 <b>ERROR CRÍTICO DEL SISTEMA</b>

⚠️ Tipo: <b>{error_type}</b>
📝 Descripción: {description}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        if details:
            message += f"\n📋 Detalles:\n<code>{details[:500]}</code>"
        
        message += "\n\n🔗 <a href=\"/admin#logs\">Ver Logs</a>"
        return self._send_message(message)
    
    def notify_content_report(self, reporter_id: int, content_id: int, reason: str) -> Dict[str, Any]:
        """Notifica sobre un nuevo reporte de contenido."""
        if not self._should_notify('content_report'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        message = f"""
🚩 <b>NUEVO REPORTE DE CONTENIDO</b>

📝 Contenido ID: <code>{content_id}</code>
👤 Reportado por: ID {reporter_id}
📌 Razón: {reason}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔗 <a href="/admin#reports">Ver Reportes</a>
"""
        return self._send_message(message)
    
    def notify_user_banned(self, user_id: int, username: str, reason: str, auto_ban: bool = False) -> Dict[str, Any]:
        """Notifica cuando un usuario es baneado."""
        if not self._should_notify('user_banned'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        ban_type = "AUTOMÁTICO" if auto_ban else "MANUAL"
        message = f"""
🔨 <b>USUARIO BANEADO ({ban_type})</b>

👤 Usuario: <code>{username}</code>
🆔 ID: {user_id}
📌 Razón: {reason}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔗 <a href="/admin#users">Ver en Panel Admin</a>
"""
        return self._send_message(message)
    
    def notify_low_balance(self, wallet_type: str, balance: float, currency: str = 'TON') -> Dict[str, Any]:
        """Notifica cuando el balance de una wallet está bajo."""
        if not self._should_notify('low_balance', balance):
            return {'success': False, 'error': 'Notification type disabled or above threshold'}
        
        message = f"""
💸 <b>BALANCE BAJO EN WALLET</b>

🏦 Wallet: <b>{wallet_type}</b>
💵 Balance actual: <b>{balance:.2f} {currency}</b>
⚠️ Se requiere recarga

📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔗 <a href="/admin#wallets">Ver Wallets</a>
"""
        return self._send_message(message)
    
    def notify_new_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """Notifica sobre un nuevo usuario registrado."""
        if not self._should_notify('new_user'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        message = f"""
👋 <b>NUEVO USUARIO</b>

👤 Usuario: <code>{username}</code>
🆔 ID: {user_id}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        return self._send_message(message)
    
    def notify_new_ticket(self, ticket_id: int, user_id: int, subject: str) -> Dict[str, Any]:
        """Notifica sobre un nuevo ticket de soporte."""
        if not self._should_notify('new_ticket'):
            return {'success': False, 'error': 'Notification type disabled'}
        
        message = f"""
📩 <b>NUEVO TICKET DE SOPORTE</b>

🎫 Ticket #: <b>{ticket_id}</b>
👤 Usuario ID: {user_id}
📌 Asunto: {subject[:100]}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔗 <a href="/admin#support">Ver Tickets</a>
"""
        return self._send_message(message)
    
    def send_test_message(self) -> Dict[str, Any]:
        """Envía un mensaje de prueba."""
        message = f"""
✅ <b>TEST DE NOTIFICACIONES BUNK3R</b>

Las notificaciones de Telegram están configuradas correctamente.

📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
🤖 Bot funcionando
"""
        return self._send_message(message)
    
    def send_custom_message(self, message: str) -> Dict[str, Any]:
        """Envía un mensaje personalizado."""
        return self._send_message(message)
    
    def get_settings(self) -> Dict[str, Any]:
        """Obtiene la configuración actual de notificaciones."""
        return {
            'enabled': self._enabled,
            'is_configured': self.is_configured,
            'has_bot_token': bool(self.bot_token),
            'has_chat_id': bool(self.admin_chat_id),
            'notification_types': self._notification_settings
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza la configuración de notificaciones."""
        if 'enabled' in settings:
            self._enabled = bool(settings['enabled'])
        
        if 'notification_types' in settings:
            for key, value in settings['notification_types'].items():
                if key in self._notification_settings:
                    if isinstance(value, dict):
                        self._notification_settings[key].update(value)
                    elif isinstance(value, bool):
                        self._notification_settings[key]['enabled'] = value
        
        return self.get_settings()
    
    def verify_bot(self) -> Dict[str, Any]:
        """Verifica que el bot esté funcionando correctamente."""
        if not self.bot_token:
            return {'success': False, 'error': 'Bot token not configured'}
        
        try:
            url = f"{self.BASE_URL}{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('ok'):
                bot_info = data['result']
                return {
                    'success': True,
                    'bot_name': bot_info.get('first_name'),
                    'bot_username': bot_info.get('username'),
                    'can_join_groups': bot_info.get('can_join_groups', False)
                }
            else:
                return {'success': False, 'error': data.get('description', 'Unknown error')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}


telegram_service = TelegramNotificationService()
