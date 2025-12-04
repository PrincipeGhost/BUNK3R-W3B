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