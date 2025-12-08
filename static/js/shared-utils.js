/**
 * Shared Utils - Utilidades compartidas (SOLO LECTURA)
 * 
 * IMPORTANTE: Este archivo NO debe ser modificado por ningun agente.
 * Contiene funciones basicas que usan tanto admin como user.
 * 
 * Si un agente necesita funciones adicionales, debe agregarlas a:
 * - admin-utils.js (Frontend-Admin)
 * - utils.js (Frontend-User)
 */

const SharedUtils = {
    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const str = String(text);
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Escapa atributos HTML
     */
    escapeAttribute(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    },

    /**
     * Formatea fecha a formato legible
     */
    formatDate(date, options = {}) {
        if (!date) return '';
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const defaultOptions = {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            ...options
        };
        
        return d.toLocaleDateString('es-ES', defaultOptions);
    },

    /**
     * Formatea fecha relativa (hace X minutos)
     */
    formatRelativeTime(date) {
        if (!date) return '';
        const now = new Date();
        const d = new Date(date);
        const diffMs = now - d;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) return 'Ahora';
        if (diffMins < 60) return `Hace ${diffMins}m`;
        if (diffHours < 24) return `Hace ${diffHours}h`;
        if (diffDays < 7) return `Hace ${diffDays}d`;
        
        return this.formatDate(date);
    },

    /**
     * Formatea numeros con separadores de miles
     */
    formatNumber(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return Number(num).toLocaleString('es-ES', {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimals
        });
    },

    /**
     * Formatea moneda
     */
    formatCurrency(amount, currency = 'USD') {
        if (amount === null || amount === undefined || isNaN(amount)) return '$0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    /**
     * Debounce para evitar llamadas excesivas
     */
    debounce(fn, delay = 300) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /**
     * Throttle para limitar llamadas por tiempo
     */
    throttle(fn, limit = 300) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                fn.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Copia texto al portapapeles
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const result = document.execCommand('copy');
            document.body.removeChild(textarea);
            return result;
        }
    },

    /**
     * Genera un ID unico
     */
    generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Trunca texto con elipsis
     */
    truncate(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text || '';
        return text.substring(0, maxLength - 3) + '...';
    },

    /**
     * Valida email
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Obtiene parametros de URL
     */
    getUrlParams() {
        const params = {};
        const searchParams = new URLSearchParams(window.location.search);
        for (const [key, value] of searchParams) {
            params[key] = value;
        }
        return params;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SharedUtils;
}
