// =============================================================================
// BUNK3R SECURITY AUDIT - SCRIPT MAESTRO PARA CONSOLA F12
// =============================================================================
// ADVERTENCIA: Este script EXTRAE Y MUESTRA datos sensibles encontrados.
// - NO compartas capturas de pantalla de la salida
// - Ejecuta en privado
// - Borra la consola despues de revisar (Ctrl+L)
// =============================================================================

(async function BUNK3R_MASTER_AUDIT() {
    'use strict';
    
    const VERSION = '2.0';
    const results = { critical: [], high: [], medium: [], low: [], info: [] };
    const extractedData = { tokens: [], passwords: [], apiKeys: [], cookies: [], storage: [], globals: [], endpoints: [], secrets: [] };
    const baseUrl = window.location.origin;
    
    console.clear();
    console.log('%c' + '='.repeat(70), 'color:#ff0000');
    console.log('%c  BUNK3R MASTER SECURITY AUDIT v' + VERSION, 'font-size:24px;color:#ff0000;font-weight:bold');
    console.log('%c  EXTRACCION DE DATOS SENSIBLES ACTIVADA', 'font-size:14px;color:#ffff00;font-weight:bold');
    console.log('%c' + '='.repeat(70), 'color:#ff0000');
    console.log('%c  ADVERTENCIA: Los datos extraidos se mostraran al final', 'color:#ff8800');
    console.log('%c  NO compartas capturas de esta consola', 'color:#ff8800');
    console.log('%c' + '='.repeat(70) + '\n', 'color:#ff0000');

    const sensitivePatterns = {
        jwt: /eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/g,
        apiKey: /['"]?(api[_-]?key|apikey|api_secret)['"]?\s*[:=]\s*['"]?([a-zA-Z0-9_-]{16,})['"]?/gi,
        awsKey: /AKIA[0-9A-Z]{16}/g,
        googleKey: /AIza[0-9A-Za-z_-]{35}/g,
        stripeKey: /(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}/g,
        privateKey: /-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----/g,
        password: /['"]?(password|passwd|pwd|pass|secret)['"]?\s*[:=]\s*['"]([^'"]{4,})['"]?/gi,
        bearer: /Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/g,
        basicAuth: /Basic\s+[A-Za-z0-9+/=]{10,}/g,
        mongoDb: /mongodb(\+srv)?:\/\/[^\s"']+/g,
        postgres: /postgres(ql)?:\/\/[^\s"']+/g,
        telegram: /[0-9]{9,10}:[A-Za-z0-9_-]{35}/g,
        genericSecret: /['"]?(secret|token|key|credential|auth)['"]?\s*[:=]\s*['"]([^'"]{8,})['"]?/gi
    };

    const sensitiveKeys = ['token', 'auth', 'password', 'secret', 'key', 'jwt', 'session', 'user', 'credit', 'card', 'api', 'bearer', 'credential', 'private', 'wallet', 'seed', 'mnemonic'];

    function addFinding(severity, test, desc, fix, extracted = null) {
        const finding = { test, desc, fix, extracted };
        results[severity].push(finding);
    }

    function extractSecrets(text, source) {
        if (!text || typeof text !== 'string') return;
        
        for (const [type, pattern] of Object.entries(sensitivePatterns)) {
            const matches = text.match(pattern);
            if (matches) {
                matches.forEach(match => {
                    if (match.length > 10 && match.length < 500) {
                        extractedData.secrets.push({
                            type: type,
                            value: match,
                            source: source,
                            timestamp: new Date().toISOString()
                        });
                    }
                });
            }
        }
    }

    // =========================================================================
    // BLOQUE 1: COOKIES (EXTRACCION COMPLETA)
    // =========================================================================
    console.log('%c[1/25] ANALIZANDO COOKIES...', 'font-size:12px;color:#00ff00');
    
    const cookies = document.cookie.split(';');
    cookies.forEach(cookie => {
        const [name, value] = cookie.split('=').map(s => s.trim());
        if (name && value) {
            extractedData.cookies.push({ name, value, httpOnly: false });
            
            sensitiveKeys.forEach(sensitive => {
                if (name.toLowerCase().includes(sensitive) || (value && value.toLowerCase().includes(sensitive))) {
                    addFinding('critical', 'Cookie Sensible Expuesta', 
                        `Cookie "${name}" accesible por JavaScript`,
                        'Agregar flag HttpOnly a cookies sensibles',
                        { name, value: value.substring(0, 100) + (value.length > 100 ? '...' : '') });
                }
            });
            
            extractSecrets(value, `Cookie: ${name}`);
            
            if (/^eyJ/.test(value)) {
                extractedData.tokens.push({ type: 'JWT en Cookie', name, value });
                addFinding('critical', 'JWT en Cookie sin HttpOnly',
                    `Cookie "${name}" contiene JWT expuesto`,
                    'Mover JWT a cookie HttpOnly o usar otro metodo');
            }
        }
    });

    // =========================================================================
    // BLOQUE 2: LOCALSTORAGE (EXTRACCION COMPLETA)
    // =========================================================================
    console.log('%c[2/25] ANALIZANDO LOCALSTORAGE...', 'font-size:12px;color:#00ff00');
    
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        
        extractedData.storage.push({ type: 'localStorage', key, value: value.substring(0, 500) });
        extractSecrets(value, `localStorage: ${key}`);
        
        sensitiveKeys.forEach(sensitive => {
            if (key.toLowerCase().includes(sensitive) || value.toLowerCase().includes(sensitive)) {
                addFinding('critical', 'Dato Sensible en localStorage',
                    `Key "${key}" contiene informacion sensible`,
                    'No almacenar tokens/passwords/secrets en localStorage',
                    { key, value: value.substring(0, 200) + (value.length > 200 ? '...' : '') });
            }
        });
        
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en localStorage', key, value });
            addFinding('critical', 'JWT en localStorage',
                `Key "${key}" contiene token JWT`,
                'Usar cookies HttpOnly para tokens de sesion');
        }
    }

    // =========================================================================
    // BLOQUE 3: SESSIONSTORAGE (EXTRACCION COMPLETA)
    // =========================================================================
    console.log('%c[3/25] ANALIZANDO SESSIONSTORAGE...', 'font-size:12px;color:#00ff00');
    
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const value = sessionStorage.getItem(key);
        
        extractedData.storage.push({ type: 'sessionStorage', key, value: value.substring(0, 500) });
        extractSecrets(value, `sessionStorage: ${key}`);
        
        sensitiveKeys.forEach(sensitive => {
            if (key.toLowerCase().includes(sensitive) || value.toLowerCase().includes(sensitive)) {
                addFinding('critical', 'Dato Sensible en sessionStorage',
                    `Key "${key}" contiene informacion sensible`,
                    'No almacenar datos sensibles en sessionStorage',
                    { key, value: value.substring(0, 200) + (value.length > 200 ? '...' : '') });
            }
        });
    }

    // =========================================================================
    // BLOQUE 4: VARIABLES GLOBALES (EXTRACCION)
    // =========================================================================
    console.log('%c[4/25] ANALIZANDO VARIABLES GLOBALES...', 'font-size:12px;color:#00ff00');
    
    const dangerousGlobals = ['token', 'apiKey', 'api_key', 'secret', 'password', 'auth', 'config', 
                              'user', 'credentials', 'privateKey', 'secretKey', 'jwt', 'bearer',
                              'initData', 'telegramData', 'userData', 'sessionData', 'authToken',
                              'accessToken', 'refreshToken', 'API_KEY', 'SECRET_KEY', 'PRIVATE_KEY'];
    
    dangerousGlobals.forEach(varName => {
        if (window[varName] !== undefined) {
            const val = window[varName];
            const valStr = typeof val === 'object' ? JSON.stringify(val) : String(val);
            
            extractedData.globals.push({ name: varName, value: valStr.substring(0, 300) });
            extractSecrets(valStr, `window.${varName}`);
            
            addFinding('critical', 'Variable Global Sensible',
                `window.${varName} esta expuesto globalmente`,
                'No exponer datos sensibles en variables globales',
                { variable: varName, value: valStr.substring(0, 150) + (valStr.length > 150 ? '...' : '') });
        }
    });

    // Buscar JWTs en cualquier variable de window
    const checkedKeys = new Set();
    Object.keys(window).forEach(key => {
        if (checkedKeys.has(key)) return;
        checkedKeys.add(key);
        
        try {
            const val = window[key];
            if (typeof val === 'string' && val.length > 20 && val.length < 2000) {
                if (/^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(val)) {
                    extractedData.tokens.push({ type: 'JWT en window', key, value: val });
                    addFinding('critical', 'JWT en Variable Global',
                        `window.${key} contiene un JWT`,
                        'No exponer tokens JWT en window',
                        { variable: key, jwt: val });
                }
                
                extractSecrets(val, `window.${key}`);
            }
        } catch(e) {}
    });

    // =========================================================================
    // BLOQUE 5: HEADERS DE SEGURIDAD
    // =========================================================================
    console.log('%c[5/25] VERIFICANDO HEADERS DE SEGURIDAD...', 'font-size:12px;color:#00ff00');
    
    try {
        const resp = await fetch(baseUrl, { method: 'HEAD' });
        const headers = resp.headers;
        
        const securityHeaders = {
            'content-security-policy': { severity: 'critical', desc: 'Protege contra XSS y otros ataques' },
            'x-frame-options': { severity: 'high', desc: 'Protege contra clickjacking' },
            'x-content-type-options': { severity: 'medium', desc: 'Previene MIME sniffing' },
            'strict-transport-security': { severity: 'high', desc: 'Fuerza HTTPS' },
            'x-xss-protection': { severity: 'medium', desc: 'Proteccion XSS del navegador' },
            'referrer-policy': { severity: 'low', desc: 'Controla informacion de referencia' },
            'permissions-policy': { severity: 'low', desc: 'Controla permisos del navegador' }
        };
        
        Object.entries(securityHeaders).forEach(([header, info]) => {
            if (!headers.get(header)) {
                addFinding(info.severity, 'Header de Seguridad Faltante',
                    `No tiene header: ${header}`,
                    `Agregar header ${header} en el servidor. ${info.desc}`);
            }
        });
        
        // Headers que exponen informacion
        ['Server', 'X-Powered-By', 'X-AspNet-Version'].forEach(h => {
            const val = headers.get(h);
            if (val) {
                addFinding('low', 'Informacion del Servidor Expuesta',
                    `Header ${h}: ${val}`,
                    `Remover o ocultar header ${h}`);
            }
        });
    } catch(e) {
        addFinding('info', 'Headers', 'No se pudieron verificar headers', 'Verificar manualmente');
    }

    // =========================================================================
    // BLOQUE 6: SCRIPTS INLINE (BUSQUEDA DE SECRETOS)
    // =========================================================================
    console.log('%c[6/25] ANALIZANDO SCRIPTS INLINE...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('script:not([src])').forEach((script, idx) => {
        const code = script.textContent;
        if (!code || code.length < 10) return;
        
        extractSecrets(code, `Script inline #${idx + 1}`);
        
        // Buscar patrones especificos
        const patterns = [
            { name: 'API Key', regex: /['"]?(api[_-]?key|apikey)['"]?\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { name: 'Password', regex: /['"]?(password|passwd|pwd)['"]?\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { name: 'Secret', regex: /['"]?(secret|token|private)['"]?\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { name: 'Bearer Token', regex: /Bearer\s+[a-zA-Z0-9_.-]+/gi },
            { name: 'Connection String', regex: /(mongodb|postgres|mysql):\/\/[^\s"']+/gi }
        ];
        
        patterns.forEach(({ name, regex }) => {
            const matches = code.match(regex);
            if (matches) {
                matches.forEach(match => {
                    extractedData.secrets.push({ type: name, value: match, source: `Script inline #${idx + 1}` });
                    addFinding('critical', `${name} en Codigo Inline`,
                        `Script #${idx + 1} contiene ${name}`,
                        'Mover secretos al backend, nunca en frontend',
                        { found: match.substring(0, 100) });
                });
            }
        });
    });

    // =========================================================================
    // BLOQUE 7: SCRIPTS EXTERNOS
    // =========================================================================
    console.log('%c[7/25] ANALIZANDO SCRIPTS EXTERNOS...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('script[src]').forEach(script => {
        const src = script.src;
        if (src && src.startsWith('http') && !src.includes(window.location.hostname)) {
            if (!script.integrity) {
                addFinding('high', 'Script Externo sin SRI',
                    `Script: ${src.substring(0, 80)}...`,
                    'Agregar atributo integrity con hash SRI para verificar integridad');
            }
            
            // Verificar si el script esta en HTTP en pagina HTTPS
            if (window.location.protocol === 'https:' && src.startsWith('http:')) {
                addFinding('critical', 'Script HTTP en Pagina HTTPS',
                    `Mixed content: ${src}`,
                    'Usar HTTPS para todos los recursos');
            }
        }
    });

    // =========================================================================
    // BLOQUE 8: FORMULARIOS
    // =========================================================================
    console.log('%c[8/25] ANALIZANDO FORMULARIOS...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('form').forEach((form, idx) => {
        if (form.action && form.action.startsWith('http:')) {
            addFinding('critical', 'Formulario sin HTTPS',
                `Formulario #${idx + 1} envia datos por HTTP inseguro`,
                'Usar HTTPS para todos los formularios');
        }
        
        // Inputs de password
        form.querySelectorAll('input[type="password"]').forEach(input => {
            if (input.autocomplete === 'on' || !input.autocomplete) {
                addFinding('medium', 'Password con Autocomplete',
                    'Input password permite autocompletado del navegador',
                    'Agregar autocomplete="off" o "new-password"');
            }
        });
        
        // Buscar CSRF token
        const csrfInput = form.querySelector('input[name*="csrf"], input[name*="token"]');
        if (!csrfInput && form.method && form.method.toUpperCase() === 'POST') {
            addFinding('high', 'Sin Proteccion CSRF',
                `Formulario #${idx + 1} POST sin token CSRF visible`,
                'Implementar proteccion CSRF en formularios');
        }
    });

    // =========================================================================
    // BLOQUE 9: INPUTS HIDDEN
    // =========================================================================
    console.log('%c[9/25] ANALIZANDO INPUTS HIDDEN...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('input[type="hidden"]').forEach(input => {
        const name = input.name || input.id || '';
        const value = input.value || '';
        
        extractSecrets(value, `Input hidden: ${name}`);
        
        sensitiveKeys.forEach(sensitive => {
            if (name.toLowerCase().includes(sensitive) || value.toLowerCase().includes(sensitive)) {
                addFinding('high', 'Input Hidden Sensible',
                    `Input hidden "${name}" puede contener datos sensibles`,
                    'No poner tokens/passwords en inputs hidden visibles en DOM',
                    { name, value: value.substring(0, 100) });
            }
        });
        
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en input hidden', name, value });
            addFinding('critical', 'JWT en Input Hidden',
                `Input "${name}" contiene token JWT expuesto en DOM`,
                'No exponer JWTs en el DOM');
        }
    });

    // =========================================================================
    // BLOQUE 10: COMENTARIOS HTML
    // =========================================================================
    console.log('%c[10/25] BUSCANDO COMENTARIOS HTML SENSIBLES...', 'font-size:12px;color:#00ff00');
    
    const htmlContent = document.documentElement.innerHTML;
    const comments = htmlContent.match(/<!--[\s\S]*?-->/g) || [];
    
    comments.forEach(comment => {
        const lower = comment.toLowerCase();
        extractSecrets(comment, 'Comentario HTML');
        
        const hasSensitive = sensitiveKeys.some(k => lower.includes(k));
        const hasDebug = ['todo', 'fixme', 'hack', 'bug', 'xxx', 'debug'].some(k => lower.includes(k));
        
        if (hasSensitive) {
            addFinding('high', 'Comentario HTML con Info Sensible',
                comment.substring(0, 150) + '...',
                'Remover comentarios sensibles en produccion');
        } else if (hasDebug) {
            addFinding('medium', 'Comentario de Debug en Produccion',
                comment.substring(0, 100) + '...',
                'Remover comentarios TODO/FIXME/DEBUG en produccion');
        }
    });

    // =========================================================================
    // BLOQUE 11: DATA ATTRIBUTES
    // =========================================================================
    console.log('%c[11/25] ANALIZANDO DATA ATTRIBUTES...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('*').forEach(el => {
        if (el.dataset) {
            Object.entries(el.dataset).forEach(([key, value]) => {
                if (value) {
                    extractSecrets(value, `data-${key}`);
                    
                    sensitiveKeys.forEach(sensitive => {
                        if (key.toLowerCase().includes(sensitive) || value.toLowerCase().includes(sensitive)) {
                            addFinding('high', 'Data Attribute Sensible',
                                `data-${key} contiene informacion sensible`,
                                'No almacenar datos sensibles en data attributes',
                                { attribute: `data-${key}`, value: value.substring(0, 100) });
                        }
                    });
                }
            });
        }
    });

    // =========================================================================
    // BLOQUE 12: IFRAMES
    // =========================================================================
    console.log('%c[12/25] ANALIZANDO IFRAMES...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('iframe').forEach(iframe => {
        if (!iframe.sandbox) {
            addFinding('medium', 'Iframe sin Sandbox',
                `Iframe: ${iframe.src?.substring(0, 50) || 'sin src'}`,
                'Agregar atributo sandbox a iframes para limitar permisos');
        }
        
        if (iframe.src && iframe.src.startsWith('http:') && window.location.protocol === 'https:') {
            addFinding('high', 'Iframe HTTP en Pagina HTTPS',
                `Iframe carga contenido inseguro: ${iframe.src}`,
                'Usar HTTPS para todos los iframes');
        }
    });

    // =========================================================================
    // BLOQUE 13: LINKS PELIGROSOS
    // =========================================================================
    console.log('%c[13/25] ANALIZANDO LINKS...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('a[href^="javascript:"]').forEach(link => {
        addFinding('high', 'Link javascript:',
            `Enlace con javascript: potencialmente peligroso`,
            'Evitar javascript: en href, usar addEventListener');
    });
    
    document.querySelectorAll('a[target="_blank"]:not([rel*="noopener"])').forEach(link => {
        addFinding('medium', 'Link sin noopener',
            `Link a nueva ventana sin rel="noopener"`,
            'Agregar rel="noopener noreferrer" a links con target="_blank"');
    });

    // =========================================================================
    // BLOQUE 14: EVENT HANDLERS INLINE
    // =========================================================================
    console.log('%c[14/25] ANALIZANDO EVENT HANDLERS...', 'font-size:12px;color:#00ff00');
    
    const dangerousHandlers = ['onclick', 'onmouseover', 'onerror', 'onload', 'onfocus', 'onblur'];
    dangerousHandlers.forEach(handler => {
        const elements = document.querySelectorAll(`[${handler}]`);
        if (elements.length > 0) {
            addFinding('medium', 'Event Handler Inline',
                `${elements.length} elementos con ${handler} inline`,
                'Usar addEventListener en lugar de handlers inline (mejor para CSP)');
        }
    });

    // =========================================================================
    // BLOQUE 15: MIXED CONTENT
    // =========================================================================
    console.log('%c[15/25] VERIFICANDO MIXED CONTENT...', 'font-size:12px;color:#00ff00');
    
    if (window.location.protocol === 'https:') {
        document.querySelectorAll('[src^="http:"], link[href^="http:"]').forEach(el => {
            const url = el.src || el.href;
            if (url && !el.tagName.match(/^A$/i)) {
                addFinding('high', 'Mixed Content',
                    `Recurso HTTP en pagina HTTPS: ${url.substring(0, 60)}`,
                    'Usar HTTPS para todos los recursos');
            }
        });
    }

    // =========================================================================
    // BLOQUE 16: DEBUG MODE
    // =========================================================================
    console.log('%c[16/25] VERIFICANDO MODO DEBUG...', 'font-size:12px;color:#00ff00');
    
    const debugVars = ['DEBUG', 'debug', 'isDebug', 'IS_DEBUG', 'DEV', 'dev', 'isDev', 'DEVELOPMENT'];
    debugVars.forEach(v => {
        if (window[v] === true || window[v] === 'true' || window[v] === 1) {
            addFinding('high', 'Modo Debug Activo',
                `window.${v} = ${window[v]}`,
                'Desactivar modo debug en produccion');
        }
    });

    // =========================================================================
    // BLOQUE 17: ENDPOINTS EN CODIGO
    // =========================================================================
    console.log('%c[17/25] DESCUBRIENDO ENDPOINTS...', 'font-size:12px;color:#00ff00');
    
    const endpoints = new Set();
    
    document.querySelectorAll('script:not([src])').forEach(script => {
        const code = script.textContent || '';
        
        // Patrones de endpoints
        const patterns = [
            /['"`](\/api\/[^'"`\s]+)['"`]/g,
            /fetch\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /axios\.\w+\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /url\s*[:=]\s*['"`]([^'"`]*\/api\/[^'"`]+)['"`]/g,
            /endpoint\s*[:=]\s*['"`]([^'"`]+)['"`]/g
        ];
        
        patterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(code)) !== null) {
                if (match[1] && match[1].length < 200) {
                    endpoints.add(match[1]);
                }
            }
        });
    });
    
    if (endpoints.size > 0) {
        extractedData.endpoints = Array.from(endpoints);
        addFinding('info', 'Endpoints Descubiertos',
            `${endpoints.size} endpoints API encontrados en codigo JS`,
            'Verificar que todos los endpoints requieran autenticacion adecuada');
    }

    // =========================================================================
    // BLOQUE 18: SERVICE WORKERS
    // =========================================================================
    console.log('%c[18/25] VERIFICANDO SERVICE WORKERS...', 'font-size:12px;color:#00ff00');
    
    if ('serviceWorker' in navigator) {
        try {
            const registrations = await navigator.serviceWorker.getRegistrations();
            registrations.forEach(reg => {
                addFinding('info', 'Service Worker Activo',
                    `SW: ${reg.active?.scriptURL || 'registrado'}`,
                    'Verificar que el SW no cachee datos sensibles');
            });
        } catch(e) {}
    }

    // =========================================================================
    // BLOQUE 19: PERMISOS DEL NAVEGADOR
    // =========================================================================
    console.log('%c[19/25] VERIFICANDO PERMISOS...', 'font-size:12px;color:#00ff00');
    
    if (navigator.permissions) {
        const permsToCheck = ['geolocation', 'notifications', 'camera', 'microphone', 'clipboard-read'];
        for (const perm of permsToCheck) {
            try {
                const status = await navigator.permissions.query({ name: perm });
                if (status.state === 'granted') {
                    addFinding('low', 'Permiso Concedido',
                        `Permiso "${perm}" esta activo`,
                        'Verificar que el permiso sea necesario para la aplicacion');
                }
            } catch(e) {}
        }
    }

    // =========================================================================
    // BLOQUE 20: WEBSOCKETS
    // =========================================================================
    console.log('%c[20/25] ANALIZANDO WEBSOCKETS...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('script:not([src])').forEach(script => {
        const code = script.textContent || '';
        
        const wsMatch = code.match(/new\s+WebSocket\s*\(\s*['"`]([^'"`]+)['"`]/g);
        if (wsMatch) {
            wsMatch.forEach(ws => {
                if (ws.includes('ws://') && window.location.protocol === 'https:') {
                    addFinding('high', 'WebSocket Inseguro',
                        'WebSocket usa ws:// en pagina HTTPS',
                        'Usar wss:// para conexiones WebSocket seguras');
                }
                extractedData.endpoints.push(ws);
            });
        }
    });

    // =========================================================================
    // BLOQUE 21: POSTMESSAGE
    // =========================================================================
    console.log('%c[21/25] ANALIZANDO POSTMESSAGE...', 'font-size:12px;color:#00ff00');
    
    document.querySelectorAll('script:not([src])').forEach(script => {
        const code = script.textContent || '';
        
        if (code.includes('addEventListener') && code.includes('message')) {
            if (!code.includes('event.origin') && !code.includes('e.origin')) {
                addFinding('high', 'PostMessage sin Validacion de Origen',
                    'Listener de message sin verificar event.origin',
                    'Siempre validar event.origin en listeners de postMessage');
            }
        }
        
        if (code.includes('.postMessage(') && code.includes("'*'")) {
            addFinding('high', 'PostMessage a Cualquier Origen',
                "postMessage usa '*' como targetOrigin",
                'Especificar origen exacto en postMessage, no usar *');
        }
    });

    // =========================================================================
    // BLOQUE 22: TELEGRAM-SPECIFIC (Para BUNK3R)
    // =========================================================================
    console.log('%c[22/25] VERIFICANDO DATOS DE TELEGRAM...', 'font-size:12px;color:#00ff00');
    
    // Buscar initData de Telegram
    const telegramPatterns = [
        { name: 'Telegram initData', pattern: /initData\s*[:=]\s*['"`]([^'"`]+)['"`]/g },
        { name: 'Telegram User ID', pattern: /telegram_id\s*[:=]\s*['"`]?(\d{5,15})['"`]?/g },
        { name: 'Bot Token', pattern: /bot_token\s*[:=]\s*['"`](\d+:[A-Za-z0-9_-]+)['"`]/gi },
        { name: 'Telegram Hash', pattern: /hash\s*[:=]\s*['"`]([a-f0-9]{64})['"`]/g }
    ];
    
    [localStorage, sessionStorage].forEach(storage => {
        for (let i = 0; i < storage.length; i++) {
            const key = storage.key(i);
            const value = storage.getItem(key);
            
            telegramPatterns.forEach(({ name, pattern }) => {
                const matches = value.match(pattern);
                if (matches) {
                    extractedData.secrets.push({ type: name, value: matches[0], source: `${storage === localStorage ? 'localStorage' : 'sessionStorage'}: ${key}` });
                    addFinding('critical', `${name} Expuesto`,
                        `Encontrado en ${key}`,
                        'Datos de Telegram deben manejarse de forma segura',
                        { found: matches[0].substring(0, 80) });
                }
            });
        }
    });

    // =========================================================================
    // BLOQUE 23: CREDENCIALES EN URL
    // =========================================================================
    console.log('%c[23/25] VERIFICANDO URL ACTUAL...', 'font-size:12px;color:#00ff00');
    
    const currentUrl = window.location.href;
    const urlParams = new URLSearchParams(window.location.search);
    
    sensitiveKeys.forEach(key => {
        if (urlParams.has(key) || urlParams.has(key.toLowerCase()) || urlParams.has(key.toUpperCase())) {
            const value = urlParams.get(key) || urlParams.get(key.toLowerCase()) || urlParams.get(key.toUpperCase());
            addFinding('critical', 'Dato Sensible en URL',
                `Parametro "${key}" visible en URL`,
                'No pasar tokens/passwords en URL, usar headers o body',
                { param: key, value: value?.substring(0, 50) });
        }
    });
    
    // JWT en URL
    if (currentUrl.match(/[?&](token|jwt|auth)=eyJ/)) {
        addFinding('critical', 'JWT en URL',
            'Token JWT visible en la URL del navegador',
            'Nunca pasar JWTs en URL, usar headers Authorization');
    }

    // =========================================================================
    // BLOQUE 24: CONSOLE LOGS EXISTENTES
    // =========================================================================
    console.log('%c[24/25] VERIFICANDO CONSOLE OVERRIDES...', 'font-size:12px;color:#00ff00');
    
    // Verificar si console fue modificado
    if (console.log.toString().indexOf('[native code]') === -1) {
        addFinding('info', 'Console Modificado',
            'console.log ha sido sobrescrito',
            'Verificar que no se intercepten datos sensibles');
    }

    // =========================================================================
    // BLOQUE 25: BUSQUEDA PROFUNDA EN TODO EL DOM
    // =========================================================================
    console.log('%c[25/25] BUSQUEDA PROFUNDA EN DOM...', 'font-size:12px;color:#00ff00');
    
    const bodyText = document.body?.innerText || '';
    const bodyHtml = document.body?.innerHTML || '';
    
    // Buscar patrones en todo el DOM
    Object.entries(sensitivePatterns).forEach(([type, pattern]) => {
        const textMatches = bodyText.match(pattern);
        const htmlMatches = bodyHtml.match(pattern);
        
        const allMatches = new Set([...(textMatches || []), ...(htmlMatches || [])]);
        
        allMatches.forEach(match => {
            if (!extractedData.secrets.some(s => s.value === match)) {
                extractedData.secrets.push({ type, value: match, source: 'DOM Content' });
            }
        });
    });

    // =========================================================================
    // GENERAR REPORTE FINAL
    // =========================================================================
    
    console.log('\n' + '='.repeat(70));
    console.log('%c  REPORTE DE AUDITORIA COMPLETADO', 'font-size:20px;color:#ff0000;font-weight:bold');
    console.log('='.repeat(70));
    
    // Resumen de vulnerabilidades
    console.log('\n%c  RESUMEN DE VULNERABILIDADES:', 'font-size:16px;color:#00ff00;font-weight:bold');
    console.log('%c  ' + '-'.repeat(40), 'color:#888');
    console.log(`%c  🔴 CRITICO: ${results.critical.length}`, 'color:#ff0000;font-weight:bold;font-size:14px');
    console.log(`%c  🟠 ALTO: ${results.high.length}`, 'color:#ff8800;font-weight:bold;font-size:14px');
    console.log(`%c  🟡 MEDIO: ${results.medium.length}`, 'color:#ffff00;font-weight:bold;font-size:14px');
    console.log(`%c  🟢 BAJO: ${results.low.length}`, 'color:#00ff00;font-weight:bold;font-size:14px');
    console.log(`%c  🔵 INFO: ${results.info.length}`, 'color:#00ffff;font-weight:bold;font-size:14px');
    
    const totalVulns = results.critical.length + results.high.length + results.medium.length + results.low.length;
    console.log(`\n%c  TOTAL VULNERABILIDADES: ${totalVulns}`, 'font-size:18px;color:#ff0000;font-weight:bold');
    
    // =========================================================================
    // MOSTRAR DATOS SENSIBLES EXTRAIDOS
    // =========================================================================
    
    console.log('\n' + '='.repeat(70));
    console.log('%c  DATOS SENSIBLES EXTRAIDOS', 'font-size:20px;color:#ff0000;font-weight:bold;background:#ffff00');
    console.log('%c  ⚠️ ATENCION: ESTOS SON TUS DATOS EXPUESTOS ⚠️', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('='.repeat(70));
    
    // Tokens encontrados
    if (extractedData.tokens.length > 0) {
        console.log('\n%c  🔑 TOKENS EXPUESTOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        extractedData.tokens.forEach((t, i) => {
            console.log(`%c  ${i + 1}. ${t.type}`, 'color:#ff8800');
            console.log(`%c     Ubicacion: ${t.name || t.key}`, 'color:#888');
            console.log(`%c     Valor: ${t.value.substring(0, 100)}${t.value.length > 100 ? '...' : ''}`, 'color:#ff0000');
        });
    }
    
    // Secretos encontrados
    if (extractedData.secrets.length > 0) {
        console.log('\n%c  🔐 SECRETOS/CLAVES ENCONTRADOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        const uniqueSecrets = [...new Map(extractedData.secrets.map(s => [s.value, s])).values()];
        uniqueSecrets.slice(0, 20).forEach((s, i) => {
            console.log(`%c  ${i + 1}. [${s.type}] en ${s.source}`, 'color:#ff8800');
            console.log(`%c     ${s.value.substring(0, 120)}${s.value.length > 120 ? '...' : ''}`, 'color:#ff0000');
        });
        if (uniqueSecrets.length > 20) {
            console.log(`%c  ... y ${uniqueSecrets.length - 20} mas`, 'color:#888');
        }
    }
    
    // Cookies
    if (extractedData.cookies.length > 0) {
        console.log('\n%c  🍪 COOKIES ACCESIBLES POR JS:', 'color:#ff8800;font-size:14px;font-weight:bold');
        extractedData.cookies.forEach((c, i) => {
            console.log(`%c  ${i + 1}. ${c.name} = ${c.value.substring(0, 80)}${c.value.length > 80 ? '...' : ''}`, 'color:#ffff00');
        });
    }
    
    // Storage
    const sensitiveStorage = extractedData.storage.filter(s => 
        sensitiveKeys.some(k => s.key.toLowerCase().includes(k) || s.value.toLowerCase().includes(k))
    );
    if (sensitiveStorage.length > 0) {
        console.log('\n%c  💾 DATOS SENSIBLES EN STORAGE:', 'color:#ff8800;font-size:14px;font-weight:bold');
        sensitiveStorage.forEach((s, i) => {
            console.log(`%c  ${i + 1}. [${s.type}] ${s.key}`, 'color:#ffff00');
            console.log(`%c     ${s.value.substring(0, 150)}${s.value.length > 150 ? '...' : ''}`, 'color:#ff8800');
        });
    }
    
    // Variables globales
    if (extractedData.globals.length > 0) {
        console.log('\n%c  🌐 VARIABLES GLOBALES SENSIBLES:', 'color:#ff8800;font-size:14px;font-weight:bold');
        extractedData.globals.forEach((g, i) => {
            console.log(`%c  ${i + 1}. window.${g.name}`, 'color:#ffff00');
            console.log(`%c     ${g.value.substring(0, 150)}${g.value.length > 150 ? '...' : ''}`, 'color:#ff8800');
        });
    }
    
    // Endpoints
    if (extractedData.endpoints.length > 0) {
        console.log('\n%c  🔗 ENDPOINTS DESCUBIERTOS:', 'color:#00ffff;font-size:14px;font-weight:bold');
        extractedData.endpoints.slice(0, 30).forEach((e, i) => {
            console.log(`%c  ${i + 1}. ${e}`, 'color:#00ffff');
        });
    }
    
    // =========================================================================
    // MOSTRAR VULNERABILIDADES CON DETALLES
    // =========================================================================
    
    console.log('\n' + '='.repeat(70));
    console.log('%c  DETALLES DE VULNERABILIDADES', 'font-size:18px;color:#00ff00;font-weight:bold');
    console.log('='.repeat(70));
    
    if (results.critical.length > 0) {
        console.log('\n%c  🔴 CRITICOS (Arreglar inmediatamente):', 'color:#ff0000;font-size:14px;font-weight:bold');
        results.critical.forEach((r, i) => {
            console.log(`%c  ${i + 1}. ${r.test}`, 'color:#ff0000;font-weight:bold');
            console.log(`%c     Problema: ${r.desc}`, 'color:#ff8888');
            console.log(`%c     Solucion: ${r.fix}`, 'color:#88ff88');
            if (r.extracted) {
                console.log(`%c     Datos: ${JSON.stringify(r.extracted).substring(0, 200)}`, 'color:#ffff00');
            }
        });
    }
    
    if (results.high.length > 0) {
        console.log('\n%c  🟠 ALTOS:', 'color:#ff8800;font-size:14px;font-weight:bold');
        results.high.forEach((r, i) => {
            console.log(`%c  ${i + 1}. ${r.test}: ${r.desc}`, 'color:#ff8800');
            console.log(`%c     Solucion: ${r.fix}`, 'color:#88ff88');
        });
    }
    
    if (results.medium.length > 0) {
        console.log('\n%c  🟡 MEDIOS:', 'color:#ffff00;font-size:14px;font-weight:bold');
        results.medium.slice(0, 15).forEach((r, i) => {
            console.log(`%c  ${i + 1}. ${r.test}: ${r.desc}`, 'color:#ffff00');
        });
        if (results.medium.length > 15) {
            console.log(`%c  ... y ${results.medium.length - 15} mas`, 'color:#888');
        }
    }
    
    // =========================================================================
    // EXPORTAR RESULTADOS
    // =========================================================================
    
    console.log('\n' + '='.repeat(70));
    console.log('%c  EXPORTAR RESULTADOS', 'font-size:16px;color:#00ff00;font-weight:bold');
    console.log('='.repeat(70));
    
    const fullReport = {
        metadata: {
            url: window.location.href,
            date: new Date().toISOString(),
            version: VERSION,
            userAgent: navigator.userAgent
        },
        summary: {
            critical: results.critical.length,
            high: results.high.length,
            medium: results.medium.length,
            low: results.low.length,
            info: results.info.length,
            total: totalVulns
        },
        vulnerabilities: results,
        extractedData: extractedData
    };
    
    window.BUNK3R_AUDIT_RESULTS = fullReport;
    window.BUNK3R_EXTRACTED_DATA = extractedData;
    
    console.log('%c  Para copiar todo el reporte:', 'color:#00ff00');
    console.log('%c  copy(BUNK3R_AUDIT_RESULTS)', 'color:#00ffff;font-weight:bold');
    console.log('%c  Para copiar solo los datos extraidos:', 'color:#00ff00');
    console.log('%c  copy(BUNK3R_EXTRACTED_DATA)', 'color:#00ffff;font-weight:bold');
    console.log('%c  Para descargar como archivo JSON:', 'color:#00ff00');
    console.log('%c  BUNK3R_DOWNLOAD_REPORT()', 'color:#00ffff;font-weight:bold');
    
    // Funcion para descargar
    window.BUNK3R_DOWNLOAD_REPORT = function() {
        const blob = new Blob([JSON.stringify(fullReport, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bunk3r_audit_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        console.log('%c  Archivo descargado!', 'color:#00ff00');
    };
    
    console.log('\n' + '='.repeat(70));
    console.log('%c  AUDITORIA COMPLETADA', 'font-size:20px;color:#00ff00;font-weight:bold');
    console.log('%c  Recuerda: Borra la consola (Ctrl+L) cuando termines', 'color:#ff8800');
    console.log('='.repeat(70));
    
    return fullReport;
})();
