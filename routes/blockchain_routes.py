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
import uuid
import logging
import requests

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
