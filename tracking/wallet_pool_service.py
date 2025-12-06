"""
Wallet Pool Service - Sistema de wallets únicas para depósitos B3C (Sección 24)
Genera wallets temporales para cada compra, permitiendo identificación 100% segura de pagos.
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
    logger.info("tonsdk loaded successfully - real TON wallet generation enabled")
except ImportError:
    TONSDK_AVAILABLE = False
    logger.warning("tonsdk not available - using simulated wallet generation")


class WalletPoolService:
    """Servicio para gestionar el pool de wallets de depósito."""
    
    TONCENTER_API_V3 = 'https://toncenter.com/api/v3'
    TESTNET_API = 'https://testnet.toncenter.com/api/v2'
    CONSOLIDATION_FEE = Decimal('0.01')
    DEFAULT_EXPIRATION_MINUTES = 30
    MIN_POOL_SIZE = 10
    
    def __init__(self, db_manager, master_key: Optional[str] = None):
        """
        Inicializar el servicio.
        
        Args:
            db_manager: Instancia de DatabaseManager
            master_key: Clave maestra para encriptar private keys (de env var)
        """
        self.db = db_manager
        self.master_key = master_key or os.environ.get('WALLET_MASTER_KEY') or os.environ.get('ENCRYPTION_MASTER_KEY')
        self.hot_wallet = os.environ.get('B3C_HOT_WALLET', '')
        self.toncenter_api_key = os.environ.get('TONCENTER_API_KEY', '')
        self.use_testnet = os.environ.get('B3C_USE_TESTNET', 'true').lower() == 'true'
        
        if not self.master_key:
            raise ValueError("CRITICAL: ENCRYPTION_MASTER_KEY must be set! Cannot create wallets without encryption key.")
        
        self.encryption_key = self._derive_key(self.master_key)
        logger.info(f"WalletPoolService initialized - TONSDK: {TONSDK_AVAILABLE}, Testnet: {self.use_testnet}, HotWallet: {self.hot_wallet[:20] if self.hot_wallet else 'NOT SET'}...")
    
    def _derive_key(self, master_key: str) -> bytes:
        """Derivar clave de 32 bytes (AES-256) del master key usando SHA-256."""
        return hashlib.sha256(master_key.encode()).digest()
    
    def encrypt_private_key(self, data: str) -> str:
        """
        Encriptar datos usando AES-256-CBC con IV único.
        
        Args:
            data: Datos a encriptar (mnemonic o private key)
            
        Returns:
            String base64 con formato: IV:CIPHERTEXT
        """
        iv = secrets.token_bytes(16)
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        combined = base64.b64encode(iv).decode() + ':' + base64.b64encode(ciphertext).decode()
        return combined
    
    def decrypt_private_key(self, encrypted: str) -> str:
        """
        Desencriptar datos AES-256-CBC.
        
        Args:
            encrypted: String en formato IV:CIPHERTEXT (base64)
            
        Returns:
            Datos desencriptados
        """
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
            logger.error(f"Error decrypting private key: {e}")
            raise
    
    def generate_ton_wallet(self) -> Dict[str, Any]:
        """
        Generar un nuevo par de llaves TON válido usando tonsdk.
        
        Returns:
            Dict con address, mnemonic, public_key
        """
        if TONSDK_AVAILABLE:
            return self._generate_real_wallet()
        else:
            return self._generate_simulated_wallet()
    
    def _generate_real_wallet(self) -> Dict[str, Any]:
        """Generar wallet TON real usando tonsdk."""
        try:
            wallet_workchain = 0
            wallet_version = WalletVersionEnum.v4r2
            
            mnemonic = mnemonic_new()
            
            _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
                mnemonic, wallet_version, wallet_workchain
            )
            
            address = wallet.address.to_string(True, True, False)
            
            mnemonic_str = ' '.join(mnemonic)
            
            logger.info(f"Generated real TON wallet: {address[:20]}...")
            
            return {
                'address': address,
                'private_key': mnemonic_str,
                'public_key': _pub_k.hex() if isinstance(_pub_k, bytes) else str(_pub_k),
                'is_real': True
            }
        except Exception as e:
            logger.error(f"Error generating real TON wallet: {e}")
            return self._generate_simulated_wallet()
    
    def _generate_simulated_wallet(self) -> Dict[str, Any]:
        """Generar wallet simulada para desarrollo/testeo."""
        try:
            seed = secrets.token_bytes(32)
            private_key = hashlib.sha256(seed).hexdigest()
            public_key = hashlib.sha256(bytes.fromhex(private_key)).hexdigest()
            
            addr_hash = hashlib.sha256(f"{public_key}_deposit_{secrets.token_hex(4)}".encode()).hexdigest()
            
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'
            address_body = ''.join(chars[int(addr_hash[i:i+2], 16) % len(chars)] for i in range(0, 48, 2))
            address = f"UQ{address_body}"
            
            logger.warning(f"Generated SIMULATED wallet (not real TON): {address[:20]}...")
            
            return {
                'address': address,
                'private_key': private_key,
                'public_key': public_key,
                'is_real': False,
                'warning': 'SIMULATED - Install tonsdk for real wallets'
            }
        except Exception as e:
            logger.error(f"Error generating simulated wallet: {e}")
            raise
    
    def add_wallet_to_pool(self) -> Optional[str]:
        """
        Generar una nueva wallet y agregarla al pool.
        
        Returns:
            Dirección de la wallet agregada o None si falla
        """
        try:
            wallet = self.generate_ton_wallet()
            encrypted_key = self.encrypt_private_key(wallet['private_key'])
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO deposit_wallets (wallet_address, private_key_encrypted, public_key, status)
                        VALUES (%s, %s, %s, 'available')
                        RETURNING wallet_address
                    """, (wallet['address'], encrypted_key, wallet['public_key']))
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        logger.info(f"New wallet added to pool: {wallet['address'][:20]}...")
                        return result[0]
            return None
        except Exception as e:
            logger.error(f"Error adding wallet to pool: {e}")
            return None
    
    def ensure_minimum_pool_size(self, min_size: int = None) -> int:
        """
        Asegurar que el pool tenga un mínimo de wallets disponibles.
        
        Args:
            min_size: Tamaño mínimo del pool (default: MIN_POOL_SIZE)
            
        Returns:
            Número de wallets agregadas
        """
        min_size = min_size or self.MIN_POOL_SIZE
        added = 0
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM deposit_wallets WHERE status = 'available'")
                    available = cur.fetchone()[0]
                    
                    needed = max(0, min_size - available)
                    
            for _ in range(needed):
                if self.add_wallet_to_pool():
                    added += 1
                    
            if added > 0:
                logger.info(f"Added {added} wallets to pool (now have {available + added} available)")
                
            return added
        except Exception as e:
            logger.error(f"Error ensuring pool size: {e}")
            return 0
    
    def assign_wallet_for_purchase(self, user_id: str, ton_amount: float, 
                                    purchase_id: str) -> Optional[Dict[str, Any]]:
        """
        Asignar una wallet del pool para una compra específica.
        
        Args:
            user_id: ID del usuario de Telegram
            ton_amount: Cantidad de TON a depositar
            purchase_id: ID único de la compra
            
        Returns:
            Dict con datos de la wallet asignada o None si falla
        """
        try:
            expiration_minutes = self.DEFAULT_EXPIRATION_MINUTES
            expires_at = datetime.now() + timedelta(minutes=expiration_minutes)
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE deposit_wallets
                        SET status = 'assigned',
                            assigned_to_user_id = %s,
                            assigned_to_purchase_id = %s,
                            expected_amount = %s,
                            assigned_at = NOW(),
                            expires_at = %s
                        WHERE id = (
                            SELECT id FROM deposit_wallets 
                            WHERE status = 'available' 
                            ORDER BY created_at ASC 
                            LIMIT 1
                            FOR UPDATE SKIP LOCKED
                        )
                        RETURNING wallet_address, id
                    """, (user_id, purchase_id, ton_amount, expires_at))
                    
                    result = cur.fetchone()
                    
                    if not result:
                        conn.rollback()
                        self.add_wallet_to_pool()
                        
                        cur.execute("""
                            UPDATE deposit_wallets
                            SET status = 'assigned',
                                assigned_to_user_id = %s,
                                assigned_to_purchase_id = %s,
                                expected_amount = %s,
                                assigned_at = NOW(),
                                expires_at = %s
                            WHERE id = (
                                SELECT id FROM deposit_wallets 
                                WHERE status = 'available' 
                                ORDER BY created_at ASC 
                                LIMIT 1
                                FOR UPDATE
                            )
                            RETURNING wallet_address, id
                        """, (user_id, purchase_id, ton_amount, expires_at))
                        result = cur.fetchone()
                    
                    conn.commit()
                    
                    if result:
                        wallet_address, wallet_id = result
                        logger.info(f"Wallet {wallet_address[:20]}... assigned to purchase {purchase_id}")
                        
                        return {
                            'success': True,
                            'deposit_address': wallet_address,
                            'wallet_id': wallet_id,
                            'amount_to_send': float(ton_amount),
                            'amount_with_fee': float(Decimal(str(ton_amount)) + self.CONSOLIDATION_FEE),
                            'expires_at': expires_at.isoformat(),
                            'expires_in_minutes': expiration_minutes,
                            'purchase_id': purchase_id
                        }
            
            logger.error(f"No wallet available for purchase {purchase_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning wallet: {e}")
            return None
    
    def check_deposit(self, purchase_id: str) -> Dict[str, Any]:
        """
        Verificar si llegó un depósito para una compra.
        
        Args:
            purchase_id: ID de la compra
            
        Returns:
            Dict con estado del depósito
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, wallet_address, expected_amount, status, 
                               deposit_tx_hash, deposit_amount, expires_at,
                               assigned_to_user_id
                        FROM deposit_wallets 
                        WHERE assigned_to_purchase_id = %s
                    """, (purchase_id,))
                    
                    result = cur.fetchone()
                    
                    if not result:
                        return {
                            'success': False,
                            'error': 'Compra no encontrada',
                            'status': 'not_found'
                        }
                    
                    wallet_id, address, expected_amount, status, tx_hash, deposit_amount, expires_at, user_id = result
                    
                    if status == 'deposit_confirmed':
                        return {
                            'success': True,
                            'status': 'confirmed',
                            'tx_hash': tx_hash,
                            'amount_received': float(deposit_amount) if deposit_amount else 0,
                            'purchase_id': purchase_id
                        }
                    
                    if status == 'assigned':
                        is_expired = expires_at and datetime.now() > expires_at
                        
                        logger.info(f"[CHECK DEPOSIT] Purchase {purchase_id}: wallet={address[:20]}..., expired={is_expired}")
                        
                        deposit = self._check_wallet_for_deposit(address, float(expected_amount))
                        
                        if deposit.get('found'):
                            try:
                                cur.execute("""
                                    UPDATE deposit_wallets 
                                    SET status = 'deposit_confirmed',
                                        deposit_detected_at = NOW(),
                                        deposit_tx_hash = %s,
                                        deposit_amount = %s
                                    WHERE id = %s
                                """, (deposit['tx_hash'], deposit['amount'], wallet_id))
                                
                                credit_result = self._credit_b3c_to_user_atomic(cur, user_id, float(expected_amount), purchase_id)
                                
                                if credit_result:
                                    conn.commit()
                                    logger.info(f"[CHECK DEPOSIT] ATOMIC: Deposit confirmed + B3C credited for purchase {purchase_id}")
                                    
                                    self._send_purchase_notifications(user_id, credit_result['b3c_amount'], float(expected_amount), purchase_id)
                                else:
                                    conn.rollback()
                                    logger.error(f"[CHECK DEPOSIT] B3C credit failed, rolled back deposit for purchase {purchase_id}")
                                    return {
                                        'success': False,
                                        'status': 'error',
                                        'error': 'Failed to credit B3C, please contact support'
                                    }
                                
                            except Exception as e:
                                conn.rollback()
                                logger.error(f"[CHECK DEPOSIT] Atomic transaction failed: {e}")
                                return {
                                    'success': False,
                                    'status': 'error',
                                    'error': 'Transaction failed, please try again'
                                }
                            
                            return {
                                'success': True,
                                'status': 'confirmed',
                                'tx_hash': deposit['tx_hash'],
                                'amount_received': deposit['amount'],
                                'purchase_id': purchase_id
                            }
                        
                        if is_expired:
                            logger.info(f"[CHECK DEPOSIT] No deposit found and wallet expired, releasing...")
                            cur.execute("""
                                UPDATE deposit_wallets 
                                SET status = 'available',
                                    assigned_to_user_id = NULL,
                                    assigned_to_purchase_id = NULL,
                                    expected_amount = NULL,
                                    assigned_at = NULL,
                                    expires_at = NULL
                                WHERE id = %s
                            """, (wallet_id,))
                            conn.commit()
                            
                            return {
                                'success': True,
                                'status': 'expired',
                                'message': 'La dirección de depósito expiró sin recibir pago'
                            }
                        
                        return {
                            'success': True,
                            'status': 'pending',
                            'deposit_address': address,
                            'expected_amount': float(expected_amount),
                            'expires_at': expires_at.isoformat() if expires_at else None
                        }
                    
                    return {
                        'success': True,
                        'status': status,
                        'purchase_id': purchase_id
                    }
                    
        except Exception as e:
            logger.error(f"Error checking deposit: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'error'
            }
    
    def _check_wallet_for_deposit(self, wallet_address: str, expected_amount: float) -> Dict[str, Any]:
        """
        Consultar TonCenter API para verificar si llegó depósito a una wallet.
        
        Args:
            wallet_address: Dirección de la wallet
            expected_amount: Monto esperado
            
        Returns:
            Dict con resultado de la verificación
        """
        try:
            headers = {'Content-Type': 'application/json'}
            if self.toncenter_api_key:
                headers['X-API-Key'] = self.toncenter_api_key
            
            logger.info(f"[DEPOSIT CHECK] Wallet: {wallet_address}, Expected: {expected_amount} TON")
            logger.info(f"[DEPOSIT CHECK] API Key configured: {bool(self.toncenter_api_key)}, Testnet: {self.use_testnet}")
            
            if self.use_testnet:
                api_url = f'{self.TESTNET_API}/getTransactions'
                params = {
                    'address': wallet_address,
                    'limit': 10
                }
            else:
                api_url = f'{self.TONCENTER_API_V3}/transactions'
                params = {
                    'account': wallet_address,
                    'limit': 10,
                    'sort': 'desc'
                }
            
            logger.info(f"[DEPOSIT CHECK] Calling API: {api_url}")
            
            response = requests.get(
                api_url,
                params=params,
                headers=headers,
                timeout=15
            )
            
            logger.info(f"[DEPOSIT CHECK] API Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if self.use_testnet:
                    transactions = data.get('result', [])
                else:
                    transactions = data.get('transactions', [])
                
                logger.info(f"[DEPOSIT CHECK] Found {len(transactions)} transactions")
                
                for i, tx in enumerate(transactions):
                    in_msg = tx.get('in_msg', {})
                    if not in_msg:
                        logger.debug(f"[DEPOSIT CHECK] TX {i}: No in_msg, skipping")
                        continue
                    
                    value_raw = in_msg.get('value', 0)
                    source = in_msg.get('source', 'unknown')
                    
                    try:
                        value = int(value_raw) / 1e9 if value_raw else 0
                    except (ValueError, TypeError) as e:
                        logger.warning(f"[DEPOSIT CHECK] TX {i}: Error parsing value '{value_raw}': {e}")
                        continue
                    
                    logger.info(f"[DEPOSIT CHECK] TX {i}: value={value} TON, source={source[:20] if source else 'N/A'}...")
                    
                    if value >= expected_amount * 0.99:
                        if self.use_testnet:
                            tx_hash = tx.get('transaction_id', {}).get('hash', '')
                        else:
                            tx_hash = tx.get('hash', '')
                        
                        logger.info(f"[DEPOSIT CHECK] FOUND! TX hash: {tx_hash}, Amount: {value} TON")
                        
                        return {
                            'found': True,
                            'tx_hash': tx_hash,
                            'amount': value,
                            'from_address': source,
                            'timestamp': tx.get('utime', tx.get('now', 0))
                        }
                
                logger.info(f"[DEPOSIT CHECK] No matching transaction found (expected >= {expected_amount * 0.99} TON)")
                return {'found': False, 'transactions_checked': len(transactions)}
            
            logger.warning(f"[DEPOSIT CHECK] TonCenter API error: {response.status_code} - {response.text[:200]}")
            return {'found': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            logger.error(f"[DEPOSIT CHECK] Error checking wallet for deposit: {e}", exc_info=True)
            return {'found': False, 'error': str(e)}
    
    def _credit_b3c_to_user_atomic(self, cur, user_id: str, ton_amount: float, purchase_id: str) -> dict:
        """
        Acreditar B3C al usuario usando el cursor existente (para transacción atómica).
        USA EL b3c_amount ORIGINAL calculado al crear la orden, no recalcula.
        
        Args:
            cur: Cursor de la base de datos
            user_id: ID del usuario
            ton_amount: Cantidad de TON recibida
            purchase_id: ID de la compra
            
        Returns:
            dict con b3c_amount si es exitoso, None si falla
        """
        try:
            cur.execute("""
                SELECT b3c_amount, commission_ton FROM b3c_purchases 
                WHERE purchase_id = %s
            """, (purchase_id,))
            purchase_data = cur.fetchone()
            
            if not purchase_data:
                logger.error(f"[B3C CREDIT ATOMIC] Purchase {purchase_id} not found")
                return None
            
            b3c_amount = Decimal(str(purchase_data[0]))
            commission = Decimal(str(purchase_data[1]))
            
            logger.info(f"[B3C CREDIT ATOMIC] Using original b3c_amount={b3c_amount} from order creation (purchase {purchase_id})")
            
            cur.execute("""
                UPDATE b3c_purchases 
                SET status = 'confirmed',
                    confirmed_at = NOW()
                WHERE purchase_id = %s
            """, (purchase_id,))
            
            cur.execute("""
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, description, reference_id, created_at)
                VALUES (%s, 'b3c_purchase', %s, %s, %s, NOW())
            """, (user_id, float(b3c_amount), f'Compra B3C - {purchase_id}', purchase_id))
            
            cur.execute("""
                INSERT INTO b3c_commissions (transaction_type, reference_id, commission_ton)
                VALUES ('purchase', %s, %s)
            """, (purchase_id, float(commission)))
            
            logger.info(f"[B3C CREDIT ATOMIC] Prepared credit of {b3c_amount} B3C for user {user_id}, purchase {purchase_id}")
            
            return {'b3c_amount': float(b3c_amount), 'commission': float(commission)}
            
        except Exception as e:
            logger.error(f"[B3C CREDIT ATOMIC] Error preparing B3C credit: {e}")
            return None
    
    def _credit_b3c_to_user(self, user_id: str, ton_amount: float, purchase_id: str) -> bool:
        """
        Acreditar B3C al usuario después de confirmar depósito.
        USA EL b3c_amount ORIGINAL calculado al crear la orden, no recalcula.
        
        Args:
            user_id: ID del usuario
            ton_amount: Cantidad de TON recibida
            purchase_id: ID de la compra
            
        Returns:
            True si se acreditó correctamente
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT b3c_amount, commission_ton FROM b3c_purchases 
                        WHERE purchase_id = %s
                    """, (purchase_id,))
                    purchase_data = cur.fetchone()
                    
                    if not purchase_data:
                        logger.error(f"[B3C CREDIT] Purchase {purchase_id} not found")
                        return False
                    
                    b3c_amount = Decimal(str(purchase_data[0]))
                    commission = Decimal(str(purchase_data[1]))
                    
                    logger.info(f"[B3C CREDIT] Using original b3c_amount={b3c_amount} from order creation (purchase {purchase_id})")
                    
                    cur.execute("""
                        UPDATE b3c_purchases 
                        SET status = 'confirmed',
                            confirmed_at = NOW()
                        WHERE purchase_id = %s
                    """, (purchase_id,))
                    
                    cur.execute("""
                        INSERT INTO wallet_transactions (user_id, transaction_type, amount, description, reference_id)
                        VALUES (%s, 'b3c_purchase', %s, %s, %s)
                    """, (user_id, float(b3c_amount), f'Compra B3C - {purchase_id}', purchase_id))
                    
                    cur.execute("""
                        INSERT INTO b3c_commissions (transaction_type, reference_id, commission_ton)
                        VALUES ('purchase', %s, %s)
                    """, (purchase_id, float(commission)))
                    
                    conn.commit()
                    
            logger.info(f"[B3C CREDIT] Credited {b3c_amount} B3C to user {user_id} for purchase {purchase_id}")
            
            self._send_purchase_notifications(user_id, float(b3c_amount), float(ton_amount), purchase_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error crediting B3C: {e}")
            return False
    
    def _send_purchase_notifications(self, user_id: str, b3c_amount: float, ton_amount: float, purchase_id: str):
        """
        Enviar notificaciones de compra exitosa.
        
        Args:
            user_id: ID del usuario
            b3c_amount: Cantidad de B3C acreditados
            ton_amount: Cantidad de TON pagados
            purchase_id: ID de la compra
        """
        try:
            bot_token = os.environ.get('BOT_TOKEN', '')
            owner_id = os.environ.get('OWNER_TELEGRAM_ID', '')
            
            if not bot_token:
                logger.warning("[NOTIFICATION] BOT_TOKEN not configured, skipping notifications")
                return
            
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            user_message = (
                f"Tu compra fue exitosa.\n\n"
                f"+{b3c_amount:.2f} B3C acreditados a tu cuenta.\n"
                f"Pagaste: {ton_amount} TON\n"
                f"ID: {purchase_id}"
            )
            
            try:
                response = requests.post(api_url, json={
                    'chat_id': user_id,
                    'text': user_message,
                    'parse_mode': 'HTML'
                }, timeout=5)
                if response.status_code == 200:
                    logger.info(f"[NOTIFICATION] Sent purchase confirmation to user {user_id}")
                else:
                    logger.warning(f"[NOTIFICATION] Failed to notify user {user_id}: {response.text}")
            except Exception as e:
                logger.warning(f"[NOTIFICATION] Error sending to user {user_id}: {e}")
            
            if owner_id and owner_id != user_id:
                owner_message = (
                    f"Nueva compra B3C recibida\n\n"
                    f"Usuario: {user_id}\n"
                    f"B3C: +{b3c_amount:.2f}\n"
                    f"TON: {ton_amount}\n"
                    f"ID: {purchase_id}"
                )
                
                try:
                    response = requests.post(api_url, json={
                        'chat_id': owner_id,
                        'text': owner_message,
                        'parse_mode': 'HTML'
                    }, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"[NOTIFICATION] Sent purchase alert to owner {owner_id}")
                    else:
                        logger.warning(f"[NOTIFICATION] Failed to notify owner: {response.text}")
                except Exception as e:
                    logger.warning(f"[NOTIFICATION] Error sending to owner: {e}")
                    
        except Exception as e:
            logger.error(f"[NOTIFICATION] Error in send_purchase_notifications: {e}")
    
    def release_expired_wallets(self) -> int:
        """
        Liberar wallets expiradas que no recibieron depósito.
        
        Returns:
            Número de wallets liberadas
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE deposit_wallets 
                        SET status = 'available',
                            assigned_to_user_id = NULL,
                            assigned_to_purchase_id = NULL,
                            expected_amount = NULL,
                            assigned_at = NULL,
                            expires_at = NULL
                        WHERE status = 'assigned' 
                        AND expires_at < NOW()
                        RETURNING id
                    """)
                    released = cur.rowcount
                    conn.commit()
                    
                    if released > 0:
                        logger.info(f"Released {released} expired wallets back to pool")
                    
                    return released
        except Exception as e:
            logger.error(f"Error releasing expired wallets: {e}")
            return 0
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del pool de wallets.
        
        Returns:
            Dict con estadísticas
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT status, COUNT(*) 
                        FROM deposit_wallets 
                        GROUP BY status
                    """)
                    
                    stats = {'total': 0}
                    for row in cur.fetchall():
                        stats[row[0]] = row[1]
                        stats['total'] += row[1]
                    
                    return {
                        'success': True,
                        'pool_stats': stats,
                        'available': stats.get('available', 0),
                        'assigned': stats.get('assigned', 0),
                        'deposit_confirmed': stats.get('deposit_confirmed', 0),
                        'consolidated': stats.get('consolidated', 0),
                        'total': stats['total']
                    }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_wallet_seqno(self, address: str) -> int:
        """
        Obtener el seqno (sequence number) de una wallet para la transacción.
        
        Args:
            address: Dirección de la wallet
            
        Returns:
            Seqno de la wallet (0 si es nueva o error)
        """
        try:
            api_url = f"{self.TONCENTER_API_V3}/wallet"
            params = {'address': address}
            
            if self.toncenter_api_key:
                params['api_key'] = self.toncenter_api_key
            
            response = requests.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                seqno = data.get('seqno', 0)
                logger.info(f"Got seqno {seqno} for wallet {address[:20]}...")
                return seqno
            else:
                logger.warning(f"Failed to get seqno for {address[:20]}...: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting wallet seqno: {e}")
            return 0
    
    def _send_ton_transfer(self, mnemonic: str, to_address: str, amount_nano: int) -> Optional[str]:
        """
        Enviar TON desde una wallet a otra dirección.
        
        Args:
            mnemonic: Mnemonic de 24 palabras de la wallet origen
            to_address: Dirección destino
            amount_nano: Cantidad en nanoTON
            
        Returns:
            Hash de la transacción o None si falla
        """
        if not TONSDK_AVAILABLE:
            logger.error("tonsdk not available - cannot send real transfers")
            return None
        
        try:
            from tonsdk.utils import bytes_to_b64str
            
            mnemonic_list = mnemonic.split(' ')
            
            _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
                mnemonic_list, 
                WalletVersionEnum.v4r2, 
                0
            )
            
            from_address = wallet.address.to_string(True, True, False)
            logger.info(f"Sending {amount_nano} nanoTON from {from_address[:20]}... to {to_address[:20]}...")
            
            seqno = self._get_wallet_seqno(from_address)
            
            query = wallet.create_transfer_message(
                to_addr=to_address,
                amount=amount_nano,
                seqno=seqno,
                payload="B3C consolidation"
            )
            
            boc = bytes_to_b64str(query["message"].to_boc(False))
            
            send_url = "https://toncenter.com/api/v2/sendBoc"
            send_data = {'boc': boc}
            
            headers = {'Content-Type': 'application/json'}
            if self.toncenter_api_key:
                headers['X-API-Key'] = self.toncenter_api_key
            
            response = requests.post(send_url, json=send_data, headers=headers, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                tx_hash = result.get('result', {}).get('hash', f"tx_{seqno}")
                logger.info(f"Transaction sent successfully! Hash: {tx_hash}")
                return tx_hash
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Transaction failed: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending TON transfer: {e}")
            return None
    
    def consolidate_confirmed_deposits(self) -> int:
        """
        Consolidar fondos de wallets con depósitos confirmados a la hot wallet.
        Realiza transferencias reales de TON.
        
        Returns:
            Número de wallets consolidadas
        """
        consolidated = 0
        
        if not self.hot_wallet:
            logger.error("B3C_HOT_WALLET not configured - cannot consolidate")
            return 0
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, wallet_address, private_key_encrypted, deposit_amount
                        FROM deposit_wallets 
                        WHERE status = 'deposit_confirmed'
                        AND deposit_amount > 0
                        LIMIT 10
                    """)
                    
                    wallets = cur.fetchall()
                    
                    if not wallets:
                        logger.info("No wallets pending consolidation")
                        return 0
                    
                    logger.info(f"Found {len(wallets)} wallets to consolidate")
                    
                    for wallet in wallets:
                        wallet_id, address, encrypted_key, amount = wallet
                        
                        try:
                            mnemonic = self.decrypt_private_key(encrypted_key)
                            
                            amount_nano = int(Decimal(str(amount)) * Decimal('1000000000'))
                            
                            fee_nano = int(self.CONSOLIDATION_FEE * Decimal('1000000000'))
                            send_amount = amount_nano - fee_nano
                            
                            if send_amount <= 0:
                                logger.warning(f"Wallet {wallet_id} has insufficient funds after fee")
                                continue
                            
                            logger.info(f"Consolidating wallet {wallet_id}: {amount} TON -> {self.hot_wallet[:20]}...")
                            
                            tx_hash = self._send_ton_transfer(mnemonic, self.hot_wallet, send_amount)
                            
                            if tx_hash:
                                cur.execute("""
                                    UPDATE deposit_wallets 
                                    SET status = 'consolidated',
                                        consolidation_tx_hash = %s,
                                        consolidated_at = NOW()
                                    WHERE id = %s
                                """, (tx_hash, wallet_id))
                                consolidated += 1
                                logger.info(f"Wallet {wallet_id} consolidated successfully. TX: {tx_hash}")
                            else:
                                logger.error(f"Failed to consolidate wallet {wallet_id}")
                            
                        except Exception as e:
                            logger.error(f"Error consolidating wallet {wallet_id}: {e}")
                            continue
                    
                    conn.commit()
                    
            if consolidated > 0:
                logger.info(f"Successfully consolidated {consolidated} wallets to hot wallet")
                
            return consolidated
            
        except Exception as e:
            logger.error(f"Error in consolidation batch: {e}")
            return 0


_wallet_pool_service = None

def get_wallet_pool_service(db_manager=None):
    """Obtener instancia singleton del servicio."""
    global _wallet_pool_service
    if _wallet_pool_service is None and db_manager:
        _wallet_pool_service = WalletPoolService(db_manager)
    return _wallet_pool_service
