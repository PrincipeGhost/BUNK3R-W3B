const Utils = {
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const str = String(text);
        const div = document.createElement('div');
        div.textContent = str;
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

Logger.init();

window.escapeHtml = Utils.escapeHtml.bind(Utils);
window.escapeAttribute = Utils.escapeAttribute.bind(Utils);
window.sanitizeForJs = Utils.sanitizeForJs.bind(Utils);
window.Logger = Logger;
window.ErrorHandler = ErrorHandler;
window.FallbackUI = FallbackUI;
