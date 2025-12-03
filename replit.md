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
    └── images/          # Logo and images
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
The application uses PostgreSQL with three main tables:
- `trackings` - Main tracking records
- `shipping_routes` - Predefined routes and delivery estimates
- `status_history` - Tracking status change history

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
- 2024-12-03: Added bottom navigation bar and profile modal
  - Added fixed bottom navigation with 5 icons (Home, Videos, Messages, Search, Profile)
  - Created profile modal popup with user stats and info (similar to Instagram style)
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
