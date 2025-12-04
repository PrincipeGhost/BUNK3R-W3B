# BUNK3R - Telegram Package Tracking System

## Overview
This is a Telegram Web App for managing package tracking and shipments. Built with Flask (Python) backend and vanilla JavaScript frontend, it provides a complete tracking management system with Telegram authentication.

## Project Structure
```
.
├── app.py                  # Main Flask application with routes and authentication
├── run.py                  # Production runner (runs on 0.0.0.0:5000)
├── init_db.py             # Database initialization script
├── requirements.txt       # Python dependencies
├── tracking/              # Core tracking module
│   ├── __init__.py
│   ├── database.py       # Database manager and operations
│   ├── models.py         # Data models and schema definitions
│   └── email_service.py  # Email notification service (Resend API)
├── templates/            # HTML templates
│   ├── index.html       # Main SPA template
│   └── access_denied.html
└── static/              # Static assets
    ├── css/styles.css   # Application styles
    ├── js/app.js        # Frontend JavaScript
    ├── images/          # Logo and images
    └── uploads/         # User uploaded files
        └── avatars/     # Profile photos
```

## Features
- 📦 Package tracking management
- 🔐 Telegram Web App authentication
- 📊 Status tracking and history
- 📧 Email notifications via Resend
- 🚚 Route generation and delivery estimation
- 📱 Mobile-optimized interface

## Technology Stack
- **Backend**: Flask 3.0.0, Python 3.11
- **Database**: PostgreSQL (via DATABASE_URL)
- **Frontend**: Vanilla JavaScript, CSS3
- **Authentication**: Telegram Web App API
- **Deployment**: Gunicorn (production)

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `OWNER_TELEGRAM_ID` - Telegram user ID of the owner

### Optional
- `CHANNEL_ID` - Telegram channel ID for notifications
- `ADMIN_TOKEN` - Secret key for sessions (auto-generated if not set)
- `RESEND_API_KEY` - API key for email service

## Database
The application uses PostgreSQL with the following tables:

### Tracking Tables
- `trackings` - Main tracking records
- `shipping_routes` - Predefined routes and delivery estimates
- `status_history` - Tracking status change history

### Social/Marketplace Tables
- `users` - User profiles (extended with social fields: level, credits, bio, etc.)
- `posts` - User publications (images, videos, text)
- `follows` - Follower/following relationships
- `products` - Marketplace listings
- `user_bots` - User's active bots
- `achievements` - User badges and achievements
- `achievement_types` - Available achievement definitions
- `wallet_transactions` - Credit transactions history
- `shared_posts` - Reposted/shared content
- `post_likes` - Like tracking for posts

Database is initialized automatically on first run via `init_db.py`.

## Development

### Running Locally
The application runs on `0.0.0.0:5000` with cache control headers disabled for development.

```bash
python run.py
```

### Database Operations
```bash
# Initialize/reset database
python init_db.py
```

## Deployment
Configured for Replit deployment with:
- Frontend on port 5000 (webview)
- Cache control headers for iframe compatibility
- Production-ready Gunicorn setup

## Recent Changes
- 2024-12-04: SISTEMA DE SEGURIDAD DE 17 PUNTOS PARA BUNK3RCO1N
  - **Sistema Completo de Seguridad para Wallet y Dispositivos:**
  
  1. Bloqueo de BUNK3RCO1N en dispositivos no confiables
  2. Validacion de wallet unica por usuario (primera wallet registrada)
  3. Gestion de dispositivos de confianza (maximo 2)
  4. Integracion con sistema 2FA existente
  5. Controles de admin para monitoreo de usuarios/dispositivos
  6. Notificaciones de Telegram para eventos de seguridad
  7. Pantalla de bloqueo para dispositivos no confiables
  8. Pantalla de wallet incorrecta con intentos restantes
  9. Pantalla de cuenta bloqueada con temporizador
  10. Modal de agregar dispositivo de confianza (3 pasos)
  11. Widget de estado de seguridad con score
  12. Listado y gestion de dispositivos en perfil
  13. Sistema de wallet de respaldo para recuperacion
  14. Historial de actividad de seguridad
  15. Sistema de bloqueo por intentos fallidos (3 intentos = 15 min bloqueo)
  16. Expiracion automatica de dispositivos (60 dias)
  17. Cerrar sesion en todos los dispositivos
  
  - **Nuevas tablas en base de datos:**
    - `trusted_devices` - Dispositivos de confianza por usuario
    - `wallet_failed_attempts` - Intentos fallidos de wallet
    - `user_lockouts` - Bloqueos temporales de cuenta
    - `security_activity_log` - Historial de actividad de seguridad
    - `security_alerts` - Alertas de seguridad para admin
  
  - **Nuevos endpoints de seguridad:**
    - /api/security/wallet/validate - Validar wallet conectada
    - /api/security/wallet/primary - Obtener wallet primaria
    - /api/security/wallet/backup - Registrar wallet de respaldo
    - /api/security/status - Estado de seguridad completo
    - /api/security/devices - Lista de dispositivos
    - /api/security/devices/check - Verificar dispositivo actual
    - /api/security/devices/add - Agregar dispositivo de confianza
    - /api/security/devices/remove - Eliminar dispositivo
    - /api/security/devices/remove-all - Cerrar sesion en todos
    - /api/security/activity - Historial de actividad
    - /api/security/lockout/check - Verificar bloqueo
  
  - **Endpoints de admin:**
    - /api/admin/security/users - Listar usuarios con dispositivos
    - /api/admin/security/user/<id>/devices - Dispositivos de usuario
    - /api/admin/security/user/<id>/device/remove - Eliminar dispositivo
    - /api/admin/security/alerts - Alertas de seguridad
    - /api/admin/security/alerts/<id>/resolve - Resolver alerta
    - /api/admin/security/statistics - Estadisticas de seguridad
    - /api/admin/security/user/<id>/activity - Actividad de usuario

- 2024-12-04: Implemented Trusted Devices System for Wallet Synchronization
  - New database table `trusted_devices` for storing trusted device information per user
  - API endpoints: /api/devices/trusted (list), /check (verify), /add, /remove
  - Device fingerprinting using browser characteristics (user agent, screen size, timezone, etc.)
  - Automatic device type detection (Telegram Android/iOS/Desktop, mobile browsers, desktop browsers)
  - UI: Banner notification when wallet is synced but device is not trusted
  - Modal for adding device as trusted with device info preview
  - Security: Payment operations blocked on untrusted devices even if wallet is connected
  - This allows users to sync their wallet across devices while maintaining security

- 2024-12-04: Renombrado de creditos a BUNK3RCO1N
  - La sección "Billetera" ahora se llama "BUNK3RCO1N"
  - Todos los "creditos" en la UI ahora son "BUNK3RCO1N"
  - Actualizado en: templates/index.html, static/js/app.js, app.py
  - El sistema de moneda interna ahora usa el nombre BUNK3RCO1N para distinguirse del dinero real
  - Los precios de bots y recargas ahora se muestran en BUNK3RCO1N

- 2024-12-04: Implemented secure TON payment verification system
  - New payment flow: Create pending payment -> User sends TON with comment -> Verify on blockchain
  - Server-side credit calculation (no client-controlled credits)
  - TonCenter API v3 integration for blockchain verification
  - Payment modal with wallet address and unique comment to identify transactions
  - Endpoints: /api/ton/payment/create, /verify, /status
  - Rate table: 1 TON = 10 credits (with volume bonuses)
  - Prevents fraud by verifying actual blockchain transactions before crediting

- 2024-12-04: Fixed Telegram Wallet synchronization issues
  - Added missing `getAuthHeaders()` function in App object
  - Fixed wallet address conversion to use non-bounceable format (UQ...) matching Telegram Wallet
  - Previously used bounceable format (EQ...) which caused address mismatch
  - Wallet now correctly syncs across devices using proper authentication headers

- 2024-12-04: Integrated ChangeNow cryptocurrency exchange
  - Full Exchange section accessible via sidebar menu
  - Backend API endpoints for currency listing, rate estimation, and transaction creation
  - Currency modal with search functionality for selecting tokens
  - Real-time rate estimation when entering amounts
  - Transaction creation with deposit address display
  - Copy-to-clipboard functionality for deposit addresses
  - Uses CHANGENOW_API_KEY secret for API authentication
  - API endpoints: /api/exchange/currencies, /min-amount, /estimate, /create, /status/<tx_id>

- 2024-12-04: Bot renamed from "Tracking Manager" to "Trackings Correos"
  - Updated bot name across database, templates, and code
  - Removed marketplace demo products and available bots (owner-only access)

- 2024-12-04: Improved demo mode authentication
  - Demo mode now works in development environments
  - Added try/catch error handling in completeLogin() for better stability

- 2024-12-04: Added custom loading screen for cold starts
  - Custom branded preload overlay with BUNK3R logo and animated spinner
  - Inline CSS for instant rendering (no external dependencies)
  - Smooth fade-out transition when app is ready
  - Added /api/health endpoint for server health checks (useful for external monitoring)
  - Loading screen shows immediately before CSS/JS files load

- 2024-12-04: Implemented dynamic bot validation system
  - Bots are now loaded dynamically per user (only shows bots the user owns/purchased)
  - Added bot_types table with owner_only flag for exclusive bots
  - Tracking Manager bot is automatically assigned to the owner on login
  - Users can only see and purchase bots available to their permission level
  - Added purchase validation (credits check, duplicate prevention)
  - API endpoints: /api/bots/my, /api/bots/available, /api/bots/purchase, /api/bots/{id}/remove

- 2024-12-03: Added profile avatar upload functionality
  - Users can now upload their own profile photo by clicking on the avatar area
  - Backend endpoint `/api/users/me/avatar` handles file uploads (PNG, JPG, JPEG, GIF, WEBP)
  - Images are stored in `static/uploads/avatars/` with unique filenames
  - Avatar persists across page reloads via database storage
  - Maximum file size: 5MB
  - Avatar automatically updates in profile page, sidebar, and bottom navigation

- 2024-12-03: Security hardening for social features
  - Demo mode only allowed when BOT_TOKEN is not configured (development only)
  - Production environments require valid Telegram authentication
  - Separate `require_telegram_user` decorator for social features (allows any authenticated user)
  - Original `require_telegram_auth` decorator requires owner-level access

- 2024-12-03: Implemented social features - Posts and Followers system
  - Added POST/GET/DELETE endpoints for posts (/api/posts)
  - Added like/unlike functionality for posts (/api/posts/<id>/like)
  - Added follow/unfollow endpoints (/api/users/<id>/follow)
  - Added followers/following list endpoints
  - Added user profile endpoints with stats (/api/users/<id>)
  - Database functions for social features in tracking/database.py

- 2024-12-03: Converted profile from modal to integrated page
  - Profile is now a page-screen like other sections (Marketplace, Bots, Wallet)
  - Both top and bottom navigation bars remain visible when viewing profile
  - Instagram-style layout maintained: avatar, stats, bio, professional panel, gallery grid
  - Telegram back button properly handles profile screen navigation

- 2024-12-03: Added new pages for Marketplace, Bots, and Wallet
  - Redesigned bottom navigation: Home, Marketplace, Bots, BUNK3RCO1N, Perfil (Profile)
  - Created Marketplace page with product categories and item grid (prices in BUNK3RCO1N)
  - Created Bots page with active user bots and available bots for purchase
  - Created BUNK3RCO1N page with balance, transaction history, and top-up options
  - Fixed Telegram back button handler for all new pages
  - Updated navigation system with showPage() function

- 2024-12-03: Added bottom navigation bar and profile modal
  - Instagram-style profile modal with avatar, stats, bio, and photo gallery
  - Moved user profile from top bar to sidebar menu
  - Added slide-up animation for profile modal
  
- 2024-12-03: Initial Replit setup and configuration
  - Installed Python 3.11 and dependencies
  - Created PostgreSQL database
  - Configured workflows and deployment
  - Added cache control headers for Replit iframe

## UI Components
- **Bottom Navigation**: Fixed navigation bar at the bottom with SVG icons
- **Profile Modal**: Instagram-style slide-up modal showing user stats and profile info
- **Sidebar Menu**: Hamburger menu with navigation options and user profile at bottom

## User Preferences
- Language: Spanish (es)
- Framework: Flask + Vanilla JS
- Database: PostgreSQL
- UI Style: Dark theme, Instagram-inspired design
