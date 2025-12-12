# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App for comprehensive package tracking and shipment management. It offers a mobile-optimized, secure, and user-friendly experience for logistics, integrating an internal monetary system (BUNK3RCO1N) and social features, all authenticated via Telegram. The project aims to provide a robust solution for package management, notifications, and community engagement, leveraging the TON blockchain for its monetary system. The business vision includes market potential in the logistics and crypto sectors, with ambitions to become a leading platform for package tracking with integrated Web3 functionalities.

## User Preferences
- Language: Spanish (es)
- Framework: Flask + Vanilla JS
- Database: PostgreSQL
- UI Style: Neo-bank dark theme with Binance-style gold (#F0B90B) accents
- Design Reference: Binance/Revolut/N26 - professional, minimalist, no emojis (use SVG icons)

## System Architecture
The application features a Flask (Python) backend, a PostgreSQL database, and a vanilla JavaScript frontend. Telegram Web App API handles authentication. The UI/UX is mobile-optimized with an Instagram-inspired dark theme, a bottom navigation bar, a slide-up profile modal, and a sidebar menu.

**UI/UX Decisions:**
- Neo-bank dark theme with ultra-dark backgrounds (#0B0E11, #12161C, #1E2329) and gold accents (#F0B90B, #FCD535).
- Bottom navigation with SVG icons (Home, Marketplace, Wallet, Profile).
- Story rings, preload screens, primary buttons, toasts, loaders, and modals all use the gold theme.
- Sidebar elements use Lucide SVG icons.

**Technical Implementations:**
- **Frontend:** Vanilla JavaScript for dynamic interactions, CSS3 for styling, focusing on accessibility. Includes dynamic screen navigation, infinite scroll, pagination, and optimized media uploads.
- **Backend:** Flask for routing, APIs, business logic, with input validation, rate limiting, error handling, and production logging.
- **Database:** PostgreSQL with a comprehensive schema.
- **Deployment:** Optimized for Replit with Gunicorn, including cache control headers.
- **State Management:** Centralized client-side state management using a StateManager module with event-based pub/sub.
- **Request Management:** Robust API request handling with configurable timeouts, automatic retries with exponential backoff, and cancellation.
- **Performance:** Database connection pooling, memory leak prevention, and skeleton loaders.
- **Security:** Rate limiting, robust TON address validation, mandatory ADMIN_TOKEN in production, consistent XSS prevention, CSRF protection, and security headers. Demo mode is protected with TOTP 2FA.
- **BUNK3RCO1N (B3C) Integration:** Dedicated service layer for TON blockchain interaction, real-time pricing via STON.fi DEX API, TON/USD conversion via CoinGecko, and buy/sell/withdraw/deposit functionalities.
- **Unique Wallets for Purchases:** System generates unique, temporary TON wallets for each purchase using `tonsdk`, encrypting mnemonic phrases. Wallets expire if unused and consolidate funds to a hot wallet upon successful deposit verification.
- **Migration to Blueprints:** The project is undergoing a gradual migration from a monolithic `app.py` to a modular architecture using Flask Blueprints for `AUTH`, `BLOCKCHAIN`, `ADMIN`, and `USER` routes, supported by shared services and decorators.

**Feature Specifications:**
- **Package Tracking:** Management of tracking records, status history, and delivery estimations.
- **Telegram Integration:** Authentication, notifications, and owner-specific access controls.
- **Security System:** Multi-point security for wallet and device management (trusted devices, 2FA, lockout, activity logs).
- **Monetary System (BUNK3RCO1N):** Internal currency for in-app purchases, secured by TON payment verification and TonCenter API. Features include auto-registration of wallets, address validation, transaction history, and a debit system.
- **Social Features:** User profiles, posts, likes, follows, avatar uploads, and AES-256-GCM encrypted media publications via Cloudinary.
- **Marketplace:** Sections for products and dynamic bot management.
- **Admin Panel:** Comprehensive logging and auditing system, content moderation, and support system.

## External Dependencies
- **PostgreSQL:** Primary database.
- **Telegram Web App API:** User authentication and core Telegram integration.
- **Resend API:** Email notifications.
- **TonCenter API (v3):** TON blockchain transaction verification for BUNK3RCO1N.
- **ChangeNow API:** Cryptocurrency exchange functionalities.
- **Cloudinary:** Encrypted media storage for publications.
- **Cryptography (Python library):** AES-256-GCM encryption/decryption of media files.
- **SMSPool API:** Virtual phone numbers provisioning.
- **Legit SMS API:** Primary SMS provider with automatic fallback to SMSPool.
- **STON.fi DEX API:** Real-time B3C/TON pricing.
- **CoinGecko API:** TON/USD conversion.
- **TON Connect SDK:** For wallet connection and transaction signing.
- **tonsdk (Python library):** For generating unique TON wallets.

## Recent Changes (December 2025)

### Balance Total Multi-Token en USD/EUR - 12 Diciembre 2025
Nueva funcionalidad para mostrar el valor total de todos los activos del usuario (B3C, TON, USDT) calculado en USD o EUR.

**Archivos creados:**
- `tracking/price_service.py` - Servicio de precios usando CoinGecko API con cache de 120 segundos

**Nuevos endpoints:**
- `GET /api/wallet/total-balance?currency=usd|eur` - Calcula el valor total de activos
- `GET /api/wallet/prices` - Obtiene precios actuales de criptomonedas

**Funcionalidades:**
- Obtiene precios en tiempo real de TON, USDT, BTC, ETH desde CoinGecko
- Precio fijo de B3C: $0.10 USD
- Toggle USD/EUR en la UI con persistencia en localStorage
- Soporte completo para modo demo (sin autenticación de Telegram)
- Fallback a precios por defecto cuando la API falla

### Migration to Flask Blueprints - 10 Diciembre 2025
Migrated ~30+ endpoints from monolithic `app.py` to modular Flask Blueprints:

**Endpoints migrated to `routes/admin_routes.py`:**
- Wallet Pool: `/api/admin/wallets/hot`, `/api/admin/wallets/deposits`, `/api/admin/wallets/fill-pool`, `/api/admin/wallets/consolidate`, `/api/admin/wallets/pool-config`, `/api/admin/wallets/<id>/consolidate`
- Blockchain: `/api/admin/blockchain/history`
- Analytics: `/api/admin/analytics/users`, `/api/admin/analytics/usage`, `/api/admin/analytics/conversion`
- Support: `/api/admin/support/tickets`, `/api/admin/support/tickets/<id>`, `/api/admin/support/tickets/<id>/reply`, `/api/admin/support/templates`
- FAQ Admin: `/api/admin/faq` (CRUD)
- Mass Messages: `/api/admin/messages`, `/api/admin/messages/scheduled`, `/api/admin/messages/<id>/cancel`

**Endpoints migrated to `routes/user_routes.py`:**
- Public FAQ: `/api/faq`

**Files cleaned:**
- Removed ~1300 lines of duplicate endpoints from `app.py`
- Removed ~900 lines of duplicate endpoints from `routes/admin_routes.py`
- Removed duplicate `create_ton_payment` function from `routes/blockchain_routes.py`

**Current Blueprint Structure:**
- `auth_routes.py` - Authentication, 2FA, sessions
- `blockchain_routes.py` - TON payments, B3C purchases, wallet operations
- `admin_routes.py` - Admin panel, analytics, support, FAQ, messages
- `user_routes.py` - User profiles, social features, notifications, public FAQ
- `tracking_routes.py` - Package tracking
- `bots_routes.py` - Bot management
- `vn_routes.py` - Virtual numbers

### Limpieza de Codigo - 10 Diciembre 2025
Eliminacion masiva de codigo duplicado y comentado de app.py:

**Lineas eliminadas:** ~4,650 (app.py paso de 12,750 a 8,095 lineas)

**Codigo eliminado:**
- Endpoints BOTS duplicados (7 endpoints) - Ya en bots_routes.py
- Endpoints TON/Wallet duplicados (6 endpoints) - Ya en blockchain_routes.py
- ~50 endpoints comentados de admin logs/security/config
- ~20 endpoints comentados de notifications/messages
- ~15 endpoints comentados de publications/comments
- Funciones legacy sin ruta (_old_* functions)

**Endpoints que permanecen en app.py (173 rutas activas):**
- Paginas: `/`, `/admin`, `/virtual-numbers`
- Core: `/api/health`, `/api/validate`, `/static/tonconnect-manifest.json`
- Proxy: `/api/proxy`, `/api/mobile-screenshot`
- Interactive Browser: `/api/interactive-browser/*`
- Admin 2FA: `/api/admin/2fa/verify`
- Stories, Encryption, Cloudinary, Config endpoints