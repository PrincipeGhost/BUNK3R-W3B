# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App for comprehensive package tracking and shipment management. It offers a mobile-optimized, secure, and user-friendly experience for logistics, including an internal monetary system (BUNK3RCO1N) and social features, all integrated with Telegram authentication. The project aims to provide a robust solution for users to manage packages, receive notifications, and engage within a community, leveraging the TON blockchain for its monetary system.

## User Preferences
- Language: Spanish (es)
- Framework: Flask + Vanilla JS
- Database: PostgreSQL
- UI Style: Neo-bank dark theme with Binance-style gold (#F0B90B) accents
- Design Reference: Binance/Revolut/N26 - professional, minimalist, no emojis (use SVG icons)

## System Architecture
The application is built with a Flask (Python) backend, a PostgreSQL database, and a vanilla JavaScript frontend. Telegram Web App API is used for authentication. The UI/UX is mobile-optimized with an Instagram-inspired dark theme, featuring a bottom navigation bar, a slide-up profile modal, and a sidebar menu.

**Key Features:**
- **Package Tracking:** Management of tracking records, status history, and delivery estimations.
- **Telegram Integration:** Authentication via Telegram Web App API, notifications, and owner-specific access controls.
- **Security System:** Multi-point security for wallet and device management, including trusted devices, 2FA, lockout mechanisms, and activity logs.
- **Monetary System (BUNK3RCO1N):** Internal currency for in-app purchases, secured by TON payment verification and TonCenter API integration. Features include auto-registration of wallets, address validation, transaction history, and a debit system.
- **Social Features:** User profiles, posts, likes, follows, avatar uploads, and AES-256-GCM encrypted media publications via Cloudinary.
- **Marketplace:** Sections for products and dynamic bot management with activation toggles and configuration panels.
- **External Exchange:** Integration with ChangeNow for cryptocurrency swapping.
- **Virtual Numbers System:** Purchase phone numbers for SMS verification using BUNK3RCO1N, integrated with SMSPool API.

**Technical Implementations:**
- **Frontend:** Vanilla JavaScript for dynamic interactions, CSS3 for styling, with a focus on accessibility (A11y). Includes dynamic screen navigation, infinite scroll, pagination, and optimized media uploads.
- **Backend:** Flask for routing, APIs, and business logic, with input validation, rate limiting, error handling, and production logging.
- **Database Schema:** PostgreSQL with comprehensive tables for all application features.
- **Deployment:** Optimized for Replit with Gunicorn, including cache control headers for iframe compatibility.
- **State Management:** Centralized client-side state management using a StateManager module with event-based pub/sub.
- **Request Management:** Robust API request handling with configurable timeouts, automatic retries with exponential backoff, and cancellation.
- **Performance:** Database connection pooling, memory leak prevention mechanisms, and smart skeleton loaders for improved user experience.
- **BUNK3RCO1N (B3C) Integration:** Dedicated service layer for TON blockchain interaction, real-time pricing via STON.fi DEX API, TON/USD conversion via CoinGecko, buy/sell/withdraw/deposit functionalities, and commission tracking.

## B3C Token Configuration (Current: MAINNET - Fixed Price)

**Modo actual:** MAINNET - Token real con precio fijo controlado (sin pool DEX).

**Token creado:**
- **Address:** `EQDQI0-UQ56AuBGTWNDgLPE6naQYFvrZTcRt-GI7jx6dwSmM`
- **Symbol:** B3C (BUNK3RCO1N)
- **Decimals:** 9
- **Supply:** 1,000,000,000

**Variables de entorno configuradas:**
- `B3C_USE_TESTNET=false` - Usar mainnet
- `B3C_NETWORK=mainnet` - Indicador de red
- `B3C_TOKEN_ADDRESS` - Dirección del contrato Jetton
- `B3C_HOT_WALLET` - Wallet para operaciones
- `B3C_COMMISSION_WALLET` - Wallet para comisiones (5%)
- `B3C_USE_FIXED_PRICE=true` - Usar precio fijo (sin DEX)
- `B3C_FIXED_PRICE_USD=0.10` - Precio fijo: $0.10 USD por B3C

**Sistema de precio fijo:**
El usuario decidió NO usar pool de liquidez (DEX). En su lugar:
1. **Compras en app:** Usuario paga TON -> Va a wallet del propietario -> Propietario envía B3C
2. **Ventas/Retiros:** Usuario devuelve B3C -> Recibe TON (menos 5% comisión)
3. **Precio controlado:** Fijado por el propietario (inicialmente $0.10 USD)
4. **Sin riesgo de manipulación:** No hay pool que pueda ser atacado

**Endpoints B3C disponibles:**
- `GET /api/b3c/price` - Precio actual (fijo: $0.10 USD)
- `GET /api/b3c/balance` - Balance del usuario
- `GET /api/b3c/config` - Configuración del servicio
- `GET /api/b3c/network` - Estado de la red
- `POST /api/b3c/transfer` - Transferir B3C entre usuarios (P2P)
- `POST /api/b3c/admin/price` - Actualizar precio fijo (admin)

## Cambios Recientes (5 Diciembre 2025)

### SECCIÓN 17 - Pagos TON Connect (COMPLETADO)
- Corregido error TON_CONNECT_SDK_ERROR en payload de transacciones
- Eliminado payload problemático de buildTextCommentPayload()
- Las transacciones ahora envían solo dirección y monto (formato válido para SDK)

### SECCIÓN 18 - Números Virtuales (COMPLETADO)  
- Corregido botón "Atrás" que cerraba toda la mini app
- Ahora navega correctamente a la pantalla principal

### SECCIÓN 19 - Transferencias P2P (COMPLETADO)
- Nuevo endpoint POST /api/b3c/transfer para transferencias entre usuarios
- Tabla b3c_transfers para rastrear transferencias
- Modal de transferencia con búsqueda de usuarios
- Transacciones atómicas con nivel de aislamiento SERIALIZABLE
- Bloqueo de filas con FOR UPDATE para prevenir doble gasto

### SECCIÓN 20 - Conexión de Wallet y Sincronización (COMPLETADO)
- Actualizado tonconnect-manifest.json con URL dinámica del entorno
- Nueva sección de UI de Wallet TON en pantalla de wallet:
  - Estado de conexión (conectada/desconectada)
  - Botón para conectar wallet vía TON Connect
  - Visualización de dirección con botón de copiar
  - Botones para cambiar/desconectar wallet
- Verificada sincronización de wallet con backend (saveWalletToBackend, loadSavedWallet)
- Integración con sistema de dispositivos confiables funcionando
- TON Connect SDK se inicializa correctamente con manejo de errores

### SECCIÓN 21 - Neo-Bank UI Redesign (COMPLETADO)
Rediseño completo del UI al estilo neo-bank profesional (Binance/Revolut/N26):

**Cambios realizados:**
- Paleta de colores actualizada a Binance-style:
  - Fondos ultra-oscuros: #0B0E11, #12161C, #1E2329
  - Acento primario: #F0B90B (gold)
  - Acento secundario: #FCD535 (light gold)
  - Colores de estado: #02C076 (success), #F6465D (danger)
- Bottom navigation con 4 iconos SVG (Home, Marketplace, Wallet, Profile)
- Indicador de pestaña activa en dorado con línea superior
- Story ring actualizado a gradiente dorado
- Preload screen con colores gold
- Botones primarios con fondo gold y texto oscuro
- Toasts, loaders y modals actualizados
- Token badge y wallet connect button con estilo gold
- Formularios e inputs con focus state dorado
- Sidebar emojis reemplazados con iconos SVG Lucide
- Todos los colores azules (#4299e1, #63b3ed, rgba(66,153,225)) reemplazados por gold
- Gradientes actualizados a tonos dorados

### SECCIÓN 22 - Auditoría de Seguridad (EN PROGRESO)
Mejoras de seguridad implementadas:

**Cambios realizados (5 Diciembre 2025):**
- Rate limiting agregado a endpoints críticos:
  - `/api/b3c/price` - price_check (60/min)
  - `/api/b3c/calculate/buy` y `/sell` - calculate (30/min)
  - `/api/b3c/balance` - balance_check (60/min)
  - `/api/exchange/currencies` - exchange (30/min)
- Validación robusta de direcciones TON usando `validate_ton_address()`
- ADMIN_TOKEN obligatorio en producción (fail-fast si no está configurado)
- Confirmado que escapeHtml() se usa consistentemente para prevenir XSS
- Verificado SERIALIZABLE isolation level en transferencias P2P

### SECCIÓN 24 - Sistema de Wallets Únicas por Compra (COMPLETADO)
Sistema de wallets temporales para identificación 100% segura de pagos B3C:

**Arquitectura:**
- Cada compra genera una wallet TON única usando biblioteca `tonsdk`
- Wallet v4r2 con mnemonic de 24 palabras como private key
- Private keys encriptados con AES-256-CBC con IV único por wallet
- Wallets expiran después de 30 minutos sin depósito

**Componentes:**
- **Tablas DB:** `deposit_wallets`, `wallet_pool_config`
- **Servicio:** `WalletPoolService` en `tracking/wallet_pool_service.py`
- **Endpoints:**
  - `POST /api/b3c/buy/create` - Genera wallet única para depósito
  - `POST /api/b3c/buy/:id/verify` - Verifica depósito y acredita B3C
  - `GET /api/b3c/wallet-pool/stats` - Estadísticas del pool (admin)
  - `POST /api/b3c/wallet-pool/fill` - Rellenar pool (admin)
  - `POST /api/b3c/wallet-pool/consolidate` - Consolidar fondos (admin)

**Flujo de compra:**
1. Usuario solicita compra -> Sistema asigna wallet única
2. Frontend usa `depositAddress` en TON Connect (no hotWallet)
3. Usuario confirma transacción en wallet
4. Backend verifica depósito en wallet única
5. Si válido: acredita B3C y consolida fondos a hot wallet

**Variables de entorno requeridas:**
- `WALLET_MASTER_KEY` - Clave para encriptar/desencriptar private keys (OBLIGATORIO en producción)

**Última actualización:** 5 Diciembre 2025

## External Dependencies
- **PostgreSQL:** Primary database.
- **Telegram Web App API:** User authentication and core Telegram integration.
- **Resend API:** Email notifications.
- **TonCenter API (v3):** TON blockchain transaction verification for BUNK3RCO1N.
- **ChangeNow API:** Cryptocurrency exchange functionalities.
- **Cloudinary:** Encrypted media storage for publications.
- **Cryptography (Python):** AES-256-GCM encryption/decryption of media files.
- **SMSPool API:** Virtual phone numbers provisioning.
- **STON.fi DEX API:** Real-time B3C/TON pricing.
- **CoinGecko API:** TON/USD conversion.