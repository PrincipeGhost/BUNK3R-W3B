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
            
            this.showMainApp();
            this.setupEventListeners();
            await this.loadInitialData();
            
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
        
        this.showMainApp();
        this.setupEventListeners();
        await this.loadInitialData();
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
            const initials = userName.charAt(0).toUpperCase();
            sidebarAvatar.textContent = initials;
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
        document.getElementById('home-screen').classList.remove('hidden');
        
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
        
        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.filterTrackings(e.target.value);
        });
        
        document.getElementById('create-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createTracking();
        });
        
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchTrackings(e.target.value);
            }, 300);
        });
        
        document.getElementById('search-btn').addEventListener('click', () => {
            const query = document.getElementById('search-input').value;
            this.searchTrackings(query);
        });
        
        document.getElementById('btn-back').addEventListener('click', () => {
            this.goBack();
        });
        
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === document.getElementById('modal-overlay')) {
                this.closeModal();
            }
        });
        
        if (this.tg) {
            this.tg.onEvent('backButtonClicked', () => {
                const trackingModule = document.getElementById('tracking-module');
                if (trackingModule && !trackingModule.classList.contains('hidden')) {
                    if (this.currentSection === 'detail') {
                        this.goBack();
                    } else {
                        this.goToHome();
                    }
                }
            });
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
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
