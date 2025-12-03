"""
Database models and schema definitions for the tracking system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Tracking:
    """Tracking data model"""
    tracking_id: str
    delivery_address: str
    date_time: str
    package_weight: str
    product_name: str
    sender_address: str
    product_price: str
    # New separated fields for recipient
    recipient_postal_code: str = ""
    recipient_province: str = ""
    recipient_country: str = ""
    # New separated fields for sender
    sender_postal_code: str = ""
    sender_province: str = ""
    sender_country: str = ""
    # Legacy fields (kept for backwards compatibility, optional)
    recipient_name: Optional[str] = None
    country_postal: Optional[str] = None
    sender_name: Optional[str] = None
    sender_state: Optional[str] = None
    # Status and metadata
    status: str = "RETENIDO"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    estimated_delivery_date: Optional[str] = None
    actual_delay_days: int = 0
    user_telegram_id: Optional[int] = None
    username: Optional[str] = None
    created_by_admin_id: Optional[int] = None
    # OpenRouteService geocoding data
    sender_lat: Optional[float] = None
    sender_lon: Optional[float] = None
    sender_formatted_address: Optional[str] = None
    recipient_lat: Optional[float] = None
    recipient_lon: Optional[float] = None
    recipient_formatted_address: Optional[str] = None
    route_distance_km: Optional[float] = None
    route_duration_hours: Optional[float] = None
    route_geometry: Optional[str] = None
    # Additional database fields
    route_steps: Optional[list] = None
    current_step_index: int = 0
    route_distance: Optional[int] = None
    route_duration: Optional[int] = None
    owner_id: Optional[int] = None
    created_by: Optional[str] = None
    route_states: Optional[str] = None

@dataclass
class ShippingRoute:
    """Shipping route model"""
    origin_country: str
    destination_country: str
    estimated_days: int

@dataclass
class StatusHistory:
    """Status change history model"""
    tracking_id: str
    old_status: str
    new_status: str
    changed_at: datetime
    notes: Optional[str] = None
    id: Optional[int] = None

# Database table creation SQL
CREATE_TABLES_SQL = """
-- Trackings table
CREATE TABLE IF NOT EXISTS trackings (
    tracking_id VARCHAR(50) PRIMARY KEY,
    delivery_address TEXT NOT NULL,
    date_time VARCHAR(255) NOT NULL,
    package_weight VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    sender_address TEXT NOT NULL,
    product_price VARCHAR(100) NOT NULL,
    -- New separated fields
    recipient_postal_code VARCHAR(20) DEFAULT '',
    recipient_province VARCHAR(255) DEFAULT '',
    recipient_country VARCHAR(255) DEFAULT '',
    sender_postal_code VARCHAR(20) DEFAULT '',
    sender_province VARCHAR(255) DEFAULT '',
    sender_country VARCHAR(255) DEFAULT '',
    -- Legacy fields (kept for backwards compatibility)
    recipient_name VARCHAR(255),
    country_postal VARCHAR(255),
    sender_name VARCHAR(255),
    sender_state VARCHAR(255),
    -- Status and metadata
    status VARCHAR(50) DEFAULT 'RETENIDO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery_date VARCHAR(255),
    actual_delay_days INTEGER DEFAULT 0,
    user_telegram_id BIGINT,
    username VARCHAR(255),
    sender_lat DECIMAL(10, 8),
    sender_lon DECIMAL(11, 8),
    sender_formatted_address TEXT,
    recipient_lat DECIMAL(10, 8),
    recipient_lon DECIMAL(11, 8),
    recipient_formatted_address TEXT,
    route_distance_km DECIMAL(10, 2),
    route_duration_hours DECIMAL(10, 2),
    route_geometry TEXT
);

-- Shipping routes table
CREATE TABLE IF NOT EXISTS shipping_routes (
    id SERIAL PRIMARY KEY,
    origin_country VARCHAR(255) NOT NULL,
    destination_country VARCHAR(255) NOT NULL,
    estimated_days INTEGER NOT NULL,
    UNIQUE(origin_country, destination_country)
);

-- Status history table
CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    tracking_id VARCHAR(50) REFERENCES trackings(tracking_id),
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Insert default shipping routes
INSERT INTO shipping_routes (origin_country, destination_country, estimated_days) VALUES
('España', 'España', 2),
('España', 'Colombia', 10),
('España', 'México', 8),
('España', 'Argentina', 12),
('España', 'Chile', 11),
('España', 'Perú', 9),
('España', 'Ecuador', 8),
('España', 'Francia', 3),
('España', 'Italia', 4),
('España', 'Alemania', 3),
('España', 'Portugal', 2),
('España', 'Reino Unido', 4),
('España', 'Estados Unidos', 7),
('España', 'Canadá', 8)
ON CONFLICT (origin_country, destination_country) DO NOTHING;
"""

# Status constants
STATUS_RETENIDO = "RETENIDO"
STATUS_CONFIRMAR_PAGO = "CONFIRMAR_PAGO"
STATUS_EN_TRANSITO = "EN_TRANSITO"
STATUS_ENTREGADO = "ENTREGADO"

VALID_STATUSES = [STATUS_RETENIDO, STATUS_CONFIRMAR_PAGO, STATUS_EN_TRANSITO, STATUS_ENTREGADO]

# Status display with emojis
STATUS_DISPLAY = {
    STATUS_RETENIDO: "🔴 RETENIDO",
    STATUS_CONFIRMAR_PAGO: "🟡 CONFIRMAR PAGO",
    STATUS_EN_TRANSITO: "🔵 EN TRÁNSITO",
    STATUS_ENTREGADO: "🟢 ENTREGADO"
}