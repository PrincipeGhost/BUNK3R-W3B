"""
Blockchain Routes - Endpoints de B3C, Wallets, Transacciones TON, Exchange
Agente: Blockchain-Services
Rama: feature/blockchain-services

Este archivo contiene los endpoints relacionados con blockchain y wallets.
Endpoints migrados desde app.py.

Endpoints en este modulo:
- /api/b3c/* - Compra, venta, balance, transacciones
- /api/wallet/* - Conexion wallet, balance, creditos
- /api/ton/* - Pagos TON
- /api/exchange/* - Intercambio de criptomonedas (ChangeNow)
"""

import os
import re
import uuid
import logging
import requests
import psycopg2
import psycopg2.extras
import psycopg2.extensions

from flask import Blueprint, jsonify, request

from tracking.decorators import require_telegram_user, require_telegram_auth, require_owner
from tracking.utils import rate_limit, sanitize_error
from tracking.services import get_db_manager, IS_PRODUCTION

logger = logging.getLogger(__name__)

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='')

CHANGENOW_API_KEY = os.environ.get('CHANGENOW_API_KEY', '')
CHANGENOW_BASE_URL = 'https://api.changenow.io/v1'

TONCENTER_API_URL = 'https://toncenter.com/api/v3'
MERCHANT_TON_WALLET = os.environ.get('TON_WALLET_ADDRESS', 'UQA5l6-8ka5wsyOhn8S7qcXWESgvPJgOBC3wsOVBnxm87Bck')

TON_CREDIT_RATES = {
    1: 10,
    2: 22,
    5: 60,
    10: 130,
    20: 280,
    50: 750,
}


def calculate_credits_from_ton(ton_amount):
    """Calcula BUNK3RCO1N basado en TON con tasa del servidor."""
    ton_amount = float(ton_amount)
    if ton_amount in TON_CREDIT_RATES:
        return TON_CREDIT_RATES[ton_amount]
    credits = int(ton_amount * 10)
    if ton_amount >= 10:
        credits = int(credits * 1.3)
    elif ton_amount >= 5:
        credits = int(credits * 1.2)
    elif ton_amount >= 2:
        credits = int(credits * 1.1)
    return max(credits, 1)


@blockchain_bp.route('/api/blockchain/health', methods=['GET'])
def blockchain_health():
    """Health check del modulo blockchain."""
    return jsonify({
        'success': True,
        'module': 'blockchain_routes',
        'status': 'active',
        'endpoints_migrated': [
            '/api/exchange/*',
            '/api/ton/*',
            '/api/wallet/*',
            '/api/b3c/*'
        ]
    })


@blockchain_bp.route('/api/exchange/currencies', methods=['GET'])
@require_telegram_user
@rate_limit('exchange')
def get_exchange_currencies():
    """Obtener lista de criptomonedas disponibles."""
    try:
        if not CHANGENOW_API_KEY:
            return jsonify({'error': 'API key no configurada'}), 500
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/currencies',
            params={'active': 'true', 'fixedRate': 'true'},
            timeout=10
        )
        
        if response.status_code == 200:
            currencies = response.json()
            popular = ['btc', 'eth', 'usdt', 'ltc', 'xrp', 'doge', 'bnb', 'sol', 'trx', 'matic']
            sorted_currencies = sorted(currencies, key=lambda x: (x['ticker'].lower() not in popular, x['ticker'].lower()))
            return jsonify({'success': True, 'currencies': sorted_currencies})
        else:
            return jsonify({'error': 'Error al obtener monedas'}), 500
            
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@blockchain_bp.route('/api/exchange/min-amount', methods=['GET'])
@require_telegram_user
def get_min_amount():
    """Obtener monto minimo para intercambio."""
    try:
        from_currency = request.args.get('from', '').lower()
        to_currency = request.args.get('to', '').lower()
        
        if not from_currency or not to_currency:
            return jsonify({'error': 'Monedas requeridas'}), 400
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/min-amount/{from_currency}_{to_currency}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({'success': True, 'minAmount': data.get('minAmount')})
        else:
            return jsonify({'error': 'Error al obtener monto minimo'}), 500
            
    except Exception as e:
        logger.error(f"Error getting min amount: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@blockchain_bp.route('/api/exchange/estimate', methods=['GET'])
@require_telegram_user
def get_exchange_estimate():
    """Obtener estimacion de intercambio."""
    try:
        from_currency = request.args.get('from', '').lower()
        to_currency = request.args.get('to', '').lower()
        amount = request.args.get('amount', '')
        
        if not from_currency or not to_currency or not amount:
            return jsonify({'error': 'Parametros requeridos'}), 400
        
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/exchange-amount/{amount}/{from_currency}_{to_currency}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'estimatedAmount': data.get('estimatedAmount'),
                'transactionSpeedForecast': data.get('transactionSpeedForecast'),
                'warningMessage': data.get('warningMessage')
            })
        else:
            error_data = response.json() if response.content else {}
            return jsonify({'error': error_data.get('message', 'Error al estimar')}), 400
            
    except Exception as e:
        logger.error(f"Error getting estimate: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@blockchain_bp.route('/api/exchange/create', methods=['POST'])
@require_telegram_user
def create_exchange():
    """Crear una transaccion de intercambio."""
    try:
        data = request.get_json()
        
        from_currency = data.get('from', '').lower()
        to_currency = data.get('to', '').lower()
        amount = data.get('amount')
        address = data.get('address')
        refund_address = data.get('refundAddress', '')
        
        if not all([from_currency, to_currency, amount, address]):
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        payload = {
            'from': from_currency,
            'to': to_currency,
            'amount': float(amount),
            'address': address,
            'refundAddress': refund_address,
            'api_key': CHANGENOW_API_KEY
        }
        
        response = requests.post(
            f'{CHANGENOW_BASE_URL}/transactions',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            tx_data = response.json()
            return jsonify({
                'success': True,
                'id': tx_data.get('id'),
                'payinAddress': tx_data.get('payinAddress'),
                'payoutAddress': tx_data.get('payoutAddress'),
                'fromCurrency': tx_data.get('fromCurrency'),
                'toCurrency': tx_data.get('toCurrency'),
                'amount': tx_data.get('amount'),
                'payinExtraId': tx_data.get('payinExtraId')
            })
        else:
            error_data = response.json() if response.content else {}
            return jsonify({'error': error_data.get('message', 'Error al crear transaccion')}), 400
            
    except Exception as e:
        logger.error(f"Error creating exchange: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@blockchain_bp.route('/api/exchange/status/<tx_id>', methods=['GET'])
@require_telegram_user
def get_exchange_status(tx_id):
    """Obtener estado de una transaccion."""
    try:
        response = requests.get(
            f'{CHANGENOW_BASE_URL}/transactions/{tx_id}',
            params={'api_key': CHANGENOW_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'status': data.get('status'),
                'payinHash': data.get('payinHash'),
                'payoutHash': data.get('payoutHash'),
                'amountFrom': data.get('amountFrom'),
                'amountTo': data.get('amountTo'),
                'fromCurrency': data.get('fromCurrency'),
                'toCurrency': data.get('toCurrency')
            })
        else:
            return jsonify({'error': 'Transaccion no encontrada'}), 404
            
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@blockchain_bp.route('/api/ton/payment/create', methods=['POST'])
@require_telegram_user
def create_ton_payment():
    """Crear una solicitud de pago pendiente."""
    try:
        data = request.get_json()
        ton_amount = data.get('tonAmount', 0)
        
        if not ton_amount or float(ton_amount) <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        ton_amount = float(ton_amount)
        if ton_amount < 0.5:
            return jsonify({'success': False, 'error': 'Monto minimo: 0.5 TON'}), 400
        if ton_amount > 1000:
            return jsonify({'success': False, 'error': 'Monto maximo: 1000 TON'}), 400
        
        credits = calculate_credits_from_ton(ton_amount)
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        payment_id = str(uuid.uuid4())[:8].upper()
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'paymentId': payment_id,
                'tonAmount': ton_amount,
                'credits': credits,
                'walletAddress': MERCHANT_TON_WALLET,
                'memo': payment_id
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ton_payments (payment_id, user_id, ton_amount, credits, status, created_at)
                    VALUES (%s, %s, %s, %s, 'pending', NOW())
                """, (payment_id, user_id, ton_amount, credits))
                conn.commit()
        
        return jsonify({
            'success': True,
            'paymentId': payment_id,
            'tonAmount': ton_amount,
            'credits': credits,
            'walletAddress': MERCHANT_TON_WALLET,
            'memo': payment_id
        })
        
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return jsonify({'success': False, 'error': 'Error al crear pago'}), 500


@blockchain_bp.route('/api/ton/wallet-info', methods=['GET'])
def get_ton_wallet_info():
    """Obtener informacion de la wallet del comercio."""
    return jsonify({
        'success': True,
        'address': MERCHANT_TON_WALLET,
        'network': 'mainnet'
    })


@blockchain_bp.route('/api/wallet/merchant', methods=['GET'])
def get_merchant_wallet():
    """Obtener wallet del comercio para depositos."""
    return jsonify({
        'success': True,
        'address': MERCHANT_TON_WALLET
    })


@blockchain_bp.route('/api/wallet/balance', methods=['GET'])
@require_telegram_user
def get_wallet_balance():
    """Obtener el saldo de BUNK3RCO1N del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'balance': 0})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                balance = result[0] if result else 0
                
        return jsonify({'success': True, 'balance': float(balance)})
        
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return jsonify({'success': True, 'balance': 0})


@blockchain_bp.route('/api/wallet/connect', methods=['POST'])
@require_telegram_user
def connect_wallet():
    """Conectar/guardar direccion de wallet TON del usuario."""
    try:
        data = request.get_json()
        wallet_address = data.get('address', '').strip()
        
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Direccion requerida'}), 400
        
        if not (wallet_address.startswith('EQ') or wallet_address.startswith('UQ') or 
                wallet_address.startswith('0:') or wallet_address.startswith('kQ')):
            return jsonify({'success': False, 'error': 'Direccion TON invalida'}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'message': 'Wallet guardada (demo)'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET wallet_address = %s WHERE telegram_id = %s
                """, (wallet_address, user_id))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Wallet conectada'})
        
    except Exception as e:
        logger.error(f"Error connecting wallet: {e}")
        return jsonify({'success': False, 'error': 'Error al conectar wallet'}), 500


@blockchain_bp.route('/api/wallet/address', methods=['GET'])
@require_telegram_user
def get_wallet_address():
    """Obtener la direccion de wallet guardada del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'address': None})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT wallet_address FROM users WHERE telegram_id = %s
                """, (user_id,))
                result = cur.fetchone()
                address = result[0] if result else None
                
        return jsonify({'success': True, 'address': address})
        
    except Exception as e:
        logger.error(f"Error getting wallet address: {e}")
        return jsonify({'success': True, 'address': None})


@blockchain_bp.route('/api/b3c/price', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_price():
    """Obtener precio actual del token B3C."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        price_data = b3c.get_b3c_price()
        return jsonify(price_data)
    except Exception as e:
        logger.error(f"Error getting B3C price: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener precio'}), 500


@blockchain_bp.route('/api/b3c/calculate/buy', methods=['POST'])
@rate_limit('calculate', use_ip=True)
def calculate_b3c_buy():
    """Calcular cuantos B3C recibe el usuario por X TON."""
    try:
        data = request.get_json()
        ton_amount = float(data.get('tonAmount', 0))
        
        if ton_amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if ton_amount < 0.1:
            return jsonify({'success': False, 'error': 'Minimo 0.1 TON'}), 400
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        result = b3c.calculate_b3c_from_ton(ton_amount)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calculating B3C: {e}")
        return jsonify({'success': False, 'error': 'Error en calculo'}), 500


@blockchain_bp.route('/api/b3c/calculate/sell', methods=['POST'])
@rate_limit('calculate', use_ip=True)
def calculate_b3c_sell():
    """Calcular cuantos TON recibe el usuario por X B3C."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        
        if b3c_amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        result = b3c.calculate_ton_from_b3c(b3c_amount)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calculating TON: {e}")
        return jsonify({'success': False, 'error': 'Error en calculo'}), 500


@blockchain_bp.route('/api/b3c/balance', methods=['GET'])
@rate_limit('balance_check', use_ip=True)
def get_b3c_balance():
    """Obtener balance de B3C del usuario desde compras confirmadas y retiros."""
    try:
        user_id = '0'
        if hasattr(request, 'telegram_user') and request.telegram_user:
            user_id = str(request.telegram_user.get('id', 0))
        elif request.headers.get('X-Demo-Mode') == 'true' and not IS_PRODUCTION:
            user_id = '0'
        else:
            init_data = request.headers.get('X-Telegram-Init-Data', '')
            if init_data:
                from urllib.parse import parse_qs
                import json
                parsed = parse_qs(init_data)
                if 'user' in parsed:
                    user_data = json.loads(parsed['user'][0])
                    user_id = str(user_data.get('id', 0))
        
        b3c_balance = 0.0
        db_manager = get_db_manager()
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(SUM(b3c_amount), 0) as total_purchased
                        FROM b3c_purchases 
                        WHERE user_id = %s AND status = 'confirmed'
                    """, (user_id,))
                    purchased = cur.fetchone()
                    total_purchased = float(purchased[0]) if purchased and purchased[0] else 0
                    
                    cur.execute("""
                        SELECT COALESCE(SUM(b3c_amount), 0) as total_withdrawn
                        FROM b3c_withdrawals 
                        WHERE user_id = %s AND status = 'completed'
                    """, (user_id,))
                    withdrawn = cur.fetchone()
                    total_withdrawn = float(withdrawn[0]) if withdrawn and withdrawn[0] else 0
                    
                    b3c_balance = total_purchased - total_withdrawn
        
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        price_data = b3c.get_b3c_price()
        
        price_ton = price_data.get('price_ton', 0.001)
        price_usd = price_data.get('price_usd', 0.005)
        
        return jsonify({
            'success': True,
            'balance': b3c_balance,
            'balance_formatted': f"{b3c_balance:,.2f}",
            'value_ton': b3c_balance * price_ton,
            'value_usd': b3c_balance * price_usd,
            'price_per_b3c_ton': price_ton,
            'price_per_b3c_usd': price_usd,
            'is_testnet': b3c.use_testnet
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C balance: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener balance', 'balance': 0}), 500


@blockchain_bp.route('/api/b3c/config', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_config():
    """Obtener configuracion del servicio B3C."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify({
            'success': True,
            'config': b3c.get_service_config()
        })
    except Exception as e:
        logger.error(f"Error getting B3C config: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener configuracion'}), 500


@blockchain_bp.route('/api/b3c/network', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_b3c_network_status():
    """Verificar estado de la red TON."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify(b3c.get_network_status())
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar red'}), 500


@blockchain_bp.route('/api/b3c/testnet/guide', methods=['GET'])
@rate_limit('price_check', use_ip=True)
def get_testnet_setup_guide():
    """Obtener guia de configuracion para testnet."""
    try:
        from tracking.b3c_service import get_b3c_service
        b3c = get_b3c_service()
        return jsonify({
            'success': True,
            'guide': b3c.get_testnet_setup_guide()
        })
    except Exception as e:
        logger.error(f"Error getting testnet guide: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener guia'}), 500


def validate_ton_address(address):
    """Validate TON wallet address format server-side."""
    if not address or not isinstance(address, str):
        return False, 'Direccion de wallet requerida'
    
    address = address.strip()
    
    if len(address) != 48:
        return False, 'La direccion debe tener 48 caracteres'
    
    prefix = address[:2]
    if prefix not in ['EQ', 'UQ']:
        return False, 'Direccion invalida. Debe empezar con EQ o UQ'
    
    if not re.match(r'^[A-Za-z0-9_-]+$', address):
        return False, 'La direccion contiene caracteres invalidos'
    
    return True, None


@blockchain_bp.route('/api/b3c/buy/create', methods=['POST'])
@require_telegram_user
def create_b3c_purchase():
    """Crear solicitud de compra de B3C con wallet unica de deposito."""
    try:
        data = request.get_json()
        ton_amount = float(data.get('tonAmount', 0))
        
        if ton_amount < 0.1:
            return jsonify({'success': False, 'error': 'Minimo 0.1 TON'}), 400
        if ton_amount > 1000:
            return jsonify({'success': False, 'error': 'Maximo 1000 TON'}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        purchase_id = str(uuid.uuid4())[:8].upper()
        
        from tracking.b3c_service import get_b3c_service
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        b3c = get_b3c_service()
        calculation = b3c.calculate_b3c_from_ton(ton_amount)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'purchaseId': purchase_id,
                'calculation': calculation,
                'depositAddress': 'DEMO_WALLET_ADDRESS',
                'message': 'Demo mode'
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO b3c_purchases (purchase_id, user_id, ton_amount, b3c_amount, 
                                               commission_ton, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
                """, (purchase_id, user_id, ton_amount, calculation['b3c_amount'], 
                      calculation['commission_ton']))
                conn.commit()
        
        wallet_pool = get_wallet_pool_service(db_manager)
        wallet_assignment = wallet_pool.assign_wallet_for_purchase(user_id, ton_amount, purchase_id)
        
        if not wallet_assignment or not wallet_assignment.get('success'):
            return jsonify({
                'success': False,
                'error': 'No hay wallets disponibles. Intenta de nuevo.'
            }), 503
        
        return jsonify({
            'success': True,
            'purchaseId': purchase_id,
            'calculation': calculation,
            'depositAddress': wallet_assignment['deposit_address'],
            'amountToSend': wallet_assignment['amount_to_send'],
            'expiresAt': wallet_assignment['expires_at'],
            'expiresInMinutes': wallet_assignment['expires_in_minutes'],
            'useUniqueWallet': True,
            'instructions': [
                f"Envia exactamente {ton_amount} TON a la direccion indicada",
                "Esta direccion es unica para esta compra",
                f"Tienes {wallet_assignment['expires_in_minutes']} minutos para completar el pago",
                "Los B3C se acreditaran automaticamente al detectar el pago"
            ]
        })
        
    except Exception as e:
        logger.error(f"Error creating B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al crear compra'}), 500


@blockchain_bp.route('/api/b3c/buy/<purchase_id>/verify', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_verify')
def verify_b3c_purchase(purchase_id):
    """Verificar si un pago de compra B3C fue recibido usando wallet unica."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'status': 'confirmed', 'message': 'Demo mode'})
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_purchases 
                    WHERE purchase_id = %s AND user_id = %s
                """, (purchase_id, user_id))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                if purchase['status'] == 'confirmed':
                    return jsonify({'success': True, 'status': 'confirmed', 
                                    'b3c_credited': float(purchase['b3c_amount'])})
        
        wallet_pool = get_wallet_pool_service(db_manager)
        deposit_check = wallet_pool.check_deposit(purchase_id)
        
        if not deposit_check.get('success'):
            return jsonify({
                'success': False,
                'error': deposit_check.get('error', 'Error verificando deposito')
            }), 500
        
        status = deposit_check.get('status')
        
        if status == 'confirmed':
            return jsonify({
                'success': True,
                'status': 'confirmed',
                'b3c_credited': float(purchase['b3c_amount']),
                'tx_hash': deposit_check.get('tx_hash'),
                'amount_received': deposit_check.get('amount_received')
            })
        
        if status == 'expired':
            return jsonify({
                'success': True,
                'status': 'expired',
                'message': 'El tiempo para esta compra expiro. Crea una nueva compra.'
            })
        
        return jsonify({
            'success': True,
            'status': 'pending',
            'message': 'Esperando confirmacion de deposito',
            'deposit_address': deposit_check.get('deposit_address'),
            'expected_amount': deposit_check.get('expected_amount'),
            'expires_at': deposit_check.get('expires_at')
        })
                
    except Exception as e:
        logger.error(f"Error verifying B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar compra'}), 500


@blockchain_bp.route('/api/b3c/transactions', methods=['GET'])
@require_telegram_user
def get_b3c_transactions():
    """Obtener historial de transacciones B3C del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'transactions': [], 'total': 0})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, amount, transaction_type, description, reference_id, created_at
                    FROM wallet_transactions 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))
                transactions = cur.fetchall()
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions WHERE user_id = %s", (user_id,))
                total = cur.fetchone()['count']
                
        return jsonify({
            'success': True,
            'transactions': [{
                'id': tx['id'],
                'amount': float(tx['amount']),
                'type': tx['transaction_type'],
                'description': tx['description'],
                'reference': tx['reference_id'],
                'date': tx['created_at'].isoformat() if tx['created_at'] else None
            } for tx in transactions],
            'total': total,
            'has_more': offset + limit < total
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C transactions: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener transacciones'}), 500


@blockchain_bp.route('/api/b3c/transfer', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_transfer')
def transfer_b3c():
    """Transferir B3C a otro usuario."""
    try:
        data = request.get_json()
        to_username = data.get('toUsername', '').strip().lstrip('@')
        to_user_id = data.get('toUserId', '').strip()
        b3c_amount = float(data.get('amount', 0))
        note = data.get('note', '').strip()[:255]
        
        if b3c_amount < 1:
            return jsonify({'success': False, 'error': 'Minimo 1 B3C para transferir'}), 400
        if b3c_amount > 1000000:
            return jsonify({'success': False, 'error': 'Maximo 1,000,000 B3C por transferencia'}), 400
        
        from_user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        from_username = request.telegram_user.get('username', '') if hasattr(request, 'telegram_user') else ''
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if to_username and not to_user_id:
                    cur.execute("""
                        SELECT user_id, username, first_name FROM users WHERE LOWER(username) = LOWER(%s)
                    """, (to_username,))
                    to_user = cur.fetchone()
                    if not to_user:
                        return jsonify({'success': False, 'error': f'Usuario @{to_username} no encontrado'}), 404
                    to_user_id = to_user['user_id']
                    to_display_name = to_user['username'] or to_user['first_name']
                elif to_user_id:
                    cur.execute("""
                        SELECT user_id, username, first_name FROM users WHERE user_id = %s
                    """, (to_user_id,))
                    to_user = cur.fetchone()
                    if not to_user:
                        return jsonify({'success': False, 'error': 'Usuario destino no encontrado'}), 404
                    to_display_name = to_user['username'] or to_user['first_name']
                else:
                    return jsonify({'success': False, 'error': 'Debes especificar usuario destino'}), 400
                
                if str(from_user_id) == str(to_user_id):
                    return jsonify({'success': False, 'error': 'No puedes transferirte a ti mismo'}), 400
                
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (from_user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    conn.rollback()
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                transfer_id = str(uuid.uuid4())[:8].upper()
                
                cur.execute("""
                    INSERT INTO b3c_transfers (transfer_id, from_user_id, to_user_id, b3c_amount, note, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'completed', NOW())
                """, (transfer_id, from_user_id, to_user_id, b3c_amount, note))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (from_user_id, b3c_amount, f'Enviado a @{to_display_name}', transfer_id))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'credit', %s, %s, NOW())
                """, (to_user_id, b3c_amount, f'Recibido de @{from_username}', transfer_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'transfer_id': transfer_id,
                    'amount': b3c_amount,
                    'to_user': to_display_name,
                    'message': f'Transferencia exitosa de {b3c_amount} B3C a @{to_display_name}'
                })
                
    except Exception as e:
        logger.error(f"Error transferring B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al transferir B3C'}), 500


@blockchain_bp.route('/api/b3c/sell', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_sell')
def sell_b3c():
    """Vender B3C por TON. El usuario recibe TON menos comision."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        destination_wallet = data.get('destinationWallet', '').strip()
        
        if b3c_amount < 100:
            return jsonify({'success': False, 'error': 'Minimo 100 B3C para vender'}), 400
        if b3c_amount > 1000000:
            return jsonify({'success': False, 'error': 'Maximo 1,000,000 B3C por venta'}), 400
        
        is_valid, error_msg = validate_ton_address(destination_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                from tracking.b3c_service import get_b3c_service
                b3c = get_b3c_service()
                calculation = b3c.calculate_ton_from_b3c(b3c_amount)
                
                sell_id = str(uuid.uuid4())[:8].upper()
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (user_id, b3c_amount, f'Venta B3C - {calculation["net_ton"]:.4f} TON', sell_id))
                
                cur.execute("""
                    INSERT INTO b3c_commissions 
                    (user_id, operation_type, b3c_amount, ton_amount, commission_ton, reference_id, created_at)
                    VALUES (%s, 'sell', %s, %s, %s, %s, NOW())
                """, (user_id, b3c_amount, calculation['net_ton'], calculation['commission_ton'], sell_id))
                
                conn.commit()
                
        return jsonify({
            'success': True,
            'sellId': sell_id,
            'b3cSold': b3c_amount,
            'tonReceived': calculation['net_ton'],
            'commission': calculation['commission_ton'],
            'destinationWallet': destination_wallet,
            'status': 'processing',
            'message': f'Venta procesada. Recibiras {calculation["net_ton"]:.4f} TON en tu wallet.'
        })
        
    except Exception as e:
        logger.error(f"Error selling B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al procesar venta'}), 500


@blockchain_bp.route('/api/b3c/withdraw', methods=['POST'])
@require_telegram_user
@rate_limit('b3c_withdraw')
def withdraw_b3c():
    """Retirar B3C a una wallet externa."""
    try:
        data = request.get_json()
        b3c_amount = float(data.get('b3cAmount', 0))
        destination_wallet = data.get('destinationWallet', '').strip()
        
        if b3c_amount < 100:
            return jsonify({'success': False, 'error': 'Minimo 100 B3C para retirar'}), 400
        if b3c_amount > 100000:
            return jsonify({'success': False, 'error': 'Maximo 100,000 B3C por retiro diario'}), 400
        
        is_valid, error_msg = validate_ton_address(destination_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conn.set_session(isolation_level='SERIALIZABLE')
                
                cur.execute("""
                    SELECT COALESCE(
                        (SELECT SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) 
                         FROM wallet_transactions WHERE user_id = %s FOR UPDATE), 0
                    ) as balance
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result['balance']) if result else 0
                
                if current_balance < b3c_amount:
                    return jsonify({
                        'success': False, 
                        'error': f'Saldo insuficiente. Tienes {current_balance:.2f} B3C'
                    }), 400
                
                cur.execute("""
                    SELECT COUNT(*) as count FROM b3c_withdrawals 
                    WHERE user_id = %s AND created_at > NOW() - INTERVAL '1 hour'
                """, (user_id,))
                recent = cur.fetchone()
                if recent and recent['count'] >= 3:
                    return jsonify({
                        'success': False, 
                        'error': 'Limite de retiros alcanzado. Espera 1 hora.'
                    }), 429
                
                withdrawal_id = str(uuid.uuid4())[:8].upper()
                withdrawal_fee = 0.5
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'debit', %s, %s, NOW())
                """, (user_id, b3c_amount, f'Retiro B3C a {destination_wallet[:8]}...', withdrawal_id))
                
                cur.execute("""
                    INSERT INTO b3c_withdrawals 
                    (withdrawal_id, user_id, b3c_amount, destination_wallet, status, created_at)
                    VALUES (%s, %s, %s, %s, 'pending', NOW())
                """, (withdrawal_id, user_id, b3c_amount, destination_wallet))
                
                cur.execute("""
                    INSERT INTO b3c_commissions 
                    (user_id, operation_type, b3c_amount, ton_amount, commission_ton, reference_id, created_at)
                    VALUES (%s, 'withdraw', %s, 0, %s, %s, NOW())
                """, (user_id, b3c_amount, withdrawal_fee, withdrawal_id))
                
                conn.commit()
                
        return jsonify({
            'success': True,
            'withdrawalId': withdrawal_id,
            'b3cAmount': b3c_amount,
            'destinationWallet': destination_wallet,
            'networkFee': withdrawal_fee,
            'status': 'pending',
            'estimatedTime': '5-15 minutos',
            'message': f'Retiro de {b3c_amount:,.0f} B3C iniciado. Llegara a tu wallet en 5-15 minutos.'
        })
        
    except Exception as e:
        logger.error(f"Error withdrawing B3C: {e}")
        return jsonify({'success': False, 'error': 'Error al procesar retiro'}), 500


@blockchain_bp.route('/api/b3c/withdraw/<withdrawal_id>/status', methods=['GET'])
@require_telegram_user
def get_withdrawal_status(withdrawal_id):
    """Obtener estado de un retiro."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_withdrawals 
                    WHERE withdrawal_id = %s AND user_id = %s
                """, (withdrawal_id, user_id))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
                
        return jsonify({
            'success': True,
            'withdrawal': {
                'id': withdrawal['withdrawal_id'],
                'amount': float(withdrawal['b3c_amount']),
                'destination': withdrawal['destination_wallet'],
                'status': withdrawal['status'],
                'txHash': withdrawal.get('tx_hash'),
                'createdAt': withdrawal['created_at'].isoformat() if withdrawal['created_at'] else None,
                'processedAt': withdrawal['processed_at'].isoformat() if withdrawal.get('processed_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting withdrawal status: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estado'}), 500


@blockchain_bp.route('/api/b3c/deposit/address', methods=['GET'])
@require_telegram_user
def get_deposit_address():
    """Crear deposito externo con wallet unica del pool."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        purchase_id = str(uuid.uuid4())[:8].upper()
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        
        db_manager = get_db_manager()
        if not db_manager:
            hot_wallet = os.environ.get('TON_WALLET_ADDRESS', '')
            return jsonify({
                'success': True,
                'depositAddress': hot_wallet,
                'depositMemo': f'DEP-{user_id[:8]}',
                'instructions': ['Demo mode - deposito simulado'],
                'minimumDeposit': 0.1,
                'notice': 'Modo demo'
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO b3c_purchases (purchase_id, user_id, ton_amount, b3c_amount, 
                                               commission_ton, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
                """, (purchase_id, user_id, 0, 0, 0))
                conn.commit()
        
        wallet_pool = get_wallet_pool_service(db_manager)
        wallet_assignment = wallet_pool.assign_wallet_for_purchase(user_id, 0, purchase_id)
        
        if not wallet_assignment or not wallet_assignment.get('success'):
            return jsonify({
                'success': False,
                'error': 'No hay wallets disponibles. Intenta de nuevo.'
            }), 503
        
        return jsonify({
            'success': True,
            'depositAddress': wallet_assignment['deposit_address'],
            'depositMemo': f'EXT-{purchase_id}',
            'purchaseId': purchase_id,
            'expiresAt': wallet_assignment['expires_at'],
            'expiresInMinutes': wallet_assignment['expires_in_minutes'],
            'instructions': [
                'Envia TON a la direccion indicada',
                'Esta direccion es unica para este deposito',
                f"Tienes {wallet_assignment['expires_in_minutes']} minutos para completar",
                'El deposito se detectara automaticamente',
                'Minimo: 0.1 TON'
            ],
            'minimumDeposit': 0.1,
            'notice': 'Esta wallet es unica para ti. Los fondos se acreditaran automaticamente.'
        })
        
    except Exception as e:
        logger.error(f"Error getting deposit address: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener direccion'}), 500


@blockchain_bp.route('/api/b3c/commissions', methods=['GET'])
@require_telegram_user
def get_b3c_commissions():
    """Obtener resumen de comisiones B3C (solo admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'commissions': [], 'totals': {}})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        operation_type,
                        COUNT(*) as count,
                        SUM(b3c_amount) as total_b3c,
                        SUM(ton_amount) as total_ton,
                        SUM(commission_ton) as total_commission
                    FROM b3c_commissions
                    GROUP BY operation_type
                """)
                by_type = cur.fetchall()
                
                cur.execute("""
                    SELECT SUM(commission_ton) as total FROM b3c_commissions
                """)
                total_result = cur.fetchone()
                total_commissions = float(total_result['total']) if total_result and total_result['total'] else 0
                
                cur.execute("""
                    SELECT * FROM b3c_commissions 
                    ORDER BY created_at DESC LIMIT 50
                """)
                recent = cur.fetchall()
                
        return jsonify({
            'success': True,
            'totals': {
                'totalCommissionsTon': total_commissions,
                'byType': [{
                    'type': row['operation_type'],
                    'count': row['count'],
                    'totalB3c': float(row['total_b3c']) if row['total_b3c'] else 0,
                    'totalTon': float(row['total_ton']) if row['total_ton'] else 0,
                    'totalCommission': float(row['total_commission']) if row['total_commission'] else 0
                } for row in by_type]
            },
            'recentTransactions': [{
                'id': row['id'],
                'userId': row['user_id'],
                'type': row['operation_type'],
                'b3c': float(row['b3c_amount']) if row['b3c_amount'] else 0,
                'ton': float(row['ton_amount']) if row['ton_amount'] else 0,
                'commission': float(row['commission_ton']) if row['commission_ton'] else 0,
                'date': row['created_at'].isoformat() if row['created_at'] else None
            } for row in recent]
        })
        
    except Exception as e:
        logger.error(f"Error getting commissions: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener comisiones'}), 500


@blockchain_bp.route('/api/b3c/scheduler/status', methods=['GET'])
@require_telegram_user
def get_scheduler_status():
    """Obtener estado del scheduler de depositos automaticos (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        from tracking.deposit_scheduler import get_deposit_scheduler
        db_manager = get_db_manager()
        deposit_scheduler = get_deposit_scheduler(db_manager) if db_manager else None
        
        if deposit_scheduler:
            return jsonify({
                'success': True,
                'scheduler': deposit_scheduler.get_status(),
                'message': 'Scheduler de depositos automaticos activo'
            })
        else:
            return jsonify({
                'success': True,
                'scheduler': {'running': False},
                'message': 'Scheduler no inicializado'
            })
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@blockchain_bp.route('/api/b3c/wallet-pool/stats', methods=['GET'])
@require_telegram_user
def get_wallet_pool_stats():
    """Obtener estadisticas del pool de wallets de deposito (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'stats': {'available': 0, 'total': 0}})
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        return jsonify(wallet_pool.get_pool_stats())
        
    except Exception as e:
        logger.error(f"Error getting wallet pool stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadisticas'}), 500


@blockchain_bp.route('/api/b3c/wallet-pool/fill', methods=['POST'])
@require_telegram_user
def fill_wallet_pool():
    """Rellenar el pool de wallets de deposito (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        data = request.get_json() or {}
        min_size = int(data.get('minSize', 10))
        
        added = wallet_pool.ensure_minimum_pool_size(min_size)
        stats = wallet_pool.get_pool_stats()
        
        return jsonify({
            'success': True,
            'walletsAdded': added,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error filling wallet pool: {e}")
        return jsonify({'success': False, 'error': 'Error al rellenar pool'}), 500


@blockchain_bp.route('/api/b3c/wallet-pool/consolidate', methods=['POST'])
@require_telegram_user
def consolidate_wallets():
    """Consolidar fondos de wallets con depositos a hot wallet (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        consolidated = wallet_pool.consolidate_confirmed_deposits()
        released = wallet_pool.release_expired_wallets()
        
        return jsonify({
            'success': True,
            'walletsConsolidated': consolidated,
            'expiredReleased': released,
            'message': f'Consolidados: {consolidated}, Liberados: {released}'
        })
        
    except Exception as e:
        logger.error(f"Error consolidating wallets: {e}")
        return jsonify({'success': False, 'error': 'Error en consolidacion'}), 500


@blockchain_bp.route('/api/b3c/admin/force-verify/<purchase_id>', methods=['POST'])
@require_telegram_user
def admin_force_verify_purchase(purchase_id):
    """Forzar verificacion de una compra especifica (admin) - ignora expiracion."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'BD no disponible'}), 500
        
        from tracking.wallet_pool_service import get_wallet_pool_service
        wallet_pool = get_wallet_pool_service(db_manager)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT dw.id, dw.wallet_address, dw.expected_amount, dw.status,
                           dw.assigned_to_user_id, bp.purchase_id
                    FROM deposit_wallets dw
                    JOIN b3c_purchases bp ON bp.purchase_id = dw.assigned_to_purchase_id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                wallet_data = cur.fetchone()
                
                if not wallet_data:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                logger.info(f"[ADMIN FORCE VERIFY] Purchase {purchase_id}: wallet={wallet_data['wallet_address']}")
                
                deposit = wallet_pool._check_wallet_for_deposit(
                    wallet_data['wallet_address'], 
                    float(wallet_data['expected_amount'])
                )
                
                if deposit.get('found'):
                    cur.execute("""
                        UPDATE deposit_wallets 
                        SET status = 'deposit_confirmed',
                            deposit_detected_at = NOW(),
                            deposit_tx_hash = %s,
                            deposit_amount = %s
                        WHERE id = %s
                    """, (deposit['tx_hash'], deposit['amount'], wallet_data['id']))
                    
                    wallet_pool._credit_b3c_to_user(
                        wallet_data['assigned_to_user_id'], 
                        float(wallet_data['expected_amount']), 
                        purchase_id
                    )
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'status': 'confirmed',
                        'tx_hash': deposit['tx_hash'],
                        'amount_received': deposit['amount'],
                        'purchase_id': purchase_id,
                        'message': 'Deposito confirmado y B3C acreditados'
                    })
                
                return jsonify({
                    'success': False,
                    'status': 'not_found',
                    'message': 'No se encontro deposito en la blockchain',
                    'wallet': wallet_data['wallet_address'],
                    'expected': float(wallet_data['expected_amount']),
                    'api_response': deposit
                })
        
    except Exception as e:
        logger.error(f"Error in admin force verify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@blockchain_bp.route('/api/b3c/deposits/check', methods=['POST'])
@require_telegram_user
def check_b3c_deposits():
    """Verificar y procesar depositos B3C pendientes (admin)."""
    try:
        if not hasattr(request, 'telegram_user') or not request.telegram_user:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401
        
        user_id = str(request.telegram_user.get('id', 0))
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if not owner_id or user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        from tracking.b3c_service import get_b3c_service
        b3c_service = get_b3c_service()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(MAX(last_processed_lt), 0) as last_lt
                    FROM b3c_deposit_cursor
                    WHERE wallet_address = %s
                """, (os.environ.get('TON_WALLET_ADDRESS', ''),))
                cursor_result = cur.fetchone()
                last_lt = int(cursor_result['last_lt']) if cursor_result and cursor_result['last_lt'] else 0
        
        token_configured = bool(os.environ.get('B3C_TOKEN_ADDRESS', ''))
        
        if token_configured:
            poll_result = b3c_service.poll_jetton_deposits(last_lt)
        else:
            poll_result = b3c_service.poll_hot_wallet_deposits(last_lt)
        
        if not poll_result['success']:
            return jsonify({
                'success': False,
                'error': poll_result.get('error', 'Error al consultar blockchain')
            }), 500
        
        processed_deposits = []
        new_deposits = poll_result.get('deposits', [])
        
        for deposit in new_deposits:
            is_valid, user_prefix = b3c_service.validate_deposit_memo(deposit.get('memo', ''))
            
            if not is_valid or not user_prefix:
                logger.warning(f"Deposito sin memo valido: {deposit.get('tx_hash')}")
                continue
            
            tx_hash = deposit.get('tx_hash', '')
            if not tx_hash:
                logger.warning("Deposito sin tx_hash, omitiendo")
                continue
            
            with db_manager.get_connection() as conn:
                raw_conn = conn._conn if hasattr(conn, '_conn') else conn
                try:
                    raw_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
                    with raw_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT user_id FROM users 
                            WHERE user_id LIKE %s
                            LIMIT 1
                        """, (user_prefix + '%',))
                        user_match = cur.fetchone()
                        
                        if not user_match:
                            logger.warning(f"Usuario no encontrado para prefix: {user_prefix}")
                            raw_conn.rollback()
                            continue
                        
                        target_user_id = user_match['user_id']
                        deposit_id = f"DEP-{tx_hash[:16]}"
                        
                        cur.execute("""
                            INSERT INTO b3c_deposits 
                            (deposit_id, user_id, b3c_amount, source_wallet, tx_hash, status, created_at, confirmed_at)
                            VALUES (%s, %s, %s, %s, %s, 'confirmed', NOW(), NOW())
                            ON CONFLICT (tx_hash) DO NOTHING
                        """, (
                            deposit_id,
                            target_user_id,
                            deposit.get('amount', 0),
                            deposit.get('source_wallet', ''),
                            tx_hash
                        ))
                        
                        if cur.rowcount == 1:
                            cur.execute("""
                                UPDATE users SET credits = credits + %s
                                WHERE user_id = %s
                            """, (deposit.get('amount', 0), target_user_id))
                            
                            processed_deposits.append({
                                'depositId': deposit_id,
                                'userId': target_user_id,
                                'amount': deposit.get('amount', 0),
                                'txHash': tx_hash
                            })
                            
                            raw_conn.commit()
                        else:
                            logger.info(f"Deposito {tx_hash} ya procesado, omitiendo")
                            raw_conn.rollback()
                except Exception as tx_error:
                    raw_conn.rollback()
                    logger.error(f"Error procesando deposito {tx_hash}: {tx_error}")
                finally:
                    raw_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        
        if poll_result.get('latest_lt', 0) > last_lt:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO b3c_deposit_cursor (wallet_address, last_processed_lt, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (wallet_address) 
                        DO UPDATE SET last_processed_lt = %s, updated_at = NOW()
                    """, (
                        os.environ.get('TON_WALLET_ADDRESS', ''),
                        poll_result['latest_lt'],
                        poll_result['latest_lt']
                    ))
                    conn.commit()
        
        return jsonify({
            'success': True,
            'checked': len(new_deposits),
            'processed': len(processed_deposits),
            'deposits': processed_deposits,
            'lastLt': poll_result.get('latest_lt', 0),
            'checkedAt': poll_result.get('checked_at')
        })
        
    except Exception as e:
        logger.error(f"Error checking B3C deposits: {e}")
        return jsonify({'success': False, 'error': 'Error al verificar depositos'}), 500


@blockchain_bp.route('/api/b3c/deposits/history', methods=['GET'])
@require_telegram_user
def get_b3c_deposit_history():
    """Obtener historial de depositos B3C del usuario."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'deposits': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_deposits 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_id,))
                deposits = cur.fetchall()
                
        return jsonify({
            'success': True,
            'deposits': [{
                'id': d['deposit_id'],
                'amount': float(d['b3c_amount']),
                'status': d['status'],
                'txHash': d.get('tx_hash'),
                'sourceWallet': d.get('source_wallet'),
                'createdAt': d['created_at'].isoformat() if d['created_at'] else None,
                'confirmedAt': d['confirmed_at'].isoformat() if d.get('confirmed_at') else None
            } for d in deposits]
        })
        
    except Exception as e:
        logger.error(f"Error getting deposit history: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener historial'}), 500


@blockchain_bp.route('/api/b3c/deposits/pending', methods=['GET'])
@require_telegram_user
def get_pending_deposits():
    """Obtener depositos pendientes (admin)."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
        
        if user_id != owner_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'deposits': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT d.*, u.username, u.first_name
                    FROM b3c_deposits d
                    LEFT JOIN users u ON d.user_id = u.id
                    WHERE d.status = 'pending'
                    ORDER BY d.created_at DESC
                """)
                deposits = cur.fetchall()
                
        return jsonify({
            'success': True,
            'deposits': [{
                'id': d['deposit_id'],
                'userId': d['user_id'],
                'username': d.get('username'),
                'firstName': d.get('first_name'),
                'amount': float(d['b3c_amount']),
                'status': d['status'],
                'txHash': d.get('tx_hash'),
                'sourceWallet': d.get('source_wallet'),
                'createdAt': d['created_at'].isoformat() if d['created_at'] else None
            } for d in deposits]
        })
        
    except Exception as e:
        logger.error(f"Error getting pending deposits: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener pendientes'}), 500


@blockchain_bp.route('/api/b3c/last-purchase', methods=['GET'])
@require_telegram_auth
@require_owner
@rate_limit('price_check', use_ip=True)
def get_last_b3c_purchase():
    """Obtener logs de la ultima compra de B3C con informacion del usuario (admin only)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
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
                        u.avatar_url,
                        dw.wallet_address as deposit_wallet,
                        dw.expected_amount as wallet_expected_amount,
                        dw.status as wallet_status,
                        dw.assigned_at as wallet_assigned_at
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    ORDER BY bp.created_at DESC
                    LIMIT 1
                """)
                last_purchase = cur.fetchone()
                
                if not last_purchase:
                    logger.info("[B3C LOGS] No hay compras registradas en el sistema")
                    return jsonify({
                        'success': True,
                        'message': 'No hay compras registradas',
                        'lastPurchase': None
                    })
                
                logger.info(f"[B3C LOGS] ========== ULTIMA COMPRA DE B3C ==========")
                logger.info(f"[B3C LOGS] ID de Compra: {last_purchase['purchase_id']}")
                logger.info(f"[B3C LOGS] Usuario ID: {last_purchase['user_id']}")
                logger.info(f"[B3C LOGS] Username: @{last_purchase['username'] or 'N/A'}")
                logger.info(f"[B3C LOGS] Nombre: {last_purchase['first_name'] or 'N/A'} {last_purchase['last_name'] or ''}")
                logger.info(f"[B3C LOGS] TON enviados: {float(last_purchase['ton_amount']):.4f} TON")
                logger.info(f"[B3C LOGS] B3C recibidos: {float(last_purchase['b3c_amount']):.4f} B3C")
                logger.info(f"[B3C LOGS] Comision: {float(last_purchase['commission_ton']):.4f} TON")
                logger.info(f"[B3C LOGS] Estado: {last_purchase['status']}")
                logger.info(f"[B3C LOGS] Fecha: {last_purchase['created_at']}")
                if last_purchase.get('deposit_wallet'):
                    logger.info(f"[B3C LOGS] Wallet de Deposito: {last_purchase['deposit_wallet']}")
                    logger.info(f"[B3C LOGS] Monto Esperado: {float(last_purchase['wallet_expected_amount'] or 0):.4f} TON")
                    logger.info(f"[B3C LOGS] Estado Wallet: {last_purchase['wallet_status']}")
                if last_purchase['tx_hash']:
                    logger.info(f"[B3C LOGS] TX Hash: {last_purchase['tx_hash']}")
                logger.info(f"[B3C LOGS] =============================================")
                
        return jsonify({
            'success': True,
            'lastPurchase': {
                'purchaseId': last_purchase['purchase_id'],
                'userId': last_purchase['user_id'],
                'username': last_purchase['username'],
                'firstName': last_purchase['first_name'],
                'lastName': last_purchase['last_name'],
                'avatarUrl': last_purchase['avatar_url'],
                'tonAmount': float(last_purchase['ton_amount']),
                'b3cAmount': float(last_purchase['b3c_amount']),
                'commissionTon': float(last_purchase['commission_ton']),
                'status': last_purchase['status'],
                'txHash': last_purchase['tx_hash'],
                'depositWallet': last_purchase.get('deposit_wallet'),
                'walletExpectedAmount': float(last_purchase['wallet_expected_amount']) if last_purchase.get('wallet_expected_amount') else None,
                'walletStatus': last_purchase.get('wallet_status'),
                'createdAt': last_purchase['created_at'].isoformat() if last_purchase['created_at'] else None,
                'confirmedAt': last_purchase['confirmed_at'].isoformat() if last_purchase.get('confirmed_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting last B3C purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener ultima compra'}), 500


# ============================================================
# TON PAYMENT VERIFICATION - Migrado desde app.py 10 Dic 2025
# (create_ton_payment ya existe en lineas ~256-308)
# ============================================================

@blockchain_bp.route('/api/ton/payment/<payment_id>/verify', methods=['POST'])
@require_telegram_user
@rate_limit('payment_verify')
def verify_ton_payment(payment_id):
    """Verificar si un pago fue recibido en la blockchain."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'status': 'confirmed', 'message': 'Demo mode'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM pending_payments 
                    WHERE payment_id = %s AND user_id = %s
                """, (payment_id, user_id))
                payment = cur.fetchone()
                
                if not payment:
                    return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
                
                if payment['status'] == 'confirmed':
                    return jsonify({'success': True, 'status': 'confirmed', 'message': 'Pago ya confirmado'})
                
                expected_comment = f'BUNK3R-{payment_id}'
                expected_amount = float(payment['ton_amount'])
                
                try:
                    response = requests.get(
                        f'{TONCENTER_API_URL}/transactions',
                        params={
                            'account': MERCHANT_TON_WALLET,
                            'limit': 50,
                            'sort': 'desc'
                        },
                        timeout=15
                    )
                    
                    if response.status_code != 200:
                        return jsonify({
                            'success': True, 
                            'status': 'pending',
                            'message': 'Esperando confirmacion en la blockchain...'
                        })
                    
                    tx_data = response.json()
                    transactions = tx_data.get('transactions', [])
                    
                    for tx in transactions:
                        in_msg = tx.get('in_msg', {})
                        
                        if not in_msg or in_msg.get('msg_type') != 'int_msg':
                            continue
                        
                        msg_value = int(in_msg.get('value', 0))
                        msg_amount_ton = msg_value / 1e9
                        
                        if msg_amount_ton < expected_amount * 0.99:
                            continue
                        
                        decoded = in_msg.get('decoded_body', {})
                        comment = decoded.get('text', '') if decoded else ''
                        
                        if not comment:
                            raw_body = in_msg.get('message', '')
                            if raw_body:
                                try:
                                    comment = bytes.fromhex(raw_body).decode('utf-8', errors='ignore')
                                except (ValueError, UnicodeDecodeError) as e:
                                    logger.debug(f"Error decoding message body: {e}")
                        
                        if expected_comment.lower() in comment.lower():
                            tx_hash = tx.get('hash', '')
                            
                            cur.execute("""
                                UPDATE pending_payments 
                                SET status = 'confirmed', tx_hash = %s, confirmed_at = NOW()
                                WHERE payment_id = %s
                            """, (tx_hash, payment_id))
                            
                            credits = calculate_credits_from_ton(expected_amount)
                            cur.execute("""
                                INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id, created_at)
                                VALUES (%s, %s, 'credit', %s, %s, NOW())
                            """, (user_id, credits, f'Recarga TON - {expected_amount} TON', tx_hash))
                            
                            conn.commit()
                            
                            cur.execute("""
                                SELECT COALESCE(SUM(amount), 0) as balance
                                FROM wallet_transactions
                                WHERE user_id = %s
                            """, (user_id,))
                            result = cur.fetchone()
                            new_balance = float(result['balance']) if result else credits
                            
                            db_manager.create_transaction_notification(
                                user_id=user_id,
                                amount=credits,
                                transaction_type='credit',
                                new_balance=new_balance
                            )
                            
                            return jsonify({
                                'success': True,
                                'status': 'confirmed',
                                'txHash': tx_hash,
                                'creditsAdded': credits,
                                'newBalance': new_balance,
                                'message': f'+{credits} BUNK3RCO1N agregados!'
                            })
                    
                    return jsonify({
                        'success': True,
                        'status': 'pending',
                        'message': 'Transaccion no encontrada aun. Espera unos segundos...'
                    })
                    
                except requests.RequestException as e:
                    logger.error(f"TonCenter API error: {e}")
                    return jsonify({
                        'success': True,
                        'status': 'pending',
                        'message': 'Verificando en la blockchain...'
                    })
                    
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@blockchain_bp.route('/api/ton/payment/<payment_id>/status', methods=['GET'])
@require_telegram_user
def get_payment_status(payment_id):
    """Obtener el estado de un pago pendiente."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'status': 'pending'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT status, tx_hash, credits FROM pending_payments 
                    WHERE payment_id = %s AND user_id = %s
                """, (payment_id, user_id))
                payment = cur.fetchone()
                
                if not payment:
                    return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
                
                return jsonify({
                    'success': True,
                    'status': payment['status'],
                    'txHash': payment.get('tx_hash'),
                    'credits': payment['credits']
                })
                
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@blockchain_bp.route('/api/wallet/credit', methods=['POST'])
@require_telegram_user
def credit_wallet():
    """Agregar BUNK3RCO1N a la billetera del usuario."""
    try:
        data = request.get_json()
        credits = data.get('credits', 0)
        usdt_amount = data.get('usdtAmount', 0)
        transaction_boc = data.get('transactionBoc', '')
        user_id = str(data.get('userId') or (request.telegram_user.get('id', 0) if hasattr(request, 'telegram_user') else 0))
        
        if not credits or credits <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'newBalance': credits, 'message': 'Demo mode'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, 'credit', %s, %s, NOW())
                """, (user_id, credits, f'Recarga de {usdt_amount} USDT', transaction_boc))
                conn.commit()
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                new_balance = result[0] if result else credits
        
        db_manager.create_transaction_notification(
            user_id=user_id,
            amount=credits,
            transaction_type='credit',
            new_balance=float(new_balance)
        )
                
        return jsonify({
            'success': True,
            'newBalance': float(new_balance),
            'creditsAdded': credits
        })
        
    except Exception as e:
        logger.error(f"Error crediting wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@blockchain_bp.route('/api/wallet/transactions', methods=['GET'])
@require_telegram_auth
def get_wallet_transactions():
    """Obtener historial de transacciones del usuario con filtros."""
    try:
        user_id = str(request.telegram_user.get('id', 0)) if hasattr(request, 'telegram_user') else '0'
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        filter_type = request.args.get('filter', 'all')
        from_date = request.args.get('from_date', None)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'transactions': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, amount, transaction_type, description, created_at
                    FROM wallet_transactions
                    WHERE user_id = %s
                """
                params = [user_id]
                
                if filter_type == 'credit':
                    query += " AND amount > 0"
                elif filter_type == 'debit':
                    query += " AND amount < 0"
                
                if from_date:
                    query += " AND created_at >= %s"
                    params.append(from_date)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                transactions = cur.fetchall()
                
        return jsonify({
            'success': True,
            'transactions': [dict(t) for t in transactions] if transactions else []
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'success': True, 'transactions': []})
