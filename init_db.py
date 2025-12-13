"""
Database initialization script
Creates all required tables for the tracking system and social features
"""

import os
import sys
import logging
from bot.tracking_correos.models import CREATE_TABLES_SQL, CREATE_SOCIAL_TABLES_SQL, CREATE_ADMIN_TABLES_SQL, CREATE_ADVANCED_ADMIN_TABLES_SQL, CREATE_MULTITOKEN_WALLET_SQL
from bot.tracking_correos.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        logger.info("Initializing database connection...")
        db_manager = DatabaseManager()
        
        logger.info("Creating tracking tables...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLES_SQL)
                conn.commit()
        
        logger.info("Creating social/marketplace tables...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_SOCIAL_TABLES_SQL)
                conn.commit()
        
        logger.info("Creating admin/support tables...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_ADMIN_TABLES_SQL)
                conn.commit()
        
        logger.info("Creating advanced admin tables (risk scores, anomalies, messages)...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_ADVANCED_ADMIN_TABLES_SQL)
                conn.commit()
        
        logger.info("Creating multi-token wallet tables...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_MULTITOKEN_WALLET_SQL)
                conn.commit()
        
        logger.info("Database initialized successfully!")
        logger.info("All tables created (tracking + social features).")
        
        db_manager.initialize_database()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
