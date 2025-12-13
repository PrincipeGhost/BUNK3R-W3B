#!/usr/bin/env python3
"""
Script de Auditoría Automática de Endpoints - BUNK3R API
Lee dinámicamente todos los endpoints desde los archivos de rutas.
Solo anota errores, NO arregla nada.
"""

import os
import sys
import re
import json
import time
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:5000"
OWNER_TELEGRAM_ID = os.environ.get('OWNER_TELEGRAM_ID', '8305740334')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '') or os.environ.get('TELEGRAM_BOT_TOKEN', '')

ROUTES_DIR = Path(__file__).parent.parent / 'routes'

results = {
    'tested': 0,
    'passed': 0,
    'failed': 0,
    'errors': [],
    'by_blueprint': {},
    'endpoints_found': {}
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


def parse_route_file(file_path):
    """
    Parsea un archivo de rutas y extrae todos los endpoints.
    Retorna lista de diccionarios con info del endpoint.
    """
    endpoints = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️ Error leyendo {file_path}: {e}")
        return endpoints
    
    bp_match = re.search(r"(\w+)_bp\s*=\s*Blueprint\(['\"](\w+)['\"]", content)
    if bp_match:
        bp_name = bp_match.group(2)
    else:
        bp_name = file_path.stem.replace('_routes', '')
    
    bp_prefix_match = re.search(r"url_prefix=['\"]([^'\"]+)['\"]", content)
    bp_prefix = bp_prefix_match.group(1) if bp_prefix_match else ''
    
    route_pattern = r"@\w+_bp\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"
    
    for match in re.finditer(route_pattern, content):
        route_path = match.group(1)
        methods_str = match.group(2)
        
        if methods_str:
            methods = [m.strip().strip("'\"") for m in methods_str.split(',')]
        else:
            methods = ['GET']
        
        full_path = bp_prefix + route_path if not route_path.startswith(bp_prefix) else route_path
        
        for method in methods:
            endpoints.append({
                'method': method.upper(),
                'path': full_path,
                'blueprint': bp_name,
                'file': file_path.name
            })
    
    return endpoints


def discover_all_endpoints():
    """Descubre todos los endpoints de todos los archivos de rutas."""
    all_endpoints = []
    
    if not ROUTES_DIR.exists():
        print(f"❌ Directorio de rutas no encontrado: {ROUTES_DIR}")
        return all_endpoints
    
    print("\n📂 Escaneando archivos de rutas...")
    print("-" * 40)
    
    for route_file in sorted(ROUTES_DIR.glob('*_routes.py')):
        endpoints = parse_route_file(route_file)
        all_endpoints.extend(endpoints)
        
        bp_name = route_file.stem
        results['endpoints_found'][bp_name] = len(endpoints)
        print(f"  📄 {route_file.name}: {len(endpoints)} endpoints")
    
    print("-" * 40)
    print(f"  📊 Total endpoints descubiertos: {len(all_endpoints)}")
    
    return all_endpoints


def prepare_test_url(path):
    """
    Prepara la URL para testing, reemplazando parámetros dinámicos.
    """
    uid = OWNER_TELEGRAM_ID
    
    path = re.sub(r'<(?:int:)?user_id>', uid, path)
    path = re.sub(r'<(?:int:)?other_user_id>', uid, path)
    path = re.sub(r'<(?:int:)?telegram_id>', uid, path)
    
    path = re.sub(r'<(?:int:)?post_id>', '1', path)
    path = re.sub(r'<(?:int:)?message_id>', '1', path)
    path = re.sub(r'<(?:int:)?transaction_id>', '1', path)
    path = re.sub(r'<(?:int:)?ticket_id>', '1', path)
    path = re.sub(r'<(?:int:)?id>', '1', path)
    
    path = re.sub(r'<\w+_id>', 'test123', path)
    path = re.sub(r'<\w+>', 'test', path)
    
    return path


def get_test_data(method, path):
    """
    Genera datos de prueba apropiados según el endpoint.
    """
    if method == 'GET':
        return None
    
    if 'login' in path or 'auth' in path or 'validate' in path:
        return {'initData': generate_telegram_init_data()}
    
    if 'message' in path:
        return {'content': 'Test message', 'message': 'Test'}
    
    if 'balance' in path or 'credits' in path:
        return {'amount': 0}
    
    if 'ban' in path:
        return {'banned': False}
    
    if 'note' in path:
        return {'note': 'Test note'}
    
    if 'tags' in path:
        return {'tags': ['test']}
    
    if '2fa' in path or 'verify' in path:
        return {'code': '123456'}
    
    if 'config' in path or 'settings' in path:
        return {'key': 'test', 'value': 'test'}
    
    if 'ticket' in path:
        return {'status': 'open', 'message': 'Test'}
    
    if 'faq' in path:
        return {'question': 'Test?', 'answer': 'Test'}
    
    if 'product' in path:
        return {'name': 'Test', 'price': 10}
    
    if 'bot' in path:
        return {'name': 'Test', 'type': 'test'}
    
    if 'ip' in path or 'blacklist' in path:
        return {'ip': '1.2.3.4', 'reason': 'Test'}
    
    if 'withdraw' in path:
        return {'amount': 0, 'address': 'test'}
    
    if 'transfer' in path:
        return {'to_user_id': OWNER_TELEGRAM_ID, 'amount': 0}
    
    if 'deposit' in path:
        return {'amount': 0}
    
    if 'post' in path or 'publication' in path:
        return {'content': 'Test post'}
    
    if 'comment' in path:
        return {'content': 'Test comment'}
    
    if 'react' in path:
        return {'reaction': 'like'}
    
    if 'follow' in path:
        return {}
    
    if 'notify' in path:
        return {'message': 'Test notification'}
    
    if 'session' in path:
        return {'session_id': 'test'}
    
    if 'template' in path:
        return {'name': 'Test', 'content': 'Test template'}
    
    if 'report' in path:
        return {'reason': 'Test report'}
    
    if 'action' in path:
        return {'action': 'approve'}
    
    return {}


def test_endpoint(method, url, data=None, description="", with_auth=True, expected_codes=None, blueprint="unknown"):
    """Prueba un endpoint y registra resultado."""
    if expected_codes is None:
        expected_codes = [200, 201, 204, 400, 401, 403, 404, 500]
    
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
        elif method == 'PATCH':
            response = requests.patch(full_url, json=data or {}, headers=headers, timeout=10)
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
            return False
        
        if response.status_code < 500:
            results['passed'] += 1
            results['by_blueprint'][blueprint]['passed'] += 1
            print(f"  ✅ {method} {url} -> {response.status_code}")
            return True
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
            return False
            
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
        return False
        
    except requests.exceptions.ConnectionError:
        results['failed'] += 1
        results['by_blueprint'][blueprint]['failed'] += 1
        results['errors'].append({
            'endpoint': f"{method} {url}",
            'blueprint': blueprint,
            'description': description,
            'error': "CONNECTION ERROR",
            'status_code': None
        })
        print(f"  🔌 {method} {url} -> CONNECTION ERROR")
        return False
        
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
        return False


def audit_blueprint(bp_name, endpoints):
    """Audita todos los endpoints de un blueprint."""
    print(f"\n{'='*60}")
    print(f"📁 BLUEPRINT: {bp_name} ({len(endpoints)} endpoints)")
    print("="*60)
    
    for ep in endpoints:
        method = ep['method']
        path = ep['path']
        
        test_url = prepare_test_url(path)
        test_data = get_test_data(method, path)
        
        with_auth = not any(x in path.lower() for x in ['health', 'demo', 'public'])
        
        test_endpoint(
            method=method,
            url=test_url,
            data=test_data,
            description=f"{method} {path}",
            with_auth=with_auth,
            blueprint=bp_name
        )


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
        print("🔴 ERRORES DETECTADOS (HTTP 500+)")
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
    
    output_file = Path(__file__).parent / 'audit_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tested': results['tested'],
                'passed': results['passed'],
                'failed': results['failed'],
                'success_rate': f"{success_rate:.1f}%"
            },
            'endpoints_discovered': results['endpoints_found'],
            'by_blueprint': results['by_blueprint'],
            'errors': results['errors']
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Resultados guardados en: {output_file}")


def main():
    print("="*60)
    print("🔍 AUDITORÍA AUTOMÁTICA DE ENDPOINTS - BUNK3R API")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Owner ID: {OWNER_TELEGRAM_ID}")
    print(f"📂 Directorio de rutas: {ROUTES_DIR}")
    print("="*60)
    
    all_endpoints = discover_all_endpoints()
    
    if not all_endpoints:
        print("\n❌ No se encontraron endpoints para auditar.")
        sys.exit(1)
    
    print(f"\n📊 Total endpoints a probar: {len(all_endpoints)}")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Servidor activo en {BASE_URL}")
    except:
        print(f"❌ ERROR: No se puede conectar al servidor en {BASE_URL}")
        print("Asegúrate de que el servidor Flask esté corriendo.")
        sys.exit(1)
    
    endpoints_by_bp = {}
    for ep in all_endpoints:
        bp = ep['blueprint']
        if bp not in endpoints_by_bp:
            endpoints_by_bp[bp] = []
        endpoints_by_bp[bp].append(ep)
    
    for bp_name in sorted(endpoints_by_bp.keys()):
        audit_blueprint(bp_name, endpoints_by_bp[bp_name])
    
    print_summary()


if __name__ == '__main__':
    main()
