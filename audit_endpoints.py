#!/usr/bin/env python3
"""
Script de Auditoría de Endpoints - BUNK3R API
Prueba TODOS los endpoints de TODOS los blueprints.
Solo anota errores, NO arregla nada.

Blueprints:
1. auth_routes.py
2. admin_routes.py
3. blockchain_routes.py
4. bots_routes.py
5. tracking_routes.py
6. user_routes.py
7. vn_routes.py
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
    'errors': []
}


def generate_telegram_init_data(user_id=None):
    """Genera initData VÁLIDO para autenticación Telegram según documentación oficial."""
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
        print("⚠️ BOT_TOKEN no disponible - no se puede generar hash válido")
        hash_value = "invalid_no_bot_token"
    
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


def test_endpoint(method, url, data=None, description="", with_auth=True, expected_codes=[200]):
    """Prueba un endpoint y registra resultado."""
    results['tested'] += 1
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
            results['errors'].append({
                'endpoint': f"{method} {url}",
                'description': description,
                'error': f"Método no soportado: {method}",
                'status_code': None
            })
            return
        
        if response.status_code in expected_codes:
            results['passed'] += 1
            print(f"  ✅ {method} {url} -> {response.status_code}")
        else:
            results['failed'] += 1
            try:
                resp_json = response.json()
                error_msg = resp_json.get('error', resp_json.get('message', str(resp_json)[:200]))
            except:
                error_msg = response.text[:200]
            
            results['errors'].append({
                'endpoint': f"{method} {url}",
                'description': description,
                'error': error_msg,
                'status_code': response.status_code
            })
            print(f"  ❌ {method} {url} -> {response.status_code}: {error_msg[:100]}")
            
    except requests.exceptions.Timeout:
        results['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'description': description,
            'error': "TIMEOUT - Request tardó más de 10 segundos",
            'status_code': None
        })
        print(f"  ⏱️ {method} {url} -> TIMEOUT")
        
    except requests.exceptions.ConnectionError as e:
        results['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'description': description,
            'error': f"CONNECTION ERROR: {str(e)[:100]}",
            'status_code': None
        })
        print(f"  🔌 {method} {url} -> CONNECTION ERROR")
        
    except Exception as e:
        results['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'description': description,
            'error': f"EXCEPTION: {str(e)[:200]}",
            'status_code': None
        })
        print(f"  💥 {method} {url} -> EXCEPTION: {str(e)[:50]}")


def audit_auth_routes():
    """1. auth_routes.py - Endpoints de autenticación y 2FA"""
    print("\n" + "="*60)
    print("🔐 BLUEPRINT 1: auth_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/auth/health', description="Health check auth", with_auth=False)
    test_endpoint('POST', '/api/demo/2fa/verify', {'code': '110917'}, "Demo 2FA verify", with_auth=False, expected_codes=[200, 403])
    test_endpoint('POST', '/api/demo/2fa/logout', description="Demo 2FA logout", with_auth=False, expected_codes=[200, 403])
    test_endpoint('POST', '/api/2fa/status', description="2FA status")
    test_endpoint('POST', '/api/2fa/setup', description="2FA setup")
    test_endpoint('POST', '/api/2fa/verify', {'code': '123456'}, "2FA verify", expected_codes=[200, 400, 401])
    test_endpoint('POST', '/api/2fa/session', description="2FA session check")
    test_endpoint('POST', '/api/2fa/refresh', description="2FA refresh session")
    test_endpoint('POST', '/api/2fa/disable', {'code': '123456'}, "2FA disable", expected_codes=[200, 400, 401])
    test_endpoint('POST', '/api/validate', {'initData': generate_telegram_init_data()}, "Validate user", with_auth=False)


def audit_admin_routes():
    """2. admin_routes.py - Endpoints de administración"""
    print("\n" + "="*60)
    print("👑 BLUEPRINT 2: admin_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/admin/health', description="Health check admin")
    test_endpoint('GET', '/api/admin/dashboard/stats', description="Dashboard stats")
    test_endpoint('GET', '/api/admin/dashboard/activity', description="Dashboard activity")
    test_endpoint('GET', '/api/admin/dashboard/alerts', description="Dashboard alerts")
    test_endpoint('GET', '/api/admin/dashboard/charts', description="Dashboard charts")
    
    test_user_id = OWNER_TELEGRAM_ID
    test_endpoint('GET', f'/api/admin/users/{test_user_id}/detail', description="User detail")
    test_endpoint('GET', f'/api/admin/users/{test_user_id}/risk-score', description="User risk score")
    test_endpoint('GET', f'/api/admin/users/{test_user_id}/related-accounts', description="Related accounts")
    test_endpoint('POST', f'/api/admin/users/{test_user_id}/risk-score/calculate', description="Calculate risk score")
    test_endpoint('GET', f'/api/admin/users/{test_user_id}/risk-score/history', description="Risk score history")
    
    test_endpoint('GET', '/api/admin/users', description="List users")
    test_endpoint('GET', '/api/admin/users/export', description="Export users")
    test_endpoint('GET', f'/api/admin/user/{test_user_id}', description="Get single user")
    
    test_endpoint('GET', '/api/admin/stats', description="Admin stats")
    test_endpoint('GET', '/api/admin/stats/overview', description="Stats overview")
    test_endpoint('GET', '/api/admin/stats/users', description="Stats users")
    test_endpoint('GET', '/api/admin/stats/transactions', description="Stats transactions")
    
    test_endpoint('GET', '/api/admin/security/users', description="Security users")
    test_endpoint('GET', f'/api/admin/security/user/{test_user_id}/devices', description="User devices")
    test_endpoint('GET', f'/api/admin/security/user/{test_user_id}/activity', description="User activity")
    test_endpoint('GET', '/api/admin/security/alerts', description="Security alerts")
    test_endpoint('GET', '/api/admin/security/statistics', description="Security statistics")
    
    test_endpoint('GET', '/api/admin/financial/stats', description="Financial stats")
    test_endpoint('GET', '/api/admin/financial/period-stats', description="Period stats")
    
    test_endpoint('GET', '/api/admin/logs/admin', description="Admin logs")
    test_endpoint('GET', '/api/admin/logs/security', description="Security logs")
    test_endpoint('GET', '/api/admin/logs/errors', description="Error logs")
    test_endpoint('GET', '/api/admin/logs/logins', description="Login logs")
    test_endpoint('GET', '/api/admin/logs/config-history', description="Config history")
    
    test_endpoint('GET', '/api/admin/config', description="Get config")
    
    test_endpoint('GET', '/api/admin/analytics/users', description="Analytics users")
    test_endpoint('GET', '/api/admin/analytics/usage', description="Analytics usage")
    test_endpoint('GET', '/api/admin/analytics/conversion', description="Analytics conversion")
    
    test_endpoint('GET', '/api/admin/support/tickets', description="Support tickets")
    test_endpoint('GET', '/api/admin/support/templates', description="Support templates")
    
    test_endpoint('GET', '/api/admin/faq', description="FAQ list")
    
    test_endpoint('GET', '/api/admin/promotional-codes', description="Promo codes")
    
    test_endpoint('GET', '/api/admin/transactions', description="Transactions")
    test_endpoint('GET', '/api/admin/transactions/pending', description="Pending transactions")
    test_endpoint('GET', '/api/admin/transactions/charts', description="Transaction charts")
    test_endpoint('GET', '/api/admin/transactions/export', description="Export transactions")


def audit_blockchain_routes():
    """3. blockchain_routes.py - Endpoints de blockchain/crypto"""
    print("\n" + "="*60)
    print("⛓️ BLUEPRINT 3: blockchain_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/blockchain/health', description="Health check blockchain", with_auth=False)
    
    test_endpoint('GET', '/api/exchange/currencies', description="Exchange currencies", with_auth=False)
    test_endpoint('GET', '/api/exchange/min-amount?from=btc&to=ton', description="Exchange min amount", with_auth=False)
    test_endpoint('GET', '/api/exchange/estimate?from=btc&to=ton&amount=0.01', description="Exchange estimate", with_auth=False)
    test_endpoint('POST', '/api/exchange/create', {'from': 'btc', 'to': 'ton', 'amount': 0.01, 'address': 'test'}, "Exchange create", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/exchange/status/test123', description="Exchange status", expected_codes=[200, 404, 500])
    
    test_endpoint('POST', '/api/ton/payment/create', {'amount': 1}, "TON payment create", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/ton/wallet-info', description="TON wallet info")
    
    test_endpoint('GET', '/api/wallet/merchant', description="Wallet merchant")
    test_endpoint('GET', '/api/wallet/balance', description="Wallet balance")
    test_endpoint('GET', '/api/wallet/address', description="Wallet address")
    test_endpoint('POST', '/api/wallet/connect', {'address': 'test_wallet'}, "Wallet connect", expected_codes=[200, 400, 500])
    
    test_endpoint('GET', '/api/b3c/price', description="B3C price", with_auth=False)
    test_endpoint('POST', '/api/b3c/calculate/buy', {'amount': 100}, "B3C calculate buy")
    test_endpoint('POST', '/api/b3c/calculate/sell', {'amount': 100}, "B3C calculate sell")
    test_endpoint('GET', '/api/b3c/balance', description="B3C balance")
    test_endpoint('GET', '/api/b3c/config', description="B3C config", with_auth=False)
    test_endpoint('GET', '/api/b3c/network', description="B3C network", with_auth=False)
    test_endpoint('GET', '/api/b3c/testnet/guide', description="B3C testnet guide", with_auth=False)
    test_endpoint('POST', '/api/b3c/buy/create', {'amount_usd': 10}, "B3C buy create", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/b3c/transactions', description="B3C transactions")
    test_endpoint('GET', '/api/b3c/commissions', description="B3C commissions")
    test_endpoint('GET', '/api/b3c/deposit/address', description="B3C deposit address")
    test_endpoint('GET', '/api/b3c/deposits/history', description="B3C deposits history")
    test_endpoint('GET', '/api/b3c/deposits/pending', description="B3C deposits pending")
    test_endpoint('GET', '/api/b3c/scheduler/status', description="B3C scheduler status")
    test_endpoint('GET', '/api/b3c/wallet-pool/stats', description="B3C wallet pool stats")


def audit_bots_routes():
    """4. bots_routes.py - Endpoints de bots"""
    print("\n" + "="*60)
    print("🤖 BLUEPRINT 4: bots_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/bots/health', description="Health check bots", with_auth=False)
    test_endpoint('POST', '/api/bots/init', description="Init bots")
    test_endpoint('GET', '/api/bots/my', description="My bots")
    test_endpoint('GET', '/api/bots/available', description="Available bots")
    test_endpoint('POST', '/api/bots/purchase', {'botType': 'test_bot'}, "Purchase bot", expected_codes=[200, 400, 500])
    test_endpoint('POST', '/api/bots/1/remove', description="Remove bot", expected_codes=[200, 500])
    test_endpoint('POST', '/api/bots/1/toggle', description="Toggle bot", expected_codes=[200, 500])
    test_endpoint('GET', '/api/bots/1/config', description="Get bot config", expected_codes=[200, 404])
    test_endpoint('POST', '/api/bots/1/config', {'config': {}}, "Update bot config", expected_codes=[200, 404, 500])


def audit_tracking_routes():
    """5. tracking_routes.py - Endpoints de tracking"""
    print("\n" + "="*60)
    print("📦 BLUEPRINT 5: tracking_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/tracking/health', description="Health check tracking", with_auth=False)
    test_endpoint('GET', '/api/trackings', description="List trackings")
    test_endpoint('GET', '/api/stats', description="Tracking stats")
    test_endpoint('GET', '/api/delay-reasons', description="Delay reasons")
    test_endpoint('GET', '/api/statuses', description="Available statuses")
    
    test_endpoint('POST', '/api/tracking', {
        'trackingId': 'TEST123456789',
        'recipientName': 'Test User',
        'productName': 'Test Product'
    }, "Create tracking", expected_codes=[200, 400, 500])
    
    test_endpoint('GET', '/api/tracking/TEST123456789', description="Get tracking", expected_codes=[200, 404])
    test_endpoint('PUT', '/api/tracking/TEST123456789', {'recipientName': 'Updated'}, "Update tracking", expected_codes=[200, 400, 404])
    test_endpoint('PUT', '/api/tracking/TEST123456789/status', {'status': 'EN_TRANSITO'}, "Update status", expected_codes=[200, 400, 404])
    test_endpoint('POST', '/api/tracking/TEST123456789/delay', {'days': 1, 'reason': 'Test'}, "Add delay", expected_codes=[200, 500])
    test_endpoint('POST', '/api/tracking/TEST123456789/email', {'email': 'test@test.com', 'bankEntity': 'Test', 'iban': 'ES123'}, "Send email", expected_codes=[200, 400, 404, 500])
    test_endpoint('DELETE', '/api/tracking/TEST123456789', description="Delete tracking", expected_codes=[200, 404])


def audit_user_routes():
    """6. user_routes.py - Endpoints de usuario"""
    print("\n" + "="*60)
    print("👤 BLUEPRINT 6: user_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/user/health', description="Health check user", with_auth=False)
    
    test_endpoint('GET', '/api/users/me', description="Get me")
    test_endpoint('GET', '/api/users/me/profile', description="Get my profile")
    test_endpoint('GET', '/api/users/me/avatar', description="Get my avatar")
    
    test_user_id = OWNER_TELEGRAM_ID
    test_endpoint('GET', f'/api/users/{test_user_id}/profile', description="Get user profile")
    test_endpoint('GET', f'/api/users/{test_user_id}/posts', description="Get user posts")
    test_endpoint('GET', f'/api/users/{test_user_id}/followers', description="Get followers")
    test_endpoint('GET', f'/api/users/{test_user_id}/following', description="Get following")
    test_endpoint('GET', f'/api/users/{test_user_id}/stats', description="Get user stats")
    
    test_endpoint('GET', '/api/messages/unread-count', description="Unread messages count")
    test_endpoint('GET', '/api/conversations', description="Conversations")
    
    test_endpoint('GET', '/api/posts', description="Get posts")
    test_endpoint('GET', '/api/publications/feed', description="Publications feed")
    test_endpoint('GET', '/api/publications/check-new', description="Check new publications")
    
    test_endpoint('GET', '/api/devices/trusted', description="Trusted devices")
    
    test_endpoint('GET', '/api/security/wallet/settings', description="Wallet security settings")


def audit_vn_routes():
    """7. vn_routes.py - Endpoints de números virtuales"""
    print("\n" + "="*60)
    print("📱 BLUEPRINT 7: vn_routes.py")
    print("="*60)
    
    test_endpoint('GET', '/api/vn/health', description="Health check VN", with_auth=False)
    test_endpoint('GET', '/api/vn/providers', description="VN providers")
    test_endpoint('GET', '/api/vn/countries', description="VN countries")
    test_endpoint('GET', '/api/vn/services', description="VN services")
    test_endpoint('POST', '/api/vn/purchase', {'country': 'US', 'service': 'test'}, "VN purchase", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/vn/check/test123', description="VN check", expected_codes=[200, 404, 500])
    test_endpoint('GET', '/api/vn/history', description="VN history")
    test_endpoint('GET', '/api/vn/active', description="VN active")
    test_endpoint('POST', '/api/vn/cancel/test123', description="VN cancel", expected_codes=[200, 400, 404, 500])
    
    test_endpoint('GET', '/api/admin/vn/stats', description="Admin VN stats")
    test_endpoint('GET', '/api/admin/vn/settings', description="Admin VN settings")
    test_endpoint('POST', '/api/admin/vn/settings', {'key': 'value'}, "Admin VN update settings", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/admin/vn/inventory', description="Admin VN inventory")
    test_endpoint('POST', '/api/admin/vn/inventory', {'item': 'test'}, "Admin VN add inventory", expected_codes=[200, 400, 500])
    test_endpoint('GET', '/api/admin/vn/orders', description="Admin VN orders")


def print_summary():
    """Imprime resumen de la auditoría."""
    print("\n" + "="*60)
    print("📊 RESUMEN DE AUDITORÍA")
    print("="*60)
    print(f"Total endpoints probados: {results['tested']}")
    print(f"✅ Pasaron: {results['passed']}")
    print(f"❌ Fallaron: {results['failed']}")
    print(f"Tasa de éxito: {(results['passed']/results['tested']*100):.1f}%" if results['tested'] > 0 else "N/A")
    
    if results['errors']:
        print("\n" + "="*60)
        print("🔴 ERRORES DETECTADOS")
        print("="*60)
        
        errors_by_blueprint = {}
        for error in results['errors']:
            endpoint = error['endpoint']
            if '/api/auth/' in endpoint or '/api/demo/' in endpoint or '/api/2fa/' in endpoint or '/api/validate' in endpoint:
                bp = 'auth_routes'
            elif '/api/admin/' in endpoint:
                bp = 'admin_routes'
            elif '/api/blockchain/' in endpoint or '/api/exchange/' in endpoint or '/api/ton/' in endpoint or '/api/wallet/' in endpoint or '/api/b3c/' in endpoint:
                bp = 'blockchain_routes'
            elif '/api/bots/' in endpoint:
                bp = 'bots_routes'
            elif '/api/tracking' in endpoint or '/api/stats' in endpoint or '/api/delay' in endpoint or '/api/statuses' in endpoint:
                bp = 'tracking_routes'
            elif '/api/user' in endpoint or '/api/messages' in endpoint or '/api/posts' in endpoint or '/api/publications' in endpoint or '/api/devices' in endpoint or '/api/security/wallet' in endpoint or '/api/conversations' in endpoint:
                bp = 'user_routes'
            elif '/api/vn/' in endpoint or '/api/admin/vn/' in endpoint:
                bp = 'vn_routes'
            else:
                bp = 'unknown'
            
            if bp not in errors_by_blueprint:
                errors_by_blueprint[bp] = []
            errors_by_blueprint[bp].append(error)
        
        for bp, errors in errors_by_blueprint.items():
            print(f"\n📁 {bp} ({len(errors)} errores):")
            for err in errors:
                status = f"[{err['status_code']}]" if err['status_code'] else "[N/A]"
                print(f"  • {status} {err['endpoint']}")
                print(f"    └─ {err['error'][:150]}")
    
    with open('audit_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tested': results['tested'],
                'passed': results['passed'],
                'failed': results['failed'],
                'success_rate': f"{(results['passed']/results['tested']*100):.1f}%" if results['tested'] > 0 else "N/A"
            },
            'errors': results['errors']
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Resultados guardados en: audit_results.json")


def main():
    print("="*60)
    print("🔍 AUDITORÍA COMPLETA DE ENDPOINTS - BUNK3R API")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Owner ID: {OWNER_TELEGRAM_ID}")
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
