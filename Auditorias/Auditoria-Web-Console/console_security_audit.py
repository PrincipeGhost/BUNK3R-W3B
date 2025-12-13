#!/usr/bin/env python3
"""
=============================================================================
AUDITORÍA DE SEGURIDAD WEB CONSOLE - MASIVA
=============================================================================
Script de auditoría enfocado en vulnerabilidades detectables desde
la consola del navegador (DevTools) - 100+ pruebas en 20 bloques

Simula lo que un atacante buscaría en:
- Console (errores JS)
- Network (tráfico)
- Application (storage, cookies)
- Sources (código JS)
- Elements (DOM)

Autor: Console Security Audit Tool
Versión: 1.0
=============================================================================
"""

import os
import re
import json
import time
import base64
import hashlib
import urllib.parse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    os.system("pip install requests")
    import requests

# Configuración
BASE_URL = os.environ.get("AUDIT_TARGET_URL", "http://localhost:5000")
TIMEOUT = 10
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Resultados
results = {
    "metadata": {
        "target": BASE_URL,
        "date": datetime.now().isoformat(),
        "total_tests": 100,
        "blocks": 20,
        "type": "Console Security Audit"
    },
    "summary": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    },
    "findings": []
}

def add_finding(block: str, test: str, severity: str, description: str,
                details: str = "", recommendation: str = "", evidence: str = ""):
    """Agrega un hallazgo al reporte"""
    finding = {
        "block": block,
        "test": test,
        "severity": severity,
        "description": description,
        "details": details,
        "recommendation": recommendation,
        "evidence": evidence[:1000] if evidence else "",
        "timestamp": datetime.now().isoformat()
    }
    results["findings"].append(finding)
    
    if severity.lower() in results["summary"]:
        results["summary"][severity.lower()] += 1
    
    icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
    print(f"  {icons.get(severity.lower(), '⚪')} [{severity.upper()}] {test}: {description[:80]}")

def safe_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """Request seguro con manejo de errores"""
    try:
        kwargs.setdefault("timeout", TIMEOUT)
        kwargs.setdefault("verify", False)
        kwargs.setdefault("allow_redirects", True)
        return requests.request(method, url, **kwargs)
    except:
        return None

def get_all_js_files() -> List[str]:
    """Obtiene todos los archivos JS del proyecto"""
    js_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT / "static"):
        dirs[:] = [d for d in dirs if d not in ["node_modules", ".git"]]
        for file in files:
            if file.endswith((".js", ".jsx", ".ts", ".tsx")):
                js_files.append(os.path.join(root, file))
    return js_files

def get_all_html_files() -> List[str]:
    """Obtiene todos los archivos HTML/templates"""
    html_files = []
    for folder in ["templates", "static"]:
        folder_path = PROJECT_ROOT / folder
        if folder_path.exists():
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith((".html", ".htm", ".jinja", ".jinja2")):
                        html_files.append(os.path.join(root, file))
    return html_files

# =============================================================================
# BLOQUE 1: ERRORES DE JAVASCRIPT
# =============================================================================
def audit_block_1():
    """Analiza errores de JavaScript que exponen información"""
    print(f"\n{'='*60}\n📁 BLOQUE 1: ERRORES DE JAVASCRIPT\n{'='*60}")
    
    js_files = get_all_js_files()
    
    # Patrones de código propenso a errores
    error_patterns = {
        "undefined_access": (r'\w+\.\w+\.\w+\.\w+', "Acceso profundo a objetos sin validación"),
        "throw_with_info": (r'throw\s+new\s+Error\([^)]*\+[^)]*\)', "Throw con concatenación de info"),
        "console_error": (r'console\.(error|warn|log)\([^)]*\)', "Console output (puede exponer datos)"),
        "eval_usage": (r'\beval\s*\(', "Uso de eval() - peligroso"),
        "innerhtml": (r'\.innerHTML\s*=', "innerHTML sin sanitizar - riesgo XSS"),
        "document_write": (r'document\.write\s*\(', "document.write - riesgo XSS"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in error_patterns.items():
                    matches = re.findall(pattern, content)
                    if matches:
                        severity = "high" if pattern_name in ["eval_usage", "innerhtml"] else "medium"
                        add_finding("Bloque 1", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   details=f"Encontradas {len(matches)} ocurrencias",
                                   recommendation="Revisar y corregir el código para evitar exposición de información")
        except:
            pass
    
    # Verificar try-catch vacíos o con console
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                # Catch vacío
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', content):
                    add_finding("Bloque 1", "empty_catch", "medium",
                               f"Catch vacío en {rel_path}",
                               recommendation="Manejar errores apropiadamente")
                
                # Catch que solo hace console.log
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*console\.(log|error)', content):
                    add_finding("Bloque 1", "console_in_catch", "low",
                               f"Console en catch en {rel_path}",
                               recommendation="Evitar exponer errores en producción")
        except:
            pass

# =============================================================================
# BLOQUE 2: VARIABLES GLOBALES
# =============================================================================
def audit_block_2():
    """Analiza variables globales expuestas"""
    print(f"\n{'='*60}\n📁 BLOQUE 2: VARIABLES GLOBALES\n{'='*60}")
    
    js_files = get_all_js_files()
    
    # Patrones de variables globales sensibles
    global_patterns = {
        "window_token": (r'window\.(token|apiKey|api_key|secret|password|auth)', "Token/secreto en window"),
        "global_config": (r'(var|let|const)\s+(config|CONFIG|settings|SETTINGS)\s*=\s*\{', "Configuración global expuesta"),
        "global_user": (r'window\.(user|currentUser|userData|userInfo)', "Datos de usuario en window"),
        "debug_flag": (r'(DEBUG|debug|isDebug|IS_DEBUG)\s*[=:]\s*true', "Flag de debug activo"),
        "api_url": (r'(API_URL|apiUrl|BASE_URL|baseUrl)\s*[=:]\s*["\']', "URL de API expuesta"),
        "credentials": (r'(username|password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']', "Credenciales en código"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in global_patterns.items():
                    if re.search(pattern, content, re.I):
                        severity = "critical" if pattern_name in ["credentials", "window_token"] else "high"
                        add_finding("Bloque 2", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   recommendation="Mover datos sensibles al backend")
        except:
            pass

# =============================================================================
# BLOQUE 3: LOCALSTORAGE/SESSIONSTORAGE
# =============================================================================
def audit_block_3():
    """Analiza uso de localStorage/sessionStorage"""
    print(f"\n{'='*60}\n📁 BLOQUE 3: LOCALSTORAGE/SESSIONSTORAGE\n{'='*60}")
    
    js_files = get_all_js_files()
    
    storage_patterns = {
        "store_token": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*token', "Token guardado en storage"),
        "store_password": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*password', "Password en storage"),
        "store_user": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*user', "Datos de usuario en storage"),
        "store_auth": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*auth', "Auth data en storage"),
        "store_key": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*key', "Key en storage"),
        "store_secret": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*secret', "Secreto en storage"),
        "store_credit": (r'(localStorage|sessionStorage)\.setItem\s*\([^)]*(card|credit|payment)', "Datos de pago en storage"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in storage_patterns.items():
                    if re.search(pattern, content, re.I):
                        severity = "critical" if "password" in pattern_name or "credit" in pattern_name else "high"
                        add_finding("Bloque 3", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   recommendation="No almacenar datos sensibles en storage del navegador")
        except:
            pass
    
    # Verificar si hay JSON.stringify de objetos sensibles
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                if re.search(r'JSON\.stringify\s*\([^)]*\)\s*\)', content) and \
                   re.search(r'(localStorage|sessionStorage)\.setItem', content):
                    add_finding("Bloque 3", "json_to_storage", "medium",
                               f"Objetos JSON almacenados en storage en {rel_path}",
                               recommendation="Verificar qué datos se serializan")
        except:
            pass

# =============================================================================
# BLOQUE 4: COOKIES
# =============================================================================
def audit_block_4():
    """Analiza seguridad de cookies"""
    print(f"\n{'='*60}\n📁 BLOQUE 4: COOKIES\n{'='*60}")
    
    response = safe_request("GET", BASE_URL)
    if not response:
        add_finding("Bloque 4", "no_connection", "critical", "No se puede conectar al servidor")
        return
    
    # Analizar Set-Cookie headers
    set_cookies = response.headers.get("Set-Cookie", "")
    if set_cookies:
        cookies_list = set_cookies.split(",")
        for cookie in cookies_list:
            cookie_lower = cookie.lower()
            
            if "httponly" not in cookie_lower:
                add_finding("Bloque 4", "missing_httponly", "high",
                           "Cookie sin flag HttpOnly",
                           evidence=cookie[:100],
                           recommendation="Agregar HttpOnly a todas las cookies de sesión")
            
            if "secure" not in cookie_lower:
                add_finding("Bloque 4", "missing_secure", "high",
                           "Cookie sin flag Secure",
                           evidence=cookie[:100],
                           recommendation="Agregar Secure flag para cookies en HTTPS")
            
            if "samesite" not in cookie_lower:
                add_finding("Bloque 4", "missing_samesite", "medium",
                           "Cookie sin flag SameSite",
                           evidence=cookie[:100],
                           recommendation="Agregar SameSite=Strict o SameSite=Lax")
    
    # Analizar cookies en respuesta
    for cookie in response.cookies:
        if not cookie.secure:
            add_finding("Bloque 4", "insecure_cookie", "high",
                       f"Cookie '{cookie.name}' sin Secure flag")
        
        if "session" in cookie.name.lower() or "token" in cookie.name.lower():
            if len(cookie.value) < 32:
                add_finding("Bloque 4", "weak_session", "critical",
                           f"Cookie de sesión '{cookie.name}' muy corta ({len(cookie.value)} chars)",
                           recommendation="Usar tokens de al menos 128 bits")
            
            if cookie.value.isdigit():
                add_finding("Bloque 4", "predictable_session", "critical",
                           f"Cookie '{cookie.name}' es numérica y predecible",
                           recommendation="Usar generador criptográficamente seguro")

# =============================================================================
# BLOQUE 5: NETWORK REQUESTS
# =============================================================================
def audit_block_5():
    """Analiza seguridad de requests de red"""
    print(f"\n{'='*60}\n📁 BLOQUE 5: NETWORK REQUESTS\n{'='*60}")
    
    js_files = get_all_js_files()
    
    # Buscar endpoints en código JS
    endpoint_patterns = [
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'axios\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'\$\.(get|post|ajax)\s*\(\s*["\']([^"\']+)["\']',
        r'XMLHttpRequest[^;]*open\s*\([^,]*,\s*["\']([^"\']+)["\']',
        r'url\s*[=:]\s*["\']([^"\']+/api/[^"\']+)["\']',
    ]
    
    discovered_endpoints = set()
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern in endpoint_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        endpoint = match[-1] if isinstance(match, tuple) else match
                        if endpoint.startswith("/") or "api" in endpoint.lower():
                            discovered_endpoints.add(endpoint)
        except:
            pass
    
    # Probar endpoints descubiertos
    for endpoint in list(discovered_endpoints)[:20]:
        if endpoint.startswith("/"):
            full_url = f"{BASE_URL}{endpoint}"
        else:
            full_url = endpoint
        
        response = safe_request("GET", full_url)
        if response:
            # Verificar si responde sin auth
            if response.status_code == 200:
                add_finding("Bloque 5", "endpoint_no_auth", "high",
                           f"Endpoint {endpoint} accesible sin autenticación",
                           recommendation="Implementar autenticación en endpoints sensibles")
            
            # Buscar tokens en URL
            if "token=" in full_url or "key=" in full_url or "api_key=" in full_url:
                add_finding("Bloque 5", "token_in_url", "critical",
                           f"Token/key en URL: {endpoint[:50]}",
                           recommendation="Usar headers para transportar tokens")
    
    # Buscar credenciales en requests
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                # Password en body de fetch
                if re.search(r'body\s*:\s*[^}]*password', content, re.I):
                    if not re.search(r'content-type["\']?\s*:\s*["\']application/json', content, re.I):
                        add_finding("Bloque 5", "password_plain", "high",
                                   f"Password enviado sin JSON en {rel_path}",
                                   recommendation="Enviar credenciales como JSON con Content-Type apropiado")
        except:
            pass

# =============================================================================
# BLOQUE 6: HEADERS DE RESPUESTA
# =============================================================================
def audit_block_6():
    """Analiza headers de seguridad en respuestas"""
    print(f"\n{'='*60}\n📁 BLOQUE 6: HEADERS DE RESPUESTA\n{'='*60}")
    
    response = safe_request("GET", BASE_URL)
    if not response:
        return
    
    security_headers = {
        "X-Frame-Options": ("critical", "Protección contra clickjacking"),
        "X-Content-Type-Options": ("high", "Prevención de MIME sniffing"),
        "X-XSS-Protection": ("medium", "Protección XSS del navegador"),
        "Content-Security-Policy": ("critical", "Política de seguridad de contenido"),
        "Strict-Transport-Security": ("high", "Forzar HTTPS"),
        "Referrer-Policy": ("medium", "Control de información de referencia"),
        "Permissions-Policy": ("low", "Control de permisos del navegador"),
        "Cross-Origin-Opener-Policy": ("medium", "Aislamiento de origen"),
        "Cross-Origin-Embedder-Policy": ("medium", "Política de embebido"),
        "Cross-Origin-Resource-Policy": ("medium", "Política de recursos"),
    }
    
    for header, (severity, desc) in security_headers.items():
        if header not in response.headers:
            add_finding("Bloque 6", f"missing_{header.lower()}", severity,
                       f"Falta header: {header}",
                       details=desc,
                       recommendation=f"Agregar header {header} en todas las respuestas")
    
    # Verificar headers que exponen información
    info_headers = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Runtime"]
    for header in info_headers:
        if header in response.headers:
            add_finding("Bloque 6", "info_disclosure", "low",
                       f"Header '{header}' expone información: {response.headers[header]}",
                       recommendation=f"Remover o ocultar header {header}")
    
    # Verificar CORS
    acao = response.headers.get("Access-Control-Allow-Origin", "")
    if acao == "*":
        add_finding("Bloque 6", "cors_wildcard", "high",
                   "CORS permite cualquier origen (*)",
                   recommendation="Restringir CORS a orígenes conocidos")

# =============================================================================
# BLOQUE 7: CÓDIGO JAVASCRIPT EXPUESTO
# =============================================================================
def audit_block_7():
    """Analiza código JavaScript en busca de secretos"""
    print(f"\n{'='*60}\n📁 BLOQUE 7: CÓDIGO JAVASCRIPT EXPUESTO\n{'='*60}")
    
    js_files = get_all_js_files()
    
    secret_patterns = {
        "api_key": (r'["\']?api[_-]?key["\']?\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']', "API Key expuesta"),
        "aws_key": (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        "aws_secret": (r'["\']?aws[_-]?secret["\']?\s*[=:]\s*["\'][^"\']{20,}["\']', "AWS Secret"),
        "google_key": (r'AIza[0-9A-Za-z_-]{35}', "Google API Key"),
        "stripe_key": (r'(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}', "Stripe Key"),
        "jwt_token": (r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', "JWT Token hardcodeado"),
        "private_key": (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', "Clave privada"),
        "password_var": (r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']', "Password hardcodeado"),
        "secret_key": (r'secret[_-]?key\s*[=:]\s*["\'][^"\']{10,}["\']', "Secret key expuesto"),
        "bearer_token": (r'Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', "Bearer token hardcodeado"),
        "basic_auth": (r'Basic\s+[A-Za-z0-9+/=]{10,}', "Basic auth hardcodeado"),
        "firebase": (r'firebase[a-zA-Z]*\.com/[^\s"\']+', "Firebase URL con posibles credenciales"),
        "mongodb": (r'mongodb(\+srv)?://[^\s"\']+', "MongoDB connection string"),
        "postgres": (r'postgres(ql)?://[^\s"\']+', "PostgreSQL connection string"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in secret_patterns.items():
                    matches = re.findall(pattern, content, re.I)
                    if matches:
                        add_finding("Bloque 7", pattern_name, "critical",
                                   f"{desc} en {rel_path}",
                                   evidence=str(matches[0])[:50] if matches else "",
                                   recommendation="Mover secretos al backend, nunca en código JS")
        except:
            pass
    
    # Buscar rutas de admin en JS
    admin_patterns = [
        r'["\']/(admin|administrator|manage|dashboard|control)["\']',
        r'["\'].*/(admin|administrator)/.*["\']',
        r'isAdmin\s*[=:]\s*true',
        r'role\s*[=:]\s*["\']admin["\']',
    ]
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern in admin_patterns:
                    if re.search(pattern, content, re.I):
                        add_finding("Bloque 7", "admin_route_exposed", "medium",
                                   f"Ruta de admin expuesta en {rel_path}",
                                   recommendation="No exponer rutas administrativas en código frontend")
        except:
            pass

# =============================================================================
# BLOQUE 8: SOURCE MAPS
# =============================================================================
def audit_block_8():
    """Analiza source maps expuestos"""
    print(f"\n{'='*60}\n📁 BLOQUE 8: SOURCE MAPS\n{'='*60}")
    
    # Buscar referencias a source maps en JS
    js_files = get_all_js_files()
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                if "//# sourceMappingURL=" in content:
                    add_finding("Bloque 8", "source_map_reference", "high",
                               f"Referencia a source map en {rel_path}",
                               recommendation="Remover source maps en producción")
        except:
            pass
    
    # Intentar acceder a source maps comunes
    map_endpoints = [
        "/static/js/app.js.map",
        "/static/js/main.js.map",
        "/static/js/bundle.js.map",
        "/js/app.js.map",
        "/assets/index.js.map",
    ]
    
    for endpoint in map_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code == 200:
            add_finding("Bloque 8", "source_map_accessible", "critical",
                       f"Source map accesible: {endpoint}",
                       recommendation="Bloquear acceso a archivos .map en producción")

# =============================================================================
# BLOQUE 9: HTML/DOM
# =============================================================================
def audit_block_9():
    """Analiza seguridad del HTML/DOM"""
    print(f"\n{'='*60}\n📁 BLOQUE 9: HTML/DOM\n{'='*60}")
    
    html_files = get_all_html_files()
    
    # Patrones peligrosos en HTML
    html_patterns = {
        "html_comment_sensitive": (r'<!--[^>]*(password|secret|key|token|todo|fixme|hack|bug)[^>]*-->', "Comentario HTML sensible"),
        "hidden_input_sensitive": (r'<input[^>]*type=["\']hidden["\'][^>]*(password|token|secret|key)[^>]*>', "Input hidden con datos sensibles"),
        "data_attribute_sensitive": (r'data-(password|token|secret|key|user|auth)=["\'][^"\']+["\']', "Data attribute sensible"),
        "inline_script": (r'<script[^>]*>[^<]{50,}</script>', "Script inline largo"),
        "inline_style_expression": (r'style=["\'][^"\']*expression\s*\(', "CSS expression (IE XSS)"),
        "form_action_javascript": (r'<form[^>]*action=["\']javascript:', "Form action con javascript:"),
        "href_javascript": (r'href=["\']javascript:[^"\']*["\']', "Href con javascript:"),
        "onclick_inline": (r'onclick=["\'][^"\']{20,}["\']', "Onclick con código largo"),
        "autocomplete_password": (r'<input[^>]*type=["\']password["\'][^>]*(?!autocomplete=["\']off["\'])', "Password sin autocomplete=off"),
    }
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(html_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in html_patterns.items():
                    matches = re.findall(pattern, content, re.I)
                    if matches:
                        severity = "high" if "sensitive" in pattern_name or "password" in pattern_name else "medium"
                        add_finding("Bloque 9", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   recommendation="Revisar y limpiar el código HTML")
        except:
            pass
    
    # Verificar meta tags
    response = safe_request("GET", BASE_URL)
    if response:
        # Buscar meta tags sensibles
        meta_patterns = [
            r'<meta[^>]*name=["\']?robots["\']?[^>]*content=["\']?noindex',
            r'<meta[^>]*name=["\']?generator["\']?[^>]*content=["\']?([^"\']+)',
            r'<meta[^>]*name=["\']?author["\']?[^>]*content=["\']?([^"\']+)',
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, response.text, re.I)
            if matches:
                add_finding("Bloque 9", "meta_info_disclosure", "low",
                           f"Meta tag expone información",
                           evidence=str(matches[0])[:100])

# =============================================================================
# BLOQUE 10: WEBSOCKETS
# =============================================================================
def audit_block_10():
    """Analiza seguridad de WebSockets"""
    print(f"\n{'='*60}\n📁 BLOQUE 10: WEBSOCKETS\n{'='*60}")
    
    js_files = get_all_js_files()
    
    ws_patterns = {
        "ws_connection": (r'new\s+WebSocket\s*\(\s*["\']([^"\']+)["\']', "Conexión WebSocket"),
        "ws_no_wss": (r'new\s+WebSocket\s*\(\s*["\']ws://[^"\']+["\']', "WebSocket sin TLS (ws://)"),
        "ws_send_sensitive": (r'\.send\s*\([^)]*(?:password|token|secret|key)', "WebSocket envía datos sensibles"),
        "socket_io": (r'io\s*\(\s*["\']([^"\']+)["\']', "Socket.IO conexión"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in ws_patterns.items():
                    matches = re.findall(pattern, content, re.I)
                    if matches:
                        severity = "high" if "no_wss" in pattern_name or "sensitive" in pattern_name else "medium"
                        add_finding("Bloque 10", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   evidence=str(matches[0])[:100] if matches else "",
                                   recommendation="Usar WSS y no enviar datos sensibles sin encriptar")
        except:
            pass
    
    # Verificar endpoints de WebSocket
    ws_endpoints = ["/ws", "/websocket", "/socket.io/", "/sockjs/", "/cable"]
    for endpoint in ws_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code != 404:
            add_finding("Bloque 10", "ws_endpoint_found", "info",
                       f"Endpoint WebSocket encontrado: {endpoint}",
                       recommendation="Verificar autenticación en WebSockets")

# =============================================================================
# BLOQUE 11: SERVICE WORKERS
# =============================================================================
def audit_block_11():
    """Analiza Service Workers"""
    print(f"\n{'='*60}\n📁 BLOQUE 11: SERVICE WORKERS\n{'='*60}")
    
    # Buscar registro de service workers
    js_files = get_all_js_files()
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                if "serviceWorker.register" in content:
                    add_finding("Bloque 11", "sw_registered", "info",
                               f"Service Worker registrado en {rel_path}",
                               recommendation="Verificar qué datos cachea el SW")
                
                # Buscar cache de datos sensibles
                if re.search(r'cache\.(put|add|addAll)[^;]*(?:api|token|auth)', content, re.I):
                    add_finding("Bloque 11", "sw_cache_sensitive", "high",
                               f"Service Worker cachea datos sensibles en {rel_path}",
                               recommendation="No cachear endpoints con datos sensibles")
        except:
            pass
    
    # Verificar si existe sw.js o service-worker.js
    sw_files = ["/sw.js", "/service-worker.js", "/serviceworker.js"]
    for sw_file in sw_files:
        response = safe_request("GET", f"{BASE_URL}{sw_file}")
        if response and response.status_code == 200:
            add_finding("Bloque 11", "sw_accessible", "medium",
                       f"Service Worker accesible: {sw_file}",
                       recommendation="Revisar qué cachea el Service Worker")
            
            # Analizar contenido del SW
            if "password" in response.text.lower() or "token" in response.text.lower():
                add_finding("Bloque 11", "sw_sensitive_reference", "high",
                           f"Service Worker menciona datos sensibles: {sw_file}")

# =============================================================================
# BLOQUE 12: APIs DEL NAVEGADOR
# =============================================================================
def audit_block_12():
    """Analiza uso de APIs del navegador"""
    print(f"\n{'='*60}\n📁 BLOQUE 12: APIs DEL NAVEGADOR\n{'='*60}")
    
    js_files = get_all_js_files()
    
    api_patterns = {
        "geolocation": (r'navigator\.geolocation', "Uso de geolocalización"),
        "camera": (r'getUserMedia|navigator\.mediaDevices', "Acceso a cámara/micrófono"),
        "notifications": (r'Notification\.requestPermission|new Notification', "Uso de notificaciones"),
        "clipboard_read": (r'navigator\.clipboard\.read', "Lectura de clipboard"),
        "clipboard_write": (r'navigator\.clipboard\.write', "Escritura de clipboard"),
        "bluetooth": (r'navigator\.bluetooth', "Acceso Bluetooth"),
        "usb": (r'navigator\.usb', "Acceso USB"),
        "payment": (r'PaymentRequest|navigator\.payment', "API de pagos"),
        "credentials": (r'navigator\.credentials', "API de credenciales"),
        "storage_estimate": (r'navigator\.storage\.estimate', "Storage estimate"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for api_name, (pattern, desc) in api_patterns.items():
                    if re.search(pattern, content, re.I):
                        severity = "medium" if api_name in ["geolocation", "camera", "payment"] else "low"
                        add_finding("Bloque 12", api_name, severity,
                                   f"{desc} en {rel_path}",
                                   recommendation="Verificar que el usuario da consentimiento explícito")
        except:
            pass

# =============================================================================
# BLOQUE 13: POSTMESSAGE
# =============================================================================
def audit_block_13():
    """Analiza uso de postMessage"""
    print(f"\n{'='*60}\n📁 BLOQUE 13: POSTMESSAGE\n{'='*60}")
    
    js_files = get_all_js_files()
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                # postMessage sin validar origen
                if "postMessage" in content:
                    add_finding("Bloque 13", "postmessage_used", "info",
                               f"postMessage usado en {rel_path}")
                    
                    # Verificar si hay validación de origen
                    if re.search(r'addEventListener\s*\(["\']message["\']', content):
                        if not re.search(r'event\.origin|e\.origin|msg\.origin', content, re.I):
                            add_finding("Bloque 13", "postmessage_no_origin_check", "critical",
                                       f"postMessage sin validar origen en {rel_path}",
                                       recommendation="Siempre validar event.origin en listeners de message")
                
                # postMessage con * como target
                if re.search(r'\.postMessage\s*\([^)]*,\s*["\']\*["\']', content):
                    add_finding("Bloque 13", "postmessage_wildcard", "high",
                               f"postMessage con target '*' en {rel_path}",
                               recommendation="Especificar origen exacto en postMessage")
                
                # Datos sensibles en postMessage
                if re.search(r'\.postMessage\s*\([^)]*(?:token|password|secret|key)', content, re.I):
                    add_finding("Bloque 13", "postmessage_sensitive", "critical",
                               f"Datos sensibles en postMessage en {rel_path}",
                               recommendation="No enviar datos sensibles por postMessage")
        except:
            pass

# =============================================================================
# BLOQUE 14: FETCH/XHR INTERCEPTION
# =============================================================================
def audit_block_14():
    """Analiza intercepción de Fetch/XHR"""
    print(f"\n{'='*60}\n📁 BLOQUE 14: FETCH/XHR INTERCEPTION\n{'='*60}")
    
    js_files = get_all_js_files()
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                # Credenciales en headers
                header_patterns = [
                    (r'["\']Authorization["\']:\s*["\']Bearer\s+[^"\']+["\']', "Bearer token hardcodeado en header"),
                    (r'["\']X-API-Key["\']:\s*["\'][^"\']+["\']', "API Key en header"),
                    (r'["\']Authorization["\']:\s*["\']Basic\s+[^"\']+["\']', "Basic auth hardcodeado"),
                    (r'headers\s*:\s*\{[^}]*password', "Password en headers"),
                ]
                
                for pattern, desc in header_patterns:
                    if re.search(pattern, content, re.I):
                        add_finding("Bloque 14", "sensitive_header", "critical",
                                   f"{desc} en {rel_path}",
                                   recommendation="No hardcodear credenciales en código frontend")
                
                # Credenciales en body
                if re.search(r'body\s*:\s*JSON\.stringify\s*\(\s*\{[^}]*password\s*:', content, re.I):
                    add_finding("Bloque 14", "password_in_body", "info",
                               f"Password en body de request en {rel_path}",
                               details="Esto es normal para login, pero verificar que sea HTTPS")
                
                # Credentials: 'include' sin validación
                if "credentials: 'include'" in content or 'credentials: "include"' in content:
                    add_finding("Bloque 14", "credentials_include", "medium",
                               f"Fetch con credentials: 'include' en {rel_path}",
                               recommendation="Verificar que CORS esté configurado correctamente")
        except:
            pass

# =============================================================================
# BLOQUE 15: THIRD PARTY SCRIPTS
# =============================================================================
def audit_block_15():
    """Analiza scripts de terceros"""
    print(f"\n{'='*60}\n📁 BLOQUE 15: THIRD PARTY SCRIPTS\n{'='*60}")
    
    response = safe_request("GET", BASE_URL)
    if not response:
        return
    
    # Buscar scripts externos
    external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', response.text, re.I)
    
    for script in external_scripts:
        # Scripts de CDN sin integridad
        if any(cdn in script for cdn in ["cdn.", "unpkg.com", "cdnjs.", "jsdelivr"]):
            if "integrity=" not in response.text.split(script)[0][-200:]:
                add_finding("Bloque 15", "cdn_no_sri", "high",
                           f"CDN sin Subresource Integrity: {script[:80]}",
                           recommendation="Agregar atributo integrity con hash SRI")
        
        # Scripts de tracking
        tracking_domains = ["google-analytics", "googletagmanager", "facebook", 
                          "hotjar", "mixpanel", "segment", "amplitude"]
        for tracker in tracking_domains:
            if tracker in script.lower():
                add_finding("Bloque 15", "tracking_script", "info",
                           f"Script de tracking detectado: {script[:80]}",
                           details="Los trackers pueden capturar datos del usuario")
    
    html_files = get_all_html_files()
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(html_file, PROJECT_ROOT)
                
                scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>', content)
                for script in scripts:
                    if script.startswith("http") and "integrity" not in content.split(script)[0][-200:]:
                        add_finding("Bloque 15", "external_no_sri", "medium",
                                   f"Script externo sin SRI en {rel_path}: {script[:50]}",
                                   recommendation="Agregar integrity hash")
        except:
            pass

# =============================================================================
# BLOQUE 16: PROTOTYPE POLLUTION
# =============================================================================
def audit_block_16():
    """Analiza riesgos de Prototype Pollution"""
    print(f"\n{'='*60}\n📁 BLOQUE 16: PROTOTYPE POLLUTION\n{'='*60}")
    
    js_files = get_all_js_files()
    
    pollution_patterns = {
        "proto_access": (r'\[[\'"]\s*__proto__\s*[\'"]\]', "Acceso a __proto__"),
        "constructor_access": (r'\[[\'"]\s*constructor\s*[\'"]\]', "Acceso a constructor"),
        "prototype_assign": (r'Object\.prototype\s*\[', "Asignación a Object.prototype"),
        "merge_deep": (r'(merge|extend|assign|deepCopy|deepMerge)\s*\(', "Función de merge profundo"),
        "json_parse_unsafe": (r'JSON\.parse\s*\([^)]*\)', "JSON.parse (verificar origen)"),
        "lodash_merge": (r'_\.(merge|defaultsDeep|set)\s*\(', "Lodash merge (vulnerable en versiones antiguas)"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in pollution_patterns.items():
                    if re.search(pattern, content, re.I):
                        severity = "high" if pattern_name in ["proto_access", "prototype_assign"] else "medium"
                        add_finding("Bloque 16", pattern_name, severity,
                                   f"{desc} en {rel_path}",
                                   recommendation="Validar y sanitizar objetos antes de merge")
        except:
            pass

# =============================================================================
# BLOQUE 17: DOM CLOBBERING
# =============================================================================
def audit_block_17():
    """Analiza riesgos de DOM Clobbering"""
    print(f"\n{'='*60}\n📁 BLOQUE 17: DOM CLOBBERING\n{'='*60}")
    
    html_files = get_all_html_files()
    
    # IDs peligrosos que pueden sobrescribir globals
    dangerous_ids = ["location", "document", "window", "top", "self", "parent",
                    "frames", "opener", "closed", "length", "name"]
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(html_file, PROJECT_ROOT)
                
                for dangerous_id in dangerous_ids:
                    if re.search(f'id=["\']?{dangerous_id}["\']?', content, re.I):
                        add_finding("Bloque 17", "dangerous_id", "high",
                                   f"ID peligroso '{dangerous_id}' puede causar DOM clobbering en {rel_path}",
                                   recommendation=f"Cambiar el ID '{dangerous_id}' por otro nombre")
                
                # Name attributes en forms
                if re.search(r'name=["\']?(action|method|target)["\']?', content, re.I):
                    add_finding("Bloque 17", "form_clobbering", "medium",
                               f"Posible form clobbering en {rel_path}",
                               recommendation="Evitar usar 'action', 'method', 'target' como name de inputs")
        except:
            pass

# =============================================================================
# BLOQUE 18: EVENT HANDLERS
# =============================================================================
def audit_block_18():
    """Analiza event handlers inseguros"""
    print(f"\n{'='*60}\n📁 BLOQUE 18: EVENT HANDLERS\n{'='*60}")
    
    html_files = get_all_html_files()
    
    dangerous_handlers = ["onclick", "onmouseover", "onerror", "onload", 
                         "onfocus", "onblur", "onsubmit", "onchange"]
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(html_file, PROJECT_ROOT)
                
                for handler in dangerous_handlers:
                    pattern = f'{handler}=["\'][^"\']*["\']'
                    matches = re.findall(pattern, content, re.I)
                    if matches:
                        add_finding("Bloque 18", f"inline_{handler}", "medium",
                                   f"Handler inline '{handler}' en {rel_path}",
                                   details=f"Encontrados {len(matches)} handlers inline",
                                   recommendation="Usar addEventListener en lugar de handlers inline")
                
                # javascript: en href
                if re.search(r'href=["\']javascript:[^"\']+["\']', content, re.I):
                    add_finding("Bloque 18", "javascript_href", "high",
                               f"javascript: en href en {rel_path}",
                               recommendation="Evitar javascript: en links")
        except:
            pass

# =============================================================================
# BLOQUE 19: FUZZING DE ENDPOINTS
# =============================================================================
def audit_block_19():
    """Fuzzing de endpoints desde código JS"""
    print(f"\n{'='*60}\n📁 BLOQUE 19: FUZZING DE ENDPOINTS\n{'='*60}")
    
    js_files = get_all_js_files()
    discovered_paths = set()
    
    # Extraer todas las rutas del código JS
    path_patterns = [
        r'["\']/(api/[^"\']+)["\']',
        r'["\']/(admin[^"\']*)["\']',
        r'["\']/(user[^"\']*)["\']',
        r'["\']/(auth[^"\']*)["\']',
        r'["\']/(login[^"\']*)["\']',
        r'["\']/(register[^"\']*)["\']',
        r'["\']/(dashboard[^"\']*)["\']',
        r'["\']/(settings[^"\']*)["\']',
        r'["\']/(profile[^"\']*)["\']',
        r'["\']/(upload[^"\']*)["\']',
        r'["\']/(download[^"\']*)["\']',
        r'["\']/(export[^"\']*)["\']',
        r'["\']/(import[^"\']*)["\']',
        r'["\']/(delete[^"\']*)["\']',
        r'["\']/(edit[^"\']*)["\']',
        r'["\']/(create[^"\']*)["\']',
        r'["\']/(update[^"\']*)["\']',
    ]
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern in path_patterns:
                    matches = re.findall(pattern, content, re.I)
                    for match in matches:
                        discovered_paths.add(f"/{match}" if not match.startswith("/") else match)
        except:
            pass
    
    print(f"  Endpoints descubiertos: {len(discovered_paths)}")
    
    # Probar cada endpoint
    for path in list(discovered_paths)[:30]:
        response = safe_request("GET", f"{BASE_URL}{path}")
        if response:
            if response.status_code == 200:
                add_finding("Bloque 19", "endpoint_accessible", "medium",
                           f"Endpoint accesible: {path} (Status: 200)",
                           recommendation="Verificar que requiere autenticación apropiada")
            elif response.status_code in [401, 403]:
                add_finding("Bloque 19", "endpoint_protected", "info",
                           f"Endpoint protegido: {path} (Status: {response.status_code})")
    
    # Endpoints de debug comunes
    debug_endpoints = [
        "/debug", "/test", "/dev", "/phpinfo.php",
        "/api/debug", "/api/test", "/api/health",
        "/.env", "/.git/config", "/config.js",
        "/swagger", "/api-docs", "/graphql",
        "/actuator/health", "/metrics", "/trace"
    ]
    
    for endpoint in debug_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code == 200:
            add_finding("Bloque 19", "debug_endpoint", "high",
                       f"Endpoint de debug/config accesible: {endpoint}",
                       recommendation="Bloquear endpoints de debug en producción")

# =============================================================================
# BLOQUE 20: FINGERPRINTING Y LEAKS
# =============================================================================
def audit_block_20():
    """Analiza fingerprinting y leaks de información"""
    print(f"\n{'='*60}\n📁 BLOQUE 20: FINGERPRINTING Y LEAKS\n{'='*60}")
    
    js_files = get_all_js_files()
    
    fingerprint_patterns = {
        "canvas_fingerprint": (r'canvas.*getContext|toDataURL|getImageData', "Canvas fingerprinting"),
        "webgl_fingerprint": (r'getParameter\s*\(\s*\w+\.(VENDOR|RENDERER)', "WebGL fingerprinting"),
        "audio_fingerprint": (r'AudioContext|OfflineAudioContext', "Audio fingerprinting"),
        "font_fingerprint": (r'measureText|fonts\.check', "Font fingerprinting"),
        "screen_info": (r'screen\.(width|height|colorDepth|pixelDepth)', "Screen info leaking"),
        "navigator_info": (r'navigator\.(userAgent|platform|language|plugins)', "Navigator info leaking"),
        "timing_attack": (r'performance\.(now|timing)|Date\.(now|getTime)', "Posible timing attack"),
        "battery_api": (r'navigator\.getBattery', "Battery API (fingerprinting)"),
    }
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(js_file, PROJECT_ROOT)
                
                for pattern_name, (pattern, desc) in fingerprint_patterns.items():
                    if re.search(pattern, content, re.I):
                        add_finding("Bloque 20", pattern_name, "low",
                                   f"{desc} en {rel_path}",
                                   recommendation="Considerar implicaciones de privacidad")
        except:
            pass
    
    # Verificar headers que leakean información
    response = safe_request("GET", BASE_URL)
    if response:
        leak_headers = ["X-Request-Id", "X-Correlation-Id", "X-Trace-Id", 
                       "X-Amzn-RequestId", "X-Debug-Token"]
        for header in leak_headers:
            if header in response.headers:
                add_finding("Bloque 20", "debug_header", "low",
                           f"Header de debug expuesto: {header}",
                           evidence=f"{header}: {response.headers[header]}")

# =============================================================================
# GENERACIÓN DE REPORTE
# =============================================================================
def generate_report():
    """Genera los reportes finales"""
    report_dir = Path(__file__).parent
    
    # Reporte TXT
    txt_path = report_dir / "reporte_console_audit.txt"
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE AUDITORÍA DE SEGURIDAD - WEB CONSOLE\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Objetivo: {results['metadata']['target']}\n")
        f.write(f"Fecha: {results['metadata']['date']}\n")
        f.write(f"Total de pruebas: {results['metadata']['total_tests']}\n")
        f.write(f"Bloques auditados: {results['metadata']['blocks']}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("RESUMEN EJECUTIVO\n")
        f.write("-" * 80 + "\n\n")
        
        f.write(f"🔴 CRÍTICO: {results['summary']['critical']}\n")
        f.write(f"🟠 ALTO:    {results['summary']['high']}\n")
        f.write(f"🟡 MEDIO:   {results['summary']['medium']}\n")
        f.write(f"🟢 BAJO:    {results['summary']['low']}\n")
        f.write(f"🔵 INFO:    {results['summary']['info']}\n\n")
        
        total = sum(results['summary'].values())
        f.write(f"TOTAL DE HALLAZGOS: {total}\n\n")
        
        if results['summary']['critical'] > 0:
            f.write("⚠️  SE ENCONTRARON VULNERABILIDADES CRÍTICAS\n")
            f.write("    Se recomienda acción inmediata\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("HALLAZGOS DETALLADOS\n")
        f.write("=" * 80 + "\n\n")
        
        # Ordenar por severidad
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(results['findings'],
                                key=lambda x: severity_order.get(x['severity'].lower(), 5))
        
        current_block = ""
        for finding in sorted_findings:
            if finding['block'] != current_block:
                current_block = finding['block']
                f.write(f"\n{'─' * 60}\n")
                f.write(f"📁 {current_block}\n")
                f.write(f"{'─' * 60}\n\n")
            
            icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
            icon = icons.get(finding['severity'].lower(), "⚪")
            
            f.write(f"{icon} [{finding['severity'].upper()}] {finding['test']}\n")
            f.write(f"   Descripción: {finding['description']}\n")
            
            if finding.get('details'):
                f.write(f"   Detalles: {finding['details']}\n")
            
            if finding.get('evidence'):
                f.write(f"   Evidencia: {finding['evidence'][:200]}\n")
            
            if finding.get('recommendation'):
                f.write(f"   ✅ Recomendación: {finding['recommendation']}\n")
            
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMENDACIONES GENERALES PARA CONSOLA WEB\n")
        f.write("=" * 80 + "\n\n")
        
        recommendations = [
            "1. No exponer datos sensibles en localStorage/sessionStorage",
            "2. Usar cookies HttpOnly, Secure y SameSite",
            "3. Implementar Content-Security-Policy estricto",
            "4. Remover console.log y debug code en producción",
            "5. No hardcodear API keys en código JavaScript",
            "6. Validar origen en postMessage handlers",
            "7. Usar Subresource Integrity (SRI) para CDNs",
            "8. Deshabilitar source maps en producción",
            "9. Sanitizar todo HTML antes de insertarlo en DOM",
            "10. Implementar rate limiting en todos los endpoints"
        ]
        
        for rec in recommendations:
            f.write(f"   {rec}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("FIN DEL REPORTE\n")
        f.write("=" * 80 + "\n")
    
    # Reporte JSON
    json_path = report_dir / "reporte_console_audit.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print("REPORTE GENERADO")
    print(f"{'=' * 60}")
    print(f"📄 Reporte TXT: {txt_path}")
    print(f"📊 Reporte JSON: {json_path}")
    print(f"\n🔴 Crítico: {results['summary']['critical']}")
    print(f"🟠 Alto: {results['summary']['high']}")
    print(f"🟡 Medio: {results['summary']['medium']}")
    print(f"🟢 Bajo: {results['summary']['low']}")
    print(f"🔵 Info: {results['summary']['info']}")

# =============================================================================
# MAIN
# =============================================================================
def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("🔒 AUDITORÍA DE SEGURIDAD WEB CONSOLE - MASIVA")
    print("=" * 60)
    print(f"Objetivo: {BASE_URL}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar conectividad
    print("\nVerificando conectividad...")
    response = safe_request("GET", BASE_URL)
    if not response:
        print(f"⚠️  No se puede conectar a {BASE_URL}")
        print("   Algunas pruebas de red no estarán disponibles")
    else:
        print(f"✅ Conectado exitosamente (Status: {response.status_code})")
    
    try:
        audit_block_1()   # Errores de JavaScript
        audit_block_2()   # Variables Globales
        audit_block_3()   # LocalStorage/SessionStorage
        audit_block_4()   # Cookies
        audit_block_5()   # Network Requests
        audit_block_6()   # Headers de Respuesta
        audit_block_7()   # Código JavaScript Expuesto
        audit_block_8()   # Source Maps
        audit_block_9()   # HTML/DOM
        audit_block_10()  # WebSockets
        audit_block_11()  # Service Workers
        audit_block_12()  # APIs del Navegador
        audit_block_13()  # PostMessage
        audit_block_14()  # Fetch/XHR Interception
        audit_block_15()  # Third Party Scripts
        audit_block_16()  # Prototype Pollution
        audit_block_17()  # DOM Clobbering
        audit_block_18()  # Event Handlers
        audit_block_19()  # Fuzzing de Endpoints
        audit_block_20()  # Fingerprinting y Leaks
    except KeyboardInterrupt:
        print("\n\n⚠️ Auditoría interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la auditoría: {str(e)}")
    
    generate_report()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    
    import urllib3
    urllib3.disable_warnings()
    
    main()
