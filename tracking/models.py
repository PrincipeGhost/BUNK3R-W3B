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

@dataclass
class RiskScore:
    """User risk score model for fraud detection"""
    user_id: str
    score: int  # 0-100, higher = more risk
    risk_level: str  # low, medium, high, critical
    factors: Optional[dict] = None
    last_calculated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class RiskScoreHistory:
    """History of risk score changes"""
    user_id: str
    old_score: int
    new_score: int
    old_level: str
    new_level: str
    reason: Optional[str] = None
    changed_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class SupportTicket:
    """Support ticket model"""
    user_id: str
    subject: str
    message: str
    status: str = "open"  # open, in_progress, resolved, closed
    priority: str = "normal"  # low, normal, high, urgent
    category: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class TicketReply:
    """Reply to a support ticket"""
    ticket_id: int
    user_id: str
    message: str
    is_admin: bool = False
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class SystemConfig:
    """System configuration model"""
    key: str
    value: str
    description: Optional[str] = None
    category: str = "general"
    is_public: bool = False
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    id: Optional[int] = None

@dataclass
class PrivateMessage:
    """Private message between users"""
    sender_id: str
    receiver_id: str
    content: str
    is_read: bool = False
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class AnomalyDetection:
    """Anomaly detection record"""
    user_id: Optional[str] = None
    anomaly_type: str = ""  # unusual_login, large_transaction, rapid_transfers, etc.
    severity: str = "medium"  # low, medium, high, critical
    description: Optional[str] = None
    data: Optional[dict] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    action_taken: Optional[str] = None
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

CREATE_ENCRYPTED_POSTS_SQL = """
-- ============================================================
-- SISTEMA COMPLETO DE PUBLICACIONES ENCRIPTADAS
-- ============================================================

-- Agregar columnas de encriptación a posts existente
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='encryption_key') THEN
        ALTER TABLE posts ADD COLUMN encryption_key TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='encryption_iv') THEN
        ALTER TABLE posts ADD COLUMN encryption_iv TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='is_encrypted') THEN
        ALTER TABLE posts ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='views_count') THEN
        ALTER TABLE posts ADD COLUMN views_count INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='is_repost') THEN
        ALTER TABLE posts ADD COLUMN is_repost BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='original_post_id') THEN
        ALTER TABLE posts ADD COLUMN original_post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='quote_text') THEN
        ALTER TABLE posts ADD COLUMN quote_text TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='comments_enabled') THEN
        ALTER TABLE posts ADD COLUMN comments_enabled BOOLEAN DEFAULT TRUE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='pinned_comment_id') THEN
        ALTER TABLE posts ADD COLUMN pinned_comment_id INTEGER;
    END IF;
END $$;

-- ============================================================
-- MEDIA DE PUBLICACIONES (Carrusel de imágenes/videos)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_media (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    media_type VARCHAR(20) NOT NULL, -- image, video
    media_url TEXT NOT NULL,
    encrypted_url TEXT, -- URL encriptada en Cloudinary
    encryption_key TEXT,
    encryption_iv TEXT,
    thumbnail_url TEXT, -- Miniatura para videos
    media_order INTEGER DEFAULT 0, -- Orden en carrusel
    width INTEGER,
    height INTEGER,
    duration_seconds INTEGER, -- Para videos
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_post_media_post_id ON post_media(post_id);

-- ============================================================
-- REACCIONES DE PUBLICACIONES (múltiples emojis)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_reactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) NOT NULL, -- heart, laugh, wow, sad, fire, clap
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_post_reactions_post_id ON post_reactions(post_id);
CREATE INDEX IF NOT EXISTS idx_post_reactions_type ON post_reactions(reaction_type);

-- ============================================================
-- COMENTARIOS DE PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS post_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id INTEGER REFERENCES post_comments(id) ON DELETE CASCADE, -- Para hilos
    content TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_user_id ON post_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_parent ON post_comments(parent_comment_id);

-- ============================================================
-- LIKES EN COMENTARIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS comment_likes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES post_comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, comment_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_likes_comment_id ON comment_likes(comment_id);

-- ============================================================
-- HASHTAGS
-- ============================================================
CREATE TABLE IF NOT EXISTS hashtags (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(100) UNIQUE NOT NULL,
    posts_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hashtags_tag ON hashtags(tag);
CREATE INDEX IF NOT EXISTS idx_hashtags_count ON hashtags(posts_count DESC);

-- ============================================================
-- RELACIÓN POSTS-HASHTAGS
-- ============================================================
CREATE TABLE IF NOT EXISTS post_hashtags (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, hashtag_id)
);

CREATE INDEX IF NOT EXISTS idx_post_hashtags_post ON post_hashtags(post_id);
CREATE INDEX IF NOT EXISTS idx_post_hashtags_hashtag ON post_hashtags(hashtag_id);

-- ============================================================
-- MENCIONES EN PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS post_mentions (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    mentioned_user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, mentioned_user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_mentions_post ON post_mentions(post_id);
CREATE INDEX IF NOT EXISTS idx_post_mentions_user ON post_mentions(mentioned_user_id);

-- ============================================================
-- MENCIONES EN COMENTARIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS comment_mentions (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER REFERENCES post_comments(id) ON DELETE CASCADE,
    mentioned_user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(comment_id, mentioned_user_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_mentions_comment ON comment_mentions(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_mentions_user ON comment_mentions(mentioned_user_id);

-- ============================================================
-- PUBLICACIONES GUARDADAS (Favoritos)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_saves (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_post_saves_user ON post_saves(user_id);
CREATE INDEX IF NOT EXISTS idx_post_saves_post ON post_saves(post_id);

-- ============================================================
-- VISTAS DE PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS post_views (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_views_post ON post_views(post_id);
CREATE INDEX IF NOT EXISTS idx_post_views_user ON post_views(user_id);

-- ============================================================
-- HISTORIAS (24 horas)
-- ============================================================
CREATE TABLE IF NOT EXISTS stories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    media_type VARCHAR(20) NOT NULL, -- image, video
    media_url TEXT NOT NULL,
    encrypted_url TEXT,
    encryption_key TEXT,
    encryption_iv TEXT,
    thumbnail_url TEXT,
    duration_seconds INTEGER DEFAULT 15,
    views_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stories_user ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at);
CREATE INDEX IF NOT EXISTS idx_stories_active ON stories(is_active, expires_at);

-- ============================================================
-- VISTAS DE HISTORIAS
-- ============================================================
CREATE TABLE IF NOT EXISTS story_views (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id) ON DELETE CASCADE,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_story_views_story ON story_views(story_id);
CREATE INDEX IF NOT EXISTS idx_story_views_user ON story_views(user_id);

-- ============================================================
-- USUARIOS BLOQUEADOS
-- ============================================================
CREATE TABLE IF NOT EXISTS user_blocks (
    id SERIAL PRIMARY KEY,
    blocker_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    blocked_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blocker_id, blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_user_blocks_blocker ON user_blocks(blocker_id);
CREATE INDEX IF NOT EXISTS idx_user_blocks_blocked ON user_blocks(blocked_id);

-- ============================================================
-- REPORTES DE CONTENIDO
-- ============================================================
CREATE TABLE IF NOT EXISTS content_reports (
    id SERIAL PRIMARY KEY,
    reporter_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL, -- post, comment, story, user
    content_id INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL, -- spam, harassment, inappropriate, violence, other
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, reviewed, resolved, dismissed
    admin_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON content_reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_type ON content_reports(content_type);
CREATE INDEX IF NOT EXISTS idx_reports_created ON content_reports(created_at DESC);

-- ============================================================
-- NOTIFICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- like, comment, follow, mention, share, story_reply
    actor_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE, -- Quien generó la notificación
    reference_type VARCHAR(20), -- post, comment, story
    reference_id INTEGER,
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- ============================================================
-- COMPARTIDOS DE PUBLICACIONES
-- ============================================================
CREATE TABLE IF NOT EXISTS post_shares (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    share_type VARCHAR(20) DEFAULT 'repost', -- repost, quote, dm
    quote_text TEXT, -- Para citas
    recipient_id VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL, -- Para DM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_post_shares_user ON post_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_post_shares_post ON post_shares(post_id);

-- ============================================================
-- CLAVES DE ENCRIPTACIÓN (para gestión segura)
-- ============================================================
CREATE TABLE IF NOT EXISTS encryption_keys (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    key_type VARCHAR(20) NOT NULL, -- master, post, story
    encrypted_key TEXT NOT NULL,
    key_iv TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_encryption_keys_user ON encryption_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_encryption_keys_active ON encryption_keys(is_active);
"""

CREATE_VIRTUAL_NUMBERS_SQL = """
-- ============================================================
-- SISTEMA DE NUMEROS VIRTUALES
-- ============================================================

-- Tabla principal de ordenes de numeros virtuales
CREATE TABLE IF NOT EXISTS virtual_number_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(20) NOT NULL,  -- 'smspool' | 'legitsms'
    country_code VARCHAR(10) NOT NULL,
    country_name VARCHAR(100),
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(100),
    phone_number VARCHAR(50),
    provider_order_id VARCHAR(100),
    
    -- Precios
    cost_usd DECIMAL(10,4),           -- Precio original USD del proveedor
    cost_with_commission DECIMAL(10,4), -- Precio + comision
    bunkercoin_charged DECIMAL(10,2),   -- Lo que pago el usuario en BUNK3RCO1N
    
    -- SMS recibido
    sms_code TEXT,
    sms_full_text TEXT,
    
    -- Estado: pending, active, received, cancelled, expired, refunded
    status VARCHAR(20) DEFAULT 'pending',
    expires_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vn_orders_user ON virtual_number_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_vn_orders_status ON virtual_number_orders(status);
CREATE INDEX IF NOT EXISTS idx_vn_orders_created ON virtual_number_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vn_orders_provider ON virtual_number_orders(provider);

-- ============================================================
-- INVENTARIO DE NUMEROS MANUALES (Legit SMS)
-- ============================================================
CREATE TABLE IF NOT EXISTS virtual_number_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(20) DEFAULT 'legitsms',
    country_code VARCHAR(10) NOT NULL,
    country_name VARCHAR(100),
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(100),
    phone_number VARCHAR(50) NOT NULL,
    
    cost_usd DECIMAL(10,4),  -- Lo que costo al comprarlo
    is_available BOOLEAN DEFAULT TRUE,
    assigned_to_user VARCHAR(255),
    assigned_order_id UUID,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vn_inventory_available ON virtual_number_inventory(is_available);
CREATE INDEX IF NOT EXISTS idx_vn_inventory_provider ON virtual_number_inventory(provider);
CREATE INDEX IF NOT EXISTS idx_vn_inventory_country ON virtual_number_inventory(country_code);
CREATE INDEX IF NOT EXISTS idx_vn_inventory_service ON virtual_number_inventory(service_code);

-- ============================================================
-- CONFIGURACION DE NUMEROS VIRTUALES (Admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS virtual_number_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Valores iniciales de configuracion
INSERT INTO virtual_number_settings (setting_key, setting_value) VALUES
    ('commission_percent', '30'),
    ('smspool_enabled', 'true'),
    ('legitsms_enabled', 'true'),
    ('default_expiry_minutes', '20'),
    ('usd_to_bunkercoin_rate', '10')
ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================
-- ESTADISTICAS DE VENTAS DE NUMEROS VIRTUALES
-- ============================================================
CREATE TABLE IF NOT EXISTS virtual_number_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    provider VARCHAR(20) NOT NULL,
    orders_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    cancelled_count INTEGER DEFAULT 0,
    revenue_bunkercoin DECIMAL(12,2) DEFAULT 0,
    cost_usd DECIMAL(12,4) DEFAULT 0,
    profit_usd DECIMAL(12,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date, provider)
);

CREATE INDEX IF NOT EXISTS idx_vn_stats_date ON virtual_number_stats(stat_date DESC);
CREATE INDEX IF NOT EXISTS idx_vn_stats_provider ON virtual_number_stats(provider);
"""


CREATE_ADMIN_TABLES_SQL = """
-- ============================================================
-- SISTEMA DE ADMINISTRACION - TABLAS ADICIONALES
-- ============================================================

-- Tabla de IPs bloqueadas
CREATE TABLE IF NOT EXISTS blocked_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,
    blocked_by VARCHAR(255),
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_permanent BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(ip_address)
);

CREATE INDEX IF NOT EXISTS idx_blocked_ips_address ON blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_active ON blocked_ips(is_active);

-- Tabla de alertas de seguridad
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    metadata JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_alerts_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resolved ON security_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created ON security_alerts(created_at DESC);

-- Tabla de notas de admin sobre usuarios
CREATE TABLE IF NOT EXISTS admin_user_notes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_notes_user ON admin_user_notes(user_id);

-- Tabla de tickets de soporte
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'new',
    assigned_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_user ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON support_tickets(created_at DESC);

-- Tabla de mensajes de tickets
CREATE TABLE IF NOT EXISTS ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_id BIGINT,
    message TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id);

-- Tabla de plantillas de respuesta
CREATE TABLE IF NOT EXISTS response_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de FAQs
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    display_order INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT TRUE,
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);
CREATE INDEX IF NOT EXISTS idx_faqs_published ON faqs(is_published);
CREATE INDEX IF NOT EXISTS idx_faqs_order ON faqs(display_order);
"""

CREATE_MULTITOKEN_WALLET_SQL = """
-- ============================================================
-- SISTEMA DE WALLETS PERSONALES MULTI-TOKEN (Seccion 25)
-- ============================================================

-- Wallet personal permanente del usuario
CREATE TABLE IF NOT EXISTS user_wallets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    address VARCHAR(100) NOT NULL,
    encrypted_mnemonic TEXT NOT NULL,
    wallet_version VARCHAR(20) DEFAULT 'v4r2',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_wallets_user ON user_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_wallets_address ON user_wallets(address);

-- Balances por token (cache sincronizado con blockchain)
CREATE TABLE IF NOT EXISTS token_balances (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    token_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20),
    token_name VARCHAR(100),
    token_decimals INTEGER DEFAULT 9,
    token_icon_url TEXT,
    balance DECIMAL(30,9) DEFAULT 0,
    balance_usd DECIMAL(20,4) DEFAULT 0,
    is_main_token BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 999,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token_address)
);

CREATE INDEX IF NOT EXISTS idx_token_balances_user ON token_balances(user_id);
CREATE INDEX IF NOT EXISTS idx_token_balances_token ON token_balances(token_address);
CREATE INDEX IF NOT EXISTS idx_token_balances_main ON token_balances(is_main_token);

-- Historial de transacciones de tokens
CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    token_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20),
    tx_type VARCHAR(20) NOT NULL,
    amount DECIMAL(30,9) NOT NULL,
    fee_amount DECIMAL(30,9) DEFAULT 0,
    platform_fee DECIMAL(30,9) DEFAULT 0,
    tx_hash VARCHAR(100),
    from_address VARCHAR(100),
    to_address VARCHAR(100),
    internal_receiver_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_token_tx_user ON token_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_token_tx_token ON token_transactions(token_address);
CREATE INDEX IF NOT EXISTS idx_token_tx_type ON token_transactions(tx_type);
CREATE INDEX IF NOT EXISTS idx_token_tx_status ON token_transactions(status);
CREATE INDEX IF NOT EXISTS idx_token_tx_hash ON token_transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_token_tx_created ON token_transactions(created_at DESC);

-- Configuracion de comisiones de retiro (admin)
CREATE TABLE IF NOT EXISTS withdrawal_fees (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(100) UNIQUE NOT NULL,
    token_symbol VARCHAR(20),
    fee_type VARCHAR(10) DEFAULT 'percent',
    fee_value DECIMAL(10,4) DEFAULT 2.0,
    min_withdrawal DECIMAL(30,9) DEFAULT 0,
    max_withdrawal DECIMAL(30,9) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_withdrawal_fees_token ON withdrawal_fees(token_address);
CREATE INDEX IF NOT EXISTS idx_withdrawal_fees_active ON withdrawal_fees(is_active);

-- Configuraciones de tokens conocidos
INSERT INTO withdrawal_fees (token_address, token_symbol, fee_type, fee_value, min_withdrawal, is_active) VALUES
    ('native', 'TON', 'fixed', 0.05, 0.1, true),
    ('EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs', 'USDT', 'percent', 1.5, 1.0, true)
ON CONFLICT (token_address) DO NOTHING;
"""

CREATE_ADVANCED_ADMIN_TABLES_SQL = """
-- ============================================================
-- SISTEMA DE PUNTUACION DE RIESGO
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    risk_level VARCHAR(20) DEFAULT 'low',
    factors JSONB DEFAULT '{}',
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_risk_scores_user ON risk_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_level ON risk_scores(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_scores_score ON risk_scores(score DESC);

CREATE TABLE IF NOT EXISTS risk_score_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    old_score INTEGER,
    new_score INTEGER,
    old_level VARCHAR(20),
    new_level VARCHAR(20),
    reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_history_user ON risk_score_history(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_history_date ON risk_score_history(changed_at DESC);

-- ============================================================
-- CONFIGURACION DEL SISTEMA
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_public BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);

-- Configuraciones iniciales
INSERT INTO system_config (key, value, description, category, is_public) VALUES
    ('maintenance_mode', 'false', 'Modo mantenimiento activo', 'system', false),
    ('maintenance_message', 'Sistema en mantenimiento', 'Mensaje de mantenimiento', 'system', true),
    ('max_login_attempts', '5', 'Intentos maximos de login', 'security', false),
    ('session_timeout_hours', '24', 'Tiempo de expiracion de sesion', 'security', false),
    ('min_withdrawal_amount', '10', 'Monto minimo de retiro', 'wallet', true),
    ('max_withdrawal_amount', '10000', 'Monto maximo de retiro', 'wallet', true),
    ('withdrawal_fee_percent', '2', 'Comision de retiro en porcentaje', 'wallet', true),
    ('new_user_bonus', '0', 'Bonus para nuevos usuarios', 'rewards', true),
    ('referral_bonus', '5', 'Bonus por referido', 'rewards', true)
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- MENSAJES PRIVADOS
-- ============================================================
CREATE TABLE IF NOT EXISTS private_messages (
    id SERIAL PRIMARY KEY,
    sender_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    receiver_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pm_sender ON private_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_pm_receiver ON private_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_pm_created ON private_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pm_unread ON private_messages(receiver_id, is_read) WHERE is_read = FALSE;

-- ============================================================
-- DETECCION DE ANOMALIAS
-- ============================================================
CREATE TABLE IF NOT EXISTS anomaly_detections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    data JSONB DEFAULT '{}',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_user ON anomaly_detections(user_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_type ON anomaly_detections(anomaly_type);
CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON anomaly_detections(severity);
CREATE INDEX IF NOT EXISTS idx_anomaly_resolved ON anomaly_detections(is_resolved);
CREATE INDEX IF NOT EXISTS idx_anomaly_created ON anomaly_detections(created_at DESC);

-- ============================================================
-- CUENTAS RELACIONADAS (para detector de multi-cuentas)
-- ============================================================
CREATE TABLE IF NOT EXISTS related_accounts (
    id SERIAL PRIMARY KEY,
    user_id_1 VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    user_id_2 VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 0.00,
    evidence JSONB DEFAULT '{}',
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_false_positive BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    UNIQUE(user_id_1, user_id_2, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_related_user1 ON related_accounts(user_id_1);
CREATE INDEX IF NOT EXISTS idx_related_user2 ON related_accounts(user_id_2);
CREATE INDEX IF NOT EXISTS idx_related_type ON related_accounts(relation_type);
CREATE INDEX IF NOT EXISTS idx_related_confirmed ON related_accounts(is_confirmed);

-- ============================================================
-- SISTEMA DE WALLETS PERSONALES MULTI-TOKEN (Seccion 25)
-- ============================================================

-- Wallet personal permanente del usuario
CREATE TABLE IF NOT EXISTS user_wallets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(100) NOT NULL,
    encrypted_mnemonic TEXT NOT NULL,
    wallet_version VARCHAR(20) DEFAULT 'v4r2',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_wallets_user ON user_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_wallets_address ON user_wallets(address);

-- Balances por token (cache sincronizado con blockchain)
CREATE TABLE IF NOT EXISTS token_balances (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20),
    token_name VARCHAR(100),
    token_decimals INTEGER DEFAULT 9,
    token_icon_url TEXT,
    balance DECIMAL(30,9) DEFAULT 0,
    balance_usd DECIMAL(20,4) DEFAULT 0,
    is_main_token BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 999,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token_address)
);

CREATE INDEX IF NOT EXISTS idx_token_balances_user ON token_balances(user_id);
CREATE INDEX IF NOT EXISTS idx_token_balances_token ON token_balances(token_address);
CREATE INDEX IF NOT EXISTS idx_token_balances_main ON token_balances(is_main_token);

-- Historial de transacciones de tokens
CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20),
    tx_type VARCHAR(20) NOT NULL,
    amount DECIMAL(30,9) NOT NULL,
    fee_amount DECIMAL(30,9) DEFAULT 0,
    platform_fee DECIMAL(30,9) DEFAULT 0,
    tx_hash VARCHAR(100),
    from_address VARCHAR(100),
    to_address VARCHAR(100),
    internal_receiver_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_token_tx_user ON token_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_token_tx_token ON token_transactions(token_address);
CREATE INDEX IF NOT EXISTS idx_token_tx_type ON token_transactions(tx_type);
CREATE INDEX IF NOT EXISTS idx_token_tx_status ON token_transactions(status);
CREATE INDEX IF NOT EXISTS idx_token_tx_hash ON token_transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_token_tx_created ON token_transactions(created_at DESC);

-- Configuracion de comisiones de retiro (admin)
CREATE TABLE IF NOT EXISTS withdrawal_fees (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(100) UNIQUE NOT NULL,
    token_symbol VARCHAR(20),
    fee_type VARCHAR(10) DEFAULT 'percent',
    fee_value DECIMAL(10,4) DEFAULT 2.0,
    min_withdrawal DECIMAL(30,9) DEFAULT 0,
    max_withdrawal DECIMAL(30,9) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_withdrawal_fees_token ON withdrawal_fees(token_address);
CREATE INDEX IF NOT EXISTS idx_withdrawal_fees_active ON withdrawal_fees(is_active);

-- Configuraciones de tokens conocidos
INSERT INTO withdrawal_fees (token_address, token_symbol, fee_type, fee_value, min_withdrawal, is_active) VALUES
    ('native', 'TON', 'fixed', 0.05, 0.1, true),
    ('EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs', 'USDT', 'percent', 1.5, 1.0, true)
ON CONFLICT (token_address) DO NOTHING;
"""