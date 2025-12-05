# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App designed for comprehensive package tracking and shipment management. It provides a robust system for users to track packages, manage shipments, and receive notifications, all integrated seamlessly with Telegram authentication. The project aims to offer a mobile-optimized, secure, and user-friendly experience for managing logistics, including an internal monetary system (BUNK3RCO1N) and social features.

## User Preferences
- Language: Spanish (es)
- Framework: Flask + Vanilla JS
- Database: PostgreSQL
- UI Style: Dark theme, Instagram-inspired design

## System Architecture
The application uses a Flask (Python) backend with a PostgreSQL database and a vanilla JavaScript frontend. Telegram Web App API handles authentication. The UI/UX is mobile-optimized with an Instagram-inspired dark theme, featuring a bottom navigation bar, a slide-up profile modal, and a sidebar menu.

**Key Features:**
- **Package Tracking:** Management of tracking records, status history, and delivery estimations.
- **Telegram Integration:** Authentication via Telegram Web App API, Telegram notifications, and owner-specific access controls.
- **Security System:** A multi-point security system for wallet and device management including trusted devices, 2FA integration, lockout mechanisms, security activity logs, and administrative monitoring.
- **Monetary System (BUNK3RCO1N):** Internal currency for in-app purchases, supported by a secure TON payment verification system and integration with TonCenter API. It includes features like auto-registration of primary wallets, TON wallet address validation, transaction history, and a debit system.
- **Social Features:** User profiles, posts, likes, follows, avatar uploads, and an encrypted publications system with AES-256-GCM encryption for all media uploaded to Cloudinary.
- **Marketplace:** Sections for products and dynamic bot management.
- **External Exchange:** Integration with ChangeNow for cryptocurrency swapping.
- **Virtual Numbers System:** Purchase phone numbers for SMS verification using BUNK3RCO1N, integrated with SMSPool API.

**Technical Implementations:**
- **Frontend:** Vanilla JavaScript for dynamic interactions, CSS3 for styling, with a focus on accessibility (A11y) improvements like ARIA attributes, focus management, and screen reader announcements.
- **Backend:** Flask for routing, API endpoints, and business logic. Includes robust input validation, rate limiting, error handling, and production logging.
- **Database Schema:** PostgreSQL with comprehensive tables for all application features including tracking, users, social interactions, wallets, and security data.
- **Deployment:** Optimized for Replit with Gunicorn, with specific cache control headers for iframe compatibility.
- **State Management:** Centralized client-side state management using a StateManager module with event-based pub/sub, pending operations tracking, and session management.
- **Request Management:** Robust API request handling with configurable timeouts, automatic retries with exponential backoff, and request cancellation.
- **Performance:** Implemented infinite scroll for feeds, comment pagination, and optimized image/video uploads to Cloudinary with pre-encryption validation and detailed progress indicators.
- **User Experience:** Dynamic screen navigation system with smooth page transitions, profile stats, followers/following modals, edit profile functionality, and a recharge success animation.

## External Dependencies
- **PostgreSQL:** Primary database.
- **Telegram Web App API:** User authentication and core Telegram integration.
- **Resend API:** Email notifications.
- **TonCenter API (v3):** TON blockchain transaction verification for BUNK3RCO1N.
- **ChangeNow API:** Cryptocurrency exchange functionalities.
- **Cloudinary:** Encrypted media storage for publications.
- **Cryptography (Python):** AES-256-GCM encryption/decryption of media files.
- **SMSPool API:** Virtual phone numbers provisioning.

## Recent Changes (December 2025)

### Completed Priority Features:
1. **Notifications System** - Full backend and frontend implementation for auto-generated notifications (likes, follows, comments, reactions, wallet transactions) with notification preferences and badge count.

2. **Wallet Date Filter** - Added date range filter UI (today/week/month/all) to transaction history with backend support for `from_date` parameter.

3. **Explore Screen** - New hashtag search with trending hashtags display, grid results, and sanitized rendering for XSS protection.

4. **Security Improvements**:
   - Added `escapeHtmlForExplore()`, `sanitizeHashtag()`, `sanitizeUrl()` functions for XSS prevention
   - URL validation for media content in Explore
   - Safe hashtag rendering with proper encoding

5. **Verified Existing Features**:
   - Stories (viewer with time remaining, delete, "seen by" list)
   - Profile grid (Instagram-style 3-column layout)
   - Comments (nested replies)
   - Memory leak cleanup functions in both app.js and publications.js

6. **Bug Fixes**:
   - Changed `count_user_publications` to query 'posts' table instead of non-existent 'encrypted_publications'
   - Fixed notification creation for wallet credits and bot purchases

### Performance Optimizations (December 5, 2025):

7. **Database Connection Pooling**:
   - Implemented `ThreadedConnectionPool` with min=2, max=10 connections
   - Added `PooledConnection` wrapper for automatic connection return
   - Fixed connection leak in `return_connection()` method

8. **Memory Leak Prevention**:
   - `cleanupCurrentScreen()` function clears timeouts/intervals on navigation
   - `RequestManager.cancel()` integrated in `loadFeed()` to prevent race conditions
   - Proper cleanup of visibility handlers and polling intervals

9. **Code Unification**:
   - Consolidated duplicate `getDeviceIcon()` functions:
     - `getDeviceIconEmoji(deviceType)` - returns emoji icons
     - `getDeviceIconSVG()` - returns SVG icons for device modal
   - `apiRequest()` in publications.js now supports `cancelKey` for request cancellation

10. **UI Improvements for Mobile**:
    - Modals now scrollable on small screens (max-height: 85vh)
    - Sticky modal header/footer on mobile devices
    - Toast notifications use `column-reverse` layout to prevent overlap
    - CSS animations for toast slide-in/out