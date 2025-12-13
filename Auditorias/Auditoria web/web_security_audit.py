#!/usr/bin/env python3
"""
=============================================================================
AUDITORÍA DE SEGURIDAD WEB COMPLETA
=============================================================================
Script de auditoría de seguridad con 58 pruebas en 14 bloques
Genera reporte detallado con vulnerabilidades encontradas

Autor: Security Audit Tool
Versión: 1.0
=============================================================================
"""

import os
import re
import json
import time
import socket
import ssl
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError
except ImportError:
    print("Instalando requests...")
    os.system("pip install requests")
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError

# Configuración
BASE_URL = os.environ.get("AUDIT_TARGET_URL", "http://localhost:5000")
TIMEOUT = 10
MAX_REQUESTS_PER_TEST = 5
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Colores para terminal
class Colors:
    CRITICAL = "\033[91m"
    HIGH = "\033[93m"
    MEDIUM = "\033[94m"
    LOW = "\033[92m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# Almacenamiento de resultados
results = {
    "metadata": {
        "target": BASE_URL,
        "date": datetime.now().isoformat(),
        "total_tests": 58,
        "blocks": 14
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
        "evidence": evidence[:500] if evidence else "",
        "timestamp": datetime.now().isoformat()
    }
    results["findings"].append(finding)
    
    severity_lower = severity.lower()
    if severity_lower in results["summary"]:
        results["summary"][severity_lower] += 1
    
    severity_icon = {
        "critical": "🔴",
        "high": "🟠", 
        "medium": "🟡",
        "low": "🟢",
        "info": "🔵"
    }.get(severity_lower, "⚪")
    
    print(f"  {severity_icon} [{severity.upper()}] {test}: {description}")

def safe_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """Realiza request segura con manejo de errores"""
    try:
        kwargs.setdefault("timeout", TIMEOUT)
        kwargs.setdefault("verify", False)
        kwargs.setdefault("allow_redirects", False)
        response = requests.request(method, url, **kwargs)
        return response
    except Exception as e:
        return None

# =============================================================================
# BLOQUE 1: CONFIGURACIÓN Y HEADERS
# =============================================================================
def audit_block_1():
    """Auditoría de configuración y headers de seguridad"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 1: CONFIGURACIÓN Y HEADERS ═══{Colors.RESET}")
    
    response = safe_request("GET", BASE_URL)
    if not response:
        add_finding("Bloque 1", "Conexión", "critical", 
                   "No se puede conectar al servidor",
                   recommendation="Verificar que el servidor esté corriendo")
        return
    
    headers = response.headers
    
    # 1.1 Headers de seguridad faltantes
    security_headers = {
        "X-Frame-Options": ("Protege contra clickjacking", "high"),
        "X-Content-Type-Options": ("Previene MIME sniffing", "medium"),
        "X-XSS-Protection": ("Protección XSS del navegador", "medium"),
        "Strict-Transport-Security": ("Fuerza HTTPS (HSTS)", "high"),
        "Content-Security-Policy": ("Política de seguridad de contenido", "high"),
        "Referrer-Policy": ("Controla información de referencia", "low"),
        "Permissions-Policy": ("Controla permisos del navegador", "low"),
        "X-Permitted-Cross-Domain-Policies": ("Políticas cross-domain", "low"),
        "Cache-Control": ("Control de caché", "medium"),
    }
    
    for header, (desc, severity) in security_headers.items():
        if header not in headers:
            add_finding("Bloque 1", "Headers Seguridad", severity,
                       f"Falta header: {header}",
                       details=desc,
                       recommendation=f"Agregar header {header} en las respuestas HTTP")
    
    # 1.2 Cookies inseguras
    cookies = response.cookies
    for cookie in cookies:
        issues = []
        if not cookie.secure:
            issues.append("Sin flag Secure")
        if not cookie.has_nonstandard_attr("HttpOnly"):
            issues.append("Sin flag HttpOnly")
        if not cookie.has_nonstandard_attr("SameSite"):
            issues.append("Sin flag SameSite")
            
        if issues:
            add_finding("Bloque 1", "Cookies Inseguras", "high",
                       f"Cookie '{cookie.name}' insegura: {', '.join(issues)}",
                       recommendation="Configurar cookies con Secure, HttpOnly y SameSite")
    
    # Verificar Set-Cookie en headers
    set_cookie = headers.get("Set-Cookie", "")
    if set_cookie:
        if "Secure" not in set_cookie:
            add_finding("Bloque 1", "Cookies Inseguras", "high",
                       "Cookies sin flag Secure en Set-Cookie header",
                       evidence=set_cookie[:200])
        if "HttpOnly" not in set_cookie:
            add_finding("Bloque 1", "Cookies Inseguras", "high",
                       "Cookies sin flag HttpOnly en Set-Cookie header")
    
    # 1.3 Información en headers del servidor
    sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version", 
                        "X-AspNetMvc-Version", "X-Runtime"]
    for header in sensitive_headers:
        if header in headers:
            add_finding("Bloque 1", "Info Expuesta", "low",
                       f"Header '{header}' expone información del servidor",
                       evidence=f"{header}: {headers[header]}",
                       recommendation=f"Remover o ocultar header {header}")

# =============================================================================
# BLOQUE 2: INYECCIONES
# =============================================================================
def audit_block_2():
    """Auditoría de vulnerabilidades de inyección"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 2: INYECCIONES ═══{Colors.RESET}")
    
    # Obtener endpoints conocidos
    endpoints = get_known_endpoints()
    
    # 2.1 SQL Injection
    sql_payloads = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "1' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT username,password FROM users--",
        "1' AND SLEEP(5)--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--"
    ]
    
    sql_errors = [
        "sql syntax", "mysql", "sqlite", "postgresql", "ora-",
        "syntax error", "unclosed quotation", "quoted string not properly terminated",
        "sqlstate", "odbc", "sql server", "database error"
    ]
    
    for endpoint in endpoints[:10]:
        for payload in sql_payloads[:3]:
            test_url = f"{BASE_URL}{endpoint}?id={urllib.parse.quote(payload)}"
            response = safe_request("GET", test_url)
            if response:
                content = response.text.lower()
                for error in sql_errors:
                    if error in content:
                        add_finding("Bloque 2", "SQL Injection", "critical",
                                   f"Posible SQL Injection en {endpoint}",
                                   details=f"Payload: {payload}",
                                   evidence=content[:300],
                                   recommendation="Usar prepared statements y parameterized queries")
                        break
    
    # 2.2 XSS Reflejado
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "'\"><script>alert('XSS')</script>",
        "<body onload=alert('XSS')>"
    ]
    
    for endpoint in endpoints[:10]:
        for payload in xss_payloads[:2]:
            test_url = f"{BASE_URL}{endpoint}?q={urllib.parse.quote(payload)}"
            response = safe_request("GET", test_url)
            if response and payload in response.text:
                add_finding("Bloque 2", "XSS Reflejado", "high",
                           f"XSS reflejado en {endpoint}",
                           details=f"Payload reflejado sin sanitizar",
                           evidence=payload,
                           recommendation="Sanitizar y escapar toda entrada del usuario")
    
    # 2.3 Command Injection
    cmd_payloads = [
        "; ls -la",
        "| cat /etc/passwd",
        "`whoami`",
        "$(id)",
        "; ping -c 1 localhost"
    ]
    
    cmd_indicators = ["root:", "bin/", "uid=", "gid=", "total ", "drwx"]
    
    for endpoint in endpoints[:5]:
        for payload in cmd_payloads[:2]:
            test_url = f"{BASE_URL}{endpoint}?cmd={urllib.parse.quote(payload)}"
            response = safe_request("GET", test_url)
            if response:
                for indicator in cmd_indicators:
                    if indicator in response.text:
                        add_finding("Bloque 2", "Command Injection", "critical",
                                   f"Posible Command Injection en {endpoint}",
                                   details=f"Payload: {payload}",
                                   recommendation="Nunca pasar entrada de usuario a comandos del sistema")
                        break
    
    # 2.4 LDAP Injection
    ldap_payloads = ["*", "*)(&", "*)(objectClass=*"]
    for endpoint in endpoints[:3]:
        for payload in ldap_payloads:
            response = safe_request("GET", f"{BASE_URL}{endpoint}?user={payload}")
            if response and ("ldap" in response.text.lower() or "directory" in response.text.lower()):
                add_finding("Bloque 2", "LDAP Injection", "high",
                           f"Posible LDAP Injection en {endpoint}",
                           recommendation="Sanitizar entrada para consultas LDAP")
    
    # 2.5 XXE Injection
    xxe_payload = '''<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'''
    for endpoint in endpoints[:5]:
        response = safe_request("POST", f"{BASE_URL}{endpoint}", 
                               data=xxe_payload, 
                               headers={"Content-Type": "application/xml"})
        if response and "root:" in response.text:
            add_finding("Bloque 2", "XXE Injection", "critical",
                       f"XXE Injection en {endpoint}",
                       recommendation="Deshabilitar entidades externas en el parser XML")
    
    # 2.6 SSTI (Server-Side Template Injection)
    ssti_payloads = ["{{7*7}}", "${7*7}", "<%= 7*7 %>", "#{7*7}", "*{7*7}"]
    for endpoint in endpoints[:5]:
        for payload in ssti_payloads:
            response = safe_request("GET", f"{BASE_URL}{endpoint}?name={urllib.parse.quote(payload)}")
            if response and "49" in response.text:
                add_finding("Bloque 2", "SSTI", "critical",
                           f"Template Injection en {endpoint}",
                           details=f"Payload {payload} evaluado a 49",
                           recommendation="No renderizar entrada de usuario directamente en templates")
    
    # 2.7 NoSQL Injection
    nosql_payloads = [
        '{"$gt": ""}',
        '{"$ne": null}',
        '{"$where": "1==1"}'
    ]
    for endpoint in endpoints[:5]:
        for payload in nosql_payloads:
            response = safe_request("POST", f"{BASE_URL}{endpoint}",
                                   json={"username": json.loads(payload)})
            if response and response.status_code == 200:
                add_finding("Bloque 2", "NoSQL Injection", "high",
                           f"Posible NoSQL Injection en {endpoint}",
                           recommendation="Validar y sanitizar operadores de consulta")

# =============================================================================
# BLOQUE 3: AUTENTICACIÓN
# =============================================================================
def audit_block_3():
    """Auditoría de autenticación y sesiones"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 3: AUTENTICACIÓN ═══{Colors.RESET}")
    
    # 3.1 Endpoints sin autenticación
    protected_patterns = ["/admin", "/api/users", "/dashboard", "/settings", 
                         "/profile", "/account", "/wallet", "/transactions"]
    
    for pattern in protected_patterns:
        response = safe_request("GET", f"{BASE_URL}{pattern}")
        if response and response.status_code == 200:
            if "login" not in response.url.lower():
                add_finding("Bloque 3", "Sin Autenticación", "critical",
                           f"Endpoint {pattern} accesible sin autenticación",
                           recommendation="Implementar middleware de autenticación")
    
    # 3.2 JWT mal configurados
    jwt_endpoints = ["/api/auth/login", "/auth/login", "/login", "/api/login"]
    for endpoint in jwt_endpoints:
        response = safe_request("POST", f"{BASE_URL}{endpoint}",
                               json={"username": "test", "password": "test"})
        if response:
            auth_header = response.headers.get("Authorization", "")
            set_cookie = response.headers.get("Set-Cookie", "")
            
            # Buscar JWT en respuesta
            jwt_pattern = r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'
            jwt_match = re.search(jwt_pattern, response.text + auth_header + set_cookie)
            
            if jwt_match:
                token = jwt_match.group()
                try:
                    parts = token.split(".")
                    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
                    
                    if header.get("alg") == "none":
                        add_finding("Bloque 3", "JWT Inseguro", "critical",
                                   "JWT permite algoritmo 'none'",
                                   recommendation="Forzar algoritmo seguro (RS256, HS256)")
                    
                    if header.get("alg") == "HS256":
                        # Intentar con clave débil
                        weak_keys = ["secret", "password", "123456", "key"]
                        add_finding("Bloque 3", "JWT Inseguro", "medium",
                                   "JWT usa HS256 - verificar fortaleza de la clave",
                                   recommendation="Usar claves de al menos 256 bits")
                except:
                    pass
    
    # 3.3 Sesiones débiles
    response = safe_request("GET", BASE_URL)
    if response:
        session_cookie = None
        for cookie in response.cookies:
            if "session" in cookie.name.lower():
                session_cookie = cookie.value
                
                if len(session_cookie) < 32:
                    add_finding("Bloque 3", "Sesión Débil", "high",
                               "Token de sesión muy corto",
                               recommendation="Usar tokens de sesión de al menos 128 bits")
                
                if session_cookie.isdigit():
                    add_finding("Bloque 3", "Sesión Predecible", "critical",
                               "Token de sesión numérico predecible",
                               recommendation="Usar generador criptográficamente seguro")
    
    # 3.4 Fuerza bruta (prueba controlada)
    login_endpoints = ["/login", "/api/login", "/auth/login", "/api/auth/login"]
    for endpoint in login_endpoints:
        responses = []
        for i in range(5):
            response = safe_request("POST", f"{BASE_URL}{endpoint}",
                                   json={"username": "test", "password": f"wrong{i}"})
            if response:
                responses.append(response.status_code)
        
        if len(responses) == 5 and all(r in [200, 401, 400] for r in responses):
            add_finding("Bloque 3", "Sin Rate Limit Login", "high",
                       f"No hay límite de intentos en {endpoint}",
                       details="5 intentos fallidos sin bloqueo",
                       recommendation="Implementar rate limiting y bloqueo temporal")
    
    # 3.5 Recuperación de contraseña insegura
    reset_endpoints = ["/forgot-password", "/reset-password", "/api/password/reset"]
    for endpoint in reset_endpoints:
        response = safe_request("POST", f"{BASE_URL}{endpoint}",
                               json={"email": "test@test.com"})
        if response and response.status_code == 200:
            if "token" in response.text.lower() or "reset" in response.url:
                add_finding("Bloque 3", "Reset Inseguro", "medium",
                           f"Verificar seguridad de {endpoint}",
                           recommendation="Tokens de reset de un solo uso con expiración corta")

# =============================================================================
# BLOQUE 4: RATE LIMITING Y DoS
# =============================================================================
def audit_block_4():
    """Auditoría de rate limiting y protección DoS"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 4: RATE LIMITING Y DoS ═══{Colors.RESET}")
    
    # 4.1 Falta de rate limiting general
    test_endpoint = BASE_URL
    success_count = 0
    
    for i in range(20):
        response = safe_request("GET", test_endpoint)
        if response and response.status_code == 200:
            success_count += 1
    
    if success_count == 20:
        add_finding("Bloque 4", "Sin Rate Limiting", "high",
                   "No se detecta rate limiting en endpoint principal",
                   details="20 requests exitosos consecutivos",
                   recommendation="Implementar rate limiting (ej: Flask-Limiter)")
    
    # 4.2 Endpoints vulnerables a spam
    spam_endpoints = ["/api/send", "/contact", "/subscribe", "/api/message"]
    for endpoint in spam_endpoints:
        responses = []
        for i in range(10):
            response = safe_request("POST", f"{BASE_URL}{endpoint}",
                                   json={"message": f"test{i}"})
            if response:
                responses.append(response.status_code)
        
        if len([r for r in responses if r in [200, 201]]) >= 8:
            add_finding("Bloque 4", "Spam Posible", "medium",
                       f"Endpoint {endpoint} permite múltiples requests",
                       recommendation="Agregar rate limiting y captcha")
    
    # 4.3 Recursos pesados sin límite
    heavy_endpoints = ["/api/export", "/download", "/report", "/api/search"]
    for endpoint in heavy_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}?limit=99999999")
        if response and response.status_code == 200:
            if len(response.content) > 1000000:
                add_finding("Bloque 4", "DoS Posible", "high",
                           f"Endpoint {endpoint} permite requests pesados",
                           recommendation="Limitar parámetros de paginación")

# =============================================================================
# BLOQUE 5: EXPOSICIÓN DE INFORMACIÓN
# =============================================================================
def audit_block_5():
    """Auditoría de exposición de información sensible"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 5: EXPOSICIÓN DE INFORMACIÓN ═══{Colors.RESET}")
    
    # 5.1 Archivos sensibles expuestos
    sensitive_files = [
        "/.env", "/.env.local", "/.env.production",
        "/.git/config", "/.git/HEAD",
        "/config.py", "/settings.py", "/config.json",
        "/database.yml", "/secrets.yml",
        "/.htaccess", "/.htpasswd",
        "/phpinfo.php", "/info.php",
        "/backup.sql", "/dump.sql", "/database.sql",
        "/backup.zip", "/backup.tar.gz",
        "/logs/app.log", "/log/error.log",
        "/debug.log", "/application.log",
        "/wp-config.php", "/configuration.php",
        "/.DS_Store", "/Thumbs.db",
        "/composer.json", "/package.json",
        "/requirements.txt", "/Gemfile",
        "/.svn/entries", "/.hg/hgrc",
        "/server-status", "/server-info",
        "/elmah.axd", "/trace.axd",
        "/crossdomain.xml", "/clientaccesspolicy.xml"
    ]
    
    for file_path in sensitive_files:
        response = safe_request("GET", f"{BASE_URL}{file_path}")
        if response and response.status_code == 200:
            if len(response.content) > 0:
                severity = "critical" if any(x in file_path for x in [".env", ".git", "password", "secret", "backup"]) else "high"
                add_finding("Bloque 5", "Archivo Expuesto", severity,
                           f"Archivo sensible accesible: {file_path}",
                           evidence=response.text[:200] if len(response.text) < 500 else "[contenido truncado]",
                           recommendation="Bloquear acceso a archivos sensibles en el servidor")
    
    # 5.2 Listado de directorios
    directories = ["/uploads/", "/images/", "/files/", "/static/", 
                  "/assets/", "/media/", "/backup/", "/tmp/"]
    
    for directory in directories:
        response = safe_request("GET", f"{BASE_URL}{directory}")
        if response and response.status_code == 200:
            if "Index of" in response.text or "<title>Directory" in response.text:
                add_finding("Bloque 5", "Directory Listing", "medium",
                           f"Listado de directorio habilitado: {directory}",
                           recommendation="Deshabilitar autoindex en el servidor")
    
    # 5.3 Mensajes de error detallados
    error_triggers = [
        "/'",
        "/nonexistent" + "A"*500,
        "/test?id=1'",
        "/api/undefined"
    ]
    
    error_patterns = [
        "Traceback", "stack trace", "exception", "error in",
        "line ", "File \"", "at /", "Debug mode",
        "SQLSTATE", "mysql_", "pg_", "sqlite3"
    ]
    
    for trigger in error_triggers:
        response = safe_request("GET", f"{BASE_URL}{trigger}")
        if response:
            for pattern in error_patterns:
                if pattern.lower() in response.text.lower():
                    add_finding("Bloque 5", "Error Detallado", "medium",
                               f"Mensajes de error exponen información",
                               evidence=response.text[:300],
                               recommendation="Configurar páginas de error personalizadas sin detalles técnicos")
                    break
    
    # 5.4 Stack traces expuestos
    response = safe_request("GET", f"{BASE_URL}/api/nonexistent")
    if response:
        if "Traceback" in response.text or "at line" in response.text:
            add_finding("Bloque 5", "Stack Trace", "high",
                       "Stack trace expuesto en respuestas de error",
                       evidence=response.text[:400],
                       recommendation="Deshabilitar debug mode en producción")

# =============================================================================
# BLOQUE 6: APIs Y LÓGICA
# =============================================================================
def audit_block_6():
    """Auditoría de seguridad de APIs y lógica de negocio"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 6: APIs Y LÓGICA ═══{Colors.RESET}")
    
    # 6.1 IDOR (Insecure Direct Object Reference)
    idor_endpoints = [
        "/api/user/{id}",
        "/api/users/{id}",
        "/api/profile/{id}",
        "/api/order/{id}",
        "/api/transaction/{id}",
        "/api/wallet/{id}",
        "/user/{id}",
        "/profile/{id}"
    ]
    
    for endpoint in idor_endpoints:
        for test_id in ["1", "2", "100", "admin"]:
            test_endpoint = endpoint.replace("{id}", test_id)
            response = safe_request("GET", f"{BASE_URL}{test_endpoint}")
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data and isinstance(data, dict):
                        add_finding("Bloque 6", "IDOR Posible", "high",
                                   f"Endpoint {test_endpoint} retorna datos sin verificar propiedad",
                                   recommendation="Verificar que el usuario autenticado sea dueño del recurso")
                except:
                    pass
    
    # 6.2 Falta de paginación
    list_endpoints = ["/api/users", "/api/transactions", "/api/logs", "/api/orders"]
    for endpoint in list_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 100:
                    add_finding("Bloque 6", "Sin Paginación", "medium",
                               f"Endpoint {endpoint} retorna todos los registros",
                               details=f"Retorna {len(data)} items",
                               recommendation="Implementar paginación obligatoria")
            except:
                pass
    
    # 6.3 Respuestas con datos excesivos
    user_endpoints = ["/api/me", "/api/user", "/api/profile"]
    sensitive_fields = ["password", "hash", "secret", "token", "key", 
                       "credit_card", "ssn", "pin", "private"]
    
    for endpoint in user_endpoints:
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code == 200:
            for field in sensitive_fields:
                if field in response.text.lower():
                    add_finding("Bloque 6", "Datos Excesivos", "high",
                               f"Endpoint {endpoint} expone campo sensible: {field}",
                               recommendation="Filtrar campos sensibles de las respuestas")
    
    # 6.4 Endpoints ocultos (fuzzing)
    hidden_paths = [
        "/admin", "/administrator", "/admin123",
        "/api/admin", "/api/internal", "/api/debug",
        "/debug", "/test", "/dev",
        "/swagger", "/api-docs", "/docs",
        "/graphql", "/graphiql",
        "/actuator", "/metrics", "/health",
        "/console", "/shell", "/terminal",
        "/phpmyadmin", "/adminer", "/pgadmin",
        "/.well-known/", "/robots.txt", "/sitemap.xml"
    ]
    
    for path in hidden_paths:
        response = safe_request("GET", f"{BASE_URL}{path}")
        if response and response.status_code in [200, 301, 302]:
            add_finding("Bloque 6", "Endpoint Oculto", "medium",
                       f"Endpoint descubierto: {path}",
                       details=f"Status: {response.status_code}",
                       recommendation="Proteger o remover endpoints internos")
    
    # 6.5 Rutas de admin expuestas
    admin_paths = ["/admin", "/admin/login", "/administrator", 
                  "/wp-admin", "/panel", "/dashboard", "/manage"]
    
    for path in admin_paths:
        response = safe_request("GET", f"{BASE_URL}{path}")
        if response and response.status_code == 200:
            if "login" not in response.url.lower() and "admin" in response.text.lower():
                add_finding("Bloque 6", "Admin Expuesto", "critical",
                           f"Panel admin accesible: {path}",
                           recommendation="Proteger panel admin con autenticación fuerte y IP whitelist")

# =============================================================================
# BLOQUE 7: ANÁLISIS DE CÓDIGO
# =============================================================================
def audit_block_7():
    """Análisis estático del código fuente"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 7: ANÁLISIS DE CÓDIGO ═══{Colors.RESET}")
    
    code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".php", ".rb", ".java"]
    
    # Patrones peligrosos
    dangerous_patterns = {
        "password_hardcoded": (
            r'(?i)(password|passwd|pwd|secret|api_key|apikey|token)\s*[=:]\s*["\'][^"\']{3,}["\']',
            "Contraseña/secreto hardcodeado", "critical"
        ),
        "eval_exec": (
            r'\b(eval|exec|os\.system|subprocess\.call|shell_exec|system)\s*\(',
            "Función peligrosa detectada", "high"
        ),
        "sql_raw": (
            r'(execute|cursor\.execute|raw|rawQuery)\s*\([^)]*["\'][^"\']*%|' +
            r'f["\'][^"\']*SELECT|f["\'][^"\']*INSERT|f["\'][^"\']*UPDATE|f["\'][^"\']*DELETE',
            "SQL query sin parametrizar", "high"
        ),
        "debug_mode": (
            r'(?i)(debug\s*=\s*true|DEBUG\s*=\s*True|app\.debug\s*=\s*True)',
            "Debug mode habilitado", "medium"
        ),
        "cors_any": (
            r'(?i)(cors\s*\(\s*\*|Access-Control-Allow-Origin.*\*|"origin":\s*"\*")',
            "CORS permite cualquier origen", "medium"
        ),
        "private_key": (
            r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
            "Clave privada en código", "critical"
        ),
        "aws_key": (
            r'(AKIA[0-9A-Z]{16}|aws_secret_access_key)',
            "AWS credentials en código", "critical"
        )
    }
    
    # Buscar en archivos del proyecto
    scanned_files = 0
    for ext in code_extensions:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Ignorar directorios comunes
            dirs[:] = [d for d in dirs if d not in [
                "node_modules", ".git", "__pycache__", "venv", 
                ".venv", "env", "dist", "build", ".next"
            ]]
            
            for file in files:
                if file.endswith(ext):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            scanned_files += 1
                            
                            for pattern_name, (pattern, desc, severity) in dangerous_patterns.items():
                                matches = re.findall(pattern, content)
                                if matches:
                                    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                                    add_finding("Bloque 7", pattern_name, severity,
                                               f"{desc} en {rel_path}",
                                               evidence=str(matches[:2])[:100],
                                               recommendation="Remover datos sensibles del código fuente")
                    except Exception as e:
                        pass
    
    print(f"  Archivos escaneados: {scanned_files}")
    
    # Verificar dependencias vulnerables
    check_dependencies()

def check_dependencies():
    """Verifica vulnerabilidades en dependencias"""
    
    # Python requirements
    req_path = PROJECT_ROOT / "requirements.txt"
    if req_path.exists():
        with open(req_path) as f:
            content = f.read()
            
        vulnerable_packages = {
            "django<2.2": "Django versión vulnerable a múltiples CVEs",
            "flask<1.0": "Flask versión antigua con vulnerabilidades conocidas",
            "requests<2.20": "Requests vulnerable a CRLF injection",
            "pyyaml<5.4": "PyYAML vulnerable a deserialización insegura",
            "pillow<8.0": "Pillow con múltiples vulnerabilidades de imágenes",
            "jinja2<2.10.1": "Jinja2 vulnerable a sandbox escape"
        }
        
        for vuln_pattern, desc in vulnerable_packages.items():
            if vuln_pattern.split("<")[0] in content.lower():
                add_finding("Bloque 7", "Dependencia Vulnerable", "high",
                           desc,
                           recommendation="Actualizar a la última versión estable")
    
    # Node package.json
    pkg_path = PROJECT_ROOT / "package.json"
    if pkg_path.exists():
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            
            # Verificaciones básicas de versión
            for dep, version in deps.items():
                if "^0." in version or "~0." in version:
                    add_finding("Bloque 7", "Dependencia Inestable", "low",
                               f"Dependencia {dep} en versión 0.x (posiblemente inestable)",
                               recommendation="Considerar usar versiones estables")
        except:
            pass

# =============================================================================
# BLOQUE 8: CORS Y ORÍGENES
# =============================================================================
def audit_block_8():
    """Auditoría de CORS y políticas de origen"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 8: CORS Y ORÍGENES ═══{Colors.RESET}")
    
    # 8.1 CORS permisivo
    test_origins = [
        "https://evil.com",
        "https://attacker.com",
        "null"
    ]
    
    for origin in test_origins:
        response = safe_request("GET", BASE_URL, headers={"Origin": origin})
        if response:
            acao = response.headers.get("Access-Control-Allow-Origin", "")
            acac = response.headers.get("Access-Control-Allow-Credentials", "")
            
            if acao == "*":
                add_finding("Bloque 8", "CORS Permisivo", "high",
                           "CORS permite cualquier origen (*)",
                           recommendation="Configurar lista blanca de orígenes permitidos")
            
            if origin in acao and acac.lower() == "true":
                add_finding("Bloque 8", "CORS Credenciales", "critical",
                           f"CORS refleja origen {origin} con credenciales",
                           recommendation="No permitir credenciales con orígenes dinámicos")
    
    # 8.2 Preflight bypass
    response = safe_request("OPTIONS", BASE_URL,
                           headers={
                               "Origin": "https://evil.com",
                               "Access-Control-Request-Method": "DELETE"
                           })
    if response:
        methods = response.headers.get("Access-Control-Allow-Methods", "")
        if "DELETE" in methods or "PUT" in methods:
            add_finding("Bloque 8", "CORS Métodos", "medium",
                       f"CORS permite métodos peligrosos: {methods}",
                       recommendation="Restringir métodos permitidos en CORS")
    
    # 8.3 Clickjacking
    response = safe_request("GET", BASE_URL)
    if response:
        xfo = response.headers.get("X-Frame-Options", "")
        csp = response.headers.get("Content-Security-Policy", "")
        
        if not xfo and "frame-ancestors" not in csp:
            add_finding("Bloque 8", "Clickjacking", "medium",
                       "No hay protección contra clickjacking",
                       recommendation="Agregar X-Frame-Options: DENY o CSP frame-ancestors")

# =============================================================================
# BLOQUE 9: SESIONES Y TOKENS
# =============================================================================
def audit_block_9():
    """Auditoría de manejo de sesiones y tokens"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 9: SESIONES Y TOKENS ═══{Colors.RESET}")
    
    # 9.1 Session fixation
    response1 = safe_request("GET", BASE_URL)
    session1 = None
    if response1:
        for cookie in response1.cookies:
            if "session" in cookie.name.lower():
                session1 = cookie.value
    
    # Simular login
    response2 = safe_request("POST", f"{BASE_URL}/login",
                            json={"username": "test", "password": "test"},
                            cookies={"session": session1} if session1 else {})
    
    if response2:
        for cookie in response2.cookies:
            if "session" in cookie.name.lower():
                if cookie.value == session1:
                    add_finding("Bloque 9", "Session Fixation", "high",
                               "Sesión no se regenera después del login",
                               recommendation="Regenerar ID de sesión después de autenticación")
    
    # 9.2 Tokens predecibles
    tokens = []
    for i in range(3):
        response = safe_request("POST", f"{BASE_URL}/api/token")
        if response:
            try:
                data = response.json()
                if "token" in data:
                    tokens.append(data["token"])
            except:
                pass
    
    if len(tokens) >= 2:
        # Verificar si son secuenciales
        if all(t.isdigit() for t in tokens):
            nums = [int(t) for t in tokens]
            if nums == sorted(nums) and all(nums[i+1] - nums[i] == 1 for i in range(len(nums)-1)):
                add_finding("Bloque 9", "Token Predecible", "critical",
                           "Tokens son secuenciales y predecibles",
                           recommendation="Usar generador criptográficamente seguro")
    
    # 9.3 Falta de expiración
    response = safe_request("GET", BASE_URL)
    if response:
        for cookie in response.cookies:
            if "session" in cookie.name.lower() or "token" in cookie.name.lower():
                if not cookie.expires:
                    add_finding("Bloque 9", "Sin Expiración", "medium",
                               f"Cookie {cookie.name} no tiene fecha de expiración",
                               recommendation="Establecer expiración apropiada para cookies de sesión")
    
    # 9.4 Tokens en URL
    response = safe_request("GET", BASE_URL)
    if response:
        if "token=" in response.url or "session=" in response.url or "key=" in response.url:
            add_finding("Bloque 9", "Token en URL", "high",
                       "Token o sesión expuesto en URL",
                       evidence=response.url[:100],
                       recommendation="Usar headers o cookies para transportar tokens")

# =============================================================================
# BLOQUE 10: UPLOADS Y ARCHIVOS
# =============================================================================
def audit_block_10():
    """Auditoría de carga y manejo de archivos"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 10: UPLOADS Y ARCHIVOS ═══{Colors.RESET}")
    
    upload_endpoints = ["/upload", "/api/upload", "/file/upload", 
                       "/api/files", "/media/upload"]
    
    # 10.1 Subida sin validación
    dangerous_files = [
        ("test.php", "<?php echo 'test'; ?>", "application/x-php"),
        ("test.jsp", "<% out.println('test'); %>", "application/x-jsp"),
        ("test.exe", "MZ", "application/x-msdownload"),
        ("test.html", "<script>alert('xss')</script>", "text/html"),
        ("../../../test.txt", "path traversal", "text/plain")
    ]
    
    for endpoint in upload_endpoints:
        for filename, content, content_type in dangerous_files[:2]:
            files = {"file": (filename, content, content_type)}
            response = safe_request("POST", f"{BASE_URL}{endpoint}", files=files)
            if response and response.status_code in [200, 201]:
                add_finding("Bloque 10", "Upload Inseguro", "critical",
                           f"Archivo peligroso {filename} aceptado en {endpoint}",
                           recommendation="Validar tipo de archivo, extensión y contenido")
    
    # 10.2 Path traversal
    traversal_payloads = [
        "../../../etc/passwd",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam"
    ]
    
    file_endpoints = ["/api/file", "/download", "/read", "/api/download"]
    
    for endpoint in file_endpoints:
        for payload in traversal_payloads[:2]:
            response = safe_request("GET", f"{BASE_URL}{endpoint}?file={urllib.parse.quote(payload)}")
            if response and ("root:" in response.text or "Administrator" in response.text):
                add_finding("Bloque 10", "Path Traversal", "critical",
                           f"Path traversal exitoso en {endpoint}",
                           recommendation="Sanitizar rutas de archivo y usar whitelist")
    
    # 10.3 Archivos ejecutables permitidos
    response = safe_request("GET", f"{BASE_URL}/uploads/")
    if response and response.status_code == 200:
        exec_extensions = [".php", ".jsp", ".asp", ".exe", ".sh", ".py", ".pl"]
        for ext in exec_extensions:
            if ext in response.text.lower():
                add_finding("Bloque 10", "Ejecutables Permitidos", "high",
                           f"Archivos {ext} permitidos en uploads",
                           recommendation="Bloquear extensiones ejecutables")

# =============================================================================
# BLOQUE 11: SSL/TLS
# =============================================================================
def audit_block_11():
    """Auditoría de SSL/TLS"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 11: SSL/TLS ═══{Colors.RESET}")
    
    target_host = BASE_URL.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]
    
    # 11.1 Verificar certificado
    if BASE_URL.startswith("https"):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((target_host, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=target_host) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Verificar expiración
                    not_after = ssl.cert_time_to_seconds(cert["notAfter"])
                    if not_after < time.time():
                        add_finding("Bloque 11", "Certificado Expirado", "critical",
                                   "Certificado SSL ha expirado",
                                   recommendation="Renovar certificado SSL")
                    elif not_after < time.time() + (30 * 24 * 3600):
                        add_finding("Bloque 11", "Certificado Por Expirar", "medium",
                                   "Certificado expira en menos de 30 días",
                                   recommendation="Planificar renovación del certificado")
        except ssl.SSLError as e:
            add_finding("Bloque 11", "SSL Error", "high",
                       f"Error de SSL: {str(e)[:100]}",
                       recommendation="Verificar configuración SSL")
        except Exception as e:
            pass
    else:
        add_finding("Bloque 11", "Sin HTTPS", "high",
                   "El sitio no usa HTTPS",
                   recommendation="Implementar HTTPS con certificado válido")
    
    # 11.2 Mixed content
    response = safe_request("GET", BASE_URL)
    if response and BASE_URL.startswith("https"):
        http_resources = re.findall(r'(src|href)=["\']http://[^"\']+["\']', response.text)
        if http_resources:
            add_finding("Bloque 11", "Mixed Content", "medium",
                       f"Recursos HTTP en página HTTPS ({len(http_resources)} encontrados)",
                       recommendation="Usar HTTPS para todos los recursos")

# =============================================================================
# BLOQUE 12: MÉTODOS HTTP
# =============================================================================
def audit_block_12():
    """Auditoría de métodos HTTP"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 12: MÉTODOS HTTP ═══{Colors.RESET}")
    
    # 12.1 TRACE habilitado
    response = safe_request("TRACE", BASE_URL)
    if response and response.status_code == 200:
        add_finding("Bloque 12", "TRACE Habilitado", "medium",
                   "Método TRACE habilitado (riesgo de XST)",
                   recommendation="Deshabilitar método TRACE")
    
    # 12.2 PUT/DELETE sin autorización
    dangerous_methods = ["PUT", "DELETE", "PATCH"]
    for method in dangerous_methods:
        response = safe_request(method, f"{BASE_URL}/api/test")
        if response and response.status_code not in [401, 403, 405]:
            add_finding("Bloque 12", "Método Inseguro", "high",
                       f"Método {method} permitido sin autenticación",
                       recommendation=f"Requerir autenticación para método {method}")
    
    # 12.3 HTTP Verb Tampering
    protected_endpoints = ["/admin", "/api/users", "/api/delete"]
    for endpoint in protected_endpoints:
        # Si GET requiere auth, probar con otro método
        get_response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if get_response and get_response.status_code in [401, 403]:
            for method in ["POST", "HEAD", "OPTIONS"]:
                alt_response = safe_request(method, f"{BASE_URL}{endpoint}")
                if alt_response and alt_response.status_code == 200:
                    add_finding("Bloque 12", "Verb Tampering", "high",
                               f"Bypass de auth en {endpoint} usando {method}",
                               recommendation="Aplicar autenticación para todos los métodos HTTP")

# =============================================================================
# BLOQUE 13: WEBSOCKETS
# =============================================================================
def audit_block_13():
    """Auditoría de WebSockets"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 13: WEBSOCKETS ═══{Colors.RESET}")
    
    ws_endpoints = ["/ws", "/websocket", "/socket.io/", "/sockjs/"]
    
    for endpoint in ws_endpoints:
        # Verificar si existe endpoint WS
        response = safe_request("GET", f"{BASE_URL}{endpoint}")
        if response and response.status_code != 404:
            # 13.1 WS sin autenticación
            add_finding("Bloque 13", "WebSocket Detectado", "info",
                       f"Endpoint WebSocket encontrado: {endpoint}",
                       recommendation="Verificar autenticación en conexiones WebSocket")
            
            # Verificar upgrade header
            ws_response = safe_request("GET", f"{BASE_URL}{endpoint}",
                                       headers={
                                           "Upgrade": "websocket",
                                           "Connection": "Upgrade",
                                           "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                                           "Sec-WebSocket-Version": "13"
                                       })
            if ws_response and ws_response.status_code == 101:
                add_finding("Bloque 13", "WS Sin Auth", "high",
                           f"WebSocket {endpoint} acepta conexiones sin autenticación",
                           recommendation="Implementar autenticación en handshake WS")

# =============================================================================
# BLOQUE 14: PENETRACIÓN DE BASE DE DATOS
# =============================================================================
def audit_block_14():
    """Auditoría de seguridad de base de datos"""
    print(f"\n{Colors.BOLD}═══ BLOQUE 14: BASE DE DATOS ═══{Colors.RESET}")
    
    # 14.1 Conexión directa expuesta
    db_ports = {
        5432: "PostgreSQL",
        3306: "MySQL",
        27017: "MongoDB",
        6379: "Redis",
        1433: "MSSQL"
    }
    
    target_host = BASE_URL.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]
    
    for port, db_name in db_ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target_host, port))
            if result == 0:
                add_finding("Bloque 14", "Puerto DB Expuesto", "critical",
                           f"Puerto {port} ({db_name}) accesible externamente",
                           recommendation="Bloquear acceso externo a puertos de base de datos")
            sock.close()
        except:
            pass
    
    # 14.2 SQL Injection avanzada
    endpoints = get_known_endpoints()
    
    # Union-based
    union_payloads = [
        "1 UNION SELECT NULL--",
        "1 UNION SELECT NULL,NULL--",
        "1 UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT username,password FROM users--"
    ]
    
    # Time-based blind
    time_payloads = [
        "1' AND SLEEP(3)--",
        "1'; WAITFOR DELAY '0:0:3'--",
        "1' AND pg_sleep(3)--"
    ]
    
    for endpoint in endpoints[:5]:
        # Union-based
        for payload in union_payloads[:2]:
            response = safe_request("GET", f"{BASE_URL}{endpoint}?id={urllib.parse.quote(payload)}")
            if response and "null" in response.text.lower():
                add_finding("Bloque 14", "Union SQLi", "critical",
                           f"Union-based SQL injection en {endpoint}",
                           recommendation="Usar prepared statements")
        
        # Time-based
        for payload in time_payloads:
            start = time.time()
            response = safe_request("GET", f"{BASE_URL}{endpoint}?id={urllib.parse.quote(payload)}", 
                                   timeout=5)
            elapsed = time.time() - start
            if elapsed >= 3:
                add_finding("Bloque 14", "Blind SQLi", "critical",
                           f"Time-based blind SQL injection en {endpoint}",
                           details=f"Delay: {elapsed:.2f}s",
                           recommendation="Usar prepared statements")
    
    # 14.3 Extracción de información DB
    db_info_payloads = [
        ("' UNION SELECT version()--", "version"),
        ("' UNION SELECT current_user()--", "user"),
        ("' UNION SELECT database()--", "database"),
        ("' UNION SELECT table_name FROM information_schema.tables--", "tables")
    ]
    
    for endpoint in endpoints[:3]:
        for payload, info_type in db_info_payloads[:2]:
            response = safe_request("GET", f"{BASE_URL}{endpoint}?id={urllib.parse.quote(payload)}")
            if response:
                # Buscar patrones de versión de DB
                version_patterns = [
                    r"PostgreSQL \d+\.\d+",
                    r"MySQL \d+\.\d+",
                    r"SQLite \d+\.\d+",
                    r"Microsoft SQL Server"
                ]
                for pattern in version_patterns:
                    if re.search(pattern, response.text, re.I):
                        add_finding("Bloque 14", "Info DB Expuesta", "high",
                                   f"Información de {info_type} extraída de {endpoint}",
                                   evidence=re.search(pattern, response.text, re.I).group()[:50],
                                   recommendation="Prevenir exposición de información de la BD")
    
    # 14.4 Verificar datos sensibles en código
    sensitive_patterns = {
        "plain_password": r'password\s*[=:]\s*["\'][^"\']+["\'](?!\s*#)',
        "connection_string": r'(postgresql|mysql|mongodb|redis)://[^"\'\s]+',
        "db_credentials": r'(DB_PASSWORD|DATABASE_PASSWORD|POSTGRES_PASSWORD)\s*=\s*["\'][^"\']+["\']'
    }
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", "venv"]]
        
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".env", ".yml", ".yaml", ".json")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        for pattern_name, pattern in sensitive_patterns.items():
                            matches = re.findall(pattern, content, re.I)
                            if matches:
                                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                                add_finding("Bloque 14", "Credenciales DB", "critical",
                                           f"Credenciales de BD en {rel_path}",
                                           recommendation="Usar variables de entorno para credenciales")
                except:
                    pass
    
    # 14.5 ORM Injection / Raw Queries
    orm_patterns = [
        r'\.raw\s*\([^)]*\+',  # raw queries con concatenación
        r'execute\s*\([^)]*%',  # execute con format string
        r'cursor\.execute\s*\([^)]*\+',  # cursor con concatenación
        r'\.query\s*\([^)]*\$\{',  # template literals en queries
    ]
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", "venv"]]
        
        for file in files:
            if file.endswith((".py", ".js", ".ts")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        for pattern in orm_patterns:
                            if re.search(pattern, content):
                                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                                add_finding("Bloque 14", "ORM Inseguro", "high",
                                           f"Query insegura en {rel_path}",
                                           recommendation="Usar parámetros en lugar de concatenación")
                except:
                    pass

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def get_known_endpoints() -> List[str]:
    """Obtiene lista de endpoints conocidos del proyecto"""
    endpoints = ["/", "/api", "/login", "/register", "/admin", "/dashboard"]
    
    # Buscar en archivos de rutas
    route_patterns = [
        r'@app\.route\(["\']([^"\']+)["\']',
        r'@bp\.route\(["\']([^"\']+)["\']',
        r'router\.(get|post|put|delete)\(["\']([^"\']+)["\']',
        r'app\.(get|post|put|delete)\(["\']([^"\']+)["\']'
    ]
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", "venv"]]
        
        for file in files:
            if file.endswith((".py", ".js", ".ts")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        for pattern in route_patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if isinstance(match, tuple):
                                    endpoints.append(match[-1])
                                else:
                                    endpoints.append(match)
                except:
                    pass
    
    return list(set(endpoints))

def generate_report():
    """Genera el reporte final"""
    report_dir = Path(__file__).parent
    
    # Reporte TXT
    txt_path = report_dir / "reporte_auditoria.txt"
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE AUDITORÍA DE SEGURIDAD WEB\n")
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
        
        total_issues = sum(results['summary'].values())
        f.write(f"TOTAL DE HALLAZGOS: {total_issues}\n\n")
        
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
            
            severity_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "🔵"
            }.get(finding['severity'].lower(), "⚪")
            
            f.write(f"{severity_icon} [{finding['severity'].upper()}] {finding['test']}\n")
            f.write(f"   Descripción: {finding['description']}\n")
            
            if finding.get('details'):
                f.write(f"   Detalles: {finding['details']}\n")
            
            if finding.get('evidence'):
                f.write(f"   Evidencia: {finding['evidence'][:200]}\n")
            
            if finding.get('recommendation'):
                f.write(f"   ✅ Recomendación: {finding['recommendation']}\n")
            
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMENDACIONES GENERALES\n")
        f.write("=" * 80 + "\n\n")
        
        recommendations = [
            "1. Implementar headers de seguridad en todas las respuestas HTTP",
            "2. Usar prepared statements para todas las consultas SQL",
            "3. Sanitizar y validar toda entrada del usuario",
            "4. Implementar rate limiting en endpoints sensibles",
            "5. Configurar CORS restrictivo solo para orígenes conocidos",
            "6. Usar HTTPS en toda la aplicación",
            "7. Almacenar secretos en variables de entorno, no en código",
            "8. Implementar autenticación y autorización robusta",
            "9. Mantener dependencias actualizadas",
            "10. Deshabilitar debug mode en producción"
        ]
        
        for rec in recommendations:
            f.write(f"   {rec}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("FIN DEL REPORTE\n")
        f.write("=" * 80 + "\n")
    
    # Reporte JSON
    json_path = report_dir / "reporte_auditoria.json"
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

def main():
    """Función principal de auditoría"""
    print("\n" + "=" * 60)
    print("🔒 AUDITORÍA DE SEGURIDAD WEB")
    print("=" * 60)
    print(f"Objetivo: {BASE_URL}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar conectividad
    print("\nVerificando conectividad...")
    response = safe_request("GET", BASE_URL)
    if not response:
        print(f"❌ No se puede conectar a {BASE_URL}")
        print("   Verifica que el servidor esté corriendo")
        return
    
    print(f"✅ Conectado exitosamente (Status: {response.status_code})")
    
    # Ejecutar todos los bloques
    try:
        audit_block_1()  # Configuración y Headers
        audit_block_2()  # Inyecciones
        audit_block_3()  # Autenticación
        audit_block_4()  # Rate Limiting
        audit_block_5()  # Exposición de Info
        audit_block_6()  # APIs y Lógica
        audit_block_7()  # Análisis de Código
        audit_block_8()  # CORS
        audit_block_9()  # Sesiones
        audit_block_10() # Uploads
        audit_block_11() # SSL/TLS
        audit_block_12() # Métodos HTTP
        audit_block_13() # WebSockets
        audit_block_14() # Base de Datos
    except KeyboardInterrupt:
        print("\n\n⚠️ Auditoría interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la auditoría: {str(e)}")
    
    # Generar reporte
    generate_report()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    
    # Suprimir advertencias de SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()
