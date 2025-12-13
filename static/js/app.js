const App = {
    tg: null,
    user: null,
    initData: null,
    isOwner: false,
    isDemoMode: false,
    isDevMode: false,
    currentSection: 'dashboard',
    previousSection: null,
    trackings: [],
    delayReasons: [],
    statuses: [],
    userPhotoUrl: null,
    userInitials: 'U',
    twoFactorEnabled: false,
    sessionActivityInterval: null,
    lastActivityTime: Date.now(),
    demoSessionToken: null,
    tonConnectUI: null,
    connectedWallet: null,
    walletSyncedFromServer: false,
    syncedWalletAddress: null,
    deviceId: null,
    isDeviceTrusted: false,
    trustedDeviceName: null,
    USDT_MASTER_ADDRESS: 'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs',
    MERCHANT_WALLET: null,
    _initialDataLoaded: false,
    _securityDataLoaded: false,
    editModeActive: false,
    _intervals: [],
    _eventListeners: [],
    _abortControllers: [],
    _sessionId: Math.random().toString(36).substring(2, 10),
    
    sendLog(action, details = {}, type = 'info') {
        const isMobile = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent);
        const isTelegram = !!window.Telegram?.WebApp?.initData;
        const platform = isTelegram ? 'telegram' : (isMobile ? 'mobile-browser' : 'desktop');
        
        const logData = {
            action,
            type,
            details: {
                ...details,
                timestamp: new Date().toISOString(),
                url: window.location.href
            },
            sessionId: this._sessionId,
            isTelegram,
            platform
        };
        
        this.devLog(`[CLIENT LOG] ${action}:`, details);
        
        fetch('/api/client/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(logData)
        }).catch(() => {});
    },
    
    devLog(...args) {
        if (this.isDevMode || this.isDemoMode) {
            console.log('[DEV]', ...args);
        }
    },
    
    registerInterval(intervalId) {
        this._intervals.push(intervalId);
        return intervalId;
    },
    
    registerEventListener(element, event, handler, options) {
        if (element) {
            element.addEventListener(event, handler, options);
            this._eventListeners.push({ element, event, handler, options });
        }
    },
    
    registerAbortController(controller) {
        this._abortControllers.push(controller);
        return controller;
    },
    
    cleanup() {
        this._intervals.forEach(id => {
            if (id) clearInterval(id);
        });
        this._intervals = [];
        
        if (this.notificationBadgeInterval) {
            clearInterval(this.notificationBadgeInterval);
            this.notificationBadgeInterval = null;
        }
        
        if (this.sessionActivityInterval) {
            clearInterval(this.sessionActivityInterval);
            this.sessionActivityInterval = null;
        }
        
        if (this.walletPollingInterval) {
            clearInterval(this.walletPollingInterval);
            this.walletPollingInterval = null;
        }
        
        this._eventListeners.forEach(({ element, event, handler, options }) => {
            if (element) {
                element.removeEventListener(event, handler, options);
            }
        });
        this._eventListeners = [];
        
        this._abortControllers.forEach(controller => {
            if (controller && !controller.signal.aborted) {
                controller.abort();
            }
        });
        this._abortControllers = [];
        
        if (typeof PublicationsManager !== 'undefined' && PublicationsManager.cleanup) {
            PublicationsManager.cleanup();
        }
        
        this.devLog('App cleanup completed');
    },
    
    async init() {
        this.tg = window.Telegram?.WebApp;
        
        if (!this.tg || !this.tg.initData) {
            this.initDemoMode();
            return;
        }
        
        this.tg.ready();
        this.tg.expand();
        
        if (this.tg.colorScheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        }
        
        this.initData = this.tg.initData;
        
        try {
            const response = await this.apiRequest('/api/validate', {
                method: 'POST',
                body: JSON.stringify({ initData: this.initData })
            });
            
            if (!response.valid) {
                this.showAccessDenied(response.error || 'Acceso no autorizado');
                return;
            }
            
            this.user = response.user;
            this.isOwner = response.isOwner;
            
            if (response.user.photoUrl) {
                this.userPhotoUrl = response.user.photoUrl;
            }
            
            this.userInitials = (response.user.firstName || response.user.username || 'U').charAt(0).toUpperCase();
            
            await this.check2FAStatus();
            
        } catch (error) {
            console.error('Validation error:', error);
            this.showAccessDenied('Error al validar el acceso: ' + error.message);
        }
    },
    
    async initDemoMode() {
        this.devLog('Iniciando modo demo (fuera de Telegram)');
        this.isDemoMode = true;
        this.isOwner = true;
        this.user = {
            id: 0,
            firstName: 'Demo',
            lastName: 'User',
            username: 'demo_user'
        };
        
        this.userInitials = 'D';
        this.userPhotoUrl = null;
        
        sessionStorage.removeItem('demoSessionToken');
        this.demoSessionToken = null;
        
        await this.check2FAStatus();
    },
    
    async check2FAStatus() {
        try {
            if (this.isDemoMode) {
                this.devLog('Modo demo: verificando sesión 2FA...');
                try {
                    await this.apiRequest('/api/2fa/status', { method: 'POST' });
                    this.devLog('Sesión demo válida, completando login');
                    this.completeLogin();
                    return;
                } catch (error) {
                    if (error.message && error.message.includes('DEMO_2FA_REQUIRED')) {
                        this.devLog('Demo 2FA requerido, mostrando pantalla de verificación');
                        this.showDemo2FAVerifyScreen();
                        return;
                    }
                    this.devLog('Error al verificar sesión demo:', error);
                    this.showDemo2FAVerifyScreen();
                    return;
                }
            }
            
            this.devLog('Checking 2FA status...');
            const response = await this.apiRequest('/api/2fa/status', { method: 'POST' });
            this.devLog('2FA status response:', response);
            
            if (response.success) {
                this.twoFactorEnabled = response.enabled;
                
                if (response.requiresVerification) {
                    this.devLog('2FA requires verification, showing verify screen');
                    this.show2FAVerifyScreen();
                    return;
                }
                
                if (!response.configured && this.isOwner) {
                    this.devLog('2FA not configured, showing setup screen');
                    this.show2FASetupScreen();
                    return;
                }
                
                if (response.configured && !response.enabled && this.isOwner) {
                    this.devLog('2FA configured but not enabled, showing setup screen to complete activation');
                    this.show2FASetupScreen();
                    return;
                }
                
                this.devLog('2FA configured or not owner, completing login');
                this.completeLogin();
            } else {
                this.devLog('2FA status failed, completing login');
                this.completeLogin();
            }
        } catch (error) {
            console.error('Error checking 2FA status:', error);
            this.completeLogin();
        }
    },
    
    hidePreloadOverlay() {
        const overlay = document.getElementById('preload-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        }
    },
    
    async show2FASetupScreen() {
        this.devLog('Showing 2FA setup screen');
        this.hidePreloadOverlay();
        document.getElementById('loading-screen').classList.add('hidden');
        const setupScreen = document.getElementById('setup-2fa-screen');
        setupScreen.classList.remove('hidden');
        this.devLog('Setup screen visible:', !setupScreen.classList.contains('hidden'));
        
        try {
            const response = await this.apiRequest('/api/2fa/setup', { method: 'POST' });
            this.devLog('2FA setup response:', response.success ? 'success' : 'failed');
            
            if (response.success) {
                document.getElementById('qr-code-img').src = response.qrCode;
                document.getElementById('secret-code').textContent = response.secret;
            }
        } catch (error) {
            console.error('Error setting up 2FA:', error);
            this.showToast('Error al configurar 2FA', 'error');
        }
        
        this.setup2FAEventListeners();
    },
    
    show2FAVerifyScreen() {
        this.hidePreloadOverlay();
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('verify-2fa-screen').classList.remove('hidden');
        
        this.setupOTPInputs();
        this.setup2FAEventListeners();
        
        const firstInput = document.querySelector('.otp-input[data-index="0"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },
    
    showDemo2FAVerifyScreen() {
        this.devLog('Mostrando pantalla de verificación 2FA para modo demo');
        this.hidePreloadOverlay();
        document.getElementById('loading-screen').classList.add('hidden');
        
        let demoScreen = document.getElementById('demo-2fa-screen');
        if (!demoScreen) {
            demoScreen = document.createElement('div');
            demoScreen.id = 'demo-2fa-screen';
            demoScreen.className = 'auth-screen';
            demoScreen.innerHTML = `
                <div class="auth-container">
                    <div class="auth-header">
                        <div class="auth-icon">🔐</div>
                        <h2>Verificación Demo 2FA</h2>
                        <p>Ingresa el código de los logs del servidor para acceder al modo demo</p>
                    </div>
                    <div class="otp-container">
                        <div id="demo-otp-inputs" class="otp-inputs-container">
                            <input type="text" class="otp-input demo-otp" data-index="0" maxlength="1" inputmode="numeric" pattern="[0-9]">
                            <input type="text" class="otp-input demo-otp" data-index="1" maxlength="1" inputmode="numeric" pattern="[0-9]">
                            <input type="text" class="otp-input demo-otp" data-index="2" maxlength="1" inputmode="numeric" pattern="[0-9]">
                            <input type="text" class="otp-input demo-otp" data-index="3" maxlength="1" inputmode="numeric" pattern="[0-9]">
                            <input type="text" class="otp-input demo-otp" data-index="4" maxlength="1" inputmode="numeric" pattern="[0-9]">
                            <input type="text" class="otp-input demo-otp" data-index="5" maxlength="1" inputmode="numeric" pattern="[0-9]">
                        </div>
                    </div>
                    <div id="demo-2fa-error" class="auth-error hidden"></div>
                    <div id="demo-2fa-loading" class="auth-loading hidden">
                        <div class="loading-spinner"></div>
                        <span>Verificando...</span>
                    </div>
                    <button id="demo-verify-btn" class="btn btn-primary btn-block">Verificar</button>
                    <p class="auth-hint">El código se muestra en los logs del servidor y cambia cada 60 segundos</p>
                </div>
            `;
            document.body.appendChild(demoScreen);
        }
        
        demoScreen.classList.remove('hidden');
        this.setupDemo2FAInputs();
        
        const firstInput = demoScreen.querySelector('.demo-otp[data-index="0"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },
    
    setupDemo2FAInputs() {
        const container = document.getElementById('demo-otp-inputs');
        if (!container) return;
        
        const inputs = container.querySelectorAll('.demo-otp');
        
        inputs.forEach((input, index) => {
            input.value = '';
            input.classList.remove('filled', 'error');
            
            input.addEventListener('input', (e) => {
                const value = e.target.value.replace(/\D/g, '');
                e.target.value = value.slice(0, 1);
                
                if (value) {
                    e.target.classList.add('filled');
                    if (index < inputs.length - 1) {
                        inputs[index + 1].focus();
                    }
                } else {
                    e.target.classList.remove('filled');
                }
                
                const code = Array.from(inputs).map(i => i.value).join('');
                if (code.length === 6) {
                    this.verifyDemo2FA(code);
                }
            });
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace') {
                    if (!e.target.value && index > 0) {
                        inputs[index - 1].focus();
                        inputs[index - 1].value = '';
                        inputs[index - 1].classList.remove('filled');
                    } else {
                        e.target.classList.remove('filled');
                    }
                }
                if (e.key === 'ArrowLeft' && index > 0) {
                    e.preventDefault();
                    inputs[index - 1].focus();
                }
                if (e.key === 'ArrowRight' && index < inputs.length - 1) {
                    e.preventDefault();
                    inputs[index + 1].focus();
                }
            });
            
            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
                pastedData.split('').forEach((digit, i) => {
                    if (inputs[i]) {
                        inputs[i].value = digit;
                        inputs[i].classList.add('filled');
                    }
                });
                const focusIndex = Math.min(pastedData.length, inputs.length - 1);
                inputs[focusIndex].focus();
                
                const code = Array.from(inputs).map(i => i.value).join('');
                if (code.length === 6) {
                    this.verifyDemo2FA(code);
                }
            });
        });
        
        const verifyBtn = document.getElementById('demo-verify-btn');
        if (verifyBtn) {
            verifyBtn.onclick = () => {
                const code = Array.from(inputs).map(i => i.value).join('');
                if (code.length === 6) {
                    this.verifyDemo2FA(code);
                } else {
                    this.showDemo2FAError('Ingresa los 6 dígitos');
                }
            };
        }
    },
    
    async verifyDemo2FA(code) {
        const loadingEl = document.getElementById('demo-2fa-loading');
        const verifyBtn = document.getElementById('demo-verify-btn');
        const errorEl = document.getElementById('demo-2fa-error');
        const inputs = document.querySelectorAll('.demo-otp');
        
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (verifyBtn) verifyBtn.classList.add('hidden');
        if (errorEl) errorEl.classList.add('hidden');
        
        try {
            const response = await fetch('/api/demo/2fa/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            
            const data = await response.json();
            
            if (data.success && data.sessionToken) {
                this.demoSessionToken = data.sessionToken;
                
                const demoScreen = document.getElementById('demo-2fa-screen');
                if (demoScreen) demoScreen.classList.add('hidden');
                
                this.devLog('Demo 2FA verificado, completando login');
                this.completeLogin();
            } else {
                this.showDemo2FAError(data.error || 'Código incorrecto');
                inputs.forEach(input => {
                    input.value = '';
                    input.classList.remove('filled');
                    input.classList.add('error');
                });
                if (inputs[0]) inputs[0].focus();
            }
        } catch (error) {
            console.error('Error verificando demo 2FA:', error);
            this.showDemo2FAError('Error de conexión');
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
            if (verifyBtn) verifyBtn.classList.remove('hidden');
        }
    },
    
    showDemo2FAError(message) {
        const errorEl = document.getElementById('demo-2fa-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
            setTimeout(() => errorEl.classList.add('hidden'), 3000);
        }
    },
    
    setupOTPInputs() {
        const container = document.getElementById('otp-inputs-container');
        if (!container) return;
        
        const inputs = container.querySelectorAll('.otp-input');
        const hiddenInput = document.getElementById('verify-2fa-code');
        
        inputs.forEach((input, index) => {
            input.value = '';
            input.classList.remove('filled', 'error');
            
            input.addEventListener('input', (e) => {
                const value = e.target.value.replace(/\D/g, '');
                e.target.value = value.slice(0, 1);
                
                if (value) {
                    e.target.classList.add('filled');
                    if (index < inputs.length - 1) {
                        inputs[index + 1].focus();
                    }
                } else {
                    e.target.classList.remove('filled');
                }
                
                this.updateHiddenOTPValue(inputs, hiddenInput);
            });
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace') {
                    if (!e.target.value && index > 0) {
                        inputs[index - 1].focus();
                        inputs[index - 1].value = '';
                        inputs[index - 1].classList.remove('filled');
                    } else {
                        e.target.classList.remove('filled');
                    }
                    this.updateHiddenOTPValue(inputs, hiddenInput);
                }
                
                if (e.key === 'ArrowLeft' && index > 0) {
                    e.preventDefault();
                    inputs[index - 1].focus();
                }
                
                if (e.key === 'ArrowRight' && index < inputs.length - 1) {
                    e.preventDefault();
                    inputs[index + 1].focus();
                }
            });
            
            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
                
                pastedData.split('').forEach((digit, i) => {
                    if (inputs[i]) {
                        inputs[i].value = digit;
                        inputs[i].classList.add('filled');
                    }
                });
                
                this.updateHiddenOTPValue(inputs, hiddenInput);
                
                const focusIndex = Math.min(pastedData.length, inputs.length - 1);
                inputs[focusIndex].focus();
            });
            
            input.addEventListener('focus', () => {
                input.select();
            });
        });
    },
    
    updateHiddenOTPValue(inputs, hiddenInput) {
        const code = Array.from(inputs).map(i => i.value).join('');
        if (hiddenInput) {
            hiddenInput.value = code;
        }
        
        if (code.length === 6) {
            this.autoVerify2FA(code);
        }
    },
    
    async autoVerify2FA(code) {
        const verifyBtn = document.getElementById('verify-2fa-btn');
        const loadingEl = document.getElementById('verify-loading');
        const inputs = document.querySelectorAll('.otp-input');
        
        if (verifyBtn) verifyBtn.classList.add('hidden');
        if (loadingEl) loadingEl.classList.remove('hidden');
        
        inputs.forEach(input => input.disabled = true);
        
        const result = await this.verify2FACode(code);
        
        if (verifyBtn) verifyBtn.classList.remove('hidden');
        if (loadingEl) loadingEl.classList.add('hidden');
        inputs.forEach(input => input.disabled = false);
    },
    
    clearOTPInputs() {
        const inputs = document.querySelectorAll('.otp-input');
        const hiddenInput = document.getElementById('verify-2fa-code');
        
        inputs.forEach(input => {
            input.value = '';
            input.classList.remove('filled', 'error');
            input.disabled = false;
        });
        
        if (hiddenInput) hiddenInput.value = '';
        if (inputs[0]) inputs[0].focus();
    },
    
    showOTPError() {
        const inputs = document.querySelectorAll('.otp-input');
        inputs.forEach(input => {
            input.classList.add('error');
        });
        
        setTimeout(() => {
            this.clearOTPInputs();
        }, 600);
    },
    
    setup2FAEventListeners() {
        const setupCodeInput = document.getElementById('setup-2fa-code');
        const verifySetupBtn = document.getElementById('verify-setup-2fa-btn');
        const skipBtn = document.getElementById('skip-2fa-btn');
        const verifyBtn = document.getElementById('verify-2fa-btn');
        
        if (setupCodeInput) {
            setupCodeInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
            });
            
            setupCodeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.target.value.length === 6) {
                    this.verifyAndEnable2FA(e.target.value);
                }
            });
        }
        
        if (verifySetupBtn) {
            verifySetupBtn.addEventListener('click', () => {
                const code = document.getElementById('setup-2fa-code').value;
                if (code.length === 6) {
                    this.verifyAndEnable2FA(code);
                } else {
                    this.showToast('Ingresa un codigo de 6 digitos', 'error');
                }
            });
        }
        
        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                this.skip2FASetup();
            });
        }
        
        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => {
                const code = document.getElementById('verify-2fa-code').value;
                if (code.length === 6) {
                    this.autoVerify2FA(code);
                } else {
                    this.showToast('Ingresa un codigo de 6 digitos', 'error');
                }
            });
        }
    },
    
    async verifyAndEnable2FA(code) {
        try {
            const response = await this.apiRequest('/api/2fa/verify', {
                method: 'POST',
                body: JSON.stringify({ code: code, enable: true })
            });
            
            if (response.success) {
                this.twoFactorEnabled = true;
                this.showToast('2FA activado correctamente', 'success');
                document.getElementById('setup-2fa-screen').classList.add('hidden');
                this.completeLogin();
            } else {
                this.showToast(response.error || 'Codigo incorrecto', 'error');
                document.getElementById('setup-2fa-code').value = '';
                document.getElementById('setup-2fa-code').focus();
            }
        } catch (error) {
            console.error('Error verifying 2FA:', error);
            this.showToast('Error al verificar codigo', 'error');
        }
    },
    
    async verify2FACode(code) {
        const errorEl = document.getElementById('verify-2fa-error');
        
        try {
            const response = await this.apiRequest('/api/2fa/verify', {
                method: 'POST',
                body: JSON.stringify({ code: code, enable: false })
            });
            
            if (response.success) {
                document.getElementById('verify-2fa-screen').classList.add('hidden');
                this.completeLogin();
                return { success: true };
            } else {
                if (errorEl) {
                    errorEl.textContent = response.error || 'Codigo incorrecto';
                    errorEl.classList.remove('hidden');
                }
                this.showOTPError();
                return { success: false, error: response.error };
            }
        } catch (error) {
            console.error('Error verifying 2FA:', error);
            if (errorEl) {
                errorEl.textContent = 'Error al verificar. Intenta de nuevo.';
                errorEl.classList.remove('hidden');
            }
            this.showOTPError();
            return { success: false, error: 'Error de conexion' };
        }
    },
    
    skip2FASetup() {
        document.getElementById('setup-2fa-screen').classList.add('hidden');
        this.completeLogin();
    },
    
    async completeLogin() {
        try {
            this.showMainApp();
            this.setupEventListeners();
            this.setupProfileEventListeners();
            this.updateAllAvatars();
            this.loadInitialData();
            this.loadProfileStats();
            this.startSessionActivityMonitor();
            this.initTonConnect();
            this.loadWalletBalance();
            await this.loadMerchantWallet();
            
            await this.initSecuritySystem();
            
            this.initNotificationFilters();
            this.initTransactionFilters();
            this.updateNotificationBadge();
            
            this.initDevPhaseLock();
            
            if (this.notificationBadgeInterval) {
                clearInterval(this.notificationBadgeInterval);
            }
            this.notificationBadgeInterval = setInterval(() => this.updateNotificationBadge(), 30000);
        } catch (error) {
            console.error('Error in completeLogin():', error);
            this.showMainApp();
        }
    },
    
    initDevPhaseLock() {
        if (this._devPhaseLockInitialized) {
            this.devLog('Dev phase lock already initialized, skipping');
            return;
        }
        this._devPhaseLockInitialized = true;
        
        const lockedSections = ['home', 'marketplace', 'profile'];
        const lockedSidebarItems = ['numeros', 'cuentas', 'metodos', 'planes', 'exchange', 'foro'];
        const unlockedSections = ['wallet', 'bots'];
        const unlockedSidebarItems = ['bots', 'settings'];
        
        const lockIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`;
        
        lockedSections.forEach(section => {
            const navItem = document.querySelector(`.bottom-nav-item[data-nav="${section}"]`);
            if (navItem) {
                navItem.classList.add('dev-locked');
            }
        });
        
        lockedSidebarItems.forEach(section => {
            const sidebarItem = document.querySelector(`.sidebar-item[data-section="${section}"]`);
            if (sidebarItem) {
                sidebarItem.classList.add('dev-locked');
                const lockBadge = document.createElement('span');
                lockBadge.className = 'dev-lock-badge';
                lockBadge.innerHTML = lockIcon;
                sidebarItem.appendChild(lockBadge);
            }
        });
        
        const homeScreen = document.getElementById('home-screen');
        if (homeScreen) {
            homeScreen.classList.add('dev-locked');
            const lockOverlay = document.createElement('div');
            lockOverlay.className = 'dev-lock-icon';
            lockOverlay.innerHTML = `${lockIcon}<span>Proximamente</span>`;
            homeScreen.appendChild(lockOverlay);
        }
        
        const marketplaceScreen = document.getElementById('marketplace-screen');
        if (marketplaceScreen) {
            marketplaceScreen.classList.add('dev-locked');
            const lockOverlay = document.createElement('div');
            lockOverlay.className = 'dev-lock-icon';
            lockOverlay.innerHTML = `${lockIcon}<span>Proximamente</span>`;
            marketplaceScreen.appendChild(lockOverlay);
        }
        
        if (this.isOwner || this.isDemoMode) {
            this.isDevMode = true;
            document.body.classList.add('dev-mode-active');
            this.createDevModeIndicator();
        }
        
        this.devLog('Dev phase lock initialized. DevMode:', this.isDevMode);
    },
    
    createDevModeIndicator() {
        const existing = document.querySelector('.dev-mode-indicator');
        if (existing) existing.remove();
        
        const indicator = document.createElement('div');
        indicator.className = 'dev-mode-indicator';
        indicator.textContent = 'DEV MODE';
        indicator.title = 'Click para alternar modo desarrollador';
        indicator.onclick = () => this.toggleDevMode();
        document.body.appendChild(indicator);
    },
    
    toggleDevMode() {
        this.isDevMode = !this.isDevMode;
        document.body.classList.toggle('dev-mode-active', this.isDevMode);
        
        const indicator = document.querySelector('.dev-mode-indicator');
        if (indicator) {
            indicator.classList.toggle('inactive', !this.isDevMode);
            indicator.textContent = this.isDevMode ? 'DEV MODE' : 'LOCKED';
        }
        
        this.devLog('Dev mode toggled:', this.isDevMode);
    },
    
    async loadMerchantWallet() {
        try {
            const response = await this.apiRequest('/api/wallet/merchant');
            if (response.success && response.merchantWallet) {
                this.MERCHANT_WALLET = response.merchantWallet;
                this.devLog('Merchant wallet loaded:', this.MERCHANT_WALLET);
            }
        } catch (error) {
            console.error('Error loading merchant wallet:', error);
        }
    },
    
    startSessionActivityMonitor() {
        if (this.sessionActivityInterval) {
            clearInterval(this.sessionActivityInterval);
        }
        
        this.lastActivityTime = Date.now();
        if (typeof StateManager !== 'undefined') {
            StateManager.updateActivity();
        }
        
        const activityEvents = ['click', 'touchstart', 'keypress', 'scroll'];
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.lastActivityTime = Date.now();
                if (typeof StateManager !== 'undefined') {
                    StateManager.updateActivity();
                }
            }, { passive: true });
        });
        
        this.sessionActivityInterval = setInterval(() => {
            this.checkSessionValidity();
        }, 60000);
    },
    
    async checkSessionValidity() {
        if (!this.twoFactorEnabled) return;
        
        const lastActivity = typeof StateManager !== 'undefined' 
            ? StateManager.get('lastActivityTime') 
            : this.lastActivityTime;
        const inactiveTime = Date.now() - lastActivity;
        const tenMinutes = 10 * 60 * 1000;
        
        if (inactiveTime >= tenMinutes) {
            Logger?.info('Session expired due to inactivity');
            if (typeof StateManager !== 'undefined') {
                StateManager.set('twoFactorVerified', false);
            }
            this.show2FAVerifyScreen();
            document.getElementById('main-app').classList.add('hidden');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/2fa/session', { method: 'POST' });
            
            if (response.requiresVerification) {
                if (typeof StateManager !== 'undefined') {
                    StateManager.set('twoFactorVerified', false);
                }
                this.show2FAVerifyScreen();
                document.getElementById('main-app').classList.add('hidden');
            } else if (response.sessionValid) {
                if (typeof StateManager !== 'undefined') {
                    StateManager.set('twoFactorVerified', true);
                }
                await this.apiRequest('/api/2fa/refresh', { method: 'POST' });
            }
        } catch (error) {
            Logger?.error('Error checking session:', error);
        }
    },
    
    showDemoBanner() {
        const banner = document.createElement('div');
        banner.className = 'demo-banner';
        banner.innerHTML = '🔧 Modo Demo - Abre desde Telegram para usar todas las funciones';
        banner.style.cssText = 'background: #ff9800; color: #000; text-align: center; padding: 6px; font-size: 11px; position: fixed; top: 50px; left: 0; right: 0; z-index: 999;';
        document.body.insertBefore(banner, document.body.firstChild);
        
        const homeScreen = document.getElementById('home-screen');
        if (homeScreen) {
            homeScreen.style.paddingTop = '100px';
        }
    },
    
    showAccessDenied(message) {
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('access-denied').classList.remove('hidden');
        document.getElementById('denied-message').textContent = message;
    },
    
    showMainApp() {
        this.hidePreloadOverlay();
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        document.getElementById('bottom-nav').classList.remove('hidden');
        
        const userName = this.user.firstName || this.user.username || 'Usuario';
        const userUsername = this.user.username || 'usuario';
        const initials = userName.charAt(0).toUpperCase();
        
        document.getElementById('user-name').textContent = userName;
        
        const homeUserName = document.getElementById('home-user-name');
        if (homeUserName) {
            homeUserName.textContent = userName;
        }
        
        const sidebarName = document.getElementById('sidebar-name');
        if (sidebarName) {
            sidebarName.textContent = userName;
        }
        
        const sidebarAvatar = document.getElementById('sidebar-avatar');
        if (sidebarAvatar) {
            sidebarAvatar.textContent = initials;
        }
        
        const bottomNavAvatar = document.getElementById('bottom-nav-avatar');
        if (bottomNavAvatar) {
            bottomNavAvatar.textContent = initials;
        }
        
        const profileModalAvatar = document.getElementById('profile-modal-avatar');
        if (profileModalAvatar) {
            profileModalAvatar.textContent = initials;
        }
        
        const profileModalName = document.getElementById('profile-modal-name');
        if (profileModalName) {
            profileModalName.textContent = userName;
        }
        
        const profileModalUsername = document.getElementById('profile-modal-username');
        if (profileModalUsername) {
            profileModalUsername.textContent = '@' + userUsername;
        }
        
        this.updateSidebarRole();
    },
    
    openModule(moduleName) {
        if (moduleName === 'tracking') {
            document.getElementById('home-screen').classList.add('hidden');
            document.getElementById('tracking-module').classList.remove('hidden');
            this.loadInitialData();
            
            if (this.tg && this.tg.BackButton) {
                this.tg.BackButton.show();
            }
        }
    },
    
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (!sidebar) return;
        
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        } else {
            sidebar.classList.add('open');
            if (overlay) overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
        }
    },
    
    closeSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.classList.remove('sidebar-open');
    },
    
    goToHome(animate = true) {
        const activeScreens = document.querySelectorAll('.page-screen:not(.hidden), #tracking-module:not(.hidden)');
        const homeScreen = document.getElementById('home-screen');
        const isHomeAlreadyVisible = homeScreen && !homeScreen.classList.contains('hidden');
        
        if (isHomeAlreadyVisible) {
            this.updateBottomNavActive('home');
            return;
        }
        
        document.querySelectorAll('.page-screen, #home-screen, #tracking-module').forEach(screen => {
            screen.classList.remove('page-enter', 'page-exit');
        });
        
        const showHome = () => {
            this.hideAllScreens();
            if (homeScreen) {
                homeScreen.classList.remove('hidden');
            }
            
            this.updateBottomNavActive('home');
            this.updateFloatingButtonVisibility('home');
            
            if (this.tg && this.tg.BackButton) {
                this.tg.BackButton.hide();
            }
            
            this.currentSection = 'home';
            if (typeof StateManager !== 'undefined') {
                StateManager.setSection('home');
            }
        };
        
        if (animate && activeScreens.length > 0) {
            activeScreens.forEach(screen => screen.classList.add('page-exit'));
            setTimeout(showHome, 150);
        } else {
            showHome();
        }
    },
    
    setupEventListeners() {
        document.querySelectorAll('.menu-card:not(.disabled)').forEach(card => {
            card.addEventListener('click', () => {
                const module = card.dataset.module;
                if (module && module !== 'coming-soon') {
                    this.openModule(module);
                }
            });
        });
        
        const btnGoHome = document.getElementById('btn-go-home');
        if (btnGoHome) {
            btnGoHome.addEventListener('click', () => {
                this.goToHome();
            });
        }
        
        const hamburgerMenu = document.getElementById('hamburger-menu');
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        const sidebarClose = document.getElementById('sidebar-close');
        
        const closeSidebar = () => {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            hamburgerMenu.setAttribute('aria-expanded', 'false');
            sidebarOverlay.setAttribute('aria-hidden', 'true');
        };
        
        if (hamburgerMenu && sidebar) {
            hamburgerMenu.addEventListener('click', () => {
                sidebar.classList.add('active');
                sidebarOverlay.classList.add('active');
                hamburgerMenu.setAttribute('aria-expanded', 'true');
                sidebarOverlay.setAttribute('aria-hidden', 'false');
                const firstFocusable = sidebar.querySelector('button, a, [tabindex]:not([tabindex="-1"])');
                if (firstFocusable) firstFocusable.focus();
            });
        }
        
        if (sidebarClose) {
            sidebarClose.addEventListener('click', closeSidebar);
        }
        
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', closeSidebar);
        }
        
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                const section = item.dataset.section;
                this.handleSidebarNavigation(section);
            });
        });
        
        const sidebarProfile = document.getElementById('sidebar-profile');
        if (sidebarProfile) {
            sidebarProfile.addEventListener('click', () => {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                if (this.isOwner) {
                    this.showAdminScreen();
                } else {
                    this.showPage('profile');
                }
            });
        }
        
        const settingsBackBtn = document.getElementById('settings-back-btn');
        if (settingsBackBtn) {
            settingsBackBtn.addEventListener('click', () => this.goToHome());
        }
        
        const adminBackBtn = document.getElementById('admin-back-btn');
        if (adminBackBtn) {
            adminBackBtn.addEventListener('click', () => this.goToHome());
        }
        
        this.setupAdminEventListeners();
        
        const settingsAddDeviceBtn = document.getElementById('settings-add-device-btn');
        if (settingsAddDeviceBtn) {
            settingsAddDeviceBtn.addEventListener('click', () => this.showAddDeviceModal());
        }
        
        const settingsBackupWalletItem = document.getElementById('settings-backup-wallet-item');
        if (settingsBackupWalletItem) {
            settingsBackupWalletItem.addEventListener('click', () => this.showBackupWalletModal());
        }
        
        const settingsLogoutBtn = document.getElementById('settings-logout-btn');
        if (settingsLogoutBtn) {
            settingsLogoutBtn.addEventListener('click', () => this.logoutAllDevices());
        }
        
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchSection(tab.dataset.section);
            });
        });
        
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                const status = card.dataset.status;
                document.getElementById('status-filter').value = status;
                this.switchSection('trackings');
                this.filterTrackings(status);
            });
        });
        
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterTrackings(e.target.value);
            });
        }
        
        const createForm = document.getElementById('create-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createTracking();
            });
        }
        
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.searchTrackings(e.target.value);
                }, 300);
            });
        }
        
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const query = document.getElementById('search-input').value;
                this.searchTrackings(query);
            });
        }
        
        const btnBack = document.getElementById('btn-back');
        if (btnBack) {
            btnBack.addEventListener('click', () => {
                this.goBack();
            });
        }
        
        const modalOverlay = document.getElementById('modal-overlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeModal();
                }
            });
        }
        
        if (this.tg) {
            this.tg.onEvent('backButtonClicked', () => {
                const trackingModule = document.getElementById('tracking-module');
                const marketplaceScreen = document.getElementById('marketplace-screen');
                const botsScreen = document.getElementById('bots-screen');
                const walletScreen = document.getElementById('wallet-screen');
                const profileScreen = document.getElementById('profile-screen');
                const exchangeScreen = document.getElementById('exchange-screen');
                
                if (exchangeScreen && !exchangeScreen.classList.contains('hidden')) {
                    this.goToHome();
                } else if (marketplaceScreen && !marketplaceScreen.classList.contains('hidden')) {
                    this.goToHome();
                } else if (botsScreen && !botsScreen.classList.contains('hidden')) {
                    this.goToHome();
                } else if (walletScreen && !walletScreen.classList.contains('hidden')) {
                    this.goToHome();
                } else if (profileScreen && !profileScreen.classList.contains('hidden')) {
                    this.goToHome();
                } else if (trackingModule && !trackingModule.classList.contains('hidden')) {
                    if (this.currentSection === 'detail') {
                        this.goBack();
                    } else {
                        this.goToHome();
                    }
                }
            });
        }
        
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const navType = item.dataset.nav;
                this.handleBottomNav(navType);
            });
        });
        
        const profileModalOverlay = document.getElementById('profile-modal-overlay');
        const profileModalClose = document.getElementById('profile-modal-close');
        
        if (profileModalClose) {
            profileModalClose.addEventListener('click', () => {
                this.closeProfileModal();
            });
        }
        
        if (profileModalOverlay) {
            profileModalOverlay.addEventListener('click', (e) => {
                if (e.target === profileModalOverlay) {
                    this.closeProfileModal();
                }
            });
        }
        
        document.querySelectorAll('.profile-page-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                this.switchProfileTab(tabName);
            });
        });
        
        if (!this._editProfileListenerAdded) {
            this._editProfileListenerAdded = true;
            document.body.addEventListener('click', (e) => {
                const editBtn = e.target.closest('#edit-profile-btn');
                if (editBtn) {
                    this.devLog('Edit profile button clicked!');
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggleEditMode();
                }
            });
        }
        
        this.setupAvatarUpload();
        this.initExchange();
    },
    
    switchProfileTab(tabName) {
        document.querySelectorAll('.profile-page-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        const activeTab = document.querySelector(`.profile-page-tab[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
        
        document.querySelectorAll('.profile-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const activeContent = document.getElementById(`tab-${tabName}`);
        if (activeContent) {
            activeContent.classList.add('active');
        }
    },
    
    handleBottomNav(navType) {
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
            item.removeAttribute('aria-current');
        });
        
        const activeItem = document.querySelector(`.bottom-nav-item[data-nav="${navType}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
            activeItem.setAttribute('aria-current', 'page');
        }
        
        A11y.announce(this._getNavLabel(navType));
        
        switch(navType) {
            case 'home':
                this.goToHome();
                break;
            case 'marketplace':
                this.showPage('marketplace');
                break;
            case 'wallet':
                this.showPage('wallet');
                break;
            case 'notifications':
                this.showPage('notifications');
                this.loadNotifications();
                break;
            case 'profile':
                this.showPage('profile');
                this.updateProfilePage();
                break;
        }
    },
    
    _getNavLabel(navType) {
        const labels = {
            'home': 'Inicio',
            'marketplace': 'Tienda',
            'notifications': 'Notificaciones',
            'wallet': 'Billetera',
            'profile': 'Mi perfil'
        };
        return labels[navType] || navType;
    },
    
    handleSidebarNavigation(section) {
        switch (section) {
            case 'numeros':
                const initDataParam = this.initData ? `?initData=${encodeURIComponent(this.initData)}` : '';
                window.location.href = '/virtual-numbers' + initDataParam;
                break;
            case 'cuentas':
                this.showPage('marketplace');
                break;
            case 'metodos':
                this.showPage('wallet');
                break;
            case 'bots':
                this.showPage('bots');
                break;
            case 'planes':
                this.showPage('marketplace');
                break;
            case 'exchange':
                this.showPage('exchange');
                break;
            case 'foro':
                this.goToHome();
                break;
            case 'settings':
                this.showSettingsScreen();
                break;
            default:
                this.goToHome();
        }
    },
    
    hideAllScreens() {
        this.cleanupCurrentScreen();
        document.querySelectorAll('.page-screen, #home-screen, #tracking-module').forEach(screen => {
            screen.classList.add('hidden');
        });
    },
    
    cleanupCurrentScreen() {
        if (this.exchangeData && this.exchangeData.estimateTimeout) {
            clearTimeout(this.exchangeData.estimateTimeout);
            this.exchangeData.estimateTimeout = null;
        }
        
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }
        
        if (this._exploreSearchController) {
            this._exploreSearchController.abort();
            this._exploreSearchController = null;
        }
        
        if (typeof PublicationsManager !== 'undefined' && PublicationsManager._storyTimeout) {
            clearTimeout(PublicationsManager._storyTimeout);
            PublicationsManager._storyTimeout = null;
        }
    },
    
    showPage(pageName) {
        const currentScreen = document.querySelector('.page-screen:not(.hidden)');
        
        if (currentScreen && !currentScreen.id.includes(pageName)) {
            currentScreen.classList.add('page-exit');
            setTimeout(() => {
                this.hideAllScreens();
                this._showPageContent(pageName);
            }, 150);
        } else {
            this.hideAllScreens();
            this._showPageContent(pageName);
        }
    },
    
    _showPageContent(pageName) {
        const pageScreen = document.getElementById(`${pageName}-screen`);
        if (!pageScreen) {
            console.warn(`[Navigation] Page "${pageName}" not found, redirecting to home`);
            this.goToHome();
            return;
        }
        
        const isAlreadyVisible = !pageScreen.classList.contains('hidden');
        if (isAlreadyVisible) {
            this.updateBottomNavActive(pageName);
            return;
        }
        
        document.querySelectorAll('.page-screen').forEach(screen => {
            screen.classList.remove('page-enter', 'page-exit');
        });
        
        pageScreen.classList.remove('hidden');
        
        this.updateBottomNavActive(pageName);
        
        if (this.tg && this.tg.BackButton) {
            this.tg.BackButton.show();
        }
        
        this.currentSection = pageName;
        if (typeof StateManager !== 'undefined') {
            StateManager.setSection(pageName);
        }
        
        if (pageName === 'bots') {
            this.loadUserBots();
        }
        
        if (pageName === 'exchange') {
            this.loadExchangeCurrencies();
        }
        
        if (pageName === 'wallet') {
            this.showWalletSkeleton();
            this.loadTransactionHistory();
            this.loadWalletBalance();
            this.startB3CPricePolling();
            this.loadB3CBalance();
            this.loadPersonalWalletAssets();
            this.loadTotalBalance();
        }
        
        if (pageName === 'explore') {
            this.initExplore();
        }
        
        if (pageName === 'notifications') {
            this.showNotificationsSkeleton();
        }
        
        if (pageName === 'profile') {
            this.showProfileSkeleton();
        }
        
        
        this.updateFloatingButtonVisibility(pageName);
    },
    
    showScreen(screenId) {
        const screenName = screenId.replace('-screen', '');
        this.showPage(screenName);
    },
    
    updateFloatingButtonVisibility(pageName) {
        const floatingBtn = document.getElementById('floating-create-btn');
        if (!floatingBtn) return;
        
        if (pageName === 'home' || pageName === 'profile') {
            floatingBtn.classList.remove('hidden');
        } else {
            floatingBtn.classList.add('hidden');
        }
    },
    
    updateBottomNavActive(pageName) {
        const navMap = {
            'home': 'home',
            'explore': 'explore',
            'notifications': 'notifications',
            'profile': 'profile'
        };
        
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
            const navId = item.dataset.nav || item.id?.replace('nav-', '');
            if (navMap[pageName] === navId) {
                item.classList.add('active');
            }
        });
    },
    
    showSettingsScreen() {
        this.hideAllScreens();
        document.getElementById('settings-screen')?.classList.remove('hidden');
        
        if (this.tg && this.tg.BackButton) {
            this.tg.BackButton.show();
        }
        
        this.currentSection = 'settings';
        if (typeof StateManager !== 'undefined') {
            StateManager.setSection('settings');
        }
        
        this.loadSettingsSecurityStatus();
        this.loadSettingsDevices();
    },
    
    async initExplore() {
        this.loadExploreTrending();
        
        const searchInput = document.getElementById('explore-search-input');
        if (searchInput && !searchInput._hasListener) {
            searchInput._hasListener = true;
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.performExploreSearch(e.target.value);
                }, 300);
            });
        }
    },
    
    escapeHtmlForExplore(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    sanitizeHashtag(tag) {
        return String(tag).replace(/[^a-zA-Z0-9_]/g, '');
    },
    
    sanitizeUrl(url) {
        if (!url) return '';
        try {
            const parsed = new URL(url, window.location.origin);
            if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                return url;
            }
        } catch {
            if (url.startsWith('/')) return url;
        }
        return '';
    },
    
    async loadExploreTrending() {
        try {
            const response = await this.apiRequest('/api/trending/hashtags?limit=15');
            const container = document.getElementById('explore-trending-list');
            
            if (response.success && response.hashtags && container) {
                SafeDOM.setHTML(container, response.hashtags.map(tag => {
                    const safeTag = this.sanitizeHashtag(tag.tag);
                    const count = parseInt(tag.count) || 0;
                    return `
                    <div class="explore-trending-item" onclick="App.searchHashtag('${safeTag}')">
                        <span class="explore-trending-tag">#${this.escapeHtmlForExplore(safeTag)}</span>
                        <span class="explore-trending-count">${count} posts</span>
                    </div>
                `;}).join(''));
            }
        } catch (error) {
            console.error('Error loading trending:', error);
        }
    },
    
    async performExploreSearch(query) {
        if (!query || query.length < 2) {
            document.getElementById('explore-trending')?.classList.remove('hidden');
            document.getElementById('explore-hashtag-header')?.classList.add('hidden');
            document.getElementById('explore-results').innerHTML = '';
            return;
        }
        
        let hashtag = query.startsWith('#') ? query.substring(1) : query;
        hashtag = this.sanitizeHashtag(hashtag);
        if (hashtag) this.searchHashtag(hashtag);
    },
    
    async searchHashtag(hashtag) {
        const safeHashtag = this.sanitizeHashtag(hashtag);
        if (!safeHashtag) return;
        
        if (this._exploreSearchController) {
            this._exploreSearchController.abort();
        }
        this._exploreSearchController = new AbortController();
        
        const resultsContainer = document.getElementById('explore-results');
        const trendingSection = document.getElementById('explore-trending');
        const hashtagHeader = document.getElementById('explore-hashtag-header');
        
        trendingSection?.classList.add('hidden');
        hashtagHeader?.classList.remove('hidden');
        
        document.getElementById('explore-hashtag-tag').textContent = `#${safeHashtag}`;
        SafeDOM.setHTML(resultsContainer, '<div class="explore-loading"><div class="spinner"></div></div>');
        
        const searchInput = document.getElementById('explore-search-input');
        if (searchInput) searchInput.value = `#${safeHashtag}`;
        
        try {
            const response = await this.apiRequest(
                `/api/hashtag/${encodeURIComponent(safeHashtag)}?limit=30`,
                { signal: this._exploreSearchController.signal }
            );
            
            if (response.success) {
                document.getElementById('explore-hashtag-count').textContent = 
                    `${parseInt(response.total) || response.posts?.length || 0} publicaciones`;
                
                if (response.posts && response.posts.length > 0) {
                    SafeDOM.setHTML(resultsContainer, response.posts.map(post => this.renderExplorePostThumb(post)).join(''));
                } else {
                    const emptyDiv = document.createElement('div');
                    emptyDiv.className = 'explore-empty';
                    const p = document.createElement('p');
                    p.textContent = `No se encontraron publicaciones con #${safeHashtag}`;
                    emptyDiv.appendChild(p);
                    resultsContainer.textContent = '';
                    resultsContainer.appendChild(emptyDiv);
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') return;
            console.error('Error searching hashtag:', error);
            SafeDOM.setHTML(resultsContainer, '<div class="explore-empty">Error al buscar</div>');
        }
    },
    
    renderExplorePostThumb(post) {
        const postId = parseInt(post.id) || 0;
        let thumbContent = '';
        
        if (post.content_type === 'image' && post.content_url) {
            const safeUrl = this.sanitizeUrl(post.content_url);
            thumbContent = safeUrl ? `<img src="${this.escapeHtmlForExplore(safeUrl)}" alt="" loading="lazy">` : '';
        } else if (post.content_type === 'video' && post.content_url) {
            const safeUrl = this.sanitizeUrl(post.content_url.replace(/\.[^/.]+$/, '.jpg'));
            thumbContent = safeUrl ? `<img src="${this.escapeHtmlForExplore(safeUrl)}" alt="" loading="lazy">
                           <div class="video-indicator">▶</div>` : '';
        } else {
            const text = String(post.caption || post.text || '').substring(0, 60);
            thumbContent = `<div class="text-thumb">${this.escapeHtmlForExplore(text)}${(post.caption || post.text || '').length > 60 ? '...' : ''}</div>`;
        }
        
        return `
            <div class="explore-post-thumb" onclick="PublicationsManager.showPostDetail(${postId})">
                ${thumbContent}
            </div>
        `;
    },
    
    showAdminScreen() {
        if (!this.isOwner) {
            this.showToast('Acceso denegado', 'error');
            return;
        }
        
        window.location.href = '/admin';
    },
    
    async loadSettingsSecurityStatus() {
        try {
            const response = await this.apiRequest('/api/security/status');
            if (response.success) {
                const scoreEl = document.getElementById('settings-security-score');
                const levelEl = document.getElementById('settings-security-level');
                const walletDot = document.getElementById('settings-wallet-dot');
                const twofaDot = document.getElementById('settings-2fa-dot');
                const devicesDot = document.getElementById('settings-devices-dot');
                const twoFaStatus = document.getElementById('settings-2fa-status');
                const backupStatus = document.getElementById('settings-backup-status');
                const devicesCount = document.getElementById('settings-devices-count');
                
                if (scoreEl) {
                    const score = response.security_score || 0;
                    scoreEl.innerHTML = `<span>${score}%</span>`;
                    scoreEl.style.background = `conic-gradient(var(--accent-success) ${score}%, var(--bg-input) ${score}%)`;
                }
                
                if (levelEl) {
                    levelEl.textContent = `Nivel: ${response.security_level || 'bajo'}`;
                }
                
                if (walletDot) {
                    walletDot.className = 'status-dot ' + (response.wallet_connected ? 'active' : 'inactive');
                }
                
                if (twofaDot) {
                    twofaDot.className = 'status-dot ' + (response.two_factor_enabled ? 'active' : 'inactive');
                }
                
                if (devicesDot) {
                    const hasDevices = (response.trusted_devices_count || 0) > 0;
                    devicesDot.className = 'status-dot ' + (hasDevices ? 'active' : 'warning');
                }
                
                if (twoFaStatus) {
                    twoFaStatus.textContent = response.two_factor_enabled ? 'Activado' : 'Desactivado';
                }
                
                if (backupStatus) {
                    backupStatus.textContent = response.has_backup_wallet ? 'Configurada' : 'No configurada';
                }
                
                if (devicesCount) {
                    devicesCount.textContent = `${response.trusted_devices_count || 0}/${response.max_devices || 2} dispositivos`;
                }
            }
        } catch (error) {
            console.error('Error loading security status:', error);
        }
    },
    
    async loadSettingsDevices() {
        try {
            const response = await this.apiRequest('/api/security/devices');
            const listEl = document.getElementById('settings-devices-list');
            
            if (!listEl) return;
            
            if (response.success && response.devices && response.devices.length > 0) {
                SafeDOM.setTrustedHTML(listEl, response.devices.map(device => {
                    const safeDeviceId = this.sanitizeForJs(device.device_id);
                    return `
                    <div class="settings-device-item">
                        <span class="device-icon">${this.getDeviceIcon(device.device_type)}</span>
                        <div class="device-info">
                            <span class="device-name">${this.escapeHtml(device.device_name || 'Dispositivo')}</span>
                            <span class="device-details">${this.escapeHtml(device.device_type || 'Desconocido')}</span>
                        </div>
                        ${device.is_current ? '<span class="device-current">Actual</span>' : `
                            <button class="device-remove-btn" onclick="App.removeDevice('${safeDeviceId}')">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        `}
                    </div>
                `;}).join(''));
            } else {
                SafeDOM.setHTML(listEl, '<div class="devices-empty">No hay dispositivos de confianza</div>');
            }
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    },
    
    getDeviceIcon(deviceType) {
        return this.getDeviceIconEmoji(deviceType);
    },
    
    async loadAdminStats() {
        try {
            const response = await this.apiRequest('/api/admin/stats');
            if (response.success) {
                document.getElementById('admin-total-users').textContent = response.total_users || 0;
                document.getElementById('admin-total-bots').textContent = response.active_bots || 0;
                document.getElementById('admin-total-transactions').textContent = response.total_transactions || 0;
                document.getElementById('admin-security-alerts').textContent = response.security_alerts || 0;
                
                const alertBadge = document.getElementById('admin-alert-badge');
                if (alertBadge && response.security_alerts > 0) {
                    alertBadge.textContent = response.security_alerts;
                    alertBadge.classList.remove('hidden');
                }
            }
        } catch (error) {
            console.error('Error loading admin stats:', error);
        }
    },
    
    updateSidebarRole() {
        const roleEl = document.getElementById('sidebar-role');
        const arrowEl = document.getElementById('sidebar-admin-arrow');
        
        if (roleEl) {
            roleEl.textContent = this.isOwner ? 'Owner' : 'Usuario';
        }
        
        if (arrowEl) {
            if (this.isOwner) {
                arrowEl.classList.remove('hidden');
            } else {
                arrowEl.classList.add('hidden');
            }
        }
    },
    
    updateProfilePage() {
        const username = document.getElementById('profile-page-username');
        const atUsername = document.getElementById('profile-at-username');
        const displayName = document.getElementById('profile-display-name');
        const bioText = document.getElementById('profile-bio-text');
        const verifiedBadge = document.getElementById('profile-verified-badge');
        const userBadge = document.getElementById('profile-user-badge');
        const walletBalance = document.getElementById('profile-wallet-balance');
        
        const userUsername = this.user?.username || 'demo_user';
        const userName = this.user?.firstName || this.user?.first_name || 'Usuario';
        const userBio = this.user?.bio || 'Sin biografia';
        
        if (username) {
            username.textContent = `@${userUsername}`;
        }
        if (atUsername) {
            atUsername.textContent = `@${userUsername}`;
        }
        if (displayName) {
            displayName.textContent = userName;
        }
        if (bioText) {
            bioText.textContent = userBio;
        }
        
        if (verifiedBadge) {
            if (this.user?.isVerified || this.user?.is_verified) {
                verifiedBadge.classList.remove('hidden');
            } else {
                verifiedBadge.classList.add('hidden');
            }
        }
        
        if (userBadge) {
            if (this.isOwner) {
                userBadge.textContent = 'Owner';
                userBadge.style.background = 'rgba(246, 70, 93, 0.15)';
                userBadge.style.color = '#F6465D';
            } else if (this.user?.isPremium || this.user?.is_premium) {
                userBadge.textContent = 'Premium';
                userBadge.style.background = 'rgba(179, 136, 255, 0.15)';
                userBadge.style.color = '#B388FF';
            } else {
                userBadge.textContent = 'Miembro';
                userBadge.style.background = 'rgba(240, 185, 11, 0.15)';
                userBadge.style.color = '#F0B90B';
            }
        }
        
        if (walletBalance && this.walletBalance !== undefined) {
            walletBalance.textContent = parseFloat(this.walletBalance || 0).toFixed(2);
        }
        
        this.updateAllAvatars();
        this.loadProfileGallery();
        this.loadProfileStats();
        this.setupNewProfileListeners();
    },
    
    setupNewProfileListeners() {
        if (this._newProfileListenersSetup) return;
        this._newProfileListenersSetup = true;
        
        const backBtn = document.getElementById('profile-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.goToHome());
        }
        
        const walletCard = document.getElementById('profile-wallet-card');
        if (walletCard) {
            walletCard.addEventListener('click', () => this.showPage('wallet'));
        }
        
        const settingsBtn = document.getElementById('profile-settings-btn-inline');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettingsScreen());
        }
        
        const statsElements = document.querySelectorAll('.profile-page-stat[data-action]');
        statsElements.forEach(stat => {
            stat.addEventListener('click', () => {
                const action = stat.dataset.action;
                if (action === 'followers') {
                    this.showFollowersModal();
                } else if (action === 'following') {
                    this.showFollowingModal();
                }
            });
        });
    },
    
    async loadProfileGallery() {
        const gallery = document.getElementById('profile-gallery');
        const emptyGallery = document.getElementById('empty-gallery');
        
        if (!gallery) return;
        
        try {
            const userId = this.user?.id || '0';
            const response = await this.apiRequest(`/api/users/${userId}/posts`);
            
            if (response.success && response.posts && response.posts.length > 0) {
                gallery.innerHTML = '';
                emptyGallery?.classList.add('hidden');
                
                response.posts.forEach(post => {
                    const item = document.createElement('div');
                    item.className = 'gallery-item' + (this.editModeActive ? ' edit-mode' : '');
                    item.dataset.postId = post.id;
                    
                    let thumbnail = '';
                    if (post.media && post.media.length > 0) {
                        const media = post.media[0];
                        if (media.thumbnail_url) {
                            thumbnail = `<img src="${media.thumbnail_url}" alt="" class="gallery-thumb">`;
                        } else if (media.media_url) {
                            thumbnail = `<img src="${media.media_url}" alt="" class="gallery-thumb">`;
                        }
                        if (post.media.length > 1) {
                            thumbnail += '<span class="gallery-multi-icon">📷</span>';
                        }
                        if (media.media_type === 'video') {
                            thumbnail += '<span class="gallery-video-icon">▶</span>';
                        }
                    } else if (post.contentType === 'text') {
                        const captionPreview = post.caption?.substring(0, 50) || '';
                        thumbnail = `<div class="gallery-text-preview">${captionPreview}</div>`;
                    }
                    
                    if (this.editModeActive) {
                        thumbnail += `<button class="gallery-delete-btn" onclick="event.stopPropagation(); App.deleteGalleryPost(${post.id})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>`;
                    }
                    
                    item.innerHTML = thumbnail;
                    if (!this.editModeActive) {
                        item.addEventListener('click', () => this.openPostDetail(post.id));
                    }
                    gallery.appendChild(item);
                });
            } else {
                gallery.innerHTML = '';
                emptyGallery?.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading profile gallery:', error);
            gallery.innerHTML = '';
            emptyGallery?.classList.remove('hidden');
        }
    },
    
    toggleEditMode() {
        this.devLog('toggleEditMode called, current state:', this.editModeActive);
        this.editModeActive = !this.editModeActive;
        this.devLog('new edit mode state:', this.editModeActive);
        
        const editBtn = document.getElementById('edit-profile-btn');
        
        if (editBtn) {
            if (this.editModeActive) {
                editBtn.textContent = 'Listo';
                editBtn.classList.add('editing');
            } else {
                editBtn.textContent = 'Editar perfil';
                editBtn.classList.remove('editing');
            }
        }
        
        this.loadProfileGallery();
    },
    
    async deleteGalleryPost(postId) {
        if (!confirm('¿Estás seguro de que quieres eliminar esta publicación?')) {
            return;
        }
        
        try {
            const response = await this.apiRequest(`/api/publications/${postId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Publicación eliminada', 'success');
                this.loadProfileGallery();
                
                const postsCountEl = document.getElementById('profile-page-posts');
                if (postsCountEl) {
                    const currentCount = parseInt(postsCountEl.textContent) || 0;
                    postsCountEl.textContent = Math.max(0, currentCount - 1);
                }
            } else {
                this.showToast(response.error || 'Error al eliminar', 'error');
            }
        } catch (error) {
            console.error('Error deleting post:', error);
            this.showToast('Error al eliminar la publicación', 'error');
        }
    },
    
    async openPostDetail(postId) {
        if (window.BUNK3R_Publications && window.BUNK3R_Publications.loadSinglePost) {
            await window.BUNK3R_Publications.loadSinglePost(postId);
            this.showPage('home');
        }
    },
    
    setupAvatarUpload() {
        const avatarWrap = document.getElementById('avatar-upload-wrap');
        const avatarInput = document.getElementById('avatar-input');
        
        if (avatarInput) {
            avatarInput.addEventListener('change', (e) => this.handleAvatarSelect(e));
        }
        
        if (avatarWrap) {
            avatarWrap.addEventListener('click', () => {
                if (avatarInput) avatarInput.click();
            });
        }
        
        const editAvatarInput = document.getElementById('edit-avatar-input');
        if (editAvatarInput) {
            editAvatarInput.addEventListener('change', (e) => this.handleAvatarSelect(e));
        }
        
        const editAvatarWrap = document.getElementById('edit-avatar-wrap');
        if (editAvatarWrap) {
            editAvatarWrap.addEventListener('click', () => {
                if (editAvatarInput) editAvatarInput.click();
            });
        }
    },
    
    setupProfileEventListeners() {
        const editProfileBtn = document.getElementById('edit-profile-btn');
        if (editProfileBtn) {
            editProfileBtn.addEventListener('click', () => this.showEditProfileModal());
        }
        
        const followersStatEl = document.querySelector('.profile-page-stat:nth-child(2)');
        const followingStatEl = document.querySelector('.profile-page-stat:nth-child(3)');
        
        if (followersStatEl) {
            followersStatEl.addEventListener('click', () => this.showFollowersModal('followers'));
        }
        if (followingStatEl) {
            followingStatEl.addEventListener('click', () => this.showFollowersModal('following'));
        }
        
        const bioInput = document.getElementById('edit-profile-bio');
        if (bioInput) {
            bioInput.addEventListener('input', () => {
                const count = bioInput.value.length;
                const countEl = document.getElementById('bio-char-count');
                if (countEl) countEl.textContent = count;
            });
        }
    },
    
    async showFollowersModal(type = 'followers') {
        const modal = document.getElementById('followers-modal');
        if (!modal) return;
        
        modal.classList.remove('hidden');
        this.switchFollowersTab(type);
    },
    
    hideFollowersModal() {
        const modal = document.getElementById('followers-modal');
        if (modal) modal.classList.add('hidden');
    },
    
    async switchFollowersTab(type) {
        document.querySelectorAll('.followers-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.type === type);
        });
        
        const title = document.getElementById('followers-modal-title');
        if (title) {
            title.textContent = type === 'followers' ? 'Seguidores' : 'Siguiendo';
        }
        
        const list = document.getElementById('followers-list');
        if (list) {
            list.innerHTML = '<div class="followers-loading"><div class="spinner"></div></div>';
        }
        
        this._currentFollowersTab = type;
        
        try {
            const userId = this.user?.id || '0';
            const endpoint = type === 'followers' 
                ? `/api/users/${userId}/followers` 
                : `/api/users/${userId}/following`;
            
            const response = await this.apiRequest(endpoint);
            
            if (response.success) {
                const users = response[type] || [];
                if (users.length === 0) {
                    SafeDOM.setHTML(list, `<div class="followers-empty">
                        ${type === 'followers' ? 'Aun no tienes seguidores' : 'No sigues a nadie'}
                    </div>`);
                } else {
                    SafeDOM.setTrustedHTML(list, users.map(user => {
                        const isVerified = user.isVerified || user.is_verified;
                        const verifiedBadge = isVerified ? '<span class="verified-badge" title="Cuenta verificada">✓</span>' : '';
                        const userName = this.escapeHtml(user.firstName || user.first_name || user.username || 'Usuario');
                        
                        let actionButton = '';
                        if (type === 'following') {
                            actionButton = `
                                <button class="follower-btn following" onclick="event.stopPropagation(); App.toggleFollowFromList('${this.sanitizeForJs(user.id)}', true)">
                                    Siguiendo
                                </button>
                            `;
                        } else {
                            actionButton = `
                                <button class="follower-btn follow" onclick="event.stopPropagation(); App.toggleFollowFromList('${this.sanitizeForJs(user.id)}', false)">
                                    Seguir
                                </button>
                            `;
                        }
                        
                        return `
                            <div class="follower-item" onclick="App.viewUserProfile('${this.sanitizeForJs(user.id)}')">
                                <img src="${this.escapeAttribute(user.avatarUrl || user.avatar_url || '/static/images/default-avatar.png')}" 
                                     class="follower-avatar" 
                                     onerror="this.src='/static/images/default-avatar.png'">
                                <div class="follower-info">
                                    <span class="follower-name">${userName}${verifiedBadge}</span>
                                    <span class="follower-username">@${this.escapeHtml(user.username || 'usuario')}</span>
                                </div>
                                ${actionButton}
                            </div>
                        `;
                    }).join(''));
                }
            }
        } catch (error) {
            console.error('Error loading followers:', error);
            if (list) {
                SafeDOM.setHTML(list, '<div class="followers-empty">Error al cargar</div>');
            }
        }
    },
    
    async toggleFollowFromList(userId, isCurrentlyFollowing) {
        try {
            const response = await this.apiRequest(`/api/users/${userId}/follow`, {
                method: 'POST'
            });
            
            if (response.success) {
                const action = isCurrentlyFollowing ? 'dejado de seguir' : 'siguiendo';
                this.showToast(`Usuario ${action}`, 'success');
                this.switchFollowersTab(this._currentFollowersTab || 'followers');
                this.loadProfileStats();
            }
        } catch (error) {
            console.error('Toggle follow error:', error);
            this.showToast('Error al procesar la solicitud', 'error');
        }
    },
    
    async unfollowUser(userId) {
        try {
            const response = await this.apiRequest(`/api/users/${userId}/follow`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Usuario dejado de seguir', 'success');
                this.switchFollowersTab('following');
                this.loadProfileStats();
            }
        } catch (error) {
            console.error('Unfollow error:', error);
        }
    },
    
    async viewUserProfile(userId) {
        this.hideFollowersModal();
        
        if (!userId) {
            this.showToast('Usuario no encontrado', 'error');
            return;
        }
        
        const ownUserId = this.user?.id?.toString();
        if (userId.toString() === ownUserId) {
            this.showPage('profile');
            return;
        }
        
        try {
            const response = await this.apiRequest(`/api/users/${userId}/profile`);
            if (response.success && response.profile) {
                this.showUserProfileModal(response.profile);
            } else {
                this.showToast(response.error || 'Error al cargar perfil', 'error');
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.showToast('Error al cargar el perfil', 'error');
        }
    },
    
    showUserProfileModal(profile) {
        let modal = document.getElementById('user-profile-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'user-profile-modal';
            modal.className = 'modal-overlay';
            document.body.appendChild(modal);
        }
        
        const isFollowing = profile.is_following || false;
        const followBtnText = isFollowing ? 'Siguiendo' : 'Seguir';
        const followBtnClass = isFollowing ? 'following' : '';
        
        modal.innerHTML = `
            <div class="modal-content user-profile-modal-content">
                <div class="modal-header">
                    <h3>Perfil</h3>
                    <button class="modal-close" onclick="App.closeUserProfileModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="user-profile-content">
                    <div class="user-profile-header">
                        <img src="${this.escapeAttribute(profile.avatar_url || '/static/images/default-avatar.png')}" 
                             class="user-profile-avatar" 
                             onerror="this.src='/static/images/default-avatar.png'">
                        <div class="user-profile-info">
                            <h4 class="user-profile-name">${this.escapeHtml(profile.display_name || profile.first_name || 'Usuario')}</h4>
                            <span class="user-profile-username">@${this.escapeHtml(profile.username || 'usuario')}</span>
                        </div>
                    </div>
                    ${profile.bio ? `<p class="user-profile-bio">${this.escapeHtml(profile.bio)}</p>` : ''}
                    <div class="user-profile-stats">
                        <div class="user-profile-stat">
                            <span class="stat-value">${parseInt(profile.posts_count, 10) || 0}</span>
                            <span class="stat-label">Publicaciones</span>
                        </div>
                        <div class="user-profile-stat">
                            <span class="stat-value">${parseInt(profile.followers_count, 10) || 0}</span>
                            <span class="stat-label">Seguidores</span>
                        </div>
                        <div class="user-profile-stat">
                            <span class="stat-value">${parseInt(profile.following_count, 10) || 0}</span>
                            <span class="stat-label">Siguiendo</span>
                        </div>
                    </div>
                    <button class="user-profile-follow-btn ${followBtnClass}" 
                            onclick="App.toggleFollowFromProfile('${this.escapeForOnclick(profile.user_id || profile.id)}', ${isFollowing})">
                        ${followBtnText}
                    </button>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeUserProfileModal();
        });
    },
    
    closeUserProfileModal() {
        const modal = document.getElementById('user-profile-modal');
        if (modal) modal.classList.add('hidden');
    },
    
    async toggleFollowFromProfile(userId, isCurrentlyFollowing) {
        try {
            const response = await this.apiRequest(`/api/users/${userId}/follow`, {
                method: 'POST'
            });
            
            if (response.success) {
                const newFollowing = !isCurrentlyFollowing;
                const btn = document.querySelector('.user-profile-follow-btn');
                if (btn) {
                    btn.textContent = newFollowing ? 'Siguiendo' : 'Seguir';
                    btn.className = `user-profile-follow-btn ${newFollowing ? 'following' : ''}`;
                    btn.setAttribute('onclick', `App.toggleFollowFromProfile('${this.escapeForOnclick(userId)}', ${newFollowing})`);
                }
                this.showToast(newFollowing ? 'Ahora sigues a este usuario' : 'Dejaste de seguir', 'success');
                this.loadProfileStats();
            }
        } catch (error) {
            console.error('Toggle follow error:', error);
            this.showToast('Error al procesar la solicitud', 'error');
        }
    },
    
    async showEditProfileModal() {
        const modal = document.getElementById('edit-profile-modal');
        if (!modal) return;
        
        const avatarImg = document.getElementById('edit-profile-avatar-img');
        const avatarInitial = document.getElementById('edit-profile-avatar-initial');
        
        if (this.userPhotoUrl && avatarImg) {
            avatarImg.src = this.userPhotoUrl;
            avatarImg.classList.remove('hidden');
            avatarInitial?.classList.add('hidden');
        } else if (avatarInitial) {
            avatarInitial.textContent = this.userInitials;
            avatarInitial.classList.remove('hidden');
            avatarImg?.classList.add('hidden');
        }
        
        try {
            const userId = this.user?.id || '0';
            const response = await this.apiRequest(`/api/users/${userId}/profile`);
            if (response.success && response.profile) {
                const bioInput = document.getElementById('edit-profile-bio');
                if (bioInput) {
                    bioInput.value = response.profile.bio || '';
                    const countEl = document.getElementById('bio-char-count');
                    if (countEl) countEl.textContent = bioInput.value.length;
                }
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
        
        modal.classList.remove('hidden');
    },
    
    hideEditProfileModal() {
        const modal = document.getElementById('edit-profile-modal');
        if (modal) modal.classList.add('hidden');
    },
    
    _pendingAvatarFile: null,
    _avatarCropper: null,
    _pendingCropFile: null,
    
    handleAvatarSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!file.type.startsWith('image/')) {
            this.showToast('Solo se permiten imagenes', 'error');
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) {
            this.showToast('Imagen muy grande (max 5MB)', 'error');
            return;
        }
        
        this._pendingCropFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.showAvatarCropModal(e.target.result);
        };
        reader.readAsDataURL(file);
    },
    
    showAvatarCropModal(imageSrc) {
        const modal = document.getElementById('avatar-crop-modal');
        const cropImage = document.getElementById('avatar-crop-image');
        
        if (!modal || !cropImage) return;
        
        if (this._avatarCropper) {
            this._avatarCropper.destroy();
            this._avatarCropper = null;
        }
        
        cropImage.src = imageSrc;
        modal.classList.remove('hidden');
        
        setTimeout(() => {
            if (typeof Cropper !== 'undefined') {
                this._avatarCropper = new Cropper(cropImage, {
                    aspectRatio: 1,
                    viewMode: 1,
                    dragMode: 'move',
                    guides: false,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    minCropBoxWidth: 100,
                    minCropBoxHeight: 100,
                    background: false,
                    responsive: true,
                    autoCropArea: 0.9
                });
            } else {
                console.error('Cropper.js not loaded');
                this.showToast('Error al cargar editor', 'error');
            }
        }, 100);
    },
    
    cancelAvatarCrop() {
        const modal = document.getElementById('avatar-crop-modal');
        if (modal) modal.classList.add('hidden');
        
        if (this._avatarCropper) {
            this._avatarCropper.destroy();
            this._avatarCropper = null;
        }
        
        this._pendingCropFile = null;
        const input = document.getElementById('avatar-input');
        if (input) input.value = '';
    },
    
    confirmAvatarCrop() {
        if (!this._avatarCropper) {
            this.showToast('Error al procesar imagen', 'error');
            return;
        }
        
        const canvas = this._avatarCropper.getCroppedCanvas({
            width: 400,
            height: 400,
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high'
        });
        
        if (!canvas) {
            this.showToast('Error al recortar imagen', 'error');
            return;
        }
        
        canvas.toBlob((blob) => {
            if (!blob) {
                this.showToast('Error al procesar imagen', 'error');
                return;
            }
            
            const fileName = this._pendingCropFile?.name || 'avatar.jpg';
            const croppedFile = new File([blob], fileName, { type: 'image/jpeg' });
            this._pendingAvatarFile = croppedFile;
            
            const avatarImg = document.getElementById('edit-profile-avatar-img');
            const avatarInitial = document.getElementById('edit-profile-avatar-initial');
            
            if (avatarImg) {
                avatarImg.src = canvas.toDataURL('image/jpeg');
                avatarImg.classList.remove('hidden');
            }
            if (avatarInitial) {
                avatarInitial.classList.add('hidden');
            }
            
            this.cancelAvatarCrop();
            this.showToast('Foto ajustada', 'success');
        }, 'image/jpeg', 0.9);
    },
    
    rotateAvatarCrop(degrees) {
        if (this._avatarCropper) {
            this._avatarCropper.rotate(degrees);
        }
    },
    
    zoomAvatarCrop(ratio) {
        if (this._avatarCropper) {
            this._avatarCropper.zoom(ratio);
        }
    },
    
    async saveProfile() {
        const bioInput = document.getElementById('edit-profile-bio');
        const bio = bioInput?.value.trim() || '';
        
        try {
            if (this._pendingAvatarFile) {
                const formData = new FormData();
                formData.append('avatar', this._pendingAvatarFile);
                
                const avatarResponse = await fetch('/api/users/avatar', {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                    body: formData
                });
                
                const avatarResult = await avatarResponse.json();
                if (avatarResult.success && avatarResult.avatar_url) {
                    this.userPhotoUrl = avatarResult.avatar_url;
                    this.updateAllAvatars();
                }
                
                this._pendingAvatarFile = null;
            }
            
            const userId = this.user?.id || '0';
            const response = await this.apiRequest(`/api/users/${userId}/profile`, {
                method: 'PUT',
                body: JSON.stringify({ bio })
            });
            
            if (response.success) {
                this.showToast('Perfil actualizado', 'success');
                this.hideEditProfileModal();
            } else {
                this.showToast(response.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Save profile error:', error);
            this.showToast('Error al guardar perfil', 'error');
        }
    },
    
    async loadProfileStats() {
        try {
            const userId = this.user?.id || '0';
            const response = await this.apiRequest(`/api/users/${userId}/stats`);
            
            if (response.success) {
                const postsEl = document.getElementById('profile-page-posts');
                const followersEl = document.getElementById('profile-page-followers');
                const followingEl = document.getElementById('profile-page-following');
                
                if (postsEl) postsEl.textContent = response.stats.posts || 0;
                if (followersEl) followersEl.textContent = response.stats.followers || 0;
                if (followingEl) followingEl.textContent = response.stats.following || 0;
            }
        } catch (error) {
            console.error('Error loading profile stats:', error);
        }
    },
    
    updateAllAvatars() {
        const sidebarAvatar = document.getElementById('sidebar-avatar');
        const bottomNavAvatar = document.getElementById('bottom-nav-avatar');
        const headerAvatar = document.getElementById('header-avatar');
        const headerAvatarInitial = document.getElementById('header-avatar-initial');
        const profileAvatar = document.getElementById('profile-avatar');
        const profileAvatarImg = document.getElementById('profile-avatar-img');
        const profileAvatarInitial = document.getElementById('profile-avatar-initial');
        
        const avatarElements = [sidebarAvatar, bottomNavAvatar];
        
        if (this.userPhotoUrl) {
            avatarElements.forEach(el => {
                if (el) {
                    el.style.backgroundImage = `url(${this.userPhotoUrl})`;
                    el.style.backgroundSize = 'cover';
                    el.style.backgroundPosition = 'center';
                    el.textContent = '';
                }
            });
            
            if (headerAvatar) {
                const existingImg = headerAvatar.querySelector('img');
                if (existingImg) {
                    existingImg.src = this.userPhotoUrl;
                } else {
                    const img = document.createElement('img');
                    img.src = this.userPhotoUrl;
                    img.alt = 'Avatar';
                    headerAvatar.appendChild(img);
                }
                if (headerAvatarInitial) headerAvatarInitial.classList.add('hidden');
            }
            
            if (profileAvatarImg) {
                profileAvatarImg.src = this.userPhotoUrl;
                profileAvatarImg.classList.remove('hidden');
            }
            if (profileAvatarInitial) {
                profileAvatarInitial.classList.add('hidden');
            }
        } else {
            avatarElements.forEach(el => {
                if (el) {
                    el.style.backgroundImage = 'none';
                    el.textContent = this.userInitials;
                }
            });
            
            if (headerAvatar) {
                const existingImg = headerAvatar.querySelector('img');
                if (existingImg) existingImg.remove();
                if (headerAvatarInitial) {
                    headerAvatarInitial.textContent = this.userInitials;
                    headerAvatarInitial.classList.remove('hidden');
                }
            }
            
            if (profileAvatarImg) {
                profileAvatarImg.classList.add('hidden');
            }
            if (profileAvatarInitial) {
                profileAvatarInitial.textContent = this.userInitials;
                profileAvatarInitial.classList.remove('hidden');
            }
        }
    },
    
    async loadInitialData(force = false) {
        if (this._initialDataLoaded && !force) {
            return;
        }
        
        try {
            const [statsResponse, reasonsResponse, statusesResponse] = await Promise.all([
                this.apiRequest('/api/stats'),
                this.apiRequest('/api/delay-reasons'),
                this.apiRequest('/api/statuses')
            ]);
            
            if (statsResponse.success) {
                this.updateStats(statsResponse.stats);
            }
            
            if (reasonsResponse.success) {
                this.delayReasons = reasonsResponse.reasons;
            }
            
            if (statusesResponse.success) {
                this.statuses = statusesResponse.statuses;
            }
            
            this._initialDataLoaded = true;
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error al cargar datos', 'error');
        }
    },
    
    updateStats(stats) {
        document.getElementById('stat-retenido').textContent = stats.retenido || 0;
        document.getElementById('stat-transito').textContent = stats.enTransito || 0;
        document.getElementById('stat-entregado').textContent = stats.entregado || 0;
        document.getElementById('stat-pago').textContent = stats.confirmarPago || 0;
        document.getElementById('stat-total').textContent = stats.total || 0;
    },
    
    switchSection(sectionId) {
        if (sectionId === 'wallet' && !this.deviceTrusted && !this.isDeviceTrusted) {
            this.devLog('Acceso a wallet bloqueado - dispositivo no confiable');
            this.showDeviceBlockedScreen();
            return;
        }
        
        if (sectionId !== 'detail') {
            this.previousSection = this.currentSection;
        }
        
        document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        
        const section = document.getElementById(`section-${sectionId}`);
        if (section) {
            section.classList.remove('hidden');
            section.classList.add('active');
        }
        
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.section === sectionId);
        });
        
        this.currentSection = sectionId;
        
        if (sectionId === 'detail') {
            this.tg?.BackButton?.show();
        } else {
            this.tg?.BackButton?.hide();
        }
        
        if (sectionId === 'trackings') {
            this.loadTrackings();
        }
        
        if (sectionId === 'dashboard') {
            this.loadInitialData();
        }
        
        if (sectionId === 'profile' && !this._securityDataLoaded) {
            Promise.all([
                this.loadSecurityStatus(),
                this.loadTrustedDevices(),
                this.loadSecurityActivity()
            ]).then(() => {
                this._securityDataLoaded = true;
            });
        }
    },
    
    goBack() {
        const backTo = this.previousSection || 'trackings';
        this.switchSection(backTo);
    },
    
    async loadTrackings(status = '') {
        try {
            const url = status ? `/api/trackings?status=${status}` : '/api/trackings';
            const response = await this.apiRequest(url);
            
            if (response.success) {
                this.trackings = response.trackings;
                this.renderTrackingsList(response.trackings);
            }
        } catch (error) {
            console.error('Error loading trackings:', error);
            this.showToast('Error al cargar trackings', 'error');
        }
    },
    
    async filterTrackings(status) {
        await this.loadTrackings(status);
    },
    
    async searchTrackings(query) {
        const resultsContainer = document.getElementById('search-results');
        
        if (!query || query.length < 2) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <p>Escribe al menos 2 caracteres para buscar</p>
                </div>
            `;
            return;
        }
        
        try {
            const response = await this.apiRequest(`/api/trackings?search=${encodeURIComponent(query)}`);
            
            if (response.success) {
                if (response.trackings.length === 0) {
                    resultsContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">📭</div>
                            <p>No se encontraron resultados para "${this.escapeHtml(query)}"</p>
                        </div>
                    `;
                } else {
                    this.renderTrackingsList(response.trackings, 'search-results');
                }
            }
        } catch (error) {
            console.error('Error searching:', error);
            this.showToast('Error en la busqueda', 'error');
        }
    },
    
    renderTrackingsList(trackings, containerId = 'trackings-list') {
        const container = document.getElementById(containerId);
        
        if (!trackings || trackings.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <p>No hay trackings disponibles</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = trackings.map(t => `
            <div class="tracking-card" data-id="${this.escapeHtml(t.trackingId)}">
                <div class="tracking-header">
                    <span class="tracking-id">${this.escapeHtml(this.truncateId(t.trackingId))}</span>
                    <span class="tracking-status status-${this.escapeHtml(t.status)}">
                        ${this.escapeHtml(t.statusIcon)} ${this.escapeHtml(t.statusLabel)}
                    </span>
                </div>
                <div class="tracking-info">
                    <div class="tracking-info-row">
                        <span class="icon">👤</span>
                        <span class="value">${this.escapeHtml(t.recipientName || 'Sin nombre')}</span>
                    </div>
                    <div class="tracking-info-row">
                        <span class="icon">📦</span>
                        <span class="value">${this.escapeHtml(t.productName || 'Sin producto')}</span>
                    </div>
                    ${t.productPrice ? `
                    <div class="tracking-info-row">
                        <span class="icon">💰</span>
                        <span class="value">${this.escapeHtml(t.productPrice)}€</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        container.querySelectorAll('.tracking-card').forEach(card => {
            card.addEventListener('click', () => {
                this.showTrackingDetail(card.dataset.id);
            });
        });
    },
    
    truncateId(id) {
        if (id && id.length > 25) {
            return id.substring(0, 22) + '...';
        }
        return id;
    },
    
    async showTrackingDetail(trackingId) {
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(trackingId)}`);
            
            if (!response.success) {
                this.showToast('Error al cargar detalles', 'error');
                return;
            }
            
            const t = response.tracking;
            const history = response.history || [];
            
            const detailContainer = document.getElementById('tracking-detail');
            
            detailContainer.innerHTML = `
                <div class="detail-section">
                    <div class="tracking-header" style="margin-bottom: 0;">
                        <span class="tracking-id" style="font-size: 14px;">${this.escapeHtml(t.trackingId)}</span>
                        <span class="tracking-status status-${this.escapeHtml(t.status)}">
                            ${this.escapeHtml(t.statusIcon)} ${this.escapeHtml(t.statusLabel)}
                        </span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Informacion del Paquete</div>
                    <div class="detail-row">
                        <span class="detail-label">Destinatario</span>
                        <span class="detail-value">${this.escapeHtml(t.recipientName || 'No especificado')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Producto</span>
                        <span class="detail-value">${this.escapeHtml(t.productName || 'No especificado')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Precio</span>
                        <span class="detail-value">${this.escapeHtml(t.productPrice || '0')}€</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Peso</span>
                        <span class="detail-value">${this.escapeHtml(t.packageWeight || 'No especificado')}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Direcciones</div>
                    <div class="detail-row">
                        <span class="detail-label">Direccion entrega</span>
                        <span class="detail-value">${this.escapeHtml(t.deliveryAddress || 'No especificada')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">CP Destino</span>
                        <span class="detail-value">${this.escapeHtml(t.recipientPostalCode || '-')} ${this.escapeHtml(t.recipientProvince || '')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Pais Destino</span>
                        <span class="detail-value">${this.escapeHtml(t.recipientCountry || 'No especificado')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Direccion origen</span>
                        <span class="detail-value">${this.escapeHtml(t.senderAddress || 'No especificada')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">CP Origen</span>
                        <span class="detail-value">${this.escapeHtml(t.senderPostalCode || '-')} ${this.escapeHtml(t.senderProvince || '')}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Fechas</div>
                    <div class="detail-row">
                        <span class="detail-label">Entrega estimada</span>
                        <span class="detail-value">${this.escapeHtml(t.estimatedDelivery || 'Por calcular')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Dias de retraso</span>
                        <span class="detail-value">${parseInt(t.delayDays) || 0} dias</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Creado</span>
                        <span class="detail-value">${this.formatDate(t.createdAt)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Actualizado</span>
                        <span class="detail-value">${this.formatDate(t.updatedAt)}</span>
                    </div>
                </div>
                
                ${history.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-title">Historial</div>
                    ${history.slice(0, 5).map(h => `
                        <div class="history-item">
                            <div class="history-status">${this.escapeHtml(h.status)}</div>
                            ${h.notes ? `<div class="history-notes">${this.escapeHtml(h.notes)}</div>` : ''}
                            <div class="history-date">${this.formatDate(h.changedAt)}</div>
                        </div>
                    `).join('')}
                </div>
                ` : ''}
                
                <div class="detail-actions">
                    <button class="btn btn-primary" onclick="App.showChangeStatusModal('${t.trackingId}')">
                        🔄 Cambiar Estado
                    </button>
                    <button class="btn btn-warning" onclick="App.showDelayModal('${t.trackingId}')">
                        ⏰ Agregar Retraso
                    </button>
                    <button class="btn btn-secondary" onclick="App.showEditModal('${t.trackingId}')">
                        ✏️ Editar
                    </button>
                    ${this.isOwner ? `
                    <button class="btn btn-success" onclick="App.showEmailModal('${t.trackingId}')">
                        📧 Enviar Email
                    </button>
                    ` : ''}
                    <button class="btn btn-danger" onclick="App.confirmDelete('${t.trackingId}')">
                        🗑️ Eliminar
                    </button>
                </div>
            `;
            
            this.switchSection('detail');
            
        } catch (error) {
            console.error('Error loading detail:', error);
            this.showToast('Error al cargar detalles', 'error');
        }
    },
    
    formatDate(dateString) {
        if (!dateString) return 'No disponible';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    },
    
    async createTracking() {
        const form = document.getElementById('create-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        if (!data.trackingId || !data.recipientName || !data.productName) {
            this.showToast('Por favor completa los campos obligatorios', 'error');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/tracking', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            if (response.success) {
                this.showToast('Tracking creado correctamente', 'success');
                form.reset();
                await this.loadInitialData();
                this.switchSection('dashboard');
            } else {
                this.showToast(response.error || 'Error al crear tracking', 'error');
            }
        } catch (error) {
            console.error('Error creating tracking:', error);
            this.showToast('Error al crear tracking', 'error');
        }
    },
    
    showChangeStatusModal(trackingId) {
        const statuses = [
            { value: 'RETENIDO', icon: '📦', label: 'Retenido' },
            { value: 'EN_TRANSITO', icon: '🚚', label: 'En Camino' },
            { value: 'CONFIRMAR_PAGO', icon: '💰', label: 'Confirmar Pago' },
            { value: 'ENTREGADO', icon: '✅', label: 'Entregado' }
        ];
        
        const modalContent = `
            <div class="modal-header">
                <span class="modal-title">Cambiar Estado</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                ${statuses.map(s => `
                    <div class="status-option" data-status="${s.value}" onclick="App.changeStatus('${trackingId}', '${s.value}')">
                        <span class="status-option-icon">${s.icon}</span>
                        <span class="status-option-label">${s.label}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.showModal(modalContent);
    },
    
    async changeStatus(trackingId, newStatus) {
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(trackingId)}/status`, {
                method: 'PUT',
                body: JSON.stringify({ status: newStatus })
            });
            
            if (response.success) {
                this.showToast('Estado actualizado', 'success');
                this.closeModal();
                await this.showTrackingDetail(trackingId);
            } else {
                this.showToast(response.error || 'Error al actualizar', 'error');
            }
        } catch (error) {
            console.error('Error updating status:', error);
            this.showToast('Error al actualizar estado', 'error');
        }
    },
    
    showDelayModal(trackingId) {
        const reasons = this.delayReasons.length > 0 ? this.delayReasons : [
            { id: 'customs', text: 'Problemas en aduana', days: 3 },
            { id: 'high_demand', text: 'Alta demanda', days: 2 },
            { id: 'weather', text: 'Condiciones climaticas', days: 1 },
            { id: 'logistics', text: 'Problemas logisticos', days: 2 }
        ];
        
        const modalContent = `
            <div class="modal-header">
                <span class="modal-title">Agregar Retraso</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                ${reasons.map(r => `
                    <div class="delay-option" onclick="App.addDelay('${trackingId}', ${r.days}, '${r.text}')">
                        <span class="delay-option-text">${r.text}</span>
                        <span class="delay-option-days">+${r.days} dias</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.showModal(modalContent);
    },
    
    async addDelay(trackingId, days, reason) {
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(trackingId)}/delay`, {
                method: 'POST',
                body: JSON.stringify({ days, reason })
            });
            
            if (response.success) {
                this.showToast(`Retraso de ${days} dias agregado`, 'success');
                this.closeModal();
                await this.showTrackingDetail(trackingId);
            } else {
                this.showToast(response.error || 'Error al agregar retraso', 'error');
            }
        } catch (error) {
            console.error('Error adding delay:', error);
            this.showToast('Error al agregar retraso', 'error');
        }
    },
    
    showEditModal(trackingId) {
        const tracking = this.findTrackingById(trackingId);
        
        const modalContent = `
            <div class="modal-header">
                <span class="modal-title">Editar Tracking</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Nombre Destinatario</label>
                    <input type="text" id="edit-recipient" value="${this.escapeAttribute(tracking?.recipientName || '')}" class="email-input">
                </div>
                <div class="form-group">
                    <label>Producto</label>
                    <input type="text" id="edit-product" value="${this.escapeAttribute(tracking?.productName || '')}" class="email-input">
                </div>
                <div class="form-group">
                    <label>Precio</label>
                    <input type="text" id="edit-price" value="${this.escapeAttribute(tracking?.productPrice || '')}" class="email-input">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                <button class="btn btn-primary" onclick="App.saveEdit('${this.sanitizeForJs(trackingId)}')">Guardar</button>
            </div>
        `;
        
        this.showModal(modalContent);
    },
    
    async saveEdit(trackingId) {
        const recipientName = document.getElementById('edit-recipient').value;
        const productName = document.getElementById('edit-product').value;
        const productPrice = document.getElementById('edit-price').value;
        
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(trackingId)}`, {
                method: 'PUT',
                body: JSON.stringify({ recipientName, productName, productPrice })
            });
            
            if (response.success) {
                this.showToast('Tracking actualizado', 'success');
                this.closeModal();
                await this.showTrackingDetail(trackingId);
            } else {
                this.showToast(response.error || 'Error al actualizar', 'error');
            }
        } catch (error) {
            console.error('Error updating tracking:', error);
            this.showToast('Error al actualizar tracking', 'error');
        }
    },
    
    emailStep: 1,
    emailData: {},
    
    showEmailModal(trackingId) {
        this.emailStep = 1;
        this.emailData = { trackingId };
        this.renderEmailStep();
    },
    
    renderEmailStep() {
        let content = '';
        
        if (this.emailStep === 1) {
            content = `
                <div class="modal-header">
                    <span class="modal-title">Enviar Email</span>
                    <button class="modal-close" onclick="App.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="email-step">
                        <div class="email-step-number">1</div>
                        <div class="email-step-title">Email del destinatario</div>
                        <input type="email" id="email-recipient" class="email-input" placeholder="ejemplo@correo.com">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                    <button class="btn btn-primary" onclick="App.nextEmailStep()">Siguiente</button>
                </div>
            `;
        } else if (this.emailStep === 2) {
            content = `
                <div class="modal-header">
                    <span class="modal-title">Enviar Email</span>
                    <button class="modal-close" onclick="App.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="email-step">
                        <div class="email-step-number">2</div>
                        <div class="email-step-title">Entidad Bancaria</div>
                        <input type="text" id="email-bank" class="email-input" placeholder="Ej: CaixaBank, Santander, BBVA...">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.prevEmailStep()">Atras</button>
                    <button class="btn btn-primary" onclick="App.nextEmailStep()">Siguiente</button>
                </div>
            `;
        } else if (this.emailStep === 3) {
            content = `
                <div class="modal-header">
                    <span class="modal-title">Enviar Email</span>
                    <button class="modal-close" onclick="App.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="email-step">
                        <div class="email-step-number">3</div>
                        <div class="email-step-title">IBAN</div>
                        <input type="text" id="email-iban" class="email-input" placeholder="ES00 0000 0000 0000 0000 0000">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.prevEmailStep()">Atras</button>
                    <button class="btn btn-success" onclick="App.sendEmail()">Enviar Email</button>
                </div>
            `;
        }
        
        this.showModal(content);
    },
    
    nextEmailStep() {
        if (this.emailStep === 1) {
            const email = document.getElementById('email-recipient').value;
            if (!email || !email.includes('@')) {
                this.showToast('Introduce un email valido', 'error');
                return;
            }
            this.emailData.email = email;
        } else if (this.emailStep === 2) {
            const bank = document.getElementById('email-bank').value;
            if (!bank) {
                this.showToast('Introduce la entidad bancaria', 'error');
                return;
            }
            this.emailData.bankEntity = bank;
        }
        
        this.emailStep++;
        this.renderEmailStep();
    },
    
    prevEmailStep() {
        this.emailStep--;
        this.renderEmailStep();
    },
    
    async sendEmail() {
        const iban = document.getElementById('email-iban').value;
        if (!iban) {
            this.showToast('Introduce el IBAN', 'error');
            return;
        }
        this.emailData.iban = iban;
        
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(this.emailData.trackingId)}/email`, {
                method: 'POST',
                body: JSON.stringify(this.emailData)
            });
            
            if (response.success) {
                this.showToast('Email enviado correctamente', 'success');
                this.closeModal();
            } else {
                this.showToast(response.error || 'Error al enviar email', 'error');
            }
        } catch (error) {
            console.error('Error sending email:', error);
            this.showToast('Error al enviar email', 'error');
        }
    },
    
    confirmDelete(trackingId) {
        const modalContent = `
            <div class="modal-header">
                <span class="modal-title">Confirmar Eliminacion</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="text-align: center; margin-bottom: 16px;">
                    ¿Estas seguro de que quieres eliminar este tracking?
                </p>
                <p style="text-align: center; color: var(--accent-danger); font-size: 12px;">
                    Esta accion no se puede deshacer
                </p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                <button class="btn btn-danger" onclick="App.deleteTracking('${trackingId}')">Eliminar</button>
            </div>
        `;
        
        this.showModal(modalContent);
    },
    
    async deleteTracking(trackingId) {
        try {
            const response = await this.apiRequest(`/api/tracking/${encodeURIComponent(trackingId)}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Tracking eliminado', 'success');
                this.closeModal();
                await this.loadInitialData();
                this.switchSection('dashboard');
            } else {
                this.showToast(response.error || 'Error al eliminar', 'error');
            }
        } catch (error) {
            console.error('Error deleting tracking:', error);
            this.showToast('Error al eliminar tracking', 'error');
        }
    },
    
    findTrackingById(trackingId) {
        return this.trackings.find(t => t.trackingId === trackingId);
    },
    
    showModal(content) {
        const modal = document.getElementById('modal-content');
        const overlay = document.getElementById('modal-overlay');
        modal.innerHTML = content;
        overlay.classList.remove('hidden');
        overlay.setAttribute('aria-hidden', 'false');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        const focusable = modal.querySelector('button, input, [tabindex]:not([tabindex="-1"])');
        if (focusable) focusable.focus();
    },
    
    closeModal() {
        const overlay = document.getElementById('modal-overlay');
        overlay.classList.add('hidden');
        overlay.setAttribute('aria-hidden', 'true');
    },
    
    showToast(message, type = 'info') {
        if (this.tg && this.tg.HapticFeedback) {
            try {
                this.tg.HapticFeedback.notificationOccurred(
                    type === 'error' ? 'error' : type === 'success' ? 'success' : 'warning'
                );
            } catch (e) {
                Logger?.debug('Haptic feedback not available');
            }
        }
        
        return Toast.show(message, type, 3000);
    },

    showRechargeSuccess(amount) {
        const overlay = document.createElement('div');
        overlay.className = 'recharge-success-animation';
        overlay.innerHTML = `
            <div class="confetti-container" id="confetti-container"></div>
            <div class="recharge-success-content">
                <div class="recharge-success-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <div class="recharge-success-amount">+${amount} B3C</div>
                <div class="recharge-success-text">Recarga exitosa</div>
                <div class="recharge-success-subtitle">Tu balance ha sido actualizado</div>
            </div>
        `;
        document.body.appendChild(overlay);
        
        this.launchConfetti();
        
        if (this.tg && this.tg.HapticFeedback) {
            try {
                this.tg.HapticFeedback.notificationOccurred('success');
            } catch (e) {}
        }
        
        this.refreshBalanceAfterTransaction();
        
        setTimeout(() => {
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.5s ease';
            setTimeout(() => overlay.remove(), 500);
        }, 3000);
    },
    
    launchConfetti() {
        const container = document.getElementById('confetti-container');
        if (!container) return;
        
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti-piece';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 0.5 + 's';
            confetti.style.animationDuration = (Math.random() * 1 + 2) + 's';
            container.appendChild(confetti);
        }
    },
    
    async refreshBalanceAfterTransaction() {
        await this.loadWalletBalance(true);
        this.loadTransactionHistory(0, false);
        
        setTimeout(() => this.loadWalletBalance(true), 2000);
        setTimeout(() => this.loadWalletBalance(true), 5000);
    },
    
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.isDemoMode) {
            headers['X-Demo-Mode'] = 'true';
        } else if (this.initData) {
            headers['X-Telegram-Init-Data'] = this.initData;
        }
        
        return headers;
    },
    
    async apiRequest(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.isDemoMode) {
            headers['X-Demo-Mode'] = 'true';
            if (this.demoSessionToken) {
                headers['X-Demo-Session'] = this.demoSessionToken;
            }
        } else if (this.initData) {
            headers['X-Telegram-Init-Data'] = this.initData;
        }
        
        const mergedOptions = {
            ...options,
            headers: {
                ...headers,
                ...(options.headers || {})
            }
        };
        
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok && !data.success) {
            if (data.code === 'DEMO_2FA_REQUIRED' && this.isDemoMode) {
                throw new Error('DEMO_2FA_REQUIRED');
            }
            throw new Error(data.error || `HTTP error ${response.status}`);
        }
        
        return data;
    },
    
    async loadUserBots() {
        const myBotsList = document.getElementById('my-bots-list');
        const myBotsEmpty = document.getElementById('my-bots-empty');
        
        SafeDOM.setHTML(myBotsList, '<div class="bots-loading"><div class="loading-spinner"></div><p>Cargando tus bots...</p></div>');
        myBotsEmpty.classList.add('hidden');
        
        try {
            const myBotsResponse = await this.apiRequest('/api/bots/my');
            this.renderMyBots(myBotsResponse.bots || []);
            
        } catch (error) {
            console.error('Error loading bots:', error);
            SafeDOM.setHTML(myBotsList, '<div class="bots-empty"><div class="empty-icon">⚠️</div><p>Error al cargar bots</p></div>');
        }
    },
    
    renderMyBots(bots) {
        const myBotsList = document.getElementById('my-bots-list');
        const myBotsEmpty = document.getElementById('my-bots-empty');
        
        if (!bots || bots.length === 0) {
            myBotsList.textContent = '';
            myBotsEmpty.classList.remove('hidden');
            return;
        }
        
        myBotsEmpty.classList.add('hidden');
        SafeDOM.setTrustedHTML(myBotsList, bots.map(bot => {
            const isActive = bot.isActive !== false;
            const statusClass = isActive ? 'online' : 'offline';
            const statusText = isActive ? 'Activo' : 'Inactivo';
            
            if (bot.botType === 'tracking_manager') {
                return `
                    <div class="bot-card active-bot owner-bot clickable" data-bot-id="${bot.id}" onclick="App.openBotPanel('${this.escapeHtml(bot.botType)}')">
                        <div class="bot-avatar">${bot.icon || '🤖'}</div>
                        <div class="bot-info">
                            <h3>${this.escapeHtml(bot.botName)}</h3>
                            <p class="bot-status ${statusClass}">${statusText}</p>
                            ${bot.description ? `<p class="bot-desc">${this.escapeHtml(bot.description)}</p>` : ''}
                        </div>
                        <div class="bot-arrow">→</div>
                    </div>
                `;
            }
            return `
                <div class="bot-card active-bot ${!isActive ? 'bot-inactive' : ''}" data-bot-id="${bot.id}">
                    <div class="bot-avatar">${bot.icon || '🤖'}</div>
                    <div class="bot-info">
                        <h3>${this.escapeHtml(bot.botName)}</h3>
                        <p class="bot-status ${statusClass}">${statusText}</p>
                        ${bot.description ? `<p class="bot-desc">${this.escapeHtml(bot.description)}</p>` : ''}
                    </div>
                    <div class="bot-controls">
                        <label class="bot-toggle" onclick="event.stopPropagation()">
                            <input type="checkbox" ${isActive ? 'checked' : ''} onchange="App.toggleBot(${bot.id}, this.checked)">
                            <span class="toggle-slider"></span>
                        </label>
                        <button class="bot-config-btn" onclick="App.openBotConfig(${bot.id}, '${this.escapeHtml(bot.botName)}')" title="Configurar">⚙️</button>
                    </div>
                </div>
            `;
        }).join(''));
    },
    
    openBotPanel(botType) {
        if (botType === 'tracking_manager') {
            document.getElementById('bots-screen').classList.add('hidden');
            document.getElementById('home-screen').classList.add('hidden');
            document.getElementById('tracking-module').classList.remove('hidden');
            this.previousSection = 'bots';
            this.loadTrackings();
        }
    },
    
    renderAvailableBots(bots) {
        const availableBotsList = document.getElementById('available-bots-list');
        const availableBotsEmpty = document.getElementById('available-bots-empty');
        
        if (!bots || bots.length === 0) {
            availableBotsList.innerHTML = '';
            availableBotsEmpty.classList.remove('hidden');
            return;
        }
        
        availableBotsEmpty.classList.add('hidden');
        availableBotsList.innerHTML = bots.map(bot => `
            <div class="bot-card available-bot" data-bot-type="${bot.botType}">
                <div class="bot-avatar">${bot.icon || '🤖'}</div>
                <div class="bot-info">
                    <h3>${this.escapeHtml(bot.botName)}</h3>
                    <p class="bot-desc">${this.escapeHtml(bot.description || '')}</p>
                    <span class="bot-price">${bot.price > 0 ? bot.price + ' BUNK3RCO1N' : 'Gratis'}</span>
                </div>
                <div class="bot-actions">
                    <button class="bot-buy-btn" onclick="App.purchaseBot('${this.escapeHtml(bot.botType)}', '${this.escapeHtml(bot.botName)}', ${bot.price})">
                        ${bot.price > 0 ? 'Obtener' : 'Activar'}
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    configureBot(botId, botType) {
        this.openBotConfig(botId, botType);
    },
    
    async toggleBot(botId, activate) {
        try {
            const response = await this.apiRequest(`/api/bots/${botId}/toggle`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(response.message || (response.isActive ? 'Bot activado' : 'Bot desactivado'), 'success');
            } else {
                this.showToast(response.error || 'Error al cambiar estado', 'error');
                await this.loadUserBots();
            }
        } catch (error) {
            console.error('Error toggling bot:', error);
            this.showToast('Error al cambiar estado del bot', 'error');
            await this.loadUserBots();
        }
    },
    
    async openBotConfig(botId, botName) {
        try {
            const response = await this.apiRequest(`/api/bots/${botId}/config`);
            
            if (!response.success) {
                this.showToast(response.error || 'Error al cargar configuracion', 'error');
                return;
            }
            
            const config = response.config || {};
            const modalContent = `
                <div class="modal-header">
                    <h3>Configurar ${this.escapeHtml(botName)}</h3>
                    <button class="modal-close" onclick="App.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="config-section">
                        <label class="config-label">Notificaciones</label>
                        <div class="config-option">
                            <span>Recibir alertas</span>
                            <label class="bot-toggle">
                                <input type="checkbox" id="config-notifications" ${config.notifications !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="config-section">
                        <label class="config-label">Frecuencia de actualizaciones</label>
                        <select id="config-frequency" class="config-select">
                            <option value="realtime" ${config.frequency === 'realtime' ? 'selected' : ''}>Tiempo real</option>
                            <option value="hourly" ${config.frequency === 'hourly' ? 'selected' : ''}>Cada hora</option>
                            <option value="daily" ${config.frequency === 'daily' ? 'selected' : ''}>Diario</option>
                        </select>
                    </div>
                    <div class="config-section">
                        <label class="config-label">Modo silencioso</label>
                        <div class="config-option">
                            <span>No molestar de noche</span>
                            <label class="bot-toggle">
                                <input type="checkbox" id="config-silent" ${config.silentMode ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                    <button class="btn btn-primary" onclick="App.saveBotConfig(${botId})">Guardar</button>
                </div>
            `;
            
            this.showModal(modalContent);
        } catch (error) {
            console.error('Error loading bot config:', error);
            this.showToast('Error al cargar configuracion', 'error');
        }
    },
    
    async saveBotConfig(botId) {
        try {
            const config = {
                notifications: document.getElementById('config-notifications')?.checked !== false,
                frequency: document.getElementById('config-frequency')?.value || 'realtime',
                silentMode: document.getElementById('config-silent')?.checked || false
            };
            
            const response = await this.apiRequest(`/api/bots/${botId}/config`, {
                method: 'POST',
                body: JSON.stringify({ config })
            });
            
            if (response.success) {
                this.showToast('Configuracion guardada', 'success');
                this.closeModal();
            } else {
                this.showToast(response.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error saving bot config:', error);
            this.showToast('Error al guardar configuracion', 'error');
        }
    },
    
    confirmRemoveBot(botId, botName) {
        const modalContent = `
            <div class="modal-header">
                <h3>Desactivar Bot</h3>
            </div>
            <div class="modal-body">
                <p style="text-align: center; margin-bottom: 16px;">
                    Estas seguro que quieres desactivar <strong>${this.escapeHtml(botName)}</strong>?
                </p>
                <p style="text-align: center; color: var(--text-secondary); font-size: 12px;">
                    Podras volver a activarlo desde los bots disponibles
                </p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                <button class="btn btn-danger" onclick="App.removeBot(${botId})">Desactivar</button>
            </div>
        `;
        
        this.showModal(modalContent);
    },
    
    async removeBot(botId) {
        try {
            const response = await this.apiRequest(`/api/bots/${botId}/remove`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Bot desactivado correctamente', 'success');
                this.closeModal();
                await this.loadUserBots();
            } else {
                this.showToast(response.error || 'Error al desactivar bot', 'error');
            }
        } catch (error) {
            console.error('Error removing bot:', error);
            this.showToast('Error al desactivar bot', 'error');
        }
    },
    
    async purchaseBot(botType, botName, price) {
        if (price > 0) {
            const modalContent = `
                <div class="modal-header">
                    <h3>Confirmar Compra</h3>
                </div>
                <div class="modal-body">
                    <p style="text-align: center; margin-bottom: 16px;">
                        Quieres obtener <strong>${this.escapeHtml(botName)}</strong>?
                    </p>
                    <p style="text-align: center; font-size: 18px; font-weight: bold; color: var(--accent-warning);">
                        ${price} BUNK3RCO1N
                    </p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                    <button class="btn btn-primary" onclick="App.confirmPurchaseBot('${this.escapeHtml(botType)}')">Confirmar</button>
                </div>
            `;
            this.showModal(modalContent);
        } else {
            await this.confirmPurchaseBot(botType);
        }
    },
    
    async confirmPurchaseBot(botType) {
        try {
            const response = await this.apiRequest('/api/bots/purchase', {
                method: 'POST',
                body: JSON.stringify({ botType: botType })
            });
            
            if (response.success) {
                this.showToast(response.message || 'Bot activado correctamente', 'success');
                this.closeModal();
                await this.loadUserBots();
                
                if (response.creditsRemaining !== undefined) {
                    const walletBalance = document.getElementById('wallet-balance');
                    if (walletBalance) {
                        walletBalance.textContent = response.creditsRemaining.toLocaleString();
                    }
                }
            } else {
                this.showToast(response.error || 'Error al obtener bot', 'error');
            }
        } catch (error) {
            console.error('Error purchasing bot:', error);
            this.showToast(error.message || 'Error al obtener bot', 'error');
        }
    },
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    escapeAttribute(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    },

    sanitizeForJs(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/\\/g, '\\\\')
            .replace(/'/g, "\\'")
            .replace(/"/g, '\\"')
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '\\r');
    },
    
    // ========== EXCHANGE FUNCTIONS ==========
    exchangeData: {
        currencies: [],
        fromCurrency: { ticker: 'btc', name: 'Bitcoin', image: '' },
        toCurrency: { ticker: 'eth', name: 'Ethereum', image: '' },
        selectingFor: 'from',
        estimateTimeout: null
    },
    
    initExchange() {
        const fromBtn = document.getElementById('from-currency-btn');
        const toBtn = document.getElementById('to-currency-btn');
        const swapBtn = document.getElementById('swap-currencies-btn');
        const amountInput = document.getElementById('exchange-amount-from');
        const createBtn = document.getElementById('create-exchange-btn');
        const modalClose = document.getElementById('currency-modal-close');
        const searchInput = document.getElementById('currency-search');
        const copyBtn = document.getElementById('copy-payin-address');
        const newExchangeBtn = document.getElementById('new-exchange-btn');
        
        if (fromBtn) {
            fromBtn.addEventListener('click', () => this.openCurrencyModal('from'));
        }
        if (toBtn) {
            toBtn.addEventListener('click', () => this.openCurrencyModal('to'));
        }
        if (swapBtn) {
            swapBtn.addEventListener('click', () => this.swapCurrencies());
        }
        if (amountInput) {
            amountInput.addEventListener('input', () => this.debounceEstimate());
        }
        if (createBtn) {
            createBtn.addEventListener('click', () => this.createExchange());
        }
        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeCurrencyModal());
        }
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterCurrencies(e.target.value));
        }
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyPayinAddress());
        }
        if (newExchangeBtn) {
            newExchangeBtn.addEventListener('click', () => this.resetExchange());
        }
        
        document.getElementById('currency-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'currency-modal') {
                this.closeCurrencyModal();
            }
        });
    },
    
    async loadExchangeCurrencies() {
        try {
            const response = await this.apiRequest('/api/exchange/currencies');
            if (response.success && response.currencies) {
                this.exchangeData.currencies = response.currencies;
            }
        } catch (error) {
            console.error('Error loading currencies:', error);
        }
    },
    
    openCurrencyModal(selectingFor) {
        this.exchangeData.selectingFor = selectingFor;
        const modal = document.getElementById('currency-modal');
        const list = document.getElementById('currency-list');
        const search = document.getElementById('currency-search');
        
        if (modal) {
            modal.classList.remove('hidden');
            if (search) search.value = '';
            this.renderCurrencyList(this.exchangeData.currencies);
            
            if (this.exchangeData.currencies.length === 0) {
                list.innerHTML = '<div class="currency-loading">Cargando monedas...</div>';
                this.loadExchangeCurrencies().then(() => {
                    this.renderCurrencyList(this.exchangeData.currencies);
                });
            }
        }
    },
    
    closeCurrencyModal() {
        document.getElementById('currency-modal')?.classList.add('hidden');
    },
    
    renderCurrencyList(currencies) {
        const list = document.getElementById('currency-list');
        if (!list) return;
        
        if (!currencies || currencies.length === 0) {
            list.innerHTML = '<div class="currency-loading">No hay monedas disponibles</div>';
            return;
        }
        
        list.innerHTML = currencies.slice(0, 100).map(c => `
            <div class="currency-item" onclick="App.selectCurrency('${this.sanitizeForJs(c.ticker)}', '${this.sanitizeForJs(c.name)}', '${this.sanitizeForJs(c.image || '')}')">
                <div class="currency-item-icon">
                    ${c.image ? `<img src="${this.escapeAttribute(c.image)}" alt="${this.escapeAttribute(c.ticker)}" onerror="this.style.display='none'">` : this.escapeHtml(c.ticker.substring(0, 2).toUpperCase())}
                </div>
                <div class="currency-item-info">
                    <div class="currency-item-ticker">${this.escapeHtml(c.ticker.toUpperCase())}</div>
                    <div class="currency-item-name">${this.escapeHtml(c.name)}</div>
                </div>
            </div>
        `).join('');
    },
    
    filterCurrencies(query) {
        const filtered = this.exchangeData.currencies.filter(c => 
            c.ticker.toLowerCase().includes(query.toLowerCase()) ||
            c.name.toLowerCase().includes(query.toLowerCase())
        );
        this.renderCurrencyList(filtered);
    },
    
    selectCurrency(ticker, name, image) {
        const target = this.exchangeData.selectingFor;
        
        if (target === 'from') {
            this.exchangeData.fromCurrency = { ticker, name, image };
            document.getElementById('from-currency-ticker').textContent = ticker.toUpperCase();
        } else {
            this.exchangeData.toCurrency = { ticker, name, image };
            document.getElementById('to-currency-ticker').textContent = ticker.toUpperCase();
            document.getElementById('to-currency-label').textContent = ticker.toUpperCase();
        }
        
        this.closeCurrencyModal();
        this.updateMinAmount();
        this.debounceEstimate();
    },
    
    swapCurrencies() {
        const temp = this.exchangeData.fromCurrency;
        this.exchangeData.fromCurrency = this.exchangeData.toCurrency;
        this.exchangeData.toCurrency = temp;
        
        document.getElementById('from-currency-ticker').textContent = this.exchangeData.fromCurrency.ticker.toUpperCase();
        document.getElementById('to-currency-ticker').textContent = this.exchangeData.toCurrency.ticker.toUpperCase();
        document.getElementById('to-currency-label').textContent = this.exchangeData.toCurrency.ticker.toUpperCase();
        
        this.updateMinAmount();
        this.debounceEstimate();
    },
    
    async updateMinAmount() {
        const from = this.exchangeData.fromCurrency.ticker;
        const to = this.exchangeData.toCurrency.ticker;
        const minAmountInfo = document.getElementById('min-amount-info');
        
        try {
            const response = await this.apiRequest(`/api/exchange/min-amount?from=${from}&to=${to}`);
            if (response.success && response.minAmount) {
                minAmountInfo.textContent = `Minimo: ${response.minAmount} ${from.toUpperCase()}`;
            }
        } catch (error) {
            minAmountInfo.textContent = '';
        }
    },
    
    debounceEstimate() {
        if (this.exchangeData.estimateTimeout) {
            clearTimeout(this.exchangeData.estimateTimeout);
        }
        this.exchangeData.estimateTimeout = setTimeout(() => this.getEstimate(), 500);
    },
    
    async getEstimate() {
        const amount = document.getElementById('exchange-amount-from')?.value;
        const from = this.exchangeData.fromCurrency.ticker;
        const to = this.exchangeData.toCurrency.ticker;
        const rateValue = document.getElementById('rate-value');
        const amountTo = document.getElementById('exchange-amount-to');
        
        if (!amount || parseFloat(amount) <= 0) {
            if (amountTo) amountTo.value = '';
            if (rateValue) rateValue.textContent = '--';
            return;
        }
        
        try {
            const response = await this.apiRequest(`/api/exchange/estimate?from=${from}&to=${to}&amount=${amount}`);
            if (response.success && response.estimatedAmount) {
                if (amountTo) amountTo.value = response.estimatedAmount;
                if (rateValue) {
                    const rate = (response.estimatedAmount / parseFloat(amount)).toFixed(6);
                    rateValue.textContent = `1 ${from.toUpperCase()} ≈ ${rate} ${to.toUpperCase()}`;
                }
            } else {
                if (amountTo) amountTo.value = '';
                if (rateValue) rateValue.textContent = response.error || 'Error';
            }
        } catch (error) {
            if (amountTo) amountTo.value = '';
            if (rateValue) rateValue.textContent = 'Error al estimar';
        }
    },
    
    async createExchange() {
        const amount = document.getElementById('exchange-amount-from')?.value;
        const address = document.getElementById('exchange-address')?.value;
        const refundAddress = document.getElementById('exchange-refund-address')?.value;
        const from = this.exchangeData.fromCurrency.ticker;
        const to = this.exchangeData.toCurrency.ticker;
        
        if (!amount || parseFloat(amount) <= 0) {
            this.showToast('Ingresa un monto valido', 'error');
            return;
        }
        
        if (!address) {
            this.showToast('Ingresa tu direccion de wallet', 'error');
            return;
        }
        
        const btn = document.getElementById('create-exchange-btn');
        const btnText = btn?.querySelector('.btn-text');
        const btnLoader = btn?.querySelector('.btn-loader');
        
        if (btn) btn.disabled = true;
        if (btnText) btnText.textContent = 'Procesando...';
        if (btnLoader) btnLoader.classList.remove('hidden');
        
        try {
            const response = await this.apiRequest('/api/exchange/create', {
                method: 'POST',
                body: JSON.stringify({
                    from: from,
                    to: to,
                    amount: amount,
                    address: address,
                    refundAddress: refundAddress
                })
            });
            
            if (response.success) {
                this.showExchangeResult(response);
                this.showToast('Intercambio creado exitosamente', 'success');
            } else {
                this.showToast(response.error || 'Error al crear intercambio', 'error');
            }
        } catch (error) {
            this.showToast(error.message || 'Error al crear intercambio', 'error');
        } finally {
            if (btn) btn.disabled = false;
            if (btnText) btnText.textContent = 'Intercambiar';
            if (btnLoader) btnLoader.classList.add('hidden');
        }
    },
    
    showExchangeResult(data) {
        document.querySelector('.exchange-card')?.classList.add('hidden');
        const result = document.getElementById('exchange-result');
        if (result) result.classList.remove('hidden');
        
        document.getElementById('result-tx-id').textContent = data.id;
        document.getElementById('result-from-currency').textContent = data.fromCurrency?.toUpperCase() || '';
        document.getElementById('result-payin-address').textContent = data.payinAddress;
        document.getElementById('result-amount').textContent = `${data.amount} ${data.fromCurrency?.toUpperCase()}`;
        
        if (data.payinExtraId) {
            document.getElementById('result-extra-id-container').style.display = 'block';
            document.getElementById('result-extra-id').textContent = data.payinExtraId;
        }
    },
    
    copyPayinAddress() {
        const address = document.getElementById('result-payin-address')?.textContent;
        if (address) {
            navigator.clipboard.writeText(address).then(() => {
                this.showToast('Direccion copiada', 'success');
            });
        }
    },
    
    resetExchange() {
        document.querySelector('.exchange-card')?.classList.remove('hidden');
        document.getElementById('exchange-result')?.classList.add('hidden');
        document.getElementById('exchange-amount-from').value = '';
        document.getElementById('exchange-amount-to').value = '';
        document.getElementById('exchange-address').value = '';
        document.getElementById('exchange-refund-address').value = '';
        document.getElementById('rate-value').textContent = '--';
        document.getElementById('result-extra-id-container').style.display = 'none';
    },

    initTonConnect() {
        const initializeSDK = async () => {
            try {
                const TonConnectUIClass = window.TON_CONNECT_UI?.TonConnectUI || window.TonConnectUI;
                
                if (!TonConnectUIClass) {
                    console.error('TON Connect UI class not found');
                    return;
                }
                
                this.tonConnectUI = new TonConnectUIClass({
                    manifestUrl: window.location.origin + '/static/tonconnect-manifest.json'
                });

                this.tonConnectUI.onStatusChange(async (wallet) => {
                    if (wallet) {
                        this.connectedWallet = wallet;
                        this.updateWalletUI(wallet);
                        await this.saveWalletToBackend(wallet.account.address);
                    } else {
                        this.connectedWallet = null;
                        const savedAddress = await this.loadSavedWallet();
                        if (!savedAddress) {
                            this.updateWalletUI(null);
                        }
                    }
                });

                this.setupTonConnectListeners();
                this.devLog('TON Connect initialized successfully');
                
                if (!this.tonConnectUI.wallet) {
                    await this.loadSavedWallet();
                }
            } catch (error) {
                console.error('Error initializing TON Connect:', error);
            }
        };

        const checkTonConnect = () => {
            return window.TON_CONNECT_UI?.TonConnectUI || window.TonConnectUI;
        };

        if (checkTonConnect()) {
            initializeSDK();
        } else {
            let attempts = 0;
            const checkInterval = setInterval(() => {
                attempts++;
                if (checkTonConnect()) {
                    clearInterval(checkInterval);
                    initializeSDK();
                } else if (attempts >= 20) {
                    clearInterval(checkInterval);
                    this.devLog('TonConnectUI failed to load after 10 seconds');
                }
            }, 500);
        }
    },

    setupTonConnectListeners() {
        const connectBtn = document.getElementById('ton-connect-btn');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connectWallet());
        }

        const disconnectBtn = document.getElementById('ton-disconnect-btn');
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnectWallet());
        }

        const changeBtn = document.getElementById('ton-change-btn');
        if (changeBtn) {
            changeBtn.addEventListener('click', () => this.connectWallet());
        }

        const copyAddressBtn = document.getElementById('ton-copy-address');
        if (copyAddressBtn) {
            copyAddressBtn.addEventListener('click', () => this.copyWalletAddress());
        }

        document.querySelectorAll('.recharge-option').forEach(option => {
            option.addEventListener('click', () => {
                const credits = parseInt(option.dataset.amount);
                const tonAmount = parseFloat(option.dataset.ton || option.dataset.usdt);
                if (credits && tonAmount) {
                    this.initiateTONPayment(credits, tonAmount);
                }
            });
        });

        const customRechargeBtn = document.getElementById('custom-recharge-btn');
        if (customRechargeBtn) {
            customRechargeBtn.addEventListener('click', () => {
                const input = document.getElementById('custom-usdt-amount');
                const amount = parseFloat(input?.value);
                if (amount && amount > 0) {
                    this.initiateTONPayment(Math.floor(amount * 10), amount);
                } else {
                    this.showToast('Ingresa una cantidad valida', 'error');
                }
            });
        }
    },

    async connectWallet() {
        try {
            if (!this.tonConnectUI) {
                this.showToast('TON Connect no disponible', 'error');
                return;
            }
            await this.tonConnectUI.openModal();
        } catch (error) {
            console.error('Error connecting wallet:', error);
            this.showToast('Error al conectar wallet', 'error');
        }
    },

    async disconnectWallet() {
        try {
            if (this.tonConnectUI) {
                await this.tonConnectUI.disconnect();
                this.showToast('Wallet desconectada', 'info');
            }
        } catch (error) {
            console.error('Error disconnecting wallet:', error);
        }
    },

    copyWalletAddress() {
        if (this.currentWalletAddress) {
            navigator.clipboard.writeText(this.currentWalletAddress).then(() => {
                this.showToast('Direccion copiada', 'success');
            }).catch(() => {
                this.showToast('Error al copiar', 'error');
            });
        }
    },

    rawAddressToUserFriendly(rawAddress, bounceable = false) {
        try {
            if (!rawAddress || !rawAddress.includes(':')) {
                return rawAddress;
            }
            
            const [workchainStr, hexHash] = rawAddress.split(':');
            const workchain = parseInt(workchainStr);
            
            const hashBytes = new Uint8Array(32);
            for (let i = 0; i < 32; i++) {
                hashBytes[i] = parseInt(hexHash.substr(i * 2, 2), 16);
            }
            
            const addressBytes = new Uint8Array(34);
            addressBytes[0] = bounceable ? 0x11 : 0x51;
            addressBytes[1] = workchain === -1 ? 0xff : workchain;
            addressBytes.set(hashBytes, 2);
            
            const crc = this.crc16(addressBytes);
            
            const fullAddress = new Uint8Array(36);
            fullAddress.set(addressBytes);
            fullAddress[34] = (crc >> 8) & 0xff;
            fullAddress[35] = crc & 0xff;
            
            let base64 = btoa(String.fromCharCode.apply(null, fullAddress));
            base64 = base64.replace(/\+/g, '-').replace(/\//g, '_');
            
            return base64;
        } catch (error) {
            console.error('Error converting address:', error);
            return rawAddress;
        }
    },

    crc16(data) {
        const polynomial = 0x1021;
        let crc = 0;
        
        for (let byte of data) {
            crc ^= byte << 8;
            for (let i = 0; i < 8; i++) {
                if (crc & 0x8000) {
                    crc = (crc << 1) ^ polynomial;
                } else {
                    crc <<= 1;
                }
                crc &= 0xffff;
            }
        }
        return crc;
    },

    updateWalletUI(wallet, isSyncedFromServer = false) {
        const notConnected = document.getElementById('ton-wallet-not-connected');
        const connected = document.getElementById('ton-wallet-connected');
        const addressEl = document.getElementById('ton-wallet-address');
        const statusLabel = document.getElementById('ton-wallet-status-label');
        const disconnectBtn = document.getElementById('ton-disconnect-btn');
        const changeBtn = document.getElementById('ton-change-btn');

        let rawAddress = null;
        if (wallet) {
            rawAddress = typeof wallet === 'string' ? wallet : wallet.account?.address;
        }

        if (rawAddress) {
            if (notConnected) notConnected.classList.add('hidden');
            if (connected) connected.classList.remove('hidden');
            
            const friendlyAddress = this.rawAddressToUserFriendly(rawAddress);
            this.currentWalletAddress = friendlyAddress;
            this.currentWalletRawAddress = rawAddress;
            
            if (addressEl) addressEl.textContent = friendlyAddress;
            
            if (isSyncedFromServer && !this.connectedWallet) {
                if (statusLabel) statusLabel.textContent = 'Wallet sincronizada';
                if (disconnectBtn) disconnectBtn.classList.add('hidden');
                if (changeBtn) changeBtn.classList.remove('hidden');
            } else {
                if (statusLabel) statusLabel.textContent = 'Wallet conectada';
                if (disconnectBtn) disconnectBtn.classList.remove('hidden');
                if (changeBtn) changeBtn.classList.add('hidden');
            }
            
            this.devLog('Wallet UI actualizada - Raw:', rawAddress.slice(0, 10) + '..., Friendly:', friendlyAddress, isSyncedFromServer ? '(sincronizada)' : '(conectada)');
        } else {
            if (notConnected) notConnected.classList.remove('hidden');
            if (connected) connected.classList.add('hidden');
            this.currentWalletAddress = null;
            this.currentWalletRawAddress = null;
        }
    },

    async loadSavedWallet() {
        try {
            this.devLog('Intentando cargar wallet guardada...');
            const headers = this.getAuthHeaders();
            this.devLog('Headers para wallet:', JSON.stringify(headers));
            
            const response = await fetch('/api/wallet/address', {
                method: 'GET',
                headers: headers
            });
            
            this.devLog('Response status:', response.status);
            const data = await response.json();
            this.devLog('Wallet response:', JSON.stringify(data));
            
            if (data.success && data.address) {
                this.devLog('Wallet cargada del servidor:', data.address);
                this.walletSyncedFromServer = true;
                this.syncedWalletAddress = data.address;
                this.updateWalletUI(data.address, true);
                return data.address;
            } else {
                this.devLog('No hay wallet guardada para este usuario');
                this.walletSyncedFromServer = false;
                this.syncedWalletAddress = null;
            }
        } catch (error) {
            console.error('Error cargando wallet guardada:', error.message || error);
        }
        return null;
    },

    async saveWalletToBackend(rawAddress) {
        try {
            const friendlyAddress = this.rawAddressToUserFriendly(rawAddress);
            const response = await fetch('/api/wallet/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ 
                    address: friendlyAddress,
                    rawAddress: rawAddress
                })
            });
            const data = await response.json();
            if (data.success) {
                this.devLog('Wallet guardada en el servidor:', friendlyAddress);
                
                const checkResponse = await this.apiRequest('/api/security/wallet/primary/check');
                
                if (checkResponse.success && !checkResponse.hasPrimaryWallet) {
                    await this.apiRequest('/api/security/wallet/primary/register', {
                        method: 'POST',
                        body: JSON.stringify({ walletAddress: friendlyAddress })
                    });
                    this.showToast('Wallet registrada como principal para seguridad', 'success');
                }
            }
        } catch (error) {
            console.error('Error guardando wallet:', error);
        }
    },

    validateTonWalletAddress(address) {
        if (!address || typeof address !== 'string') {
            return { valid: false, error: 'Direccion requerida' };
        }
        
        address = address.trim();
        
        if (address.length !== 48) {
            return { valid: false, error: 'La direccion debe tener 48 caracteres' };
        }
        
        const validPrefixes = ['EQ', 'UQ'];
        const prefix = address.substring(0, 2);
        
        if (!validPrefixes.includes(prefix)) {
            return { valid: false, error: 'Direccion invalida. Debe empezar con EQ o UQ' };
        }
        
        const base64Regex = /^[A-Za-z0-9_-]+$/;
        if (!base64Regex.test(address)) {
            return { valid: false, error: 'La direccion contiene caracteres invalidos' };
        }
        
        return { valid: true, error: null };
    },

    showBackupWalletModal() {
        const existingModal = document.getElementById('backup-wallet-modal');
        if (existingModal) existingModal.remove();
        
        const modalHtml = `
            <div id="backup-wallet-modal" class="modal-overlay" onclick="if(event.target === this) App.closeBackupWalletModal()">
                <div class="modal-content backup-wallet-modal">
                    <div class="modal-header">
                        <h3>Configurar Wallet de Respaldo</h3>
                        <button class="modal-close" onclick="App.closeBackupWalletModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="backup-wallet-info">
                            <div class="info-icon">🔐</div>
                            <p>Configura una wallet de respaldo para recuperar tu cuenta en caso de emergencia.</p>
                        </div>
                        
                        <div class="input-group">
                            <label>Direccion de Wallet TON</label>
                            <input type="text" id="backup-wallet-input" class="wallet-input" 
                                   placeholder="UQ... o EQ..." maxlength="48">
                            <span class="input-hint" id="backup-wallet-hint"></span>
                        </div>
                        
                        <div class="wallet-requirements">
                            <h4>Requisitos:</h4>
                            <ul>
                                <li>Debe empezar con UQ o EQ</li>
                                <li>Debe tener 48 caracteres</li>
                                <li>Debe ser diferente a tu wallet principal</li>
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="App.closeBackupWalletModal()">Cancelar</button>
                        <button class="btn btn-primary" id="save-backup-wallet-btn" onclick="App.saveBackupWallet()">Guardar</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const input = document.getElementById('backup-wallet-input');
        const hint = document.getElementById('backup-wallet-hint');
        
        input.addEventListener('input', () => {
            const validation = this.validateTonWalletAddress(input.value);
            if (input.value.length > 0) {
                hint.textContent = validation.valid ? '✓ Formato valido' : validation.error;
                hint.className = `input-hint ${validation.valid ? 'valid' : 'invalid'}`;
            } else {
                hint.textContent = '';
            }
        });
    },

    closeBackupWalletModal() {
        const modal = document.getElementById('backup-wallet-modal');
        if (modal) modal.remove();
    },

    async saveBackupWallet() {
        const input = document.getElementById('backup-wallet-input');
        const btn = document.getElementById('save-backup-wallet-btn');
        const address = input?.value?.trim();
        
        const validation = this.validateTonWalletAddress(address);
        if (!validation.valid) {
            this.showToast(validation.error, 'error');
            return;
        }
        
        btn.disabled = true;
        btn.textContent = 'Guardando...';
        
        try {
            const response = await this.apiRequest('/api/security/wallet/backup', {
                method: 'POST',
                body: JSON.stringify({ backupWallet: address })
            });
            
            if (response.success) {
                this.showToast('Wallet de respaldo registrada correctamente', 'success');
                this.closeBackupWalletModal();
            } else {
                this.showToast(response.error || 'Error al registrar wallet', 'error');
            }
        } catch (error) {
            this.showToast('Error al registrar wallet de respaldo', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Guardar';
        }
    },

    async setupBackupWallet() {
        this.showBackupWalletModal();
    },

    transactionOffset: 0,
    transactionLimit: 10,
    hasMoreTransactions: true,
    currentTransactionFilter: 'all',
    walletPollingInterval: null,
    _lastKnownBalance: 0,
    
    startWalletPolling() {
        if (this.walletPollingInterval) {
            clearInterval(this.walletPollingInterval);
        }
        this.walletPollingInterval = setInterval(() => {
            this.checkBalanceChange();
        }, 45000);
    },
    
    stopWalletPolling() {
        if (this.walletPollingInterval) {
            clearInterval(this.walletPollingInterval);
            this.walletPollingInterval = null;
        }
    },
    
    async checkBalanceChange() {
        try {
            const response = await this.apiRequest('/api/wallet/balance', { method: 'GET' });
            if (response.success) {
                const newBalance = response.balance;
                const oldBalance = this._lastKnownBalance;
                
                if (oldBalance !== 0 && newBalance !== oldBalance) {
                    const diff = newBalance - oldBalance;
                    this.onBalanceChanged(oldBalance, newBalance, diff);
                }
                
                this._lastKnownBalance = newBalance;
            }
        } catch (error) {
            console.error('Error checking balance:', error);
        }
    },
    
    onBalanceChanged(oldBalance, newBalance, diff) {
        const balanceEl = document.getElementById('wallet-balance');
        if (balanceEl) {
            this.animateBalanceChange(balanceEl, oldBalance, newBalance);
        }
        
        if (diff > 0) {
            this.showToast(`+${diff.toLocaleString()} BUNK3RCO1N recibidos!`, 'success');
            if (this.tg && this.tg.HapticFeedback) {
                this.tg.HapticFeedback.notificationOccurred('success');
            }
        } else {
            this.showToast(`${diff.toLocaleString()} BUNK3RCO1N gastados`, 'info');
        }
        
        const walletScreen = document.getElementById('wallet-screen');
        if (walletScreen && !walletScreen.classList.contains('hidden')) {
            this.loadTransactionHistory(0, false);
        }
    },
    
    refreshWallet() {
        const refreshBtn = document.querySelector('.wallet-refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('spinning');
        }
        
        Promise.all([
            this.loadWalletBalance(true),
            this.loadTransactionHistory(0, false)
        ]).finally(() => {
            if (refreshBtn) {
                setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
            }
        });
    },

    b3cPriceData: null,
    b3cPriceInterval: null,

    async loadB3CPrice() {
        try {
            const response = await this.apiRequest('/api/b3c/price');
            if (response.success) {
                this.b3cPriceData = response;
                this.updateB3CPriceUI(response);
                this.updateB3CEstimates(response);
            }
        } catch (error) {
            console.error('Error loading B3C price:', error);
        }
    },

    updateB3CPriceUI(priceData) {
        const priceTonEl = document.getElementById('b3c-price-ton');
        const priceUsdEl = document.getElementById('b3c-price-usd');
        const networkBadge = document.getElementById('b3c-network-badge');
        
        if (priceTonEl) {
            priceTonEl.textContent = `${priceData.price_ton.toFixed(6)} TON`;
        }
        if (priceUsdEl) {
            priceUsdEl.textContent = `~$${priceData.price_usd.toFixed(4)}`;
        }
        if (networkBadge) {
            networkBadge.textContent = priceData.is_testnet ? 'TESTNET' : 'MAINNET';
            networkBadge.classList.toggle('mainnet', !priceData.is_testnet);
        }
    },

    updateB3CEstimates(priceData) {
        const amounts = [0.5, 1, 5, 10, 20];
        amounts.forEach(ton => {
            const estId = ton === 0.5 ? 'b3c-est-05' : `b3c-est-${ton}`;
            const estEl = document.getElementById(estId);
            if (estEl && priceData.price_ton) {
                const b3c = (ton * 0.95) / priceData.price_ton;
                estEl.textContent = `~${Math.floor(b3c).toLocaleString()} B3C`;
            }
        });
    },

    preferredCurrency: 'usd',
    totalBalanceData: null,

    async refreshTotalBalance() {
        const refreshBtn = document.querySelector('.neo-refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('spinning');
        }
        
        try {
            await Promise.all([
                this.loadTotalBalance(),
                this.loadPersonalWalletAssets()
            ]);
        } finally {
            if (refreshBtn) {
                setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
            }
        }
    },

    async loadTotalBalance() {
        try {
            const savedCurrency = localStorage.getItem('preferredCurrency');
            if (savedCurrency && (savedCurrency === 'usd' || savedCurrency === 'eur')) {
                this.preferredCurrency = savedCurrency;
            }
            
            const response = await this.apiRequest(`/api/wallet/total-balance?currency=${this.preferredCurrency}`);
            if (response.success) {
                this.totalBalanceData = response;
                this.updateTotalBalanceUI(response);
            }
        } catch (error) {
            console.error('Error loading total balance:', error);
        }
    },

    updateTotalBalanceUI(data) {
        const totalEl = document.getElementById('wallet-total-balance');
        const symbolEl = document.getElementById('balance-currency-symbol');
        const labelEl = document.getElementById('balance-currency-label');
        const tokenCountEl = document.getElementById('balance-token-count');
        
        if (totalEl) {
            const total = data.total || 0;
            totalEl.textContent = total.toLocaleString('en-US', { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
            });
        }
        
        if (symbolEl) {
            symbolEl.textContent = data.currency === 'EUR' ? '\u20AC' : '$';
        }
        
        if (labelEl) {
            labelEl.textContent = data.currency || 'USD';
        }
        
        if (tokenCountEl && data.breakdown) {
            const activeTokens = data.breakdown.filter(t => t.value > 0).length;
            tokenCountEl.textContent = `${activeTokens} activo${activeTokens !== 1 ? 's' : ''} con valor`;
        }
    },

    toggleBalanceCurrency() {
        this.preferredCurrency = this.preferredCurrency === 'usd' ? 'eur' : 'usd';
        localStorage.setItem('preferredCurrency', this.preferredCurrency);
        
        if (this.totalBalanceData && this.totalBalanceData.prices) {
            const prices = this.totalBalanceData.prices;
            let newTotal = 0;
            const newBreakdown = [];
            
            if (this.totalBalanceData.breakdown) {
                this.totalBalanceData.breakdown.forEach(item => {
                    const symbol = item.symbol;
                    const balance = item.balance;
                    let price = 0;
                    
                    if (prices[symbol]) {
                        price = prices[symbol][this.preferredCurrency] || 0;
                    }
                    
                    const value = balance * price;
                    newTotal += value;
                    newBreakdown.push({ ...item, price, value });
                });
            }
            
            this.totalBalanceData.total = Math.round(newTotal * 100) / 100;
            this.totalBalanceData.currency = this.preferredCurrency.toUpperCase();
            this.totalBalanceData.breakdown = newBreakdown;
            
            this.updateTotalBalanceUI(this.totalBalanceData);
        } else {
            this.loadTotalBalance();
        }
    },

    async refreshB3CBalance() {
        const refreshBtn = document.querySelector('.wallet-refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('spinning');
        }
        
        try {
            await Promise.all([
                this.loadB3CBalance(),
                this.loadB3CPrice(),
                this.loadTransactionHistory(0, false)
            ]);
        } finally {
            if (refreshBtn) {
                setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
            }
        }
    },

    async loadB3CBalance() {
        try {
            const response = await this.apiRequest('/api/b3c/balance');
            if (response.success) {
                const balanceEl = document.getElementById('wallet-balance');
                const valueTonEl = document.getElementById('b3c-value-ton');
                const valueUsdEl = document.getElementById('b3c-value-usd');
                
                if (balanceEl) {
                    const balance = response.balance || 0;
                    balanceEl.textContent = balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                }
                if (valueTonEl) {
                    valueTonEl.textContent = `~${response.value_ton.toFixed(4)} TON`;
                }
                if (valueUsdEl) {
                    const usdValue = response.value_usd || 0;
                    valueUsdEl.textContent = `~$${usdValue.toFixed(2)} USD`;
                }
                
                this.state.update('wallet.balance', response.balance);
            }
        } catch (error) {
            console.error('Error loading B3C balance:', error);
        }
    },

    personalWalletAddress: null,

    async loadPersonalWalletAssets() {
        const loadingEl = document.getElementById('assets-loading');
        const contentEl = document.getElementById('assets-content');
        
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (contentEl) contentEl.classList.add('hidden');
        
        try {
            const response = await this.apiRequest('/api/wallet/assets');
            
            if (response.success) {
                this.personalWalletAddress = response.wallet?.address || null;
                
                const addressEl = document.getElementById('personal-wallet-address');
                if (addressEl && this.personalWalletAddress) {
                    const shortAddr = this.personalWalletAddress.slice(0, 8) + '...' + this.personalWalletAddress.slice(-6);
                    addressEl.textContent = shortAddr;
                    addressEl.dataset.fullAddress = this.personalWalletAddress;
                }
                
                this.updateMainTokensUI(response.main_tokens || []);
                this.updateOtherTokensUI(response.other_tokens || []);
            }
        } catch (error) {
            console.error('Error loading personal wallet assets:', error);
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
            if (contentEl) contentEl.classList.remove('hidden');
        }
    },

    updateMainTokensUI(tokens) {
        const tokenMap = {
            'B3C': 'asset-b3c-balance',
            'USDT': 'asset-usdt-balance',
            'TON': 'asset-ton-balance'
        };
        
        tokens.forEach(token => {
            const elId = tokenMap[token.symbol];
            if (elId) {
                const el = document.getElementById(elId);
                if (el) {
                    const balance = parseFloat(token.balance) || 0;
                    el.textContent = balance.toLocaleString('en-US', { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: token.symbol === 'B3C' ? 2 : 6 
                    });
                }
            }
        });
    },

    updateOtherTokensUI(tokens) {
        const section = document.getElementById('other-tokens-section');
        const list = document.getElementById('other-tokens-list');
        
        if (!section || !list) return;
        
        if (!tokens || tokens.length === 0) {
            section.classList.add('hidden');
            return;
        }
        
        section.classList.remove('hidden');
        list.innerHTML = '';
        
        tokens.forEach(token => {
            const item = document.createElement('div');
            item.className = 'neo-token-item';
            item.dataset.token = token.address;
            item.onclick = () => this.showTokenDetail(token.address);
            
            const balance = parseFloat(token.balance) || 0;
            
            item.innerHTML = `
                <div class="neo-token-left">
                    <div class="neo-token-icon">
                        ${token.icon ? `<img src="${token.icon}" alt="${token.symbol}" onerror="this.innerHTML='🪙'">` : '🪙'}
                    </div>
                    <div class="neo-token-info">
                        <span class="neo-token-symbol">${token.symbol}</span>
                        <span class="neo-token-name">${token.name || token.symbol}</span>
                    </div>
                </div>
                <div class="neo-token-right">
                    <span class="neo-token-balance">${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</span>
                    <svg class="neo-token-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </div>
            `;
            
            list.appendChild(item);
        });
    },

    async syncPersonalWallet() {
        const syncBtn = document.getElementById('sync-assets-btn');
        if (syncBtn) syncBtn.classList.add('syncing');
        
        try {
            const response = await this.apiRequest('/api/wallet/sync', { method: 'POST' });
            
            if (response.success) {
                this.showToast('Wallet sincronizada', 'success');
                await this.loadPersonalWalletAssets();
            } else {
                this.showToast(response.error || 'Error al sincronizar', 'error');
            }
        } catch (error) {
            console.error('Error syncing wallet:', error);
            this.showToast('Error al sincronizar wallet', 'error');
        } finally {
            if (syncBtn) {
                setTimeout(() => syncBtn.classList.remove('syncing'), 500);
            }
        }
    },

    copyPersonalWalletAddress() {
        const addressEl = document.getElementById('personal-wallet-address');
        const fullAddress = addressEl?.dataset?.fullAddress || this.personalWalletAddress;
        
        if (!fullAddress) {
            this.showToast('No hay direccion disponible', 'error');
            return;
        }
        
        navigator.clipboard.writeText(fullAddress).then(() => {
            this.showToast('Direccion copiada', 'success');
            if (this.tg?.HapticFeedback) {
                this.tg.HapticFeedback.notificationOccurred('success');
            }
        }).catch(() => {
            this.showToast('Error al copiar', 'error');
        });
    },

    async showTokenDetail(tokenSymbolOrAddress) {
        let tokenAddress = tokenSymbolOrAddress;
        
        const mainTokens = {
            'B3C': 'B3C',
            'USDT': 'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs',
            'TON': 'native'
        };
        
        if (mainTokens[tokenSymbolOrAddress]) {
            tokenAddress = mainTokens[tokenSymbolOrAddress];
        }
        
        this.showToast(`Cargando ${tokenSymbolOrAddress}...`, 'info');
    },

    selectedDepositToken: 'TON',
    depositQRInstance: null,

    async showPersonalDepositModal() {
        const modal = document.getElementById('deposit-qr-modal');
        if (!modal) return;
        
        modal.classList.remove('hidden');
        
        this.selectedDepositToken = 'TON';
        document.querySelectorAll('.deposit-token-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.token === 'TON');
        });
        document.getElementById('deposit-token-name').textContent = 'TON';
        
        const loadingEl = document.getElementById('deposit-qr-loading');
        const qrContainer = document.getElementById('deposit-qr-code');
        const addressText = document.getElementById('deposit-address-text');
        
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (qrContainer) qrContainer.innerHTML = '';
        
        try {
            let walletAddress = this.personalWalletAddress;
            
            if (!walletAddress) {
                const response = await this.apiRequest('/api/wallet/personal');
                if (response.success && response.wallet) {
                    walletAddress = response.wallet.address;
                    this.personalWalletAddress = walletAddress;
                }
            }
            
            if (walletAddress) {
                if (addressText) addressText.textContent = walletAddress;
                
                if (this.depositQRInstance) {
                    this.depositQRInstance.clear();
                    this.depositQRInstance = null;
                }
                
                if (typeof QRCode !== 'undefined') {
                    qrContainer.innerHTML = '';
                    this.depositQRInstance = new QRCode(qrContainer, {
                        text: walletAddress,
                        width: 180,
                        height: 180,
                        colorDark: '#000000',
                        colorLight: '#ffffff',
                        correctLevel: QRCode.CorrectLevel.M
                    });
                }
            } else {
                if (addressText) addressText.textContent = 'Error al cargar direccion';
            }
        } catch (error) {
            console.error('Error loading deposit address:', error);
            if (addressText) addressText.textContent = 'Error al cargar';
        } finally {
            if (loadingEl) loadingEl.classList.add('hidden');
        }
    },

    closeDepositQRModal() {
        const modal = document.getElementById('deposit-qr-modal');
        if (modal) modal.classList.add('hidden');
        
        if (this.depositQRInstance) {
            this.depositQRInstance.clear();
            this.depositQRInstance = null;
        }
    },

    selectDepositToken(token) {
        this.selectedDepositToken = token;
        
        document.querySelectorAll('.deposit-token-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.token === token);
        });
        
        const tokenNameEl = document.getElementById('deposit-token-name');
        if (tokenNameEl) {
            const tokenNames = { 'TON': 'TON', 'B3C': 'B3C', 'USDT': 'USDT (Jetton)' };
            tokenNameEl.textContent = tokenNames[token] || token;
        }
    },

    copyDepositAddress() {
        const addressEl = document.getElementById('deposit-address-text');
        const address = addressEl?.textContent || this.personalWalletAddress;
        
        if (!address || address === 'Cargando...' || address.includes('Error')) {
            this.showToast('No hay direccion disponible', 'error');
            return;
        }
        
        navigator.clipboard.writeText(address).then(() => {
            this.showToast('Direccion copiada', 'success');
            if (this.tg?.HapticFeedback) {
                this.tg.HapticFeedback.notificationOccurred('success');
            }
        }).catch(() => {
            const textArea = document.createElement('textarea');
            textArea.value = address;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showToast('Direccion copiada', 'success');
        });
    },

    async calculateB3CPreview() {
        const tonInput = document.getElementById('custom-ton-amount');
        const previewContainer = document.getElementById('b3c-preview');
        
        if (!tonInput || !previewContainer) return;
        
        const tonAmount = parseFloat(tonInput.value) || 0;
        
        if (tonAmount < 0.1) {
            previewContainer.classList.add('hidden');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/b3c/calculate/buy', {
                method: 'POST',
                body: JSON.stringify({ tonAmount })
            });
            
            if (response.success) {
                previewContainer.classList.remove('hidden');
                
                document.getElementById('b3c-preview-ton').textContent = `${response.ton_amount} TON`;
                document.getElementById('b3c-preview-commission').textContent = `${response.commission_ton.toFixed(4)} TON`;
                document.getElementById('b3c-preview-amount').textContent = `~${Math.floor(response.b3c_amount).toLocaleString()} B3C`;
            }
        } catch (error) {
            console.error('Error calculating B3C preview:', error);
        }
    },

    selectB3CAmount(tonAmount) {
        document.querySelectorAll('.b3c-option').forEach(opt => opt.classList.remove('selected'));
        const selectedOption = document.querySelector(`.b3c-option[data-ton="${tonAmount}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        const tonInput = document.getElementById('custom-ton-amount');
        if (tonInput) {
            tonInput.value = tonAmount;
        }
        
        this.calculateB3CPreview();
    },

    async buyB3CCustom() {
        const tonInput = document.getElementById('custom-ton-amount');
        const tonAmount = parseFloat(tonInput?.value) || 0;
        
        if (tonAmount < 0.1) {
            this.showToast('Minimo 0.1 TON', 'error');
            return;
        }
        
        await this.buyB3CWithTonConnect(tonAmount);
    },

    async buyB3CWithTonConnect(tonAmount) {
        this.sendLog('DEPOSIT_START', { tonAmount, walletConnected: !!this.connectedWallet });
        this.devLog('[B3C PURCHASE] Starting purchase for', tonAmount, 'TON');
        
        if (!this.tonConnectUI) {
            this.sendLog('DEPOSIT_ERROR', { error: 'TON Connect not initialized' }, 'error');
            console.error('[B3C PURCHASE] TON Connect UI not initialized');
            this.showToast('TON Connect no disponible. Recarga la pagina.', 'error');
            return;
        }

        if (!this.connectedWallet) {
            this.sendLog('WALLET_CONNECT_ATTEMPT', { reason: 'No wallet connected' });
            this.devLog('[B3C PURCHASE] Wallet not connected, attempting to connect...');
            this.showToast('Conectando wallet...', 'info');
            try {
                await this.tonConnectUI.openModal();
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error('Connection timeout'));
                    }, 60000);
                    
                    const unsubscribe = this.tonConnectUI.onStatusChange((wallet) => {
                        if (wallet) {
                            clearTimeout(timeout);
                            this.connectedWallet = wallet;
                            unsubscribe();
                            resolve(wallet);
                        }
                    });
                });
                
                if (!this.connectedWallet) {
                    this.sendLog('WALLET_CONNECT_FAILED', { error: 'Wallet null after connect' }, 'error');
                    this.showToast('Wallet no conectada', 'error');
                    return;
                }
                this.sendLog('WALLET_CONNECT_SUCCESS', { address: this.connectedWallet?.account?.address?.substring(0, 20) });
                this.devLog('[B3C PURCHASE] Wallet connected successfully');
            } catch (e) {
                this.sendLog('WALLET_CONNECT_ERROR', { error: e.message }, 'error');
                console.error('[B3C PURCHASE] Wallet connection failed:', e);
                if (e.message?.includes('timeout')) {
                    this.showToast('Tiempo agotado. Intenta de nuevo.', 'error');
                } else {
                    this.showToast('Error al conectar wallet', 'error');
                }
                return;
            }
        }

        try {
            this.showToast(`Preparando compra de B3C por ${tonAmount} TON...`, 'info');
            this.sendLog('DEPOSIT_CREATE_ORDER', { tonAmount });
            this.devLog('[B3C PURCHASE] Creating purchase order...');

            const response = await this.apiRequest('/api/b3c/buy/create', {
                method: 'POST',
                body: JSON.stringify({ tonAmount })
            });

            this.devLog('[B3C PURCHASE] Create response:', JSON.stringify(response));

            if (!response.success) {
                this.showToast(response.error || 'Error al crear compra', 'error');
                return;
            }

            const depositAddress = response.depositAddress || response.hotWallet;
            if (!depositAddress) {
                console.error('[B3C PURCHASE] Missing deposit address in response:', response);
                this.showToast('Error: Direccion de deposito no disponible', 'error');
                return;
            }

            const purchaseId = response.purchaseId;
            const amountToSend = response.amountToSend || tonAmount;
            const amountNano = Math.floor(amountToSend * 1e9).toString();

            this.devLog('[B3C PURCHASE] Transaction details:', {
                address: depositAddress,
                amount: amountNano,
                purchaseId: purchaseId,
                useUniqueWallet: response.useUniqueWallet,
                expiresInMinutes: response.expiresInMinutes
            });

            if (response.useUniqueWallet) {
                this.showToast(`Direccion unica asignada. Tienes ${response.expiresInMinutes} min para pagar.`, 'info');
            }

            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + (response.expiresInMinutes || 15) * 60,
                messages: [
                    {
                        address: depositAddress,
                        amount: amountNano
                    }
                ]
            };

            this.showToast('Abriendo wallet para confirmar...', 'info');
            this.devLog('[B3C PURCHASE] Sending transaction...');

            try {
                const sendPromise = this.tonConnectUI.sendTransaction(transaction);
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('WALLET_TIMEOUT')), 10000)
                );
                
                const result = await Promise.race([sendPromise, timeoutPromise]);
                this.devLog('[B3C PURCHASE] Transaction result:', result);

                if (result && result.boc) {
                    this.showToast('Transaccion enviada! Verificando...', 'success');
                    await this.verifyB3CPurchaseAfterTx(purchaseId, result.boc);
                } else {
                    console.warn('[B3C PURCHASE] No BOC in result');
                    this.showManualDepositModal(depositAddress, tonAmount, purchaseId, response.expiresInMinutes || 30);
                }
            } catch (walletError) {
                console.error('[B3C PURCHASE] Wallet error:', walletError);
                if (walletError.message === 'WALLET_TIMEOUT' || walletError.message?.includes('timeout')) {
                    this.devLog('[B3C PURCHASE] Wallet timeout, showing manual deposit option');
                    this.showManualDepositModal(depositAddress, tonAmount, purchaseId, response.expiresInMinutes || 30);
                } else if (walletError.message?.includes('Canceled') || walletError.message?.includes('cancel') || walletError.message?.includes('rejected')) {
                    this.showToast('Compra cancelada', 'info');
                } else if (walletError.message?.includes('User rejects') || walletError.message?.includes('user rejected')) {
                    this.showToast('Transaccion rechazada', 'info');
                } else {
                    this.showManualDepositModal(depositAddress, tonAmount, purchaseId, response.expiresInMinutes || 30);
                }
            }
        } catch (error) {
            console.error('[B3C PURCHASE] Error:', error);
            this.showToast('Error: ' + (error.message?.substring(0, 50) || 'Intenta de nuevo'), 'error');
        }
    },
    
    showManualDepositModal(address, amount, purchaseId, expiresMinutes) {
        const existingModal = document.getElementById('manual-deposit-modal');
        if (existingModal) existingModal.remove();
        
        const modal = document.createElement('div');
        modal.id = 'manual-deposit-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px; background: var(--card-bg, #1a1a2e); border-radius: 16px; padding: 24px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 48px; margin-bottom: 10px;">💳</div>
                    <h3 style="color: #fff; margin: 0 0 8px 0;">Deposito Manual</h3>
                    <p style="color: #888; font-size: 14px; margin: 0;">La wallet no respondio. Envia manualmente:</p>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                    <div style="color: #888; font-size: 12px; margin-bottom: 4px;">Cantidad:</div>
                    <div style="color: #ffd700; font-size: 24px; font-weight: bold;">${amount} TON</div>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                    <div style="color: #888; font-size: 12px; margin-bottom: 8px;">Direccion de deposito:</div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <code style="flex: 1; color: #4ecdc4; font-size: 11px; word-break: break-all; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px;">${address}</code>
                        <button onclick="navigator.clipboard.writeText('${address}'); App.showToast('Copiado!', 'success');" 
                                style="background: #4ecdc4; color: #000; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            Copiar
                        </button>
                    </div>
                </div>
                
                <div style="background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.3); border-radius: 12px; padding: 12px; margin-bottom: 16px;">
                    <div style="color: #ffc107; font-size: 13px;">
                        <strong>Importante:</strong> Tienes ${expiresMinutes} minutos para enviar exactamente ${amount} TON a esta direccion.
                        El sistema detectara tu pago automaticamente.
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px;">
                    <button onclick="App.openTonLink('${address}', ${amount});" 
                            style="flex: 1; background: #0088cc; color: #fff; border: none; padding: 14px; border-radius: 12px; cursor: pointer; font-weight: bold; font-size: 14px;">
                        Abrir Wallet
                    </button>
                    <button onclick="document.getElementById('manual-deposit-modal').remove();" 
                            style="flex: 1; background: rgba(255,255,255,0.1); color: #fff; border: none; padding: 14px; border-radius: 12px; cursor: pointer; font-size: 14px;">
                        Cerrar
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    },
    
    openTonLink(address, amount) {
        const amountNano = Math.floor(amount * 1e9);
        const tonLink = `ton://transfer/${address}?amount=${amountNano}`;
        this.devLog('[TON LINK] Opening:', tonLink);
        
        if (window.Telegram?.WebApp?.openLink) {
            window.Telegram.WebApp.openLink(tonLink);
        } else {
            window.open(tonLink, '_blank');
        }
    },

    buildTextCommentPayload(comment) {
        return undefined;
    },

    async verifyB3CPurchaseAfterTx(purchaseId, boc) {
        let attempts = 0;
        const maxAttempts = 10;
        const delay = 3000;

        const checkPayment = async () => {
            attempts++;
            try {
                const response = await this.apiRequest(`/api/b3c/buy/${purchaseId}/verify`, {
                    method: 'POST',
                    body: JSON.stringify({ boc })
                });

                if (response.success && response.status === 'confirmed') {
                    this.showToast(`+${response.b3c_credited.toLocaleString()} B3C recibidos!`, 'success');
                    this.showRechargeSuccess(response.b3c_credited);
                    this.refreshB3CBalance();
                    return true;
                } else if (attempts < maxAttempts) {
                    this.showToast(`Verificando pago... (${attempts}/${maxAttempts})`, 'info');
                    setTimeout(checkPayment, delay);
                } else {
                    this.showToast('Pago enviado. La verificacion puede tardar unos minutos.', 'info');
                }
            } catch (error) {
                console.error('Verification error:', error);
                if (attempts < maxAttempts) {
                    setTimeout(checkPayment, delay);
                }
            }
        };

        setTimeout(checkPayment, delay);
    },

    showB3CPaymentModal(purchaseData) {
        const modal = document.createElement('div');
        modal.className = 'b3c-payment-modal modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirmar Compra B3C</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="b3c-purchase-summary">
                        <div class="summary-row">
                            <span>Pagas:</span>
                            <span class="summary-value">${purchaseData.calculation.ton_amount} TON</span>
                        </div>
                        <div class="summary-row">
                            <span>Comision (5%):</span>
                            <span class="summary-value">${purchaseData.calculation.commission_ton.toFixed(4)} TON</span>
                        </div>
                        <div class="summary-row highlight">
                            <span>Recibiras:</span>
                            <span class="summary-value success">~${Math.floor(purchaseData.calculation.b3c_amount).toLocaleString()} B3C</span>
                        </div>
                    </div>
                    <div class="b3c-payment-info">
                        <p class="payment-instruction">Envia exactamente <strong>${purchaseData.amountToSend || purchaseData.calculation.ton_amount} TON</strong> a:</p>
                        <div class="payment-address">
                            <code>${purchaseData.depositAddress || purchaseData.hotWallet}</code>
                            <button class="copy-btn" onclick="navigator.clipboard.writeText('${purchaseData.depositAddress || purchaseData.hotWallet}'); App.showToast('Copiado!', 'success')">Copiar</button>
                        </div>
                        ${purchaseData.useUniqueWallet ? 
                            `<p class="payment-unique-notice">Esta direccion es UNICA para esta compra. Tienes <strong>${purchaseData.expiresInMinutes} minutos</strong>.</p>` : 
                            `<p class="payment-memo">Memo/Comentario: <strong>${purchaseData.comment}</strong></p>`
                        }
                    </div>
                    <div class="b3c-purchase-status" id="purchase-status-${purchaseData.purchaseId}">
                        <div class="status-waiting">Esperando pago...</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-verify" onclick="App.verifyB3CPurchase('${purchaseData.purchaseId}')">Verificar Pago</button>
                    <button class="btn-cancel" onclick="this.closest('.modal-overlay').remove()">Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    },

    async verifyB3CPurchase(purchaseId) {
        const statusEl = document.getElementById(`purchase-status-${purchaseId}`);
        if (statusEl) {
            statusEl.innerHTML = '<div class="status-checking">Verificando en blockchain...</div>';
        }
        
        try {
            const response = await this.apiRequest(`/api/b3c/buy/${purchaseId}/verify`, {
                method: 'POST'
            });
            
            if (response.success) {
                if (response.status === 'confirmed') {
                    if (statusEl) {
                        statusEl.innerHTML = `<div class="status-success">Pago confirmado! +${response.b3c_credited.toLocaleString()} B3C</div>`;
                    }
                    this.showToast(`+${response.b3c_credited.toLocaleString()} B3C recibidos!`, 'success');
                    this.showRechargeSuccess(response.b3c_credited);
                    
                    setTimeout(() => {
                        document.querySelector('.b3c-payment-modal')?.remove();
                        this.refreshB3CBalance();
                    }, 2000);
                } else {
                    if (statusEl) {
                        statusEl.innerHTML = '<div class="status-waiting">Pago no detectado. Intenta de nuevo en unos segundos.</div>';
                    }
                }
            } else {
                if (statusEl) {
                    statusEl.innerHTML = `<div class="status-error">${response.error || 'Error al verificar'}</div>`;
                }
            }
        } catch (error) {
            console.error('Error verifying B3C purchase:', error);
            if (statusEl) {
                statusEl.innerHTML = '<div class="status-error">Error de conexion</div>';
            }
        }
    },

    showB3CBuyModal() {
        const tonInput = document.getElementById('custom-ton-amount');
        if (tonInput && tonInput.value) {
            this.buyB3CCustom();
        } else {
            this.showToast('Selecciona una cantidad de TON primero', 'info');
            tonInput?.focus();
        }
    },

    showB3CSellModal() {
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-sell-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Vender B3C</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-sell-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="b3c-sell-info">
                        <p>Vende tus B3C y recibe TON en tu wallet.</p>
                        <div class="b3c-current-price">
                            <span>Precio actual:</span>
                            <strong id="sell-price-display">${this.b3cPriceData ? this.b3cPriceData.price_ton.toFixed(6) : '0.001'} TON</strong>
                        </div>
                    </div>
                    
                    <div class="b3c-input-group">
                        <label>Cantidad de B3C a vender</label>
                        <input type="number" id="sell-b3c-amount" placeholder="Minimo 100 B3C" min="100" step="100" oninput="App.calculateSellPreview()">
                    </div>
                    
                    <div class="b3c-input-group">
                        <label>Tu wallet TON (donde recibiras)</label>
                        <input type="text" id="sell-destination-wallet" placeholder="UQ... o EQ..." value="${this._savedWalletAddress || ''}">
                    </div>
                    
                    <div class="b3c-preview" id="sell-preview" style="display:none;">
                        <div class="b3c-preview-row">
                            <span>B3C a vender:</span>
                            <span id="sell-preview-b3c">0 B3C</span>
                        </div>
                        <div class="b3c-preview-row">
                            <span>TON bruto:</span>
                            <span id="sell-preview-gross">0 TON</span>
                        </div>
                        <div class="b3c-preview-row">
                            <span>Comision (5%):</span>
                            <span id="sell-preview-commission">0 TON</span>
                        </div>
                        <div class="b3c-preview-row b3c-preview-total">
                            <span>Recibiras:</span>
                            <span id="sell-preview-net">0 TON</span>
                        </div>
                    </div>
                    
                    <div class="b3c-modal-actions">
                        <button class="btn-secondary" onclick="App.closeB3CModal('b3c-sell-modal')">Cancelar</button>
                        <button class="btn-primary" id="confirm-sell-btn" onclick="App.confirmSellB3C()">Confirmar Venta</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-sell-modal');
        });
    },

    async calculateSellPreview() {
        const amountInput = document.getElementById('sell-b3c-amount');
        const preview = document.getElementById('sell-preview');
        const amount = parseFloat(amountInput?.value) || 0;
        
        if (amount < 100) {
            if (preview) preview.style.display = 'none';
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/b3c/calculate/sell', {
                method: 'POST',
                body: JSON.stringify({ b3cAmount: amount })
            });
            
            if (response.success) {
                document.getElementById('sell-preview-b3c').textContent = `${amount.toLocaleString()} B3C`;
                document.getElementById('sell-preview-gross').textContent = `${response.gross_ton.toFixed(4)} TON`;
                document.getElementById('sell-preview-commission').textContent = `${response.commission_ton.toFixed(4)} TON`;
                document.getElementById('sell-preview-net').textContent = `${response.net_ton.toFixed(4)} TON`;
                preview.style.display = 'block';
            }
        } catch (error) {
            console.error('Error calculating sell:', error);
        }
    },

    async confirmSellB3C() {
        const amount = parseFloat(document.getElementById('sell-b3c-amount')?.value) || 0;
        const wallet = document.getElementById('sell-destination-wallet')?.value?.trim();
        
        if (amount < 100) {
            this.showToast('Minimo 100 B3C para vender', 'error');
            return;
        }
        
        if (!wallet || wallet.length < 40) {
            this.showToast('Ingresa una direccion de wallet valida', 'error');
            return;
        }
        
        const btn = document.getElementById('confirm-sell-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Procesando...';
        }
        
        try {
            const response = await this.apiRequest('/api/b3c/sell', {
                method: 'POST',
                body: JSON.stringify({ 
                    b3cAmount: amount,
                    destinationWallet: wallet
                })
            });
            
            if (response.success) {
                this.closeB3CModal('b3c-sell-modal');
                this.showToast(`Venta exitosa! Recibiras ${response.tonReceived.toFixed(4)} TON`, 'success');
                this.refreshB3CBalance();
            } else {
                this.showToast(response.error || 'Error al procesar venta', 'error');
            }
        } catch (error) {
            console.error('Error selling B3C:', error);
            this.showToast('Error de conexion', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Confirmar Venta';
            }
        }
    },

    _withdrawAssets: {
        'B3C': { symbol: 'B3C', name: 'BUNK3RCO1N', min: 100, max: 100000, fee: '~0.05 TON', decimals: 2 },
        'TON': { symbol: 'TON', name: 'Toncoin', min: 0.5, max: 10000, fee: '~0.01 TON', decimals: 4 },
        'USDT': { symbol: 'USDT', name: 'Tether USD', min: 1, max: 50000, fee: '~0.1 TON', decimals: 2 }
    },
    _selectedWithdrawAsset: 'B3C',

    showB3CWithdrawModal() {
        const assets = this._withdrawAssets;
        const selectedAsset = assets[this._selectedWithdrawAsset];
        
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-withdraw-modal';
        modal.innerHTML = `
            <div class="modal-content withdraw-modal-content">
                <div class="withdraw-modal-header">
                    <h3>Retirar Activos</h3>
                    <button class="modal-close-btn" onclick="App.closeB3CModal('b3c-withdraw-modal')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="withdraw-modal-body">
                    <p class="withdraw-description">Retira tus activos a tu wallet personal en la red TON.</p>
                    
                    <div class="withdraw-asset-section">
                        <label class="withdraw-label">Seleccionar activo</label>
                        <div class="withdraw-asset-selector" id="withdraw-asset-selector">
                            ${Object.keys(assets).map(key => `
                                <button class="withdraw-asset-option ${key === this._selectedWithdrawAsset ? 'active' : ''}" 
                                        data-asset="${key}" onclick="App.selectWithdrawAsset('${key}')">
                                    <span class="withdraw-asset-symbol">${key}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="withdraw-balance-display" id="withdraw-balance-display">
                        <span class="withdraw-balance-label">Disponible:</span>
                        <span class="withdraw-balance-value" id="withdraw-available-balance">-- ${this._selectedWithdrawAsset}</span>
                    </div>
                    
                    <div class="withdraw-limits-bar">
                        <span class="withdraw-limit">Min: ${selectedAsset.min} ${selectedAsset.symbol}</span>
                        <span class="withdraw-limit">Max: ${selectedAsset.max.toLocaleString()} ${selectedAsset.symbol}/dia</span>
                    </div>
                    
                    <div class="withdraw-input-group">
                        <label class="withdraw-label">Cantidad a retirar</label>
                        <div class="withdraw-input-wrapper">
                            <input type="number" id="withdraw-amount" class="withdraw-input" 
                                   placeholder="0.00" min="${selectedAsset.min}" max="${selectedAsset.max}" 
                                   step="0.01" oninput="App.updateWithdrawPreview()">
                            <button class="withdraw-max-btn" onclick="App.setMaxWithdraw()">MAX</button>
                        </div>
                    </div>
                    
                    <div class="withdraw-input-group">
                        <label class="withdraw-label">Wallet destino (TON)</label>
                        <input type="text" id="withdraw-destination-wallet" class="withdraw-input wallet-input" 
                               placeholder="UQ... o EQ..." value="${this._savedWalletAddress || ''}">
                    </div>
                    
                    <div class="withdraw-fee-info">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                        <span id="withdraw-fee-text">Fee de red: ${selectedAsset.fee}</span>
                    </div>
                    
                    <div class="withdraw-actions">
                        <button class="withdraw-cancel-btn" onclick="App.closeB3CModal('b3c-withdraw-modal')">Cancelar</button>
                        <button class="withdraw-confirm-btn" id="confirm-withdraw-btn" onclick="App.confirmWithdrawB3C()">
                            <span>Retirar</span>
                            <span id="withdraw-btn-asset">${this._selectedWithdrawAsset}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-withdraw-modal');
        });
        
        this.updateWithdrawBalance();
    },

    selectWithdrawAsset(assetKey) {
        this._selectedWithdrawAsset = assetKey;
        const asset = this._withdrawAssets[assetKey];
        
        document.querySelectorAll('.withdraw-asset-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.asset === assetKey);
        });
        
        const amountInput = document.getElementById('withdraw-amount');
        if (amountInput) {
            amountInput.min = asset.min;
            amountInput.max = asset.max;
            amountInput.value = '';
        }
        
        const limitsBar = document.querySelector('.withdraw-limits-bar');
        if (limitsBar) {
            limitsBar.innerHTML = `
                <span class="withdraw-limit">Min: ${asset.min} ${asset.symbol}</span>
                <span class="withdraw-limit">Max: ${asset.max.toLocaleString()} ${asset.symbol}/dia</span>
            `;
        }
        
        const feeText = document.getElementById('withdraw-fee-text');
        if (feeText) {
            feeText.textContent = `Fee de red: ${asset.fee}`;
        }
        
        const btnAsset = document.getElementById('withdraw-btn-asset');
        if (btnAsset) {
            btnAsset.textContent = assetKey;
        }
        
        this.updateWithdrawBalance();
    },

    async updateWithdrawBalance() {
        const balanceEl = document.getElementById('withdraw-available-balance');
        if (!balanceEl) return;
        
        const asset = this._selectedWithdrawAsset;
        balanceEl.textContent = `Cargando...`;
        
        try {
            if (asset === 'B3C') {
                const walletBalanceEl = document.getElementById('wallet-balance');
                if (walletBalanceEl) {
                    const balance = parseFloat(walletBalanceEl.textContent.replace(/,/g, '')) || 0;
                    balanceEl.textContent = `${balance.toLocaleString()} B3C`;
                } else {
                    balanceEl.textContent = `-- B3C`;
                }
            } else {
                const response = await this.apiRequest('/api/wallet/personal/assets');
                if (response.success && response.main_tokens) {
                    const token = response.main_tokens.find(t => t.symbol === asset);
                    if (token) {
                        balanceEl.textContent = `${token.balance.toLocaleString(undefined, {maximumFractionDigits: 4})} ${asset}`;
                    } else {
                        balanceEl.textContent = `0 ${asset}`;
                    }
                } else {
                    balanceEl.textContent = `-- ${asset}`;
                }
            }
        } catch (error) {
            balanceEl.textContent = `-- ${asset}`;
        }
    },

    setMaxWithdraw() {
        const asset = this._selectedWithdrawAsset;
        const assetConfig = this._withdrawAssets[asset];
        
        if (asset === 'B3C') {
            const balanceEl = document.getElementById('wallet-balance');
            if (balanceEl) {
                const balance = parseFloat(balanceEl.textContent.replace(/,/g, '')) || 0;
                const max = Math.min(balance, assetConfig.max);
                document.getElementById('withdraw-amount').value = max;
            }
        } else {
            const balanceText = document.getElementById('withdraw-available-balance')?.textContent || '';
            const balance = parseFloat(balanceText.replace(/,/g, '').replace(asset, '').trim()) || 0;
            const max = Math.min(balance, assetConfig.max);
            document.getElementById('withdraw-amount').value = max;
        }
        
        this.updateWithdrawPreview();
    },

    updateWithdrawPreview() {
    },

    async confirmWithdrawB3C() {
        const asset = this._selectedWithdrawAsset;
        const assetConfig = this._withdrawAssets[asset];
        const amount = parseFloat(document.getElementById('withdraw-amount')?.value) || 0;
        const wallet = document.getElementById('withdraw-destination-wallet')?.value?.trim();
        
        if (amount < assetConfig.min) {
            this.showToast(`Minimo ${assetConfig.min} ${asset} para retirar`, 'error');
            return;
        }
        
        if (amount > assetConfig.max) {
            this.showToast(`Maximo ${assetConfig.max.toLocaleString()} ${asset} por retiro`, 'error');
            return;
        }
        
        if (!wallet || wallet.length < 40) {
            this.showToast('Ingresa una direccion de wallet valida', 'error');
            return;
        }
        
        const btn = document.getElementById('confirm-withdraw-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span>Procesando...</span>';
        }
        
        try {
            let endpoint = '/api/b3c/withdraw';
            let body = { b3cAmount: amount, destinationWallet: wallet };
            
            if (asset === 'TON') {
                endpoint = '/api/wallet/withdraw/ton';
                body = { amount: amount, destinationWallet: wallet };
            } else if (asset === 'USDT') {
                endpoint = '/api/wallet/withdraw/usdt';
                body = { amount: amount, destinationWallet: wallet };
            }
            
            const response = await this.apiRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify(body)
            });
            
            if (response.success) {
                this.closeB3CModal('b3c-withdraw-modal');
                this.showToast(`Retiro iniciado: ${amount.toLocaleString()} ${asset}`, 'success');
                this.refreshB3CBalance();
                this._savedWalletAddress = wallet;
            } else {
                this.showToast(response.error || 'Error al procesar retiro', 'error');
            }
        } catch (error) {
            console.error('Error withdrawing:', error);
            this.showToast('Error de conexion', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<span>Retirar</span><span>${asset}</span>`;
            }
        }
    },

    closeB3CModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.remove();
    },

    showTransferModal() {
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-transfer-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Transferir B3C</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-transfer-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="b3c-transfer-info">
                        <p>Envia B3C a otro usuario de BUNK3R</p>
                        <div class="b3c-limits">
                            <span>Minimo: 1 B3C</span>
                            <span>Sin comision</span>
                        </div>
                    </div>
                    
                    <div class="b3c-input-group">
                        <label>Usuario destino (@username)</label>
                        <input type="text" id="transfer-recipient" placeholder="@usuario" autocomplete="off">
                        <div id="user-search-results" class="user-search-results hidden"></div>
                    </div>
                    
                    <div class="b3c-input-group">
                        <label>Cantidad de B3C</label>
                        <input type="number" id="transfer-b3c-amount" placeholder="Cantidad" min="1" step="1">
                        <button class="btn-max" onclick="App.setMaxTransfer()">MAX</button>
                    </div>
                    
                    <div class="b3c-input-group">
                        <label>Nota (opcional)</label>
                        <input type="text" id="transfer-note" placeholder="Ej: Para el cafe" maxlength="100">
                    </div>
                    
                    <div class="b3c-modal-actions">
                        <button class="btn-secondary" onclick="App.closeB3CModal('b3c-transfer-modal')">Cancelar</button>
                        <button class="btn-primary" id="confirm-transfer-btn" onclick="App.confirmTransferB3C()">Enviar B3C</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-transfer-modal');
        });
        
        const recipientInput = document.getElementById('transfer-recipient');
        if (recipientInput) {
            let searchTimeout;
            recipientInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => this.searchUsersForTransfer(query), 300);
                } else {
                    document.getElementById('user-search-results').classList.add('hidden');
                }
            });
        }
    },

    async searchUsersForTransfer(query) {
        try {
            const response = await this.apiRequest(`/api/search/users?q=${encodeURIComponent(query)}`);
            if (response.success && response.users.length > 0) {
                const resultsDiv = document.getElementById('user-search-results');
                SafeDOM.setTrustedHTML(resultsDiv, response.users.map(u => `
                    <div class="user-result-item" onclick="App.selectTransferRecipient('${this.sanitizeForJs(u.username || u.id)}', '${this.sanitizeForJs(u.name || u.username)}')">
                        <img src="${this.escapeAttribute(u.avatar || '/static/images/default-avatar.png')}" class="user-result-avatar">
                        <div class="user-result-info">
                            <span class="user-result-name">${this.escapeHtml(u.name || 'Usuario')}</span>
                            <span class="user-result-username">@${this.escapeHtml(u.username || u.id)}</span>
                        </div>
                    </div>
                `).join(''));
                resultsDiv.classList.remove('hidden');
            } else {
                document.getElementById('user-search-results').classList.add('hidden');
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    },

    selectTransferRecipient(username, displayName) {
        document.getElementById('transfer-recipient').value = '@' + username;
        document.getElementById('user-search-results').classList.add('hidden');
        this._selectedRecipient = { username, displayName };
    },

    setMaxTransfer() {
        const balanceEl = document.getElementById('wallet-balance');
        if (balanceEl) {
            const balance = parseFloat(balanceEl.textContent.replace(/,/g, '')) || 0;
            document.getElementById('transfer-b3c-amount').value = Math.floor(balance);
        }
    },

    async confirmTransferB3C() {
        const recipientInput = document.getElementById('transfer-recipient')?.value?.trim();
        const amount = parseFloat(document.getElementById('transfer-b3c-amount')?.value) || 0;
        const note = document.getElementById('transfer-note')?.value?.trim() || '';
        
        if (!recipientInput || recipientInput.length < 2) {
            this.showToast('Ingresa el usuario destino', 'error');
            return;
        }
        
        if (amount < 1) {
            this.showToast('Minimo 1 B3C para transferir', 'error');
            return;
        }
        
        const btn = document.getElementById('confirm-transfer-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Enviando...';
        }
        
        try {
            const response = await this.apiRequest('/api/b3c/transfer', {
                method: 'POST',
                body: JSON.stringify({ 
                    toUsername: recipientInput.replace('@', ''),
                    amount: amount,
                    note: note
                })
            });
            
            if (response.success) {
                this.closeB3CModal('b3c-transfer-modal');
                this.showToast(response.message || `Enviado ${amount} B3C correctamente`, 'success');
                this.refreshB3CBalance();
            } else {
                this.showToast(response.error || 'Error al transferir', 'error');
            }
        } catch (error) {
            console.error('Error transferring B3C:', error);
            this.showToast('Error de conexion', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Enviar B3C';
            }
        }
    },

    getSyncedWallets() {
        try {
            const wallets = localStorage.getItem('syncedWallets');
            return wallets ? JSON.parse(wallets) : {};
        } catch (e) {
            return {};
        }
    },
    
    saveSyncedWallet(type, address) {
        try {
            const wallets = this.getSyncedWallets();
            wallets[type] = {
                address: address,
                syncedAt: new Date().toISOString()
            };
            localStorage.setItem('syncedWallets', JSON.stringify(wallets));
        } catch (e) {
            console.error('Error saving wallet:', e);
        }
    },
    
    removeSyncedWallet(type) {
        try {
            const wallets = this.getSyncedWallets();
            delete wallets[type];
            localStorage.setItem('syncedWallets', JSON.stringify(wallets));
        } catch (e) {
            console.error('Error removing wallet:', e);
        }
    },
    
    formatWalletAddress(address) {
        if (!address || address.length < 12) return address;
        return address.substring(0, 6) + '...' + address.substring(address.length - 4);
    },

    countSyncedWallets() {
        const wallets = this.getSyncedWallets();
        let count = 0;
        if (wallets.telegram) count++;
        if (wallets.binance) count++;
        return count;
    },
    
    getPrimaryWallet() {
        const wallets = this.getSyncedWallets();
        if (wallets.telegram) return { type: 'telegram', data: wallets.telegram };
        if (wallets.binance) return { type: 'binance', data: wallets.binance };
        return null;
    },
    
    getSecondaryWallet() {
        const wallets = this.getSyncedWallets();
        const types = [];
        if (wallets.telegram) types.push({ type: 'telegram', data: wallets.telegram });
        if (wallets.binance) types.push({ type: 'binance', data: wallets.binance });
        return types.length > 1 ? types[1] : null;
    },
    
    getAvailableWalletToSync() {
        const wallets = this.getSyncedWallets();
        if (!wallets.telegram) return 'telegram';
        if (!wallets.binance) return 'binance';
        return null;
    },

    showB3CDepositModal() {
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-deposit-options-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Depositar B3C</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-deposit-options-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="neo-deposit-intro">
                        <p class="neo-deposit-text">Selecciona como deseas recargar tu balance:</p>
                    </div>
                    
                    <div class="neo-deposit-options">
                        <div class="neo-deposit-option" onclick="App.showRechargePackages()">
                            <div class="neo-deposit-option-icon recharge">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                                </svg>
                            </div>
                            <div class="neo-deposit-option-info">
                                <span class="neo-deposit-option-title">Comprar B3C con TON</span>
                                <span class="neo-deposit-option-desc">Paquetes de recarga rapida</span>
                            </div>
                            <svg class="neo-deposit-option-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </div>
                        
                        <div class="neo-deposit-option" onclick="App.closeB3CModal('b3c-deposit-options-modal'); App.showPersonalDepositModal()">
                            <div class="neo-deposit-option-icon wallet">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="2" y="5" width="20" height="14" rx="2"/>
                                    <path d="M2 10h20"/>
                                </svg>
                            </div>
                            <div class="neo-deposit-option-info">
                                <span class="neo-deposit-option-title">Depositar a Mi Wallet</span>
                                <span class="neo-deposit-option-desc">Envia TON/USDT/B3C a tu direccion personal</span>
                            </div>
                            <svg class="neo-deposit-option-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-deposit-options-modal');
        });
    },
    
    showRechargePackages() {
        this.closeB3CModal('b3c-deposit-options-modal');
        
        const syncedWallets = this.getSyncedWallets();
        const hasSyncedWallet = syncedWallets.telegram || syncedWallets.binance;
        
        if (hasSyncedWallet) {
            const primaryType = syncedWallets.telegram ? 'telegram' : 'binance';
            this.showDepositPackages(primaryType);
        } else {
            this.showWalletSyncModal();
        }
    },
    
    showWalletSyncModal() {
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-sync-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Vincular Wallet</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-sync-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="neo-sync-intro">
                        <div class="neo-sync-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="1.5">
                                <rect x="2" y="6" width="20" height="12" rx="2"/>
                                <path d="M22 10H2M7 15h4"/>
                            </svg>
                        </div>
                        <p class="neo-sync-text">Para depositar B3C necesitas vincular una wallet. Selecciona tu wallet preferida:</p>
                    </div>
                    <div class="neo-wallets-section">
                        <div class="neo-wallet-options">
                            <div class="neo-wallet-item" onclick="App.syncWalletAndDeposit('telegram')">
                                <div class="neo-wallet-icon telegram">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.828.94z"/>
                                    </svg>
                                </div>
                                <div class="neo-wallet-info">
                                    <span class="neo-wallet-name">Telegram Wallet</span>
                                    <span class="neo-wallet-desc">Wallet nativa de Telegram</span>
                                </div>
                                <svg class="neo-wallet-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 18l6-6-6-6"/>
                                </svg>
                            </div>
                            <div class="neo-wallet-item" onclick="App.syncWalletAndDeposit('binance')">
                                <div class="neo-wallet-icon binance">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 0L7.172 4.828l1.768 1.768L12 3.536l3.06 3.06 1.768-1.768L12 0zM4.828 7.172L0 12l4.828 4.828 1.768-1.768L3.536 12l3.06-3.06-1.768-1.768zM19.172 7.172l-1.768 1.768L20.464 12l-3.06 3.06 1.768 1.768L24 12l-4.828-4.828zM12 8.464L8.464 12 12 15.536 15.536 12 12 8.464zM12 20.464l-3.06-3.06-1.768 1.768L12 24l4.828-4.828-1.768-1.768L12 20.464z"/>
                                    </svg>
                                </div>
                                <div class="neo-wallet-info">
                                    <span class="neo-wallet-name">Binance</span>
                                    <span class="neo-wallet-desc">Conecta tu cuenta Binance</span>
                                </div>
                                <svg class="neo-wallet-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 18l6-6-6-6"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-sync-modal');
        });
    },
    
    showWalletSelectionModal() {
        const wallets = this.getSyncedWallets();
        const walletNames = {
            telegram: 'Telegram Wallet',
            binance: 'Binance',
            external: 'Wallet Externa'
        };
        
        let walletsHtml = '';
        
        if (wallets.telegram) {
            walletsHtml += `
                <div class="neo-wallet-item synced" onclick="App.selectWalletAndShowPackages('telegram')">
                    <div class="neo-wallet-icon telegram">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.828.94z"/>
                        </svg>
                    </div>
                    <div class="neo-wallet-info">
                        <span class="neo-wallet-name">Telegram Wallet</span>
                        <span class="neo-wallet-synced"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Principal</span>
                    </div>
                    <svg class="neo-wallet-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </div>
            `;
        }
        
        if (wallets.binance) {
            const isSecondary = wallets.telegram ? true : false;
            walletsHtml += `
                <div class="neo-wallet-item synced" onclick="App.selectWalletAndShowPackages('binance')">
                    <div class="neo-wallet-icon binance">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0L7.172 4.828l1.768 1.768L12 3.536l3.06 3.06 1.768-1.768L12 0zM4.828 7.172L0 12l4.828 4.828 1.768-1.768L3.536 12l3.06-3.06-1.768-1.768zM19.172 7.172l-1.768 1.768L20.464 12l-3.06 3.06 1.768 1.768L24 12l-4.828-4.828zM12 8.464L8.464 12 12 15.536 15.536 12 12 8.464zM12 20.464l-3.06-3.06-1.768 1.768L12 24l4.828-4.828-1.768-1.768L12 20.464z"/>
                        </svg>
                    </div>
                    <div class="neo-wallet-info">
                        <span class="neo-wallet-name">Binance</span>
                        <span class="neo-wallet-synced"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> ${isSecondary ? 'Secundaria / Recuperacion' : 'Principal'}</span>
                    </div>
                    <svg class="neo-wallet-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </div>
            `;
        }
        
        walletsHtml += `
            <div class="neo-wallet-item external-option" onclick="App.selectWalletAndShowPackages('external')">
                <div class="neo-wallet-icon external">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="6" width="20" height="12" rx="2"/>
                        <path d="M22 10H2M7 15h4"/>
                    </svg>
                </div>
                <div class="neo-wallet-info">
                    <span class="neo-wallet-name">Cuenta Externa</span>
                    <span class="neo-wallet-desc">Depositar desde otra wallet</span>
                </div>
                <svg class="neo-wallet-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 18l6-6-6-6"/>
                </svg>
            </div>
        `;
        
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-wallet-select-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Seleccionar Wallet</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-wallet-select-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <p class="neo-select-wallet-text">Elige desde que wallet deseas depositar:</p>
                    <div class="neo-wallets-section">
                        <div class="neo-wallet-options">
                            ${walletsHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-wallet-select-modal');
        });
    },
    
    selectWalletAndShowPackages(type) {
        this.closeB3CModal('b3c-wallet-select-modal');
        this.selectedWalletType = type;
        if (type === 'external') {
            this.showExternalDepositAddress();
        } else {
            this.showDepositPackages(type);
        }
    },
    
    async syncWalletAndDeposit(type) {
        this.closeB3CModal('b3c-sync-modal');
        this.selectedWalletType = type;
        
        if (type === 'telegram') {
            try {
                const walletAddress = await this.connectTelegramWallet();
                if (walletAddress) {
                    this.saveSyncedWallet('telegram', walletAddress);
                    this.showDepositPackages('telegram');
                } else {
                    this.showToast('Conexion de wallet cancelada', 'info');
                }
            } catch (error) {
                console.error('Error connecting telegram wallet:', error);
                this.showToast('Error al conectar wallet', 'error');
            }
        } else if (type === 'binance') {
            this.connectBinanceWallet();
        }
    },
    
    async selectWalletForDeposit(type) {
        const syncedWallets = this.getSyncedWallets();
        this.selectedWalletType = type;
        
        if (syncedWallets[type]) {
            this.closeB3CModal('b3c-deposit-modal');
            this.showDepositPackages(type);
        } else {
            if (type === 'telegram') {
                this.closeB3CModal('b3c-deposit-modal');
                try {
                    const walletAddress = await this.connectTelegramWallet();
                    if (walletAddress) {
                        this.saveSyncedWallet('telegram', walletAddress);
                        this.showDepositPackages('telegram');
                    } else {
                        this.showToast('Conexion de wallet cancelada', 'info');
                    }
                } catch (error) {
                    console.error('Error connecting telegram wallet:', error);
                    this.showToast('Error al conectar wallet', 'error');
                }
            } else if (type === 'binance') {
                this.closeB3CModal('b3c-deposit-modal');
                this.connectBinanceWallet();
            } else if (type === 'external') {
                this.closeB3CModal('b3c-deposit-modal');
                this.saveSyncedWallet('external', 'wallet-externa');
                this.showDepositPackages('external');
            }
        }
    },
    
    showDepositPackages(walletType) {
        const walletNames = {
            telegram: 'Telegram Wallet',
            binance: 'Binance',
            external: 'Wallet Externa'
        };
        
        const syncedWallets = this.getSyncedWallets();
        const syncedCount = this.countSyncedWallets();
        const availableToSync = this.getAvailableWalletToSync();
        
        let syncedWalletsHtml = '';
        let addSecondaryHtml = '';
        
        if (syncedCount === 1 && availableToSync) {
            const availableNames = {
                telegram: 'Telegram Wallet',
                binance: 'Binance'
            };
            const availableIcons = {
                telegram: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.828.94z"/></svg>`,
                binance: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0L7.172 4.828l1.768 1.768L12 3.536l3.06 3.06 1.768-1.768L12 0zM4.828 7.172L0 12l4.828 4.828 1.768-1.768L3.536 12l3.06-3.06-1.768-1.768zM19.172 7.172l-1.768 1.768L20.464 12l-3.06 3.06 1.768 1.768L24 12l-4.828-4.828zM12 8.464L8.464 12 12 15.536 15.536 12 12 8.464zM12 20.464l-3.06-3.06-1.768 1.768L12 24l4.828-4.828-1.768-1.768L12 20.464z"/></svg>`
            };
            
            syncedWalletsHtml = `
                <div class="neo-synced-wallets-section">
                    <h5 class="neo-synced-title">Wallets vinculadas</h5>
                    <div class="neo-synced-wallet-item active">
                        <span class="neo-synced-wallet-icon ${walletType}">${walletType === 'telegram' ? availableIcons.telegram : availableIcons.binance}</span>
                        <span class="neo-synced-wallet-name">${walletNames[walletType]}</span>
                        <span class="neo-synced-wallet-badge">En uso</span>
                    </div>
                    <div class="neo-add-secondary" onclick="App.addSecondaryWallet('${availableToSync}')">
                        <span class="neo-add-icon">+</span>
                        <div class="neo-add-info">
                            <span class="neo-add-title">Agregar ${availableNames[availableToSync]}</span>
                            <span class="neo-add-desc">Wallet secundaria / recuperacion</span>
                        </div>
                    </div>
                </div>
            `;
        } else if (syncedCount === 2) {
            const otherWallet = walletType === 'telegram' ? 'binance' : 'telegram';
            const otherIcons = {
                telegram: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.828.94z"/></svg>`,
                binance: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0L7.172 4.828l1.768 1.768L12 3.536l3.06 3.06 1.768-1.768L12 0zM4.828 7.172L0 12l4.828 4.828 1.768-1.768L3.536 12l3.06-3.06-1.768-1.768zM19.172 7.172l-1.768 1.768L20.464 12l-3.06 3.06 1.768 1.768L24 12l-4.828-4.828zM12 8.464L8.464 12 12 15.536 15.536 12 12 8.464zM12 20.464l-3.06-3.06-1.768 1.768L12 24l4.828-4.828-1.768-1.768L12 20.464z"/></svg>`
            };
            
            syncedWalletsHtml = `
                <div class="neo-synced-wallets-section">
                    <h5 class="neo-synced-title">Wallets vinculadas</h5>
                    <div class="neo-synced-wallet-item active">
                        <span class="neo-synced-wallet-icon ${walletType}">${otherIcons[walletType]}</span>
                        <span class="neo-synced-wallet-name">${walletNames[walletType]}</span>
                        <span class="neo-synced-wallet-badge">En uso</span>
                    </div>
                    <div class="neo-synced-wallet-item" onclick="App.switchToWallet('${otherWallet}')">
                        <span class="neo-synced-wallet-icon ${otherWallet}">${otherIcons[otherWallet]}</span>
                        <span class="neo-synced-wallet-name">${walletNames[otherWallet]}</span>
                        <span class="neo-synced-wallet-badge secondary">Secundaria</span>
                    </div>
                </div>
            `;
        }
        
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'b3c-packages-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content b3c-packages-modal">
                <div class="modal-header">
                    <h3>Depositar B3C</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('b3c-packages-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="neo-packages-section">
                        <h4 class="neo-packages-title">Selecciona un paquete</h4>
                        <p class="neo-packages-info">Comision: 5% - Precio en tiempo real</p>
                        
                        <div class="neo-packages-grid">
                            <div class="neo-package-item test" onclick="App.selectPackage(0.5)">
                                <span class="neo-package-badge">Prueba</span>
                                <span class="neo-package-amount">0.5 TON</span>
                                <span class="neo-package-estimate" id="pkg-est-05">Calculando...</span>
                            </div>
                            <div class="neo-package-item" onclick="App.selectPackage(1)">
                                <span class="neo-package-amount">1 TON</span>
                                <span class="neo-package-estimate" id="pkg-est-1">Calculando...</span>
                            </div>
                            <div class="neo-package-item popular" onclick="App.selectPackage(5)">
                                <span class="neo-package-badge">Popular</span>
                                <span class="neo-package-amount">5 TON</span>
                                <span class="neo-package-estimate" id="pkg-est-5">Calculando...</span>
                            </div>
                            <div class="neo-package-item" onclick="App.selectPackage(10)">
                                <span class="neo-package-amount">10 TON</span>
                                <span class="neo-package-estimate" id="pkg-est-10">Calculando...</span>
                            </div>
                            <div class="neo-package-item" onclick="App.selectPackage(20)">
                                <span class="neo-package-amount">20 TON</span>
                                <span class="neo-package-estimate" id="pkg-est-20">Calculando...</span>
                            </div>
                        </div>
                        
                        <div class="neo-custom-amount">
                            <label>Monto personalizado</label>
                            <div class="neo-custom-input-row">
                                <input type="number" id="modal-custom-ton" placeholder="Cantidad en TON" min="0.1" step="0.1">
                                <span class="neo-input-suffix">TON</span>
                            </div>
                            <button class="neo-custom-btn" onclick="App.selectCustomPackage()">Depositar</button>
                        </div>
                    </div>
                    
                    ${syncedWalletsHtml}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('b3c-packages-modal');
        });
        
        if (!this.b3cPriceData) {
            this.loadB3CPrice().then(() => {
                this.updatePackageEstimates();
            });
        } else {
            this.updatePackageEstimates();
        }
    },
    
    async addSecondaryWallet(type) {
        this.closeB3CModal('b3c-packages-modal');
        
        if (type === 'telegram') {
            try {
                const walletAddress = await this.connectTelegramWallet();
                if (walletAddress) {
                    this.saveSyncedWallet('telegram', walletAddress);
                    this.showToast('Wallet secundaria vinculada', 'success');
                    this.showDepositPackages('telegram');
                }
            } catch (error) {
                console.error('Error connecting telegram wallet:', error);
                this.showToast('Error al conectar wallet', 'error');
            }
        } else if (type === 'binance') {
            this.connectBinanceWallet();
        }
    },
    
    connectBinanceWallet() {
        this.showToast('La integracion con Binance estara disponible proximamente', 'info');
    },
    
    switchToWallet(type) {
        this.closeB3CModal('b3c-packages-modal');
        this.selectedWalletType = type;
        this.showDepositPackages(type);
    },
    
    updatePackageEstimates() {
        const priceData = this.b3cPriceData;
        if (priceData && priceData.price_ton && priceData.price_ton > 0) {
            const packages = [0.5, 1, 5, 10, 20];
            packages.forEach(ton => {
                const b3c = Math.floor((ton * 0.95) / priceData.price_ton);
                const id = ton === 0.5 ? 'pkg-est-05' : `pkg-est-${ton}`;
                const el = document.getElementById(id);
                if (el) el.textContent = `~${b3c.toLocaleString()} B3C`;
            });
        }
    },
    
    selectPackage(tonAmount) {
        this.closeB3CModal('b3c-packages-modal');
        this.buyB3CWithTonConnect(tonAmount);
    },
    
    selectCustomPackage() {
        const input = document.getElementById('modal-custom-ton');
        const amount = parseFloat(input?.value);
        if (amount && amount >= 0.1) {
            this.closeB3CModal('b3c-packages-modal');
            this.buyB3CWithTonConnect(amount);
        } else {
            this.showToast('Ingresa un monto valido (minimo 0.1 TON)', 'error');
        }
    },
    
    showExternalDepositAddress() {
        this.closeB3CModal('b3c-deposit-modal');
        this.apiRequest('/api/b3c/deposit/address').then(response => {
            if (!response.success) {
                this.showToast(response.error || 'Error al obtener direccion de deposito', 'error');
                return;
            }
            
            const expiresInfo = response.expiresInMinutes ? 
                `<div class="b3c-expires-info">
                    <span class="expires-icon">⏱️</span>
                    <span>Expira en ${response.expiresInMinutes} minutos</span>
                </div>` : '';
            
            const purchaseInfo = response.purchaseId ?
                `<div class="b3c-purchase-id">
                    <label>ID de Deposito</label>
                    <code>${response.purchaseId}</code>
                </div>` : '';
            
            const modal = document.createElement('div');
            modal.className = 'b3c-modal modal-overlay';
            modal.id = 'b3c-deposit-address-modal';
            modal.innerHTML = `
                <div class="modal-content b3c-modal-content">
                    <div class="modal-header">
                        <h3>Depositar desde Wallet Externa</h3>
                        <button class="modal-close" onclick="App.closeB3CModal('b3c-deposit-address-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${expiresInfo}
                        ${purchaseInfo}
                        
                        <div class="b3c-deposit-info">
                            <p>Envia TON a la siguiente direccion unica:</p>
                        </div>
                        
                        <div class="b3c-deposit-address">
                            <label>Direccion de deposito (unica para ti)</label>
                            <div class="address-box">
                                <code id="deposit-address">${response.depositAddress}</code>
                                <button class="btn-copy" onclick="App.copyToClipboard('${response.depositAddress}')">Copiar</button>
                            </div>
                        </div>
                        
                        <div class="b3c-deposit-instructions">
                            <h4>Instrucciones:</h4>
                            <ul>
                                ${response.instructions.map(i => `<li>${i}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="b3c-notice">
                            <span class="notice-icon">✅</span>
                            <span>${response.notice}</span>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeB3CModal('b3c-deposit-address-modal');
            });
        }).catch(error => {
            console.error('Error getting deposit address:', error);
            this.showToast('Error de conexion', 'error');
        });
    },

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado al portapapeles', 'success');
        }).catch(() => {
            this.showToast('Error al copiar', 'error');
        });
    },

    startB3CPricePolling() {
        this.loadB3CPrice();
        
        if (this.b3cPriceInterval) {
            clearInterval(this.b3cPriceInterval);
        }
        
        this.b3cPriceInterval = setInterval(() => {
            this.loadB3CPrice();
        }, 30000);
    },

    stopB3CPricePolling() {
        if (this.b3cPriceInterval) {
            clearInterval(this.b3cPriceInterval);
            this.b3cPriceInterval = null;
        }
    },

    currentDateRange: 'all',
    
    initTransactionFilters() {
        document.querySelectorAll('.tx-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tx-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentTransactionFilter = btn.dataset.filter;
                this.loadTransactionHistory(0, false);
            });
        });
        
        const dateRangeSelect = document.getElementById('tx-date-range');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                this.currentDateRange = e.target.value;
                this.loadTransactionHistory(0, false);
            });
        }
        
        this.startWalletPolling();
    },
    
    getDateRangeParams() {
        const now = new Date();
        let fromDate = null;
        
        switch (this.currentDateRange) {
            case 'today':
                fromDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                break;
            case 'week':
                fromDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case 'month':
                fromDate = new Date(now.getFullYear(), now.getMonth(), 1);
                break;
            default:
                return '';
        }
        
        return fromDate ? `&from_date=${fromDate.toISOString()}` : '';
    },

    async loadTransactionHistory(offset = 0, append = false) {
        const container = document.getElementById('transactions-list');
        const loadMoreBtn = document.getElementById('load-more-transactions');
        
        if (!container) return;
        
        if (!append) {
            container.innerHTML = '<div class="loading-transactions">Cargando transacciones...</div>';
        }
        
        try {
            let url = `/api/wallet/transactions?offset=${offset}&limit=${this.transactionLimit}`;
            if (this.currentTransactionFilter && this.currentTransactionFilter !== 'all') {
                url += `&filter=${this.currentTransactionFilter}`;
            }
            url += this.getDateRangeParams();
            const response = await this.apiRequest(url);
            
            if (response.success) {
                const transactions = response.transactions || [];
                
                if (!append) {
                    container.innerHTML = '';
                }
                
                if (transactions.length === 0 && offset === 0) {
                    container.innerHTML = `
                        <div class="transactions-empty">
                            <div class="empty-icon">📋</div>
                            <p>No hay transacciones aun</p>
                            <span>Tus movimientos apareceran aqui</span>
                        </div>
                    `;
                    if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
                    return;
                }
                
                transactions.forEach(tx => {
                    container.insertAdjacentHTML('beforeend', this.renderTransaction(tx));
                });
                
                this.transactionOffset = offset + transactions.length;
                this.hasMoreTransactions = transactions.length === this.transactionLimit;
                
                if (loadMoreBtn) {
                    loadMoreBtn.classList.toggle('hidden', !this.hasMoreTransactions);
                }
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
            if (!append) {
                container.innerHTML = '<div class="transactions-error">Error al cargar transacciones</div>';
            }
        }
    },

    renderTransaction(tx) {
        const isCredit = tx.amount > 0;
        const dateStr = this.formatRelativeDate(tx.created_at);
        const status = tx.status || 'confirmed';
        
        const typeIcons = {
            'purchase': '🛒',
            'reward': '🎁',
            'transfer_in': '📥',
            'transfer_out': '📤',
            'recharge': '💰',
            'payment': '💳',
            'refund': '↩️',
            'bonus': '⭐'
        };
        
        const icon = typeIcons[tx.type] || (isCredit ? '📥' : '📤');
        
        let statusBadge = '';
        if (status === 'pending') {
            statusBadge = '<span class="tx-status pending">Pendiente</span>';
        } else if (status === 'cancelled') {
            statusBadge = '<span class="tx-status cancelled">Cancelado</span>';
        }
        
        return `
            <div class="transaction-item ${isCredit ? 'credit' : 'debit'} ${status}">
                <div class="tx-icon">${icon}</div>
                <div class="tx-details">
                    <span class="tx-description">${tx.description || (isCredit ? 'Recarga' : 'Gasto')}</span>
                    <span class="tx-date">${dateStr} ${statusBadge}</span>
                </div>
                <div class="tx-amount ${isCredit ? 'positive' : 'negative'}">
                    ${isCredit ? '+' : ''}${Math.abs(tx.amount).toFixed(2)} B3C
                </div>
            </div>
        `;
    },

    formatRelativeDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSecs < 60) return 'Hace un momento';
        if (diffMins < 60) return `Hace ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
        if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
        if (diffDays < 7) return `Hace ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
        
        return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    },

    loadMoreTransactions() {
        if (this.hasMoreTransactions) {
            this.loadTransactionHistory(this.transactionOffset, true);
        }
    },

    toggleHistoryMenu() {
        const dropdown = document.getElementById('history-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('hidden');
            
            const closeDropdown = (e) => {
                if (!e.target.closest('.neo-history-menu-wrapper')) {
                    dropdown.classList.add('hidden');
                    document.removeEventListener('click', closeDropdown);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', closeDropdown);
            }, 10);
        }
    },
    
    showFilterModal() {
        const dropdown = document.getElementById('history-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
        
        const modal = document.createElement('div');
        modal.className = 'b3c-modal modal-overlay';
        modal.id = 'filter-modal';
        modal.innerHTML = `
            <div class="modal-content b3c-modal-content">
                <div class="modal-header">
                    <h3>Filtrar transacciones</h3>
                    <button class="modal-close" onclick="App.closeB3CModal('filter-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="filter-section">
                        <label class="filter-label">Tipo de transaccion</label>
                        <div class="filter-options">
                            <button class="filter-option-btn ${this.currentTxFilter === 'all' ? 'active' : ''}" data-filter="all" onclick="App.setTxTypeFilter('all')">Todos</button>
                            <button class="filter-option-btn ${this.currentTxFilter === 'credit' ? 'active' : ''}" data-filter="credit" onclick="App.setTxTypeFilter('credit')">Recargas</button>
                            <button class="filter-option-btn ${this.currentTxFilter === 'debit' ? 'active' : ''}" data-filter="debit" onclick="App.setTxTypeFilter('debit')">Gastos</button>
                        </div>
                    </div>
                    <div class="filter-section">
                        <label class="filter-label">Periodo de tiempo</label>
                        <div class="filter-options">
                            <button class="filter-option-btn ${this.currentDateFilter === 'all' ? 'active' : ''}" data-date="all" onclick="App.setDateFilter('all')">Todo</button>
                            <button class="filter-option-btn ${this.currentDateFilter === 'today' ? 'active' : ''}" data-date="today" onclick="App.setDateFilter('today')">Hoy</button>
                            <button class="filter-option-btn ${this.currentDateFilter === 'week' ? 'active' : ''}" data-date="week" onclick="App.setDateFilter('week')">Semana</button>
                            <button class="filter-option-btn ${this.currentDateFilter === 'month' ? 'active' : ''}" data-date="month" onclick="App.setDateFilter('month')">Mes</button>
                        </div>
                    </div>
                    <button class="neo-apply-filter-btn" onclick="App.applyFilters()">Aplicar filtros</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeB3CModal('filter-modal');
        });
    },
    
    currentTxFilter: 'all',
    currentDateFilter: 'all',
    
    setTxTypeFilter(filter) {
        this.currentTxFilter = filter;
        document.querySelectorAll('#filter-modal .filter-options:first-of-type .filter-option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
    },
    
    setDateFilter(date) {
        this.currentDateFilter = date;
        document.querySelectorAll('#filter-modal .filter-section:last-of-type .filter-option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.date === date);
        });
    },
    
    applyFilters() {
        this.closeB3CModal('filter-modal');
        const badge = document.getElementById('active-filter-badge');
        const badgeText = document.getElementById('filter-badge-text');
        
        if (this.currentTxFilter !== 'all' || this.currentDateFilter !== 'all') {
            let filterText = [];
            if (this.currentTxFilter !== 'all') {
                filterText.push(this.currentTxFilter === 'credit' ? 'Recargas' : 'Gastos');
            }
            if (this.currentDateFilter !== 'all') {
                const dateLabels = { today: 'Hoy', week: 'Semana', month: 'Mes' };
                filterText.push(dateLabels[this.currentDateFilter]);
            }
            badgeText.textContent = filterText.join(' - ');
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
        
        this.transactionOffset = 0;
        this.loadTransactionHistory(0, false);
    },
    
    clearFilters() {
        this.currentTxFilter = 'all';
        this.currentDateFilter = 'all';
        document.getElementById('active-filter-badge').classList.add('hidden');
        this.transactionOffset = 0;
        this.loadTransactionHistory(0, false);
    },

    async exportTransactionHistory() {
        const dropdown = document.getElementById('history-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
        
        try {
            const response = await this.apiRequest('/api/wallet/transactions?offset=0&limit=1000');
            
            if (response.success && response.transactions) {
                let csv = 'Fecha,Tipo,Descripcion,Monto\n';
                response.transactions.forEach(tx => {
                    const date = new Date(tx.created_at).toISOString();
                    const type = tx.amount > 0 ? 'Credito' : 'Debito';
                    const desc = (tx.description || '').replace(/,/g, ';');
                    csv += `${date},${type},"${desc}",${tx.amount}\n`;
                });
                
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transacciones_${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.showToast('Historial exportado', 'success');
            }
        } catch (error) {
            this.showToast('Error al exportar historial', 'error');
        }
    },

    async purchaseBot(botId, price) {
        const response = await this.apiRequest('/api/wallet/debit', {
            method: 'POST',
            body: JSON.stringify({
                amount: price,
                type: 'bot_purchase',
                description: `Compra de Bot #${botId}`,
                reference_id: botId
            })
        });
        
        if (response.success) {
            await this.loadWalletBalance(true);
            return true;
        } else if (response.error === 'insufficient_balance') {
            this.showToast('Saldo insuficiente. Recarga tu wallet.', 'error');
            return false;
        } else {
            this.showToast(response.error || 'Error al procesar compra', 'error');
            return false;
        }
    },

    getDeviceType() {
        const ua = navigator.userAgent.toLowerCase();
        if (ua.includes('telegram')) {
            if (ua.includes('android')) return 'telegram_android';
            if (ua.includes('iphone') || ua.includes('ipad')) return 'telegram_ios';
            return 'telegram_desktop';
        }
        if (ua.includes('android')) return 'mobile_android';
        if (ua.includes('iphone') || ua.includes('ipad')) return 'mobile_ios';
        if (ua.includes('mac')) return 'desktop_mac';
        if (ua.includes('win')) return 'desktop_windows';
        if (ua.includes('linux')) return 'desktop_linux';
        return 'unknown';
    },

    getDeviceName() {
        const type = this.getDeviceType();
        const names = {
            'telegram_android': 'Telegram Android',
            'telegram_ios': 'Telegram iOS',
            'telegram_desktop': 'Telegram Desktop',
            'mobile_android': 'Navegador Android',
            'mobile_ios': 'Navegador iOS',
            'desktop_mac': 'Mac',
            'desktop_windows': 'Windows',
            'desktop_linux': 'Linux',
            'unknown': 'Dispositivo'
        };
        return names[type] || 'Dispositivo';
    },

    async addCurrentDeviceAsTrusted() {
        try {
            const deviceName = this.getDeviceName();
            const deviceType = this.getDeviceType();
            
            const response = await fetch('/api/devices/trusted/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({
                    deviceId: this.deviceId,
                    deviceName: deviceName,
                    deviceType: deviceType
                })
            });
            const data = await response.json();
            
            if (data.success) {
                this.isDeviceTrusted = true;
                this.trustedDeviceName = deviceName;
                this.showToast('Dispositivo agregado como confianza', 'success');
                this.closeAddDeviceModal();
                return true;
            } else {
                this.showToast(data.error || 'Error al agregar dispositivo', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error agregando dispositivo:', error);
            this.showToast('Error al agregar dispositivo', 'error');
            return false;
        }
    },

    showAddDeviceModal() {
        const existingModal = document.getElementById('add-device-modal');
        if (existingModal) existingModal.remove();
        
        const deviceName = this.getDeviceName();
        const walletPreview = this.syncedWalletAddress ? 
            this.syncedWalletAddress.slice(0, 6) + '...' + this.syncedWalletAddress.slice(-4) : 
            'No disponible';
        
        const modalHtml = `
            <div id="add-device-modal" class="modal-overlay" onclick="if(event.target === this) App.closeAddDeviceModal()">
                <div class="modal-content device-modal">
                    <div class="modal-header">
                        <h3>Agregar Dispositivo de Confianza</h3>
                        <button class="modal-close" onclick="App.closeAddDeviceModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="device-info-card">
                            <div class="device-icon">
                                ${this.getDeviceIconSVG()}
                            </div>
                            <div class="device-details">
                                <h4>${deviceName}</h4>
                                <p class="device-id-preview">ID: ${this.deviceId.slice(0, 12)}...</p>
                            </div>
                        </div>
                        
                        <div class="wallet-sync-info">
                            <div class="info-row">
                                <span class="info-label">Wallet sincronizada:</span>
                                <span class="info-value">${walletPreview}</span>
                            </div>
                        </div>
                        
                        <div class="device-benefits">
                            <h4>Al agregar este dispositivo podras:</h4>
                            <ul>
                                <li>Ver tu saldo de creditos</li>
                                <li>Realizar recargas con tu wallet</li>
                                <li>Acceder a todas las funciones de la app</li>
                            </ul>
                        </div>
                        
                        <p class="device-warning">
                            Solo agrega dispositivos que sean tuyos y de tu confianza.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="App.closeAddDeviceModal()">Cancelar</button>
                        <button class="btn btn-primary" onclick="App.confirmAddDevice()">Agregar Dispositivo</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    getDeviceIconSVG() {
        const type = this.getDeviceType();
        if (type.includes('telegram')) {
            return '<svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.94z"/></svg>';
        }
        if (type.includes('mobile')) {
            return '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12" y2="18"/></svg>';
        }
        return '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>';
    },

    closeAddDeviceModal() {
        const modal = document.getElementById('add-device-modal');
        if (modal) modal.remove();
    },

    async confirmAddDevice() {
        const btn = document.querySelector('#add-device-modal .btn-primary');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Agregando...';
        }
        
        const success = await this.addCurrentDeviceAsTrusted();
        
        if (success && this.walletSyncedFromServer) {
            this.updateDeviceTrustUI();
        }
        
        if (btn && !success) {
            btn.disabled = false;
            btn.textContent = 'Agregar Dispositivo';
        }
    },

    updateDeviceTrustUI() {
        const walletSection = document.querySelector('.wallet-section');
        if (!walletSection) return;
        
        const existingBanner = document.getElementById('device-trust-banner');
        if (existingBanner) existingBanner.remove();
        
        if (this.walletSyncedFromServer && !this.connectedWallet && !this.isDeviceTrusted) {
            const bannerHtml = `
                <div id="device-trust-banner" class="device-trust-banner">
                    <div class="banner-content">
                        <div class="banner-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            </svg>
                        </div>
                        <div class="banner-text">
                            <strong>Wallet sincronizada</strong>
                            <p>Agrega este dispositivo como confianza para usar todas las funciones</p>
                        </div>
                    </div>
                    <button class="btn btn-small btn-primary" onclick="App.showAddDeviceModal()">
                        Agregar Dispositivo
                    </button>
                </div>
            `;
            walletSection.insertAdjacentHTML('afterbegin', bannerHtml);
        } else if (this.isDeviceTrusted && !this.connectedWallet) {
            const trustedBannerHtml = `
                <div id="device-trust-banner" class="device-trust-banner trusted">
                    <div class="banner-content">
                        <div class="banner-icon trusted">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                <polyline points="22 4 12 14.01 9 11.01"/>
                            </svg>
                        </div>
                        <div class="banner-text">
                            <strong>Dispositivo de confianza</strong>
                            <p>Conecta tu wallet para realizar transacciones</p>
                        </div>
                    </div>
                    <button class="btn btn-small btn-secondary" onclick="App.connectWallet()">
                        Conectar Wallet
                    </button>
                </div>
            `;
            walletSection.insertAdjacentHTML('afterbegin', trustedBannerHtml);
        }
    },

    async initiateUSDTPayment(credits, usdtAmount) {
        if (!this.isDeviceTrusted && this.walletSyncedFromServer) {
            this.showToast('Agrega este dispositivo como confianza para realizar transacciones', 'info');
            this.showAddDeviceModal();
            return;
        }
        
        if (!this.connectedWallet) {
            if (this.isDeviceTrusted && this.walletSyncedFromServer) {
                this.showToast('Conecta tu wallet para firmar la transaccion', 'info');
                await this.connectWallet();
            } else {
                this.showToast('Primero conecta tu wallet', 'error');
                await this.connectWallet();
            }
            return;
        }
        
        if (!this.MERCHANT_WALLET) {
            await this.loadMerchantWallet();
            if (!this.MERCHANT_WALLET) {
                this.showToast('Error de configuracion del sistema de pagos', 'error');
                return;
            }
        }

        try {
            this.showToast(`Preparando pago de ${usdtAmount} USDT...`, 'info');
            
            const amountInNano = BigInt(usdtAmount * 1000000);
            
            const forwardPayload = this.buildJettonTransferPayload(
                this.MERCHANT_WALLET,
                amountInNano.toString(),
                this.user?.id?.toString() || 'unknown'
            );

            const userJettonWallet = await this.getUserJettonWalletAddress(
                this.connectedWallet.account.address
            );

            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 600,
                messages: [
                    {
                        address: userJettonWallet,
                        amount: '100000000',
                        payload: forwardPayload
                    }
                ]
            };

            const result = await this.tonConnectUI.sendTransaction(transaction);
            
            if (result) {
                this.showToast('Transaccion enviada! Procesando...', 'success');
                
                await this.recordPayment(credits, usdtAmount, result.boc);
            }
        } catch (error) {
            console.error('Payment error:', error);
            if (error.message?.includes('Canceled')) {
                this.showToast('Pago cancelado', 'info');
            } else {
                this.showToast('Error al procesar pago: ' + (error.message || 'Intenta de nuevo'), 'error');
            }
        }
    },

    buildJettonTransferPayload(destination, amount, comment) {
        return btoa(JSON.stringify({
            op: 0xf8a7ea5,
            queryId: Date.now(),
            amount: amount,
            destination: destination,
            responseDestination: destination,
            forwardAmount: '1',
            forwardPayload: comment
        }));
    },

    async getUserJettonWalletAddress(userAddress) {
        return this.USDT_MASTER_ADDRESS;
    },

    async recordPayment(credits, usdtAmount, transactionBoc) {
        try {
            const response = await this.apiRequest('/api/wallet/credit', {
                method: 'POST',
                body: JSON.stringify({
                    credits: credits,
                    usdtAmount: usdtAmount,
                    transactionBoc: transactionBoc,
                    userId: this.user?.id
                })
            });

            if (response.success) {
                this.showToast(`+${credits} BUNK3RCO1N agregados!`, 'success');
                this.loadWalletBalance(true);
            }
        } catch (error) {
            console.error('Error recording payment:', error);
        }
    },

    async loadWalletBalance(animate = false) {
        try {
            const response = await this.apiRequest('/api/wallet/balance', { method: 'GET' });
            if (response.success) {
                const balanceEl = document.getElementById('wallet-balance');
                if (balanceEl) {
                    const oldBalance = parseFloat(balanceEl.textContent.replace(/,/g, '')) || 0;
                    const newBalance = response.balance || 0;
                    
                    this._lastKnownBalance = newBalance;
                    
                    if (animate && oldBalance !== newBalance) {
                        this.animateBalanceChange(balanceEl, oldBalance, newBalance);
                    } else {
                        balanceEl.textContent = newBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    }
                    
                    if (typeof StateManager !== 'undefined') {
                        StateManager.set('wallet.balance', newBalance, { silent: true });
                    }
                }
            }
        } catch (error) {
            console.error('Error loading wallet balance:', error);
        }
    },

    animateBalanceChange(element, from, to) {
        const duration = 1000;
        const start = performance.now();
        const diff = to - from;
        
        element.classList.add('balance-updating');
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = from + diff * easeOut;
            
            element.textContent = current.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.classList.remove('balance-updating');
                element.classList.add('balance-changed');
                setTimeout(() => element.classList.remove('balance-changed'), 500);
            }
        };
        
        requestAnimationFrame(animate);
    },

    showWalletSkeleton() {
        const transactionList = document.getElementById('transaction-list');
        if (!transactionList) return;
        if (transactionList.querySelector('[data-skeleton]')) return;
        if (transactionList.querySelector('.transaction-item')) return;
        
        const skeletonHtml = Array(4).fill().map(() => `
            <div class="skeleton-transaction" data-skeleton="true">
                <div class="skeleton-transaction-icon"></div>
                <div class="skeleton-transaction-info">
                    <div class="skeleton-text"></div>
                    <div class="skeleton-text"></div>
                </div>
            </div>
        `).join('');
        transactionList.innerHTML = skeletonHtml;
    },

    hideWalletSkeleton() {
        const transactionList = document.getElementById('transaction-list');
        if (transactionList) {
            transactionList.querySelectorAll('[data-skeleton]').forEach(s => s.remove());
        }
    },

    showNotificationsSkeleton() {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        if (notificationsList.querySelector('[data-skeleton]')) return;
        if (notificationsList.querySelector('.notification-item')) return;
        
        const skeletonHtml = Array(5).fill().map(() => `
            <div class="skeleton-notification" data-skeleton="true">
                <div class="skeleton-avatar"></div>
                <div class="skeleton-transaction-info">
                    <div class="skeleton-text" style="width: 80%"></div>
                    <div class="skeleton-text" style="width: 50%"></div>
                </div>
            </div>
        `).join('');
        notificationsList.innerHTML = skeletonHtml;
    },

    hideNotificationsSkeleton() {
        const notificationsList = document.getElementById('notifications-list');
        if (notificationsList) {
            notificationsList.querySelectorAll('[data-skeleton]').forEach(s => s.remove());
        }
    },

    showProfileSkeleton() {
        const profileGrid = document.getElementById('profile-posts-grid');
        if (!profileGrid) return;
        if (profileGrid.querySelector('[data-skeleton]')) return;
        if (profileGrid.querySelector('.profile-grid-item')) return;
        
        const skeletonHtml = Array(6).fill().map(() => 
            `<div class="skeleton-grid-item" data-skeleton="true"></div>`
        ).join('');
        profileGrid.innerHTML = skeletonHtml;
    },

    hideProfileSkeleton() {
        const profileGrid = document.getElementById('profile-posts-grid');
        if (profileGrid) {
            profileGrid.querySelectorAll('[data-skeleton]').forEach(s => s.remove());
        }
    },

    async initiateTONPayment(credits, tonAmount) {
        try {
            this.showToast('Creando solicitud de pago...', 'info');
            
            const response = await this.apiRequest('/api/ton/payment/create', {
                method: 'POST',
                body: JSON.stringify({
                    credits: credits,
                    tonAmount: tonAmount
                })
            });
            
            if (!response.success) {
                this.showToast(response.error || 'Error al crear pago', 'error');
                return;
            }
            
            this.showPaymentModal(response);
            
        } catch (error) {
            console.error('Payment creation error:', error);
            this.showToast('Error al iniciar pago: ' + (error.message || 'Intenta de nuevo'), 'error');
        }
    },

    showPaymentModal(paymentData) {
        const { paymentId, merchantWallet, tonAmount, credits, comment } = paymentData;
        
        const modalHtml = `
            <div class="payment-modal-content">
                <h3>Recarga de BUNK3RCO1N</h3>
                <div class="payment-info">
                    <div class="payment-amount">
                        <span class="label">Cantidad a enviar:</span>
                        <span class="value">${tonAmount} TON</span>
                    </div>
                    <div class="payment-credits">
                        <span class="label">BUNK3RCO1N a recibir:</span>
                        <span class="value">+${credits}</span>
                    </div>
                </div>
                
                <div class="payment-instructions">
                    <p><strong>Paso 1:</strong> Copia la direccion de wallet</p>
                    <div class="wallet-address-box" onclick="App.copyToClipboard('${merchantWallet}')">
                        <span class="address">${merchantWallet}</span>
                        <span class="copy-icon">📋</span>
                    </div>
                    
                    <p><strong>Paso 2:</strong> Copia el comentario (IMPORTANTE)</p>
                    <div class="comment-box" onclick="App.copyToClipboard('${comment}')">
                        <span class="comment">${comment}</span>
                        <span class="copy-icon">📋</span>
                    </div>
                    
                    <p class="warning">⚠️ El comentario es OBLIGATORIO para identificar tu pago</p>
                    
                    <p><strong>Paso 3:</strong> Envia ${tonAmount} TON desde tu Telegram Wallet</p>
                </div>
                
                <div class="payment-actions">
                    <button class="btn-verify" onclick="App.verifyPayment('${paymentId}')">
                        Ya envie el pago - Verificar
                    </button>
                    <button class="btn-cancel" onclick="App.closeModal()">
                        Cancelar
                    </button>
                </div>
                
                <div id="payment-status" class="payment-status hidden">
                    <div class="spinner"></div>
                    <span>Verificando en blockchain...</span>
                </div>
            </div>
        `;
        
        this.showModal(modalHtml);
        this.currentPaymentId = paymentId;
    },

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado al portapapeles', 'success');
        }).catch(() => {
            const input = document.createElement('input');
            input.value = text;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            this.showToast('Copiado al portapapeles', 'success');
        });
    },

    paymentVerificationAttempts: {},
    pendingPaymentTimeouts: {},
    PAYMENT_TIMEOUT_MS: 15 * 60 * 1000,
    MAX_VERIFICATION_ATTEMPTS: 5,
    MAX_POLL_ATTEMPTS: 15,
    
    async verifyPayment(paymentId) {
        if (!this.paymentVerificationAttempts[paymentId]) {
            this.paymentVerificationAttempts[paymentId] = { 
                count: 0, 
                maxRetries: this.MAX_VERIFICATION_ATTEMPTS,
                startTime: Date.now()
            };
            
            this.startPaymentTimeout(paymentId);
        }
        
        const attemptData = this.paymentVerificationAttempts[paymentId];
        
        if (attemptData.count >= attemptData.maxRetries) {
            this.showPaymentLimitReached(paymentId);
            return;
        }
        
        attemptData.count++;
        
        const statusEl = document.getElementById('payment-status');
        const verifyBtn = document.querySelector('.btn-verify');
        const cancelBtn = document.querySelector('.btn-cancel');
        
        if (statusEl) {
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = `
                <div class="payment-verification-progress">
                    <div class="spinner"></div>
                    <span>Verificando en blockchain...</span>
                    <div class="verification-progress-bar">
                        <div class="verification-progress-fill" id="verify-progress"></div>
                    </div>
                    <span class="verification-attempt">Intento ${attemptData.count} de ${attemptData.maxRetries}</span>
                </div>
            `;
        }
        if (verifyBtn) {
            verifyBtn.disabled = true;
            verifyBtn.innerHTML = '<span class="btn-spinner"></span> Verificando...';
        }
        if (cancelBtn) {
            cancelBtn.textContent = 'Cancelar verificacion';
        }
        
        let pollAttempts = 0;
        const maxPollAttempts = this.MAX_POLL_ATTEMPTS;
        
        const checkPayment = async () => {
            try {
                if (this.isPaymentTimedOut(paymentId)) {
                    this.handlePaymentTimeout(paymentId);
                    return;
                }
                
                const response = await this.apiRequest(`/api/ton/payment/${paymentId}/verify`, {
                    method: 'POST'
                });
                
                if (response.status === 'confirmed') {
                    this.clearPaymentTimeout(paymentId);
                    delete this.paymentVerificationAttempts[paymentId];
                    this.closeModal();
                    this.showRechargeSuccess(response.creditsAdded);
                    return true;
                }
                
                if (response.status === 'pending') {
                    this.updatePaymentPendingUI(statusEl, paymentId);
                }
                
                pollAttempts++;
                const progressPercent = (pollAttempts / maxPollAttempts) * 100;
                const progressEl = document.getElementById('verify-progress');
                if (progressEl) {
                    progressEl.style.width = progressPercent + '%';
                }
                
                if (pollAttempts < maxPollAttempts) {
                    if (statusEl) {
                        const timeElapsed = Math.floor((Date.now() - attemptData.startTime) / 1000);
                        statusEl.querySelector('span:not(.verification-attempt)').textContent = 
                            `Buscando transaccion... (${pollAttempts}/${maxPollAttempts}) - ${timeElapsed}s`;
                    }
                    setTimeout(checkPayment, 4000);
                } else {
                    this.handleVerificationFailed(paymentId, attemptData, statusEl, verifyBtn);
                }
                
            } catch (error) {
                console.error('Verification error:', error);
                this.handleVerificationError(statusEl, verifyBtn, error);
            }
        };
        
        await checkPayment();
    },
    
    startPaymentTimeout(paymentId) {
        this.clearPaymentTimeout(paymentId);
        
        this.pendingPaymentTimeouts[paymentId] = {
            startTime: Date.now(),
            timeoutId: setTimeout(() => {
                this.handlePaymentTimeout(paymentId);
            }, this.PAYMENT_TIMEOUT_MS)
        };
    },
    
    clearPaymentTimeout(paymentId) {
        if (this.pendingPaymentTimeouts[paymentId]) {
            clearTimeout(this.pendingPaymentTimeouts[paymentId].timeoutId);
            delete this.pendingPaymentTimeouts[paymentId];
        }
    },
    
    isPaymentTimedOut(paymentId) {
        const timeout = this.pendingPaymentTimeouts[paymentId];
        if (!timeout) return false;
        return (Date.now() - timeout.startTime) >= this.PAYMENT_TIMEOUT_MS;
    },
    
    handlePaymentTimeout(paymentId) {
        this.clearPaymentTimeout(paymentId);
        delete this.paymentVerificationAttempts[paymentId];
        
        const statusEl = document.getElementById('payment-status');
        const verifyBtn = document.querySelector('.btn-verify');
        
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="payment-timeout-message">
                    <span class="timeout-icon">⏱️</span>
                    <span class="timeout-title">Tiempo de espera agotado</span>
                    <span class="timeout-text">Han pasado 15 minutos. Si realizaste el pago, contacta a soporte con el ID: ${paymentId}</span>
                </div>
            `;
        }
        if (verifyBtn) {
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Tiempo agotado';
        }
        
        this.showToast('El tiempo para verificar este pago ha expirado', 'error');
    },
    
    updatePaymentPendingUI(statusEl, paymentId) {
        const timeout = this.pendingPaymentTimeouts[paymentId];
        if (!timeout || !statusEl) return;
        
        const elapsed = Date.now() - timeout.startTime;
        const remaining = Math.max(0, this.PAYMENT_TIMEOUT_MS - elapsed);
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        
        const pendingInfo = statusEl.querySelector('.pending-time-remaining');
        if (!pendingInfo) {
            const infoEl = document.createElement('div');
            infoEl.className = 'pending-time-remaining';
            infoEl.textContent = `Tiempo restante: ${minutes}:${seconds.toString().padStart(2, '0')}`;
            statusEl.appendChild(infoEl);
        } else {
            pendingInfo.textContent = `Tiempo restante: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    },
    
    handleVerificationFailed(paymentId, attemptData, statusEl, verifyBtn) {
        const remaining = attemptData.maxRetries - attemptData.count;
        
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="verification-failed">
                    <span class="failed-icon">❌</span>
                    <span class="failed-title">No se encontro la transaccion</span>
                    <span class="failed-text">Verifica que hayas enviado el pago con el comentario correcto.</span>
                    ${remaining > 0 ? `<span class="failed-attempts">${remaining} intento(s) restante(s)</span>` : ''}
                </div>
            `;
        }
        if (verifyBtn) {
            verifyBtn.disabled = remaining === 0;
            verifyBtn.innerHTML = remaining > 0 ? '🔄 Reintentar verificacion' : '❌ Sin intentos disponibles';
            if (remaining === 0) {
                verifyBtn.classList.add('btn-exhausted');
            }
        }
    },
    
    handleVerificationError(statusEl, verifyBtn, error) {
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="verification-error">
                    <span class="error-icon">⚠️</span>
                    <span>Error de conexion. Intenta de nuevo.</span>
                </div>
            `;
        }
        if (verifyBtn) {
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = '🔄 Reintentar verificacion';
        }
    },
    
    showPaymentLimitReached(paymentId) {
        const statusEl = document.getElementById('payment-status');
        const verifyBtn = document.querySelector('.btn-verify');
        
        if (statusEl) {
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = `
                <div class="limit-reached">
                    <span class="limit-icon">🚫</span>
                    <span class="limit-title">Limite de verificaciones alcanzado</span>
                    <span class="limit-text">Has agotado los ${this.MAX_VERIFICATION_ATTEMPTS} intentos de verificacion.</span>
                    <span class="limit-help">Si realizaste el pago correctamente, espera 10 minutos e intenta de nuevo o contacta a soporte.</span>
                    <span class="limit-id">ID de pago: ${paymentId}</span>
                </div>
            `;
        }
        if (verifyBtn) {
            verifyBtn.disabled = true;
            verifyBtn.classList.add('btn-exhausted');
            verifyBtn.textContent = 'Sin intentos disponibles';
        }
        
        this.showToast('Limite de verificaciones alcanzado', 'error');
        
        setTimeout(() => {
            delete this.paymentVerificationAttempts[paymentId];
        }, 10 * 60 * 1000);
    },

    // ============================================================
    // SISTEMA DE SEGURIDAD - DISPOSITIVOS Y WALLET
    // ============================================================

    deviceId: null,
    deviceTrusted: false,
    walletVerified: false,
    twoFAVerified: false,
    securityStatus: null,
    lockoutTimer: null,

    generateDeviceId() {
        let deviceId = localStorage.getItem('bunk3r_device_id');
        if (!deviceId) {
            const ua = navigator.userAgent;
            const screenInfo = `${screen.width}x${screen.height}x${screen.colorDepth}`;
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const lang = navigator.language;
            const random = Math.random().toString(36).substring(2);
            const data = `${ua}|${screenInfo}|${timezone}|${lang}|${Date.now()}|${random}`;
            deviceId = btoa(data).replace(/[^a-zA-Z0-9]/g, '').substring(0, 32);
            localStorage.setItem('bunk3r_device_id', deviceId);
        }
        this.deviceId = deviceId;
        return deviceId;
    },

    getDeviceInfo() {
        const ua = navigator.userAgent;
        let deviceName = 'Dispositivo desconocido';
        let deviceType = 'unknown';

        if (/iPhone|iPad|iPod/.test(ua)) {
            deviceType = 'ios';
            if (/iPad/.test(ua)) {
                deviceName = 'iPad';
            } else {
                deviceName = 'iPhone';
            }
        } else if (/Android/.test(ua)) {
            deviceType = 'android';
            const match = ua.match(/Android.*;\s*([^;)]+)/);
            deviceName = match ? match[1].trim() : 'Dispositivo Android';
        } else if (/Windows/.test(ua)) {
            deviceType = 'windows';
            deviceName = 'Windows PC';
        } else if (/Mac/.test(ua)) {
            deviceType = 'mac';
            deviceName = 'Mac';
        } else if (/Linux/.test(ua)) {
            deviceType = 'linux';
            deviceName = 'Linux PC';
        }

        return { deviceName, deviceType };
    },

    async checkDeviceTrust() {
        if (!this.deviceId) {
            this.generateDeviceId();
        }

        try {
            const response = await this.apiRequest('/api/security/devices/check', {
                method: 'POST',
                body: JSON.stringify({ deviceId: this.deviceId })
            });

            this.deviceTrusted = response.isTrusted || false;
            return this.deviceTrusted;
        } catch (error) {
            console.error('Error checking device trust:', error);
            return false;
        }
    },

    async checkUserLockout() {
        try {
            const response = await this.apiRequest('/api/security/lockout/check');
            if (response.isLocked) {
                this.showAccountLockedScreen(response.lockedUntil);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error checking lockout:', error);
            return false;
        }
    },

    showAccountLockedScreen(lockedUntil) {
        this.hideAllAuthScreens();
        document.getElementById('account-locked-screen').classList.remove('hidden');
        
        if (lockedUntil) {
            this.startLockoutTimer(new Date(lockedUntil));
        }
    },

    startLockoutTimer(lockedUntil) {
        if (this.lockoutTimer) {
            clearInterval(this.lockoutTimer);
        }

        const updateTimer = () => {
            const now = new Date();
            const diff = lockedUntil - now;
            
            if (diff <= 0) {
                clearInterval(this.lockoutTimer);
                document.getElementById('lockout-time').textContent = '00:00';
                location.reload();
                return;
            }

            const minutes = Math.floor(diff / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            document.getElementById('lockout-time').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        };

        updateTimer();
        this.lockoutTimer = setInterval(updateTimer, 1000);
    },

    showDeviceBlockedScreen() {
        this.hideAllAuthScreens();
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('device-blocked-screen').classList.remove('hidden');
        
        document.getElementById('trust-device-btn').onclick = () => this.startDeviceVerification();
        document.getElementById('view-readonly-btn').onclick = () => this.enterReadOnlyMode();
    },

    async connectTelegramWallet() {
        return new Promise((resolve) => {
            if (!this.tonConnectUI) {
                this.showToast('TON Connect no disponible', 'error');
                resolve(null);
                return;
            }

            if (this.connectedWallet) {
                const address = this.connectedWallet.account?.address;
                if (address) {
                    const friendlyAddress = this.rawAddressToUserFriendly(address);
                    resolve(friendlyAddress);
                    return;
                }
            }

            const unsubscribe = this.tonConnectUI.onStatusChange((wallet) => {
                if (wallet) {
                    const address = wallet.account?.address;
                    if (address) {
                        const friendlyAddress = this.rawAddressToUserFriendly(address);
                        this.connectedWallet = wallet;
                        unsubscribe();
                        resolve(friendlyAddress);
                    }
                }
            });

            this.tonConnectUI.openModal().catch((error) => {
                console.error('Error opening TON Connect modal:', error);
                unsubscribe();
                resolve(null);
            });

            setTimeout(() => {
                unsubscribe();
                if (!this.connectedWallet) {
                    resolve(null);
                }
            }, 120000);
        });
    },

    showWrongWalletScreen(expectedHint, connectedAddress, attemptsRemaining) {
        this.hideAllAuthScreens();
        document.getElementById('wrong-wallet-screen').classList.remove('hidden');
        
        document.getElementById('expected-wallet-hint').textContent = expectedHint;
        document.getElementById('connected-wallet-hint').textContent = 
            connectedAddress.substring(0, 8) + '...' + connectedAddress.substring(connectedAddress.length - 4);
        document.getElementById('attempts-remaining').textContent = attemptsRemaining;
        
        if (attemptsRemaining <= 1) {
            document.getElementById('attempts-warning').style.background = 'rgba(252, 129, 129, 0.2)';
        }
        
        document.getElementById('retry-wallet-btn').onclick = () => this.startDeviceVerification();
        document.getElementById('cancel-wallet-btn').onclick = () => this.showDeviceBlockedScreen();
    },

    async startDeviceVerification() {
        try {
            const walletAddress = await this.connectTelegramWallet();
            if (!walletAddress) {
                this.showToast('No se pudo conectar la wallet', 'error');
                return;
            }

            const result = await this.validateWalletForDevice(walletAddress);
            
            if (result.is_locked) {
                this.showAccountLockedScreen(result.locked_until);
                return;
            }

            if (result.is_wrong_wallet) {
                this.showWrongWalletScreen(
                    result.registered_wallet_hint,
                    walletAddress,
                    result.attempts_remaining
                );
                return;
            }

            if (result.success) {
                this.walletVerified = true;
                this.connectedWalletAddress = walletAddress;
                
                const has2FA = await this.check2FARequired();
                if (has2FA) {
                    this.showAddDeviceStep(2);
                } else {
                    this.showAddDeviceStep(3);
                }
            }
        } catch (error) {
            console.error('Error in device verification:', error);
            this.showToast('Error en la verificacion', 'error');
        }
    },

    async validateWalletForDevice(walletAddress) {
        try {
            const response = await this.apiRequest('/api/security/wallet/validate', {
                method: 'POST',
                body: JSON.stringify({
                    walletAddress: walletAddress,
                    deviceId: this.deviceId
                })
            });
            return response;
        } catch (error) {
            console.error('Error validating wallet:', error);
            throw error;
        }
    },

    async check2FARequired() {
        try {
            const response = await this.apiRequest('/api/2fa/status');
            return response.enabled || false;
        } catch (error) {
            return false;
        }
    },

    showAddDeviceStep(step) {
        document.getElementById('add-device-modal').classList.remove('hidden');
        
        document.querySelectorAll('.add-device-content').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.step-item').forEach(el => {
            el.classList.remove('active', 'completed');
        });
        
        for (let i = 1; i < step; i++) {
            document.querySelector(`.step-item[data-step="${i}"]`).classList.add('completed');
        }
        document.querySelector(`.step-item[data-step="${step}"]`).classList.add('active');
        
        document.getElementById(`add-device-step-${step}`).classList.remove('hidden');
        
        if (step === 2) {
            document.getElementById('add-device-verify-2fa').onclick = () => this.verifyDeviceTwoFA();
        } else if (step === 3) {
            document.getElementById('add-device-confirm').onclick = () => this.confirmAddDevice();
        }
    },

    async verifyDeviceTwoFA() {
        const code = document.getElementById('add-device-2fa-code').value;
        if (!code || code.length !== 6) {
            this.showToast('Ingresa un codigo de 6 digitos', 'error');
            return;
        }

        try {
            const response = await this.apiRequest('/api/2fa/verify', {
                method: 'POST',
                body: JSON.stringify({ code })
            });

            if (response.success) {
                this.twoFAVerified = true;
                this.showAddDeviceStep(3);
            } else {
                this.showToast(response.error || 'Codigo incorrecto', 'error');
            }
        } catch (error) {
            this.showToast('Error al verificar codigo', 'error');
        }
    },

    async confirmAddDevice() {
        const deviceName = document.getElementById('add-device-name').value || 'Mi dispositivo';
        const { deviceType } = this.getDeviceInfo();

        try {
            const response = await this.apiRequest('/api/security/devices/add', {
                method: 'POST',
                body: JSON.stringify({
                    deviceId: this.deviceId,
                    deviceName: deviceName,
                    deviceType: deviceType,
                    walletVerified: this.walletVerified,
                    twofaVerified: this.twoFAVerified || !await this.check2FARequired()
                })
            });

            if (response.success) {
                this.deviceTrusted = true;
                document.getElementById('add-device-modal').classList.add('hidden');
                this.hideAllAuthScreens();
                document.getElementById('main-app').classList.remove('hidden');
                this.showToast('Dispositivo agregado correctamente', 'success');
                this.loadSecurityStatus();
            } else {
                this.showToast(response.error || 'Error al agregar dispositivo', 'error');
            }
        } catch (error) {
            this.showToast('Error al agregar dispositivo', 'error');
        }
    },

    enterReadOnlyMode() {
        this.readOnlyMode = true;
        this.hideAllAuthScreens();
        document.getElementById('main-app').classList.remove('hidden');
        this.showToast('Modo lectura - Algunas funciones estan deshabilitadas', 'warning');
        
        const walletNav = document.querySelector('[data-page="wallet"]');
        if (walletNav) {
            walletNav.addEventListener('click', (e) => {
                if (this.readOnlyMode && !this.deviceTrusted) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showDeviceBlockedScreen();
                }
            }, true);
        }
    },

    async loadSecurityStatus() {
        try {
            const response = await this.apiRequest('/api/security/status');
            if (response.success) {
                this.securityStatus = response;
                this.updateSecurityWidget(response);
            }
        } catch (error) {
            console.error('Error loading security status:', error);
        }
    },

    updateSecurityWidget(status) {
        const scoreFill = document.getElementById('security-score-fill');
        const scoreText = document.getElementById('security-score-text');
        const statusTitle = document.getElementById('security-status-title');
        
        if (scoreFill) {
            scoreFill.style.width = `${status.security_score}%`;
            scoreFill.className = 'security-score-fill';
            if (status.security_score >= 80) {
                scoreFill.classList.add('high');
            } else if (status.security_score >= 50) {
                scoreFill.classList.add('medium');
            } else {
                scoreFill.classList.add('low');
            }
        }
        
        if (scoreText) {
            scoreText.textContent = `Nivel: ${status.security_level}`;
        }
        
        if (statusTitle) {
            if (status.security_score >= 80) {
                statusTitle.textContent = 'Tu cuenta esta bien protegida';
            } else if (status.security_score >= 50) {
                statusTitle.textContent = 'Tu cuenta necesita mas proteccion';
            } else {
                statusTitle.textContent = 'Tu cuenta tiene riesgo de seguridad';
            }
        }
        
        const walletIndicator = document.querySelector('#indicator-wallet .indicator-status');
        if (walletIndicator) {
            walletIndicator.textContent = status.wallet_connected ? 'Activa' : 'No';
            walletIndicator.className = 'indicator-status ' + (status.wallet_connected ? 'active' : 'pending');
        }
        
        const tfaIndicator = document.querySelector('#indicator-2fa .indicator-status');
        if (tfaIndicator) {
            tfaIndicator.textContent = status.two_factor_enabled ? 'Activo' : 'No';
            tfaIndicator.className = 'indicator-status ' + (status.two_factor_enabled ? 'active' : 'pending');
        }
        
        const devicesIndicator = document.querySelector('#indicator-devices .indicator-status');
        if (devicesIndicator) {
            devicesIndicator.textContent = `${status.trusted_devices_count}/${status.max_devices}`;
            devicesIndicator.className = 'indicator-status ' + (status.trusted_devices_count > 0 ? 'active' : 'pending');
        }

        const backupBadge = document.getElementById('backup-wallet-badge');
        if (backupBadge) {
            if (status.has_backup_wallet) {
                backupBadge.textContent = 'Configurada';
                backupBadge.classList.add('configured');
            } else {
                backupBadge.textContent = 'No configurada';
                backupBadge.classList.remove('configured');
            }
        }
    },

    async loadTrustedDevices() {
        try {
            const response = await this.apiRequest('/api/security/devices');
            if (response.success) {
                this.renderTrustedDevices(response.devices);
            }
        } catch (error) {
            console.error('Error loading trusted devices:', error);
        }
    },

    renderTrustedDevices(devices) {
        const container = document.getElementById('trusted-devices-list');
        if (!container) return;

        if (!devices || devices.length === 0) {
            container.innerHTML = `
                <div class="devices-empty">
                    <div class="devices-empty-icon">📱</div>
                    <p>No tienes dispositivos de confianza</p>
                </div>
            `;
            return;
        }

        container.innerHTML = devices.map(device => {
            const isCurrent = device.device_id === this.deviceId;
            const icon = this.getDeviceIcon(device.device_type);
            const lastUsed = device.last_used_at ? this.formatRelativeTime(device.last_used_at) : 'Nunca';
            
            return `
                <div class="device-item ${isCurrent ? 'current' : ''}" data-device-id="${device.device_id}">
                    <div class="device-item-icon">${icon}</div>
                    <div class="device-item-info">
                        <div class="device-item-name">
                            ${device.device_name}
                            ${isCurrent ? '<span class="current-badge">Este dispositivo</span>' : ''}
                        </div>
                        <div class="device-item-meta">Ultimo uso: ${lastUsed}</div>
                    </div>
                    ${!isCurrent ? `<button class="device-item-remove" onclick="App.removeDevice('${device.device_id}')">&times;</button>` : ''}
                </div>
            `;
        }).join('');
    },

    getDeviceIconEmoji(deviceType) {
        const type = (deviceType || '').toLowerCase();
        
        if (type.includes('ios') || type.includes('iphone') || type.includes('android') || type.includes('mobile')) {
            return '📱';
        }
        if (type.includes('ipad') || type.includes('tablet')) {
            return '📲';
        }
        if (type.includes('mac') || type.includes('windows') || type.includes('linux') || type.includes('desktop')) {
            return '💻';
        }
        
        const iconMap = {
            'ios': '📱',
            'android': '📱',
            'windows': '💻',
            'mac': '💻',
            'linux': '🖥️'
        };
        
        return iconMap[type] || '📱';
    },

    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Ahora';
        if (diffMins < 60) return `Hace ${diffMins} min`;
        if (diffHours < 24) return `Hace ${diffHours}h`;
        if (diffDays < 7) return `Hace ${diffDays} dias`;
        return date.toLocaleDateString('es-ES');
    },

    async removeDevice(deviceId) {
        const has2FA = await this.check2FARequired();
        
        if (has2FA) {
            const code = prompt('Ingresa tu codigo 2FA para eliminar el dispositivo:');
            if (!code || code.length !== 6) {
                this.showToast('Codigo 2FA invalido', 'error');
                return;
            }

            try {
                const response = await this.apiRequest('/api/security/devices/remove', {
                    method: 'POST',
                    body: JSON.stringify({
                        deviceId: deviceId,
                        twofaCode: code
                    })
                });

                if (response.success) {
                    this.showToast('Dispositivo eliminado', 'success');
                    this.loadTrustedDevices();
                    this.loadSecurityStatus();
                } else {
                    this.showToast(response.error || 'Error al eliminar', 'error');
                }
            } catch (error) {
                this.showToast('Error al eliminar dispositivo', 'error');
            }
        } else {
            if (confirm('¿Estas seguro de eliminar este dispositivo?')) {
                try {
                    const response = await this.apiRequest('/api/security/devices/remove', {
                        method: 'POST',
                        body: JSON.stringify({ deviceId: deviceId })
                    });

                    if (response.success) {
                        this.showToast('Dispositivo eliminado', 'success');
                        this.loadTrustedDevices();
                        this.loadSecurityStatus();
                    } else {
                        this.showToast(response.error || 'Error al eliminar', 'error');
                    }
                } catch (error) {
                    this.showToast('Error al eliminar dispositivo', 'error');
                }
            }
        }
    },

    async loadSecurityActivity() {
        try {
            const response = await this.apiRequest('/api/security/activity?limit=10');
            if (response.success) {
                this.renderSecurityActivity(response.activities);
            }
        } catch (error) {
            console.error('Error loading security activity:', error);
        }
    },

    renderSecurityActivity(activities) {
        const container = document.getElementById('security-activity-list');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = '<div class="activity-loading">No hay actividad reciente</div>';
            return;
        }

        const activityIcons = {
            'WALLET_REGISTERED': { icon: '💳', class: 'success' },
            'DEVICE_ADDED': { icon: '📱', class: 'success' },
            'DEVICE_REMOVED': { icon: '📱', class: 'warning' },
            'WALLET_FAILED_ATTEMPT': { icon: '⚠️', class: 'danger' },
            'USER_LOCKED': { icon: '🔒', class: 'danger' },
            '2FA_ENABLED': { icon: '🔐', class: 'success' },
            'ADMIN_DEVICE_REMOVED': { icon: '👮', class: 'warning' }
        };

        container.innerHTML = activities.map(activity => {
            const config = activityIcons[activity.type] || { icon: '📝', class: '' };
            const time = this.formatRelativeTime(activity.created_at);
            
            return `
                <div class="activity-item">
                    <div class="activity-item-icon ${config.class}">${config.icon}</div>
                    <div class="activity-item-content">
                        <div class="activity-item-desc">${activity.description}</div>
                        <div class="activity-item-time">${time}</div>
                    </div>
                </div>
            `;
        }).join('');
    },

    setupSecurityEventListeners() {
        document.getElementById('add-device-btn')?.addEventListener('click', () => {
            if (this.walletVerified) {
                this.showAddDeviceStep(2);
            } else {
                this.startDeviceVerification();
            }
        });

        document.getElementById('close-add-device-modal')?.addEventListener('click', () => {
            document.getElementById('add-device-modal').classList.add('hidden');
        });

        document.getElementById('logout-all-devices-btn')?.addEventListener('click', () => {
            this.logoutAllDevices();
        });

        document.getElementById('setup-backup-wallet-btn')?.addEventListener('click', () => {
            this.setupBackupWallet();
        });

        document.getElementById('see-all-activity-btn')?.addEventListener('click', () => {
            this.showAllSecurityActivity();
        });

        document.getElementById('contact-support-btn')?.addEventListener('click', () => {
            this.showToast('Contacta a @bunk3r_support en Telegram', 'info');
        });
    },

    async logoutAllDevices() {
        const has2FA = await this.check2FARequired();
        let code = '';
        
        if (has2FA) {
            code = prompt('Ingresa tu codigo 2FA para cerrar sesion en todos los dispositivos:');
            if (!code || code.length !== 6) {
                this.showToast('Codigo 2FA invalido', 'error');
                return;
            }
        }

        if (confirm('¿Estas seguro? Se cerrara sesion en todos los dispositivos excepto este.')) {
            try {
                const response = await this.apiRequest('/api/security/devices/remove-all', {
                    method: 'POST',
                    body: JSON.stringify({
                        currentDeviceId: this.deviceId,
                        twofaCode: code
                    })
                });

                if (response.success) {
                    this.showToast(`Sesion cerrada en ${response.removed_count} dispositivos`, 'success');
                    this.loadTrustedDevices();
                    this.loadSecurityStatus();
                } else {
                    this.showToast(response.error || 'Error al cerrar sesiones', 'error');
                }
            } catch (error) {
                this.showToast('Error al cerrar sesiones', 'error');
            }
        }
    },

    async setupBackupWallet() {
        const address = prompt('Ingresa la direccion de tu wallet de respaldo:');
        if (!address) return;

        try {
            const response = await this.apiRequest('/api/security/wallet/backup', {
                method: 'POST',
                body: JSON.stringify({ backupWallet: address })
            });

            if (response.success) {
                this.showToast('Wallet de respaldo configurada', 'success');
                this.loadSecurityStatus();
            } else {
                this.showToast(response.error || 'Error al configurar wallet', 'error');
            }
        } catch (error) {
            this.showToast('Error al configurar wallet de respaldo', 'error');
        }
    },

    async showAllSecurityActivity() {
        try {
            const response = await this.apiRequest('/api/security/activity?limit=50');
            if (response.success && response.activities) {
                const content = response.activities.map(a => 
                    `${a.created_at}: ${a.description}`
                ).join('\n');
                
                const modalContent = `
                    <div class="modal-header">
                        <span class="modal-title">Historial de Actividad</span>
                        <button class="modal-close" onclick="App.closeModal()">&times;</button>
                    </div>
                    <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
                        ${response.activities.map(activity => `
                            <div class="activity-item" style="padding: 12px 0; border-bottom: 1px solid var(--border-color);">
                                <div style="font-size: 13px; color: var(--text-primary);">${activity.description}</div>
                                <div style="font-size: 11px; color: var(--text-muted);">${this.formatDate(activity.created_at)}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
                this.showModal(modalContent);
            }
        } catch (error) {
            this.showToast('Error al cargar historial', 'error');
        }
    },

    hideAllAuthScreens() {
        const screens = [
            'loading-screen',
            'device-blocked-screen',
            'wrong-wallet-screen',
            'account-locked-screen',
            'setup-2fa-screen',
            'verify-2fa-screen'
        ];
        screens.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('hidden');
        });
    },

    async initSecuritySystem() {
        this.generateDeviceId();
        
        const isLocked = await this.checkUserLockout();
        if (isLocked) return false;

        const isTrusted = await this.checkDeviceTrust();
        this.deviceTrusted = isTrusted;

        this.setupSecurityEventListeners();

        if (this.user && !this._securityDataLoaded) {
            await Promise.all([
                this.loadSecurityStatus(),
                this.loadTrustedDevices(),
                this.loadSecurityActivity()
            ]);
            this._securityDataLoaded = true;
        }

        return true;
    },

    // ========================================
    // ADMIN PANEL FUNCTIONS
    // ========================================

    setupAdminEventListeners() {
        document.getElementById('admin-users-btn')?.addEventListener('click', () => this.openAdminModal('users'));
        document.getElementById('admin-bots-btn')?.addEventListener('click', () => this.openAdminModal('bots'));
        document.getElementById('admin-products-btn')?.addEventListener('click', () => this.openAdminModal('products'));
        document.getElementById('admin-transactions-btn')?.addEventListener('click', () => this.openAdminModal('transactions'));
        document.getElementById('admin-security-alerts-btn')?.addEventListener('click', () => this.openAdminModal('alerts'));
        document.getElementById('admin-activity-btn')?.addEventListener('click', () => this.openAdminModal('activity'));
        document.getElementById('admin-lockouts-btn')?.addEventListener('click', () => this.openAdminModal('lockouts'));
        document.getElementById('admin-settings-btn')?.addEventListener('click', () => this.openAdminModal('settings'));
        document.getElementById('admin-logs-btn')?.addEventListener('click', () => this.openAdminModal('logs'));

        document.getElementById('admin-users-search')?.addEventListener('input', (e) => {
            this.filterAdminUsers(e.target.value);
        });

        document.getElementById('admin-tx-filter')?.addEventListener('change', () => this.loadAdminTransactions());
        document.getElementById('admin-tx-period')?.addEventListener('change', () => this.loadAdminTransactions());
        document.getElementById('admin-activity-type')?.addEventListener('change', () => this.loadAdminActivity());
        document.getElementById('admin-logs-level')?.addEventListener('change', () => this.loadSystemLogs());
    },

    openAdminModal(type) {
        const modal = document.getElementById(`admin-${type}-modal`);
        if (modal) {
            modal.classList.remove('hidden');
            this.loadAdminModalData(type);
        }
    },

    closeAdminModal(type) {
        const modal = document.getElementById(`admin-${type}-modal`);
        if (modal) {
            modal.classList.add('hidden');
        }
    },

    async loadAdminModalData(type) {
        switch(type) {
            case 'users':
                await this.loadAdminUsers();
                break;
            case 'bots':
                await this.loadAdminBots();
                break;
            case 'products':
                await this.loadAdminProducts();
                break;
            case 'transactions':
                await this.loadAdminTransactions();
                break;
            case 'alerts':
                await this.loadAdminAlerts();
                break;
            case 'activity':
                await this.loadAdminActivity();
                break;
            case 'lockouts':
                await this.loadAdminLockouts();
                break;
            case 'settings':
                await this.loadAdminSettings();
                break;
            case 'logs':
                await this.loadSystemLogs();
                break;
        }
    },

    async loadAdminUsers() {
        const listEl = document.getElementById('admin-users-list');
        const countEl = document.getElementById('admin-users-count');
        
        try {
            const response = await this.apiRequest('/api/admin/users');
            
            if (response.success && response.users) {
                this.adminUsers = response.users;
                countEl.textContent = response.users.length;
                this.renderAdminUsers(response.users);
            } else {
                listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">👥</div><p>No hay usuarios registrados</p></div>';
            }
        } catch (error) {
            console.error('Error loading admin users:', error);
            listEl.innerHTML = '<div class="admin-loading">Error al cargar usuarios</div>';
        }
    },

    renderAdminUsers(users) {
        const listEl = document.getElementById('admin-users-list');
        
        if (!users || users.length === 0) {
            listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">👥</div><p>No hay usuarios registrados</p></div>';
            return;
        }
        
        listEl.innerHTML = users.map(user => `
            <div class="admin-user-card" onclick="App.showUserDetail('${this.sanitizeForJs(user.id)}')">
                <div class="admin-user-avatar">${this.escapeHtml((user.first_name || user.username || 'U')[0].toUpperCase())}</div>
                <div class="admin-user-info">
                    <div class="admin-user-name">${this.escapeHtml(user.first_name || 'Usuario')} ${this.escapeHtml(user.last_name || '')}</div>
                    <div class="admin-user-username">@${this.escapeHtml(user.username || 'sin_username')}</div>
                    <div class="admin-user-meta">
                        <span class="admin-user-badge ${user.is_active ? 'active' : ''}">${user.is_active ? 'Activo' : 'Inactivo'}</span>
                        <span class="admin-user-badge credits">${parseInt(user.credits) || 0} creditos</span>
                    </div>
                </div>
            </div>
        `).join('');
    },

    filterAdminUsers(query) {
        if (!this.adminUsers) return;
        
        const filtered = this.adminUsers.filter(user => {
            const searchStr = `${user.first_name} ${user.last_name} ${user.username}`.toLowerCase();
            return searchStr.includes(query.toLowerCase());
        });
        
        this.renderAdminUsers(filtered);
    },

    async showUserDetail(userId) {
        const modal = document.getElementById('admin-user-detail-modal');
        const content = document.getElementById('admin-user-detail-content');
        
        if (!modal || !content) return;
        
        modal.classList.remove('hidden');
        content.innerHTML = '<div class="admin-loading">Cargando...</div>';
        
        try {
            const response = await this.apiRequest(`/api/admin/user/${userId}`);
            
            if (response.success && response.user) {
                const user = response.user;
                const safeUserId = this.sanitizeForJs(userId);
                content.innerHTML = `
                    <div class="admin-user-detail-header">
                        <div class="admin-user-detail-avatar">${this.escapeHtml((user.first_name || user.username || 'U')[0].toUpperCase())}</div>
                        <div class="admin-user-detail-name">${this.escapeHtml(user.first_name || 'Usuario')} ${this.escapeHtml(user.last_name || '')}</div>
                        <div class="admin-user-detail-username">@${this.escapeHtml(user.username || 'sin_username')}</div>
                        <div class="admin-user-detail-stats">
                            <div class="admin-user-stat">
                                <div class="admin-user-stat-value">${parseInt(user.credits) || 0}</div>
                                <div class="admin-user-stat-label">Creditos</div>
                            </div>
                            <div class="admin-user-stat">
                                <div class="admin-user-stat-value">${parseInt(user.level) || 1}</div>
                                <div class="admin-user-stat-label">Nivel</div>
                            </div>
                            <div class="admin-user-stat">
                                <div class="admin-user-stat-value">${parseInt(user.total_transactions) || 0}</div>
                                <div class="admin-user-stat-label">Transacciones</div>
                            </div>
                        </div>
                    </div>
                    <div class="admin-user-actions">
                        <button class="admin-user-action-btn primary" onclick="App.addCreditsToUser('${safeUserId}')">Agregar Creditos</button>
                        <button class="admin-user-action-btn danger" onclick="App.blockUser('${safeUserId}')">${user.is_active ? 'Bloquear' : 'Desbloquear'}</button>
                    </div>
                    <div class="admin-user-section">
                        <div class="admin-user-section-title">Informacion</div>
                        <div class="admin-setting-item">
                            <div class="setting-info">
                                <span class="setting-label">Telegram ID</span>
                            </div>
                            <span style="color: var(--text-muted);">${this.escapeHtml(user.telegram_id || 'N/A')}</span>
                        </div>
                        <div class="admin-setting-item">
                            <div class="setting-info">
                                <span class="setting-label">Wallet</span>
                            </div>
                            <span style="color: var(--text-muted); font-size: 11px;">${user.wallet_address ? this.escapeHtml(user.wallet_address.substring(0, 20)) + '...' : 'No conectada'}</span>
                        </div>
                        <div class="admin-setting-item">
                            <div class="setting-info">
                                <span class="setting-label">Registrado</span>
                            </div>
                            <span style="color: var(--text-muted);">${this.formatDate(user.created_at)}</span>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            content.innerHTML = '<div class="admin-loading">Error al cargar usuario</div>';
        }
    },

    async addCreditsToUser(userId) {
        const amount = prompt('Cantidad de creditos a agregar:');
        if (!amount || isNaN(amount)) return;
        
        try {
            const response = await this.apiRequest('/api/admin/user/credits', {
                method: 'POST',
                body: JSON.stringify({ userId, amount: parseInt(amount) })
            });
            
            if (response.success) {
                this.showToast(`Creditos agregados correctamente`, 'success');
                this.showUserDetail(userId);
            } else {
                this.showToast(response.error || 'Error al agregar creditos', 'error');
            }
        } catch (error) {
            this.showToast('Error al agregar creditos', 'error');
        }
    },

    async blockUser(userId) {
        if (!confirm('¿Estas seguro de cambiar el estado de este usuario?')) return;
        
        try {
            const response = await this.apiRequest('/api/admin/user/toggle-status', {
                method: 'POST',
                body: JSON.stringify({ userId })
            });
            
            if (response.success) {
                this.showToast('Estado actualizado', 'success');
                this.loadAdminUsers();
                this.closeAdminModal('user-detail');
            }
        } catch (error) {
            this.showToast('Error al actualizar estado', 'error');
        }
    },

    async loadAdminBots() {
        const listEl = document.getElementById('admin-bots-list');
        
        try {
            const response = await this.apiRequest('/api/admin/bots');
            
            if (response.success && response.bots) {
                if (response.bots.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">🤖</div><p>No hay bots configurados</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.bots.map(bot => `
                    <div class="admin-bot-card">
                        <div class="admin-bot-icon">${this.escapeHtml(bot.icon || '🤖')}</div>
                        <div class="admin-bot-info">
                            <div class="admin-bot-name">${this.escapeHtml(bot.bot_name)}</div>
                            <div class="admin-bot-type">${this.escapeHtml(bot.bot_type)}</div>
                            <div class="admin-bot-desc">${this.escapeHtml(bot.description || 'Sin descripcion')}</div>
                        </div>
                        <div class="admin-bot-stats">
                            <div class="admin-bot-price">${parseInt(bot.price) || 0} creditos</div>
                            <div class="admin-bot-users">${parseInt(bot.users_count) || 0} usuarios</div>
                        </div>
                        <div class="admin-bot-actions">
                            <button class="edit-btn" onclick="App.editBot(${parseInt(bot.id)})">Editar</button>
                            <button class="delete-btn" onclick="App.deleteBot(${parseInt(bot.id)})">Eliminar</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar bots</div>';
        }
    },

    showAddBotForm() {
        const content = `
            <div class="modal-header">
                <span class="modal-title">Nuevo Bot</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Nombre del Bot</label>
                    <input type="text" id="new-bot-name" placeholder="Ej: Bot Trading Pro">
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select id="new-bot-type">
                        <option value="trading">Trading</option>
                        <option value="signals">Señales</option>
                        <option value="automation">Automatizacion</option>
                        <option value="analytics">Analytics</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Descripcion</label>
                    <textarea id="new-bot-desc" placeholder="Descripcion del bot..."></textarea>
                </div>
                <div class="form-group">
                    <label>Precio (creditos)</label>
                    <input type="number" id="new-bot-price" value="100" min="0">
                </div>
                <div class="form-group">
                    <label>Icono (emoji)</label>
                    <input type="text" id="new-bot-icon" value="🤖" maxlength="2">
                </div>
                <button class="btn btn-primary" onclick="App.createBot()" style="width: 100%; margin-top: 16px;">Crear Bot</button>
            </div>
        `;
        this.showModal(content);
    },

    async createBot() {
        const name = document.getElementById('new-bot-name').value;
        const type = document.getElementById('new-bot-type').value;
        const description = document.getElementById('new-bot-desc').value;
        const price = document.getElementById('new-bot-price').value;
        const icon = document.getElementById('new-bot-icon').value;
        
        if (!name) {
            this.showToast('Ingresa un nombre para el bot', 'error');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/admin/bots', {
                method: 'POST',
                body: JSON.stringify({ name, type, description, price: parseInt(price), icon })
            });
            
            if (response.success) {
                this.showToast('Bot creado correctamente', 'success');
                this.closeModal();
                this.loadAdminBots();
            } else {
                this.showToast(response.error || 'Error al crear bot', 'error');
            }
        } catch (error) {
            this.showToast('Error al crear bot', 'error');
        }
    },

    async deleteBot(botId) {
        if (!confirm('¿Estas seguro de eliminar este bot?')) return;
        
        try {
            const response = await this.apiRequest(`/api/admin/bots/${botId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Bot eliminado', 'success');
                this.loadAdminBots();
            }
        } catch (error) {
            this.showToast('Error al eliminar bot', 'error');
        }
    },

    async loadAdminProducts() {
        const listEl = document.getElementById('admin-products-list');
        
        try {
            const response = await this.apiRequest('/api/admin/products');
            
            if (response.success && response.products) {
                if (response.products.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">🛒</div><p>No hay productos configurados</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.products.map(product => `
                    <div class="admin-product-card">
                        <div class="admin-product-image">${this.escapeHtml(product.image_url || product.icon || '')}</div>
                        <div class="admin-product-info">
                            <div class="admin-product-name">${this.escapeHtml(product.title || product.name || 'Sin titulo')}</div>
                            <div class="admin-product-category">${this.escapeHtml(product.category || 'Sin categoria')}</div>
                            <div class="admin-product-price">${parseFloat(product.price) || 0} creditos</div>
                            <div class="admin-product-stock">Stock: ${product.stock !== null ? product.stock : 'Ilimitado'}</div>
                        </div>
                        <div class="admin-product-actions">
                            <button class="delete-btn" onclick="App.deleteProduct(${parseInt(product.id)})">Eliminar</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar productos</div>';
        }
    },

    showAddProductForm() {
        const content = `
            <div class="modal-header">
                <span class="modal-title">Nuevo Producto</span>
                <button class="modal-close" onclick="App.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Titulo del Producto</label>
                    <input type="text" id="new-product-title" placeholder="Ej: Pack Premium">
                </div>
                <div class="form-group">
                    <label>Categoria</label>
                    <select id="new-product-category">
                        <option value="digital">Digital</option>
                        <option value="subscription">Suscripcion</option>
                        <option value="service">Servicio</option>
                        <option value="physical">Fisico</option>
                        <option value="general">General</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Descripcion</label>
                    <textarea id="new-product-desc" placeholder="Descripcion del producto..."></textarea>
                </div>
                <div class="form-group">
                    <label>Precio (creditos)</label>
                    <input type="number" id="new-product-price" value="100" min="0">
                </div>
                <div class="form-group">
                    <label>Stock</label>
                    <input type="number" id="new-product-stock" value="1" min="0">
                </div>
                <div class="form-group">
                    <label>Icono (emoji)</label>
                    <input type="text" id="new-product-icon" value="" maxlength="2">
                </div>
                <button class="btn btn-primary" onclick="App.createProduct()" style="width: 100%; margin-top: 16px;">Crear Producto</button>
            </div>
        `;
        this.showModal(content);
    },

    async createProduct() {
        const title = document.getElementById('new-product-title').value;
        const category = document.getElementById('new-product-category').value;
        const description = document.getElementById('new-product-desc').value;
        const price = document.getElementById('new-product-price').value;
        const stock = document.getElementById('new-product-stock').value;
        const icon = document.getElementById('new-product-icon').value;
        
        if (!title) {
            this.showToast('Ingresa un titulo para el producto', 'error');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/admin/products', {
                method: 'POST',
                body: JSON.stringify({ title, category, description, price: parseFloat(price), stock: parseInt(stock), icon })
            });
            
            if (response.success) {
                this.showToast('Producto creado correctamente', 'success');
                this.closeModal();
                this.loadAdminProducts();
            } else {
                this.showToast(response.error || 'Error al crear producto', 'error');
            }
        } catch (error) {
            this.showToast('Error al crear producto', 'error');
        }
    },

    async deleteProduct(productId) {
        if (!confirm('Estas seguro de eliminar este producto?')) return;
        
        try {
            const response = await this.apiRequest(`/api/admin/products/${productId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Producto eliminado', 'success');
                this.loadAdminProducts();
            }
        } catch (error) {
            this.showToast('Error al eliminar producto', 'error');
        }
    },

    async loadAdminTransactions() {
        const listEl = document.getElementById('admin-transactions-list');
        const countEl = document.getElementById('admin-transactions-count');
        const filter = document.getElementById('admin-tx-filter')?.value || 'all';
        const period = document.getElementById('admin-tx-period')?.value || 'all';
        
        try {
            const response = await this.apiRequest(`/api/admin/transactions?filter=${filter}&period=${period}`);
            
            if (response.success) {
                countEl.textContent = response.transactions?.length || 0;
                
                document.getElementById('tx-total-deposits').textContent = `${response.totalDeposits || 0} TON`;
                document.getElementById('tx-total-withdrawals').textContent = `${response.totalWithdrawals || 0} TON`;
                
                if (!response.transactions || response.transactions.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">💳</div><p>No hay transacciones</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.transactions.map(tx => `
                    <div class="admin-tx-card">
                        <div class="admin-tx-icon ${this.escapeAttribute(tx.type)}">${this.getTxIcon(tx.type)}</div>
                        <div class="admin-tx-info">
                            <div class="admin-tx-type">${this.getTxTypeName(tx.type)}</div>
                            <div class="admin-tx-user">@${this.escapeHtml(tx.username || 'usuario')}</div>
                        </div>
                        <div class="admin-tx-amount">
                            <div class="amount ${tx.type === 'deposit' ? 'positive' : 'negative'}">${tx.type === 'deposit' ? '+' : '-'}${parseFloat(tx.amount) || 0} TON</div>
                            <div class="time">${this.formatDate(tx.created_at)}</div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar transacciones</div>';
        }
    },

    getTxIcon(type) {
        const icons = { deposit: '📥', withdrawal: '📤', purchase: '🛒', transfer: '↔️' };
        return icons[type] || '💰';
    },

    getTxTypeName(type) {
        const names = { deposit: 'Deposito', withdrawal: 'Retiro', purchase: 'Compra', transfer: 'Transferencia' };
        return names[type] || type;
    },

    async loadAdminAlerts() {
        const listEl = document.getElementById('admin-alerts-list');
        const countEl = document.getElementById('admin-alerts-count');
        
        try {
            const response = await this.apiRequest('/api/admin/security/alerts');
            
            if (response.success && response.alerts) {
                countEl.textContent = response.alerts.filter(a => !a.resolved).length;
                
                if (response.alerts.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">✅</div><p>No hay alertas de seguridad</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.alerts.map(alert => `
                    <div class="admin-alert-card ${alert.resolved ? 'resolved' : ''}">
                        <div class="admin-alert-header">
                            <span class="admin-alert-type">${this.escapeHtml(alert.alert_type || 'Alerta')}</span>
                            <span class="admin-alert-time">${this.formatDate(alert.created_at)}</span>
                        </div>
                        <div class="admin-alert-desc">${this.escapeHtml(alert.description || 'Sin descripcion')}</div>
                        ${!alert.resolved ? `
                            <div class="admin-alert-actions">
                                <button class="admin-alert-btn resolve" onclick="App.resolveAlert(${parseInt(alert.id)})">Resolver</button>
                                <button class="admin-alert-btn view" onclick="App.viewAlertDetails(${parseInt(alert.id)})">Ver mas</button>
                            </div>
                        ` : '<span style="font-size: 11px; color: var(--accent-success);">Resuelta</span>'}
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar alertas</div>';
        }
    },

    async resolveAlert(alertId) {
        try {
            const response = await this.apiRequest(`/api/admin/security/alerts/${alertId}/resolve`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Alerta resuelta', 'success');
                this.loadAdminAlerts();
                this.loadAdminStats();
            }
        } catch (error) {
            this.showToast('Error al resolver alerta', 'error');
        }
    },

    viewAlertDetails(alertId) {
        this.showToast('Detalles de alerta ' + this.escapeHtml(String(alertId)), 'info');
    },

    async loadAdminActivity() {
        const listEl = document.getElementById('admin-activity-list');
        const typeFilter = document.getElementById('admin-activity-type')?.value || 'all';
        
        try {
            const response = await this.apiRequest(`/api/admin/activity?type=${typeFilter}`);
            
            if (response.success && response.activities) {
                if (response.activities.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">📊</div><p>No hay actividad reciente</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.activities.map(activity => `
                    <div class="admin-activity-item">
                        <div class="admin-activity-icon">${this.getActivityIcon(activity.type)}</div>
                        <div class="admin-activity-content">
                            <div class="admin-activity-text">${this.escapeHtml(activity.description)}</div>
                            <div class="admin-activity-meta">
                                ${activity.username ? `@${this.escapeHtml(activity.username)} · ` : ''}${this.formatDate(activity.created_at)}
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar actividad</div>';
        }
    },

    getActivityIcon(type) {
        const icons = { login: '🔐', wallet: '💰', security: '🛡️', transaction: '💳', bot: '🤖' };
        return icons[type] || '📝';
    },

    async loadAdminLockouts() {
        const listEl = document.getElementById('admin-lockouts-list');
        const countEl = document.getElementById('admin-lockouts-count');
        
        try {
            const response = await this.apiRequest('/api/admin/lockouts');
            
            if (response.success && response.lockouts) {
                countEl.textContent = response.lockouts.length;
                
                if (response.lockouts.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">🔓</div><p>No hay usuarios bloqueados</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.lockouts.map(lockout => `
                    <div class="admin-lockout-card">
                        <div class="admin-lockout-info">
                            <div class="admin-lockout-user">@${this.escapeHtml(lockout.username || 'usuario')}</div>
                            <div class="admin-lockout-reason">${this.escapeHtml(lockout.reason || 'Sin razon')}</div>
                            <div class="admin-lockout-time">Bloqueado: ${this.formatDate(lockout.locked_until)}</div>
                        </div>
                        <button class="admin-unlock-btn" onclick="App.unlockUser('${this.sanitizeForJs(lockout.user_id)}')">Desbloquear</button>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar bloqueos</div>';
        }
    },

    async unlockUser(userId) {
        if (!confirm('¿Desbloquear este usuario?')) return;
        
        try {
            const response = await this.apiRequest('/api/admin/unlock-user', {
                method: 'POST',
                body: JSON.stringify({ userId })
            });
            
            if (response.success) {
                this.showToast('Usuario desbloqueado', 'success');
                this.loadAdminLockouts();
            }
        } catch (error) {
            this.showToast('Error al desbloquear usuario', 'error');
        }
    },

    async loadAdminSettings() {
        try {
            const response = await this.apiRequest('/api/admin/settings');
            
            if (response.success) {
                document.getElementById('setting-maintenance').checked = response.maintenanceMode || false;
                document.getElementById('setting-registration').checked = response.registrationOpen !== false;
                document.getElementById('setting-wallet-address').textContent = response.merchantWallet || 'No configurada';
                document.getElementById('setting-min-deposit').value = response.minDeposit || 1;
                document.getElementById('setting-email-alerts').checked = response.emailAlerts !== false;
                document.getElementById('setting-telegram-alerts').checked = response.telegramAlerts !== false;
            }
        } catch (error) {
            console.error('Error loading admin settings:', error);
        }
    },

    async saveSystemSettings() {
        const settings = {
            maintenanceMode: document.getElementById('setting-maintenance').checked,
            registrationOpen: document.getElementById('setting-registration').checked,
            minDeposit: parseFloat(document.getElementById('setting-min-deposit').value),
            emailAlerts: document.getElementById('setting-email-alerts').checked,
            telegramAlerts: document.getElementById('setting-telegram-alerts').checked
        };
        
        try {
            const response = await this.apiRequest('/api/admin/settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            
            if (response.success) {
                this.showToast('Configuracion guardada', 'success');
            } else {
                this.showToast(response.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            this.showToast('Error al guardar configuracion', 'error');
        }
    },

    copyWalletAddress() {
        const address = document.getElementById('setting-wallet-address').textContent;
        if (address && address !== 'No configurada' && address !== 'Cargando...') {
            navigator.clipboard.writeText(address);
            this.showToast('Direccion copiada', 'success');
        }
    },

    async loadSystemLogs() {
        const listEl = document.getElementById('admin-logs-list');
        const levelFilter = document.getElementById('admin-logs-level')?.value || 'all';
        
        try {
            const response = await this.apiRequest(`/api/admin/logs?level=${levelFilter}`);
            
            if (response.success && response.logs) {
                if (response.logs.length === 0) {
                    listEl.innerHTML = '<div class="admin-empty-state"><div class="empty-icon">📝</div><p>No hay logs disponibles</p></div>';
                    return;
                }
                
                listEl.innerHTML = response.logs.map(log => `
                    <div class="admin-log-entry">
                        <span class="log-time">${this.escapeHtml(log.time || '')}</span>
                        <span class="log-level ${this.escapeAttribute(log.level || 'info')}">${this.escapeHtml((log.level || 'INFO').toUpperCase())}</span>
                        <span class="log-message">${this.escapeHtml(log.message || '')}</span>
                    </div>
                `).join('');
            }
        } catch (error) {
            listEl.innerHTML = '<div class="admin-loading">Error al cargar logs</div>';
        }
    },

    editBot(botId) {
        this.showToast('Editar bot ' + this.escapeHtml(String(botId)), 'info');
    },

    notificationsState: {
        notifications: [],
        offset: 0,
        limit: 20,
        hasMore: true,
        currentFilter: 'all',
        loading: false
    },

    async loadNotifications(filter = 'all', append = false) {
        if (this.notificationsState.loading) return;
        
        const listEl = document.getElementById('notifications-list');
        const emptyEl = document.getElementById('notifications-empty');
        
        if (!listEl) return;
        
        if (!append) {
            this.notificationsState.offset = 0;
            this.notificationsState.currentFilter = filter;
            listEl.innerHTML = `
                <div class="notifications-loading">
                    <div class="skeleton-card"></div>
                    <div class="skeleton-card"></div>
                    <div class="skeleton-card"></div>
                </div>
            `;
        }
        
        this.notificationsState.loading = true;
        
        try {
            let url = `/api/notifications?limit=${this.notificationsState.limit}&offset=${this.notificationsState.offset}`;
            if (filter !== 'all') {
                url += `&filter=${filter}`;
            }
            
            const response = await this.apiRequest(url);
            
            if (response.success) {
                const notifications = response.notifications || [];
                
                if (!append) {
                    this.notificationsState.notifications = notifications;
                } else {
                    this.notificationsState.notifications = [...this.notificationsState.notifications, ...notifications];
                }
                
                this.notificationsState.hasMore = notifications.length >= this.notificationsState.limit;
                this.notificationsState.offset += notifications.length;
                
                this.renderNotifications();
                
                if (this.notificationsState.notifications.length === 0) {
                    listEl.innerHTML = '';
                    emptyEl?.classList.remove('hidden');
                } else {
                    emptyEl?.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            listEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><h4>Error al cargar notificaciones</h4></div>';
        } finally {
            this.notificationsState.loading = false;
        }
    },

    renderNotifications() {
        const listEl = document.getElementById('notifications-list');
        if (!listEl) return;
        
        const notifications = this.notificationsState.notifications;
        
        if (notifications.length === 0) {
            listEl.innerHTML = '';
            return;
        }
        
        let html = notifications.map(notif => this.renderNotificationItem(notif)).join('');
        
        if (this.notificationsState.hasMore) {
            html += `<button class="load-more-notifications" onclick="App.loadMoreNotifications()">Cargar mas notificaciones</button>`;
        }
        
        listEl.innerHTML = html;
    },

    renderNotificationItem(notif) {
        const typeIcons = {
            'like': { icon: '<svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>', class: 'like' },
            'reaction': { icon: '<svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>', class: 'like' },
            'comment': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>', class: 'comment' },
            'comment_reply': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="9 14 4 9 9 4"></polyline><path d="M20 20v-7a4 4 0 0 0-4-4H4"></path></svg>', class: 'comment' },
            'follow': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>', class: 'follow' },
            'new_follower': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>', class: 'follow' },
            'mention': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="12" cy="12" r="4"></circle><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path></svg>', class: 'mention' },
            'share': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>', class: 'share' },
            'transaction_credit': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>', class: 'transaction credit' },
            'transaction_debit': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>', class: 'transaction debit' },
            'transaction': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>', class: 'transaction' },
            'story_reply': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>', class: 'story' },
            'story_reaction': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>', class: 'story' },
            'story_view': { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>', class: 'story' }
        };
        
        const defaultIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>';
        const typeInfo = typeIcons[notif.type] || { icon: defaultIcon, class: '' };
        const isUnread = !notif.is_read;
        
        const isTransactionNotif = notif.type && (notif.type.startsWith('transaction') || notif.type === 'wallet' || notif.type.includes('credit') || notif.type.includes('debit'));
        const actorName = isTransactionNotif ? 'BUNK3RCO1N' : (notif.actor_first_name || notif.actor_username || 'Alguien');
        
        let avatarContent;
        if (isTransactionNotif) {
            avatarContent = `<span class="notification-avatar-initial" style="background: linear-gradient(135deg, #f6ad55, #48bb78); color: white; display: flex; align-items: center; justify-content: center;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg></span>`;
        } else if (notif.actor_avatar) {
            avatarContent = `<img src="${this.escapeAttribute(notif.actor_avatar)}" alt="">`;
        } else {
            avatarContent = `<span class="notification-avatar-initial">${this.escapeHtml(actorName[0].toUpperCase())}</span>`;
        }
        
        const previewHtml = notif.preview_image 
            ? `<div class="notification-preview"><img src="${this.escapeAttribute(notif.preview_image)}" alt=""></div>`
            : '';
        
        const textContent = isTransactionNotif 
            ? this.escapeHtml(notif.message || 'Movimiento de wallet')
            : `<strong>${this.escapeHtml(actorName)}</strong> ${this.escapeHtml(notif.message || this.getNotificationMessage(notif.type))}`;
        
        return `
            <div class="notification-item ${isUnread ? 'unread' : ''} ${isTransactionNotif ? 'transaction-type' : ''}" 
                 role="listitem"
                 data-notif-id="${notif.id}"
                 onclick="App.handleNotificationClick(${notif.id}, '${this.sanitizeForJs(notif.type)}', ${notif.reference_id || 'null'})">
                <div class="notification-avatar">
                    ${avatarContent}
                </div>
                <span class="notification-icon ${typeInfo.class}">${typeInfo.icon}</span>
                <div class="notification-content">
                    <p class="notification-text">${textContent}</p>
                    <span class="notification-time">${this.formatTimeAgo(notif.created_at)}</span>
                </div>
                ${previewHtml}
            </div>
        `;
    },

    getNotificationMessage(type) {
        const messages = {
            'like': 'le gusto tu publicacion',
            'reaction': 'reacciono a tu publicacion',
            'comment': 'comento en tu publicacion',
            'comment_reply': 'respondio a tu comentario',
            'follow': 'empezo a seguirte',
            'new_follower': 'empezo a seguirte',
            'mention': 'te menciono',
            'share': 'compartio tu publicacion',
            'transaction_credit': '',
            'transaction_debit': '',
            'transaction': '',
            'story_reply': 'respondio a tu historia',
            'story_reaction': 'reacciono a tu historia',
            'story_view': 'vio tu historia'
        };
        return messages[type] || 'interactuo contigo';
    },

    formatTimeAgo(dateStr) {
        if (!dateStr) return '';
        
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSecs < 60) return 'ahora';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 7) return `${diffDays}d`;
        
        return date.toLocaleDateString('es', { day: 'numeric', month: 'short' });
    },

    async handleNotificationClick(notifId, type, referenceId) {
        await this.markNotificationAsRead(notifId);
        
        const item = document.querySelector(`[data-notif-id="${notifId}"]`);
        if (item) {
            item.classList.remove('unread');
        }
        
        if (type && (type.startsWith('transaction') || type === 'wallet' || type.includes('credit') || type.includes('debit'))) {
            this.showScreen('wallet-screen');
        } else if ((type === 'follow' || type === 'new_follower') && referenceId) {
            this.showUserProfile(referenceId);
        } else if (['like', 'reaction', 'comment', 'share', 'mention', 'comment_reply', 'post_like'].includes(type) && referenceId) {
            if (typeof PublicationsManager !== 'undefined') {
                PublicationsManager.showPostDetail(referenceId);
            }
        } else if ((type === 'story_reply' || type === 'story_reaction' || type === 'story_view') && referenceId) {
            this.viewStory({ userId: referenceId });
        }
    },

    async markNotificationAsRead(notifId) {
        try {
            await this.apiRequest(`/api/notifications/${notifId}/read`, {
                method: 'POST'
            });
            this.updateNotificationBadge();
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    },

    async markAllNotificationsAsRead() {
        try {
            const response = await this.apiRequest('/api/notifications/mark-all-read', {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Todas las notificaciones marcadas como leidas', 'success');
                this.notificationsState.notifications = this.notificationsState.notifications.map(n => ({
                    ...n,
                    is_read: true
                }));
                this.renderNotifications();
                this.updateNotificationBadge();
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
            this.showToast('Error al marcar notificaciones', 'error');
        }
    },

    _previousNotifCount: 0,
    
    async updateNotificationBadge() {
        try {
            const response = await this.apiRequest('/api/notifications/unread-count');
            const count = response.count || 0;
            
            const bottomBadge = document.getElementById('notification-badge');
            const headerBadge = document.getElementById('header-notif-badge');
            
            [bottomBadge, headerBadge].forEach(badge => {
                if (badge) {
                    if (count > 0) {
                        badge.textContent = count > 99 ? '99+' : count;
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                }
            });
            
            if (count > this._previousNotifCount && this._previousNotifCount > 0) {
                this.onNewNotificationReceived(count - this._previousNotifCount);
            }
            
            this._previousNotifCount = count;
            
            if (typeof StateManager !== 'undefined') {
                StateManager.set('unreadNotifications', count);
            }
        } catch (error) {
            console.error('Error updating notification badge:', error);
        }
    },
    
    onNewNotificationReceived(newCount) {
        const headerBtn = document.getElementById('header-notif-btn');
        if (headerBtn) {
            headerBtn.classList.add('has-new');
            setTimeout(() => headerBtn.classList.remove('has-new'), 600);
        }
        
        if (this.tg && this.tg.HapticFeedback) {
            this.tg.HapticFeedback.notificationOccurred('success');
        }
        
        this.showNewNotificationToast(newCount);
    },
    
    showNewNotificationToast(count) {
        let toast = document.getElementById('new-notif-toast');
        
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'new-notif-toast';
            toast.className = 'new-notif-toast';
            toast.onclick = () => {
                this.handleBottomNav('notifications');
                this.hideNewNotificationToast();
            };
            document.body.appendChild(toast);
        }
        
        toast.innerHTML = `
            <span class="new-notif-toast-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg></span>
            <span class="new-notif-toast-text">${count} ${count === 1 ? 'nueva notificacion' : 'nuevas notificaciones'}</span>
        `;
        
        requestAnimationFrame(() => {
            toast.classList.add('visible');
        });
        
        setTimeout(() => this.hideNewNotificationToast(), 4000);
    },
    
    hideNewNotificationToast() {
        const toast = document.getElementById('new-notif-toast');
        if (toast) {
            toast.classList.remove('visible');
        }
    },

    loadMoreNotifications() {
        this.loadNotifications(this.notificationsState.currentFilter, true);
    },

    initNotificationFilters() {
        document.querySelectorAll('.notif-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.notif-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.dataset.filter;
                this.loadNotifications(filter);
            });
        });
        
        const markAllBtn = document.getElementById('mark-all-read-btn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllNotificationsAsRead());
        }
    },

    async showNotificationSettings() {
        const modal = document.getElementById('notification-settings-modal');
        if (!modal) return;
        
        modal.classList.remove('hidden');
        
        try {
            const response = await this.apiRequest('/api/notifications/preferences');
            if (response.success && response.preferences) {
                const prefs = response.preferences;
                document.getElementById('notif-pref-likes').checked = prefs.likes !== false;
                document.getElementById('notif-pref-comments').checked = prefs.comments !== false;
                document.getElementById('notif-pref-follows').checked = prefs.follows !== false;
                document.getElementById('notif-pref-mentions').checked = prefs.mentions !== false;
                document.getElementById('notif-pref-transactions').checked = prefs.transactions !== false;
                document.getElementById('notif-pref-stories').checked = prefs.stories !== false;
            }
        } catch (error) {
            console.error('Error loading notification preferences:', error);
        }
    },

    hideNotificationSettings() {
        const modal = document.getElementById('notification-settings-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    },

    async saveNotificationSettings() {
        const preferences = {
            likes: document.getElementById('notif-pref-likes').checked,
            comments: document.getElementById('notif-pref-comments').checked,
            follows: document.getElementById('notif-pref-follows').checked,
            mentions: document.getElementById('notif-pref-mentions').checked,
            transactions: document.getElementById('notif-pref-transactions').checked,
            stories: document.getElementById('notif-pref-stories').checked
        };
        
        try {
            const response = await this.apiRequest('/api/notifications/preferences', {
                method: 'POST',
                body: JSON.stringify({ preferences })
            });
            
            if (response.success) {
                this.showToast('Preferencias guardadas', 'success');
                this.hideNotificationSettings();
            } else {
                this.showToast('Error al guardar preferencias', 'error');
            }
        } catch (error) {
            console.error('Error saving notification preferences:', error);
            this.showToast('Error al guardar', 'error');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (typeof Utils !== 'undefined' && Utils.setupMobileKeyboardHandler) {
        Utils.setupMobileKeyboardHandler();
    }
    App.init();
});

window.addEventListener('beforeunload', () => {
    App.cleanup();
});

window.addEventListener('pagehide', () => {
    App.cleanup();
});

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
    }
});
