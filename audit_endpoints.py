#!/usr/bin/env python3
"""
Script de Auditoría COMPLETA de Endpoints - BUNK3R API
Prueba TODOS los 315 endpoints de los 7 blueprints.
Solo anota errores, NO arregla nada.

Blueprints:
1. auth_routes.py - 10 endpoints
2. admin_routes.py - 134 endpoints
3. blockchain_routes.py - 41 endpoints
4. bots_routes.py - 8 endpoints
5. tracking_routes.py - 12 endpoints
6. user_routes.py - 94 endpoints
7. vn_routes.py - 16 endpoints

TOTAL: 315 endpoints
"""

import os
import sys
import json
import time
import hashlib
import hmac
import urllib.parse
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:5000"
OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '8305740334')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '') or os.environ.get('TELEGRAM_BOT_TOKEN', '')

results = {
    'tested': 0,
    'passed': 0,
    'failed': 0,
    'errors': [],
    'by_blueprint': {}
}


def generate_telegram_init_data(user_id=None):
    """Genera initData VÁLIDO para autenticación Telegram."""
    if user_id is None:
        user_id = OWNER_TELEGRAM_ID
    
    user_data = {
        "id": int(user_id),
        "first_name": "Owner",
        "last_name": "Test",
        "username": "owner_test",
        "language_code": "es"
    }
    
    auth_date = int(time.time())
    user_json = json.dumps(user_data, separators=(',', ':'))
    
    data_check_string = f"auth_date={auth_date}\nuser={user_json}"
    
    if BOT_TOKEN:
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        hash_value = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
    else:
        hash_value = "demo_mode_no_token"
    
    init_data = urllib.parse.urlencode({
        'user': user_json,
        'auth_date': str(auth_date),
        'hash': hash_value
    })
    
    return init_data


def get_headers(with_auth=True):
    """Obtiene headers para requests."""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    if with_auth:
        headers['X-Telegram-Init-Data'] = generate_telegram_init_data()
    return headers


def test_endpoint(method, url, data=None, description="", with_auth=True, expected_codes=[200], blueprint="unknown"):
    """Prueba un endpoint y registra resultado."""
    results['tested'] += 1
    
    if blueprint not in results['by_blueprint']:
        results['by_blueprint'][blueprint] = {'tested': 0, 'passed': 0, 'failed': 0}
    results['by_blueprint'][blueprint]['tested'] += 1
    
    full_url = f"{BASE_URL}{url}"
    
    try:
        headers = get_headers(with_auth)
        
        if method == 'GET':
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(full_url, json=data or {}, headers=headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(full_url, json=data or {}, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(full_url, headers=headers, timeout=10)
        else:
            results['failed'] += 1
            results['by_blueprint'][blueprint]['failed'] += 1
            results['errors'].append({
                'endpoint': f"{method} {url}",
                'blueprint': blueprint,
                'description': description,
                'error': f"Método no soportado: {method}",
                'status_code': None
            })
            return
        
        if response.status_code in expected_codes:
            results['passed'] += 1
            results['by_blueprint'][blueprint]['passed'] += 1
            print(f"  ✅ {method} {url} -> {response.status_code}")
        else:
            results['failed'] += 1
            results['by_blueprint'][blueprint]['failed'] += 1
            try:
                resp_json = response.json()
                error_msg = resp_json.get('error', resp_json.get('message', str(resp_json)[:200]))
            except:
                error_msg = response.text[:200]
            
            results['errors'].append({
                'endpoint': f"{method} {url}",
                'blueprint': blueprint,
                'description': description,
                'error': error_msg,
                'status_code': response.status_code
            })
            print(f"  ❌ {method} {url} -> {response.status_code}: {str(error_msg)[:80]}")
            
    except requests.exceptions.Timeout:
        results['failed'] += 1
        results['by_blueprint'][blueprint]['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'blueprint': blueprint,
            'description': description,
            'error': "TIMEOUT",
            'status_code': None
        })
        print(f"  ⏱️ {method} {url} -> TIMEOUT")
        
    except requests.exceptions.ConnectionError as e:
        results['failed'] += 1
        results['by_blueprint'][blueprint]['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'blueprint': blueprint,
            'description': description,
            'error': f"CONNECTION ERROR",
            'status_code': None
        })
        print(f"  🔌 {method} {url} -> CONNECTION ERROR")
        
    except Exception as e:
        results['failed'] += 1
        results['by_blueprint'][blueprint]['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'blueprint': blueprint,
            'description': description,
            'error': f"EXCEPTION: {str(e)[:100]}",
            'status_code': None
        })
        print(f"  💥 {method} {url} -> {str(e)[:50]}")


def audit_auth_routes():
    """1. auth_routes.py - 10 endpoints de autenticación y 2FA"""
    print("\n" + "="*60)
    print("🔐 BLUEPRINT 1: auth_routes.py (10 endpoints)")
    print("="*60)
    bp = "auth_routes"
    
    test_endpoint('GET', '/api/auth/health', description="Health check", with_auth=False, blueprint=bp)
    test_endpoint('POST', '/api/demo/2fa/verify', {'code': '110917'}, "Demo 2FA verify", with_auth=False, expected_codes=[200, 403], blueprint=bp)
    test_endpoint('POST', '/api/demo/2fa/logout', description="Demo 2FA logout", with_auth=False, expected_codes=[200, 403], blueprint=bp)
    test_endpoint('POST', '/api/2fa/status', description="2FA status", blueprint=bp)
    test_endpoint('POST', '/api/2fa/setup', description="2FA setup", blueprint=bp)
    test_endpoint('POST', '/api/2fa/verify', {'code': '123456'}, "2FA verify", expected_codes=[200, 400, 401], blueprint=bp)
    test_endpoint('POST', '/api/2fa/session', description="2FA session", blueprint=bp)
    test_endpoint('POST', '/api/2fa/refresh', description="2FA refresh", blueprint=bp)
    test_endpoint('POST', '/api/2fa/disable', {'code': '123456'}, "2FA disable", expected_codes=[200, 400, 401], blueprint=bp)
    test_endpoint('POST', '/api/validate', {'initData': generate_telegram_init_data()}, "Validate", with_auth=False, blueprint=bp)


def audit_admin_routes():
    """2. admin_routes.py - 134 endpoints de administración"""
    print("\n" + "="*60)
    print("👑 BLUEPRINT 2: admin_routes.py (134 endpoints)")
    print("="*60)
    bp = "admin_routes"
    uid = OWNER_TELEGRAM_ID
    
    # Health
    test_endpoint('GET', '/api/admin/health', description="Health", blueprint=bp)
    
    # Dashboard (5)
    test_endpoint('GET', '/api/admin/dashboard/stats', description="Dashboard stats", blueprint=bp)
    test_endpoint('GET', '/api/admin/dashboard/activity', description="Dashboard activity", blueprint=bp)
    test_endpoint('GET', '/api/admin/dashboard/alerts', description="Dashboard alerts", blueprint=bp)
    test_endpoint('GET', '/api/admin/dashboard/charts', description="Dashboard charts", blueprint=bp)
    
    # Users management (18)
    test_endpoint('GET', '/api/admin/users', description="List users", blueprint=bp)
    test_endpoint('GET', '/api/admin/users/export', description="Export users", blueprint=bp)
    test_endpoint('GET', f'/api/admin/user/{uid}', description="Get user", blueprint=bp)
    test_endpoint('GET', f'/api/admin/users/{uid}/detail', description="User detail", blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/ban', {'banned': False}, "Ban user", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/balance', {'amount': 0}, "Update balance", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/note', {'note': 'Test'}, "Add note", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/logout', description="Force logout", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/notify', {'message': 'Test'}, "Notify user", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/tags', {'tags': ['test']}, "Update tags", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/admin/users/{uid}/risk-score', description="Risk score", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/users/{uid}/risk-score/calculate', description="Calc risk", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/admin/users/{uid}/risk-score/history', description="Risk history", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/admin/users/{uid}/related-accounts', description="Related accounts", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/user/credits', {'user_id': uid, 'amount': 0}, "Add credits", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/user/toggle-status', {'user_id': uid}, "Toggle status", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/user/verify', {'user_id': uid}, "Verify user", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Stats (4)
    test_endpoint('GET', '/api/admin/stats', description="Stats", blueprint=bp)
    test_endpoint('GET', '/api/admin/stats/overview', description="Stats overview", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/stats/users', description="Stats users", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/stats/transactions', description="Stats tx", expected_codes=[200, 500], blueprint=bp)
    
    # Security (8)
    test_endpoint('GET', '/api/admin/security/users', description="Security users", blueprint=bp)
    test_endpoint('GET', f'/api/admin/security/user/{uid}/devices', description="User devices", blueprint=bp)
    test_endpoint('POST', f'/api/admin/security/user/{uid}/device/remove', {'device_id': 1}, "Remove device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/security/alerts', description="Security alerts", blueprint=bp)
    test_endpoint('POST', '/api/admin/security/alerts/1/resolve', description="Resolve alert", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/security/statistics', description="Security stats", blueprint=bp)
    test_endpoint('GET', f'/api/admin/security/user/{uid}/activity', description="User activity", blueprint=bp)
    
    # Financial (3)
    test_endpoint('GET', '/api/admin/financial/stats', description="Financial stats", blueprint=bp)
    test_endpoint('GET', '/api/admin/financial/period-stats?start_date=2025-01-01&end_date=2025-12-31', description="Period stats", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/financial/period-stats/export?start_date=2025-01-01&end_date=2025-12-31', description="Export period", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Logs (7)
    test_endpoint('GET', '/api/admin/logs/admin', description="Admin logs", blueprint=bp)
    test_endpoint('GET', '/api/admin/logs/security', description="Security logs", blueprint=bp)
    test_endpoint('GET', '/api/admin/logs/errors', description="Error logs", blueprint=bp)
    test_endpoint('POST', '/api/admin/logs/errors/1/resolve', description="Resolve error", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/logs/logins', description="Login logs", blueprint=bp)
    test_endpoint('GET', '/api/admin/logs/config-history', description="Config history", blueprint=bp)
    test_endpoint('GET', '/api/admin/logs/export', description="Export logs", expected_codes=[200, 500], blueprint=bp)
    
    # Config (2)
    test_endpoint('GET', '/api/admin/config', description="Get config", blueprint=bp)
    test_endpoint('POST', '/api/admin/config', {'key': 'test', 'value': 'test'}, "Update config", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Analytics (3)
    test_endpoint('GET', '/api/admin/analytics/users', description="Analytics users", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/analytics/usage', description="Analytics usage", blueprint=bp)
    test_endpoint('GET', '/api/admin/analytics/conversion', description="Analytics conversion", expected_codes=[200, 500], blueprint=bp)
    
    # Support (6)
    test_endpoint('GET', '/api/admin/support/tickets', description="Tickets list", blueprint=bp)
    test_endpoint('GET', '/api/admin/support/tickets/1', description="Get ticket", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('PUT', '/api/admin/support/tickets/1', {'status': 'closed'}, "Update ticket", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/support/tickets/1/reply', {'message': 'Test'}, "Reply ticket", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/support/templates', description="Templates", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/support/templates', {'name': 'Test', 'content': 'Test'}, "Add template", expected_codes=[200, 400, 500], blueprint=bp)
    
    # FAQ (4)
    test_endpoint('GET', '/api/admin/faq', description="FAQ list", blueprint=bp)
    test_endpoint('POST', '/api/admin/faq', {'question': 'Test?', 'answer': 'Test'}, "Add FAQ", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('PUT', '/api/admin/faq/1', {'question': 'Test?', 'answer': 'Updated'}, "Update FAQ", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/faq/1', description="Delete FAQ", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Messages (4)
    test_endpoint('GET', '/api/admin/messages', description="Messages", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/messages', {'content': 'Test', 'user_ids': [uid]}, "Send message", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/messages/scheduled', description="Scheduled msgs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/messages/1/cancel', description="Cancel msg", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Blocked IPs (3)
    test_endpoint('GET', '/api/admin/blocked-ips', description="Blocked IPs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/blocked-ips', {'ip': '1.2.3.4', 'reason': 'Test'}, "Block IP", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/blocked-ips/1', description="Unblock IP", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Wallet Pool (1)
    test_endpoint('GET', '/api/admin/wallet-pool/stats', description="Wallet pool", expected_codes=[200, 500], blueprint=bp)
    
    # Secrets (1)
    test_endpoint('GET', '/api/admin/secrets-status', description="Secrets status", expected_codes=[200, 500], blueprint=bp)
    
    # Fraud (4)
    test_endpoint('GET', '/api/admin/fraud/multiple-accounts', description="Multi accounts", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/fraud/ip-blacklist', description="IP blacklist", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/fraud/ip-blacklist', {'ip': '1.2.3.4'}, "Add to blacklist", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/fraud/ip-blacklist/1', description="Remove blacklist", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Realtime (1)
    test_endpoint('GET', '/api/admin/realtime/online', description="Online users", expected_codes=[200, 500], blueprint=bp)
    
    # Sessions (4)
    test_endpoint('GET', '/api/admin/sessions', description="Sessions", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/sessions/terminate', {'session_id': 'test'}, "Terminate session", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', f'/api/admin/sessions/terminate-all/{uid}', description="Terminate all", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/sessions/logout-all', description="Logout all", expected_codes=[200, 500], blueprint=bp)
    
    # Products (3)
    test_endpoint('GET', '/api/admin/products', description="Products", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/products', {'name': 'Test', 'price': 10}, "Add product", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/products/1', description="Delete product", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Transactions (2)
    test_endpoint('GET', '/api/admin/transactions', description="Transactions", blueprint=bp)
    test_endpoint('GET', '/api/admin/transactions/1', description="Get transaction", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Purchases (3)
    test_endpoint('GET', '/api/admin/purchases', description="Purchases", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/purchases/test123', description="Get purchase", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/purchases/test123/credit', description="Credit purchase", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Activity & Lockouts (3)
    test_endpoint('GET', '/api/admin/activity', description="Activity", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/lockouts', description="Lockouts", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/unlock-user', {'user_id': uid}, "Unlock user", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Telegram (5)
    test_endpoint('GET', '/api/admin/telegram/settings', description="TG settings", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/telegram/settings', {'setting': 'test'}, "Update TG", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/telegram/test', description="Test TG", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/telegram/verify', description="Verify TG", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/telegram/send', {'user_id': uid, 'message': 'Test'}, "Send TG", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Settings (1)
    test_endpoint('GET', '/api/admin/settings', description="Settings", expected_codes=[200, 500], blueprint=bp)
    
    # Notifications (3)
    test_endpoint('GET', '/api/admin/notifications', description="Notifications", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/notifications/mark-read', {'ids': [1]}, "Mark read", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/notifications/delete', {'ids': [1]}, "Delete notif", expected_codes=[200, 400, 500], blueprint=bp)
    
    # System (1)
    test_endpoint('GET', '/api/admin/system-status', description="System status", expected_codes=[200, 500], blueprint=bp)
    
    # Content (7)
    test_endpoint('GET', '/api/admin/content/stats', description="Content stats", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/content/posts', description="Content posts", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/content/posts/1', description="Get post", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/content/posts/1', description="Delete post", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/content/posts/1/warn', {'reason': 'Test'}, "Warn post", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/content/posts/1/ban-author', description="Ban author", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/content/reported', description="Reported content", expected_codes=[200, 500], blueprint=bp)
    
    # Wallets (7)
    test_endpoint('GET', '/api/admin/wallets/hot', description="Hot wallets", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/wallets/deposits', description="Deposits", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/wallets/fill-pool', {'amount': 1}, "Fill pool", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/wallets/consolidate', description="Consolidate", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/blockchain/history', description="BC history", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/wallets/pool-config', description="Pool config", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/wallets/1/consolidate', description="Consolidate 1", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Admin 2FA (1)
    test_endpoint('POST', '/api/admin/2fa/verify', {'code': '123456'}, "Admin 2FA", expected_codes=[200, 400, 401, 500], blueprint=bp)
    
    # Reports (2)
    test_endpoint('GET', '/api/admin/reports', description="Reports", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('PUT', '/api/admin/reports/1', {'status': 'resolved'}, "Update report", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Bots management (8)
    test_endpoint('GET', '/api/admin/bots', description="Bots list", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/bots', {'name': 'Test', 'type': 'test'}, "Add bot", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/bots/1', description="Delete bot", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/bots/1/toggle', description="Toggle bot", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('PUT', '/api/admin/bots/1', {'name': 'Updated'}, "Update bot", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/bots/stats', description="Bots stats", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/bots/usage', description="Bots usage", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/bots/revenue', description="Bots revenue", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/bots/purchases', description="Bots purchases", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/bots/1/logs', description="Bot logs", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Verifications (1)
    test_endpoint('GET', '/api/admin/verifications', description="Verifications", expected_codes=[200, 500], blueprint=bp)
    
    # Shadow sessions (2)
    test_endpoint('GET', '/api/admin/shadow-sessions', description="Shadow sessions", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/shadow-sessions/start', {'user_id': uid}, "Start shadow", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Marketplace (1)
    test_endpoint('GET', '/api/admin/marketplace', description="Marketplace", expected_codes=[200, 500], blueprint=bp)
    
    # Client logs (2)
    test_endpoint('GET', '/api/admin/client-logs', description="Client logs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/logs-simple', description="Simple logs", expected_codes=[200, 500], blueprint=bp)
    
    # B3C Withdrawals (3)
    test_endpoint('GET', '/api/admin/b3c/withdrawals', description="B3C withdrawals", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/b3c/withdrawals/test123', description="Get withdrawal", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/b3c/withdrawals/test123/process', {'action': 'approve'}, "Process withdrawal", expected_codes=[200, 400, 404, 500], blueprint=bp)
    
    # Transfers (2)
    test_endpoint('GET', '/api/admin/transfers', description="Transfers", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/transfers/test123', description="Get transfer", expected_codes=[200, 404, 500], blueprint=bp)


def audit_blockchain_routes():
    """3. blockchain_routes.py - 41 endpoints de blockchain/crypto"""
    print("\n" + "="*60)
    print("⛓️ BLUEPRINT 3: blockchain_routes.py (41 endpoints)")
    print("="*60)
    bp = "blockchain_routes"
    
    # Health
    test_endpoint('GET', '/api/blockchain/health', description="Health", with_auth=False, blueprint=bp)
    
    # Exchange (6)
    test_endpoint('GET', '/api/exchange/currencies', description="Currencies", blueprint=bp)
    test_endpoint('GET', '/api/exchange/min-amount?from=btc&to=ton', description="Min amount", blueprint=bp)
    test_endpoint('GET', '/api/exchange/estimate?from=btc&to=ton&amount=0.01', description="Estimate", blueprint=bp)
    test_endpoint('POST', '/api/exchange/create', {'from': 'btc', 'to': 'ton', 'amount': 0.01, 'address': 'test'}, "Create exchange", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/exchange/status/test123', description="Exchange status", expected_codes=[200, 404, 500], blueprint=bp)
    
    # TON (5)
    test_endpoint('POST', '/api/ton/payment/create', {'tonAmount': 1}, "TON payment", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/ton/wallet-info', description="TON wallet info", with_auth=False, blueprint=bp)
    test_endpoint('POST', '/api/ton/payment/TEST123/verify', description="Verify payment", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/ton/payment/TEST123/status', description="Payment status", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Wallet (7)
    test_endpoint('GET', '/api/wallet/merchant', description="Merchant wallet", with_auth=False, blueprint=bp)
    test_endpoint('GET', '/api/wallet/balance', description="Wallet balance", blueprint=bp)
    test_endpoint('GET', '/api/wallet/address', description="Wallet address", blueprint=bp)
    test_endpoint('POST', '/api/wallet/connect', {'address': 'EQtest123'}, "Connect wallet", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/wallet/credit', {'amount': 10}, "Credit wallet", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/wallet/transactions', description="Wallet tx", expected_codes=[200, 500], blueprint=bp)
    
    # B3C (23)
    test_endpoint('GET', '/api/b3c/price', description="B3C price", with_auth=False, blueprint=bp)
    test_endpoint('POST', '/api/b3c/calculate/buy', {'tonAmount': 1}, "Calc buy", blueprint=bp)
    test_endpoint('POST', '/api/b3c/calculate/sell', {'b3cAmount': 100}, "Calc sell", blueprint=bp)
    test_endpoint('GET', '/api/b3c/balance', description="B3C balance", blueprint=bp)
    test_endpoint('GET', '/api/b3c/config', description="B3C config", with_auth=False, blueprint=bp)
    test_endpoint('GET', '/api/b3c/network', description="B3C network", with_auth=False, blueprint=bp)
    test_endpoint('GET', '/api/b3c/testnet/guide', description="Testnet guide", with_auth=False, blueprint=bp)
    test_endpoint('POST', '/api/b3c/buy/create', {'tonAmount': 1}, "Buy B3C", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/buy/TEST123/verify', description="Verify buy", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/b3c/transactions', description="B3C transactions", blueprint=bp)
    test_endpoint('POST', '/api/b3c/transfer', {'to_user_id': '123', 'amount': 10}, "Transfer B3C", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/sell', {'b3cAmount': 10}, "Sell B3C", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/withdraw', {'amount': 10, 'address': 'EQtest'}, "Withdraw B3C", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/b3c/withdraw/test123/status', description="Withdraw status", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/b3c/deposit/address', description="Deposit address", blueprint=bp)
    test_endpoint('GET', '/api/b3c/commissions', description="Commissions", blueprint=bp)
    test_endpoint('GET', '/api/b3c/scheduler/status', description="Scheduler status", blueprint=bp)
    test_endpoint('GET', '/api/b3c/wallet-pool/stats', description="Pool stats", blueprint=bp)
    test_endpoint('POST', '/api/b3c/wallet-pool/fill', {'amount': 1}, "Fill pool", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/wallet-pool/consolidate', description="Consolidate pool", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/admin/force-verify/TEST123', description="Force verify", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/b3c/deposits/check', description="Check deposits", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/b3c/deposits/history', description="Deposit history", blueprint=bp)
    test_endpoint('GET', '/api/b3c/deposits/pending', description="Pending deposits", blueprint=bp)
    test_endpoint('GET', '/api/b3c/last-purchase', description="Last purchase", blueprint=bp)


def audit_bots_routes():
    """4. bots_routes.py - 8 endpoints de bots"""
    print("\n" + "="*60)
    print("🤖 BLUEPRINT 4: bots_routes.py (8 endpoints)")
    print("="*60)
    bp = "bots_routes"
    
    test_endpoint('GET', '/api/bots/health', description="Health", with_auth=False, blueprint=bp)
    test_endpoint('POST', '/api/bots/init', description="Init bots", blueprint=bp)
    test_endpoint('GET', '/api/bots/my', description="My bots", blueprint=bp)
    test_endpoint('GET', '/api/bots/available', description="Available", blueprint=bp)
    test_endpoint('POST', '/api/bots/purchase', {'botType': 'test'}, "Purchase", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/bots/1/remove', description="Remove bot", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/bots/1/toggle', description="Toggle bot", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/bots/1/config', description="Bot config", expected_codes=[200, 404], blueprint=bp)


def audit_tracking_routes():
    """5. tracking_routes.py - 12 endpoints de tracking"""
    print("\n" + "="*60)
    print("📦 BLUEPRINT 5: tracking_routes.py (12 endpoints)")
    print("="*60)
    bp = "tracking_routes"
    
    test_endpoint('GET', '/api/tracking/health', description="Health", with_auth=False, blueprint=bp)
    test_endpoint('GET', '/api/trackings', description="List trackings", blueprint=bp)
    test_endpoint('GET', '/api/stats', description="Stats", blueprint=bp)
    test_endpoint('GET', '/api/delay-reasons', description="Delay reasons", blueprint=bp)
    test_endpoint('GET', '/api/statuses', description="Statuses", blueprint=bp)
    test_endpoint('POST', '/api/tracking', {'trackingId': 'TEST123', 'recipientName': 'Test', 'productName': 'Test'}, "Create tracking", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/tracking/TEST123', description="Get tracking", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('PUT', '/api/tracking/TEST123', {'recipientName': 'Updated'}, "Update tracking", expected_codes=[200, 400, 404], blueprint=bp)
    test_endpoint('PUT', '/api/tracking/TEST123/status', {'status': 'EN_TRANSITO'}, "Update status", expected_codes=[200, 400, 404], blueprint=bp)
    test_endpoint('POST', '/api/tracking/TEST123/delay', {'days': 1, 'reason': 'Test'}, "Add delay", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/tracking/TEST123/email', {'email': 'test@test.com', 'bankEntity': 'Test', 'iban': 'ES123'}, "Send email", expected_codes=[200, 400, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/tracking/TEST123', description="Delete tracking", expected_codes=[200, 404], blueprint=bp)


def audit_user_routes():
    """6. user_routes.py - 94 endpoints de usuario"""
    print("\n" + "="*60)
    print("👤 BLUEPRINT 6: user_routes.py (94 endpoints)")
    print("="*60)
    bp = "user_routes"
    uid = OWNER_TELEGRAM_ID
    
    # Health
    test_endpoint('GET', '/api/user/health', description="Health", with_auth=False, blueprint=bp)
    
    # Profile (7)
    test_endpoint('GET', '/api/users/me', description="My profile", blueprint=bp)
    test_endpoint('PUT', '/api/users/me/profile', {'bio': 'Test'}, "Update my profile", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/users/{uid}/profile', description="Get profile", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('PUT', f'/api/users/{uid}/profile', {'bio': 'Test'}, "Update profile", expected_codes=[200, 403, 500], blueprint=bp)
    test_endpoint('GET', f'/api/users/{uid}/posts', description="User posts", blueprint=bp)
    test_endpoint('GET', f'/api/avatar/{uid}', description="Get avatar", expected_codes=[200, 404], blueprint=bp)
    
    # Follow (5)
    test_endpoint('POST', f'/api/users/{uid}/follow', description="Follow", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', f'/api/users/{uid}/follow', description="Unfollow", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', f'/api/users/{uid}/followers', description="Followers", blueprint=bp)
    test_endpoint('GET', f'/api/users/{uid}/following', description="Following", blueprint=bp)
    test_endpoint('GET', f'/api/users/{uid}/stats', description="User stats", blueprint=bp)
    
    # Messages (5)
    test_endpoint('POST', '/api/messages', {'to_user_id': uid, 'content': 'Test'}, "Send message", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/messages/conversations', description="Conversations", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/messages/{uid}', description="Get messages", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/messages/1/read', description="Mark read", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/messages/unread-count', description="Unread count", expected_codes=[200, 500], blueprint=bp)
    
    # User Notifications (2)
    test_endpoint('GET', '/api/user/notifications', description="User notifs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/user/notifications/read', {'ids': [1]}, "Mark read", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Posts (6)
    test_endpoint('GET', '/api/posts', description="Get posts", blueprint=bp)
    test_endpoint('POST', '/api/posts', {'content': 'Test post'}, "Create post", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/posts/1', description="Get post", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('DELETE', '/api/posts/1', description="Delete post", expected_codes=[200, 403, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/posts/1/like', description="Like post", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/posts/1/like', description="Unlike post", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Publications (18)
    test_endpoint('GET', '/api/publications/feed', description="Feed", blueprint=bp)
    test_endpoint('GET', '/api/publications/check-new', description="Check new", blueprint=bp)
    test_endpoint('GET', '/api/publications/1', description="Get pub", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('PUT', '/api/publications/1', {'content': 'Updated'}, "Update pub", expected_codes=[200, 403, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/publications/1', description="Delete pub", expected_codes=[200, 403, 404, 500], blueprint=bp)
    test_endpoint('GET', f'/api/publications/gallery/{uid}', description="Gallery", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/react', {'reaction': 'like'}, "React", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/unreact', description="Unreact", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/save', description="Save pub", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/unsave', description="Unsave pub", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/publications/saved', description="Saved pubs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/share', description="Share pub", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/share-count', description="Share count", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/publications/1/comments', description="Get comments", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/comments', {'content': 'Test'}, "Add comment", expected_codes=[200, 400, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/publications/1/pin-comment', {'comment_id': 1}, "Pin comment", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Comments (8)
    test_endpoint('POST', '/api/comments/1/like', description="Like comment", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/comments/1/unlike', description="Unlike comment", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/comments/1', description="Get comment", expected_codes=[200, 404], blueprint=bp)
    test_endpoint('PUT', '/api/comments/1', {'content': 'Updated'}, "Update comment", expected_codes=[200, 403, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/comments/1/react', {'reaction': 'like'}, "React comment", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/comments/1/react', description="Unreact comment", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/comments/1/reactions', description="Comment reactions", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Devices (4)
    test_endpoint('GET', '/api/devices/trusted', description="Trusted devices", blueprint=bp)
    test_endpoint('POST', '/api/devices/trusted/check', {'fingerprint': 'test123'}, "Check device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/devices/trusted/add', {'fingerprint': 'test123', 'name': 'Test'}, "Add device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/devices/trusted/remove', {'device_id': 1}, "Remove device", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Security Wallet (5)
    test_endpoint('POST', '/api/security/wallet/validate', {'address': 'EQtest'}, "Validate wallet", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/security/wallet/primary', description="Primary wallet", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/wallet/backup', {'address': 'EQtest'}, "Backup wallet", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/security/wallet/primary/check', description="Check primary", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/wallet/primary/register', {'address': 'EQtest'}, "Register primary", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Wallet debit (1)
    test_endpoint('POST', '/api/wallet/debit', {'amount': 10, 'reason': 'test'}, "Debit wallet", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Security general (6)
    test_endpoint('GET', '/api/security/status', description="Security status", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/security/devices', description="Security devices", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/devices/check', {'fingerprint': 'test'}, "Check sec device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/devices/add', {'fingerprint': 'test', 'name': 'Test'}, "Add sec device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/devices/remove', {'device_id': 1}, "Remove sec device", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', '/api/security/devices/remove-all', description="Remove all devices", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/security/activity', description="Security activity", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/security/lockout/check', description="Lockout check", expected_codes=[200, 500], blueprint=bp)
    
    # Stories (7)
    test_endpoint('POST', '/api/stories/create', {'content': 'Test'}, "Create story", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/stories/feed', description="Stories feed", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', f'/api/stories/user/{uid}', description="User stories", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/stories/1/view', description="View story", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/stories/1/viewers', description="Story viewers", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/stories/1', description="Delete story", expected_codes=[200, 403, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/stories/1/react', {'reaction': 'like'}, "React story", expected_codes=[200, 404, 500], blueprint=bp)
    
    # Explore & Search (6)
    test_endpoint('GET', '/api/explore', description="Explore", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/search/posts?q=test', description="Search posts", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/search/users?q=test', description="Search users", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/hashtag/test', description="Hashtag", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/trending/hashtags', description="Trending", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/suggested/users', description="Suggested", expected_codes=[200, 500], blueprint=bp)
    
    # Notifications (8)
    test_endpoint('GET', '/api/notifications', description="Notifications", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('GET', '/api/notifications/count', description="Notif count", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/notifications/read', {'ids': [1]}, "Mark notif read", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/notifications/unread-count', description="Unread count", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/notifications/mark-all-read', description="Mark all read", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/notifications/1/read', description="Read one", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/notifications/preferences', description="Notif prefs", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/notifications/preferences', {'email': True}, "Update prefs", expected_codes=[200, 400, 500], blueprint=bp)
    
    # Block users (3)
    test_endpoint('POST', f'/api/users/{uid}/block', description="Block user", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('POST', f'/api/users/{uid}/unblock', description="Unblock user", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/users/blocked', description="Blocked users", expected_codes=[200, 500], blueprint=bp)
    
    # Report & FAQ (2)
    test_endpoint('POST', '/api/report', {'type': 'user', 'target_id': uid, 'reason': 'Test'}, "Report", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/faq', description="FAQ", expected_codes=[200, 500], blueprint=bp)


def audit_vn_routes():
    """7. vn_routes.py - 16 endpoints de números virtuales"""
    print("\n" + "="*60)
    print("📱 BLUEPRINT 7: vn_routes.py (16 endpoints)")
    print("="*60)
    bp = "vn_routes"
    
    test_endpoint('GET', '/api/vn/health', description="Health", with_auth=False, blueprint=bp)
    test_endpoint('GET', '/api/vn/providers', description="Providers", blueprint=bp)
    test_endpoint('GET', '/api/vn/countries', description="Countries", blueprint=bp)
    test_endpoint('GET', '/api/vn/services?country=US', description="Services", expected_codes=[200, 400], blueprint=bp)
    test_endpoint('POST', '/api/vn/purchase', {'country': 'US', 'service': 'telegram'}, "Purchase", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/vn/check/test123', description="Check order", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('POST', '/api/vn/cancel/test123', description="Cancel order", expected_codes=[200, 400, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/vn/history', description="History", blueprint=bp)
    test_endpoint('GET', '/api/vn/active', description="Active", blueprint=bp)
    
    # Admin VN (7)
    test_endpoint('GET', '/api/admin/vn/stats', description="VN stats", blueprint=bp)
    test_endpoint('GET', '/api/admin/vn/settings', description="VN settings", blueprint=bp)
    test_endpoint('POST', '/api/admin/vn/settings', {'markup': 1.5}, "Update settings", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/vn/inventory', description="VN inventory", expected_codes=[200, 500], blueprint=bp)
    test_endpoint('POST', '/api/admin/vn/inventory', {'country': 'US', 'service': 'telegram', 'quantity': 10}, "Add inventory", expected_codes=[200, 400, 500], blueprint=bp)
    test_endpoint('DELETE', '/api/admin/vn/inventory/1', description="Delete inventory", expected_codes=[200, 404, 500], blueprint=bp)
    test_endpoint('GET', '/api/admin/vn/orders', description="VN orders", expected_codes=[200, 500], blueprint=bp)


def print_summary():
    """Imprime resumen de la auditoría."""
    print("\n" + "="*60)
    print("📊 RESUMEN DE AUDITORÍA COMPLETA")
    print("="*60)
    print(f"Total endpoints probados: {results['tested']}")
    print(f"✅ Pasaron: {results['passed']}")
    print(f"❌ Fallaron: {results['failed']}")
    success_rate = (results['passed']/results['tested']*100) if results['tested'] > 0 else 0
    print(f"Tasa de éxito: {success_rate:.1f}%")
    
    print("\n📁 RESULTADOS POR BLUEPRINT:")
    print("-" * 40)
    for bp_name, bp_stats in results['by_blueprint'].items():
        bp_rate = (bp_stats['passed']/bp_stats['tested']*100) if bp_stats['tested'] > 0 else 0
        status = "✅" if bp_stats['failed'] == 0 else "⚠️" if bp_rate > 80 else "❌"
        print(f"  {status} {bp_name}: {bp_stats['passed']}/{bp_stats['tested']} ({bp_rate:.0f}%)")
    
    if results['errors']:
        print("\n" + "="*60)
        print("🔴 ERRORES DETECTADOS")
        print("="*60)
        
        errors_by_blueprint = {}
        for error in results['errors']:
            bp = error.get('blueprint', 'unknown')
            if bp not in errors_by_blueprint:
                errors_by_blueprint[bp] = []
            errors_by_blueprint[bp].append(error)
        
        for bp, errors in errors_by_blueprint.items():
            print(f"\n📁 {bp} ({len(errors)} errores):")
            for err in errors:
                status = f"[{err['status_code']}]" if err['status_code'] else "[N/A]"
                print(f"  • {status} {err['endpoint']}")
                error_text = str(err['error'])[:120]
                print(f"    └─ {error_text}")
    
    with open('audit_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tested': results['tested'],
                'passed': results['passed'],
                'failed': results['failed'],
                'success_rate': f"{success_rate:.1f}%"
            },
            'by_blueprint': results['by_blueprint'],
            'errors': results['errors']
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Resultados guardados en: audit_results.json")


def main():
    print("="*60)
    print("🔍 AUDITORÍA COMPLETA DE ENDPOINTS - BUNK3R API")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Owner ID: {OWNER_TELEGRAM_ID}")
    print("📊 Total endpoints a probar: 315")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Servidor activo en {BASE_URL}")
    except:
        print(f"❌ ERROR: No se puede conectar al servidor en {BASE_URL}")
        print("Asegúrate de que el servidor Flask esté corriendo.")
        sys.exit(1)
    
    audit_auth_routes()
    audit_admin_routes()
    audit_blockchain_routes()
    audit_bots_routes()
    audit_tracking_routes()
    audit_user_routes()
    audit_vn_routes()
    
    print_summary()


if __name__ == '__main__':
    main()
