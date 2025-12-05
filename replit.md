# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App for comprehensive package tracking and shipment management. It offers a mobile-optimized, secure, and user-friendly experience for logistics, including an internal monetary system (BUNK3RCO1N) and social features, all integrated with Telegram authentication. The project aims to provide a robust solution for users to manage packages, receive notifications, and engage within a community, leveraging the TON blockchain for its monetary system.

## User Preferences
- Language: Spanish (es)
- Framework: Flask + Vanilla JS
- Database: PostgreSQL
- UI Style: Dark theme, Instagram-inspired design

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

## B3C Token Configuration (Current: TESTNET)

**Modo actual:** TESTNET - Sistema configurado para pruebas antes de producción.

**Variables de entorno configuradas:**
- `B3C_USE_TESTNET=true` - Usar red de prueba
- `B3C_NETWORK=testnet` - Indicador de red

**Variables pendientes de configurar (cuando se cree el token):**
- `B3C_TOKEN_ADDRESS` - Dirección del contrato Jetton
- `B3C_HOT_WALLET` - Wallet para operaciones
- `B3C_COMMISSION_WALLET` - Wallet para comisiones

**Endpoints B3C disponibles:**
- `GET /api/b3c/price` - Precio actual (simulado en testnet)
- `GET /api/b3c/balance` - Balance del usuario
- `GET /api/b3c/config` - Configuración del servicio
- `GET /api/b3c/network` - Estado de la red
- `GET /api/b3c/testnet/guide` - Guía de configuración testnet

**Documentación:** Ver `docs/GUIA_TESTNET_B3C.md` para instrucciones paso a paso.

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