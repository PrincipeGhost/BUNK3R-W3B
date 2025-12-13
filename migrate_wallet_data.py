#!/usr/bin/env python3
"""
Script de migración para agregar datos de billetera faltantes a usuarios existentes.
Crea wallets personales y balances de tokens principales para usuarios que no los tienen.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from bot.tracking_correos.database import DatabaseManager
from bot.tracking_correos.personal_wallet_service import PersonalWalletService

def migrate_wallet_data():
    """Migrar datos de billetera para usuarios existentes."""
    try:
        logger.info("Iniciando migración de datos de billetera...")
        
        db_manager = DatabaseManager()
        wallet_service = PersonalWalletService(db_manager)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.username, u.telegram_id, u.primary_wallet_address
                    FROM users u
                    LEFT JOIN user_wallets uw ON u.id = uw.user_id OR u.telegram_id::text = uw.user_id
                    WHERE uw.id IS NULL
                """)
                users_without_wallet = cur.fetchall()
                
                logger.info(f"Encontrados {len(users_without_wallet)} usuarios sin wallet personal")
                
                for user in users_without_wallet:
                    user_id = str(user[0])
                    username = user[1]
                    telegram_id = user[2]
                    
                    logger.info(f"Creando wallet para usuario: {username} (ID: {user_id})")
                    
                    result = wallet_service.get_or_create_wallet(user_id)
                    
                    if result.get('success'):
                        wallet_addr = result['wallet']['address']
                        logger.info(f"  ✓ Wallet creada: {wallet_addr[:20]}...")
                    else:
                        logger.error(f"  ✗ Error creando wallet: {result.get('error', 'Unknown')}")
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.username
                    FROM users u
                    LEFT JOIN token_balances tb ON u.id = tb.user_id
                    WHERE tb.id IS NULL
                    GROUP BY u.id, u.username
                """)
                users_without_tokens = cur.fetchall()
                
                logger.info(f"Encontrados {len(users_without_tokens)} usuarios sin balances de tokens")
                
                for user in users_without_tokens:
                    user_id = str(user[0])
                    username = user[1]
                    
                    logger.info(f"Inicializando tokens para usuario: {username} (ID: {user_id})")
                    
                    wallet_service._initialize_main_tokens(cur, user_id)
                    conn.commit()
                    logger.info(f"  ✓ Tokens inicializados para {username}")
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET security_score = COALESCE(security_score, 0)
                    WHERE security_score IS NULL
                """)
                updated = cur.rowcount
                if updated > 0:
                    logger.info(f"Inicializados security_score para {updated} usuarios")
                
                cur.execute("""
                    UPDATE users 
                    SET notification_preferences = '{"likes": true, "follows": true, "stories": true, "comments": true, "mentions": true, "push_enabled": true, "transactions": true}'::jsonb
                    WHERE notification_preferences IS NULL
                """)
                updated = cur.rowcount
                if updated > 0:
                    logger.info(f"Inicializados notification_preferences para {updated} usuarios")
                
                conn.commit()
        
        logger.info("=" * 50)
        logger.info("Resumen de la migración:")
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM user_wallets")
                total_wallets = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM token_balances")
                users_with_tokens = cur.fetchone()[0]
        
        logger.info(f"  Total usuarios: {total_users}")
        logger.info(f"  Wallets personales: {total_wallets}")
        logger.info(f"  Usuarios con tokens: {users_with_tokens}")
        logger.info("Migración completada exitosamente!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en la migración: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_wallet_data()
    sys.exit(0 if success else 1)
