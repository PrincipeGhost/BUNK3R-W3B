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
  - Redesigned bottom navigation: Home, Marketplace, Bots, Billetera (Wallet), Perfil (Profile)
  - Created Marketplace page with product categories and item grid (prices in credits)
  - Created Bots page with active user bots and available bots for purchase
  - Created Wallet page with credit balance, transaction history, and top-up options
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
