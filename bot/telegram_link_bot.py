"""
BUNK3R Telegram Link Bot
Bot para manejar el comando /vincular que permite vincular cuentas de Telegram con cuentas web.

Uso: python bot/telegram_link_bot.py
Requiere: BOT_TOKEN en variables de entorno

Fase 6.2 - 14 Diciembre 2025
"""

import os
import sys
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN no configurado")
    sys.exit(1)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEB_APP_URL = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
if not WEB_APP_URL.startswith('http'):
    WEB_APP_URL = f"https://{WEB_APP_URL}"


def send_message(chat_id, text, parse_mode='HTML'):
    """Envia un mensaje a traves del bot de Telegram."""
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None


def process_vincular_command(chat_id, telegram_id, args):
    """Procesa el comando /vincular."""
    if len(args) < 2:
        send_message(chat_id, """
<b>Uso del comando /vincular</b>

Para vincular tu cuenta de Telegram con tu cuenta web de BUNK3R:

1. Ve a Configuracion en la web
2. Haz clic en "Generar Codigo de Vinculacion"
3. Copia el codigo generado
4. Escribe aqui: <code>/vincular [codigo] [codigo_2fa]</code>

<b>Ejemplo:</b>
<code>/vincular abc123xyz 456789</code>

Donde:
- <code>abc123xyz</code> es tu codigo de vinculacion
- <code>456789</code> es tu codigo 2FA de la app autenticadora
""")
        return
    
    link_code = args[0]
    totp_code = args[1]
    
    if len(totp_code) != 6 or not totp_code.isdigit():
        send_message(chat_id, "El codigo 2FA debe tener 6 digitos numericos.")
        return
    
    send_message(chat_id, "Verificando codigo de vinculacion...")
    
    try:
        response = requests.post(
            f"{WEB_APP_URL}/api/telegram/link",
            json={
                'link_code': link_code,
                'telegram_id': telegram_id,
                'totp_code': totp_code,
                'bot_token': BOT_TOKEN
            },
            timeout=15
        )
        
        data = response.json()
        
        if data.get('success'):
            send_message(chat_id, """
<b>Vinculacion exitosa!</b>

Tu cuenta de Telegram ha sido vinculada correctamente a tu cuenta web de BUNK3R.

Ahora recibiras notificaciones importantes directamente en Telegram.
""")
            logger.info(f"Telegram {telegram_id} linked successfully")
        else:
            error = data.get('error', 'Error desconocido')
            send_message(chat_id, f"<b>Error:</b> {error}\n\nIntenta generar un nuevo codigo desde la web.")
            logger.warning(f"Link failed for {telegram_id}: {error}")
            
    except requests.exceptions.Timeout:
        send_message(chat_id, "Error: Tiempo de espera agotado. Intenta de nuevo.")
    except Exception as e:
        logger.error(f"Error processing link: {e}")
        send_message(chat_id, "Error al procesar la vinculacion. Intenta de nuevo mas tarde.")


def process_update(update):
    """Procesa una actualizacion de Telegram."""
    message = update.get('message', {})
    text = message.get('text', '')
    chat_id = message.get('chat', {}).get('id')
    user = message.get('from', {})
    telegram_id = user.get('id')
    
    if not chat_id or not text:
        return
    
    if text.startswith('/vincular'):
        args = text.split()[1:]
        process_vincular_command(chat_id, telegram_id, args)
    elif text.startswith('/start'):
        send_message(chat_id, """
<b>BUNK3R Bot</b>

Este bot te permite vincular tu cuenta de Telegram con tu cuenta web de BUNK3R.

<b>Comandos disponibles:</b>
/vincular [codigo] [2fa] - Vincula tu cuenta de Telegram
/ayuda - Muestra esta ayuda

Para vincular tu cuenta:
1. Ve a Configuracion en la web de BUNK3R
2. Genera un codigo de vinculacion
3. Usa /vincular con el codigo y tu 2FA
""")
    elif text.startswith('/ayuda') or text.startswith('/help'):
        send_message(chat_id, """
<b>Ayuda - BUNK3R Bot</b>

<b>/vincular [codigo] [codigo_2fa]</b>
Vincula tu cuenta de Telegram con tu cuenta web.
El codigo lo obtienes desde Configuracion > Vincular Telegram en la web.
El codigo_2fa es de tu app autenticadora.

<b>Ejemplo:</b>
<code>/vincular abc123xyz 456789</code>
""")


def run_polling():
    """Ejecuta el bot con polling."""
    logger.info("Starting BUNK3R Link Bot...")
    logger.info(f"Web App URL: {WEB_APP_URL}")
    
    offset = 0
    
    while True:
        try:
            response = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params={'offset': offset, 'timeout': 30},
                timeout=35
            )
            
            data = response.json()
            
            if not data.get('ok'):
                logger.error(f"Telegram API error: {data}")
                continue
            
            for update in data.get('result', []):
                offset = update['update_id'] + 1
                process_update(update)
                
        except requests.exceptions.Timeout:
            continue
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            continue


if __name__ == '__main__':
    run_polling()
