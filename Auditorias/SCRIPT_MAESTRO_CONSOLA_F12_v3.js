// =============================================================================
// BUNK3R SECURITY AUDIT v3.0 - SCRIPT MAESTRO AVANZADO PARA CONSOLA F12
// =============================================================================
// INCLUYE: Pruebas de inyeccion, endpoints, archivos sensibles, y mas
// ADVERTENCIA: Solo usar en TUS propios sitios web
// =============================================================================

(async function BUNK3R_MASTER_AUDIT_V3() {
    'use strict';
    
    const VERSION = '3.0';
    const baseUrl = window.location.origin;
    const results = { critical: [], high: [], medium: [], low: [], info: [] };
    const extractedData = { 
        tokens: [], passwords: [], apiKeys: [], cookies: [], storage: [], 
        globals: [], endpoints: [], secrets: [], exposedFiles: [], 
        injectionVulns: [], authIssues: []
    };

    console.clear();
    console.log('%c' + '='.repeat(80), 'color:#ff0000');
    console.log('%c  BUNK3R MASTER SECURITY AUDIT v' + VERSION + ' - MODO AVANZADO', 'font-size:24px;color:#ff0000;font-weight:bold');
    console.log('%c  100+ PRUEBAS DE SEGURIDAD | INYECCION | ENDPOINTS | ARCHIVOS', 'font-size:12px;color:#ffff00');
    console.log('%c' + '='.repeat(80), 'color:#ff0000');
    console.log('%c  ADVERTENCIA: Solo usar en sitios propios. NO compartas la salida.', 'color:#ff8800');
    console.log('%c' + '='.repeat(80) + '\n', 'color:#ff0000');

    const sensitivePatterns = {
        jwt: /eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/g,
        apiKey: /['"]?(api[_-]?key|apikey|api_secret)['"]?\s*[:=]\s*['"]?([a-zA-Z0-9_-]{16,})['"]?/gi,
        awsKey: /AKIA[0-9A-Z]{16}/g,
        googleKey: /AIza[0-9A-Za-z_-]{35}/g,
        stripeKey: /(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}/g,
        privateKey: /-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----/g,
        password: /['"]?(password|passwd|pwd|pass)['"]?\s*[:=]\s*['"]([^'"]{4,})['"]?/gi,
        bearer: /Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/g,
        telegram: /[0-9]{8,10}:[A-Za-z0-9_-]{35}/g,
        mongoDb: /mongodb(\+srv)?:\/\/[^\s"'<>]+/g,
        postgres: /postgres(ql)?:\/\/[^\s"'<>]+/g,
        secretGeneric: /['"]?(secret|private_key|access_token|refresh_token)['"]?\s*[:=]\s*['"]([^'"]{10,})['"]?/gi
    };

    const sensitiveKeys = ['token', 'auth', 'password', 'secret', 'key', 'jwt', 'session', 'user', 'credit', 'card', 'api', 'bearer', 'credential', 'private', 'wallet', 'seed', 'mnemonic', 'hash', 'salt'];

    function addFinding(severity, test, desc, fix, extracted = null) {
        results[severity].push({ test, desc, fix, extracted });
    }

    function extractSecrets(text, source) {
        if (!text || typeof text !== 'string') return;
        for (const [type, pattern] of Object.entries(sensitivePatterns)) {
            const matches = text.match(pattern);
            if (matches) {
                matches.forEach(match => {
                    if (match.length > 10 && match.length < 500) {
                        if (!extractedData.secrets.some(s => s.value === match)) {
                            extractedData.secrets.push({ type, value: match, source });
                        }
                    }
                });
            }
        }
    }

    async function testRequest(url, options = {}) {
        try {
            const resp = await fetch(url, { 
                ...options, 
                mode: 'cors',
                credentials: 'include',
                signal: AbortSignal.timeout(5000)
            });
            return { ok: true, status: resp.status, headers: resp.headers, text: await resp.text().catch(() => '') };
        } catch(e) {
            return { ok: false, error: e.message };
        }
    }

    let currentBlock = 0;
    const totalBlocks = 30;
    function log(msg) {
        currentBlock++;
        console.log(`%c[${currentBlock}/${totalBlocks}] ${msg}`, 'font-size:11px;color:#00ff00');
    }

    // =========================================================================
    // BLOQUE 1-3: COOKIES, LOCALSTORAGE, SESSIONSTORAGE
    // =========================================================================
    log('ANALIZANDO COOKIES...');
    document.cookie.split(';').forEach(cookie => {
        const [name, value] = cookie.split('=').map(s => s.trim());
        if (name && value) {
            extractedData.cookies.push({ name, value: value.substring(0, 200) });
            extractSecrets(value, `Cookie: ${name}`);
            if (/^eyJ/.test(value)) {
                extractedData.tokens.push({ type: 'JWT en Cookie', name, value });
                addFinding('critical', 'JWT en Cookie', `Cookie "${name}" contiene JWT accesible por JS`, 'Usar HttpOnly flag');
            }
            sensitiveKeys.forEach(k => {
                if (name.toLowerCase().includes(k)) {
                    addFinding('critical', 'Cookie Sensible', `Cookie "${name}" expuesta a JavaScript`, 'Agregar HttpOnly', { name, value: value.substring(0, 50) });
                }
            });
        }
    });

    log('ANALIZANDO LOCALSTORAGE...');
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key) || '';
        extractedData.storage.push({ type: 'localStorage', key, value: value.substring(0, 300) });
        extractSecrets(value, `localStorage: ${key}`);
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en localStorage', key, value });
            addFinding('critical', 'JWT en localStorage', `"${key}" contiene token JWT`, 'No guardar JWTs en localStorage');
        }
    }

    log('ANALIZANDO SESSIONSTORAGE...');
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const value = sessionStorage.getItem(key) || '';
        extractedData.storage.push({ type: 'sessionStorage', key, value: value.substring(0, 300) });
        extractSecrets(value, `sessionStorage: ${key}`);
    }

    // =========================================================================
    // BLOQUE 4: VARIABLES GLOBALES
    // =========================================================================
    log('ANALIZANDO VARIABLES GLOBALES...');
    const dangerousGlobals = ['token', 'apiKey', 'api_key', 'secret', 'password', 'auth', 'config', 'user', 'credentials', 'privateKey', 'jwt', 'bearer', 'initData', 'telegramData', 'accessToken', 'refreshToken', 'API_KEY', 'SECRET_KEY', 'BOT_TOKEN', 'TELEGRAM_TOKEN'];
    
    dangerousGlobals.forEach(varName => {
        if (window[varName] !== undefined) {
            const val = window[varName];
            const valStr = typeof val === 'object' ? JSON.stringify(val) : String(val);
            extractedData.globals.push({ name: varName, value: valStr.substring(0, 200) });
            extractSecrets(valStr, `window.${varName}`);
            addFinding('critical', 'Variable Global Sensible', `window.${varName} expuesto`, 'Mover al backend', { variable: varName, value: valStr.substring(0, 100) });
        }
    });

    Object.keys(window).forEach(key => {
        try {
            const val = window[key];
            if (typeof val === 'string' && /^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(val)) {
                extractedData.tokens.push({ type: 'JWT en window', key, value: val });
                addFinding('critical', 'JWT Global', `window.${key} contiene JWT`, 'No exponer JWTs');
            }
        } catch(e) {}
    });

    // =========================================================================
    // BLOQUE 5-6: HEADERS DE SEGURIDAD
    // =========================================================================
    log('VERIFICANDO HEADERS DE SEGURIDAD...');
    try {
        const resp = await fetch(baseUrl, { method: 'HEAD' });
        const h = resp.headers;
        
        const secHeaders = {
            'content-security-policy': 'critical',
            'x-frame-options': 'high',
            'x-content-type-options': 'high',
            'strict-transport-security': 'high',
            'x-xss-protection': 'medium',
            'referrer-policy': 'medium',
            'permissions-policy': 'low'
        };
        
        Object.entries(secHeaders).forEach(([header, sev]) => {
            if (!h.get(header)) {
                addFinding(sev, 'Header Faltante', `No tiene: ${header}`, `Agregar ${header}`);
            }
        });
        
        ['Server', 'X-Powered-By'].forEach(hdr => {
            if (h.get(hdr)) addFinding('low', 'Info Servidor', `${hdr}: ${h.get(hdr)}`, 'Ocultar version');
        });
        
        if (h.get('Access-Control-Allow-Origin') === '*') {
            addFinding('high', 'CORS Abierto', 'Access-Control-Allow-Origin: *', 'Restringir origenes');
        }
    } catch(e) {}

    // =========================================================================
    // BLOQUE 7-8: SCRIPTS Y CODIGO
    // =========================================================================
    log('ANALIZANDO SCRIPTS INLINE...');
    document.querySelectorAll('script:not([src])').forEach((script, idx) => {
        const code = script.textContent || '';
        extractSecrets(code, `Script inline #${idx + 1}`);
        
        [
            { n: 'API Key', r: /api[_-]?key\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Password', r: /password\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Secret', r: /secret\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Token', r: /token\s*[:=]\s*['"]([^'"]{20,})['"]/gi }
        ].forEach(({n, r}) => {
            const m = code.match(r);
            if (m) {
                m.forEach(match => {
                    extractedData.secrets.push({ type: n, value: match, source: `Script #${idx+1}` });
                    addFinding('critical', `${n} en Codigo`, `Script #${idx+1} contiene ${n}`, 'Mover al backend', { found: match.substring(0, 80) });
                });
            }
        });
        
        if (/eval\s*\(/.test(code)) addFinding('high', 'Uso de eval()', 'Codigo usa eval() - peligroso', 'Eliminar eval()');
        if (/innerHTML\s*=/.test(code)) addFinding('medium', 'innerHTML directo', 'Riesgo de XSS', 'Usar textContent');
    });

    log('ANALIZANDO SCRIPTS EXTERNOS...');
    document.querySelectorAll('script[src]').forEach(script => {
        const src = script.src;
        if (src.startsWith('http') && !src.includes(location.hostname)) {
            if (!script.integrity) {
                addFinding('high', 'Script sin SRI', src.substring(0, 70) + '...', 'Agregar integrity hash');
            }
        }
    });

    // =========================================================================
    // BLOQUE 9-12: DOM ANALYSIS
    // =========================================================================
    log('ANALIZANDO FORMULARIOS...');
    document.querySelectorAll('form').forEach((form, idx) => {
        if (form.action?.startsWith('http:')) {
            addFinding('critical', 'Form HTTP', `Form #${idx+1} envia por HTTP`, 'Usar HTTPS');
        }
        if (!form.querySelector('input[name*="csrf"], input[name*="token"]') && form.method?.toUpperCase() === 'POST') {
            addFinding('high', 'Sin CSRF', `Form #${idx+1} sin token CSRF`, 'Agregar CSRF token');
        }
    });

    log('ANALIZANDO INPUTS HIDDEN...');
    document.querySelectorAll('input[type="hidden"]').forEach(input => {
        const name = input.name || input.id || '';
        const value = input.value || '';
        extractSecrets(value, `Hidden: ${name}`);
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT hidden', name, value });
            addFinding('critical', 'JWT en DOM', `Input "${name}" tiene JWT`, 'No exponer JWTs en HTML');
        }
    });

    log('ANALIZANDO DATA ATTRIBUTES...');
    document.querySelectorAll('*').forEach(el => {
        Object.entries(el.dataset || {}).forEach(([k, v]) => {
            if (v && v.length > 20) extractSecrets(v, `data-${k}`);
        });
    });

    log('BUSCANDO COMENTARIOS SENSIBLES...');
    const htmlComments = document.documentElement.innerHTML.match(/<!--[\s\S]*?-->/g) || [];
    htmlComments.forEach(c => {
        extractSecrets(c, 'Comentario HTML');
        if (sensitiveKeys.some(k => c.toLowerCase().includes(k))) {
            addFinding('high', 'Comentario Sensible', c.substring(0, 100), 'Eliminar en produccion');
        }
    });

    // =========================================================================
    // BLOQUE 13-17: DESCUBRIMIENTO DE ENDPOINTS
    // =========================================================================
    log('DESCUBRIENDO ENDPOINTS EN CODIGO...');
    const discoveredEndpoints = new Set();
    
    document.querySelectorAll('script:not([src])').forEach(script => {
        const code = script.textContent || '';
        const patterns = [
            /['"`](\/api\/[^'"`\s]+)['"`]/g,
            /fetch\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /axios\.\w+\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /url\s*[:=]\s*['"`]([^'"`]*\/[^'"`]+)['"`]/g
        ];
        patterns.forEach(p => {
            let m;
            while ((m = p.exec(code)) !== null) {
                if (m[1] && m[1].startsWith('/') && m[1].length < 100) {
                    discoveredEndpoints.add(m[1]);
                }
            }
        });
    });

    extractedData.endpoints = Array.from(discoveredEndpoints);
    
    log('PROBANDO ENDPOINTS SIN AUTENTICACION...');
    const sensitiveEndpoints = Array.from(discoveredEndpoints).filter(e => 
        /admin|user|wallet|balance|transaction|setting|config|profile|account/.test(e.toLowerCase())
    );
    
    for (const ep of sensitiveEndpoints.slice(0, 10)) {
        const result = await testRequest(baseUrl + ep);
        if (result.ok && result.status === 200) {
            extractedData.authIssues.push({ endpoint: ep, status: result.status });
            addFinding('critical', 'Endpoint sin Auth', `${ep} accesible sin autenticacion`, 'Agregar autenticacion', { endpoint: ep });
        }
    }

    // =========================================================================
    // BLOQUE 18-22: PRUEBAS DE ARCHIVOS SENSIBLES
    // =========================================================================
    log('BUSCANDO ARCHIVOS SENSIBLES EXPUESTOS...');
    const sensitiveFiles = [
        '/.env', '/.env.local', '/.env.production', '/.env.backup',
        '/.git/config', '/.git/HEAD', '/.gitignore',
        '/config.py', '/config.json', '/settings.py', '/secrets.json',
        '/backup.sql', '/dump.sql', '/database.sql', '/db.sql',
        '/backup.zip', '/backup.tar.gz', '/site.zip',
        '/debug.log', '/error.log', '/app.log',
        '/phpinfo.php', '/info.php', '/test.php',
        '/admin', '/admin/', '/administrator',
        '/api/docs', '/swagger.json', '/openapi.json',
        '/robots.txt', '/sitemap.xml',
        '/.htaccess', '/.htpasswd',
        '/wp-config.php', '/configuration.php',
        '/package.json', '/composer.json', '/requirements.txt'
    ];

    for (const file of sensitiveFiles) {
        const result = await testRequest(baseUrl + file);
        if (result.ok && result.status === 200 && result.text.length > 0) {
            const isCritical = /\.env|\.git|password|secret|backup|\.sql/.test(file);
            extractedData.exposedFiles.push({ file, size: result.text.length, preview: result.text.substring(0, 200) });
            extractSecrets(result.text, `Archivo: ${file}`);
            addFinding(isCritical ? 'critical' : 'high', 'Archivo Expuesto', `${file} accesible (${result.text.length} bytes)`, 'Bloquear acceso', { file, preview: result.text.substring(0, 100) });
        }
    }

    // =========================================================================
    // BLOQUE 23-25: PRUEBAS DE INYECCION BASICAS
    // =========================================================================
    log('PROBANDO INYECCION SQL BASICA...');
    const sqlPayloads = ["'", "' OR '1'='1", "1' OR '1'='1", "'; DROP TABLE users; --"];
    const sqlErrors = ['sql', 'syntax', 'mysql', 'postgres', 'sqlite', 'oracle', 'error in query'];
    
    for (const ep of sensitiveEndpoints.slice(0, 5)) {
        for (const payload of sqlPayloads.slice(0, 2)) {
            const result = await testRequest(baseUrl + ep + '?id=' + encodeURIComponent(payload));
            if (result.ok && sqlErrors.some(e => result.text.toLowerCase().includes(e))) {
                extractedData.injectionVulns.push({ type: 'SQL Injection', endpoint: ep, payload });
                addFinding('critical', 'Posible SQL Injection', `${ep} responde a payload SQL`, 'Usar prepared statements', { endpoint: ep, payload });
                break;
            }
        }
    }

    log('PROBANDO XSS BASICO...');
    const xssPayload = '<script>alert(1)</script>';
    for (const ep of sensitiveEndpoints.slice(0, 3)) {
        const result = await testRequest(baseUrl + ep + '?q=' + encodeURIComponent(xssPayload));
        if (result.ok && result.text.includes(xssPayload)) {
            extractedData.injectionVulns.push({ type: 'XSS Reflejado', endpoint: ep });
            addFinding('critical', 'XSS Reflejado', `${ep} refleja scripts sin sanitizar`, 'Sanitizar entrada');
        }
    }

    log('PROBANDO TRAVERSAL DE DIRECTORIOS...');
    const traversalPayload = '../../../etc/passwd';
    for (const ep of ['/api/file', '/api/download', '/file', '/download']) {
        const result = await testRequest(baseUrl + ep + '?path=' + encodeURIComponent(traversalPayload));
        if (result.ok && result.text.includes('root:')) {
            extractedData.injectionVulns.push({ type: 'Path Traversal', endpoint: ep });
            addFinding('critical', 'Path Traversal', `${ep} vulnerable a traversal`, 'Validar rutas');
        }
    }

    // =========================================================================
    // BLOQUE 26-28: PRUEBAS DE AUTENTICACION
    // =========================================================================
    log('PROBANDO ENDPOINTS DE LOGIN...');
    const loginEndpoints = ['/login', '/api/login', '/auth/login', '/api/auth/login', '/api/auth/validate'];
    
    for (const ep of loginEndpoints) {
        let successCount = 0;
        for (let i = 0; i < 5; i++) {
            const result = await testRequest(baseUrl + ep, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: 'test', password: 'wrong' + i })
            });
            if (result.ok && result.status !== 429) successCount++;
        }
        if (successCount >= 5) {
            addFinding('high', 'Sin Rate Limiting', `${ep} permite multiples intentos`, 'Implementar rate limiting');
        }
    }

    log('BUSCANDO JWT MAL CONFIGURADOS...');
    for (const ep of loginEndpoints) {
        const result = await testRequest(baseUrl + ep, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: 'test', password: 'test' })
        });
        if (result.ok) {
            const jwtMatch = result.text.match(/eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/);
            if (jwtMatch) {
                try {
                    const header = JSON.parse(atob(jwtMatch[0].split('.')[0]));
                    if (header.alg === 'none') {
                        addFinding('critical', 'JWT Inseguro', 'JWT permite algoritmo none', 'Forzar algoritmo seguro');
                    }
                    extractedData.tokens.push({ type: 'JWT de login', endpoint: ep, value: jwtMatch[0] });
                } catch(e) {}
            }
        }
    }

    // =========================================================================
    // BLOQUE 29-30: OTROS CHECKS
    // =========================================================================
    log('VERIFICANDO WEBSOCKETS...');
    document.querySelectorAll('script:not([src])').forEach(s => {
        const code = s.textContent || '';
        if (/new\s+WebSocket\s*\(\s*['"]ws:/.test(code)) {
            addFinding('high', 'WebSocket Inseguro', 'Usa ws:// en vez de wss://', 'Usar wss://');
        }
    });

    log('VERIFICANDO SERVICE WORKERS...');
    if ('serviceWorker' in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        regs.forEach(r => {
            addFinding('info', 'Service Worker', r.active?.scriptURL || 'registrado', 'Verificar que no cachee datos sensibles');
        });
    }

    // =========================================================================
    // GENERAR REPORTE FINAL
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('%c  REPORTE DE AUDITORIA AVANZADA COMPLETADO', 'font-size:22px;color:#ff0000;font-weight:bold');
    console.log('='.repeat(80));

    const total = results.critical.length + results.high.length + results.medium.length + results.low.length;
    
    console.log('\n%c  RESUMEN DE VULNERABILIDADES:', 'font-size:16px;color:#00ff00;font-weight:bold');
    console.log('%c  ' + '-'.repeat(50), 'color:#888');
    console.log(`%c  🔴 CRITICO: ${results.critical.length}`, 'color:#ff0000;font-weight:bold;font-size:14px');
    console.log(`%c  🟠 ALTO: ${results.high.length}`, 'color:#ff8800;font-weight:bold;font-size:14px');
    console.log(`%c  🟡 MEDIO: ${results.medium.length}`, 'color:#ffff00;font-weight:bold;font-size:14px');
    console.log(`%c  🟢 BAJO: ${results.low.length}`, 'color:#00ff00;font-weight:bold;font-size:14px');
    console.log(`%c  🔵 INFO: ${results.info.length}`, 'color:#00ffff;font-weight:bold;font-size:14px');
    console.log(`\n%c  TOTAL: ${total} vulnerabilidades`, 'font-size:16px;color:#ff0000;font-weight:bold');

    // Mostrar datos extraidos
    console.log('\n' + '='.repeat(80));
    console.log('%c  DATOS SENSIBLES EXTRAIDOS', 'font-size:18px;color:#ff0000;font-weight:bold;background:#ffff00');
    console.log('='.repeat(80));

    if (extractedData.tokens.length > 0) {
        console.log('\n%c  🔑 TOKENS ENCONTRADOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        extractedData.tokens.forEach((t, i) => {
            console.log(`%c  ${i+1}. [${t.type}] ${t.name || t.key || t.endpoint || ''}`, 'color:#ff8800');
            console.log(`%c     ${t.value.substring(0, 80)}...`, 'color:#ff0000');
        });
    }

    if (extractedData.secrets.length > 0) {
        console.log('\n%c  🔐 SECRETOS ENCONTRADOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        const uniqueSecrets = [...new Map(extractedData.secrets.map(s => [s.value, s])).values()];
        uniqueSecrets.slice(0, 15).forEach((s, i) => {
            console.log(`%c  ${i+1}. [${s.type}] en ${s.source}`, 'color:#ff8800');
            console.log(`%c     ${s.value.substring(0, 100)}`, 'color:#ff0000');
        });
    }

    if (extractedData.exposedFiles.length > 0) {
        console.log('\n%c  📁 ARCHIVOS SENSIBLES ACCESIBLES:', 'color:#ff0000;font-size:14px;font-weight:bold');
        extractedData.exposedFiles.forEach((f, i) => {
            console.log(`%c  ${i+1}. ${f.file} (${f.size} bytes)`, 'color:#ff8800');
            console.log(`%c     ${f.preview.substring(0, 80)}...`, 'color:#888');
        });
    }

    if (extractedData.injectionVulns.length > 0) {
        console.log('\n%c  💉 VULNERABILIDADES DE INYECCION:', 'color:#ff0000;font-size:14px;font-weight:bold');
        extractedData.injectionVulns.forEach((v, i) => {
            console.log(`%c  ${i+1}. [${v.type}] ${v.endpoint}`, 'color:#ff0000;font-weight:bold');
        });
    }

    if (extractedData.authIssues.length > 0) {
        console.log('\n%c  🚨 ENDPOINTS SIN AUTENTICACION:', 'color:#ff0000;font-size:14px;font-weight:bold');
        extractedData.authIssues.forEach((a, i) => {
            console.log(`%c  ${i+1}. ${a.endpoint} (HTTP ${a.status})`, 'color:#ff8800');
        });
    }

    if (extractedData.endpoints.length > 0) {
        console.log('\n%c  🔗 ENDPOINTS DESCUBIERTOS (${extractedData.endpoints.length}):', 'color:#00ffff;font-size:14px;font-weight:bold');
        extractedData.endpoints.slice(0, 20).forEach((e, i) => {
            console.log(`%c  ${i+1}. ${e}`, 'color:#00ffff');
        });
    }

    // Detalles de vulnerabilidades
    console.log('\n' + '='.repeat(80));
    console.log('%c  DETALLES DE VULNERABILIDADES', 'font-size:16px;color:#00ff00;font-weight:bold');
    console.log('='.repeat(80));

    if (results.critical.length > 0) {
        console.log('\n%c  🔴 CRITICOS (Arreglar YA):', 'color:#ff0000;font-size:14px;font-weight:bold');
        results.critical.forEach((r, i) => {
            console.log(`%c  ${i+1}. ${r.test}`, 'color:#ff0000;font-weight:bold');
            console.log(`%c     ${r.desc}`, 'color:#ff8888');
            console.log(`%c     FIX: ${r.fix}`, 'color:#88ff88');
        });
    }

    if (results.high.length > 0) {
        console.log('\n%c  🟠 ALTOS:', 'color:#ff8800;font-size:14px;font-weight:bold');
        results.high.slice(0, 15).forEach((r, i) => {
            console.log(`%c  ${i+1}. ${r.test}: ${r.desc.substring(0, 60)}`, 'color:#ff8800');
        });
        if (results.high.length > 15) console.log(`%c  ... y ${results.high.length - 15} mas`, 'color:#888');
    }

    // Exportar
    console.log('\n' + '='.repeat(80));
    console.log('%c  EXPORTAR RESULTADOS', 'font-size:14px;color:#00ff00;font-weight:bold');
    console.log('='.repeat(80));

    const fullReport = {
        metadata: { url: location.href, date: new Date().toISOString(), version: VERSION, userAgent: navigator.userAgent },
        summary: { critical: results.critical.length, high: results.high.length, medium: results.medium.length, low: results.low.length, info: results.info.length, total },
        vulnerabilities: results,
        extractedData
    };

    window.BUNK3R_AUDIT_RESULTS = fullReport;
    window.BUNK3R_EXTRACTED_DATA = extractedData;
    window.BUNK3R_DOWNLOAD_REPORT = function() {
        const blob = new Blob([JSON.stringify(fullReport, null, 2)], { type: 'application/json' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
        a.download = `bunk3r_audit_v3_${new Date().toISOString().split('T')[0]}.json`;
        a.click(); console.log('%c  Descargado!', 'color:#00ff00');
    };

    console.log('%c  copy(BUNK3R_AUDIT_RESULTS) - Copiar reporte', 'color:#00ffff');
    console.log('%c  BUNK3R_DOWNLOAD_REPORT() - Descargar JSON', 'color:#00ffff');
    console.log('\n%c  AUDITORIA v3.0 COMPLETADA', 'font-size:20px;color:#00ff00;font-weight:bold');
    console.log('%c  Borra la consola cuando termines (Ctrl+L)', 'color:#ff8800');

    return fullReport;
})();
