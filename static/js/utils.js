const Utils = {
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const str = String(text);
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    setupMobileKeyboardHandler() {
        let initialViewportHeight = window.innerHeight;
        let keyboardOpen = false;
        
        const detectKeyboard = () => {
            const currentHeight = window.innerHeight;
            const heightDiff = initialViewportHeight - currentHeight;
            const isKeyboardNowOpen = heightDiff > 150;
            
            if (isKeyboardNowOpen !== keyboardOpen) {
                keyboardOpen = isKeyboardNowOpen;
                document.body.classList.toggle('keyboard-open', keyboardOpen);
            }
        };
        
        window.addEventListener('resize', detectKeyboard);
        
        document.addEventListener('focusin', (e) => {
            const target = e.target;
            if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
                target.classList.add('input-focused');
                setTimeout(() => {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        });
        
        document.addEventListener('focusout', (e) => {
            const target = e.target;
            if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
                target.classList.remove('input-focused');
            }
        });
        
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                initialViewportHeight = window.innerHeight;
            }, 100);
        });
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
    }
};

const Logger = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    
    currentLevel: 1,
    isProduction: window.location.hostname !== 'localhost' && !window.location.hostname.includes('replit'),
    
    init() {
        this.currentLevel = this.isProduction ? this.WARN : this.DEBUG;
    },
    
    _formatMessage(level, ...args) {
        const timestamp = new Date().toISOString().substr(11, 12);
        const prefix = `[${timestamp}][${level}]`;
        return [prefix, ...args];
    },
    
    debug(...args) {
        if (this.currentLevel <= this.DEBUG) {
            console.log(...this._formatMessage('DEBUG', ...args));
        }
    },
    
    info(...args) {
        if (this.currentLevel <= this.INFO) {
            console.log(...this._formatMessage('INFO', ...args));
        }
    },
    
    warn(...args) {
        if (this.currentLevel <= this.WARN) {
            console.warn(...this._formatMessage('WARN', ...args));
        }
    },
    
    error(...args) {
        if (this.currentLevel <= this.ERROR) {
            console.error(...this._formatMessage('ERROR', ...args));
        }
    }
};

const ErrorHandler = {
    _toastQueue: [],
    _isShowingToast: false,
    
    handle(error, context = '', showToast = true) {
        const message = error?.message || String(error);
        const sanitizedMessage = this._sanitizeError(message);
        
        Logger.error(`${context}:`, sanitizedMessage);
        
        if (showToast) {
            this.showError(this._getUserFriendlyMessage(sanitizedMessage));
        }
        
        return sanitizedMessage;
    },
    
    _sanitizeError(message) {
        return message
            .replace(/\b(password|secret|key|token|auth)\b[:\s]*[^\s,}]*/gi, '[REDACTED]')
            .replace(/\/api\/[^\s]*/g, '/api/...')
            .substring(0, 200);
    },
    
    _getUserFriendlyMessage(technicalMessage) {
        const errorMap = {
            'network': 'Error de conexión. Verifica tu internet.',
            'timeout': 'La operación tardó demasiado. Intenta de nuevo.',
            '401': 'Sesión expirada. Recarga la página.',
            '403': 'No tienes permisos para esta acción.',
            '404': 'El recurso no existe.',
            '500': 'Error del servidor. Intenta más tarde.',
            'failed to fetch': 'Error de conexión. Verifica tu internet.',
            'decrypt': 'Error al descifrar el contenido.',
            'parse': 'Error al procesar la respuesta.'
        };
        
        const lowerMessage = technicalMessage.toLowerCase();
        for (const [key, friendly] of Object.entries(errorMap)) {
            if (lowerMessage.includes(key)) {
                return friendly;
            }
        }
        
        return 'Ha ocurrido un error. Intenta de nuevo.';
    },
    
    showError(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else if (typeof App !== 'undefined' && typeof App.showToast === 'function') {
            App.showToast(message, 'error');
        } else if (typeof PublicationsManager !== 'undefined' && typeof PublicationsManager.showToast === 'function') {
            PublicationsManager.showToast(message, 'error');
        }
    },
    
    showSuccess(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'success');
        } else if (typeof App !== 'undefined' && typeof App.showToast === 'function') {
            App.showToast(message, 'success');
        } else if (typeof PublicationsManager !== 'undefined' && typeof PublicationsManager.showToast === 'function') {
            PublicationsManager.showToast(message, 'success');
        }
    }
};

const FallbackUI = {
    showLoadingError(containerId, retryCallback, message = 'Error al cargar') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="error-fallback">
                <div class="error-fallback-icon">⚠️</div>
                <h4>${Utils.escapeHtml(message)}</h4>
                <p>No se pudo cargar el contenido</p>
                ${retryCallback ? '<button class="retry-btn" onclick="' + retryCallback + '">Reintentar</button>' : ''}
            </div>
        `;
    },
    
    showEmptyState(containerId, icon = '📭', title = 'Sin contenido', subtitle = '') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <h4>${Utils.escapeHtml(title)}</h4>
                ${subtitle ? `<p>${Utils.escapeHtml(subtitle)}</p>` : ''}
            </div>
        `;
    },
    
    showSkeleton(containerId, count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const skeletons = Array(count).fill('').map(() => `
            <div class="skeleton-card">
                <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-text" style="width: 60%"></div>
                </div>
                <div class="skeleton-body"></div>
                <div class="skeleton-footer">
                    <div class="skeleton-text" style="width: 30%"></div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = skeletons;
    }
};

const A11y = {
    _focusTrapStack: [],
    _liveRegion: null,
    
    init() {
        this._createLiveRegion();
        this._setupGlobalKeyboardHandlers();
    },
    
    _createLiveRegion() {
        if (this._liveRegion) return;
        
        this._liveRegion = document.createElement('div');
        this._liveRegion.id = 'a11y-live-region';
        this._liveRegion.setAttribute('role', 'status');
        this._liveRegion.setAttribute('aria-live', 'polite');
        this._liveRegion.setAttribute('aria-atomic', 'true');
        this._liveRegion.className = 'sr-only';
        document.body.appendChild(this._liveRegion);
    },
    
    announce(message, priority = 'polite') {
        if (!this._liveRegion) this._createLiveRegion();
        
        this._liveRegion.setAttribute('aria-live', priority);
        this._liveRegion.textContent = '';
        
        setTimeout(() => {
            this._liveRegion.textContent = message;
        }, 100);
    },
    
    _setupGlobalKeyboardHandlers() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this._focusTrapStack.length > 0) {
                const currentTrap = this._focusTrapStack[this._focusTrapStack.length - 1];
                if (currentTrap.onEscape) {
                    currentTrap.onEscape();
                }
            }
        });
    },
    
    trapFocus(element, options = {}) {
        if (!element) return null;
        
        const focusableSelector = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
        const focusableElements = element.querySelectorAll(focusableSelector);
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        const previousActiveElement = document.activeElement;
        
        const handleKeydown = (e) => {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable?.focus();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable?.focus();
                }
            }
        };
        
        element.addEventListener('keydown', handleKeydown);
        
        if (options.autoFocus !== false && firstFocusable) {
            setTimeout(() => firstFocusable.focus(), 50);
        }
        
        const trapInfo = {
            element,
            handleKeydown,
            previousActiveElement,
            onEscape: options.onEscape
        };
        
        this._focusTrapStack.push(trapInfo);
        
        return {
            release: () => this.releaseFocus(trapInfo)
        };
    },
    
    releaseFocus(trapInfo) {
        if (!trapInfo) return;
        
        trapInfo.element.removeEventListener('keydown', trapInfo.handleKeydown);
        
        const index = this._focusTrapStack.indexOf(trapInfo);
        if (index > -1) {
            this._focusTrapStack.splice(index, 1);
        }
        
        if (trapInfo.previousActiveElement && trapInfo.previousActiveElement.focus) {
            trapInfo.previousActiveElement.focus();
        }
    },
    
    openModal(modalElement, options = {}) {
        if (!modalElement) return null;
        
        modalElement.setAttribute('role', 'dialog');
        modalElement.setAttribute('aria-modal', 'true');
        
        if (options.labelledBy) {
            modalElement.setAttribute('aria-labelledby', options.labelledBy);
        }
        if (options.describedBy) {
            modalElement.setAttribute('aria-describedby', options.describedBy);
        }
        
        modalElement.classList.remove('hidden');
        modalElement.setAttribute('aria-hidden', 'false');
        
        document.body.style.overflow = 'hidden';
        
        const trap = this.trapFocus(modalElement, {
            onEscape: options.onClose,
            autoFocus: options.autoFocus
        });
        
        if (options.label) {
            this.announce(options.label + ' abierto');
        }
        
        return trap;
    },
    
    closeModal(modalElement, trap) {
        if (!modalElement) return;
        
        modalElement.classList.add('hidden');
        modalElement.setAttribute('aria-hidden', 'true');
        
        if (trap) {
            trap.release();
        }
        
        if (this._focusTrapStack.length === 0) {
            document.body.style.overflow = '';
        }
    },
    
    makeInteractive(element, onClick, options = {}) {
        if (!element) return;
        
        element.setAttribute('role', options.role || 'button');
        element.setAttribute('tabindex', '0');
        
        if (options.label) {
            element.setAttribute('aria-label', options.label);
        }
        
        element.addEventListener('click', onClick);
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick(e);
            }
        });
    }
};

const Toast = {
    _container: null,
    _queue: [],
    _isShowing: false,
    _currentTimeout: null,
    
    init() {
        this._container = document.getElementById('toast-container');
        if (!this._container) {
            this._container = document.createElement('div');
            this._container.id = 'toast-container';
            this._container.className = 'toast-container';
            this._container.setAttribute('role', 'region');
            this._container.setAttribute('aria-label', 'Notificaciones');
            this._container.setAttribute('aria-live', 'polite');
            document.body.appendChild(this._container);
        }
    },
    
    show(message, type = 'info', duration = 3000) {
        if (!this._container) this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        toast.innerHTML = `
            <span class="toast-icon" aria-hidden="true">${icons[type] || icons.info}</span>
            <span class="toast-message">${Utils.escapeHtml(message)}</span>
            <button class="toast-close" aria-label="Cerrar notificacion" tabindex="0">&times;</button>
        `;
        
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this._removeToast(toast));
        closeBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this._removeToast(toast);
            }
        });
        
        this._container.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.classList.add('toast-visible');
        });
        
        if (duration > 0) {
            setTimeout(() => this._removeToast(toast), duration);
        }
        
        A11y.announce(message, type === 'error' ? 'assertive' : 'polite');
        
        return toast;
    },
    
    _removeToast(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.classList.remove('toast-visible');
        toast.classList.add('toast-hiding');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    },
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
};

const StateManager = {
    _state: {
        user: null,
        isOwner: false,
        isDemoMode: false,
        isAuthenticated: false,
        twoFactorEnabled: false,
        twoFactorVerified: false,
        
        balance: 0,
        walletAddress: null,
        isWalletConnected: false,
        isDeviceTrusted: false,
        deviceId: null,
        
        currentSection: 'dashboard',
        previousSection: null,
        
        pendingOperations: new Set(),
        
        feedPosts: [],
        stories: [],
        notifications: [],
        unreadNotifications: 0,
        
        lastActivityTime: Date.now(),
        sessionExpiry: null
    },
    
    _subscribers: new Map(),
    _version: 0,
    
    init() {
        Logger.debug('StateManager initialized');
    },
    
    get(key) {
        if (key) {
            return this._state[key];
        }
        return { ...this._state };
    },
    
    set(key, value, silent = false) {
        const oldValue = this._state[key];
        if (oldValue === value) return;
        
        this._state[key] = value;
        this._version++;
        
        if (!silent) {
            this._notify(key, value, oldValue);
        }
        
        Logger.debug(`State updated: ${key}`, { old: oldValue, new: value });
    },
    
    update(updates, silent = false) {
        const changes = {};
        
        for (const [key, value] of Object.entries(updates)) {
            if (this._state[key] !== value) {
                changes[key] = { old: this._state[key], new: value };
                this._state[key] = value;
            }
        }
        
        if (Object.keys(changes).length > 0) {
            this._version++;
            
            if (!silent) {
                for (const [key, change] of Object.entries(changes)) {
                    this._notify(key, change.new, change.old);
                }
                this._notify('*', this._state, changes);
            }
        }
        
        return Object.keys(changes).length > 0;
    },
    
    subscribe(key, callback) {
        if (!this._subscribers.has(key)) {
            this._subscribers.set(key, new Set());
        }
        this._subscribers.get(key).add(callback);
        
        return () => this.unsubscribe(key, callback);
    },
    
    unsubscribe(key, callback) {
        if (this._subscribers.has(key)) {
            this._subscribers.get(key).delete(callback);
        }
    },
    
    _notify(key, newValue, oldValue) {
        if (this._subscribers.has(key)) {
            this._subscribers.get(key).forEach(callback => {
                try {
                    callback(newValue, oldValue, key);
                } catch (error) {
                    Logger.error('StateManager subscriber error:', error);
                }
            });
        }
    },
    
    setUser(userData) {
        this.update({
            user: userData,
            isAuthenticated: !!userData,
            isOwner: userData?.isOwner || false
        });
    },
    
    setBalance(balance) {
        this.set('balance', parseFloat(balance) || 0);
    },
    
    updateBalance(delta) {
        const newBalance = Math.max(0, this.get('balance') + delta);
        this.set('balance', newBalance);
        return newBalance;
    },
    
    setWallet(address, connected = true) {
        this.update({
            walletAddress: address,
            isWalletConnected: connected && !!address
        });
    },
    
    setSection(section) {
        const current = this.get('currentSection');
        if (current !== section) {
            this.update({
                previousSection: current,
                currentSection: section
            });
        }
    },
    
    addPendingOperation(operationId) {
        const pending = new Set(this._state.pendingOperations);
        pending.add(operationId);
        this.set('pendingOperations', pending);
    },
    
    removePendingOperation(operationId) {
        const pending = new Set(this._state.pendingOperations);
        pending.delete(operationId);
        this.set('pendingOperations', pending);
    },
    
    hasPendingOperations() {
        return this._state.pendingOperations.size > 0;
    },
    
    isPending(operationId) {
        return this._state.pendingOperations.has(operationId);
    },
    
    updateActivity() {
        this.set('lastActivityTime', Date.now(), true);
    },
    
    isSessionExpired() {
        const expiry = this.get('sessionExpiry');
        if (!expiry) return false;
        return Date.now() > expiry;
    },
    
    addNotification(notification) {
        const notifications = [...this._state.notifications, notification];
        const unread = this._state.unreadNotifications + 1;
        this.update({ notifications, unreadNotifications: unread });
    },
    
    markNotificationsRead() {
        this.set('unreadNotifications', 0);
    },
    
    updateFeed(posts) {
        this.set('feedPosts', posts);
    },
    
    updateStories(stories) {
        this.set('stories', stories);
    },
    
    reset() {
        this._state = {
            user: null,
            isOwner: false,
            isDemoMode: false,
            isAuthenticated: false,
            twoFactorEnabled: false,
            twoFactorVerified: false,
            balance: 0,
            walletAddress: null,
            isWalletConnected: false,
            isDeviceTrusted: false,
            deviceId: null,
            currentSection: 'dashboard',
            previousSection: null,
            pendingOperations: new Set(),
            feedPosts: [],
            stories: [],
            notifications: [],
            unreadNotifications: 0,
            lastActivityTime: Date.now(),
            sessionExpiry: null
        };
        this._version++;
        this._notify('*', this._state, null);
        Logger.debug('StateManager reset');
    },
    
    getVersion() {
        return this._version;
    },
    
    debug() {
        Logger.debug('StateManager state:', {
            ...this._state,
            pendingOperations: Array.from(this._state.pendingOperations)
        });
        return this._state;
    }
};

const RequestManager = {
    _pendingRequests: new Map(),
    _requestId: 0,
    
    DEFAULT_TIMEOUT: 30000,
    MAX_RETRIES: 3,
    RETRY_DELAYS: [1000, 2000, 4000],
    
    async fetch(url, options = {}) {
        const {
            timeout = this.DEFAULT_TIMEOUT,
            retries = this.MAX_RETRIES,
            retryOn = [502, 503, 504],
            cancelKey = null,
            ...fetchOptions
        } = options;
        
        if (cancelKey && this._pendingRequests.has(cancelKey)) {
            this._pendingRequests.get(cancelKey).abort();
            this._pendingRequests.delete(cancelKey);
        }
        
        const controller = new AbortController();
        const requestId = ++this._requestId;
        
        if (cancelKey) {
            this._pendingRequests.set(cancelKey, controller);
        }
        
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, timeout);
        
        let lastError = null;
        
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                if (controller.signal.aborted) {
                    throw new DOMException('Request was cancelled', 'AbortError');
                }
                
                const response = await fetch(url, {
                    ...fetchOptions,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (cancelKey) {
                    this._pendingRequests.delete(cancelKey);
                }
                
                if (!response.ok && retryOn.includes(response.status) && attempt < retries) {
                    const delay = this.RETRY_DELAYS[Math.min(attempt, this.RETRY_DELAYS.length - 1)];
                    Logger.warn(`Request failed with ${response.status}, retrying in ${delay}ms (attempt ${attempt + 1}/${retries})`);
                    await this._delay(delay);
                    continue;
                }
                
                return response;
                
            } catch (error) {
                lastError = error;
                
                if (error.name === 'AbortError') {
                    clearTimeout(timeoutId);
                    if (cancelKey) {
                        this._pendingRequests.delete(cancelKey);
                    }
                    throw error;
                }
                
                if (attempt < retries) {
                    const delay = this.RETRY_DELAYS[Math.min(attempt, this.RETRY_DELAYS.length - 1)];
                    Logger.warn(`Request error, retrying in ${delay}ms (attempt ${attempt + 1}/${retries}):`, error.message);
                    await this._delay(delay);
                }
            }
        }
        
        clearTimeout(timeoutId);
        if (cancelKey) {
            this._pendingRequests.delete(cancelKey);
        }
        
        throw lastError || new Error('Request failed after retries');
    },
    
    cancel(cancelKey) {
        if (this._pendingRequests.has(cancelKey)) {
            this._pendingRequests.get(cancelKey).abort();
            this._pendingRequests.delete(cancelKey);
            Logger.debug(`Request cancelled: ${cancelKey}`);
            return true;
        }
        return false;
    },
    
    cancelAll() {
        for (const [key, controller] of this._pendingRequests) {
            controller.abort();
        }
        this._pendingRequests.clear();
        Logger.debug('All pending requests cancelled');
    },
    
    hasPending(cancelKey) {
        return this._pendingRequests.has(cancelKey);
    },
    
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

const Debounce = {
    _timers: new Map(),
    
    run(key, callback, delay = 300) {
        if (this._timers.has(key)) {
            clearTimeout(this._timers.get(key));
        }
        
        const timerId = setTimeout(() => {
            this._timers.delete(key);
            callback();
        }, delay);
        
        this._timers.set(key, timerId);
    },
    
    cancel(key) {
        if (this._timers.has(key)) {
            clearTimeout(this._timers.get(key));
            this._timers.delete(key);
        }
    },
    
    cancelAll() {
        for (const timerId of this._timers.values()) {
            clearTimeout(timerId);
        }
        this._timers.clear();
    }
};

const Throttle = {
    _lastCalls: new Map(),
    
    run(key, callback, limit = 1000) {
        const now = Date.now();
        const lastCall = this._lastCalls.get(key) || 0;
        
        if (now - lastCall >= limit) {
            this._lastCalls.set(key, now);
            callback();
            return true;
        }
        return false;
    },
    
    reset(key) {
        this._lastCalls.delete(key);
    }
};

Logger.init();
A11y.init();
Toast.init();
StateManager.init();

window.escapeHtml = Utils.escapeHtml.bind(Utils);
window.escapeAttribute = Utils.escapeAttribute.bind(Utils);
window.sanitizeForJs = Utils.sanitizeForJs.bind(Utils);
window.Logger = Logger;
window.ErrorHandler = ErrorHandler;
window.FallbackUI = FallbackUI;
window.A11y = A11y;
window.Toast = Toast;
window.StateManager = StateManager;
window.RequestManager = RequestManager;
window.Debounce = Debounce;
window.Throttle = Throttle;

window.showToast = function(message, type, duration) {
    return Toast.show(message, type, duration);
};
