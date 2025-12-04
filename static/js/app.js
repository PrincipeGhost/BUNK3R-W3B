const App = {
    tg: null,
    user: null,
    initData: null,
    isOwner: false,
    isDemoMode: false,
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
        console.log('Iniciando modo demo (fuera de Telegram)');
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
        
        await this.check2FAStatus();
    },
    
    async check2FAStatus() {
        try {
            console.log('Checking 2FA status...');
            const response = await this.apiRequest('/api/2fa/status', { method: 'POST' });
            console.log('2FA status response:', response);
            
            if (response.success) {
                this.twoFactorEnabled = response.enabled;
                
                if (response.requiresVerification) {
                    console.log('2FA requires verification, showing verify screen');
                    this.show2FAVerifyScreen();
                    return;
                }
                
                if (!response.configured && this.isOwner) {
                    console.log('2FA not configured, showing setup screen');
                    this.show2FASetupScreen();
                    return;
                }
                
                if (response.configured && !response.enabled && this.isOwner) {
                    console.log('2FA configured but not enabled, showing setup screen to complete activation');
                    this.show2FASetupScreen();
                    return;
                }
                
                console.log('2FA configured or not owner, completing login');
                this.completeLogin();
            } else {
                console.log('2FA status failed, completing login');
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
        console.log('Showing 2FA setup screen');
        this.hidePreloadOverlay();
        document.getElementById('loading-screen').classList.add('hidden');
        const setupScreen = document.getElementById('setup-2fa-screen');
        setupScreen.classList.remove('hidden');
        console.log('Setup screen visible:', !setupScreen.classList.contains('hidden'));
        
        try {
            const response = await this.apiRequest('/api/2fa/setup', { method: 'POST' });
            console.log('2FA setup response:', response.success ? 'success' : 'failed');
            
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
        
        const input = document.getElementById('verify-2fa-code');
        if (input) {
            input.focus();
        }
        
        this.setup2FAEventListeners();
    },
    
    setup2FAEventListeners() {
        const setupCodeInput = document.getElementById('setup-2fa-code');
        const verifyCodeInput = document.getElementById('verify-2fa-code');
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
        
        if (verifyCodeInput) {
            verifyCodeInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
            });
            
            verifyCodeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.target.value.length === 6) {
                    this.verify2FACode(e.target.value);
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
                    this.verify2FACode(code);
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
            } else {
                if (errorEl) {
                    errorEl.textContent = response.error || 'Codigo incorrecto';
                    errorEl.classList.remove('hidden');
                }
                document.getElementById('verify-2fa-code').value = '';
                document.getElementById('verify-2fa-code').focus();
            }
        } catch (error) {
            console.error('Error verifying 2FA:', error);
            if (errorEl) {
                errorEl.textContent = 'Error al verificar. Intenta de nuevo.';
                errorEl.classList.remove('hidden');
            }
        }
    },
    
    skip2FASetup() {
        document.getElementById('setup-2fa-screen').classList.add('hidden');
        this.completeLogin();
    },
    
    completeLogin() {
        this.showMainApp();
        this.setupEventListeners();
        this.updateAllAvatars();
        this.loadInitialData();
        this.startSessionActivityMonitor();
    },
    
    startSessionActivityMonitor() {
        if (this.sessionActivityInterval) {
            clearInterval(this.sessionActivityInterval);
        }
        
        this.lastActivityTime = Date.now();
        
        const activityEvents = ['click', 'touchstart', 'keypress', 'scroll'];
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.lastActivityTime = Date.now();
            }, { passive: true });
        });
        
        this.sessionActivityInterval = setInterval(() => {
            this.checkSessionValidity();
        }, 60000);
    },
    
    async checkSessionValidity() {
        if (!this.twoFactorEnabled) return;
        
        const inactiveTime = Date.now() - this.lastActivityTime;
        const tenMinutes = 10 * 60 * 1000;
        
        if (inactiveTime >= tenMinutes) {
            this.show2FAVerifyScreen();
            document.getElementById('main-app').classList.add('hidden');
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/2fa/session', { method: 'POST' });
            
            if (response.requiresVerification) {
                this.show2FAVerifyScreen();
                document.getElementById('main-app').classList.add('hidden');
            } else if (response.sessionValid) {
                await this.apiRequest('/api/2fa/refresh', { method: 'POST' });
            }
        } catch (error) {
            console.error('Error checking session:', error);
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
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        
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
    
    goToHome() {
        document.getElementById('tracking-module').classList.add('hidden');
        document.getElementById('marketplace-screen').classList.add('hidden');
        document.getElementById('bots-screen').classList.add('hidden');
        document.getElementById('wallet-screen').classList.add('hidden');
        document.getElementById('profile-screen').classList.add('hidden');
        document.getElementById('home-screen').classList.remove('hidden');
        
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const homeBtn = document.querySelector('.bottom-nav-item[data-nav="home"]');
        if (homeBtn) {
            homeBtn.classList.add('active');
        }
        
        if (this.tg && this.tg.BackButton) {
            this.tg.BackButton.hide();
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
        
        if (hamburgerMenu && sidebar) {
            hamburgerMenu.addEventListener('click', () => {
                sidebar.classList.add('active');
                sidebarOverlay.classList.add('active');
            });
        }
        
        if (sidebarClose) {
            sidebarClose.addEventListener('click', () => {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            });
        }
        
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            });
        }
        
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                this.showToast('Seccion: ' + item.textContent.trim(), 'info');
            });
        });
        
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
                
                if (marketplaceScreen && !marketplaceScreen.classList.contains('hidden')) {
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
        
        this.setupAvatarUpload();
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
        });
        
        const activeItem = document.querySelector(`.bottom-nav-item[data-nav="${navType}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        switch(navType) {
            case 'home':
                this.goToHome();
                break;
            case 'marketplace':
                this.showPage('marketplace');
                break;
            case 'bots':
                this.showPage('bots');
                break;
            case 'wallet':
                this.showPage('wallet');
                break;
            case 'profile':
                this.showPage('profile');
                this.updateProfilePage();
                break;
        }
    },
    
    showPage(pageName) {
        document.getElementById('home-screen').classList.add('hidden');
        document.getElementById('tracking-module').classList.add('hidden');
        document.getElementById('marketplace-screen').classList.add('hidden');
        document.getElementById('bots-screen').classList.add('hidden');
        document.getElementById('wallet-screen').classList.add('hidden');
        document.getElementById('profile-screen').classList.add('hidden');
        
        const pageScreen = document.getElementById(`${pageName}-screen`);
        if (pageScreen) {
            pageScreen.classList.remove('hidden');
        }
        
        if (this.tg && this.tg.BackButton) {
            this.tg.BackButton.show();
        }
        
        if (pageName === 'bots') {
            this.loadUserBots();
        }
    },
    
    updateProfilePage() {
        const username = document.getElementById('profile-page-username');
        const name = document.getElementById('profile-page-name');
        
        if (username && this.user) {
            username.textContent = this.user.username ? `@${this.user.username}` : '@demo_user';
        }
        if (name && this.user) {
            name.textContent = this.user.firstName || 'Demo';
        }
        
        this.updateAllAvatars();
    },
    
    setupAvatarUpload() {
        const avatarWrap = document.getElementById('avatar-upload-wrap');
        const avatarInput = document.getElementById('avatar-input');
    },
    
    updateAllAvatars() {
        const sidebarAvatar = document.getElementById('sidebar-avatar');
        const bottomNavAvatar = document.getElementById('bottom-nav-avatar');
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
            
            if (profileAvatarImg) {
                profileAvatarImg.classList.add('hidden');
            }
            if (profileAvatarInitial) {
                profileAvatarInitial.textContent = this.userInitials;
                profileAvatarInitial.classList.remove('hidden');
            }
        }
    },
    
    async loadInitialData() {
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
            this.tg.BackButton.show();
        } else {
            this.tg.BackButton.hide();
        }
        
        if (sectionId === 'trackings') {
            this.loadTrackings();
        }
        
        if (sectionId === 'dashboard') {
            this.loadInitialData();
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
                            <p>No se encontraron resultados para "${query}"</p>
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
            <div class="tracking-card" data-id="${t.trackingId}">
                <div class="tracking-header">
                    <span class="tracking-id">${this.truncateId(t.trackingId)}</span>
                    <span class="tracking-status status-${t.status}">
                        ${t.statusIcon} ${t.statusLabel}
                    </span>
                </div>
                <div class="tracking-info">
                    <div class="tracking-info-row">
                        <span class="icon">👤</span>
                        <span class="value">${t.recipientName || 'Sin nombre'}</span>
                    </div>
                    <div class="tracking-info-row">
                        <span class="icon">📦</span>
                        <span class="value">${t.productName || 'Sin producto'}</span>
                    </div>
                    ${t.productPrice ? `
                    <div class="tracking-info-row">
                        <span class="icon">💰</span>
                        <span class="value">${t.productPrice}€</span>
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
                        <span class="tracking-id" style="font-size: 14px;">${t.trackingId}</span>
                        <span class="tracking-status status-${t.status}">
                            ${t.statusIcon} ${t.statusLabel}
                        </span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Informacion del Paquete</div>
                    <div class="detail-row">
                        <span class="detail-label">Destinatario</span>
                        <span class="detail-value">${t.recipientName || 'No especificado'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Producto</span>
                        <span class="detail-value">${t.productName || 'No especificado'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Precio</span>
                        <span class="detail-value">${t.productPrice || '0'}€</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Peso</span>
                        <span class="detail-value">${t.packageWeight || 'No especificado'}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Direcciones</div>
                    <div class="detail-row">
                        <span class="detail-label">Direccion entrega</span>
                        <span class="detail-value">${t.deliveryAddress || 'No especificada'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">CP Destino</span>
                        <span class="detail-value">${t.recipientPostalCode || '-'} ${t.recipientProvince || ''}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Pais Destino</span>
                        <span class="detail-value">${t.recipientCountry || 'No especificado'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Direccion origen</span>
                        <span class="detail-value">${t.senderAddress || 'No especificada'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">CP Origen</span>
                        <span class="detail-value">${t.senderPostalCode || '-'} ${t.senderProvince || ''}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">Fechas</div>
                    <div class="detail-row">
                        <span class="detail-label">Entrega estimada</span>
                        <span class="detail-value">${t.estimatedDelivery || 'Por calcular'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Dias de retraso</span>
                        <span class="detail-value">${t.delayDays || 0} dias</span>
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
                            <div class="history-status">${h.status}</div>
                            ${h.notes ? `<div class="history-notes">${h.notes}</div>` : ''}
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
                    <input type="text" id="edit-recipient" value="${tracking?.recipientName || ''}" class="email-input">
                </div>
                <div class="form-group">
                    <label>Producto</label>
                    <input type="text" id="edit-product" value="${tracking?.productName || ''}" class="email-input">
                </div>
                <div class="form-group">
                    <label>Precio</label>
                    <input type="text" id="edit-price" value="${tracking?.productPrice || ''}" class="email-input">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="App.closeModal()">Cancelar</button>
                <button class="btn btn-primary" onclick="App.saveEdit('${trackingId}')">Guardar</button>
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
        modal.innerHTML = content;
        document.getElementById('modal-overlay').classList.remove('hidden');
    },
    
    closeModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    },
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        if (this.tg) {
            this.tg.HapticFeedback.notificationOccurred(
                type === 'error' ? 'error' : type === 'success' ? 'success' : 'warning'
            );
        }
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
    
    async apiRequest(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.isDemoMode) {
            headers['X-Demo-Mode'] = 'true';
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
            throw new Error(data.error || `HTTP error ${response.status}`);
        }
        
        return data;
    },
    
    async loadUserBots() {
        const myBotsList = document.getElementById('my-bots-list');
        const availableBotsList = document.getElementById('available-bots-list');
        const myBotsEmpty = document.getElementById('my-bots-empty');
        const availableBotsEmpty = document.getElementById('available-bots-empty');
        
        myBotsList.innerHTML = '<div class="bots-loading"><div class="loading-spinner"></div><p>Cargando tus bots...</p></div>';
        availableBotsList.innerHTML = '<div class="bots-loading"><div class="loading-spinner"></div><p>Cargando bots disponibles...</p></div>';
        myBotsEmpty.classList.add('hidden');
        availableBotsEmpty.classList.add('hidden');
        
        try {
            const [myBotsResponse, availableBotsResponse] = await Promise.all([
                this.apiRequest('/api/bots/my'),
                this.apiRequest('/api/bots/available')
            ]);
            
            this.renderMyBots(myBotsResponse.bots || []);
            this.renderAvailableBots(availableBotsResponse.bots || []);
            
        } catch (error) {
            console.error('Error loading bots:', error);
            myBotsList.innerHTML = '<div class="bots-empty"><div class="empty-icon">⚠️</div><p>Error al cargar bots</p></div>';
            availableBotsList.innerHTML = '<div class="bots-empty"><div class="empty-icon">⚠️</div><p>Error al cargar bots</p></div>';
        }
    },
    
    renderMyBots(bots) {
        const myBotsList = document.getElementById('my-bots-list');
        const myBotsEmpty = document.getElementById('my-bots-empty');
        
        if (!bots || bots.length === 0) {
            myBotsList.innerHTML = '';
            myBotsEmpty.classList.remove('hidden');
            return;
        }
        
        myBotsEmpty.classList.add('hidden');
        myBotsList.innerHTML = bots.map(bot => {
            if (bot.botType === 'tracking_manager') {
                return `
                    <div class="bot-card active-bot owner-bot clickable" data-bot-id="${bot.id}" onclick="App.openBotPanel('${this.escapeHtml(bot.botType)}')">
                        <div class="bot-avatar">${bot.icon || '🤖'}</div>
                        <div class="bot-info">
                            <h3>${this.escapeHtml(bot.botName)}</h3>
                            <p class="bot-status online">En linea</p>
                            ${bot.description ? `<p class="bot-desc">${this.escapeHtml(bot.description)}</p>` : ''}
                        </div>
                        <div class="bot-arrow">→</div>
                    </div>
                `;
            }
            return `
                <div class="bot-card active-bot" data-bot-id="${bot.id}">
                    <div class="bot-avatar">${bot.icon || '🤖'}</div>
                    <div class="bot-info">
                        <h3>${this.escapeHtml(bot.botName)}</h3>
                        <p class="bot-status online">En linea</p>
                        ${bot.description ? `<p class="bot-desc">${this.escapeHtml(bot.description)}</p>` : ''}
                    </div>
                    <div class="bot-actions">
                        <button class="bot-action-btn" onclick="App.configureBot(${bot.id}, '${this.escapeHtml(bot.botType)}')">Configurar</button>
                        <button class="bot-remove-btn" onclick="App.confirmRemoveBot(${bot.id}, '${this.escapeHtml(bot.botName)}')">Quitar</button>
                    </div>
                </div>
            `;
        }).join('');
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
                    <span class="bot-price">${bot.price > 0 ? bot.price + ' creditos' : 'Gratis'}</span>
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
        this.showToast('Configuracion de bot disponible proximamente', 'info');
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
                        ${price} creditos
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
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
