# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App designed for comprehensive package tracking and shipment management. It provides a mobile-optimized, secure, and user-friendly experience for logistics, integrating an internal monetary system (BUNK3RCO1N) and social features, all authenticated via Telegram. The project aims to offer a robust solution for package management, notifications, and community engagement, leveraging the TON blockchain for its monetary system. The business vision includes market potential in the logistics and crypto sectors, with ambitions to become a leading platform for package tracking with integrated Web3 functionalities.

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
- Sidebar elements use Lucide SVG icons instead of emojis.

**Technical Implementations:**
- **Frontend:** Vanilla JavaScript for dynamic interactions, CSS3 for styling, focusing on accessibility. Includes dynamic screen navigation, infinite scroll, pagination, and optimized media uploads.
- **Backend:** Flask for routing, APIs, business logic, with input validation, rate limiting, error handling, and production logging.
- **Database:** PostgreSQL with a comprehensive schema.
- **Deployment:** Optimized for Replit with Gunicorn, including cache control headers.
- **State Management:** Centralized client-side state management using a StateManager module with event-based pub/sub.
- **Request Management:** Robust API request handling with configurable timeouts, automatic retries with exponential backoff, and cancellation.
- **Performance:** Database connection pooling, memory leak prevention, and skeleton loaders.
- **Security:** Rate limiting on critical endpoints, robust TON address validation, mandatory ADMIN_TOKEN in production, consistent XSS prevention via `html.escape()`, CSRF protection with `Origin/Referer` checks, and security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS). Demo mode is protected with TOTP 2FA (code displayed in server logs, valid for 60 seconds, session tokens expire after 1 hour).
- **BUNK3RCO1N (B3C) Integration:** Dedicated service layer for TON blockchain interaction, real-time pricing via STON.fi DEX API, TON/USD conversion via CoinGecko, and buy/sell/withdraw/deposit functionalities. The current implementation uses a fixed price for B3C (0.10 USD) without a DEX pool, where purchases are made with TON to the owner's wallet and B3C is issued, and sales/withdrawals involve returning B3C for TON (minus commission).
- **Unique Wallets for Purchases:** A system generates unique, temporary TON wallets for each purchase using `tonsdk`, encrypting mnemonic phrases with AES-256-CBC. These wallets expire if unused and consolidate funds to a hot wallet upon successful deposit verification.

**Feature Specifications:**
- **Package Tracking:** Management of tracking records, status history, and delivery estimations.
- **Telegram Integration:** Authentication, notifications, and owner-specific access controls.
- **Security System:** Multi-point security for wallet and device management (trusted devices, 2FA, lockout, activity logs).
- **Monetary System (BUNK3RCO1N):** Internal currency for in-app purchases, secured by TON payment verification and TonCenter API. Features include auto-registration of wallets, address validation, transaction history, and a debit system.
- **Social Features:** User profiles, posts, likes, follows, avatar uploads, and AES-256-GCM encrypted media publications via Cloudinary.
- **Marketplace:** Sections for products and dynamic bot management.
- **Admin Panel:** Comprehensive logging and auditing system for admin and security actions with filtering, pagination, and export capabilities. Content moderation endpoints for posts, stories, and hashtags. Support system with tickets management, FAQ administration, and mass messaging capabilities.

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

## Sistema de Gestion de Tareas (007.md)

El proyecto utiliza un sistema de gestion de tareas basado en agentes especializados:

**Comando:** `start 007.md`

| Comando | Agente | Rama Git | Archivos |
|---------|--------|----------|----------|
| 1 | Crear Tareas | - | Distribuye tareas al agente correcto |
| 2 | Backend-API | `feature/backend-api` | routes/auth_routes.py, app.py (init), tracking/*.py |
| 3 | Blockchain-Services | `feature/blockchain-services` | routes/blockchain_routes.py, wallet, b3c, encryption |
| 4 | Frontend-Admin | `feature/frontend-admin` | routes/admin_routes.py, admin.js, admin-utils.js |
| 5 | Frontend-User | `feature/frontend-user` | routes/user_routes.py, app.js, utils.js |

**Archivos de tareas:** `WORK/TAREAS_*.md`

**Estructura de Rutas (Blueprints):**
```
routes/
  __init__.py         - Definicion de blueprints
  admin_routes.py     - Endpoints /api/admin/* (Frontend-Admin)
  user_routes.py      - Endpoints /api/users/*, /api/publications/* (Frontend-User)
  blockchain_routes.py - Endpoints /api/b3c/*, /api/wallet/* (Blockchain-Services)
  auth_routes.py      - Endpoints /api/2fa/*, /api/auth/* (Backend-API)
```

**Archivos de Utilidades JS:**
```
static/js/
  shared-utils.js    - Utilidades compartidas (SOLO LECTURA)
  admin-utils.js     - Utilidades admin (Frontend-Admin)
  utils.js           - Utilidades usuario (Frontend-User)
```

**Flujo obligatorio:**
1. Conectarse a la rama correspondiente
2. Esperar confirmacion del usuario
3. Ejecutar tareas (prioridad: FASE 0.1 migracion de rutas)
4. Dar comandos git al finalizar cada tarea

---

## Recent Changes (December 2024)
- **Wallet Pool Optimizations:** Added rotation algorithm, low balance alerts, automated cleanup of old consolidated wallets, and pool maintenance routine.
- **Transaction Auditing:** Implemented `blockchain_audit_log` table with JSONB storage for comprehensive transaction tracking.
- **Transaction Limits:** Added `TransactionLimits` class enforcing daily withdrawal limits (100k B3C) and single transaction limits (50k B3C), properly filtering by completed/processing status.
- **Legit SMS Service:** Implemented `LegitSMSService` with automatic fallback to SMSPool when primary provider fails.
- **Security Improvements:** Enhanced 2FA for large withdrawals (>1000 B3C), address whitelisting, and rate limiting on withdrawal endpoints.
- **Encryption:** AES-256-GCM for media, AES-256-CBC with unique IVs for private keys. Master key warning for development mode.