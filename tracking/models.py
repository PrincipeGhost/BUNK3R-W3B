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

# ============================================================
# NUEVOS MODELOS PARA RED SOCIAL / MARKETPLACE
# ============================================================

@dataclass
class User:
    """User profile model"""
    telegram_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: int = 1
    credits: int = 0
    is_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    wallet_address: Optional[str] = None
    id: Optional[int] = None

@dataclass
class Post:
    """User post/publication model"""
    user_id: int
    content_type: str  # image, video, text
    content_url: Optional[str] = None
    caption: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class Follow:
    """User follow relationship model"""
    follower_id: int  # Who follows
    following_id: int  # Who is being followed
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class Product:
    """Marketplace product model"""
    user_id: int
    title: str
    description: Optional[str] = None
    price: float = 0.0
    currency: str = "credits"
    image_url: Optional[str] = None
    category: Optional[str] = None
    stock: int = 1
    is_active: bool = True
    is_sold: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class UserBot:
    """User's active bot model"""
    user_id: int
    bot_name: str
    bot_type: str
    is_active: bool = True
    config: Optional[str] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class Achievement:
    """User achievement/badge model"""
    user_id: int
    achievement_type: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    earned_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class WalletTransaction:
    """Wallet credit transaction model"""
    user_id: int
    transaction_type: str  # deposit, withdraw, purchase, sale, reward
    amount: float
    description: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class SharedPost:
    """Shared/reposted content model"""
    user_id: int  # Who shared
    original_post_id: int  # Original post
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

# SQL para crear las nuevas tablas de red social
CREATE_SOCIAL_TABLES_SQL = """
-- ============================================================
-- USUARIOS - Agregar columnas si no existen
-- ============================================================
-- Agregar columnas faltantes a la tabla users existente
DO $$
BEGIN
    -- telegram_id
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='telegram_id') THEN
        ALTER TABLE users ADD COLUMN telegram_id BIGINT;
    END IF;
    -- first_name
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='first_name') THEN
        ALTER TABLE users ADD COLUMN first_name VARCHAR(255);
    END IF;
    -- last_name
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='last_name') THEN
        ALTER TABLE users ADD COLUMN last_name VARCHAR(255);
    END IF;
    -- avatar_url
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='avatar_url') THEN
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    END IF;
    -- bio
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='bio') THEN
        ALTER TABLE users ADD COLUMN bio TEXT;
    END IF;
    -- level
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='level') THEN
        ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1;
    END IF;
    -- credits
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits') THEN
        ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0;
    END IF;
    -- is_verified
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_verified') THEN
        ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
    END IF;
    -- is_active
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_active') THEN
        ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
    -- created_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='created_at') THEN
        ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    -- updated_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='updated_at') THEN
        ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    -- last_seen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='last_seen') THEN
        ALTER TABLE users ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Indice para busquedas rapidas por telegram_id (si existe la columna)
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- ============================================================
-- PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    content_url TEXT,
    caption TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);

-- ============================================================
-- SEGUIDORES (Relaciones de seguimiento)
-- ============================================================
CREATE TABLE IF NOT EXISTS follows (
    id SERIAL PRIMARY KEY,
    follower_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    following_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(follower_id, following_id)
);

CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);

-- ============================================================
-- PRODUCTOS DEL MARKETPLACE
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(20) DEFAULT 'credits',
    image_url TEXT,
    category VARCHAR(100),
    stock INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_sold BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active, is_sold);

-- ============================================================
-- BOTS ACTIVOS DEL USUARIO
-- ============================================================
CREATE TABLE IF NOT EXISTS user_bots (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    bot_name VARCHAR(255) NOT NULL,
    bot_type VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_bots_user_id ON user_bots(user_id);

-- ============================================================
-- LOGROS / INSIGNIAS
-- ============================================================
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_type)
);

CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);

-- ============================================================
-- TRANSACCIONES DE BILLETERA
-- ============================================================
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    reference_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallet_user_id ON wallet_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_created_at ON wallet_transactions(created_at DESC);

-- ============================================================
-- PUBLICACIONES COMPARTIDAS
-- ============================================================
CREATE TABLE IF NOT EXISTS shared_posts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    original_post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shared_posts_user_id ON shared_posts(user_id);

-- ============================================================
-- LIKES DE PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS post_likes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);

-- ============================================================
-- TIPOS DE LOGROS DISPONIBLES (tabla de referencia)
-- ============================================================
CREATE TABLE IF NOT EXISTS achievement_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    points INTEGER DEFAULT 0
);

-- Insertar tipos de logros predefinidos
INSERT INTO achievement_types (type_code, title, description, icon, points) VALUES
('new_user', 'Nuevo Usuario', 'Te uniste a BUNK3R', '🌟', 10),
('first_post', 'Primera Publicacion', 'Publicaste tu primer contenido', '📸', 20),
('first_sale', 'Primera Venta', 'Vendiste tu primer producto', '💰', 50),
('first_purchase', 'Primera Compra', 'Compraste tu primer producto', '🛒', 30),
('popular', 'Popular', 'Conseguiste 100 seguidores', '🔥', 100),
('verified', 'Verificado', 'Tu cuenta fue verificada', '✅', 200),
('tracker_pro', 'Rastreador Pro', 'Rastreaste 10 envios', '📦', 40),
('bot_master', 'Bot Master', 'Activaste tu primer bot', '🤖', 60)
ON CONFLICT (type_code) DO NOTHING;
"""