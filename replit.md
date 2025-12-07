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

## AI Constructor Module
The AI Constructor is an intelligent 8-phase system for generating web projects. Located in `tracking/ai_constructor.py` (~1340 lines).

**Architecture (8 Phases):**
1. **IntentParser** - Analyzes user messages to extract intent, task type, context, and specifications
2. **ResearchEngine** - Generates recommendations based on best practices for different contexts (restaurant, ecommerce, portfolio, SaaS, fintech)
3. **ClarificationManager** - Generates intelligent questions to clarify vague requests
4. **PromptBuilder** - Constructs optimized super-prompts for AI code generation
5. **PlanPresenter** - Formats and presents execution plans to users
6. **TaskOrchestrator** - Divides work into atomic tasks and manages execution
7. **OutputVerifier** - Verifies generated code for syntax, completeness, and requirements
8. **DeliveryManager** - Formats and delivers final results

**API Endpoints:**
- `POST /api/ai-constructor/process` - Processes message through all 8 phases
- `GET /api/ai-constructor/session` - Gets current session state
- `POST /api/ai-constructor/reset` - Resets session
- `GET /api/ai-constructor/files` - Gets generated files
- `POST /api/ai-constructor/confirm` - Confirms plan and continues execution

**Key Features:**
- Session management per user with state persistence
- Multi-language support (Spanish/English detection)
- Context-aware recommendations (restaurant, ecommerce, portfolio, SaaS, fintech)
- Style recommendations with color palettes
- Urgency detection
- Automatic clarification for vague requests
- Code verification before delivery
- OWNER-ONLY access via @require_owner decorator

## AI Toolkit Module (NEW - Dec 7, 2025)
Located in `tracking/ai_toolkit.py`, provides secure tools for AI Constructor to interact with files and system.

**Classes:**
1. **AIFileToolkit** - Secure file operations (read, write, edit, delete, search, list directory)
2. **AICommandExecutor** - Safe command execution with whitelist/blacklist
3. **AIErrorDetector** - Error pattern detection and fix suggestions for Python/Node
4. **AIProjectAnalyzer** - Project structure analysis (language, framework, dependencies)

**API Endpoints (OWNER ONLY):**
- `/api/ai-toolkit/files/read` - Read file content
- `/api/ai-toolkit/files/write` - Write file content
- `/api/ai-toolkit/files/edit` - Edit file by replacement
- `/api/ai-toolkit/files/delete` - Delete file (requires confirm=true AND confirm_text="DELETE")
- `/api/ai-toolkit/files/list` - List directory contents
- `/api/ai-toolkit/files/search` - Search code with regex
- `/api/ai-toolkit/command/run` - Execute whitelisted commands only
- `/api/ai-toolkit/command/install` - Install packages via pip/npm
- `/api/ai-toolkit/command/script` - Run validated .py/.js/.ts scripts
- `/api/ai-toolkit/errors/detect` - Detect errors in logs
- `/api/ai-toolkit/errors/analyze` - Analyze error and suggest fix
- `/api/ai-toolkit/project/analyze` - Analyze project structure

**Security Features:**
- All endpoints require @require_owner decorator
- File operations restricted to project root
- Blocked paths: .env, .git, node_modules, __pycache__, etc.
- Command whitelist: npm, pip, ls, cat, grep, git (safe commands only)
- Python/Node NOT allowed via run_command (use run_script for validated scripts)
- Script execution validates: file exists, is a file, has allowed extension (.py/.js/.ts)
- Command blacklist: rm -rf, sudo, chmod 777, eval, python -c, node -e, curl|bash, etc.
- Delete requires double confirmation (confirm=true AND confirm_text="DELETE")
- **Package Whitelist (Triple Protection):** Only approved packages can be installed automatically:
  - Python: flask, requests, beautifulsoup4, pillow, pandas, numpy, matplotlib, jinja2, werkzeug, gunicorn, pytest, click, pyyaml, python-dotenv, sqlalchemy, aiohttp, httpx, fastapi, uvicorn, psycopg2-binary, redis, celery
  - Node: express, react, vue, axios, lodash, moment, dayjs, tailwindcss, postcss, autoprefixer, vite, webpack, typescript, eslint, prettier, jest, nodemon, cors
  - Whitelist enforced at 3 levels: AIConstructor, install_package(), and run_command()

## AIToolkit-Constructor Integration (Updated - Dec 7, 2025)
The AI Constructor now uses AIToolkit for real file operations during code generation.

**Phase 1 Enhancement:**
- Automatically analyzes project structure using AIProjectAnalyzer
- Adds project context (language, framework, dependencies) to intent for better code generation

**Phase 6.1 - Real File Writing:**
- Generated files are saved to `ai_generated/` directory using AIFileToolkit
- Path traversal protection: uses os.path.basename() + os.path.abspath() validation
- Extension whitelist: .html, .css, .js, .jsx, .ts, .tsx, .json, .py, .md, .txt, .svg, .vue
- Filename sanitization: only alphanumeric, underscore, hyphen, dot allowed

**Phase 6.2 - Dependency Detection:**
- Detects Python imports and Node.js require/imports in generated code
- Filters standard library packages
- Auto-installs only whitelisted packages (max 3 per manager)
- Non-whitelisted packages reported for manual installation

**Phase 7 Enhancement:**
- Uses AIErrorDetector to scan generated files for syntax errors
- Displays detected errors in verification message
- Language-aware detection (Python, JavaScript, HTML, CSS)

## AI Workspace Module (NEW - Dec 7, 2025)
Located at `/workspace`, provides a 3-column IDE-like interface for AI Constructor.

**Frontend Components (workspace.js, workspace.css):**
1. **Chat Panel** - Left panel for user-AI interaction with 8-phase process visualization
2. **Preview Panel** - Center panel with live iframe preview, auto-refresh on file generation
3. **Files Panel** - Right panel with project file tree, context menus, file operations

**File Management API Endpoints:**
- `/api/files/tree` - Get project file tree structure
- `/api/files/content` - Read file content (requires auth)
- `/api/files/save` - Save file content (requires auth)
- `/api/files/create` - Create new file (requires auth)
- `/api/files/folder` - Create new folder (requires auth)
- `/api/files/delete` - Delete file/folder with confirmation (requires auth)
- `/api/files/rename` - Rename file/folder (requires auth)
- `/api/files/duplicate` - Duplicate file (requires auth)
- `/api/files/diff` - Generate diff between versions (requires auth)
- `/api/files/apply-diff` - Apply changes after confirmation (requires auth)
- `/api/files/history` - Get file edit history (requires auth)

**Security Features:**
- `validate_workspace_path()` - Prevents path traversal with os.path.abspath() check
- `check_workspace_auth()` - Validates demo sessions via verify_demo_session() OR Telegram init data via validate_telegram_webapp_data()
- Blocked paths: .env, .git, __pycache__, node_modules, .replit, .cache, .upm, .config, venv, .local, .nix
- Protected files: app.py, requirements.txt, run.py, init_db.py, replit.md
- Protected directories: tracking, templates, static (at root level)
- Frontend handles 401 errors with auth redirect

**UI Features:**
- Context menu (right-click): Open, Rename, Duplicate, Delete
- File highlighting animation for newly generated files
- Auto-expand folders to show generated files
- Diff viewer with syntax highlighting (green/red for add/remove)

## External Dependencies
- **PostgreSQL:** Primary database.
- **Telegram Web App API:** User authentication and core Telegram integration.
- **Resend API:** Email notifications.
- **TonCenter API (v3):** TON blockchain transaction verification for BUNK3RCO1N.
- **ChangeNow API:** Cryptocurrency exchange functionalities.
- **Cloudinary:** Encrypted media storage for publications.
- **Cryptography (Python library):** AES-256-GCM encryption/decryption of media files.
- **SMSPool API:** Virtual phone numbers provisioning.
- **STON.fi DEX API:** Real-time B3C/TON pricing.
- **CoinGecko API:** TON/USD conversion.
- **TON Connect SDK:** For wallet connection and transaction signing.
- **tonsdk (Python library):** For generating unique TON wallets.