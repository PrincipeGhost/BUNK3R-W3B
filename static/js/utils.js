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

window.escapeHtml = Utils.escapeHtml.bind(Utils);
window.escapeAttribute = Utils.escapeAttribute.bind(Utils);
window.sanitizeForJs = Utils.sanitizeForJs.bind(Utils);
