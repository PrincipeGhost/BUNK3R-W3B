# BUNK3R - Telegram Package Tracking System

## Overview
BUNK3R is a Telegram Web App designed for comprehensive package tracking and shipment management. It provides a robust system for users to track packages, manage shipments, and receive notifications, all integrated seamlessly with Telegram authentication. The project aims to offer a mobile-optimized, secure, and user-friendly experience for managing logistics.

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
- **Security System:** A 17-point security system for wallet and device management including trusted devices, 2FA integration, lockout mechanisms, security activity logs, and administrative monitoring. This includes blocking BUNK3RCO1N access on untrusted devices and a dynamic device validation system.
- **Monetary System (BUNK3RCO1N):** Internal currency for in-app purchases (bots, products), with a secure TON payment verification system for topping up, integrating with TonCenter API. Features include:
  - Auto-registration of first connected wallet as primary wallet for security
  - TON wallet address validation (48 chars, EQ/UQ prefix)
  - Backup wallet configuration via modal UI
  - Transaction history with load more and CSV export
  - Debit system for bot purchases with insufficient balance handling
  - Telegram notifications for large transactions
- **Social Features:** User profiles, posts, likes, follows, and avatar uploads.
- **Encrypted Publications System:** Complete social media-like publication system with end-to-end encryption:
  - AES-256-GCM encryption for all media before upload to Cloudinary
  - Photo/video posts with carousel support (up to 10 items)
  - Stories (24h duration, 15s max for videos)
  - Likes, comments with emoji reactions
  - Mentions (@user) and hashtags (#topic)
  - Save posts, share functionality
  - Edit/delete own posts
  - Block/report users and content
  - Explore page and notifications
  - All content encrypted client-side before external storage
- **Marketplace:** Sections for products and dynamic bot management (purchase, ownership).
- **External Exchange:** Integration with ChangeNow cryptocurrency exchange for in-app currency swapping.
- **Virtual Numbers System:** Purchase phone numbers for SMS verification using BUNK3RCO1N:
  - SMSPool API integration for automated number provisioning
  - Server-side price calculation with 30% commission (1 USD = 10 BUNK3RCO1N)
  - Atomic purchase flow: order creation → wallet debit → provider API → refund on failure
  - Automatic SMS polling every 5 seconds
  - Order history and active orders management
  - Admin-only provider balance visibility
  - API key validation on all SMSPool endpoints

**Technical Implementations:**
- **Frontend:** Vanilla JavaScript for dynamic interactions, CSS3 for styling.
- **Backend:** Flask for routing, API endpoints, and business logic.
- **Database Schema:** PostgreSQL with tables for trackings, shipping routes, status history, users, posts, follows, products, user bots, achievements, wallet transactions, security-related data, and encrypted publications system tables (`encrypted_publications`, `publication_media`, `publication_reactions`, `publication_comments`, `publication_saves`, `publication_shares`, `stories`, `story_views`, `story_reactions`, `hashtags`, `publication_hashtags`, `mentions`, `user_blocks`, `content_reports`, `notifications`).
- **Deployment:** Optimized for Replit with Gunicorn for production, and specific cache control headers for iframe compatibility.

## External Dependencies
- **PostgreSQL:** Primary database for all application data.
- **Telegram Web App API:** For user authentication and core Telegram integration.
- **Resend API:** For sending email notifications.
- **TonCenter API (v3):** For verifying TON blockchain transactions for BUNK3RCO1N top-ups.
- **ChangeNow API:** For cryptocurrency exchange functionalities within the app.
- **Cloudinary:** Encrypted media storage for publications system. All media is AES-256-GCM encrypted before uploading.
- **Cryptography (Python):** For AES-256-GCM encryption/decryption of media files.
- **SMSPool API:** For virtual phone numbers provisioning.

## Recent Security Improvements (Dec 2025)

### Section 15 - XSS Vulnerabilities Fixed
- Created centralized `utils.js` with `escapeHtml()` and `escapeAttribute()` functions
- Sanitized all user input rendering in:
  - `virtual-numbers.js`: Service names, country names, prices
  - `publications.js`: Usernames, captions, comments, stories, mentions
  - `app.js`: Tracking cards (recipientName, productName, addresses), search queries, history notes
- All dynamic HTML uses parseInt() for numeric IDs to prevent injection
- All onclick handlers use escapeAttribute() for string parameters

### Section 16 - Error Handling Improvements
- Created centralized `Logger` module with log levels (DEBUG, INFO, WARN, ERROR)
- Logger automatically reduces verbosity in production environment
- Created `ErrorHandler` module with:
  - `sanitize_error()`: Removes sensitive info from error messages
  - `_getUserFriendlyMessage()`: Maps technical errors to user-friendly Spanish messages
  - Integration with toast notification system
- Created `FallbackUI` module with:
  - `showLoadingError()`: Displays retry button on failed loads
  - `showEmptyState()`: Displays empty state with icons
  - `showSkeleton()`: Displays skeleton loaders during data fetch
- Added CSS for error-fallback, empty-state, and skeleton-card components
- Updated `loadFeed()` and `loadStories()` to show proper error feedback
- Updated `decryptMedia()` to use ErrorHandler for encryption errors
- Backend: Created `sanitize_error()` function to prevent technical error exposure
- All API endpoints now use sanitize_error() instead of raw str(e)

### Section 17 - Backend Input Validation
- Created `InputValidator` class with comprehensive validation methods:
  - `sanitize_html()`: Escapes HTML to prevent XSS
  - `sanitize_text()`: Removes control characters, limits length
  - `sanitize_name()`: Sanitizes names with character filtering
  - `validate_url()`: SSRF protection with private IP blocking
  - `validate_telegram_url()`: Validates Telegram-specific URLs
  - `validate_cloudinary_url()`: Validates Cloudinary URLs
  - `validate_file_content()`: Magic byte validation for file types
  - `validate_tracking_id()`: Format validation for tracking IDs
  - `validate_caption()`: Caption length and sanitization
- Updated `download_telegram_photo()` with SSRF protection and content validation
- Updated `/api/tracking` endpoint with input sanitization
- Updated `/api/posts` endpoint with caption and URL validation
- All text fields now have maximum length limits defined

### Section 18 - Accessibility (A11Y) Improvements
- Created centralized `A11y` module in `utils.js` with:
  - `trapFocus()`: Focus trap for modals preventing tab-out
  - `releaseFocus()`: Properly releases focus trap and restores previous focus
  - `openModal()`: Opens modals with proper ARIA attributes and focus management
  - `closeModal()`: Closes modals and restores scroll/focus
  - `announce()`: Screen reader announcements via live region
  - `makeInteractive()`: Adds keyboard navigation to custom interactive elements
- Created centralized `Toast` module with accessibility support:
  - All toasts use `role="alert"` for screen reader announcements
  - Error toasts use `aria-live="assertive"` for immediate reading
  - Close buttons are keyboard accessible (Enter/Space)
  - Toasts auto-announce via A11y.announce()
- Added ARIA attributes to HTML:
  - Bottom navigation: `role="navigation"`, `aria-label`, `aria-current="page"`
  - All SVG icons: `aria-hidden="true"` to hide from screen readers
  - Screen reader only labels: `<span class="sr-only">` for icon-only buttons
  - All modals: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
  - Modal close buttons: `aria-label="Cerrar"`
  - Stories viewer: Progress bar with `role="progressbar"`
  - Options menu: `role="menu"` and `role="menuitem"`
  - Lists: `role="list"` with `aria-label`
  - Page regions: `role="region"` with `aria-label`
  - Back buttons: `aria-label="Volver al inicio"`
- CSS improvements:
  - Added `.sr-only` class for screen-reader-only content
  - Added `.sr-only-focusable` for focusable skip links
  - Focus indicators already present with `:focus-visible`
  - `prefers-reduced-motion` already supported
  - `user-scalable=yes` already set in viewport
- Updated `App.handleBottomNav()` to manage `aria-current` attribute
- Updated `App.showToast()` to use centralized Toast module with haptic feedback