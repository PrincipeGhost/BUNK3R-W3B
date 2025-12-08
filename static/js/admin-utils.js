/**
 * Admin Utils - Utilidades especificas del Panel Admin
 * Agente: Frontend-Admin
 * Rama: feature/frontend-admin
 * 
 * Este archivo contiene funciones de utilidad especificas para el panel de admin.
 * Importa las funciones compartidas de SharedUtils.
 */

const AdminUtils = {
    /**
     * Formatea tabla de datos para admin
     */
    formatTableData(data, columns) {
        if (!Array.isArray(data)) return [];
        
        return data.map(row => {
            const formatted = {};
            columns.forEach(col => {
                let value = row[col.key];
                
                if (col.type === 'date') {
                    value = SharedUtils.formatDate(value);
                } else if (col.type === 'currency') {
                    value = SharedUtils.formatCurrency(value);
                } else if (col.type === 'number') {
                    value = SharedUtils.formatNumber(value);
                } else if (col.type === 'boolean') {
                    value = value ? 'Si' : 'No';
                } else if (col.type === 'status') {
                    value = this.formatStatus(value);
                }
                
                formatted[col.key] = value;
            });
            return { ...row, ...formatted };
        });
    },

    /**
     * Formatea estado con badge de color
     */
    formatStatus(status) {
        const statusMap = {
            'active': { label: 'Activo', class: 'status-success' },
            'inactive': { label: 'Inactivo', class: 'status-warning' },
            'banned': { label: 'Baneado', class: 'status-danger' },
            'pending': { label: 'Pendiente', class: 'status-info' },
            'verified': { label: 'Verificado', class: 'status-success' },
            'unverified': { label: 'No verificado', class: 'status-warning' },
            'completed': { label: 'Completado', class: 'status-success' },
            'failed': { label: 'Fallido', class: 'status-danger' },
            'processing': { label: 'Procesando', class: 'status-info' }
        };
        
        const info = statusMap[status?.toLowerCase()] || { 
            label: status || 'Desconocido', 
            class: 'status-default' 
        };
        
        return `<span class="status-badge ${info.class}">${SharedUtils.escapeHtml(info.label)}</span>`;
    },

    /**
     * Formatea nivel de riesgo con color
     */
    formatRiskLevel(score) {
        const numScore = parseInt(score) || 0;
        let level, colorClass;
        
        if (numScore >= 70) {
            level = 'Alto';
            colorClass = 'risk-high';
        } else if (numScore >= 40) {
            level = 'Medio';
            colorClass = 'risk-medium';
        } else {
            level = 'Bajo';
            colorClass = 'risk-low';
        }
        
        return `<span class="risk-badge ${colorClass}">${numScore} - ${level}</span>`;
    },

    /**
     * Muestra notificacion de admin
     */
    showAdminNotification(message, type = 'info') {
        if (typeof Toast !== 'undefined') {
            Toast.show(message, type);
        } else if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console.log(`[ADMIN ${type.toUpperCase()}] ${message}`);
        }
    },

    /**
     * Confirma accion con modal
     */
    async confirmAction(title, message, confirmText = 'Confirmar', cancelText = 'Cancelar') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'admin-confirm-modal';
            modal.innerHTML = `
                <div class="confirm-modal-backdrop"></div>
                <div class="confirm-modal-content">
                    <h3>${SharedUtils.escapeHtml(title)}</h3>
                    <p>${SharedUtils.escapeHtml(message)}</p>
                    <div class="confirm-modal-actions">
                        <button class="btn-cancel">${SharedUtils.escapeHtml(cancelText)}</button>
                        <button class="btn-confirm">${SharedUtils.escapeHtml(confirmText)}</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const cleanup = (result) => {
                modal.remove();
                resolve(result);
            };
            
            modal.querySelector('.btn-cancel').addEventListener('click', () => cleanup(false));
            modal.querySelector('.btn-confirm').addEventListener('click', () => cleanup(true));
            modal.querySelector('.confirm-modal-backdrop').addEventListener('click', () => cleanup(false));
        });
    },

    /**
     * Exporta datos a CSV
     */
    exportToCSV(data, filename = 'export.csv') {
        if (!Array.isArray(data) || data.length === 0) {
            this.showAdminNotification('No hay datos para exportar', 'warning');
            return;
        }
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(h => {
                    let val = row[h];
                    if (val === null || val === undefined) val = '';
                    val = String(val).replace(/"/g, '""');
                    if (val.includes(',') || val.includes('"') || val.includes('\n')) {
                        val = `"${val}"`;
                    }
                    return val;
                }).join(',')
            )
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
        
        this.showAdminNotification(`Archivo ${filename} exportado`, 'success');
    },

    /**
     * Formatea bytes a unidad legible
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
    },

    /**
     * Formatea duracion en segundos a formato legible
     */
    formatDuration(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        
        const parts = [];
        if (h > 0) parts.push(`${h}h`);
        if (m > 0) parts.push(`${m}m`);
        if (s > 0 || parts.length === 0) parts.push(`${s}s`);
        
        return parts.join(' ');
    },

    /**
     * Construye query string para filtros
     */
    buildQueryString(filters) {
        const params = new URLSearchParams();
        
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });
        
        return params.toString();
    },

    /**
     * Parsea respuesta de API admin
     */
    parseApiResponse(response) {
        if (!response) {
            return { success: false, error: 'Sin respuesta del servidor' };
        }
        
        if (response.success) {
            return response;
        }
        
        return {
            success: false,
            error: response.error || response.message || 'Error desconocido'
        };
    },

    /**
     * Maneja error de API admin
     */
    handleApiError(error, context = 'operacion') {
        const message = error?.message || error?.error || String(error);
        console.error(`[ADMIN ERROR] ${context}:`, message);
        this.showAdminNotification(`Error en ${context}: ${message}`, 'error');
        return { success: false, error: message };
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminUtils;
}
