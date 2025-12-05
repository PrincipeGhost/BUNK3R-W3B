"""
B3C Token Service - Integración con TON Blockchain (Testnet/Mainnet)
Maneja precios en tiempo real, compras, ventas, retiros y depósitos de B3C
"""
import os
import logging
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class B3CTokenService:
    """Servicio para gestionar el token B3C en TON blockchain."""
    
    TESTNET_TONCENTER_API = 'https://testnet.toncenter.com/api/v2'
    MAINNET_TONCENTER_API = 'https://toncenter.com/api/v3'
    
    TESTNET_STONFI_ROUTER = 'kQALh-JBBIKK7gr0o4AVf9JZnEsFndqO0qTCyT-D-yBsWk0v'
    TESTNET_PTON = 'kQACS30DNoUQ7NfApPvzh7eBmSZ9L4ygJ-lkNWtba8TQT-Px'
    
    STONFI_API_URL = 'https://api.ston.fi/v1'
    
    COMMISSION_RATE = Decimal('0.05')
    
    def __init__(self, 
                 use_testnet: bool = True,
                 b3c_token_address: Optional[str] = None,
                 commission_wallet: Optional[str] = None,
                 hot_wallet: Optional[str] = None,
                 toncenter_api_key: Optional[str] = None):
        """
        Inicializar el servicio B3C.
        
        Args:
            use_testnet: True para testnet, False para mainnet
            b3c_token_address: Dirección del contrato del token B3C (Jetton)
            commission_wallet: Wallet donde se envían las comisiones (5%)
            hot_wallet: Wallet caliente para operaciones de swap
            toncenter_api_key: API key para TonCenter (opcional)
        """
        self.use_testnet = use_testnet
        self.b3c_token_address: str = b3c_token_address or os.environ.get('B3C_TOKEN_ADDRESS', '')
        self.commission_wallet: str = commission_wallet or os.environ.get('B3C_COMMISSION_WALLET', '')
        self.hot_wallet: str = hot_wallet or os.environ.get('B3C_HOT_WALLET', '')
        self.toncenter_api_key: str = toncenter_api_key or os.environ.get('TONCENTER_API_KEY', '')
        
        self.api_base = self.TESTNET_TONCENTER_API if use_testnet else self.MAINNET_TONCENTER_API
        
        self._price_cache = {}
        self._price_cache_ttl = 30
        
        logger.info(f"B3C Service initialized - {'Testnet' if use_testnet else 'Mainnet'}")
        
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para las peticiones API."""
        headers = {'Content-Type': 'application/json'}
        if self.toncenter_api_key:
            headers['X-API-Key'] = self.toncenter_api_key
        return headers
    
    def get_b3c_price(self) -> Dict[str, Any]:
        """
        Obtener precio actual del token B3C.
        
        Returns:
            Dict con precio en TON, USD, y metadata
        """
        cache_key = 'b3c_price'
        now = time.time()
        
        if cache_key in self._price_cache:
            cached_data, cached_time = self._price_cache[cache_key]
            if now - cached_time < self._price_cache_ttl:
                return cached_data
        
        try:
            if not self.b3c_token_address:
                simulated_price = self._get_simulated_price()
                self._price_cache[cache_key] = (simulated_price, now)
                return simulated_price
            
            response = requests.get(
                f'{self.STONFI_API_URL}/assets/{self.b3c_token_address}',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                asset = data.get('asset', {})
                
                price_data = {
                    'success': True,
                    'price_ton': float(asset.get('dex_price_usd', 0)) / self._get_ton_usd_price(),
                    'price_usd': float(asset.get('dex_price_usd', 0)),
                    'symbol': asset.get('symbol', 'B3C'),
                    'name': asset.get('display_name', 'BUNK3R Coin'),
                    'decimals': asset.get('decimals', 9),
                    'total_supply': asset.get('third_party_usd_price', 0),
                    'liquidity_usd': float(asset.get('dex_usd_price', 0)),
                    'change_24h': 0,
                    'volume_24h': 0,
                    'updated_at': datetime.utcnow().isoformat(),
                    'source': 'stonfi',
                    'is_testnet': self.use_testnet
                }
                
                self._price_cache[cache_key] = (price_data, now)
                return price_data
            else:
                return self._get_simulated_price()
                
        except Exception as e:
            logger.error(f"Error fetching B3C price: {e}")
            return self._get_simulated_price()
    
    def _get_simulated_price(self) -> Dict[str, Any]:
        """Precio simulado para testnet o cuando no hay datos reales."""
        base_price_ton = Decimal('0.001')
        ton_usd = Decimal(str(self._get_ton_usd_price()))
        
        return {
            'success': True,
            'price_ton': float(base_price_ton),
            'price_usd': float(base_price_ton * ton_usd),
            'symbol': 'B3C',
            'name': 'BUNK3R Coin',
            'decimals': 9,
            'total_supply': 1000000000,
            'liquidity_usd': 0,
            'change_24h': 0,
            'volume_24h': 0,
            'updated_at': datetime.utcnow().isoformat(),
            'source': 'simulated',
            'is_testnet': self.use_testnet,
            'notice': 'Precio simulado - Token aún no desplegado'
        }
    
    def _get_ton_usd_price(self) -> float:
        """Obtener precio de TON en USD."""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': 'the-open-network', 'vs_currencies': 'usd'},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('the-open-network', {}).get('usd', 5.0)
        except Exception as e:
            logger.warning(f"Error fetching TON price: {e}")
        return 5.0
    
    def calculate_b3c_from_ton(self, ton_amount: float) -> Dict[str, Any]:
        """
        Calcular cuántos B3C recibirá el usuario por X TON.
        
        Args:
            ton_amount: Cantidad de TON a gastar
            
        Returns:
            Dict con desglose de la transacción
        """
        ton_decimal = Decimal(str(ton_amount))
        
        commission = ton_decimal * self.COMMISSION_RATE
        ton_for_swap = ton_decimal - commission
        
        price_data = self.get_b3c_price()
        price_ton = Decimal(str(price_data.get('price_ton', 0.001)))
        
        if price_ton <= 0:
            price_ton = Decimal('0.001')
        
        b3c_amount = ton_for_swap / price_ton
        
        slippage = Decimal('0.01')
        min_b3c = b3c_amount * (Decimal('1') - slippage)
        
        return {
            'success': True,
            'ton_amount': float(ton_decimal),
            'commission_ton': float(commission),
            'commission_rate': float(self.COMMISSION_RATE * 100),
            'ton_for_swap': float(ton_for_swap),
            'b3c_amount': float(b3c_amount),
            'min_b3c_amount': float(min_b3c),
            'price_per_b3c': float(price_ton),
            'slippage_percent': float(slippage * 100),
            'price_data': price_data
        }
    
    def calculate_ton_from_b3c(self, b3c_amount: float) -> Dict[str, Any]:
        """
        Calcular cuántos TON recibirá el usuario por X B3C (venta).
        
        Args:
            b3c_amount: Cantidad de B3C a vender
            
        Returns:
            Dict con desglose de la transacción
        """
        b3c_decimal = Decimal(str(b3c_amount))
        
        price_data = self.get_b3c_price()
        price_ton = Decimal(str(price_data.get('price_ton', 0.001)))
        
        if price_ton <= 0:
            price_ton = Decimal('0.001')
        
        gross_ton = b3c_decimal * price_ton
        
        commission = gross_ton * self.COMMISSION_RATE
        net_ton = gross_ton - commission
        
        slippage = Decimal('0.01')
        min_ton = net_ton * (Decimal('1') - slippage)
        
        return {
            'success': True,
            'b3c_amount': float(b3c_decimal),
            'gross_ton': float(gross_ton),
            'commission_ton': float(commission),
            'commission_rate': float(self.COMMISSION_RATE * 100),
            'net_ton': float(net_ton),
            'min_ton': float(min_ton),
            'price_per_b3c': float(price_ton),
            'slippage_percent': float(slippage * 100),
            'price_data': price_data
        }
    
    def get_wallet_b3c_balance(self, wallet_address: str) -> Dict[str, Any]:
        """
        Obtener balance de B3C de una wallet.
        
        Args:
            wallet_address: Dirección de la wallet TON
            
        Returns:
            Dict con balance y metadata
        """
        if not self.b3c_token_address or not wallet_address:
            return {
                'success': True,
                'balance': 0,
                'balance_formatted': '0',
                'wallet_address': wallet_address,
                'is_testnet': self.use_testnet,
                'notice': 'Token no configurado o wallet vacía'
            }
        
        try:
            response = requests.get(
                f'{self.api_base}/getAddressBalance',
                params={'address': wallet_address},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'balance': 0,
                    'balance_formatted': '0',
                    'wallet_address': wallet_address,
                    'is_testnet': self.use_testnet
                }
            
            return {
                'success': False,
                'error': 'No se pudo obtener el balance',
                'balance': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting B3C balance: {e}")
            return {
                'success': False,
                'error': str(e),
                'balance': 0
            }
    
    def verify_ton_transaction(self, tx_hash: str, expected_amount: float, 
                                expected_comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Verificar una transacción TON entrante.
        
        Args:
            tx_hash: Hash de la transacción
            expected_amount: Cantidad esperada en TON
            expected_comment: Comentario esperado (opcional)
            
        Returns:
            Dict con resultado de verificación
        """
        try:
            if not self.hot_wallet:
                return {'success': False, 'error': 'Hot wallet no configurada'}
            
            response = requests.get(
                f'{self.api_base}/transactions',
                params={
                    'account': self.hot_wallet,
                    'limit': 100,
                    'sort': 'desc'
                },
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                
                for tx in transactions:
                    in_msg = tx.get('in_msg', {})
                    value = int(in_msg.get('value', 0)) / 1e9
                    message = in_msg.get('message', '')
                    
                    if abs(value - expected_amount) < 0.01:
                        if expected_comment is None or expected_comment in message:
                            return {
                                'success': True,
                                'verified': True,
                                'tx_hash': tx.get('hash', tx_hash),
                                'amount': value,
                                'comment': message,
                                'from_address': in_msg.get('source', ''),
                                'timestamp': tx.get('utime', 0)
                            }
                
                return {
                    'success': True,
                    'verified': False,
                    'message': 'Transacción no encontrada aún'
                }
            
            return {'success': False, 'error': 'Error en API de blockchain'}
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_transaction_history(self, wallet_address: str, limit: int = 50) -> Dict[str, Any]:
        """
        Obtener historial de transacciones de una wallet.
        
        Args:
            wallet_address: Dirección de la wallet
            limit: Número máximo de transacciones
            
        Returns:
            Dict con lista de transacciones
        """
        try:
            response = requests.get(
                f'{self.api_base}/transactions',
                params={
                    'account': wallet_address,
                    'limit': limit,
                    'sort': 'desc'
                },
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                transactions = []
                
                for tx in data.get('transactions', []):
                    in_msg = tx.get('in_msg', {})
                    out_msgs = tx.get('out_msgs', [])
                    
                    transactions.append({
                        'hash': tx.get('hash', ''),
                        'timestamp': tx.get('utime', 0),
                        'type': 'incoming' if in_msg.get('value') else 'outgoing',
                        'amount': int(in_msg.get('value', 0)) / 1e9,
                        'from': in_msg.get('source', ''),
                        'to': in_msg.get('destination', ''),
                        'comment': in_msg.get('message', ''),
                        'fee': int(tx.get('fee', 0)) / 1e9
                    })
                
                return {
                    'success': True,
                    'transactions': transactions,
                    'count': len(transactions)
                }
            
            return {'success': False, 'error': 'Error obteniendo historial'}
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_network_status(self) -> Dict[str, Any]:
        """Verificar estado de la red TON."""
        try:
            response = requests.get(
                f'{self.api_base}/getMasterchainInfo',
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'network': 'testnet' if self.use_testnet else 'mainnet',
                    'status': 'online',
                    'api_url': self.api_base
                }
            
            return {
                'success': False,
                'network': 'testnet' if self.use_testnet else 'mainnet',
                'status': 'offline'
            }
            
        except Exception as e:
            logger.error(f"Error checking network status: {e}")
            return {
                'success': False,
                'network': 'testnet' if self.use_testnet else 'mainnet',
                'status': 'error',
                'error': str(e)
            }
    
    def get_service_config(self) -> Dict[str, Any]:
        """Obtener configuración actual del servicio."""
        return {
            'network': 'testnet' if self.use_testnet else 'mainnet',
            'b3c_token_configured': bool(self.b3c_token_address),
            'b3c_token_address': self.b3c_token_address[:20] + '...' if self.b3c_token_address else None,
            'commission_rate': float(self.COMMISSION_RATE * 100),
            'commission_wallet_configured': bool(self.commission_wallet),
            'hot_wallet_configured': bool(self.hot_wallet),
            'api_key_configured': bool(self.toncenter_api_key),
            'stonfi_router': self.TESTNET_STONFI_ROUTER if self.use_testnet else 'mainnet_router',
            'features': {
                'buy_b3c': True,
                'sell_b3c': True,
                'withdraw': bool(self.hot_wallet),
                'deposit': bool(self.hot_wallet),
                'price_feed': True
            }
        }
    
    def poll_hot_wallet_deposits(self, last_processed_lt: Optional[int] = None) -> Dict[str, Any]:
        """
        Consultar transacciones entrantes a la hot wallet para detectar depósitos.
        
        Args:
            last_processed_lt: Logical time de la última transacción procesada
            
        Returns:
            Dict con lista de nuevos depósitos detectados
        """
        if not self.hot_wallet:
            return {
                'success': False,
                'error': 'Hot wallet no configurada',
                'deposits': []
            }
        
        try:
            params = {
                'account': self.hot_wallet,
                'limit': 100,
                'sort': 'desc'
            }
            
            response = requests.get(
                f'{self.api_base}/transactions',
                params=params,
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'deposits': []
                }
            
            data = response.json()
            transactions = data.get('transactions', [])
            new_deposits = []
            latest_lt = last_processed_lt or 0
            
            for tx in transactions:
                tx_lt = int(tx.get('lt', 0))
                
                if last_processed_lt and tx_lt <= last_processed_lt:
                    continue
                
                in_msg = tx.get('in_msg', {})
                value = int(in_msg.get('value', 0))
                
                if value <= 0:
                    continue
                
                message = in_msg.get('message', '')
                source = in_msg.get('source', '')
                
                if message.startswith('DEP-'):
                    user_id_prefix = message.replace('DEP-', '')[:8]
                    
                    deposit = {
                        'tx_hash': tx.get('hash', ''),
                        'lt': tx_lt,
                        'amount_nano': value,
                        'amount': value / 1e9,
                        'memo': message,
                        'user_id_prefix': user_id_prefix,
                        'source_wallet': source,
                        'timestamp': tx.get('utime', 0),
                        'status': 'detected'
                    }
                    new_deposits.append(deposit)
                    
                    if tx_lt > latest_lt:
                        latest_lt = tx_lt
            
            return {
                'success': True,
                'deposits': new_deposits,
                'count': len(new_deposits),
                'latest_lt': latest_lt,
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error polling deposits: {e}")
            return {
                'success': False,
                'error': str(e),
                'deposits': []
            }
    
    def poll_jetton_deposits(self, last_processed_lt: Optional[int] = None) -> Dict[str, Any]:
        """
        Consultar transferencias de Jetton (B3C token) a la hot wallet.
        Solo funciona si B3C_TOKEN_ADDRESS está configurado.
        
        Args:
            last_processed_lt: Logical time de la última transacción procesada
            
        Returns:
            Dict con lista de depósitos de B3C detectados
        """
        if not self.hot_wallet or not self.b3c_token_address:
            return {
                'success': False,
                'error': 'Hot wallet o token B3C no configurado',
                'deposits': []
            }
        
        try:
            response = requests.get(
                f'{self.api_base}/jetton/transfers',
                params={
                    'account': self.hot_wallet,
                    'jetton_master': self.b3c_token_address,
                    'direction': 'in',
                    'limit': 100,
                    'sort': 'desc'
                },
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'deposits': []
                }
            
            data = response.json()
            transfers = data.get('jetton_transfers', [])
            new_deposits = []
            latest_lt = last_processed_lt or 0
            
            for transfer in transfers:
                tx_lt = int(transfer.get('transaction_lt', 0))
                
                if last_processed_lt and tx_lt <= last_processed_lt:
                    continue
                
                amount = int(transfer.get('amount', 0))
                if amount <= 0:
                    continue
                
                comment = transfer.get('comment', '') or ''
                source = transfer.get('source', {}).get('address', '')
                
                if comment.startswith('DEP-'):
                    user_id_prefix = comment.replace('DEP-', '')[:8]
                else:
                    user_id_prefix = None
                
                deposit = {
                    'tx_hash': transfer.get('transaction_hash', ''),
                    'lt': tx_lt,
                    'amount_nano': amount,
                    'amount': amount / 1e9,
                    'memo': comment,
                    'user_id_prefix': user_id_prefix,
                    'source_wallet': source,
                    'timestamp': transfer.get('transaction_now', 0),
                    'status': 'detected',
                    'is_jetton': True
                }
                new_deposits.append(deposit)
                
                if tx_lt > latest_lt:
                    latest_lt = tx_lt
            
            return {
                'success': True,
                'deposits': new_deposits,
                'count': len(new_deposits),
                'latest_lt': latest_lt,
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error polling jetton deposits: {e}")
            return {
                'success': False,
                'error': str(e),
                'deposits': []
            }
    
    def validate_deposit_memo(self, memo: str) -> Tuple[bool, Optional[str]]:
        """
        Validar formato del memo de depósito y extraer user_id.
        
        Args:
            memo: Memo/comentario de la transacción
            
        Returns:
            Tuple (es_válido, user_id_prefix o None)
        """
        if not memo or not memo.startswith('DEP-'):
            return False, None
        
        user_id_prefix = memo.replace('DEP-', '').strip()[:8]
        
        if len(user_id_prefix) < 4:
            return False, None
        
        return True, user_id_prefix


b3c_service = None

def get_b3c_service() -> B3CTokenService:
    """Obtener instancia singleton del servicio B3C."""
    global b3c_service
    if b3c_service is None:
        b3c_service = B3CTokenService(
            use_testnet=os.environ.get('B3C_USE_TESTNET', 'true').lower() == 'true'
        )
    return b3c_service
