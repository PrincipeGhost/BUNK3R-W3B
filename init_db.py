"""
Database initialization script
Creates all required tables for the tracking system
"""

import os
import sys
import logging
from tracking.models import CREATE_TABLES_SQL
from tracking.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        logger.info("Initializing database connection...")
        db_manager = DatabaseManager()
        
        logger.info("Creating tables...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Execute the table creation SQL
                cur.execute(CREATE_TABLES_SQL)
                conn.commit()
        
        logger.info("Database initialized successfully!")
        logger.info("All tables created and default data inserted.")
        
        # Verify tables exist
        db_manager.initialize_database()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
