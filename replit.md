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

### Section 19 - Centralized State Management
- Created `StateManager` module in `utils.js` with:
  - Centralized state storage for user, auth, wallet, balance, sections
  - Event-based pub/sub system for state changes with `subscribe()` and `unsubscribe()`
  - Helper methods: `setUser()`, `setBalance()`, `updateBalance()`, `setWallet()`, `setSection()`
  - Pending operations tracking: `addPendingOperation()`, `removePendingOperation()`, `hasPendingOperations()`
  - Session management: `updateActivity()`, `isSessionExpired()`
  - Notifications management: `addNotification()`, `markNotificationsRead()`
  - Feed/Stories state: `updateFeed()`, `updateStories()`
  - Full reset capability with `reset()`
- Created `RequestManager` for API requests with:
  - Configurable timeouts (default 30s)
  - Automatic retry with exponential backoff (3 retries by default)
  - Request cancellation by key to prevent race conditions
  - Pending request tracking
- Created `Debounce` utility for debouncing function calls
- Created `Throttle` utility for throttling function calls

### Section 20 - Production Logs
- Logger module already implemented with log levels
- Production environment automatically sets log level to WARN
- Debug/info logs suppressed in production

### Section 21 - Rate Limiting Implementation
- Created `RateLimiter` class in backend with:
  - Thread-safe request tracking
  - Automatic cleanup of old entries
  - Configurable limits per action type
- Created `@rate_limit()` decorator for Flask endpoints
- Configured rate limits for critical endpoints:
  - `posts_create`: 10 requests per minute
  - `posts_like`: 60 requests per minute
  - `comments_create`: 30 requests per minute
  - `follow`: 30 requests per minute
  - `payment_verify`: 20 requests per minute
  - `2fa_verify`: 5 requests per 5 minutes
  - `vn_purchase`: 5 requests per minute
- Added rate limiting to endpoints:
  - POST `/api/posts` - create publications
  - POST `/api/posts/<id>/like` - like posts
  - POST `/api/publications/<id>/comments` - add comments
  - POST `/api/users/<id>/follow` - follow users
  - POST `/api/ton/payment/<id>/verify` - verify payments
  - POST `/api/2fa/verify` - 2FA verification
  - POST `/api/vn/purchase` - virtual number purchase
- Response headers include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

### Section 22 - Timeouts and Retries
- `RequestManager` implements:
  - Default 30 second timeout for all requests
  - Automatic retry on 502, 503, 504 errors
  - Exponential backoff: 1s, 2s, 4s delays
  - Request cancellation to prevent race conditions
  - AbortController support for clean cancellation

### Section 23 - Cloudinary Improvements
- Added pre-encryption file size validation in `addFiles()`:
  - Images validated to max 10MB before encryption
  - Videos validated to max 100MB before encryption
  - Invalid file types rejected with user-friendly errors
- Enhanced `showUploadProgress()` with detailed stage messages:
  - 0-50%: "Encriptando archivos..."
  - 50-70%: "Preparando subida..."
  - 70-90%: "Subiendo a servidor..."
  - 90-100%: "Finalizando..."
- Progress now shows percentage and current stage

### Section 24 - Session Management
- Session activity monitoring via `startSessionActivityMonitor()`:
  - Tracks click, touch, keypress, scroll events
  - Checks session every 60 seconds
- Automatic 2FA re-verification after 10 minutes inactivity
- Session refresh via `/api/2fa/refresh` endpoint
- StateManager integration:
  - `updateActivity()`: Updates last activity timestamp
  - `isSessionExpired()`: Checks if session has expired
  - Session state sync across modules

### Section 25 - Table Creation Improvements
- Moved `pending_payments` table creation from runtime to initialization
- Added `initialize_payments_tables()` method in DatabaseManager
- Table initialization now happens at app startup
- Added indexes for `user_id` and `status` columns on pending_payments table

### Section 26 - Transaction Notifications System (Dec 2025)
- Added `create_notification()` method in DatabaseManager for generic notification creation
- Added `create_transaction_notification()` method for wallet transaction events:
  - Supports credit, debit, and general transaction types
  - Auto-generates localized messages with amounts and new balance
  - Types: `transaction_credit`, `transaction_debit`, `transaction`
- Integrated transaction notifications into payment flows:
  - Notifications created on successful TON payment verification (credits)
  - Notifications created on wallet debits (purchases)
- Enhanced notification filtering in backend:
  - Added `filter_type` parameter to `get_notifications()` method
  - Supports filters: all, unread, transactions, likes, comments, follows, mentions
- Enhanced frontend notification rendering:
  - Transaction notifications display wallet icon (coin emoji) instead of user avatar
  - Special styling for transaction notifications (gradient background)
  - Transaction click navigates to wallet screen
- Added "Transacciones" filter button to notifications screen in HTML
- Added CSS for transaction notification types with credit/debit color coding

### Section 27 - Feed & Wallet Improvements (Dec 2025)

#### Infinite Scroll for Publications Feed
- Added `feedOffset`, `feedLimit`, `hasMorePosts`, `isLoadingFeed`, `feedObserver` state to PublicationsManager
- Implemented `setupInfiniteScroll()` with IntersectionObserver for automatic loading
- Created `loadMorePosts()` for paginated feed loading (appends new posts)
- Added `appendPostsToFeed()` for incremental feed updates
- Updated `loadFeed()` to support refresh parameter and pagination state reset
- Added CSS for `.feed-sentinel`, `.feed-loading-more`, `.feed-end` indicators

#### Transaction History Filtering
- Added filter buttons (All/Recargas/Gastos) to wallet screen
- Created `initTransactionFilters()` function with event listeners
- Updated `loadTransactionHistory()` to include filter parameter in API calls
- Updated backend `/api/wallet/transactions` endpoint with filter support:
  - Accepts `filter` parameter: 'all', 'credit', 'debit'
  - Dynamic SQL query construction based on filter
- Added CSS for `.transaction-filters`, `.tx-filter-btn` with active state styling

#### Recharge Success Animation
- Created `showRechargeSuccess(amount)` function with full-screen success overlay
- Animated checkmark icon, amount display, and "Recarga exitosa" message
- Haptic feedback on successful recharge
- Auto-dismiss after 2 seconds with fade transition
- Updated payment verification to use success animation instead of toast
- Added CSS for `.recharge-success-animation` with keyframe animations

#### Clickable Hashtags Enhancement
- Improved `goToHashtag()` to navigate within SPA using App.showScreen()
- Hashtags now open explore screen and auto-populate search input
- Added CSS for `.hashtag`, `.mention` with hover styles

#### Comment Pagination (Section 6)
- Added `commentsState` object to track per-post comment pagination state
- Updated `loadInlineComments()` to support append parameter for pagination
- Added `loadMoreComments()` function for loading additional comments
- Comments load 5 at a time with "Ver mas comentarios" button
- State management includes: offset, hasMore, loading flags per post
- Added CSS for `.load-more-comments-btn`, `.loading-comments`, `.no-comments`

### Section 28 - Profile & Navigation Improvements (Dec 2025)

#### Dynamic Screen Navigation System
- Created centralized `hideAllScreens()` utility method
- Refactored screen show methods (showPage, showProfileScreen, showSettingsScreen, showAdminScreen) to use hideAllScreens()
- Added `handleSidebarNavigation()` for proper routing from sidebar menu items
- Integrated StateManager for section tracking across navigation

#### Profile Stats and Followers/Following Modal
- Added clickable profile stats (posts, followers, following)
- Created followers/following modal with tab switching UI
- Implemented `showFollowersModal()`, `hideFollowersModal()`, `switchFollowersTab()` methods
- Added `loadProfileStats()` to fetch posts/followers/following counts
- Added backend endpoints:
  - `GET /api/users/<user_id>/stats` - Get profile statistics
  - `GET /api/users/<user_id>/followers` - Get user's followers list
  - `GET /api/users/<user_id>/following` - Get users being followed
- Added `count_user_publications()` method to DatabaseManager

#### Edit Profile Modal
- Created edit profile modal with avatar upload and bio editing
- Implemented `showEditProfileModal()`, `hideEditProfileModal()`, `saveProfile()` methods
- Added `handleAvatarSelect()` for avatar file selection and preview
- Added backend endpoints:
  - `PUT /api/users/<user_id>/profile` - Update profile bio
  - `POST /api/users/avatar` - Upload avatar image
- Avatars stored in `/static/uploads/avatars/`

#### Memory Leak Cleanup
- Added interval tracking for `notificationBadgeInterval` with proper cleanup
- Interval is cleared before creating new ones to prevent memory leaks
- `sessionActivityInterval` cleanup already implemented

#### CSS Additions
- Added `.followers-modal` styles with tabs and user list
- Added `.edit-profile-modal` styles with avatar section
- Added `.follower-item`, `.follower-avatar`, `.follower-btn` styles
- Made `.profile-page-stat` clickable with hover effects