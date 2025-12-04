"""
Database connection and operations for the tracking system
"""

import os
import psycopg2
import psycopg2.extras
from typing import List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import random

try:
    import pytz
    SPAIN_TZ = pytz.timezone('Europe/Madrid')
except ImportError:
    SPAIN_TZ = None

from .models import Tracking, ShippingRoute, StatusHistory, CREATE_TABLES_SQL

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handle all database operations"""
    
    def __init__(self):
        # Use DATABASE_URL directly - it's the most reliable source
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Clean the URL (strip whitespace/newlines and handle async driver prefix)
        self.database_url = self.database_url.strip()
        
        # Clean database URL for psycopg2 (remove SQLAlchemy async driver prefix)
        if self.database_url.startswith('postgresql+asyncpg://'):
            self.database_url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        # Ensure sslmode=require is present for Neon databases
        if 'sslmode=' not in self.database_url:
            separator = '&' if '?' in self.database_url else '?'
            self.database_url = f"{self.database_url}{separator}sslmode=require"
        
        logger.info("Database connection configured using DATABASE_URL")
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
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
            
            if isinstance(checkpoints[0], dict):
                state_names = [cp.get("name", "") for cp in checkpoints if cp.get("name")]
            else:
                state_names = [str(cp) for cp in checkpoints if cp]
            
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
    
    def get_tracking_history(self, tracking_id: str, include_future: bool = False) -> List[StatusHistory]:
        """Get status change history for tracking
        
        Args:
            tracking_id: Tracking ID
            include_future: If True, includes future scheduled events. 
                           If False (default), only shows events up to current time.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if include_future:
                        cur.execute(
                            "SELECT * FROM status_history WHERE tracking_id = %s ORDER BY changed_at ASC, id ASC",
                            (tracking_id,)
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM status_history WHERE tracking_id = %s AND (changed_at IS NULL OR changed_at <= NOW()) ORDER BY changed_at ASC, id ASC",
                            (tracking_id,)
                        )
                    rows = cur.fetchall()
                    return [StatusHistory(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting tracking history: {e}")
            return []
    
    def get_statistics(self, admin_id: int, is_owner: bool = False) -> dict:
        """Get tracking statistics, filtered by admin if not owner"""
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
        """Obtener publicaciones de un usuario específico"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT p.*, u.username, u.first_name, u.avatar_url
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
                    cur.execute("SELECT id FROM posts WHERE id = %s AND is_active = TRUE", (post_id,))
                    if not cur.fetchone():
                        return {'success': False, 'error': 'post_not_found'}
                    
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
    
    def get_user_bots(self, user_id: str) -> List[dict]:
        """Obtener todos los bots activos de un usuario"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT ub.id, ub.bot_name, ub.bot_type, ub.is_active, ub.config, ub.created_at,
                                  bt.icon, bt.description, bt.price
                           FROM user_bots ub
                           LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                           WHERE ub.user_id = %s AND ub.is_active = TRUE
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
        """Comprar un bot - verifica créditos, descuenta y activa el bot"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT credits FROM users WHERE id = %s",
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
                    logger.info(f"User {user_id} purchased bot {bot_type} for {bot_price} credits")
                    return {
                        'success': True, 
                        'message': f'Bot {bot["bot_name"]} activado correctamente',
                        'bot_name': bot['bot_name'],
                        'credits_remaining': user_credits - bot_price
                    }
        except Exception as e:
            logger.error(f"Error purchasing bot {bot_type} for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
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


# Global database manager instance
db_manager = DatabaseManager()