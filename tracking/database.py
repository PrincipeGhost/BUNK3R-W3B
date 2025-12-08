"""
Database connection and operations for the tracking system
"""

import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
from typing import List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import random
from contextlib import contextmanager
import threading

try:
    import pytz
    SPAIN_TZ = pytz.timezone('Europe/Madrid')
except ImportError:
    SPAIN_TZ = None

from .models import Tracking, ShippingRoute, StatusHistory, CREATE_TABLES_SQL, CREATE_ENCRYPTED_POSTS_SQL, CREATE_VIRTUAL_NUMBERS_SQL

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple time-based cache for infrequently changing data"""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, max_age_seconds: int = 300):
        """Get cached value if not expired"""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if datetime.now() - timestamp < timedelta(seconds=max_age_seconds):
                    return value
                del self._cache[key]
        return None
    
    def set(self, key: str, value):
        """Set cache value with current timestamp"""
        with self._lock:
            self._cache[key] = (value, datetime.now())
    
    def invalidate(self, key: str = None):
        """Invalidate specific key or all cache"""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()


_stats_cache = SimpleCache()


class PooledConnection:
    """Wrapper for pooled connections that returns them to the pool on exit"""
    
    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool
    
    def __enter__(self):
        return self._conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        try:
            if self._pool is not None and self._conn is not None:
                self._pool.putconn(self._conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
        return False
    
    def __getattr__(self, name):
        return getattr(self._conn, name)


class DatabaseManager:
    """Handle all database operations with connection pooling"""
    
    _pool = None
    _pool_lock = threading.Lock()
    MIN_CONNECTIONS = 2
    MAX_CONNECTIONS = 10
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        self.database_url = self.database_url.strip()
        
        if self.database_url.startswith('postgresql+asyncpg://'):
            self.database_url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        if 'sslmode=' not in self.database_url:
            separator = '&' if '?' in self.database_url else '?'
            self.database_url = f"{self.database_url}{separator}sslmode=require"
        
        self._init_pool()
        logger.info("Database connection configured using DATABASE_URL with connection pooling")
    
    def _init_pool(self):
        """Initialize the connection pool"""
        with DatabaseManager._pool_lock:
            if DatabaseManager._pool is None:
                try:
                    DatabaseManager._pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=self.MIN_CONNECTIONS,
                        maxconn=self.MAX_CONNECTIONS,
                        dsn=self.database_url
                    )
                    logger.info(f"Connection pool initialized (min={self.MIN_CONNECTIONS}, max={self.MAX_CONNECTIONS})")
                except Exception as e:
                    logger.error(f"Failed to initialize connection pool: {e}")
                    raise
    
    def get_connection(self):
        """Get a connection from the pool wrapped for automatic return"""
        try:
            if DatabaseManager._pool is None:
                self._init_pool()
            conn = DatabaseManager._pool.getconn()
            return PooledConnection(conn, DatabaseManager._pool)
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        try:
            if DatabaseManager._pool is not None and conn is not None:
                raw_conn = conn._conn if isinstance(conn, PooledConnection) else conn
                DatabaseManager._pool.putconn(raw_conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections with automatic return to pool"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool"""
        with cls._pool_lock:
            if cls._pool is not None:
                cls._pool.closeall()
                cls._pool = None
                logger.info("Connection pool closed")
    
    def initialize_database(self):
        """Initialize database connection and verify tables exist"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Just verify that the required tables exist
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('trackings', 'shipping_routes', 'status_history')
                    """)
                    tables = cur.fetchall()
                    if len(tables) < 3:
                        logger.warning(f"Some tables missing. Found: {[t[0] for t in tables]}")
                        logger.warning("Expected: trackings, shipping_routes, status_history")
                    else:
                        logger.info("All required database tables found")
            logger.info("Database connection verified successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_tracking(self, tracking: Tracking, created_by_admin_id: Optional[int] = None) -> bool:
        """Save a new tracking to database and create initial history entries"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Parse the date_time to use as created_at
                    try:
                        parsed_datetime = datetime.strptime(tracking.date_time, "%d/%m/%Y %H:%M")
                    except ValueError:
                        logger.warning(f"Could not parse date_time '{tracking.date_time}', using current timestamp")
                        parsed_datetime = None
                    
                    if parsed_datetime:
                        sql = """
                        INSERT INTO trackings (
                            tracking_id, delivery_address, date_time, package_weight, product_name,
                            sender_address, product_price, recipient_postal_code, recipient_province,
                            recipient_country, sender_postal_code, sender_province, sender_country,
                            status, estimated_delivery_date, user_telegram_id, username,
                            created_by_admin_id, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(sql, (
                            tracking.tracking_id, tracking.delivery_address, tracking.date_time,
                            tracking.package_weight, tracking.product_name, tracking.sender_address,
                            tracking.product_price, tracking.recipient_postal_code, tracking.recipient_province,
                            tracking.recipient_country, tracking.sender_postal_code, tracking.sender_province,
                            tracking.sender_country, tracking.status, tracking.estimated_delivery_date,
                            tracking.user_telegram_id, tracking.username, created_by_admin_id,
                            parsed_datetime, parsed_datetime
                        ))
                    else:
                        sql = """
                        INSERT INTO trackings (
                            tracking_id, delivery_address, date_time, package_weight, product_name,
                            sender_address, product_price, recipient_postal_code, recipient_province,
                            recipient_country, sender_postal_code, sender_province, sender_country,
                            status, estimated_delivery_date, user_telegram_id, username,
                            created_by_admin_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(sql, (
                            tracking.tracking_id, tracking.delivery_address, tracking.date_time,
                            tracking.package_weight, tracking.product_name, tracking.sender_address,
                            tracking.product_price, tracking.recipient_postal_code, tracking.recipient_province,
                            tracking.recipient_country, tracking.sender_postal_code, tracking.sender_province,
                            tracking.sender_country, tracking.status, tracking.estimated_delivery_date,
                            tracking.user_telegram_id, tracking.username, created_by_admin_id
                        ))
                    
                    # Create initial history entries with the same timestamp
                    # 1. Paquete recibido en oficinas
                    sender_location = tracking.sender_province if tracking.sender_province else tracking.sender_country
                    if parsed_datetime:
                        cur.execute(
                            "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                            (tracking.tracking_id, None, "RECIBIDO", f"Paquete recibido en oficinas de {sender_location}", parsed_datetime)
                        )
                    else:
                        cur.execute(
                            "INSERT INTO status_history (tracking_id, old_status, new_status, notes) VALUES (%s, %s, %s, %s)",
                            (tracking.tracking_id, None, "RECIBIDO", f"Paquete recibido en oficinas de {sender_location}")
                        )
                    
                    # 2. Esperando confirmación de pago
                    if parsed_datetime:
                        cur.execute(
                            "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                            (tracking.tracking_id, "RECIBIDO", "ESPERANDO_PAGO", "Esperando confirmación de pago", parsed_datetime)
                        )
                    else:
                        cur.execute(
                            "INSERT INTO status_history (tracking_id, old_status, new_status, notes) VALUES (%s, %s, %s, %s)",
                            (tracking.tracking_id, "RECIBIDO", "ESPERANDO_PAGO", "Esperando confirmación de pago")
                        )
                    
                    conn.commit()
            logger.info(f"Tracking {tracking.tracking_id} saved successfully with initial history")
            return True
        except Exception as e:
            logger.error(f"Error saving tracking: {e}")
            return False
    
    def get_tracking(self, tracking_id: str) -> Optional[Tracking]:
        """Get tracking by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM trackings WHERE tracking_id = %s", (tracking_id,))
                    row = cur.fetchone()
                    if row:
                        return Tracking(**dict(row))
            return None
        except Exception as e:
            logger.error(f"Error getting tracking {tracking_id}: {e}")
            return None
    
    def can_access_tracking(self, tracking_id: str, admin_id: int, is_owner: bool = False) -> bool:
        """Check if admin can access this tracking"""
        if is_owner:
            return True  # Owner can access everything
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT created_by_admin_id, user_telegram_id FROM trackings WHERE tracking_id = %s",
                        (tracking_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        return False  # Tracking doesn't exist
                    
                    created_by, user_id = row
                    # Admin can access if they created it OR if it's for them
                    return created_by == admin_id or user_id == admin_id
        except Exception as e:
            logger.error(f"Error checking access for tracking {tracking_id}: {e}")
            return False
    
    def get_trackings_by_status(self, status: str, admin_id: int, is_owner: bool = False) -> List[Tracking]:
        """Get all trackings with specific status, filtered by admin if not owner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if is_owner:
                        # Owner sees everything
                        cur.execute(
                            "SELECT * FROM trackings WHERE status = %s ORDER BY created_at DESC",
                            (status,)
                        )
                    else:
                        # Admin sees trackings they created OR trackings created for them
                        cur.execute(
                            "SELECT * FROM trackings WHERE status = %s AND (created_by_admin_id = %s OR user_telegram_id = %s) ORDER BY created_at DESC",
                            (status, admin_id, admin_id)
                        )
                    rows = cur.fetchall()
                    return [Tracking(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting trackings by status {status}: {e}")
            return []
    
    def update_tracking_status(self, tracking_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """Update tracking status and log the change"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get current status
                    cur.execute("SELECT status FROM trackings WHERE tracking_id = %s", (tracking_id,))
                    result = cur.fetchone()
                    if not result:
                        return False
                    
                    old_status = result[0] if result else None
                    if not old_status:
                        return False
                    
                    # Update status
                    cur.execute(
                        "UPDATE trackings SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE tracking_id = %s",
                        (new_status, tracking_id)
                    )
                    
                    # Log status change
                    cur.execute(
                        "INSERT INTO status_history (tracking_id, old_status, new_status, notes) VALUES (%s, %s, %s, %s)",
                        (tracking_id, old_status, new_status, notes)
                    )
                    
                    conn.commit()
            logger.info(f"Tracking {tracking_id} status updated from {old_status} to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Error updating tracking status: {e}")
            return False
    
    def add_delay_to_tracking(self, tracking_id: str, delay_days: int, reason: str) -> bool:
        """Add delay to tracking and update estimated delivery"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE trackings SET actual_delay_days = actual_delay_days + %s, updated_at = CURRENT_TIMESTAMP WHERE tracking_id = %s",
                        (delay_days, tracking_id)
                    )
                    
                    # Log the delay
                    cur.execute(
                        "INSERT INTO status_history (tracking_id, old_status, new_status, notes) VALUES (%s, %s, %s, %s)",
                        (tracking_id, "DELAY_ADDED", "DELAY_ADDED", f"Retraso de {delay_days} días: {reason}")
                    )
                    
                    conn.commit()
            logger.info(f"Added {delay_days} days delay to tracking {tracking_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding delay to tracking: {e}")
            return False
    
    def get_shipping_route(self, origin: str, destination: str) -> Optional[ShippingRoute]:
        """Get shipping route between countries"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM shipping_routes WHERE origin_country = %s AND destination_country = %s",
                        (origin, destination)
                    )
                    row = cur.fetchone()
                    if row:
                        return ShippingRoute(**dict(row))
            return None
        except Exception as e:
            logger.error(f"Error getting shipping route: {e}")
            return None
    
    def generate_route_history_events(self, tracking_id: str, checkpoints: List, 
                                       estimated_days: int = 5, start_datetime: Optional[datetime] = None) -> bool:
        """
        Generate history events for each checkpoint along the route with distributed timestamps.
        Creates 'Salió de' and 'Llegó a' events for each locality/city.
        
        Uses realistic processing times per stop (~8-12 hours) and varied hours
        to make tracking look natural and not robotic.
        
        Args:
            tracking_id: Tracking ID
            checkpoints: List of checkpoint dicts [{"name": "Madrid", "type": "origin|transit|destination"}]
                        OR list of strings (legacy format) ["Madrid", "Toledo", "Ourense"]
            estimated_days: Number of days estimated for the route (default 5)
            start_datetime: When the package started transit (default: now)
        
        Returns:
            True if successful
        """
        try:
            if not checkpoints or len(checkpoints) == 0:
                logger.warning(f"No checkpoints provided for tracking {tracking_id}")
                return False
            
            import html
            import re
            
            def sanitize_location_name(name: str) -> str:
                """Sanitize location names to prevent XSS/injection."""
                if not name:
                    return ""
                name = str(name).strip()[:100]
                name = re.sub(r'[<>"\'\\/;`]', '', name)
                name = html.escape(name)
                return name
            
            if isinstance(checkpoints[0], dict):
                state_names = [sanitize_location_name(cp.get("name", "")) for cp in checkpoints if cp.get("name")]
            else:
                state_names = [sanitize_location_name(str(cp)) for cp in checkpoints if cp]
            
            if len(state_names) == 0:
                logger.warning(f"No valid state names in checkpoints for tracking {tracking_id}")
                return False
            
            if start_datetime is None:
                start_datetime = datetime.now()
            
            total_events = 0
            for i in range(len(state_names)):
                if i == 0:
                    total_events += 1
                elif i == len(state_names) - 1:
                    total_events += 1
                else:
                    total_events += 2
            
            total_hours = estimated_days * 24
            min_total_hours = max(48, total_hours)
            
            hours_per_event = min_total_hours / max(total_events, 1)
            hours_per_event = max(6, min(18, hours_per_event))
            
            def adjust_to_work_hours(event_time: datetime) -> datetime:
                """Adjust timestamp to work hours (6:00-21:59) without going backwards in time"""
                hour = event_time.hour
                minute = random.randint(0, 59)
                
                if hour < 6:
                    new_hour = random.randint(7, 11)
                    event_time = event_time.replace(hour=new_hour, minute=minute)
                elif hour >= 22:
                    event_time = event_time + timedelta(days=1)
                    new_hour = random.randint(6, 10)
                    event_time = event_time.replace(hour=new_hour, minute=minute)
                else:
                    event_time = event_time.replace(minute=minute)
                
                return event_time
            
            def generate_event_time(event_index: int, previous_time: Optional[datetime] = None) -> datetime:
                """Generate a realistic timestamp for an event with natural variation.
                GUARANTEES: result > previous_time (strictly ascending)"""
                base_hours = event_index * hours_per_event
                
                variation_range = hours_per_event * 0.3
                variation = random.uniform(-variation_range, variation_range)
                actual_hours = max(0, base_hours + variation)
                
                event_time = start_datetime + timedelta(hours=actual_hours)
                
                event_time = adjust_to_work_hours(event_time)
                
                if previous_time and event_time <= previous_time:
                    min_gap = random.uniform(4, 10)
                    event_time = previous_time + timedelta(hours=min_gap)
                    event_time = adjust_to_work_hours(event_time)
                    
                    if event_time <= previous_time:
                        event_time = previous_time + timedelta(hours=random.uniform(5, 12))
                
                return event_time
            
            def generate_departure_time(arrival_time: datetime) -> datetime:
                """Generate departure time after arrival with processing delay.
                GUARANTEES: result > arrival_time (strictly ascending)"""
                processing_hours = random.uniform(6, 14)
                departure = arrival_time + timedelta(hours=processing_hours)
                
                departure = adjust_to_work_hours(departure)
                
                if departure <= arrival_time:
                    departure = arrival_time + timedelta(hours=random.uniform(8, 14))
                
                return departure
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    event_index = 0
                    last_event_time = None
                    
                    if len(state_names) >= 1:
                        event_time = generate_event_time(event_index, None)
                        cur.execute(
                            "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                            (tracking_id, "EN_TRANSITO", "SALIO_ORIGEN", f"Salió de oficinas de {state_names[0]}", event_time)
                        )
                        event_index += 1
                        last_event_time = event_time
                        logger.debug(f"Event 'Salió de {state_names[0]}' at {event_time}")
                    
                    for i in range(1, len(state_names)):
                        state = state_names[i]
                        is_last = (i == len(state_names) - 1)
                        
                        if is_last:
                            event_time = generate_event_time(event_index, last_event_time)
                            
                            min_final_gap = timedelta(hours=max(24, estimated_days * 12))
                            if event_time < start_datetime + min_final_gap:
                                event_time = start_datetime + min_final_gap + timedelta(hours=random.uniform(-4, 8))
                            
                            hour = event_time.hour
                            if hour < 8 or hour > 20:
                                event_time = event_time.replace(hour=random.randint(10, 18), minute=random.randint(0, 59))
                            
                            cur.execute(
                                "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                                (tracking_id, "EN_RUTA", "LLEGO_DESTINO", f"Llegó a oficina de {state}", event_time)
                            )
                            logger.debug(f"Event 'Llegó a {state}' (destino) at {event_time}")
                        else:
                            arrival_time = generate_event_time(event_index, last_event_time)
                            cur.execute(
                                "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                                (tracking_id, "EN_RUTA", "LLEGO_A", f"Llegó a oficina de {state}", arrival_time)
                            )
                            logger.debug(f"Event 'Llegó a {state}' at {arrival_time}")
                            event_index += 1
                            
                            departure_time = generate_departure_time(arrival_time)
                            cur.execute(
                                "INSERT INTO status_history (tracking_id, old_status, new_status, notes, changed_at) VALUES (%s, %s, %s, %s, %s)",
                                (tracking_id, "LLEGO_A", "SALIO_DE", f"Salió de oficinas de {state}", departure_time)
                            )
                            logger.debug(f"Event 'Salió de {state}' at {departure_time}")
                            event_index += 1
                            last_event_time = departure_time
                    
                    conn.commit()
            
            logger.info(f"Generated route history events for tracking {tracking_id} with {len(state_names)} checkpoints over {estimated_days} days: {state_names}")
            return True
        except Exception as e:
            logger.error(f"Error generating route history: {e}")
            return False
    
    def get_tracking_history(self, tracking_id: str, include_future: bool = False, limit: int = 100) -> List[StatusHistory]:
        """Get status change history for tracking
        
        Args:
            tracking_id: Tracking ID
            include_future: If True, includes future scheduled events. 
                           If False (default), only shows events up to current time.
            limit: Maximum number of history entries to return (default: 100)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if include_future:
                        cur.execute(
                            "SELECT * FROM status_history WHERE tracking_id = %s ORDER BY changed_at ASC, id ASC LIMIT %s",
                            (tracking_id, limit)
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM status_history WHERE tracking_id = %s AND (changed_at IS NULL OR changed_at <= NOW()) ORDER BY changed_at ASC, id ASC LIMIT %s",
                            (tracking_id, limit)
                        )
                    rows = cur.fetchall()
                    return [StatusHistory(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting tracking history: {e}")
            return []
    
    def get_statistics(self, admin_id: int, is_owner: bool = False, use_cache: bool = True) -> dict:
        """Get tracking statistics, filtered by admin if not owner
        
        Args:
            admin_id: Admin ID to filter statistics
            is_owner: If True, shows all statistics
            use_cache: If True, uses cached results for 60 seconds
        """
        cache_key = f"stats_{admin_id}_{is_owner}"
        
        if use_cache:
            cached = _stats_cache.get(cache_key, max_age_seconds=60)
            if cached is not None:
                return cached
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    stats = {}
                    
                    if is_owner:
                        # Owner sees all statistics
                        # Count by status
                        cur.execute("SELECT status, COUNT(*) FROM trackings GROUP BY status")
                        status_counts = cur.fetchall()
                        stats['by_status'] = {status: count for status, count in status_counts}
                        
                        # Total trackings
                        cur.execute("SELECT COUNT(*) FROM trackings")
                        total_result = cur.fetchone()
                        stats['total'] = total_result[0] if total_result else 0
                        
                        # Today's trackings
                        cur.execute("SELECT COUNT(*) FROM trackings WHERE DATE(created_at) = CURRENT_DATE")
                        today_result = cur.fetchone()
                        stats['today'] = today_result[0] if today_result else 0
                    else:
                        # Admin sees statistics for trackings they created OR trackings created for them
                        # Count by status
                        cur.execute(
                            "SELECT status, COUNT(*) FROM trackings WHERE created_by_admin_id = %s OR user_telegram_id = %s GROUP BY status",
                            (admin_id, admin_id)
                        )
                        status_counts = cur.fetchall()
                        stats['by_status'] = {status: count for status, count in status_counts}
                        
                        # Total trackings
                        cur.execute("SELECT COUNT(*) FROM trackings WHERE created_by_admin_id = %s OR user_telegram_id = %s", (admin_id, admin_id))
                        total_result = cur.fetchone()
                        stats['total'] = total_result[0] if total_result else 0
                        
                        # Today's trackings
                        cur.execute(
                            "SELECT COUNT(*) FROM trackings WHERE (created_by_admin_id = %s OR user_telegram_id = %s) AND DATE(created_at) = CURRENT_DATE",
                            (admin_id, admin_id)
                        )
                        today_result = cur.fetchone()
                        stats['today'] = today_result[0] if today_result else 0
                    
                    _stats_cache.set(cache_key, stats)
                    return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_user_statistics(self) -> List[dict]:
        """Get statistics grouped by user (owner only)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get statistics grouped by username with user info
                    cur.execute("""
                        SELECT 
                            COALESCE(username, 'Usuario Desconocido') as username,
                            user_telegram_id,
                            COUNT(*) as total_trackings,
                            COUNT(CASE WHEN status = 'RETENIDO' THEN 1 END) as retenidos,
                            COUNT(CASE WHEN status = 'CONFIRMAR_PAGO' THEN 1 END) as confirmar_pago,
                            COUNT(CASE WHEN status = 'EN_TRANSITO' THEN 1 END) as en_transito,
                            COUNT(CASE WHEN status = 'ENTREGADO' THEN 1 END) as entregados,
                            MAX(created_at) as last_tracking_date
                        FROM trackings
                        WHERE username IS NOT NULL OR user_telegram_id IS NOT NULL
                        GROUP BY username, user_telegram_id
                        ORDER BY total_trackings DESC, username
                    """)
                    rows = cur.fetchall()
                    
                    user_stats = []
                    for row in rows:
                        user_stats.append({
                            'username': row[0],
                            'user_telegram_id': row[1],
                            'total_trackings': row[2],
                            'retenidos': row[3],
                            'confirmar_pago': row[4],
                            'en_transito': row[5],
                            'entregados': row[6],
                            'last_tracking_date': row[7]
                        })
                    
                    return user_stats
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return []
    
    def get_trackings_by_user(self, user_id: int) -> List[Tracking]:
        """Get all trackings created by or for a specific user"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM trackings WHERE user_telegram_id = %s ORDER BY created_at DESC",
                        (user_id,)
                    )
                    rows = cur.fetchall()
                    return [Tracking(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting trackings for user {user_id}: {e}")
            return []
    
    def delete_tracking(self, tracking_id: str) -> bool:
        """Delete a tracking and its related records"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete status history first (foreign key constraint)
                    cur.execute("DELETE FROM status_history WHERE tracking_id = %s", (tracking_id,))
                    
                    # Delete the tracking
                    cur.execute("DELETE FROM trackings WHERE tracking_id = %s", (tracking_id,))
                    
                    if cur.rowcount == 0:
                        logger.warning(f"No tracking found with ID {tracking_id}")
                        return False
                    
                    conn.commit()
            logger.info(f"Tracking {tracking_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting tracking {tracking_id}: {e}")
            return False
    
    def get_all_trackings(self, admin_id: int, is_owner: bool = False) -> List[Tracking]:
        """Get all trackings, filtered by admin if not owner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if is_owner:
                        # Owner sees everything
                        cur.execute("SELECT * FROM trackings ORDER BY created_at DESC")
                    else:
                        # Admin sees trackings they created OR trackings created for them
                        cur.execute(
                            "SELECT * FROM trackings WHERE created_by_admin_id = %s OR user_telegram_id = %s ORDER BY created_at DESC",
                            (admin_id, admin_id)
                        )
                    rows = cur.fetchall()
                    return [Tracking(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all trackings: {e}")
            return []

    # ============================================================
    # FUNCIONES PARA POSTS (Red Social)
    # ============================================================
    
    def create_post(self, user_id: str, content_type: str, content_url: str = None, caption: str = None) -> Optional[int]:
        """Crear una nueva publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO posts (user_id, content_type, content_url, caption) 
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (user_id, content_type, content_url, caption)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    post_id = result[0] if result else None
                    logger.info(f"Post {post_id} created by user {user_id}")
                    return post_id
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None
    
    def get_post(self, post_id: int) -> Optional[dict]:
        """Obtener una publicación por ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.id = %s AND p.is_active = TRUE""",
                        (post_id,)
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    def get_posts_feed(self, user_id: str = None, limit: int = 20, offset: int = 0) -> List[dict]:
        """Obtener feed de publicaciones (propias y de seguidos)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if user_id:
                        cur.execute(
                            """SELECT p.*, u.username, u.first_name, u.avatar_url,
                                      EXISTS(SELECT 1 FROM post_likes pl WHERE pl.post_id = p.id AND pl.user_id = %s) as user_liked
                               FROM posts p
                               LEFT JOIN users u ON p.user_id = u.id
                               WHERE p.is_active = TRUE 
                               AND (p.user_id = %s OR p.user_id IN (SELECT following_id FROM follows WHERE follower_id = %s))
                               ORDER BY p.created_at DESC
                               LIMIT %s OFFSET %s""",
                            (user_id, user_id, user_id, limit, offset)
                        )
                    else:
                        cur.execute(
                            """SELECT p.*, u.username, u.first_name, u.avatar_url, FALSE as user_liked
                               FROM posts p
                               LEFT JOIN users u ON p.user_id = u.id
                               WHERE p.is_active = TRUE
                               ORDER BY p.created_at DESC
                               LIMIT %s OFFSET %s""",
                            (limit, offset)
                        )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting posts feed: {e}")
            return []
    
    def get_user_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        """Obtener publicaciones de un usuario específico con media"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT json_agg(json_build_object(
                            'id', pm.id, 'media_type', pm.media_type,
                            'media_url', pm.media_url, 'encrypted_url', pm.encrypted_url, 
                            'thumbnail_url', pm.thumbnail_url, 'media_order', pm.media_order))
                            FROM post_media pm WHERE pm.post_id = p.id) as media
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.user_id = %s AND p.is_active = TRUE
                           ORDER BY p.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, limit, offset)
                    )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user posts for {user_id}: {e}")
            return []
    
    def delete_post(self, post_id: int, user_id: str) -> bool:
        """Eliminar una publicación (solo el autor puede eliminar)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE posts SET is_active = FALSE WHERE id = %s AND user_id = %s",
                        (post_id, user_id)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"Post {post_id} deleted by user {user_id}")
                    return success
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            return False
    
    def like_post(self, post_id: int, user_id: str) -> dict:
        """Dar like a una publicación. Returns dict with success status and message."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, user_id FROM posts WHERE id = %s AND is_active = TRUE", (post_id,))
                    post = cur.fetchone()
                    if not post:
                        return {'success': False, 'error': 'post_not_found'}
                    
                    post_owner_id = post[1]
                    
                    cur.execute(
                        """INSERT INTO post_likes (post_id, user_id) 
                           VALUES (%s, %s) ON CONFLICT (user_id, post_id) DO NOTHING""",
                        (post_id, user_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE posts SET likes_count = likes_count + 1 WHERE id = %s",
                            (post_id,)
                        )
                        
                        if post_owner_id and str(post_owner_id) != str(user_id):
                            cur.execute(
                                """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                                   VALUES (%s, 'like', %s, 'post', %s, 'le gustó tu publicación')
                                   ON CONFLICT DO NOTHING""",
                                (post_owner_id, user_id, post_id)
                            )
                        
                        conn.commit()
                        logger.info(f"User {user_id} liked post {post_id}")
                        return {'success': True, 'message': 'liked'}
                    else:
                        conn.commit()
                        return {'success': True, 'message': 'already_liked'}
        except Exception as e:
            logger.error(f"Error liking post {post_id}: {e}")
            return {'success': False, 'error': 'database_error'}
    
    def unlike_post(self, post_id: int, user_id: str) -> dict:
        """Quitar like de una publicación. Returns dict with success status and message."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM posts WHERE id = %s AND is_active = TRUE", (post_id,))
                    if not cur.fetchone():
                        return {'success': False, 'error': 'post_not_found'}
                    
                    cur.execute(
                        "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                        (post_id, user_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE posts SET likes_count = GREATEST(0, likes_count - 1) WHERE id = %s",
                            (post_id,)
                        )
                        conn.commit()
                        logger.info(f"User {user_id} unliked post {post_id}")
                        return {'success': True, 'message': 'unliked'}
                    else:
                        conn.commit()
                        return {'success': True, 'message': 'not_liked'}
        except Exception as e:
            logger.error(f"Error unliking post {post_id}: {e}")
            return {'success': False, 'error': 'database_error'}
    
    # ============================================================
    # FUNCIONES PARA SEGUIDORES (Red Social)
    # ============================================================
    
    def follow_user(self, follower_id: str, following_id: str) -> bool:
        """Seguir a un usuario"""
        if follower_id == following_id:
            logger.warning(f"User {follower_id} tried to follow themselves")
            return False
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO follows (follower_id, following_id) 
                           VALUES (%s, %s) ON CONFLICT (follower_id, following_id) DO NOTHING""",
                        (follower_id, following_id)
                    )
                    success = cur.rowcount > 0
                    
                    if success:
                        cur.execute(
                            """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                               VALUES (%s, 'follow', %s, 'user', %s, 'empezó a seguirte')""",
                            (following_id, follower_id, follower_id)
                        )
                    
                    conn.commit()
                    if success:
                        logger.info(f"User {follower_id} now follows {following_id}")
                    return success
        except Exception as e:
            logger.error(f"Error following user: {e}")
            return False
    
    def unfollow_user(self, follower_id: str, following_id: str) -> bool:
        """Dejar de seguir a un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM follows WHERE follower_id = %s AND following_id = %s",
                        (follower_id, following_id)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"User {follower_id} unfollowed {following_id}")
                    return success
        except Exception as e:
            logger.error(f"Error unfollowing user: {e}")
            return False
    
    def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """Obtener lista de seguidores de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT u.id, u.username, u.first_name, u.last_name, u.avatar_url, u.bio, u.is_verified,
                                  f.created_at as followed_at
                           FROM follows f
                           JOIN users u ON f.follower_id = u.id
                           WHERE f.following_id = %s
                           ORDER BY f.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, limit, offset)
                    )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting followers for {user_id}: {e}")
            return []
    
    def get_following(self, user_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """Obtener lista de usuarios que sigue"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT u.id, u.username, u.first_name, u.last_name, u.avatar_url, u.bio, u.is_verified,
                                  f.created_at as followed_at
                           FROM follows f
                           JOIN users u ON f.following_id = u.id
                           WHERE f.follower_id = %s
                           ORDER BY f.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, limit, offset)
                    )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting following for {user_id}: {e}")
            return []
    
    def get_follow_counts(self, user_id: str) -> dict:
        """Obtener conteo de seguidores y seguidos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
                    followers_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
                    following_count = cur.fetchone()[0]
                    
                    return {
                        'followers': followers_count,
                        'following': following_count
                    }
        except Exception as e:
            logger.error(f"Error getting follow counts for {user_id}: {e}")
            return {'followers': 0, 'following': 0}
    
    def is_following(self, follower_id: str, following_id: str) -> bool:
        """Verificar si un usuario sigue a otro"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM follows WHERE follower_id = %s AND following_id = %s",
                        (follower_id, following_id)
                    )
                    return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking follow status: {e}")
            return False
    
    def count_user_publications(self, user_id: str) -> int:
        """Contar publicaciones de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM posts WHERE user_id = %s AND is_active = TRUE",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting publications for {user_id}: {e}")
            return 0
    
    # ============================================================
    # FUNCIONES PARA USUARIOS (Red Social)
    # ============================================================
    
    def get_or_create_user(self, user_id: str, username: str = None, first_name: str = None, 
                           last_name: str = None, telegram_id: int = None) -> Optional[dict]:
        """Obtener o crear un usuario"""
        import hashlib
        default_password = hashlib.sha256(f"telegram_{user_id}_{telegram_id}".encode()).hexdigest()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user = cur.fetchone()
                    
                    if user:
                        if username or first_name:
                            cur.execute(
                                """UPDATE users SET username = COALESCE(%s, username), 
                                   first_name = COALESCE(%s, first_name),
                                   last_name = COALESCE(%s, last_name),
                                   telegram_id = COALESCE(%s, telegram_id),
                                   last_seen = CURRENT_TIMESTAMP,
                                   updated_at = CURRENT_TIMESTAMP
                                   WHERE id = %s""",
                                (username, first_name, last_name, telegram_id, user_id)
                            )
                            conn.commit()
                        return dict(user)
                    else:
                        cur.execute(
                            """INSERT INTO users (id, username, password, first_name, last_name, telegram_id) 
                               VALUES (%s, %s, %s, %s, %s, %s)
                               ON CONFLICT (id) DO UPDATE SET 
                                   username = COALESCE(EXCLUDED.username, users.username),
                                   last_seen = CURRENT_TIMESTAMP
                               RETURNING *""",
                            (user_id, username, default_password, first_name, last_name, telegram_id)
                        )
                        new_user = cur.fetchone()
                        conn.commit()
                        logger.info(f"Created new user {user_id}")
                        return dict(new_user) if new_user else None
        except Exception as e:
            logger.error(f"Error getting/creating user {user_id}: {e}")
            return None
    
    def get_user_profile(self, user_id: str, viewer_id: str = None) -> Optional[dict]:
        """Obtener perfil completo de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT id, username, first_name, last_name, avatar_url, bio, 
                                  level, credits, is_verified, created_at
                           FROM users WHERE id = %s""",
                        (user_id,)
                    )
                    user = cur.fetchone()
                    
                    if not user:
                        return None
                    
                    profile = dict(user)
                    
                    follow_counts = self.get_follow_counts(user_id)
                    profile['followers_count'] = follow_counts['followers']
                    profile['following_count'] = follow_counts['following']
                    
                    cur.execute("SELECT COUNT(*) FROM posts WHERE user_id = %s AND is_active = TRUE", (user_id,))
                    profile['posts_count'] = cur.fetchone()[0]
                    
                    if viewer_id and viewer_id != user_id:
                        profile['is_following'] = self.is_following(viewer_id, user_id)
                    else:
                        profile['is_following'] = False
                    
                    return profile
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            return None
    
    def update_user_profile(self, user_id: str, bio: str = None, avatar_url: str = None) -> bool:
        """Actualizar perfil de usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    updates = []
                    values = []
                    
                    if bio is not None:
                        updates.append("bio = %s")
                        values.append(bio)
                    if avatar_url is not None:
                        updates.append("avatar_url = %s")
                        values.append(avatar_url)
                    
                    if not updates:
                        return True
                    
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(user_id)
                    
                    cur.execute(
                        f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
                        values
                    )
                    conn.commit()
                    logger.info(f"Updated profile for user {user_id}")
                    return True
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return False

    def set_user_verified(self, user_id: str, is_verified: bool) -> bool:
        """Establecer el estado de verificación de un usuario (solo admin)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users SET is_verified = %s, updated_at = CURRENT_TIMESTAMP 
                           WHERE id = %s""",
                        (is_verified, user_id)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"User {user_id} verification status set to {is_verified}")
                    return success
        except Exception as e:
            logger.error(f"Error setting verification status for user {user_id}: {e}")
            return False

    def get_all_users_for_admin(self, limit: int = 100, offset: int = 0, search: str = None) -> List[dict]:
        """Obtener lista de usuarios para panel de admin"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if search:
                        cur.execute(
                            """SELECT id, username, first_name, last_name, avatar_url, bio,
                                      is_verified, credits, created_at, last_seen
                               FROM users 
                               WHERE username ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s
                               ORDER BY created_at DESC
                               LIMIT %s OFFSET %s""",
                            (f'%{search}%', f'%{search}%', f'%{search}%', limit, offset)
                        )
                    else:
                        cur.execute(
                            """SELECT id, username, first_name, last_name, avatar_url, bio,
                                      is_verified, credits, created_at, last_seen
                               FROM users 
                               ORDER BY created_at DESC
                               LIMIT %s OFFSET %s""",
                            (limit, offset)
                        )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting users for admin: {e}")
            return []

    def update_user_avatar_data(self, user_id: str, avatar_data: str) -> bool:
        """Guardar imagen de avatar como base64 en la base de datos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users SET avatar_data = %s, updated_at = CURRENT_TIMESTAMP 
                           WHERE id = %s""",
                        (avatar_data, user_id)
                    )
                    conn.commit()
                    logger.info(f"Updated avatar data for user {user_id}")
                    return True
        except Exception as e:
            logger.error(f"Error updating avatar data for user {user_id}: {e}")
            return False
    
    def get_user_avatar_data(self, user_id: str) -> Optional[str]:
        """Obtener imagen de avatar base64 de la base de datos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT avatar_data FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    if result and result[0]:
                        return result[0]
                    return None
        except Exception as e:
            logger.error(f"Error getting avatar data for user {user_id}: {e}")
            return None

    # ============================================================
    # FUNCIONES PARA BOTS DE USUARIO
    # ============================================================
    
    def get_user_bots(self, user_id: str, is_owner: bool = False) -> List[dict]:
        """Obtener todos los bots activos de un usuario.
        Si no es owner, filtra automaticamente los bots owner_only para prevenir acceso no autorizado."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if is_owner:
                        cur.execute(
                            """SELECT ub.id, ub.bot_name, ub.bot_type, ub.is_active, ub.config, ub.created_at,
                                      bt.icon, bt.description, bt.price
                               FROM user_bots ub
                               LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                               WHERE ub.user_id = %s AND ub.is_active = TRUE
                               ORDER BY ub.created_at DESC""",
                            (user_id,)
                        )
                    else:
                        cur.execute(
                            """SELECT ub.id, ub.bot_name, ub.bot_type, ub.is_active, ub.config, ub.created_at,
                                      bt.icon, bt.description, bt.price
                               FROM user_bots ub
                               LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                               WHERE ub.user_id = %s AND ub.is_active = TRUE
                               AND (bt.owner_only = FALSE OR bt.owner_only IS NULL)
                               ORDER BY ub.created_at DESC""",
                            (user_id,)
                        )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user bots for {user_id}: {e}")
            return []
    
    def get_available_bots(self, user_id: str, is_owner: bool = False) -> List[dict]:
        """Obtener bots disponibles para comprar (que el usuario aún no tiene)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if is_owner:
                        cur.execute(
                            """SELECT bt.id, bt.bot_type, bt.bot_name, bt.description, bt.icon, bt.price, bt.is_available
                               FROM bot_types bt
                               WHERE bt.is_available = TRUE 
                               AND bt.bot_type NOT IN (
                                   SELECT ub.bot_type FROM user_bots ub 
                                   WHERE ub.user_id = %s AND ub.is_active = TRUE
                               )
                               ORDER BY bt.price ASC""",
                            (user_id,)
                        )
                    else:
                        cur.execute(
                            """SELECT bt.id, bt.bot_type, bt.bot_name, bt.description, bt.icon, bt.price, bt.is_available
                               FROM bot_types bt
                               WHERE bt.is_available = TRUE 
                               AND (bt.owner_only = FALSE OR bt.owner_only IS NULL)
                               AND bt.bot_type NOT IN (
                                   SELECT ub.bot_type FROM user_bots ub 
                                   WHERE ub.user_id = %s AND ub.is_active = TRUE
                               )
                               ORDER BY bt.price ASC""",
                            (user_id,)
                        )
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting available bots for {user_id}: {e}")
            return []
    
    def add_user_bot(self, user_id: str, bot_type: str, bot_name: str, config: str = None) -> bool:
        """Agregar un bot al usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO user_bots (user_id, bot_name, bot_type, is_active, config)
                           VALUES (%s, %s, %s, TRUE, %s)
                           ON CONFLICT DO NOTHING""",
                        (user_id, bot_name, bot_type, config)
                    )
                    conn.commit()
                    logger.info(f"Added bot {bot_type} to user {user_id}")
                    return True
        except Exception as e:
            logger.error(f"Error adding bot {bot_type} to user {user_id}: {e}")
            return False
    
    def toggle_bot_activation(self, user_id: str, bot_id: int) -> dict:
        """Toggle bot activation status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT is_active FROM user_bots WHERE id = %s AND user_id = %s",
                        (bot_id, user_id)
                    )
                    bot = cur.fetchone()
                    if not bot:
                        return {'success': False, 'error': 'Bot no encontrado'}
                    
                    new_status = not bot['is_active']
                    cur.execute(
                        "UPDATE user_bots SET is_active = %s WHERE id = %s AND user_id = %s",
                        (new_status, bot_id, user_id)
                    )
                    conn.commit()
                    return {'success': True, 'is_active': new_status}
        except Exception as e:
            logger.error(f"Error toggling bot {bot_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_bot_config(self, user_id: str, bot_id: int, config: dict) -> dict:
        """Update bot configuration"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    import json
                    cur.execute(
                        "UPDATE user_bots SET config = %s WHERE id = %s AND user_id = %s",
                        (json.dumps(config), bot_id, user_id)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    return {'success': success}
        except Exception as e:
            logger.error(f"Error updating bot config {bot_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_bot_config(self, user_id: str, bot_id: int) -> dict:
        """Get bot configuration"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT config, bot_type, bot_name FROM user_bots WHERE id = %s AND user_id = %s",
                        (bot_id, user_id)
                    )
                    bot = cur.fetchone()
                    if bot:
                        import json
                        config = bot['config']
                        if isinstance(config, str):
                            config = json.loads(config) if config else {}
                        return {
                            'success': True,
                            'config': config or {},
                            'bot_type': bot['bot_type'],
                            'bot_name': bot['bot_name']
                        }
                    return {'success': False, 'error': 'Bot no encontrado'}
        except Exception as e:
            logger.error(f"Error getting bot config {bot_id}: {e}")
            return {'success': False, 'error': str(e)}

    def remove_user_bot(self, user_id: str, bot_id: int) -> bool:
        """Desactivar un bot del usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE user_bots SET is_active = FALSE 
                           WHERE id = %s AND user_id = %s""",
                        (bot_id, user_id)
                    )
                    conn.commit()
                    logger.info(f"Removed bot {bot_id} from user {user_id}")
                    return True
        except Exception as e:
            logger.error(f"Error removing bot {bot_id} from user {user_id}: {e}")
            return False
    
    def purchase_bot(self, user_id: str, bot_type: str) -> dict:
        """Comprar un bot - verifica créditos, descuenta y activa el bot.
        Usa FOR UPDATE lock para evitar race conditions con retry."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    try:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            cur.execute(
                                "SELECT credits FROM users WHERE id = %s FOR UPDATE",
                                (user_id,)
                            )
                            user = cur.fetchone()
                            if not user:
                                return {'success': False, 'error': 'Usuario no encontrado'}
                            
                            user_credits = user['credits'] or 0
                            
                            cur.execute(
                                "SELECT bot_name, price, icon FROM bot_types WHERE bot_type = %s AND is_available = TRUE",
                                (bot_type,)
                            )
                            bot = cur.fetchone()
                            if not bot:
                                return {'success': False, 'error': 'Bot no disponible'}
                            
                            bot_price = bot['price'] or 0
                            
                            if user_credits < bot_price:
                                return {'success': False, 'error': 'Créditos insuficientes', 'required': bot_price, 'current': user_credits}
                            
                            cur.execute(
                                "SELECT id FROM user_bots WHERE user_id = %s AND bot_type = %s AND is_active = TRUE",
                                (user_id, bot_type)
                            )
                            if cur.fetchone():
                                return {'success': False, 'error': 'Ya tienes este bot activo'}
                            
                            cur.execute(
                                "UPDATE users SET credits = credits - %s WHERE id = %s",
                                (bot_price, user_id)
                            )
                            
                            cur.execute(
                                """INSERT INTO user_bots (user_id, bot_name, bot_type, is_active)
                                   VALUES (%s, %s, %s, TRUE)""",
                                (user_id, bot['bot_name'], bot_type)
                            )
                            
                            cur.execute(
                                """INSERT INTO wallet_transactions (user_id, transaction_type, amount, description, reference_id)
                                   VALUES (%s, 'purchase', %s, %s, %s)""",
                                (user_id, -bot_price, f"Compra de bot: {bot['bot_name']}", bot_type)
                            )
                            
                            conn.commit()
                            
                            new_balance = user_credits - bot_price
                            self.create_transaction_notification(
                                user_id=user_id,
                                amount=bot_price,
                                transaction_type='bot_purchase',
                                new_balance=new_balance
                            )
                            
                            logger.info(f"User {user_id} purchased bot {bot_type} for {bot_price} credits")
                            return {
                                'success': True, 
                                'message': f'Bot {bot["bot_name"]} activado correctamente',
                                'bot_name': bot['bot_name'],
                                'credits_remaining': new_balance
                            }
                    except psycopg2.errors.SerializationFailure:
                        conn.rollback()
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        raise
                    except psycopg2.errors.DeadlockDetected:
                        conn.rollback()
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        raise
            except (psycopg2.errors.SerializationFailure, psycopg2.errors.DeadlockDetected):
                if attempt == max_retries - 1:
                    logger.warning(f"Purchase bot failed after {max_retries} retries for user {user_id}")
                    return {'success': False, 'error': 'Operación ocupada, intenta de nuevo'}
            except Exception as e:
                logger.error(f"Error purchasing bot {bot_type} for user {user_id}: {e}")
                return {'success': False, 'error': 'Error al procesar compra'}
        
        return {'success': False, 'error': 'Operación ocupada, intenta de nuevo'}
    
    def initialize_bot_types(self) -> bool:
        """Inicializar tabla de tipos de bots disponibles"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS bot_types (
                            id SERIAL PRIMARY KEY,
                            bot_type VARCHAR(100) UNIQUE NOT NULL,
                            bot_name VARCHAR(255) NOT NULL,
                            description TEXT,
                            icon VARCHAR(50),
                            price INTEGER DEFAULT 0,
                            is_available BOOLEAN DEFAULT TRUE,
                            owner_only BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute("""
                        ALTER TABLE bot_types ADD COLUMN IF NOT EXISTS owner_only BOOLEAN DEFAULT FALSE
                    """)
                    
                    cur.execute("""
                        ALTER TABLE bot_types ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'general'
                    """)
                    
                    cur.execute("""
                        INSERT INTO bot_types (bot_type, bot_name, description, icon, price, is_available, owner_only) VALUES
                        ('tracking_manager', 'Trackings Correos', 'Gestiona tus envios y paquetes', '📦', 0, TRUE, TRUE)
                        ON CONFLICT (bot_type) DO UPDATE SET
                            bot_name = EXCLUDED.bot_name,
                            description = EXCLUDED.description,
                            icon = EXCLUDED.icon,
                            owner_only = EXCLUDED.owner_only
                    """)
                    
                    conn.commit()
                    logger.info("Bot types initialized successfully")
                    return True
        except Exception as e:
            logger.error(f"Error initializing bot types: {e}")
            return False
    
    def assign_owner_bots(self, owner_telegram_id: int) -> bool:
        """Asignar bots exclusivos del owner automáticamente"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM users WHERE telegram_id = %s",
                        (owner_telegram_id,)
                    )
                    user_row = cur.fetchone()
                    if not user_row:
                        logger.warning(f"Owner user not found with telegram_id {owner_telegram_id}")
                        return False
                    
                    user_id = user_row[0]
                    
                    cur.execute("""
                        SELECT bot_type, bot_name FROM bot_types WHERE owner_only = TRUE
                    """)
                    owner_bots = cur.fetchall()
                    
                    for bot_type, bot_name in owner_bots:
                        cur.execute(
                            """SELECT id FROM user_bots 
                               WHERE user_id = %s AND bot_type = %s""",
                            (user_id, bot_type)
                        )
                        if not cur.fetchone():
                            cur.execute(
                                """INSERT INTO user_bots (user_id, bot_name, bot_type, is_active)
                                   VALUES (%s, %s, %s, TRUE)""",
                                (user_id, bot_name, bot_type)
                            )
                            logger.info(f"Assigned owner bot {bot_type} to user {user_id}")
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error assigning owner bots: {e}")
            return False

    # ============================================================
    # FUNCIONES PARA 2FA (Two-Factor Authentication)
    # ============================================================
    
    def get_user_2fa_status(self, user_id: str) -> dict:
        """Obtener estado de 2FA de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT totp_secret, two_factor_enabled, last_2fa_verified_at
                           FROM users WHERE telegram_id = %s""",
                        (user_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            'has_secret': row['totp_secret'] is not None,
                            'enabled': row['two_factor_enabled'] or False,
                            'last_verified': row['last_2fa_verified_at']
                        }
                    return {'has_secret': False, 'enabled': False, 'last_verified': None}
        except Exception as e:
            logger.error(f"Error getting 2FA status for user {user_id}: {e}")
            return {'has_secret': False, 'enabled': False, 'last_verified': None}
    
    def setup_2fa(self, user_id: str, totp_secret: str) -> bool:
        """Configurar secreto TOTP para un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users SET totp_secret = %s WHERE telegram_id = %s""",
                        (totp_secret, user_id)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"2FA secret configured for user {user_id}")
                    return success
        except Exception as e:
            logger.error(f"Error setting up 2FA for user {user_id}: {e}")
            return False
    
    def enable_2fa(self, user_id: str) -> bool:
        """Activar 2FA para un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users SET two_factor_enabled = TRUE, 
                           last_2fa_verified_at = NOW()
                           WHERE telegram_id = %s AND totp_secret IS NOT NULL""",
                        (user_id,)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"2FA enabled for user {user_id}")
                    return success
        except Exception as e:
            logger.error(f"Error enabling 2FA for user {user_id}: {e}")
            return False
    
    def get_user_totp_secret(self, user_id: str) -> str:
        """Obtener secreto TOTP de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT totp_secret FROM users WHERE telegram_id = %s",
                        (user_id,)
                    )
                    row = cur.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting TOTP secret for user {user_id}: {e}")
            return None
    
    def update_2fa_verified_time(self, user_id: str) -> bool:
        """Actualizar timestamp de última verificación 2FA"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET last_2fa_verified_at = NOW() WHERE telegram_id = %s",
                        (user_id,)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    return success
        except Exception as e:
            logger.error(f"Error updating 2FA verified time for user {user_id}: {e}")
            return False
    
    def check_2fa_session_valid(self, user_id: str, timeout_minutes: int = 10) -> bool:
        """Verificar si la sesión 2FA sigue siendo válida (no ha expirado)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT last_2fa_verified_at FROM users 
                           WHERE telegram_id = %s AND two_factor_enabled = TRUE""",
                        (user_id,)
                    )
                    row = cur.fetchone()
                    if not row or not row[0]:
                        return False
                    
                    last_verified = row[0]
                    now = datetime.now()
                    
                    if last_verified.tzinfo:
                        from datetime import timezone
                        now = datetime.now(timezone.utc)
                    
                    diff = now - last_verified
                    return diff.total_seconds() < (timeout_minutes * 60)
        except Exception as e:
            logger.error(f"Error checking 2FA session for user {user_id}: {e}")
            return False
    
    def disable_2fa(self, user_id: str) -> bool:
        """Desactivar 2FA para un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users SET two_factor_enabled = FALSE, 
                           totp_secret = NULL, last_2fa_verified_at = NULL
                           WHERE telegram_id = %s""",
                        (user_id,)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    if success:
                        logger.info(f"2FA disabled for user {user_id}")
                    return success
        except Exception as e:
            logger.error(f"Error disabling 2FA for user {user_id}: {e}")
            return False

    # ============================================================
    # FUNCIONES PARA PUBLICACIONES ENCRIPTADAS
    # ============================================================
    
    def initialize_encrypted_posts_tables(self):
        """Inicializar tablas para publicaciones encriptadas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(CREATE_ENCRYPTED_POSTS_SQL)
                    conn.commit()
            logger.info("Encrypted posts tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing encrypted posts tables: {e}")
            return False
    
    def initialize_virtual_numbers_tables(self):
        """Inicializar tablas para sistema de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(CREATE_VIRTUAL_NUMBERS_SQL)
                    conn.commit()
            logger.info("Virtual numbers tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing virtual numbers tables: {e}")
            return False
    
    def initialize_payments_tables(self):
        """Inicializar tablas para sistema de pagos TON"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS pending_payments (
                            id SERIAL PRIMARY KEY,
                            payment_id VARCHAR(20) UNIQUE NOT NULL,
                            user_id VARCHAR(50) NOT NULL,
                            credits INTEGER NOT NULL,
                            ton_amount DECIMAL(20, 9) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            tx_hash VARCHAR(100),
                            created_at TIMESTAMP DEFAULT NOW(),
                            confirmed_at TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_pending_payments_user 
                            ON pending_payments(user_id);
                        CREATE INDEX IF NOT EXISTS idx_pending_payments_status 
                            ON pending_payments(status);
                    """)
                    conn.commit()
            logger.info("Payments tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing payments tables: {e}")
            return False
    
    def initialize_b3c_tables(self):
        """Inicializar tablas para sistema de token B3C"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS b3c_purchases (
                            id SERIAL PRIMARY KEY,
                            purchase_id VARCHAR(20) UNIQUE NOT NULL,
                            user_id VARCHAR(50) NOT NULL,
                            ton_amount DECIMAL(20, 9) NOT NULL,
                            b3c_amount DECIMAL(20, 9) NOT NULL,
                            commission_ton DECIMAL(20, 9) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            tx_hash VARCHAR(100),
                            created_at TIMESTAMP DEFAULT NOW(),
                            confirmed_at TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_b3c_purchases_user 
                            ON b3c_purchases(user_id);
                        CREATE INDEX IF NOT EXISTS idx_b3c_purchases_status 
                            ON b3c_purchases(status);
                        
                        CREATE TABLE IF NOT EXISTS b3c_withdrawals (
                            id SERIAL PRIMARY KEY,
                            withdrawal_id VARCHAR(20) UNIQUE NOT NULL,
                            user_id VARCHAR(50) NOT NULL,
                            b3c_amount DECIMAL(20, 9) NOT NULL,
                            destination_wallet VARCHAR(100) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            tx_hash VARCHAR(100),
                            created_at TIMESTAMP DEFAULT NOW(),
                            processed_at TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_b3c_withdrawals_user 
                            ON b3c_withdrawals(user_id);
                        
                        CREATE TABLE IF NOT EXISTS b3c_deposits (
                            id SERIAL PRIMARY KEY,
                            deposit_id VARCHAR(20) UNIQUE NOT NULL,
                            user_id VARCHAR(50) NOT NULL,
                            b3c_amount DECIMAL(20, 9) NOT NULL,
                            source_wallet VARCHAR(100),
                            tx_hash VARCHAR(100),
                            status VARCHAR(20) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT NOW(),
                            confirmed_at TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_b3c_deposits_user 
                            ON b3c_deposits(user_id);
                        
                        CREATE TABLE IF NOT EXISTS b3c_commissions (
                            id SERIAL PRIMARY KEY,
                            transaction_type VARCHAR(20) NOT NULL,
                            reference_id VARCHAR(20) NOT NULL,
                            commission_ton DECIMAL(20, 9) NOT NULL,
                            commission_usd DECIMAL(20, 9),
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                        CREATE INDEX IF NOT EXISTS idx_b3c_commissions_type 
                            ON b3c_commissions(transaction_type);
                        
                        CREATE TABLE IF NOT EXISTS b3c_transfers (
                            id SERIAL PRIMARY KEY,
                            transfer_id VARCHAR(20) UNIQUE NOT NULL,
                            from_user_id VARCHAR(50) NOT NULL,
                            to_user_id VARCHAR(50) NOT NULL,
                            b3c_amount DECIMAL(20, 9) NOT NULL,
                            note VARCHAR(255),
                            status VARCHAR(20) DEFAULT 'completed',
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                        CREATE INDEX IF NOT EXISTS idx_b3c_transfers_from 
                            ON b3c_transfers(from_user_id);
                        CREATE INDEX IF NOT EXISTS idx_b3c_transfers_to 
                            ON b3c_transfers(to_user_id);
                        
                        -- Deposit Wallets Pool (Sección 24)
                        CREATE TABLE IF NOT EXISTS deposit_wallets (
                            id SERIAL PRIMARY KEY,
                            wallet_address VARCHAR(100) UNIQUE NOT NULL,
                            private_key_encrypted TEXT NOT NULL,
                            public_key VARCHAR(100),
                            status VARCHAR(20) DEFAULT 'available',
                            assigned_to_user_id VARCHAR(50),
                            assigned_to_purchase_id VARCHAR(50),
                            expected_amount DECIMAL(20, 9),
                            assigned_at TIMESTAMP,
                            expires_at TIMESTAMP,
                            deposit_detected_at TIMESTAMP,
                            deposit_tx_hash VARCHAR(100),
                            deposit_amount DECIMAL(20, 9),
                            consolidation_tx_hash VARCHAR(100),
                            consolidated_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                        CREATE INDEX IF NOT EXISTS idx_deposit_wallets_status 
                            ON deposit_wallets(status);
                        CREATE INDEX IF NOT EXISTS idx_deposit_wallets_user 
                            ON deposit_wallets(assigned_to_user_id);
                        CREATE INDEX IF NOT EXISTS idx_deposit_wallets_expires 
                            ON deposit_wallets(expires_at);
                        CREATE INDEX IF NOT EXISTS idx_deposit_wallets_purchase 
                            ON deposit_wallets(assigned_to_purchase_id);
                        
                        -- Wallet Pool Config
                        CREATE TABLE IF NOT EXISTS wallet_pool_config (
                            id SERIAL PRIMARY KEY,
                            config_key VARCHAR(50) UNIQUE NOT NULL,
                            config_value VARCHAR(255) NOT NULL,
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                        
                        -- Insert default config if not exists
                        INSERT INTO wallet_pool_config (config_key, config_value)
                        VALUES 
                            ('min_pool_size', '10'),
                            ('max_assignment_minutes', '30'),
                            ('consolidation_fee', '0.01')
                        ON CONFLICT (config_key) DO NOTHING;
                        
                        -- Blockchain Audit Log for transaction tracking
                        CREATE TABLE IF NOT EXISTS blockchain_audit_log (
                            id SERIAL PRIMARY KEY,
                            transaction_type VARCHAR(50) NOT NULL,
                            user_id VARCHAR(50) NOT NULL,
                            amount DECIMAL(20, 9),
                            details JSONB,
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                        CREATE INDEX IF NOT EXISTS idx_blockchain_audit_user 
                            ON blockchain_audit_log(user_id);
                        CREATE INDEX IF NOT EXISTS idx_blockchain_audit_type 
                            ON blockchain_audit_log(transaction_type);
                        CREATE INDEX IF NOT EXISTS idx_blockchain_audit_time 
                            ON blockchain_audit_log(created_at DESC);
                    """)
                    conn.commit()
            logger.info("B3C tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing B3C tables: {e}")
            return False
    
    
    def get_virtual_number_setting(self, key: str, default: str = None) -> str:
        """Obtener configuracion de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT setting_value FROM virtual_number_settings WHERE setting_key = %s",
                        (key,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else default
        except Exception as e:
            logger.error(f"Error getting virtual number setting {key}: {e}")
            return default
    
    def set_virtual_number_setting(self, key: str, value: str) -> bool:
        """Establecer configuracion de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO virtual_number_settings (setting_key, setting_value, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (setting_key) DO UPDATE 
                        SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
                    """, (key, value))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error setting virtual number setting {key}: {e}")
            return False
    
    def get_all_virtual_number_settings(self) -> dict:
        """Obtener todas las configuraciones de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT setting_key, setting_value FROM virtual_number_settings")
                    settings = {}
                    for row in cur.fetchall():
                        settings[row['setting_key']] = row['setting_value']
                    return settings
        except Exception as e:
            logger.error(f"Error getting all virtual number settings: {e}")
            return {}
    
    def get_virtual_number_stats(self, days: int = 30) -> dict:
        """Obtener estadisticas de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_orders,
                            COUNT(CASE WHEN status = 'received' THEN 1 END) as successful,
                            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
                            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                            COALESCE(SUM(bunkercoin_charged), 0) as total_revenue,
                            COALESCE(SUM(cost_usd), 0) as total_cost,
                            COALESCE(SUM(cost_with_commission - cost_usd), 0) as total_profit_usd
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                    """, (days,))
                    result = cur.fetchone()
                    
                    cur.execute("""
                        SELECT 
                            DATE(created_at) as date,
                            COUNT(*) as orders,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY DATE(created_at)
                        ORDER BY date DESC
                    """)
                    daily_stats = [dict(row) for row in cur.fetchall()]
                    
                    cur.execute("""
                        SELECT 
                            COALESCE(service_name, service_code) as service,
                            COUNT(*) as count,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY COALESCE(service_name, service_code)
                        ORDER BY count DESC
                        LIMIT 10
                    """, (days,))
                    top_services = [dict(row) for row in cur.fetchall()]
                    
                    cur.execute("""
                        SELECT 
                            COALESCE(country_name, country_code) as country,
                            COUNT(*) as count,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY COALESCE(country_name, country_code)
                        ORDER BY count DESC
                        LIMIT 10
                    """, (days,))
                    top_countries = [dict(row) for row in cur.fetchall()]
                    
                    return {
                        'summary': dict(result) if result else {},
                        'daily': daily_stats,
                        'top_services': top_services,
                        'top_countries': top_countries
                    }
        except Exception as e:
            logger.error(f"Error getting virtual number stats: {e}")
            return {'summary': {}, 'daily': [], 'top_services': [], 'top_countries': []}
    
    def get_legitsms_inventory(self, available_only: bool = True) -> list:
        """Obtener inventario de numeros Legit SMS"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    query = """
                        SELECT * FROM virtual_number_inventory
                        WHERE provider = 'legitsms'
                    """
                    if available_only:
                        query += " AND is_available = TRUE"
                    query += " ORDER BY created_at DESC"
                    
                    cur.execute(query)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting legitsms inventory: {e}")
            return []
    
    def add_to_legitsms_inventory(self, country_code: str, country_name: str,
                                   service_code: str, service_name: str,
                                   phone_number: str, cost_usd: float) -> bool:
        """Agregar numero al inventario de Legit SMS"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO virtual_number_inventory 
                        (provider, country_code, country_name, service_code, service_name, phone_number, cost_usd)
                        VALUES ('legitsms', %s, %s, %s, %s, %s, %s)
                    """, (country_code, country_name, service_code, service_name, phone_number, cost_usd))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding to legitsms inventory: {e}")
            return False
    
    def remove_from_legitsms_inventory(self, inventory_id: str) -> bool:
        """Eliminar numero del inventario de Legit SMS"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM virtual_number_inventory WHERE id = %s AND is_available = TRUE",
                        (inventory_id,)
                    )
                    success = cur.rowcount > 0
                    conn.commit()
                    return success
        except Exception as e:
            logger.error(f"Error removing from legitsms inventory: {e}")
            return False
    
    def create_encrypted_post(self, user_id: str, content_type: str, caption: str = None,
                             encryption_key: str = None, encryption_iv: str = None,
                             is_encrypted: bool = True) -> Optional[int]:
        """Crear una publicación encriptada"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO posts (user_id, content_type, caption, encryption_key, 
                           encryption_iv, is_encrypted, views_count) 
                           VALUES (%s, %s, %s, %s, %s, %s, 0) RETURNING id""",
                        (user_id, content_type, caption, encryption_key, encryption_iv, is_encrypted)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    post_id = result[0] if result else None
                    logger.info(f"Encrypted post {post_id} created by user {user_id}")
                    return post_id
        except Exception as e:
            logger.error(f"Error creating encrypted post: {e}")
            return None
    
    def add_post_media(self, post_id: int, media_type: str, media_url: str,
                       encrypted_url: str = None, encryption_key: str = None,
                       encryption_iv: str = None, thumbnail_url: str = None,
                       media_order: int = 0, width: int = None, height: int = None,
                       duration_seconds: int = None, file_size: int = None) -> Optional[int]:
        """Agregar media a una publicación (para carrusel)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_media (post_id, media_type, media_url, encrypted_url,
                           encryption_key, encryption_iv, thumbnail_url, media_order, width, 
                           height, duration_seconds, file_size) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (post_id, media_type, media_url, encrypted_url, encryption_key,
                         encryption_iv, thumbnail_url, media_order, width, height, 
                         duration_seconds, file_size)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error adding media to post {post_id}: {e}")
            return None
    
    def get_post_with_media(self, post_id: int, viewer_id: str = None) -> Optional[dict]:
        """Obtener publicación con todos sus medios"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT COUNT(*) FROM post_reactions WHERE post_id = p.id) as reactions_count,
                           (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id AND is_active = TRUE) as comments_count,
                           (SELECT COUNT(*) FROM post_views WHERE post_id = p.id) as views_count
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.id = %s AND p.is_active = TRUE""",
                        (post_id,)
                    )
                    post = cur.fetchone()
                    if not post:
                        return None
                    
                    post_dict = dict(post)
                    
                    cur.execute(
                        """SELECT * FROM post_media WHERE post_id = %s ORDER BY media_order""",
                        (post_id,)
                    )
                    post_dict['media'] = [dict(m) for m in cur.fetchall()]
                    
                    if viewer_id:
                        cur.execute(
                            "SELECT reaction_type FROM post_reactions WHERE post_id = %s AND user_id = %s",
                            (post_id, viewer_id)
                        )
                        reaction = cur.fetchone()
                        post_dict['user_reaction'] = reaction['reaction_type'] if reaction else None
                        
                        cur.execute(
                            "SELECT 1 FROM post_saves WHERE post_id = %s AND user_id = %s",
                            (post_id, viewer_id)
                        )
                        post_dict['user_saved'] = cur.fetchone() is not None
                    
                    cur.execute(
                        """SELECT reaction_type, COUNT(*) as count 
                           FROM post_reactions WHERE post_id = %s GROUP BY reaction_type""",
                        (post_id,)
                    )
                    post_dict['reactions_by_type'] = {r['reaction_type']: r['count'] for r in cur.fetchall()}
                    
                    return post_dict
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    def get_feed_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        """Obtener feed de publicaciones (propias, seguidos, y populares)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT COUNT(*) FROM post_reactions WHERE post_id = p.id) as reactions_count,
                           (SELECT reaction_type FROM post_reactions WHERE post_id = p.id AND user_id = %s) as user_reaction,
                           EXISTS(SELECT 1 FROM post_saves WHERE post_id = p.id AND user_id = %s) as user_saved,
                           (SELECT json_agg(json_build_object('id', pm.id, 'media_type', pm.media_type, 
                            'media_url', pm.media_url, 'encrypted_url', pm.encrypted_url, 
                            'thumbnail_url', pm.thumbnail_url, 'media_order', pm.media_order))
                            FROM post_media pm WHERE pm.post_id = p.id) as media
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.is_active = TRUE 
                           AND p.user_id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)
                           AND p.user_id NOT IN (SELECT blocker_id FROM user_blocks WHERE blocked_id = %s)
                           ORDER BY p.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, user_id, user_id, user_id, limit, offset)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting feed: {e}")
            return []
    
    def get_user_gallery(self, user_id: str, viewer_id: str = None, limit: int = 30, offset: int = 0) -> List[dict]:
        """Obtener galería de publicaciones de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if viewer_id:
                        cur.execute(
                            "SELECT 1 FROM user_blocks WHERE (blocker_id = %s AND blocked_id = %s) OR (blocker_id = %s AND blocked_id = %s)",
                            (user_id, viewer_id, viewer_id, user_id)
                        )
                        if cur.fetchone():
                            return []
                    
                    cur.execute(
                        """SELECT p.id, p.content_type, p.views_count,
                           (SELECT COUNT(*) FROM post_reactions WHERE post_id = p.id) as reactions_count,
                           (SELECT pm.thumbnail_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as thumbnail,
                           (SELECT pm.media_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as first_media,
                           (SELECT COUNT(*) FROM post_media pm WHERE pm.post_id = p.id) as media_count
                           FROM posts p
                           WHERE p.user_id = %s AND p.is_active = TRUE AND p.is_repost = FALSE
                           ORDER BY p.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, limit, offset)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user gallery: {e}")
            return []
    
    def count_new_posts(self, user_id: str, since_id: int) -> int:
        """Count new posts in feed since a given post ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(DISTINCT p.id)
                        FROM posts p
                        WHERE p.id > %s
                        AND (
                            p.user_id = %s
                            OR p.user_id IN (
                                SELECT following_id FROM follows 
                                WHERE follower_id = %s
                            )
                        )
                    """, (since_id, user_id, user_id))
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting new posts: {e}")
            return 0

    def add_reaction(self, user_id: str, post_id: int, reaction_type: str) -> bool:
        """Agregar o cambiar reacción a una publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_reactions (user_id, post_id, reaction_type)
                           VALUES (%s, %s, %s)
                           ON CONFLICT (user_id, post_id) 
                           DO UPDATE SET reaction_type = EXCLUDED.reaction_type, created_at = NOW()""",
                        (user_id, post_id, reaction_type)
                    )
                    
                    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                    post_owner = cur.fetchone()
                    if post_owner and post_owner[0] != user_id:
                        cur.execute(
                            """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                               VALUES (%s, 'reaction', %s, 'post', %s, %s)
                               ON CONFLICT DO NOTHING""",
                            (post_owner[0], user_id, post_id, f"reaccionó a tu publicación")
                        )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return False
    
    def remove_reaction(self, user_id: str, post_id: int) -> bool:
        """Quitar reacción de una publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM post_reactions WHERE user_id = %s AND post_id = %s",
                        (user_id, post_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            return False
    
    def add_comment(self, user_id: str, post_id: int, content: str, 
                    parent_comment_id: int = None) -> Optional[int]:
        """Agregar comentario a una publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_comments (post_id, user_id, content, parent_comment_id)
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (post_id, user_id, content, parent_comment_id)
                    )
                    result = cur.fetchone()
                    comment_id = result[0] if result else None
                    
                    cur.execute(
                        "UPDATE posts SET comments_count = comments_count + 1 WHERE id = %s",
                        (post_id,)
                    )
                    
                    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                    post_owner = cur.fetchone()
                    if post_owner and post_owner[0] != user_id:
                        cur.execute(
                            """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                               VALUES (%s, 'comment', %s, 'post', %s, %s)""",
                            (post_owner[0], user_id, post_id, "comentó en tu publicación")
                        )
                    
                    if parent_comment_id:
                        cur.execute("SELECT user_id FROM post_comments WHERE id = %s", (parent_comment_id,))
                        parent_author = cur.fetchone()
                        if parent_author and parent_author[0] != user_id and (not post_owner or parent_author[0] != post_owner[0]):
                            cur.execute(
                                """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                                   VALUES (%s, 'comment_reply', %s, 'comment', %s, %s)""",
                                (parent_author[0], user_id, comment_id, "respondió a tu comentario")
                            )
                    
                    conn.commit()
                    return comment_id
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return None
    
    def get_post_comments(self, post_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        """Obtener comentarios de una publicación - optimizado con una sola consulta"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """WITH parent_comments AS (
                            SELECT c.id
                            FROM post_comments c
                            WHERE c.post_id = %s AND c.is_active = TRUE AND c.parent_comment_id IS NULL
                            ORDER BY c.is_pinned DESC, c.created_at DESC
                            LIMIT %s OFFSET %s
                        )
                        SELECT c.*, u.username, u.first_name, u.avatar_url
                        FROM post_comments c
                        LEFT JOIN users u ON c.user_id = u.id
                        WHERE c.post_id = %s AND c.is_active = TRUE
                          AND (c.parent_comment_id IS NULL AND c.id IN (SELECT id FROM parent_comments)
                               OR c.parent_comment_id IN (SELECT id FROM parent_comments))
                        ORDER BY c.created_at ASC""",
                        (post_id, limit, offset, post_id)
                    )
                    all_comments = [dict(row) for row in cur.fetchall()]
                    
                    comments_map = {}
                    result = []
                    
                    for comment in all_comments:
                        if comment['parent_comment_id'] is None:
                            comment['replies'] = []
                            comments_map[comment['id']] = comment
                            result.append(comment)
                    
                    for comment in all_comments:
                        if comment['parent_comment_id'] is not None:
                            parent_id = comment['parent_comment_id']
                            parent = comments_map.get(parent_id)
                            if parent is not None:
                                parent['replies'].append(comment)
                    
                    result.sort(key=lambda x: (not x.get('is_pinned', False), x.get('created_at')), reverse=True)
                    
                    return result
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    def update_comment(self, user_id: str, comment_id: int, content: str, edit_time_limit_minutes: int = 15) -> dict:
        """Actualizar un comentario - solo el autor puede editar dentro del límite de tiempo"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT id, user_id, content, created_at 
                           FROM post_comments 
                           WHERE id = %s AND is_active = TRUE""",
                        (comment_id,)
                    )
                    comment = cur.fetchone()
                    
                    if not comment:
                        return {'success': False, 'error': 'Comentario no encontrado'}
                    
                    if str(comment['user_id']) != str(user_id):
                        return {'success': False, 'error': 'No tienes permiso para editar este comentario'}
                    
                    from datetime import datetime, timedelta, timezone
                    created_at = comment['created_at']
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    
                    time_limit = timedelta(minutes=edit_time_limit_minutes)
                    now = datetime.now(timezone.utc)
                    
                    if now - created_at > time_limit:
                        return {'success': False, 'error': f'Solo puedes editar comentarios dentro de los primeros {edit_time_limit_minutes} minutos'}
                    
                    cur.execute(
                        """UPDATE post_comments 
                           SET content = %s, updated_at = CURRENT_TIMESTAMP, is_edited = TRUE
                           WHERE id = %s""",
                        (content.strip(), comment_id)
                    )
                    conn.commit()
                    
                    return {'success': True, 'message': 'Comentario actualizado'}
        except Exception as e:
            logger.error(f"Error updating comment: {e}")
            return {'success': False, 'error': 'Error al actualizar comentario'}
    
    def get_comment_by_id(self, comment_id: int) -> Optional[dict]:
        """Obtener un comentario por ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT c.*, u.username, u.first_name, u.avatar_url
                           FROM post_comments c
                           LEFT JOIN users u ON c.user_id = u.id
                           WHERE c.id = %s AND c.is_active = TRUE""",
                        (comment_id,)
                    )
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting comment: {e}")
            return None
    
    def like_comment(self, user_id: str, comment_id: int) -> bool:
        """Dar like a un comentario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO comment_likes (user_id, comment_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (user_id, comment_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE post_comments SET likes_count = likes_count + 1 WHERE id = %s",
                            (comment_id,)
                        )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error liking comment: {e}")
            return False
    
    def unlike_comment(self, user_id: str, comment_id: int) -> bool:
        """Quitar like de un comentario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM comment_likes WHERE user_id = %s AND comment_id = %s",
                        (user_id, comment_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE post_comments SET likes_count = GREATEST(0, likes_count - 1) WHERE id = %s",
                            (comment_id,)
                        )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error unliking comment: {e}")
            return False
    
    def add_comment_reaction(self, user_id: str, comment_id: int, reaction_type: str) -> dict:
        """Agregar o actualizar reacción a un comentario"""
        valid_reactions = ['like', 'love', 'laugh', 'wow', 'sad', 'angry']
        if reaction_type not in valid_reactions:
            return {'success': False, 'error': 'Tipo de reacción no válido'}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO comment_reactions (user_id, comment_id, reaction_type)
                           VALUES (%s, %s, %s)
                           ON CONFLICT (user_id, comment_id) 
                           DO UPDATE SET reaction_type = EXCLUDED.reaction_type, created_at = NOW()""",
                        (user_id, comment_id, reaction_type)
                    )
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f"Error adding comment reaction: {e}")
            return {'success': False, 'error': 'Error al agregar reacción'}
    
    def remove_comment_reaction(self, user_id: str, comment_id: int) -> dict:
        """Eliminar reacción de un comentario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM comment_reactions WHERE user_id = %s AND comment_id = %s",
                        (user_id, comment_id)
                    )
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f"Error removing comment reaction: {e}")
            return {'success': False, 'error': 'Error al eliminar reacción'}
    
    def get_comment_reactions(self, comment_id: int) -> dict:
        """Obtener resumen de reacciones de un comentario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT reaction_type, COUNT(*) as count 
                           FROM comment_reactions WHERE comment_id = %s 
                           GROUP BY reaction_type""",
                        (comment_id,)
                    )
                    reactions = {r['reaction_type']: r['count'] for r in cur.fetchall()}
                    
                    cur.execute(
                        "SELECT COUNT(*) FROM comment_reactions WHERE comment_id = %s",
                        (comment_id,)
                    )
                    total = cur.fetchone()['count']
                    
                    return {'success': True, 'reactions': reactions, 'total': total}
        except Exception as e:
            logger.error(f"Error getting comment reactions: {e}")
            return {'success': False, 'reactions': {}, 'total': 0}
    
    def get_user_comment_reaction(self, user_id: str, comment_id: int) -> Optional[str]:
        """Obtener la reacción del usuario en un comentario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT reaction_type FROM comment_reactions WHERE user_id = %s AND comment_id = %s",
                        (user_id, comment_id)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user comment reaction: {e}")
            return None
    
    def pin_comment(self, user_id: str, post_id: int, comment_id: int) -> bool:
        """Fijar comentario (solo el dueño del post puede)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                    post = cur.fetchone()
                    if not post or post[0] != user_id:
                        return False
                    
                    cur.execute(
                        "UPDATE post_comments SET is_pinned = FALSE WHERE post_id = %s",
                        (post_id,)
                    )
                    cur.execute(
                        "UPDATE post_comments SET is_pinned = TRUE WHERE id = %s AND post_id = %s",
                        (comment_id, post_id)
                    )
                    cur.execute(
                        "UPDATE posts SET pinned_comment_id = %s WHERE id = %s",
                        (comment_id, post_id)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error pinning comment: {e}")
            return False
    
    def save_post(self, user_id: str, post_id: int) -> bool:
        """Guardar publicación en favoritos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_saves (user_id, post_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (user_id, post_id)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False
    
    def unsave_post(self, user_id: str, post_id: int) -> bool:
        """Quitar publicación de favoritos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM post_saves WHERE user_id = %s AND post_id = %s",
                        (user_id, post_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error unsaving post: {e}")
            return False
    
    def get_saved_posts(self, user_id: str, limit: int = 30, offset: int = 0) -> List[dict]:
        """Obtener publicaciones guardadas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT pm.thumbnail_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as thumbnail,
                           (SELECT pm.media_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as first_media
                           FROM post_saves ps
                           JOIN posts p ON ps.post_id = p.id
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE ps.user_id = %s AND p.is_active = TRUE
                           ORDER BY ps.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (user_id, limit, offset)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting saved posts: {e}")
            return []
    
    def record_post_view(self, post_id: int, user_id: str) -> bool:
        """Registrar vista de publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_views (post_id, user_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (post_id, user_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE posts SET views_count = views_count + 1 WHERE id = %s",
                            (post_id,)
                        )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error recording view: {e}")
            return False
    
    def process_hashtags(self, post_id: int, caption: str) -> List[str]:
        """Procesar y guardar hashtags de una publicación"""
        import re
        hashtags = re.findall(r'#(\w+)', caption or '')
        
        if not hashtags:
            return []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for tag in hashtags:
                        tag_lower = tag.lower()
                        cur.execute(
                            """INSERT INTO hashtags (tag) VALUES (%s)
                               ON CONFLICT (tag) DO UPDATE SET posts_count = hashtags.posts_count + 1
                               RETURNING id""",
                            (tag_lower,)
                        )
                        hashtag_id = cur.fetchone()[0]
                        
                        cur.execute(
                            """INSERT INTO post_hashtags (post_id, hashtag_id)
                               VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                            (post_id, hashtag_id)
                        )
                    conn.commit()
                    return hashtags
        except Exception as e:
            logger.error(f"Error processing hashtags: {e}")
            return []
    
    def process_mentions(self, post_id: int, caption: str, mention_type: str = 'post') -> List[str]:
        """Procesar y guardar menciones de una publicación o comentario"""
        import re
        mentions = re.findall(r'@(\w+)', caption or '')
        
        if not mentions:
            return []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for username in mentions:
                        cur.execute(
                            "SELECT id FROM users WHERE username = %s",
                            (username,)
                        )
                        user = cur.fetchone()
                        if user:
                            if mention_type == 'post':
                                cur.execute(
                                    """INSERT INTO post_mentions (post_id, mentioned_user_id)
                                       VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                                    (post_id, user[0])
                                )
                            
                            cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                            post_owner = cur.fetchone()
                            if post_owner:
                                cur.execute(
                                    """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                                       VALUES (%s, 'mention', %s, 'post', %s, %s)""",
                                    (user[0], post_owner[0], post_id, "te mencionó en una publicación")
                                )
                    conn.commit()
                    return mentions
        except Exception as e:
            logger.error(f"Error processing mentions: {e}")
            return []
    
    def get_trending_hashtags(self, limit: int = 10) -> List[dict]:
        """Obtener hashtags trending"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT tag, posts_count FROM hashtags
                           ORDER BY posts_count DESC
                           LIMIT %s""",
                        (limit,)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {e}")
            return []
    
    def get_posts_by_hashtag(self, hashtag: str, user_id: str = None, limit: int = 30, offset: int = 0) -> List[dict]:
        """Obtener publicaciones por hashtag"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT pm.thumbnail_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as thumbnail,
                           (SELECT pm.media_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as first_media
                           FROM posts p
                           JOIN post_hashtags ph ON p.id = ph.post_id
                           JOIN hashtags h ON ph.hashtag_id = h.id
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE h.tag = %s AND p.is_active = TRUE
                           ORDER BY p.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (hashtag.lower(), limit, offset)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting posts by hashtag: {e}")
            return []
    
    def create_story(self, user_id: str, media_type: str, media_url: str,
                     encrypted_url: str = None, encryption_key: str = None,
                     encryption_iv: str = None, thumbnail_url: str = None,
                     duration_seconds: int = 15) -> Optional[int]:
        """Crear una historia (24 horas)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    expires_at = datetime.now() + timedelta(hours=24)
                    cur.execute(
                        """INSERT INTO stories (user_id, media_type, media_url, encrypted_url,
                           encryption_key, encryption_iv, thumbnail_url, duration_seconds, expires_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (user_id, media_type, media_url, encrypted_url, encryption_key,
                         encryption_iv, thumbnail_url, duration_seconds, expires_at)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating story: {e}")
            return None
    
    def get_stories_feed(self, user_id: str) -> List[dict]:
        """Obtener historias del feed (propias y de seguidos)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT DISTINCT ON (s.user_id) 
                           s.user_id, u.username, u.first_name, u.avatar_url,
                           (SELECT COUNT(*) FROM stories WHERE user_id = s.user_id AND is_active = TRUE AND expires_at > NOW()) as stories_count,
                           EXISTS(SELECT 1 FROM story_views sv 
                                  JOIN stories st ON sv.story_id = st.id 
                                  WHERE st.user_id = s.user_id AND sv.user_id = %s 
                                  AND st.is_active = TRUE AND st.expires_at > NOW()) as has_viewed
                           FROM stories s
                           LEFT JOIN users u ON s.user_id = u.id
                           WHERE s.is_active = TRUE AND s.expires_at > NOW()
                           AND (s.user_id = %s OR s.user_id IN (SELECT following_id FROM follows WHERE follower_id = %s))
                           AND s.user_id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)
                           ORDER BY s.user_id, s.created_at DESC""",
                        (user_id, user_id, user_id, user_id)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting stories feed: {e}")
            return []
    
    def get_user_stories(self, user_id: str, viewer_id: str = None) -> List[dict]:
        """Obtener historias de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if viewer_id:
                        cur.execute(
                            "SELECT 1 FROM user_blocks WHERE (blocker_id = %s AND blocked_id = %s) OR (blocker_id = %s AND blocked_id = %s)",
                            (user_id, viewer_id, viewer_id, user_id)
                        )
                        if cur.fetchone():
                            return []
                    
                    cur.execute(
                        """SELECT s.*, 
                           EXISTS(SELECT 1 FROM story_views WHERE story_id = s.id AND user_id = %s) as viewed
                           FROM stories s
                           WHERE s.user_id = %s AND s.is_active = TRUE AND s.expires_at > NOW()
                           ORDER BY s.created_at ASC""",
                        (viewer_id or '', user_id)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user stories: {e}")
            return []
    
    def view_story(self, story_id: int, user_id: str) -> bool:
        """Registrar vista de historia"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO story_views (story_id, user_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (story_id, user_id)
                    )
                    if cur.rowcount > 0:
                        cur.execute(
                            "UPDATE stories SET views_count = views_count + 1 WHERE id = %s",
                            (story_id,)
                        )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error viewing story: {e}")
            return False
    
    def get_story_viewers(self, story_id: int, user_id: str) -> List[dict]:
        """Obtener lista de usuarios que vieron una historia (solo el dueño)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT user_id FROM stories WHERE id = %s", (story_id,))
                    story = cur.fetchone()
                    if not story or story['user_id'] != user_id:
                        return []
                    
                    cur.execute(
                        """SELECT u.id, u.username, u.first_name, u.avatar_url, sv.viewed_at
                           FROM story_views sv
                           JOIN users u ON sv.user_id = u.id
                           WHERE sv.story_id = %s
                           ORDER BY sv.viewed_at DESC""",
                        (story_id,)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting story viewers: {e}")
            return []

    def delete_story(self, story_id: int, user_id: str) -> bool:
        """Eliminar una historia (solo el dueño)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM stories WHERE id = %s AND user_id = %s",
                        (story_id, user_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting story: {e}")
            return False

    def react_to_story(self, story_id: int, user_id: str, reaction: str) -> bool:
        """Reaccionar a una historia"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM stories WHERE id = %s", (story_id,))
                    story = cur.fetchone()
                    if not story:
                        return False
                    
                    story_owner_id = story[0]
                    if story_owner_id != user_id:
                        cur.execute(
                            """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                               VALUES (%s, 'story_reaction', %s, 'story', %s, %s)""",
                            (story_owner_id, user_id, story_id, f"reaccionó {reaction} a tu historia")
                        )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error reacting to story: {e}")
            return False
    
    def block_user(self, blocker_id: str, blocked_id: str) -> bool:
        """Bloquear a un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO user_blocks (blocker_id, blocked_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (blocker_id, blocked_id)
                    )
                    
                    cur.execute(
                        "DELETE FROM follows WHERE (follower_id = %s AND following_id = %s) OR (follower_id = %s AND following_id = %s)",
                        (blocker_id, blocked_id, blocked_id, blocker_id)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return False
    
    def unblock_user(self, blocker_id: str, blocked_id: str) -> bool:
        """Desbloquear a un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM user_blocks WHERE blocker_id = %s AND blocked_id = %s",
                        (blocker_id, blocked_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            return False
    
    def get_blocked_users(self, user_id: str) -> List[dict]:
        """Obtener lista de usuarios bloqueados"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT u.id, u.username, u.first_name, u.avatar_url, ub.created_at as blocked_at
                           FROM user_blocks ub
                           JOIN users u ON ub.blocked_id = u.id
                           WHERE ub.blocker_id = %s
                           ORDER BY ub.created_at DESC""",
                        (user_id,)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting blocked users: {e}")
            return []
    
    def create_report(self, reporter_id: str, content_type: str, content_id: int, 
                      reason: str, description: str = None) -> Optional[int]:
        """Crear reporte de contenido"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO content_reports (reporter_id, content_type, content_id, reason, description)
                           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                        (reporter_id, content_type, content_id, reason, description)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return None
    
    def get_reports(self, status: str = 'pending', limit: int = 50, offset: int = 0) -> List[dict]:
        """Obtener reportes (para admin)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT r.*, u.username as reporter_username
                           FROM content_reports r
                           LEFT JOIN users u ON r.reporter_id = u.id
                           WHERE r.status = %s
                           ORDER BY r.created_at DESC
                           LIMIT %s OFFSET %s""",
                        (status, limit, offset)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting reports: {e}")
            return []
    
    def update_report_status(self, report_id: int, status: str, admin_id: str, notes: str = None) -> bool:
        """Actualizar estado de un reporte (para admin)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE content_reports 
                           SET status = %s, reviewed_by = %s, admin_notes = %s, reviewed_at = NOW()
                           WHERE id = %s""",
                        (status, admin_id, notes, report_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating report: {e}")
            return False
    
    def get_notifications(self, user_id: str, limit: int = 50, offset: int = 0, 
                          unread_only: bool = False, filter_type: str = 'all') -> List[dict]:
        """Obtener notificaciones de un usuario con filtros"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    query = """SELECT n.*, u.username as actor_username, u.first_name as actor_first_name, u.avatar_url as actor_avatar
                               FROM notifications n
                               LEFT JOIN users u ON n.actor_id = u.id
                               WHERE n.user_id = %s"""
                    params = [user_id]
                    
                    if unread_only or filter_type == 'unread':
                        query += " AND n.is_read = FALSE"
                    
                    if filter_type == 'transactions':
                        query += " AND n.type IN ('transaction', 'transaction_credit', 'transaction_debit')"
                    elif filter_type == 'likes':
                        query += " AND n.type IN ('like', 'reaction')"
                    elif filter_type == 'comments':
                        query += " AND n.type IN ('comment', 'comment_reply')"
                    elif filter_type == 'follows':
                        query += " AND n.type IN ('follow', 'new_follower')"
                    elif filter_type == 'mentions':
                        query += " AND n.type = 'mention'"
                    elif filter_type == 'stories':
                        query += " AND n.type IN ('story_reply', 'story_reaction', 'story_view')"
                    
                    query += " ORDER BY n.created_at DESC LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                    
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def mark_notifications_read(self, user_id: str, notification_ids: List[int] = None) -> bool:
        """Marcar notificaciones como leídas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    if notification_ids:
                        cur.execute(
                            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND id = ANY(%s)",
                            (user_id, notification_ids)
                        )
                    else:
                        cur.execute(
                            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
                            (user_id,)
                        )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error marking notifications read: {e}")
            return False
    
    def get_unread_notifications_count(self, user_id: str) -> int:
        """Obtener cantidad de notificaciones no leídas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def create_notification(self, user_id: str, notif_type: str, message: str,
                           actor_id: str = None, reference_type: str = None,
                           reference_id: int = None) -> Optional[int]:
        """Crear una notificación genérica"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO notifications 
                           (user_id, type, actor_id, reference_type, reference_id, message)
                           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                        (user_id, notif_type, actor_id, reference_type, reference_id, message)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def create_transaction_notification(self, user_id: str, amount: float, 
                                        transaction_type: str, new_balance: float = None) -> Optional[int]:
        """Crear notificación de transacción de wallet"""
        try:
            safe_amount = float(amount) if amount else 0.0
            safe_balance = float(new_balance) if new_balance is not None else safe_amount
            
            if transaction_type in ['credit', 'deposit', 'recharge']:
                notif_type = 'transaction_credit'
                message = f"Recarga de +{safe_amount:.2f} BUNK3RCO1N completada. Nuevo saldo: {safe_balance:.2f}"
            elif transaction_type in ['debit', 'purchase', 'bot_purchase']:
                notif_type = 'transaction_debit'
                message = f"Gasto de -{safe_amount:.2f} BUNK3RCO1N procesado. Saldo restante: {safe_balance:.2f}"
            else:
                notif_type = 'transaction'
                message = f"Movimiento de {safe_amount:.2f} BUNK3RCO1N. Saldo: {safe_balance:.2f}"
            
            return self.create_notification(
                user_id=user_id,
                notif_type=notif_type,
                message=message,
                reference_type='wallet',
                reference_id=None
            )
        except Exception as e:
            logger.error(f"Error creating transaction notification: {e}")
            return None
    
    def get_notification_preferences(self, user_id: str) -> dict:
        """Obtener preferencias de notificaciones del usuario"""
        defaults = {
            'likes': True,
            'comments': True,
            'follows': True,
            'mentions': True,
            'transactions': True,
            'stories': True,
            'push_enabled': True
        }
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT notification_preferences FROM users WHERE id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    if result and result.get('notification_preferences'):
                        prefs = result['notification_preferences']
                        if isinstance(prefs, str):
                            import json
                            prefs = json.loads(prefs)
                        return {**defaults, **prefs}
                    return defaults
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return defaults
    
    def update_notification_preferences(self, user_id: str, preferences: dict) -> bool:
        """Actualizar preferencias de notificaciones del usuario"""
        try:
            import json
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET notification_preferences = %s WHERE id = %s",
                        (json.dumps(preferences), user_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return False
    
    def should_notify_user(self, user_id: str, notif_type: str) -> bool:
        """Verificar si el usuario quiere recibir este tipo de notificación"""
        try:
            prefs = self.get_notification_preferences(user_id)
            type_map = {
                'like': 'likes',
                'reaction': 'likes',
                'comment': 'comments',
                'comment_reply': 'comments',
                'follow': 'follows',
                'new_follower': 'follows',
                'mention': 'mentions',
                'transaction': 'transactions',
                'transaction_credit': 'transactions',
                'transaction_debit': 'transactions',
                'story_reply': 'stories',
                'story_reaction': 'stories',
                'story_view': 'stories'
            }
            pref_key = type_map.get(notif_type, notif_type)
            return prefs.get(pref_key, True)
        except Exception as e:
            logger.error(f"Error checking notification preference: {e}")
            return True
    
    def share_post(self, user_id: str, post_id: int, share_type: str = 'repost', 
                   quote_text: str = None, recipient_id: str = None) -> Optional[int]:
        """Compartir/repostear una publicación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO post_shares (user_id, post_id, share_type, quote_text, recipient_id)
                           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                        (user_id, post_id, share_type, quote_text, recipient_id)
                    )
                    result = cur.fetchone()
                    
                    cur.execute(
                        "UPDATE posts SET shares_count = shares_count + 1 WHERE id = %s",
                        (post_id,)
                    )
                    
                    if share_type == 'repost':
                        cur.execute("SELECT content_type, caption FROM posts WHERE id = %s", (post_id,))
                        original = cur.fetchone()
                        if original:
                            cur.execute(
                                """INSERT INTO posts (user_id, content_type, caption, is_repost, original_post_id, quote_text)
                                   VALUES (%s, %s, %s, TRUE, %s, %s) RETURNING id""",
                                (user_id, original[0], original[1], post_id, quote_text)
                            )
                    
                    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                    post_owner = cur.fetchone()
                    if post_owner and post_owner[0] != user_id:
                        cur.execute(
                            """INSERT INTO notifications (user_id, type, actor_id, reference_type, reference_id, message)
                               VALUES (%s, 'share', %s, 'post', %s, %s)""",
                            (post_owner[0], user_id, post_id, "compartió tu publicación")
                        )
                    
                    conn.commit()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Error sharing post: {e}")
            return None
    
    def increment_share_count(self, post_id: int) -> bool:
        """Incrementar contador de shares para enlaces externos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE posts SET shares_count = COALESCE(shares_count, 0) + 1 WHERE id = %s",
                        (post_id,)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error incrementing share count: {e}")
            return False
    
    def delete_post(self, post_id: int, user_id: str) -> bool:
        """Eliminar publicación (solo el dueño)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE posts SET is_active = FALSE WHERE id = %s AND user_id = %s",
                        (post_id, user_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            return False
    
    def update_post(self, post_id: int, user_id: str, caption: str = None, 
                    comments_enabled: bool = None) -> bool:
        """Editar publicación (solo el dueño)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                    post = cur.fetchone()
                    if not post or post[0] != user_id:
                        return False
                    
                    updates = []
                    params = []
                    
                    if caption is not None:
                        updates.append("caption = %s")
                        params.append(caption)
                    
                    if comments_enabled is not None:
                        updates.append("comments_enabled = %s")
                        params.append(comments_enabled)
                    
                    if updates:
                        params.append(post_id)
                        cur.execute(
                            f"UPDATE posts SET {', '.join(updates)} WHERE id = %s",
                            params
                        )
                        
                        if caption:
                            self.process_hashtags(post_id, caption)
                            self.process_mentions(post_id, caption)
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating post: {e}")
            return False
    
    def get_explore_posts(self, user_id: str = None, limit: int = 30, offset: int = 0) -> List[dict]:
        """Obtener publicaciones para explorar (trending/populares)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    query = """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT COUNT(*) FROM post_reactions WHERE post_id = p.id) as reactions_count,
                           (SELECT pm.thumbnail_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as thumbnail,
                           (SELECT pm.media_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as first_media
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.is_active = TRUE AND p.is_repost = FALSE"""
                    
                    params = []
                    if user_id:
                        query += """ AND p.user_id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)
                                    AND p.user_id NOT IN (SELECT blocker_id FROM user_blocks WHERE blocked_id = %s)"""
                        params.extend([user_id, user_id])
                    
                    query += """ ORDER BY (
                           (SELECT COUNT(*) FROM post_reactions WHERE post_id = p.id) +
                           p.comments_count * 2 +
                           p.views_count * 0.1
                           ) DESC, p.created_at DESC
                           LIMIT %s OFFSET %s"""
                    params.extend([limit, offset])
                    
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting explore posts: {e}")
            return []
    
    def search_posts(self, query: str, user_id: str = None, limit: int = 30, offset: int = 0) -> List[dict]:
        """Buscar publicaciones por texto en caption"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    search_query = f"%{query}%"
                    sql = """SELECT p.*, u.username, u.first_name, u.avatar_url,
                           (SELECT pm.thumbnail_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as thumbnail,
                           (SELECT pm.media_url FROM post_media pm WHERE pm.post_id = p.id ORDER BY pm.media_order LIMIT 1) as first_media
                           FROM posts p
                           LEFT JOIN users u ON p.user_id = u.id
                           WHERE p.is_active = TRUE AND p.caption ILIKE %s"""
                    
                    params = [search_query]
                    if user_id:
                        sql += """ AND p.user_id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)"""
                        params.append(user_id)
                    
                    sql += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                    
                    cur.execute(sql, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return []
    
    def get_suggested_users(self, user_id: str, limit: int = 10) -> List[dict]:
        """Obtener sugerencias de usuarios para seguir"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT u.id, u.username, u.first_name, u.avatar_url, u.bio,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id) as followers_count,
                           (SELECT COUNT(*) FROM posts WHERE user_id = u.id AND is_active = TRUE) as posts_count
                           FROM users u
                           WHERE u.id != %s
                           AND u.id NOT IN (SELECT following_id FROM follows WHERE follower_id = %s)
                           AND u.id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)
                           AND u.id NOT IN (SELECT blocker_id FROM user_blocks WHERE blocked_id = %s)
                           AND u.is_active = TRUE
                           ORDER BY followers_count DESC, posts_count DESC
                           LIMIT %s""",
                        (user_id, user_id, user_id, user_id, limit)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting suggested users: {e}")
            return []
    
    def search_users(self, query: str, user_id: str = None, limit: int = 20) -> List[dict]:
        """Buscar usuarios por username o nombre"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    search_query = f"%{query}%"
                    sql = """SELECT u.id, u.username, u.first_name, u.avatar_url,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id) as followers_count
                           FROM users u
                           WHERE u.is_active = TRUE 
                           AND (u.username ILIKE %s OR u.first_name ILIKE %s)"""
                    
                    params = [search_query, search_query]
                    if user_id:
                        sql += """ AND u.id NOT IN (SELECT blocked_id FROM user_blocks WHERE blocker_id = %s)
                                  AND u.id NOT IN (SELECT blocker_id FROM user_blocks WHERE blocked_id = %s)"""
                        params.extend([user_id, user_id])
                    
                    sql += " ORDER BY followers_count DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(sql, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []


# Global database manager instance
db_manager = DatabaseManager()