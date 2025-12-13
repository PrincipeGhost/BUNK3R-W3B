"""
Deposit Scheduler - Sistema de detección automática de depósitos B3C
Ejecuta polling periódico de wallets asignadas para detectar depósitos automáticamente.
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class DepositScheduler:
    """Scheduler para polling automático de depósitos en wallets del pool."""
    
    POLL_INTERVAL_SECONDS = 30
    EXPIRATION_CHECK_INTERVAL = 60
    MIN_POOL_CHECK_INTERVAL = 300
    CONSOLIDATION_INTERVAL = 60
    
    def __init__(self, db_manager, wallet_pool_service=None):
        """
        Inicializar el scheduler.
        
        Args:
            db_manager: Instancia de DatabaseManager
            wallet_pool_service: Instancia opcional de WalletPoolService
        """
        self.db = db_manager
        self._wallet_pool = wallet_pool_service
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_pool_check = 0
        self._last_expiration_check = 0
        self._last_consolidation_check = 0
        
        logger.info("DepositScheduler initialized")
    
    @property
    def wallet_pool(self):
        """Lazy-load wallet pool service."""
        if self._wallet_pool is None:
            from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
            self._wallet_pool = get_wallet_pool_service(self.db)
        return self._wallet_pool
    
    def start(self):
        """Iniciar el scheduler en un hilo de background."""
        if self._running:
            logger.warning("DepositScheduler already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("DepositScheduler started - polling every %d seconds", self.POLL_INTERVAL_SECONDS)
    
    def stop(self):
        """Detener el scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("DepositScheduler stopped")
    
    def _run_loop(self):
        """Loop principal del scheduler."""
        logger.info("[SCHEDULER] Background deposit detection loop started")
        
        self._ensure_pool_size()
        
        while self._running:
            try:
                self._check_pending_deposits()
                
                current_time = time.time()
                
                if current_time - self._last_consolidation_check > self.CONSOLIDATION_INTERVAL:
                    self._consolidate_deposits()
                    self._last_consolidation_check = current_time
                
                if current_time - self._last_expiration_check > self.EXPIRATION_CHECK_INTERVAL:
                    self._check_expired_wallets()
                    self._last_expiration_check = current_time
                
                if current_time - self._last_pool_check > self.MIN_POOL_CHECK_INTERVAL:
                    self._ensure_pool_size()
                    self._last_pool_check = current_time
                
            except Exception as e:
                logger.error(f"[SCHEDULER] Error in deposit check loop: {e}")
            
            time.sleep(self.POLL_INTERVAL_SECONDS)
    
    def _check_pending_deposits(self):
        """Verificar todas las wallets asignadas buscando depósitos."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT dw.assigned_to_purchase_id, dw.wallet_address, 
                               dw.assigned_to_user_id, dw.expected_amount
                        FROM deposit_wallets dw
                        JOIN b3c_purchases bp ON dw.assigned_to_purchase_id = bp.purchase_id
                        WHERE dw.status = 'assigned' 
                          AND bp.status = 'pending'
                          AND dw.expires_at > NOW()
                        ORDER BY dw.assigned_at ASC
                    """)
                    pending_wallets = cur.fetchall()
            
            if pending_wallets:
                logger.info(f"[SCHEDULER] Checking {len(pending_wallets)} pending deposits")
                
                for purchase_id, wallet_address, user_id, expected_amount in pending_wallets:
                    try:
                        logger.info(f"[SCHEDULER] Checking deposit for purchase {purchase_id}, wallet {wallet_address[:20]}...")
                        result = self.wallet_pool.check_deposit(purchase_id)
                        
                        if result.get('status') == 'confirmed':
                            logger.info(f"[SCHEDULER] DEPOSIT CONFIRMED for purchase {purchase_id}!")
                            self._send_notification(user_id, purchase_id, result)
                        elif result.get('status') == 'error':
                            logger.warning(f"[SCHEDULER] Error checking deposit for {purchase_id}: {result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"[SCHEDULER] Error checking purchase {purchase_id}: {e}")
            
        except Exception as e:
            logger.error(f"[SCHEDULER] Error in _check_pending_deposits: {e}")
    
    def _check_expired_wallets(self):
        """Liberar wallets expiradas sin depósito."""
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
                        RETURNING wallet_address, assigned_to_purchase_id
                    """)
                    expired = cur.fetchall()
                    
                    if expired:
                        for wallet_addr, purchase_id in expired:
                            cur.execute("""
                                UPDATE b3c_purchases 
                                SET status = 'expired'
                                WHERE purchase_id = %s AND status = 'pending'
                            """, (purchase_id,))
                        
                        conn.commit()
                        logger.info(f"[SCHEDULER] Released {len(expired)} expired wallets back to pool")
                        
        except Exception as e:
            logger.error(f"[SCHEDULER] Error in _check_expired_wallets: {e}")
    
    def _consolidate_deposits(self):
        """Consolidar depósitos confirmados a la wallet maestra."""
        try:
            consolidated = self.wallet_pool.consolidate_confirmed_deposits()
            if consolidated > 0:
                logger.info(f"[SCHEDULER] Successfully consolidated {consolidated} deposits to master wallet")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error consolidating deposits: {e}")
    
    def _ensure_pool_size(self):
        """Asegurar que el pool tenga suficientes wallets disponibles."""
        try:
            added = self.wallet_pool.ensure_minimum_pool_size()
            if added > 0:
                logger.info(f"[SCHEDULER] Added {added} new wallets to pool")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error ensuring pool size: {e}")
    
    def _send_notification(self, user_id: str, purchase_id: str, result: dict):
        """Enviar notificación al usuario cuando se detecta un depósito."""
        try:
            bot_token = os.environ.get('BOT_TOKEN', '')
            if not bot_token or user_id == '0':
                return
            
            import requests
            
            b3c_amount = result.get('b3c_credited', result.get('amount_received', 0))
            message = (
                f"✅ *¡Depósito confirmado!*\n\n"
                f"Tu compra de B3C ha sido procesada:\n"
                f"• ID: `{purchase_id}`\n"
                f"• B3C acreditados: *{b3c_amount:.2f}*\n"
                f"• TX: `{result.get('tx_hash', 'N/A')[:20]}...`\n\n"
                f"Los tokens ya están disponibles en tu wallet."
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"[SCHEDULER] Notification sent to user {user_id} for purchase {purchase_id}")
            else:
                logger.warning(f"[SCHEDULER] Failed to send notification: {response.text}")
                
        except Exception as e:
            logger.error(f"[SCHEDULER] Error sending notification: {e}")
    
    def get_status(self) -> dict:
        """Obtener estado del scheduler."""
        return {
            'running': self._running,
            'poll_interval': self.POLL_INTERVAL_SECONDS,
            'thread_alive': self._thread.is_alive() if self._thread else False
        }


_scheduler_instance: Optional[DepositScheduler] = None

def get_deposit_scheduler(db_manager) -> DepositScheduler:
    """Obtener o crear instancia singleton del scheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DepositScheduler(db_manager)
    return _scheduler_instance

def start_deposit_scheduler(db_manager) -> DepositScheduler:
    """Iniciar el scheduler de depósitos."""
    scheduler = get_deposit_scheduler(db_manager)
    if not scheduler._running:
        scheduler.start()
    return scheduler
