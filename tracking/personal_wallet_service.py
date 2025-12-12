"""
Personal Wallet Service - Sistema de wallets personales multi-token (Seccion 25)
Wallets permanentes por usuario con soporte para B3C, USDT, TON y detección automática de Jettons.
"""

import os
import logging
import secrets
import hashlib
import base64
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

logger = logging.getLogger(__name__)

try:
    from tonsdk.contract.wallet import WalletVersionEnum, Wallets
    from tonsdk.crypto import mnemonic_new
    TONSDK_AVAILABLE = True
    logger.info("tonsdk loaded for PersonalWalletService")
except ImportError:
    TONSDK_AVAILABLE = False
    logger.warning("tonsdk not available - using simulated wallet generation")


class PersonalWalletService:
    """Servicio para gestionar wallets personales multi-token de usuarios."""
    
    TONCENTER_API_V3 = 'https://toncenter.com/api/v3'
    TESTNET_API = 'https://testnet.toncenter.com/api/v2'
    
    MAIN_TOKENS = {
        'B3C': {
            'address': os.environ.get('B3C_TOKEN_ADDRESS', ''),
            'symbol': 'B3C',
            'name': 'BUNK3R Coin',
            'decimals': 9,
            'icon': '/static/images/b3c-logo.png',
            'order': 1
        },
        'USDT': {
            'address': 'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs',
            'symbol': 'USDT',
            'name': 'Tether USD',
            'decimals': 6,
            'icon': '/static/images/usdt-logo.png',
            'order': 2
        },
        'TON': {
            'address': 'native',
            'symbol': 'TON',
            'name': 'Toncoin',
            'decimals': 9,
            'icon': '/static/images/ton-logo.png',
            'order': 3
        }
    }
    
    def __init__(self, db_manager, master_key: Optional[str] = None):
        """
        Inicializar el servicio de wallet personal.
        
        Args:
            db_manager: Instancia de DatabaseManager
            master_key: Clave maestra para encriptar mnemonics
        """
        self.db = db_manager
        self.master_key = master_key or os.environ.get('WALLET_MASTER_KEY') or os.environ.get('ENCRYPTION_MASTER_KEY')
        self.toncenter_api_key = os.environ.get('TONCENTER_API_KEY', '')
        self.use_testnet = os.environ.get('B3C_USE_TESTNET', 'true').lower() == 'true'
        
        if not self.master_key:
            self.master_key = base64.b64encode(secrets.token_bytes(32)).decode()
            logger.warning("ENCRYPTION_MASTER_KEY not configured. Using temporary key!")
        
        self.encryption_key = self._derive_key(self.master_key)
        
        b3c_addr = os.environ.get('B3C_TOKEN_ADDRESS', '')
        if b3c_addr:
            self.MAIN_TOKENS['B3C']['address'] = b3c_addr
        
        logger.info(f"PersonalWalletService initialized - TONSDK: {TONSDK_AVAILABLE}, Testnet: {self.use_testnet}")
    
    def _derive_key(self, master_key: str) -> bytes:
        """Derivar clave de 32 bytes para AES-256."""
        return hashlib.sha256(master_key.encode()).digest()
    
    def encrypt_mnemonic(self, mnemonic: str) -> str:
        """Encriptar mnemonic usando AES-256-CBC."""
        iv = secrets.token_bytes(16)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(mnemonic.encode()) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(iv).decode() + ':' + base64.b64encode(ciphertext).decode()
    
    def decrypt_mnemonic(self, encrypted: str) -> str:
        """Desencriptar mnemonic AES-256-CBC."""
        try:
            parts = encrypted.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid encrypted format")
            
            iv = base64.b64decode(parts[0])
            ciphertext = base64.b64decode(parts[1])
            
            cipher = Cipher(algorithms.AES(self.encryption_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode()
        except Exception as e:
            logger.error(f"Error decrypting mnemonic: {e}")
            raise
    
    def _generate_ton_wallet(self) -> Dict[str, Any]:
        """Generar una nueva wallet TON usando tonsdk."""
        if not TONSDK_AVAILABLE:
            fake_address = f"EQ{''.join(secrets.choice('0123456789ABCDEFabcdef') for _ in range(48))}"
            fake_mnemonic = ' '.join([f"word{i}" for i in range(24)])
            return {
                'address': fake_address,
                'mnemonic': fake_mnemonic,
                'version': 'v4r2',
                'simulated': True
            }
        
        try:
            mnemonics, pub_key, priv_key, wallet = Wallets.create(
                WalletVersionEnum.v4r2, 
                workchain=0
            )
            
            address = wallet.address.to_string(True, True, False)
            mnemonic_str = ' '.join(mnemonics)
            
            return {
                'address': address,
                'mnemonic': mnemonic_str,
                'version': 'v4r2',
                'simulated': False
            }
        except Exception as e:
            logger.error(f"Error generating TON wallet: {e}")
            raise
    
    def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener wallet existente o crear una nueva para el usuario.
        
        Args:
            user_id: ID del usuario (Telegram ID)
            
        Returns:
            Dict con datos de la wallet (sin mnemonic)
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, address, wallet_version, is_active, created_at
                        FROM user_wallets WHERE user_id = %s
                    """, (user_id,))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        return {
                            'success': True,
                            'wallet': {
                                'id': existing[0],
                                'address': existing[1],
                                'version': existing[2],
                                'is_active': existing[3],
                                'created_at': existing[4].isoformat() if existing[4] else None
                            },
                            'is_new': False
                        }
                    
                    wallet_data = self._generate_ton_wallet()
                    encrypted_mnemonic = self.encrypt_mnemonic(wallet_data['mnemonic'])
                    
                    cur.execute("""
                        INSERT INTO user_wallets (user_id, address, encrypted_mnemonic, wallet_version)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, address, wallet_version, is_active, created_at
                    """, (user_id, wallet_data['address'], encrypted_mnemonic, wallet_data['version']))
                    
                    new_wallet = cur.fetchone()
                    
                    self._initialize_main_tokens(cur, user_id)
                    
                    conn.commit()
                    
                    logger.info(f"Created new personal wallet for user {user_id}: {wallet_data['address'][:20]}...")
                    
                    return {
                        'success': True,
                        'wallet': {
                            'id': new_wallet[0],
                            'address': new_wallet[1],
                            'version': new_wallet[2],
                            'is_active': new_wallet[3],
                            'created_at': new_wallet[4].isoformat() if new_wallet[4] else None
                        },
                        'is_new': True,
                        'simulated': wallet_data.get('simulated', False)
                    }
                    
        except Exception as e:
            logger.error(f"Error in get_or_create_wallet for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _initialize_main_tokens(self, cur, user_id: str):
        """Inicializar balances de tokens principales para un usuario."""
        for symbol, token_data in self.MAIN_TOKENS.items():
            try:
                cur.execute("""
                    INSERT INTO token_balances 
                    (user_id, token_address, token_symbol, token_name, token_decimals, 
                     token_icon_url, balance, is_main_token, display_order)
                    VALUES (%s, %s, %s, %s, %s, %s, 0, TRUE, %s)
                    ON CONFLICT (user_id, token_address) DO NOTHING
                """, (
                    user_id,
                    token_data['address'],
                    token_data['symbol'],
                    token_data['name'],
                    token_data['decimals'],
                    token_data['icon'],
                    token_data['order']
                ))
            except Exception as e:
                logger.warning(f"Could not initialize token {symbol} for user {user_id}: {e}")
    
    def get_user_assets(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener todos los tokens y balances del usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con wallet info y lista de tokens con balances
        """
        try:
            wallet_result = self.get_or_create_wallet(user_id)
            if not wallet_result.get('success'):
                return wallet_result
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT token_address, token_symbol, token_name, token_decimals,
                               token_icon_url, balance, balance_usd, is_main_token, 
                               display_order, last_synced
                        FROM token_balances 
                        WHERE user_id = %s
                        ORDER BY is_main_token DESC, display_order ASC, token_symbol ASC
                    """, (user_id,))
                    
                    tokens = []
                    for row in cur.fetchall():
                        tokens.append({
                            'address': row[0],
                            'symbol': row[1],
                            'name': row[2],
                            'decimals': row[3],
                            'icon': row[4],
                            'balance': float(row[5]) if row[5] else 0,
                            'balance_usd': float(row[6]) if row[6] else 0,
                            'is_main': row[7],
                            'order': row[8],
                            'last_synced': row[9].isoformat() if row[9] else None
                        })
                    
                    main_tokens = [t for t in tokens if t['is_main']]
                    other_tokens = [t for t in tokens if not t['is_main'] and float(t['balance']) > 0]
                    
                    return {
                        'success': True,
                        'wallet': wallet_result['wallet'],
                        'main_tokens': main_tokens,
                        'other_tokens': other_tokens,
                        'total_tokens': len(tokens)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting assets for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_token_detail(self, user_id: str, token_address: str) -> Dict[str, Any]:
        """Obtener detalle de un token específico con historial."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT token_address, token_symbol, token_name, token_decimals,
                               token_icon_url, balance, balance_usd, is_main_token, last_synced
                        FROM token_balances 
                        WHERE user_id = %s AND token_address = %s
                    """, (user_id, token_address))
                    
                    row = cur.fetchone()
                    if not row:
                        return {'success': False, 'error': 'Token not found'}
                    
                    token = {
                        'address': row[0],
                        'symbol': row[1],
                        'name': row[2],
                        'decimals': row[3],
                        'icon': row[4],
                        'balance': float(row[5]) if row[5] else 0,
                        'balance_usd': float(row[6]) if row[6] else 0,
                        'is_main': row[7],
                        'last_synced': row[8].isoformat() if row[8] else None
                    }
                    
                    cur.execute("""
                        SELECT id, tx_type, amount, fee_amount, platform_fee, tx_hash,
                               from_address, to_address, status, created_at, completed_at
                        FROM token_transactions
                        WHERE user_id = %s AND token_address = %s
                        ORDER BY created_at DESC
                        LIMIT 50
                    """, (user_id, token_address))
                    
                    transactions = []
                    for tx_row in cur.fetchall():
                        transactions.append({
                            'id': tx_row[0],
                            'type': tx_row[1],
                            'amount': float(tx_row[2]) if tx_row[2] else 0,
                            'fee': float(tx_row[3]) if tx_row[3] else 0,
                            'platform_fee': float(tx_row[4]) if tx_row[4] else 0,
                            'tx_hash': tx_row[5],
                            'from': tx_row[6],
                            'to': tx_row[7],
                            'status': tx_row[8],
                            'created_at': tx_row[9].isoformat() if tx_row[9] else None,
                            'completed_at': tx_row[10].isoformat() if tx_row[10] else None
                        })
                    
                    return {
                        'success': True,
                        'token': token,
                        'transactions': transactions
                    }
                    
        except Exception as e:
            logger.error(f"Error getting token detail: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_transactions(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Obtener historial de transacciones de todos los tokens."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, token_address, token_symbol, tx_type, amount, 
                               fee_amount, platform_fee, tx_hash, from_address, 
                               to_address, status, created_at, completed_at
                        FROM token_transactions
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                    
                    transactions = []
                    for row in cur.fetchall():
                        transactions.append({
                            'id': row[0],
                            'token_address': row[1],
                            'token_symbol': row[2],
                            'type': row[3],
                            'amount': float(row[4]) if row[4] else 0,
                            'fee': float(row[5]) if row[5] else 0,
                            'platform_fee': float(row[6]) if row[6] else 0,
                            'tx_hash': row[7],
                            'from': row[8],
                            'to': row[9],
                            'status': row[10],
                            'created_at': row[11].isoformat() if row[11] else None,
                            'completed_at': row[12].isoformat() if row[12] else None
                        })
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM token_transactions WHERE user_id = %s
                    """, (user_id,))
                    total = cur.fetchone()[0]
                    
                    return {
                        'success': True,
                        'transactions': transactions,
                        'total': total,
                        'has_more': offset + limit < total
                    }
                    
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_token_balance(self, user_id: str, token_address: str, 
                            new_balance: Decimal, token_info: Dict = None) -> bool:
        """Actualizar balance de un token (usado por el sync job)."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    if token_info:
                        cur.execute("""
                            INSERT INTO token_balances 
                            (user_id, token_address, token_symbol, token_name, 
                             token_decimals, balance, last_synced)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (user_id, token_address) DO UPDATE SET
                                balance = EXCLUDED.balance,
                                token_symbol = COALESCE(EXCLUDED.token_symbol, token_balances.token_symbol),
                                token_name = COALESCE(EXCLUDED.token_name, token_balances.token_name),
                                last_synced = NOW()
                        """, (
                            user_id, 
                            token_address,
                            token_info.get('symbol'),
                            token_info.get('name'),
                            token_info.get('decimals', 9),
                            new_balance
                        ))
                    else:
                        cur.execute("""
                            UPDATE token_balances 
                            SET balance = %s, last_synced = NOW()
                            WHERE user_id = %s AND token_address = %s
                        """, (new_balance, user_id, token_address))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False
    
    def record_transaction(self, user_id: str, token_address: str, tx_type: str,
                          amount: Decimal, tx_hash: str = None, from_addr: str = None,
                          to_addr: str = None, fee: Decimal = 0, platform_fee: Decimal = 0,
                          token_symbol: str = None) -> Optional[int]:
        """Registrar una transacción de token."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO token_transactions 
                        (user_id, token_address, token_symbol, tx_type, amount, 
                         fee_amount, platform_fee, tx_hash, from_address, to_address, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed')
                        RETURNING id
                    """, (
                        user_id, token_address, token_symbol, tx_type,
                        amount, fee, platform_fee, tx_hash, from_addr, to_addr
                    ))
                    tx_id = cur.fetchone()[0]
                    conn.commit()
                    return tx_id
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            return None
    
    def get_withdrawal_fee(self, token_address: str) -> Dict[str, Any]:
        """Obtener configuración de comisión de retiro para un token."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT fee_type, fee_value, min_withdrawal, max_withdrawal, is_active
                        FROM withdrawal_fees
                        WHERE token_address = %s AND is_active = TRUE
                    """, (token_address,))
                    
                    row = cur.fetchone()
                    if row:
                        return {
                            'fee_type': row[0],
                            'fee_value': float(row[1]),
                            'min_withdrawal': float(row[2]),
                            'max_withdrawal': float(row[3]) if row[3] else None,
                            'is_active': row[4]
                        }
                    
                    return {
                        'fee_type': 'percent',
                        'fee_value': 2.0,
                        'min_withdrawal': 0,
                        'max_withdrawal': None,
                        'is_active': True
                    }
        except Exception as e:
            logger.error(f"Error getting withdrawal fee: {e}")
            return {'fee_type': 'percent', 'fee_value': 2.0, 'min_withdrawal': 0}
    
    def sync_wallet_from_blockchain(self, user_id: str) -> Dict[str, Any]:
        """
        Sincronizar balances de wallet desde la blockchain.
        Consulta TON Center API para obtener balances reales.
        """
        try:
            wallet_result = self.get_or_create_wallet(user_id)
            if not wallet_result.get('success'):
                return wallet_result
            
            wallet_address = wallet_result['wallet']['address']
            
            base_url = self.TESTNET_API if self.use_testnet else self.TONCENTER_API_V3
            
            headers = {'Content-Type': 'application/json'}
            if self.toncenter_api_key:
                headers['X-API-Key'] = self.toncenter_api_key
            
            try:
                account_url = f"{base_url}/getAddressInformation?address={wallet_address}"
                response = requests.get(account_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok') and data.get('result'):
                        balance_nano = int(data['result'].get('balance', 0))
                        balance_ton = Decimal(balance_nano) / Decimal(10**9)
                        
                        self.update_token_balance(user_id, 'native', balance_ton, {
                            'symbol': 'TON',
                            'name': 'Toncoin',
                            'decimals': 9
                        })
            except Exception as e:
                logger.warning(f"Could not sync TON balance: {e}")
            
            try:
                jettons_url = f"{base_url.replace('/v2', '/v3')}/jetton/wallets?owner_address={wallet_address}&limit=100"
                if self.use_testnet:
                    jettons_url = f"https://testnet.toncenter.com/api/v3/jetton/wallets?owner_address={wallet_address}&limit=100"
                
                response = requests.get(jettons_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    jettons = data.get('jetton_wallets', [])
                    
                    for jetton in jettons:
                        try:
                            jetton_master = jetton.get('jetton', {}).get('address', '')
                            balance_raw = int(jetton.get('balance', 0))
                            metadata = jetton.get('jetton', {}).get('metadata', {})
                            
                            decimals = int(metadata.get('decimals', 9))
                            balance = Decimal(balance_raw) / Decimal(10**decimals)
                            
                            if balance > 0:
                                self.update_token_balance(user_id, jetton_master, balance, {
                                    'symbol': metadata.get('symbol', 'UNKNOWN'),
                                    'name': metadata.get('name', 'Unknown Token'),
                                    'decimals': decimals
                                })
                        except Exception as je:
                            logger.warning(f"Could not process jetton: {je}")
            except Exception as e:
                logger.warning(f"Could not sync jetton balances: {e}")
            
            return {
                'success': True,
                'message': 'Wallet synced with blockchain',
                'address': wallet_address
            }
            
        except Exception as e:
            logger.error(f"Error syncing wallet: {e}")
            return {'success': False, 'error': str(e)}
