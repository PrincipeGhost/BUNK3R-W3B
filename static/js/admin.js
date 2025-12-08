/**
 * BUNK3R Admin Panel JavaScript
 */

const AdminPanel = {
    currentSection: 'dashboard',
    charts: {},
    refreshInterval: null,
    usersPage: 1,
    usersPerPage: 20,
    txPage: 1,
    txPerPage: 20,
    
    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.setupLogsEventListeners();
        this.loadDashboard();
        this.startAutoRefresh();
    },
    
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item[data-section]');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.navigateTo(section);
            });
        });
        
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const sidebar = document.getElementById('adminSidebar');
        
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }
        
        const hash = window.location.hash.slice(1);
        if (hash && document.getElementById(`section-${hash}`)) {
            this.navigateTo(hash);
        }
    },
    
    navigateTo(section) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');
        
        document.querySelectorAll('.admin-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`section-${section}`)?.classList.add('active');
        
        const titles = {
            dashboard: 'Dashboard',
            realtime: 'Tiempo Real',
            users: 'Gestión de Usuarios',
            sessions: 'Sesiones Activas',
            transactions: 'Transacciones',
            wallets: 'Wallets',
            content: 'Contenido',
            reports: 'Reportes',
            virtualnumbers: 'Números Virtuales',
            bots: 'Gestión de Bots',
            support: 'Tickets de Soporte',
            faq: 'Preguntas Frecuentes',
            massmessages: 'Mensajes Masivos',
            logs: 'Logs',
            analytics: 'Analíticas',
            settings: 'Configuración',
            maintenance: 'Backup y Mantenimiento',
            notifications: 'Centro de Notificaciones',
            riskscore: 'Puntuación de Riesgo',
            relatedaccounts: 'Cuentas Relacionadas',
            anomalies: 'Detector de Anomalías',
            usertags: 'Sistema de Etiquetas',
            verifications: 'Cola de Verificaciones',
            shadowmode: 'Modo Shadow',
            marketplace: 'Marketplace'
        };
        
        document.getElementById('pageTitle').textContent = titles[section] || section;
        this.currentSection = section;
        window.location.hash = section;
        
        this.loadSectionData(section);
        
        document.getElementById('adminSidebar')?.classList.remove('open');
    },
    
    loadSectionData(section) {
        switch(section) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'realtime':
                this.loadRealtime();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'sessions':
                this.loadSessions();
                break;
            case 'transactions':
                this.loadTransactions();
                break;
            case 'wallets':
                this.loadWallets();
                break;
            case 'content':
                this.loadContent();
                break;
            case 'reports':
                this.loadReports();
                break;
            case 'virtualnumbers':
                this.loadVirtualNumbers();
                break;
            case 'bots':
                this.loadBots();
                break;
            case 'logs':
                this.loadLogs();
                break;
            case 'analytics':
                this.loadAnalytics();
                this.initAnalyticsTabs();
                break;
            case 'settings':
                this.loadSettings();
                break;
            case 'support':
                SupportModule.loadTickets();
                break;
            case 'faq':
                SupportModule.loadFAQs();
                break;
            case 'massmessages':
                SupportModule.loadMassMessages();
                break;
            case 'maintenance':
                this.loadMaintenance();
                break;
            case 'notifications':
                NotificationsModule.loadNotifications();
                NotificationsModule.loadTelegramSettings();
                break;
            case 'riskscore':
                RiskScoreModule.init();
                break;
            case 'relatedaccounts':
                RelatedAccountsModule.init();
                break;
            case 'anomalies':
                AnomaliesModule.init();
                break;
            case 'usertags':
                TagsModule.init();
                break;
            case 'verifications':
                VerificationsModule.init();
                break;
            case 'shadowmode':
                ShadowModule.init();
                break;
            case 'marketplace':
                MarketplaceModule.init();
                break;
        }
    },
    
    setupEventListeners() {
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadSectionData(this.currentSection);
            this.showToast('Datos actualizados', 'success');
        });
        
        document.getElementById('refreshActivity')?.addEventListener('click', () => {
            this.loadRecentActivity();
        });
        
        document.getElementById('userSearch')?.addEventListener('input', this.debounce(() => {
            this.loadUsers();
        }, 500));
        
        document.getElementById('userStatusFilter')?.addEventListener('change', () => {
            this.loadUsers();
        });
        
        document.getElementById('exportUsersBtn')?.addEventListener('click', () => {
            this.exportUsers();
        });
        
        document.getElementById('exportTxBtn')?.addEventListener('click', () => {
            this.exportTransactions();
        });
        
        document.getElementById('fillPoolBtn')?.addEventListener('click', () => {
            this.fillWalletPool();
        });
        
        document.getElementById('consolidateBtn')?.addEventListener('click', () => {
            this.consolidateWallets();
        });
        
        document.getElementById('walletStatusFilter')?.addEventListener('change', () => {
            this.loadWallets();
        });
        
        document.getElementById('savePoolConfigBtn')?.addEventListener('click', () => {
            this.savePoolConfig();
        });
        
        document.querySelectorAll('[data-blockchain-tab]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-blockchain-tab]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const txType = btn.dataset.blockchainTab;
                this.loadBlockchainHistory(txType === 'all' ? '' : txType);
            });
        });
        
        document.getElementById('usersPrevBtn')?.addEventListener('click', () => {
            if (this.usersPage > 1) {
                this.usersPage--;
                this.loadUsers();
            }
        });
        
        document.getElementById('usersNextBtn')?.addEventListener('click', () => {
            this.usersPage++;
            this.loadUsers();
        });
        
        document.querySelectorAll('.reports-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.reports-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.loadReports(btn.dataset.status);
            });
        });
        
        document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
            el.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
            });
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const parent = btn.parentElement;
                parent.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        
        document.getElementById('usersChartPeriod')?.addEventListener('change', () => {
            this.initCharts();
        });
        
        document.getElementById('txChartPeriod')?.addEventListener('change', () => {
            this.initCharts();
        });
        
        document.getElementById('revenueChartPeriod')?.addEventListener('change', () => {
            this.initCharts();
        });
        
        document.querySelectorAll('.transactions-tabs .tx-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.transactions-tabs .tx-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const tabType = btn.dataset.tab;
                
                const purchasesSection = document.getElementById('purchasesSection');
                const transactionsSection = document.getElementById('transactionsSection');
                const withdrawalsSection = document.getElementById('withdrawalsSection');
                const p2pSection = document.getElementById('p2pSection');
                const periodStatsSection = document.getElementById('periodStatsSection');
                
                purchasesSection.style.display = 'none';
                transactionsSection.style.display = 'none';
                withdrawalsSection.style.display = 'none';
                p2pSection.style.display = 'none';
                periodStatsSection.style.display = 'none';
                
                if (tabType === 'purchases') {
                    purchasesSection.style.display = 'block';
                    this.loadPurchases();
                } else if (tabType === 'withdrawal') {
                    withdrawalsSection.style.display = 'block';
                    this.loadWithdrawals();
                } else if (tabType === 'transfer') {
                    p2pSection.style.display = 'block';
                    this.loadP2PTransfers();
                } else if (tabType === 'periodStats') {
                    periodStatsSection.style.display = 'block';
                    this.loadPeriodStats();
                } else {
                    transactionsSection.style.display = 'block';
                    document.getElementById('txTypeFilter').value = '';
                    this.loadTransactions();
                }
            });
        });
        
        document.getElementById('purchaseStatusFilter')?.addEventListener('change', () => {
            this.loadPurchases();
        });
        
        document.getElementById('withdrawalStatusFilter')?.addEventListener('change', () => {
            this.loadWithdrawals();
        });
        
        document.getElementById('p2pFilter')?.addEventListener('change', () => {
            this.loadP2PTransfers();
        });
        
        document.getElementById('p2pSearch')?.addEventListener('input', this.debounce(() => {
            this.loadP2PTransfers();
        }, 500));
        
        document.getElementById('txSearch')?.addEventListener('input', this.debounce(() => {
            this.loadTransactions();
        }, 500));
        
        document.getElementById('txDateFrom')?.addEventListener('change', () => {
            this.loadTransactions();
        });
        
        document.getElementById('txDateTo')?.addEventListener('change', () => {
            this.loadTransactions();
        });
        
        document.getElementById('confirmProcessWithdrawal')?.addEventListener('click', () => {
            this.processWithdrawal();
        });
        
        document.getElementById('confirmRejectWithdrawal')?.addEventListener('click', () => {
            this.rejectWithdrawal();
        });
        
        document.getElementById('loadPeriodStats')?.addEventListener('click', () => {
            this.loadPeriodStats();
        });
        
        document.getElementById('exportPeriodCSV')?.addEventListener('click', () => {
            this.exportPeriodCSV();
        });
        
        document.getElementById('exportPeriodPDF')?.addEventListener('click', () => {
            this.exportPeriodReport();
        });
        
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const period = btn.dataset.period;
                this.setPeriodDates(period);
            });
        });
        
        document.getElementById('contentSearch')?.addEventListener('input', this.debounce(() => {
            this.loadContentPosts();
        }, 500));
        
        document.getElementById('contentTypeFilter')?.addEventListener('change', () => {
            this.loadContentPosts();
        });
        
        document.getElementById('storiesStatusFilter')?.addEventListener('change', () => {
            this.loadStories();
        });
        
        document.getElementById('hashtagSearch')?.addEventListener('input', this.debounce(() => {
            this.loadHashtags();
        }, 500));
        
        document.getElementById('hashtagStatusFilter')?.addEventListener('change', () => {
            this.loadHashtags();
        });
        
        this.initPeriodDates();
    },
    
    initPeriodDates() {
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        
        const fromInput = document.getElementById('periodDateFrom');
        const toInput = document.getElementById('periodDateTo');
        
        if (fromInput && toInput) {
            fromInput.value = weekAgo.toISOString().split('T')[0];
            toInput.value = today.toISOString().split('T')[0];
        }
    },
    
    setPeriodDates(period) {
        const today = new Date();
        const fromInput = document.getElementById('periodDateFrom');
        const toInput = document.getElementById('periodDateTo');
        
        if (!fromInput || !toInput) return;
        
        toInput.value = today.toISOString().split('T')[0];
        
        if (period === 'custom') {
            return;
        }
        
        const days = parseInt(period);
        const fromDate = new Date(today);
        fromDate.setDate(fromDate.getDate() - days);
        fromInput.value = fromDate.toISOString().split('T')[0];
    },
    
    async loadDashboard() {
        this.showDashboardLoading();
        
        try {
            const [stats, activity, alerts] = await Promise.all([
                this.fetchAPI('/api/admin/dashboard/stats'),
                this.fetchAPI('/api/admin/dashboard/activity'),
                this.fetchAPI('/api/admin/dashboard/alerts')
            ]);
            
            if (stats.success) {
                this.updateMetrics(stats.data);
            } else {
                this.showMetricsError();
            }
            
            if (activity.success) {
                this.renderActivity(activity.data);
            }
            
            if (alerts.success) {
                this.renderAlerts(alerts.data);
            }
            
            await this.initCharts();
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.loadFallbackDashboard();
        }
    },
    
    clearMetricsState() {
        const metricIds = ['totalUsers', 'activeToday', 'totalB3C', 'hotWalletBalance', 'transactions24h', 'revenueToday'];
        metricIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.remove('no-data', 'zero-data', 'loading', 'error');
                const parentCard = el.closest('.metric-card');
                if (parentCard) {
                    parentCard.classList.remove('no-data-state', 'zero-data-state', 'error-state');
                }
            }
        });
    },
    
    showDashboardLoading() {
        this.clearMetricsState();
        
        const metricIds = ['totalUsers', 'activeToday', 'totalB3C', 'hotWalletBalance', 'transactions24h', 'revenueToday'];
        metricIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('loading');
                el.textContent = '...';
            }
        });
        
        const activityList = document.getElementById('activityList');
        if (activityList) {
            activityList.innerHTML = '<div class="loading-indicator"><div class="spinner"></div><span>Cargando actividad...</span></div>';
        }
        
        const systemAlerts = document.getElementById('systemAlerts');
        if (systemAlerts) {
            systemAlerts.innerHTML = '<div class="loading-indicator"><div class="spinner"></div><span>Cargando alertas...</span></div>';
        }
    },
    
    showMetricsError() {
        this.clearMetricsState();
        
        const metricIds = ['totalUsers', 'activeToday', 'totalB3C', 'hotWalletBalance', 'transactions24h', 'revenueToday'];
        metricIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = '-';
                el.classList.add('error');
            }
        });
    },
    
    loadFallbackDashboard() {
        this.clearMetricsState();
        
        const metricIds = ['totalUsers', 'activeToday', 'totalB3C', 'hotWalletBalance', 'transactions24h', 'revenueToday'];
        metricIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = '-';
                el.classList.add('no-data');
                const parentCard = el.closest('.metric-card');
                if (parentCard) parentCard.classList.add('no-data-state');
            }
        });
        
        const activityList = document.getElementById('activityList');
        if (activityList) {
            activityList.innerHTML = '<div class="empty-state-retry"><span>No se pudo cargar la actividad</span><button class="retry-btn" onclick="AdminPanel.loadDashboard()">Reintentar</button></div>';
        }
        
        const systemAlerts = document.getElementById('systemAlerts');
        if (systemAlerts) {
            systemAlerts.innerHTML = '<div class="empty-state-retry"><span>No se pudieron cargar las alertas</span></div>';
        }
    },
    
    updateMetrics(data) {
        this.clearMetricsState();
        
        const metrics = [
            { id: 'totalUsers', value: data.totalUsers, decimals: 0 },
            { id: 'activeToday', value: data.activeToday, decimals: 0 },
            { id: 'totalB3C', value: data.totalB3C, decimals: 0 },
            { id: 'hotWalletBalance', value: data.hotWalletBalance, decimals: 2 },
            { id: 'transactions24h', value: data.transactions24h, decimals: 0 },
            { id: 'revenueToday', value: data.revenueToday, decimals: 4 }
        ];
        
        metrics.forEach(metric => {
            const el = document.getElementById(metric.id);
            if (!el) return;
            
            const parentCard = el.closest('.metric-card');
            
            if (metric.value === undefined || metric.value === null) {
                el.textContent = '-';
                el.classList.add('no-data');
                if (parentCard) parentCard.classList.add('no-data-state');
            } else if (metric.value === 0) {
                el.textContent = '0';
                el.classList.add('zero-data');
                if (parentCard) parentCard.classList.add('zero-data-state');
            } else {
                el.textContent = this.formatNumber(metric.value, metric.decimals);
            }
        });
        
        const usersChange = data.usersChange || 0;
        const changeEl = document.getElementById('usersChange');
        if (changeEl) {
            changeEl.className = `metric-change ${usersChange >= 0 ? 'positive' : 'negative'}`;
            const spanEl = changeEl.querySelector('span');
            if (spanEl) {
                spanEl.textContent = `${usersChange >= 0 ? '+' : ''}${usersChange}%`;
            }
        }
    },
    
    renderActivity(activities) {
        const container = document.getElementById('activityList');
        if (!activities || activities.length === 0) {
            container.innerHTML = '<div class="empty-state">Sin actividad reciente</div>';
            return;
        }
        
        container.innerHTML = activities.map(act => `
            <div class="activity-item">
                <div class="activity-icon ${act.type}">
                    ${this.getActivityIcon(act.type)}
                </div>
                <div class="activity-content">
                    <div class="activity-text">${this.escapeHtml(act.message)}</div>
                    <div class="activity-time">${this.timeAgo(act.timestamp)}</div>
                </div>
            </div>
        `).join('');
    },
    
    renderAlerts(alerts) {
        const container = document.getElementById('systemAlerts');
        const countEl = document.getElementById('alertsCount');
        
        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="no-alerts">Sin alertas activas</div>';
            countEl.textContent = '0';
            return;
        }
        
        countEl.textContent = alerts.length;
        container.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.level}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <div class="alert-content">
                    <div class="alert-text">${this.escapeHtml(alert.message)}</div>
                </div>
            </div>
        `).join('');
    },
    
    async initCharts() {
        const usersCtx = document.getElementById('usersChart');
        const txCtx = document.getElementById('transactionsChart');
        const revenueCtx = document.getElementById('revenueChart');
        
        const usersPeriod = document.getElementById('usersChartPeriod')?.value || '30';
        const txPeriod = parseInt(document.getElementById('txChartPeriod')?.value || '7');
        const revenuePeriod = parseInt(document.getElementById('revenueChartPeriod')?.value || '7');
        
        try {
            const chartData = await this.fetchAPI(`/api/admin/dashboard/charts?period=${usersPeriod}`);
            
            if (chartData.success && chartData.data) {
                const usersLabels = chartData.data.users.map(d => d.label);
                const usersData = chartData.data.users.map(d => d.count);
                const txLabels = chartData.data.transactions.slice(-txPeriod).map(d => d.label);
                const txData = chartData.data.transactions.slice(-txPeriod).map(d => d.count);
                const revenueLabels = (chartData.data.revenue || []).slice(-revenuePeriod).map(d => d.label);
                const revenueData = (chartData.data.revenue || []).slice(-revenuePeriod).map(d => d.amount);
                
                if (usersCtx) {
                    if (this.charts.users) {
                        this.charts.users.data.labels = usersLabels;
                        this.charts.users.data.datasets[0].data = usersData;
                        this.charts.users.update();
                    } else {
                        this.charts.users = new Chart(usersCtx, {
                            type: 'line',
                            data: {
                                labels: usersLabels,
                                datasets: [{
                                    label: 'Nuevos usuarios',
                                    data: usersData,
                                    borderColor: '#F0B90B',
                                    backgroundColor: 'rgba(240, 185, 11, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: false }
                                },
                                scales: {
                                    x: {
                                        grid: { color: 'rgba(255,255,255,0.05)' },
                                        ticks: { color: '#848E9C' }
                                    },
                                    y: {
                                        grid: { color: 'rgba(255,255,255,0.05)' },
                                        ticks: { color: '#848E9C' }
                                    }
                                }
                            }
                        });
                    }
                }
                
                if (txCtx) {
                    if (this.charts.transactions) {
                        this.charts.transactions.data.labels = txLabels;
                        this.charts.transactions.data.datasets[0].data = txData;
                        this.charts.transactions.update();
                    } else {
                        this.charts.transactions = new Chart(txCtx, {
                            type: 'bar',
                            data: {
                                labels: txLabels,
                                datasets: [{
                                    label: 'Transacciones',
                                    data: txData,
                                    backgroundColor: 'rgba(240, 185, 11, 0.6)',
                                    borderRadius: 6
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: false }
                                },
                                scales: {
                                    x: {
                                        grid: { display: false },
                                        ticks: { color: '#848E9C' }
                                    },
                                    y: {
                                        grid: { color: 'rgba(255,255,255,0.05)' },
                                        ticks: { color: '#848E9C' }
                                    }
                                }
                            }
                        });
                    }
                }
                
                if (revenueCtx) {
                    if (this.charts.revenue) {
                        this.charts.revenue.data.labels = revenueLabels;
                        this.charts.revenue.data.datasets[0].data = revenueData;
                        this.charts.revenue.update();
                    } else {
                        this.charts.revenue = new Chart(revenueCtx, {
                            type: 'line',
                            data: {
                                labels: revenueLabels,
                                datasets: [{
                                    label: 'Comisiones (TON)',
                                    data: revenueData,
                                    borderColor: '#27ae60',
                                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: false }
                                },
                                scales: {
                                    x: {
                                        grid: { color: 'rgba(255,255,255,0.05)' },
                                        ticks: { color: '#848E9C' }
                                    },
                                    y: {
                                        grid: { color: 'rgba(255,255,255,0.05)' },
                                        ticks: { color: '#848E9C' }
                                    }
                                }
                            }
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.initFallbackCharts(usersCtx, txCtx, revenueCtx);
        }
    },
    
    initFallbackCharts(usersCtx, txCtx, revenueCtx) {
        if (usersCtx && !this.charts.users) {
            this.charts.users = new Chart(usersCtx, {
                type: 'line',
                data: {
                    labels: this.getLast30Days(),
                    datasets: [{
                        label: 'Nuevos usuarios',
                        data: Array(30).fill(0),
                        borderColor: '#F0B90B',
                        backgroundColor: 'rgba(240, 185, 11, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } }
                    }
                }
            });
        }
        
        if (txCtx && !this.charts.transactions) {
            this.charts.transactions = new Chart(txCtx, {
                type: 'bar',
                data: {
                    labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                    datasets: [{
                        label: 'Transacciones',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(240, 185, 11, 0.6)',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#848E9C' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } }
                    }
                }
            });
        }
        
        if (revenueCtx && !this.charts.revenue) {
            this.charts.revenue = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                    datasets: [{
                        label: 'Comisiones (TON)',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } }
                    }
                }
            });
        }
    },
    
    async loadUsers() {
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Cargando usuarios...</td></tr>';
        
        try {
            const search = document.getElementById('userSearch')?.value || '';
            const status = document.getElementById('userStatusFilter')?.value || '';
            
            const response = await this.fetchAPI(`/api/admin/users?page=${this.usersPage}&limit=${this.usersPerPage}&search=${encodeURIComponent(search)}&status=${status}`);
            
            if (response.success && response.users) {
                this.renderUsersTable(response.users);
                this.updateUsersPagination(response.total, response.page, response.pages);
            } else {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No se encontraron usuarios</td></tr>';
            }
        } catch (error) {
            console.error('Error loading users:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Error al cargar usuarios</td></tr>';
        }
    },
    
    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        
        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No se encontraron usuarios</td></tr>';
            return;
        }
        
        const usersHtml = users.map(user => {
            const safeUserId = typeof escapeForOnclick !== 'undefined' ? escapeForOnclick(user.user_id) : user.user_id;
            return `
            <tr>
                <td><code>${this.escapeHtml(user.user_id)}</code></td>
                <td>
                    <div class="user-cell">
                        <div class="user-avatar-sm">${(user.first_name || 'U')[0].toUpperCase()}</div>
                        <div class="user-info">
                            <span class="user-name">${this.escapeHtml(user.first_name || 'Sin nombre')}</span>
                            <span class="user-username">@${this.escapeHtml(user.username || 'N/A')}</span>
                        </div>
                    </div>
                </td>
                <td>${this.escapeHtml(user.first_name || '-')}</td>
                <td>${this.formatDate(user.created_at)}</td>
                <td>${this.formatDate(user.last_seen)}</td>
                <td>${this.formatNumber(user.credits || 0)}</td>
                <td>
                    <span class="status-badge ${user.is_banned ? 'banned' : 'active'}">
                        ${user.is_banned ? 'Baneado' : 'Activo'}
                    </span>
                </td>
                <td>
                    <div class="action-btns">
                        <button class="action-btn" onclick="AdminPanel.viewUser('${safeUserId}')">Ver</button>
                        <button class="action-btn danger" onclick="AdminPanel.banUser('${safeUserId}', ${!user.is_banned})">
                            ${user.is_banned ? 'Desbanear' : 'Banear'}
                        </button>
                    </div>
                </td>
            </tr>
        `;}).join('');
        if (typeof SafeDOM !== 'undefined') {
            SafeDOM.setHTML(tbody, usersHtml, { allowEvents: true });
        } else {
            tbody.innerHTML = usersHtml;
        }
    },
    
    updateUsersPagination(total, page, pages) {
        document.getElementById('usersPageInfo').textContent = `Página ${page} de ${pages}`;
        document.getElementById('usersPrevBtn').disabled = page <= 1;
        document.getElementById('usersNextBtn').disabled = page >= pages;
        this.usersPage = page;
    },
    
    async viewUser(userId) {
        const modal = document.getElementById('userDetailModal');
        const content = document.getElementById('userDetailContent');
        
        content.innerHTML = '<div class="loading-state">Cargando información completa...</div>';
        modal.classList.add('active');
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/detail`);
            
            if (response.success && response.user) {
                const user = response.user;
                const ips = response.ips || [];
                const devices = response.devices || [];
                const activityLog = response.activity_log || [];
                const notes = response.notes || [];
                const transactions = response.transactions || [];
                const fraudAlerts = response.fraud_alerts || [];
                
                content.innerHTML = `
                    <div class="user-detail-header">
                        <div class="user-detail-avatar">${(user.first_name || 'U')[0].toUpperCase()}</div>
                        <div class="user-detail-info">
                            <h3>${this.escapeHtml(user.first_name || 'Sin nombre')}</h3>
                            <div class="username">@${this.escapeHtml(user.username || 'N/A')}</div>
                            <div class="user-id">ID: ${user.user_id}</div>
                            ${fraudAlerts.length > 0 ? `<span class="fraud-alert-badge">Alertas de fraude: ${fraudAlerts.length}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="user-detail-tabs">
                        <button class="tab-btn active" data-tab="info">Info</button>
                        <button class="tab-btn" data-tab="ips">IPs (${ips.length})</button>
                        <button class="tab-btn" data-tab="devices">Dispositivos (${devices.length})</button>
                        <button class="tab-btn" data-tab="activity">Actividad (${activityLog.length})</button>
                        <button class="tab-btn" data-tab="transactions">Transacciones (${transactions.length})</button>
                        <button class="tab-btn" data-tab="notes">Notas (${notes.length})</button>
                    </div>
                    
                    <div class="tab-content active" id="tab-info">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Fecha de registro</label>
                                <div class="value">${this.formatDate(user.created_at)}</div>
                            </div>
                            <div class="detail-item">
                                <label>Última conexión</label>
                                <div class="value">${this.formatDate(user.last_seen)}</div>
                            </div>
                            <div class="detail-item">
                                <label>Balance B3C</label>
                                <div class="value">${this.formatNumber(user.credits || 0)} B3C</div>
                            </div>
                            <div class="detail-item">
                                <label>Estado</label>
                                <div class="value">
                                    <span class="status-badge ${user.is_banned ? 'banned' : 'active'}">
                                        ${user.is_banned ? 'Baneado' : 'Activo'}
                                    </span>
                                </div>
                            </div>
                            <div class="detail-item">
                                <label>Idioma</label>
                                <div class="value">${user.language_code || 'N/A'}</div>
                            </div>
                            <div class="detail-item">
                                <label>Wallet</label>
                                <div class="value" style="font-family: monospace; font-size: 11px; word-break: break-all;">
                                    ${user.wallet_address || 'No conectada'}
                                </div>
                            </div>
                            <div class="detail-item">
                                <label>IP Actual</label>
                                <div class="value">${user.last_ip || 'N/A'}</div>
                            </div>
                            <div class="detail-item">
                                <label>Total Transacciones</label>
                                <div class="value">${user.total_transactions || 0}</div>
                            </div>
                        </div>
                        ${fraudAlerts.length > 0 ? `
                            <div class="fraud-alerts-section">
                                <h4>Alertas de Fraude</h4>
                                <div class="fraud-alerts-list">
                                    ${fraudAlerts.map(alert => `
                                        <div class="fraud-alert-item ${alert.level}">
                                            <span class="alert-type">${this.escapeHtml(alert.type)}</span>
                                            <span class="alert-desc">${this.escapeHtml(alert.description)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="tab-content" id="tab-ips">
                        ${ips.length > 0 ? `
                            <table class="mini-table">
                                <thead>
                                    <tr>
                                        <th>IP</th>
                                        <th>País</th>
                                        <th>Primera vez</th>
                                        <th>Última vez</th>
                                        <th>Usos</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${ips.map(ip => `
                                        <tr>
                                            <td><code>${this.escapeHtml(ip.ip_address)}</code></td>
                                            <td>${this.escapeHtml(ip.country || 'N/A')}</td>
                                            <td>${this.formatDate(ip.first_seen)}</td>
                                            <td>${this.formatDate(ip.last_seen)}</td>
                                            <td>${ip.login_count || 1}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<div class="empty-state">Sin historial de IPs</div>'}
                    </div>
                    
                    <div class="tab-content" id="tab-devices">
                        ${devices.length > 0 ? `
                            <table class="mini-table">
                                <thead>
                                    <tr>
                                        <th>Dispositivo</th>
                                        <th>Navegador</th>
                                        <th>SO</th>
                                        <th>Última actividad</th>
                                        <th>Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${devices.map(d => `
                                        <tr>
                                            <td>${this.escapeHtml(d.device_name || 'Desconocido')}</td>
                                            <td>${this.escapeHtml(d.browser || 'N/A')}</td>
                                            <td>${this.escapeHtml(d.os || 'N/A')}</td>
                                            <td>${this.formatDate(d.last_activity)}</td>
                                            <td><span class="status-badge ${d.is_trusted ? 'active' : 'pending'}">${d.is_trusted ? 'Confiado' : 'Nuevo'}</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<div class="empty-state">Sin dispositivos registrados</div>'}
                    </div>
                    
                    <div class="tab-content" id="tab-activity">
                        ${activityLog.length > 0 ? `
                            <div class="activity-log-list">
                                ${activityLog.map(log => `
                                    <div class="activity-log-item">
                                        <span class="log-time">${this.formatDate(log.created_at)}</span>
                                        <span class="log-type ${log.activity_type}">${this.escapeHtml(log.activity_type)}</span>
                                        <span class="log-desc">${this.escapeHtml(log.description || '')}</span>
                                        <span class="log-ip">${this.escapeHtml(log.ip_address || '')}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<div class="empty-state">Sin actividad registrada</div>'}
                    </div>
                    
                    <div class="tab-content" id="tab-transactions">
                        ${transactions.length > 0 ? `
                            <table class="mini-table">
                                <thead>
                                    <tr>
                                        <th>Tipo</th>
                                        <th>Monto</th>
                                        <th>Estado</th>
                                        <th>Fecha</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${transactions.map(tx => `
                                        <tr>
                                            <td>${this.escapeHtml(tx.type)}</td>
                                            <td>${this.formatNumber(tx.amount, 4)} ${tx.currency || 'B3C'}</td>
                                            <td><span class="status-badge ${tx.status}">${tx.status}</span></td>
                                            <td>${this.formatDate(tx.created_at)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<div class="empty-state">Sin transacciones</div>'}
                    </div>
                    
                    <div class="tab-content" id="tab-notes">
                        <div class="add-note-form">
                            <textarea id="newNoteText" placeholder="Agregar nota interna sobre este usuario..." rows="2"></textarea>
                            <button class="btn-primary" onclick="AdminPanel.addUserNote('${user.user_id}')">Agregar Nota</button>
                        </div>
                        ${notes.length > 0 ? `
                            <div class="notes-list">
                                ${notes.map(note => `
                                    <div class="note-item">
                                        <div class="note-header">
                                            <span class="note-admin">${this.escapeHtml(note.admin_name || 'Admin')}</span>
                                            <span class="note-date">${this.formatDate(note.created_at)}</span>
                                        </div>
                                        <div class="note-content">${this.escapeHtml(note.content)}</div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<div class="empty-state" style="margin-top: 16px;">Sin notas</div>'}
                    </div>
                    
                    <div class="user-actions-grid">
                        <div class="actions-group">
                            <h4>Acciones Básicas</h4>
                            <button class="btn-secondary" onclick="AdminPanel.adjustBalance('${user.user_id}')">
                                Ajustar Balance
                            </button>
                            <button class="btn-secondary" onclick="AdminPanel.sendNotification('${user.user_id}')">
                                Enviar Notificación
                            </button>
                            <button class="btn-warning" onclick="AdminPanel.logoutUser('${user.user_id}')">
                                Cerrar Sesiones
                            </button>
                            <button class="btn-danger" onclick="AdminPanel.banUser('${user.user_id}', ${!user.is_banned})">
                                ${user.is_banned ? 'Desbanear' : 'Banear Usuario'}
                            </button>
                        </div>
                        <div class="actions-group">
                            <h4>Acciones Avanzadas</h4>
                            <button class="btn-secondary" onclick="ShadowModule.startSession('${user.user_id}')">
                                Modo Shadow
                            </button>
                            <button class="btn-secondary" onclick="AdminPanel.openTagsModal('${user.user_id}')">
                                Gestionar Tags
                            </button>
                            <button class="btn-secondary" onclick="AdminPanel.viewRelatedAccounts('${user.user_id}')">
                                Cuentas Relacionadas
                            </button>
                            <button class="btn-secondary" onclick="AdminPanel.adjustRiskScore('${user.user_id}')">
                                Ajustar Riesgo
                            </button>
                        </div>
                    </div>
                `;
                
                this.setupUserDetailTabs();
            } else {
                content.innerHTML = '<div class="empty-state">Error al cargar usuario</div>';
            }
        } catch (error) {
            console.error('Error loading user:', error);
            content.innerHTML = '<div class="empty-state">Error al cargar usuario</div>';
        }
    },
    
    setupUserDetailTabs() {
        const tabs = document.querySelectorAll('.user-detail-tabs .tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
            });
        });
    },
    
    async addUserNote(userId) {
        const noteText = document.getElementById('newNoteText')?.value?.trim();
        if (!noteText) {
            this.showToast('Escribe una nota antes de guardar', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/note`, {
                method: 'POST',
                body: JSON.stringify({ content: noteText })
            });
            
            if (response.success) {
                this.showToast('Nota agregada correctamente', 'success');
                this.viewUser(userId);
            } else {
                this.showToast(response.error || 'Error al agregar nota', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al agregar nota', 'error');
        }
    },
    
    async logoutUser(userId) {
        if (!confirm('¿Cerrar todas las sesiones activas de este usuario?')) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/logout`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(`Sesiones cerradas: ${response.sessions_closed || 0}`, 'success');
            } else {
                this.showToast(response.error || 'Error al cerrar sesiones', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al cerrar sesiones', 'error');
        }
    },
    
    async sendNotification(userId) {
        const title = prompt('Título de la notificación:');
        if (!title) return;
        
        const message = prompt('Mensaje de la notificación:');
        if (!message) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/notify`, {
                method: 'POST',
                body: JSON.stringify({ title, message })
            });
            
            if (response.success) {
                this.showToast('Notificación enviada correctamente', 'success');
            } else {
                this.showToast(response.error || 'Error al enviar notificación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al enviar notificación', 'error');
        }
    },
    
    async adjustBalance(userId) {
        const amountStr = prompt('Cantidad a ajustar (usa - para restar):');
        if (!amountStr) return;
        
        const amount = parseFloat(amountStr);
        if (isNaN(amount)) {
            this.showToast('Cantidad inválida', 'error');
            return;
        }
        
        const reason = prompt('Razón del ajuste:');
        if (!reason) {
            this.showToast('Debes proporcionar una razón', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/balance`, {
                method: 'POST',
                body: JSON.stringify({ amount, reason })
            });
            
            if (response.success) {
                this.showToast(`Balance ajustado. Nuevo balance: ${this.formatNumber(response.new_balance)} B3C`, 'success');
                this.viewUser(userId);
            } else {
                this.showToast(response.error || 'Error al ajustar balance', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al ajustar balance', 'error');
        }
    },
    
    async banUser(userId, shouldBan) {
        const action = shouldBan ? 'banear' : 'desbanear';
        if (!confirm(`¿Estás seguro de ${action} este usuario?`)) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/ban`, {
                method: 'POST',
                body: JSON.stringify({ banned: shouldBan })
            });
            
            if (response.success) {
                this.showToast(`Usuario ${shouldBan ? 'baneado' : 'desbaneado'} correctamente`, 'success');
                this.loadUsers();
                document.getElementById('userDetailModal').classList.remove('active');
            } else {
                this.showToast(response.error || 'Error al realizar acción', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al realizar acción', 'error');
        }
    },
    
    async openTagsModal(userId) {
        try {
            const response = await this.fetchAPI('/api/admin/tags');
            if (!response.success) {
                this.showToast('Error al cargar etiquetas', 'error');
                return;
            }
            
            const tags = response.tags || [];
            const html = `
                <div class="tags-modal-content">
                    <h3>Gestionar Etiquetas</h3>
                    <p>Selecciona las etiquetas para este usuario:</p>
                    <div class="tags-checkbox-list">
                        ${tags.map(tag => `
                            <label class="tag-checkbox">
                                <input type="checkbox" value="${tag.id}" data-color="${tag.color}">
                                <span class="tag-badge" style="background: ${tag.color}">${this.escapeHtml(tag.name)}</span>
                            </label>
                        `).join('')}
                    </div>
                    <div class="modal-actions">
                        <button class="btn-secondary" onclick="document.getElementById('tagsAssignModal').classList.remove('active')">Cancelar</button>
                        <button class="btn-primary" onclick="AdminPanel.saveUserTags('${userId}')">Guardar</button>
                    </div>
                </div>
            `;
            
            let modal = document.getElementById('tagsAssignModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'tagsAssignModal';
                modal.className = 'modal';
                modal.innerHTML = `<div class="modal-content">${html}</div>`;
                document.body.appendChild(modal);
            } else {
                modal.querySelector('.modal-content').innerHTML = html;
            }
            modal.classList.add('active');
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al abrir gestor de etiquetas', 'error');
        }
    },
    
    async saveUserTags(userId) {
        const modal = document.getElementById('tagsAssignModal');
        const checkboxes = modal.querySelectorAll('input[type="checkbox"]:checked');
        const tagIds = Array.from(checkboxes).map(cb => cb.value);
        
        try {
            const response = await this.fetchAPI(`/api/admin/users/${userId}/tags`, {
                method: 'POST',
                body: JSON.stringify({ tags: tagIds })
            });
            
            if (response.success) {
                this.showToast('Etiquetas actualizadas', 'success');
                modal.classList.remove('active');
            } else {
                this.showToast(response.error || 'Error al guardar etiquetas', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al guardar etiquetas', 'error');
        }
    },
    
    async viewRelatedAccounts(userId) {
        document.getElementById('userDetailModal').classList.remove('active');
        this.navigateTo('relatedaccounts');
        setTimeout(() => {
            RelatedAccountsModule.searchUserId = userId;
            RelatedAccountsModule.loadRelatedAccounts();
        }, 100);
    },
    
    async adjustRiskScore(userId) {
        const adjustment = prompt('Ingresa el ajuste de puntuación de riesgo (-100 a +100):');
        if (!adjustment) return;
        
        const numAdjustment = parseInt(adjustment);
        if (isNaN(numAdjustment) || numAdjustment < -100 || numAdjustment > 100) {
            this.showToast('Ajuste inválido. Debe ser entre -100 y +100', 'error');
            return;
        }
        
        const reason = prompt('Razón del ajuste:');
        if (!reason) {
            this.showToast('Debes proporcionar una razón', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI('/api/admin/risk-scores/adjust', {
                method: 'POST',
                body: JSON.stringify({ 
                    userId: userId, 
                    adjustment: numAdjustment,
                    reason: reason
                })
            });
            
            if (response.success) {
                this.showToast(`Puntuación de riesgo ajustada. Nuevo score: ${response.newScore}`, 'success');
                this.viewUser(userId);
            } else {
                this.showToast(response.error || 'Error al ajustar puntuación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al ajustar puntuación de riesgo', 'error');
        }
    },
    
    async loadTransactions() {
        const tbody = document.getElementById('transactionsTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Cargando transacciones...</td></tr>';
        
        await this.loadFinancialDashboard();
        
        try {
            const type = document.getElementById('txTypeFilter')?.value || '';
            const status = document.getElementById('txStatusFilter')?.value || '';
            
            const response = await this.fetchAPI(`/api/admin/transactions?page=${this.txPage}&limit=${this.txPerPage}&type=${type}&status=${status}`);
            
            if (response.success && response.transactions) {
                this.renderTransactionsTable(response.transactions);
                
                document.getElementById('txTotalVolume').textContent = `${this.formatNumber(response.totalVolume || 0, 4)} TON`;
                document.getElementById('txTotalFees').textContent = `${this.formatNumber(response.totalFees || 0, 4)} TON`;
                document.getElementById('txCount').textContent = this.formatNumber(response.total || 0);
            } else {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No se encontraron transacciones</td></tr>';
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Error al cargar transacciones</td></tr>';
        }
    },
    
    async loadFinancialDashboard() {
        try {
            const response = await this.fetchAPI('/api/admin/financial/stats');
            
            if (response.success && response.data) {
                const data = response.data;
                
                document.getElementById('finTotalB3C').textContent = this.formatNumber(data.totalB3CSold || 0, 2);
                document.getElementById('finTotalTON').textContent = this.formatNumber(data.totalTONReceived || 0, 4);
                document.getElementById('finTotalCommissions').textContent = this.formatNumber(data.totalCommissions || 0, 4);
                document.getElementById('finMonthVolume').textContent = this.formatNumber(data.monthVolume || 0, 2);
                
                const changeEl = document.getElementById('finVolumeChange');
                if (changeEl) {
                    const change = data.volumeChange || 0;
                    changeEl.className = `financial-change ${change >= 0 ? 'positive' : 'negative'}`;
                    changeEl.querySelector('span').textContent = `${change >= 0 ? '+' : ''}${change}%`;
                }
                
                document.getElementById('finPendingWithdrawals').textContent = data.pendingWithdrawals || 0;
                document.getElementById('finPendingAmount').textContent = `${this.formatNumber(data.pendingWithdrawalsAmount || 0, 2)} B3C`;
                
                const pendingCard = document.getElementById('pendingWithdrawalsCard');
                if (pendingCard) {
                    pendingCard.classList.toggle('has-pending', data.pendingWithdrawals > 0);
                }
                
                const maxVolume = Math.max(data.monthVolume || 1, data.lastMonthVolume || 1);
                const currentPercent = maxVolume > 0 ? ((data.monthVolume || 0) / maxVolume) * 100 : 0;
                const lastPercent = maxVolume > 0 ? ((data.lastMonthVolume || 0) / maxVolume) * 100 : 0;
                
                document.getElementById('finCurrentMonthBar').style.width = `${currentPercent}%`;
                document.getElementById('finLastMonthBar').style.width = `${lastPercent}%`;
                document.getElementById('finCurrentMonthValue').textContent = this.formatNumber(data.monthVolume || 0, 2) + ' B3C';
                document.getElementById('finLastMonthValue').textContent = this.formatNumber(data.lastMonthVolume || 0, 2) + ' B3C';
                
                this.initFinancialCharts(data.dailyRevenue || [], data.dailyVolume || []);
            }
        } catch (error) {
            console.error('Error loading financial dashboard:', error);
        }
    },
    
    initFinancialCharts(revenueData, volumeData) {
        const revenueCtx = document.getElementById('finRevenueChart');
        const volumeCtx = document.getElementById('finVolumeChart');
        
        if (revenueCtx) {
            if (this.charts.finRevenue) {
                this.charts.finRevenue.data.labels = revenueData.map(d => d.label);
                this.charts.finRevenue.data.datasets[0].data = revenueData.map(d => d.amount);
                this.charts.finRevenue.update();
            } else {
                this.charts.finRevenue = new Chart(revenueCtx, {
                    type: 'line',
                    data: {
                        labels: revenueData.map(d => d.label),
                        datasets: [{
                            label: 'Comisiones (TON)',
                            data: revenueData.map(d => d.amount),
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 2,
                            pointHoverRadius: 5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C', maxTicksLimit: 10 } },
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } }
                        }
                    }
                });
            }
        }
        
        if (volumeCtx) {
            if (this.charts.finVolume) {
                this.charts.finVolume.data.labels = volumeData.map(d => d.label);
                this.charts.finVolume.data.datasets[0].data = volumeData.map(d => d.amount);
                this.charts.finVolume.update();
            } else {
                this.charts.finVolume = new Chart(volumeCtx, {
                    type: 'bar',
                    data: {
                        labels: volumeData.map(d => d.label),
                        datasets: [{
                            label: 'Volumen (B3C)',
                            data: volumeData.map(d => d.amount),
                            backgroundColor: 'rgba(240, 185, 11, 0.6)',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { grid: { display: false }, ticks: { color: '#848E9C', maxTicksLimit: 10 } },
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#848E9C' } }
                        }
                    }
                });
            }
        }
    },
    
    renderTransactionsTable(transactions) {
        const tbody = document.getElementById('transactionsTableBody');
        
        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No se encontraron transacciones</td></tr>';
            return;
        }
        
        const typeLabels = {
            buy: 'Compra B3C',
            sell: 'Venta B3C',
            transfer: 'Transferencia',
            withdrawal: 'Retiro'
        };
        
        tbody.innerHTML = transactions.map(tx => `
            <tr>
                <td><code>${tx.id}</code></td>
                <td>${this.escapeHtml(tx.username || tx.user_id)}</td>
                <td>${typeLabels[tx.type] || tx.type}</td>
                <td>${this.formatNumber(tx.amount, 4)} ${tx.currency || 'B3C'}</td>
                <td><span class="status-badge ${tx.status}">${tx.status}</span></td>
                <td>${this.formatDate(tx.created_at)}</td>
                <td>
                    ${tx.tx_hash ? `<span class="tx-hash" onclick="AdminPanel.openTxHash('${tx.tx_hash}')">${tx.tx_hash.slice(0, 10)}...</span>` : '-'}
                </td>
                <td>
                    <div class="action-btns">
                        <button class="action-btn" onclick="AdminPanel.viewTransaction('${tx.id}')">Ver</button>
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    async loadWallets() {
        try {
            const statusFilter = document.getElementById('walletStatusFilter')?.value || '';
            
            const [hotWallet, poolStats, depositWallets] = await Promise.all([
                this.fetchAPI('/api/admin/wallets/hot'),
                this.fetchAPI('/api/admin/wallet-pool/stats'),
                this.fetchAPI(`/api/admin/wallets/deposits?status=${statusFilter}`)
            ]);
            
            if (hotWallet.success) {
                const explorerUrl = hotWallet.explorerUrl || this.explorerUrl || 'https://tonscan.org';
                this.explorerUrl = explorerUrl;
                document.getElementById('hwBalance').textContent = this.formatNumber(hotWallet.balance || 0, 4);
                document.getElementById('hwAddress').textContent = hotWallet.address || '-';
                document.getElementById('hotWalletLink').href = `${explorerUrl}/address/${hotWallet.address}`;
                
                const statusEl = document.getElementById('hwStatus');
                if (hotWallet.balance < 1) {
                    statusEl.className = 'wallet-status warning';
                    statusEl.innerHTML = '<span class="status-dot"></span><span>Balance bajo</span>';
                } else {
                    statusEl.className = 'wallet-status ok';
                    statusEl.innerHTML = '<span class="status-dot"></span><span>Normal</span>';
                }
            }
            
            if (poolStats.success && poolStats.stats) {
                document.getElementById('poolAvailable').textContent = poolStats.stats.available || 0;
                document.getElementById('poolAssigned').textContent = poolStats.stats.assigned || 0;
                document.getElementById('poolTotal').textContent = poolStats.stats.total || 0;
            }
            
            if (depositWallets.success && depositWallets.wallets) {
                if (depositWallets.explorerUrl) {
                    this.explorerUrl = depositWallets.explorerUrl;
                }
                this.renderDepositWallets(depositWallets.wallets);
            }
            
            this.loadBlockchainHistory();
            this.loadPoolConfig();
            
        } catch (error) {
            console.error('Error loading wallets:', error);
        }
    },
    
    renderDepositWallets(wallets) {
        const tbody = document.getElementById('depositWalletsBody');
        
        if (!wallets || wallets.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="7">No hay wallets de depósito</td></tr>';
            return;
        }
        
        const explorerUrl = this.explorerUrl || 'https://tonscan.org';
        
        tbody.innerHTML = wallets.map(w => `
            <tr>
                <td style="font-family: monospace; font-size: 11px;">
                    <span class="wallet-address-copy" onclick="AdminPanel.copyToClipboard('${w.wallet_address}')" title="Click para copiar">
                        ${w.wallet_address?.slice(0, 20)}...
                    </span>
                </td>
                <td><span class="status-badge ${w.status}">${w.status}</span></td>
                <td>${w.assigned_to_user_id || '-'}</td>
                <td>${w.deposit_amount ? this.formatNumber(w.deposit_amount, 4) + ' TON' : '-'}</td>
                <td>${w.deposit_amount && !w.consolidated_at ? this.formatNumber(w.deposit_amount, 4) + ' TON' : '-'}</td>
                <td>${this.formatDate(w.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <a href="${explorerUrl}/address/${w.wallet_address}" target="_blank" class="action-btn" title="Ver en TonScan">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
                        </a>
                        ${w.deposit_amount && !w.consolidated_at ? `
                            <button class="action-btn" onclick="AdminPanel.consolidateSingleWallet(${w.id})" title="Consolidar">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="17 1 21 5 17 9"></polyline>
                                    <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
                                </svg>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    async consolidateSingleWallet(walletId) {
        if (!confirm('¿Consolidar fondos de esta wallet al hot wallet?')) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/wallets/${walletId}/consolidate`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(`Wallet consolidada: ${response.amount} TON`, 'success');
                this.loadWallets();
            } else {
                this.showToast(response.error || 'Error al consolidar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al consolidar wallet', 'error');
        }
    },
    
    async loadBlockchainHistory(txType = '') {
        const tbody = document.getElementById('blockchainHistoryBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Cargando historial...</td></tr>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/blockchain/history?type=${txType}&limit=50`);
            
            if (response.success && response.transactions) {
                if (response.transactions.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="7">No hay transacciones blockchain</td></tr>';
                    return;
                }
                
                const explorerUrl = response.explorerUrl || 'https://tonscan.org';
                this.explorerUrl = explorerUrl;
                
                const typeLabels = {
                    deposit: { label: 'Depósito', class: 'completed' },
                    consolidation: { label: 'Consolidación', class: 'pending' },
                    withdrawal: { label: 'Retiro', class: 'warning' }
                };
                
                tbody.innerHTML = response.transactions.map(tx => `
                    <tr>
                        <td>${this.formatDateTime(tx.created_at)}</td>
                        <td><span class="status-badge ${typeLabels[tx.tx_type]?.class || ''}">${typeLabels[tx.tx_type]?.label || tx.tx_type}</span></td>
                        <td>${this.formatNumber(tx.amount, 4)} TON</td>
                        <td style="font-family: monospace; font-size: 11px;">${tx.from_address}</td>
                        <td style="font-family: monospace; font-size: 11px;">${tx.to_address}</td>
                        <td><span class="status-badge ${tx.status}">${tx.status}</span></td>
                        <td>
                            ${tx.tx_hash ? `
                                <a href="${explorerUrl}/tx/${tx.tx_hash}" target="_blank" class="tx-link" title="${tx.tx_hash}">
                                    ${tx.tx_hash.slice(0, 10)}...
                                </a>
                            ` : '-'}
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading blockchain history:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Error al cargar historial</td></tr>';
        }
    },
    
    async loadPoolConfig() {
        try {
            const response = await this.fetchAPI('/api/admin/wallets/pool-config');
            
            if (response.success && response.config) {
                document.getElementById('minPoolSize').value = response.config.minPoolSize || 10;
                document.getElementById('autoFillThreshold').value = response.config.autoFillThreshold || 5;
                document.getElementById('lowBalanceThreshold').value = response.config.lowBalanceThreshold || 1;
            }
        } catch (error) {
            console.error('Error loading pool config:', error);
        }
    },
    
    async savePoolConfig() {
        try {
            const config = {
                minPoolSize: parseInt(document.getElementById('minPoolSize').value) || 10,
                autoFillThreshold: parseInt(document.getElementById('autoFillThreshold').value) || 5,
                lowBalanceThreshold: parseFloat(document.getElementById('lowBalanceThreshold').value) || 1
            };
            
            const response = await this.fetchAPI('/api/admin/wallets/pool-config', {
                method: 'POST',
                body: JSON.stringify(config)
            });
            
            if (response.success) {
                this.showToast('Configuración guardada', 'success');
            } else {
                this.showToast(response.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error saving pool config:', error);
            this.showToast('Error al guardar configuración', 'error');
        }
    },
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado al portapapeles', 'success');
        }).catch(err => {
            console.error('Error copying:', err);
        });
    },
    
    async fillWalletPool() {
        try {
            const response = await this.fetchAPI('/api/admin/wallets/fill-pool', {
                method: 'POST',
                body: JSON.stringify({ count: 10 })
            });
            
            if (response.success) {
                this.showToast(`Pool rellenado: ${response.created} wallets creadas`, 'success');
                this.loadWallets();
            } else {
                this.showToast(response.error || 'Error al rellenar pool', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al rellenar pool', 'error');
        }
    },
    
    async consolidateWallets() {
        if (!confirm('¿Consolidar fondos de todas las wallets a la hot wallet?')) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/wallets/consolidate', {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(`Consolidación completada: ${response.consolidated} wallets, ${response.totalAmount} TON`, 'success');
                this.loadWallets();
            } else {
                this.showToast(response.error || 'Error al consolidar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al consolidar', 'error');
        }
    },
    
    async loadSessions() {
        this.setupSessionsTabs();
        
        const tbody = document.getElementById('sessionsTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="5">Cargando sesiones...</td></tr>';
        }
        
        try {
            const [sessionsRes, blockedRes] = await Promise.all([
                this.fetchAPI('/api/admin/sessions'),
                this.fetchAPI('/api/admin/blocked-ips')
            ]);
            
            if (blockedRes.success && blockedRes.ips) {
                const activeBlocked = blockedRes.ips.filter(ip => ip.is_active !== false);
                const countEl = document.getElementById('blockedIPsCount');
                if (countEl) countEl.textContent = activeBlocked.length;
            }
            
            if (sessionsRes.success && sessionsRes.sessions) {
                const sessions = sessionsRes.sessions;
                const uniqueIPs = [...new Set(sessions.map(s => s.ip || s.ip_address).filter(Boolean))];
                
                const totalSessionsEl = document.getElementById('totalSessions');
                const uniqueIPsEl = document.getElementById('uniqueIPs');
                
                if (totalSessionsEl) totalSessionsEl.textContent = sessions.length;
                if (uniqueIPsEl) uniqueIPsEl.textContent = uniqueIPs.length;
                
                if (!tbody) return;
                
                if (sessions.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="5">No hay sesiones activas</td></tr>';
                    return;
                }
                
                const sessionsHtml = sessions.map(s => {
                    const deviceName = s.device || s.device_name || '-';
                    const ipAddress = s.ip || s.ip_address || '-';
                    const userId = s.user_id || '';
                    const escapedDevice = this.escapeHtml(deviceName);
                    const escapedIP = this.escapeHtml(ipAddress);
                    
                    return `
                    <tr>
                        <td>
                            <div class="user-cell">
                                <div class="user-avatar-sm">${(s.first_name || 'U')[0].toUpperCase()}</div>
                                <span>@${this.escapeHtml(s.username || 'N/A')}</span>
                            </div>
                        </td>
                        <td>${this.escapeHtml(ipAddress)}</td>
                        <td title="${escapedDevice}">${this.escapeHtml(deviceName.slice(0, 30))}${deviceName.length > 30 ? '...' : ''}</td>
                        <td>${this.timeAgo(s.last_activity)}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="action-btn danger" onclick="AdminPanel.terminateSession('${userId}', '${escapedDevice.replace(/'/g, "\\'")}')">
                                    Cerrar
                                </button>
                                <button class="action-btn warning" onclick="AdminPanel.terminateAllUserSessions('${userId}')">
                                    Cerrar Todas
                                </button>
                                ${ipAddress !== '-' ? `<button class="action-btn secondary" onclick="AdminPanel.blockIPFromSession('${escapedIP}')" title="Bloquear IP">
                                    Bloquear IP
                                </button>` : ''}
                            </div>
                        </td>
                    </tr>
                `;
                }).join('');
                SafeDOM.setHTML(tbody, sessionsHtml);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            if (tbody) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="5">Error al cargar sesiones</td></tr>';
            }
        }
    },
    
    async terminateSession(userId, deviceName) {
        if (!confirm(`¿Cerrar la sesión del dispositivo "${deviceName}"?`)) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/sessions/terminate', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, device_name: deviceName })
            });
            
            if (response.success) {
                this.showToast(response.message || 'Sesión cerrada', 'success');
                this.loadSessions();
            } else {
                this.showToast(response.error || 'Error al cerrar sesión', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al cerrar sesión', 'error');
        }
    },
    
    async terminateAllUserSessions(userId) {
        if (!confirm('¿Cerrar TODAS las sesiones de este usuario?')) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/sessions/terminate-all/${userId}`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(response.message || 'Todas las sesiones cerradas', 'success');
                this.loadSessions();
            } else {
                this.showToast(response.error || 'Error al cerrar sesiones', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al cerrar sesiones', 'error');
        }
    },
    
    async logoutAllUsers() {
        if (!confirm('¿Cerrar TODAS las sesiones de TODOS los usuarios (excepto admins)?')) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/sessions/logout-all', {
                method: 'POST',
                body: JSON.stringify({ exclude_admins: true })
            });
            
            if (response.success) {
                this.showToast(response.message || 'Todas las sesiones cerradas', 'success');
                this.loadSessions();
            } else {
                this.showToast(response.error || 'Error al cerrar sesiones', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al cerrar sesiones', 'error');
        }
    },
    
    setupSessionsTabs() {
        document.querySelectorAll('[data-sessions-tab]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-sessions-tab]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const tabName = btn.dataset.sessionsTab;
                document.getElementById('sessionsTabActive').style.display = tabName === 'active' ? 'block' : 'none';
                document.getElementById('sessionsTabIPs').style.display = tabName === 'ips' ? 'block' : 'none';
                
                if (tabName === 'ips') {
                    this.loadBlockedIPs();
                }
            });
        });
    },
    
    blockedIPsData: [],
    
    async loadBlockedIPs() {
        const tbody = document.getElementById('blockedIPsTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Cargando IPs bloqueadas...</td></tr>';
        }
        
        try {
            const response = await this.fetchAPI('/api/admin/blocked-ips');
            
            if (response.success && response.ips) {
                this.blockedIPsData = response.ips;
                this.renderBlockedIPs(response.ips);
                
                const countEl = document.getElementById('blockedIPsCount');
                if (countEl) countEl.textContent = response.ips.filter(ip => ip.is_active !== false).length;
            }
        } catch (error) {
            console.error('Error loading blocked IPs:', error);
            if (tbody) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar IPs</td></tr>';
            }
        }
    },
    
    renderBlockedIPs(ips) {
        const tbody = document.getElementById('blockedIPsTableBody');
        if (!tbody) return;
        
        const statusFilter = document.getElementById('ipStatusFilter')?.value || 'active';
        let filteredIPs = ips;
        
        if (statusFilter === 'active') {
            filteredIPs = ips.filter(ip => ip.is_active !== false);
        }
        
        if (filteredIPs.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay IPs bloqueadas</td></tr>';
            return;
        }
        
        const html = filteredIPs.map(ip => `
            <tr data-ip-id="${ip.id}">
                <td><code>${this.escapeHtml(ip.ip_address)}</code></td>
                <td>${this.escapeHtml(ip.reason || '-')}</td>
                <td>${this.escapeHtml(ip.blocked_by || 'Admin')}</td>
                <td>${this.formatDate(ip.blocked_at || ip.created_at)}</td>
                <td>
                    <span class="badge ${ip.is_permanent ? 'badge-danger' : 'badge-warning'}">
                        ${ip.is_permanent ? 'Sí' : 'No'}
                    </span>
                </td>
                <td>
                    <button class="action-btn warning" onclick="AdminPanel.unblockIP(${ip.id})" title="Desbloquear">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');
        
        SafeDOM.setHTML(tbody, html);
    },
    
    filterBlockedIPs() {
        const searchTerm = document.getElementById('ipSearchInput')?.value?.toLowerCase() || '';
        const filtered = this.blockedIPsData.filter(ip => 
            ip.ip_address?.toLowerCase().includes(searchTerm) ||
            ip.reason?.toLowerCase().includes(searchTerm)
        );
        this.renderBlockedIPs(filtered);
    },
    
    showAddIPModal() {
        document.getElementById('blockIPAddress').value = '';
        document.getElementById('blockIPReason').value = '';
        document.getElementById('blockIPPermanent').checked = false;
        document.getElementById('addIPModal').classList.add('active');
    },
    
    closeIPModal() {
        document.getElementById('addIPModal').classList.remove('active');
    },
    
    async blockIP() {
        const ipAddress = document.getElementById('blockIPAddress')?.value?.trim();
        const reason = document.getElementById('blockIPReason')?.value?.trim();
        const isPermanent = document.getElementById('blockIPPermanent')?.checked || false;
        
        if (!ipAddress) {
            this.showToast('Ingresa una dirección IP', 'error');
            return;
        }
        
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        if (!ipRegex.test(ipAddress)) {
            this.showToast('Formato de IP inválido', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI('/api/admin/blocked-ips', {
                method: 'POST',
                body: JSON.stringify({
                    ip_address: ipAddress,
                    reason: reason || 'Bloqueado manualmente por admin',
                    is_permanent: isPermanent
                })
            });
            
            if (response.success) {
                this.showToast(`IP ${ipAddress} bloqueada correctamente`, 'success');
                this.closeIPModal();
                this.loadBlockedIPs();
            } else {
                this.showToast(response.error || 'Error al bloquear IP', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al bloquear IP', 'error');
        }
    },
    
    async unblockIP(ipId) {
        if (!confirm('¿Desbloquear esta IP?')) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/blocked-ips/${ipId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('IP desbloqueada correctamente', 'success');
                this.loadBlockedIPs();
            } else {
                this.showToast(response.error || 'Error al desbloquear IP', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al desbloquear IP', 'error');
        }
    },
    
    async blockIPFromSession(ipAddress) {
        const reason = prompt('Razón del bloqueo (opcional):') || 'IP sospechosa - bloqueada desde sesiones';
        
        try {
            const response = await this.fetchAPI('/api/admin/blocked-ips', {
                method: 'POST',
                body: JSON.stringify({
                    ip_address: ipAddress,
                    reason: reason,
                    is_permanent: false
                })
            });
            
            if (response.success) {
                this.showToast(`IP ${ipAddress} bloqueada`, 'success');
                this.loadSessions();
            } else {
                this.showToast(response.error || 'Error al bloquear IP', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al bloquear IP', 'error');
        }
    },
    
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = (now - date) / 1000;
        
        if (diff < 60) return 'Hace un momento';
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `Hace ${Math.floor(diff / 3600)}h`;
        if (diff < 604800) return `Hace ${Math.floor(diff / 86400)}d`;
        
        return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    },
    
    async loadContent() {
        this.setupContentTabs();
        
        try {
            const response = await this.fetchAPI('/api/admin/content/stats');
            
            if (response.success) {
                document.getElementById('totalPosts').textContent = this.formatNumber(response.totalPosts || 0);
                document.getElementById('postsToday').textContent = this.formatNumber(response.postsToday || 0);
                document.getElementById('totalMedia').textContent = this.formatNumber(response.totalMedia || 0);
                document.getElementById('totalStories').textContent = this.formatNumber(response.totalStories || 0);
                document.getElementById('reportedPostsCount').textContent = this.formatNumber(response.reportedPosts || 0);
            }
            
            await this.loadContentPosts();
        } catch (error) {
            console.error('Error loading content:', error);
        }
    },
    
    setupContentTabs() {
        document.querySelectorAll('.content-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.content-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const tabName = btn.dataset.contentTab;
                
                document.querySelectorAll('.content-tab-panel').forEach(panel => {
                    panel.style.display = 'none';
                    panel.classList.remove('active');
                });
                
                const targetPanel = document.getElementById(`contentTab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
                if (targetPanel) {
                    targetPanel.style.display = 'block';
                    targetPanel.classList.add('active');
                }
                
                switch(tabName) {
                    case 'posts':
                        this.loadContentPosts();
                        break;
                    case 'reported':
                        this.loadReportedContent();
                        break;
                    case 'stories':
                        this.loadStories();
                        break;
                    case 'hashtags':
                        this.loadHashtags();
                        break;
                }
            });
        });
    },
    
    async loadContentPosts() {
        const tbody = document.getElementById('contentTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Cargando contenido...</td></tr>';
        
        const search = document.getElementById('contentSearch')?.value || '';
        const contentType = document.getElementById('contentTypeFilter')?.value || '';
        
        try {
            let url = '/api/admin/content/posts?limit=50';
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (contentType) url += `&content_type=${encodeURIComponent(contentType)}`;
            
            const postsResponse = await this.fetchAPI(url);
            
            if (postsResponse.success && postsResponse.posts) {
                const posts = postsResponse.posts;
                
                if (posts.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No hay publicaciones</td></tr>';
                    return;
                }
                
                tbody.innerHTML = posts.map(post => `
                    <tr>
                        <td>${post.id}</td>
                        <td>@${this.escapeHtml(post.username || 'N/A')}</td>
                        <td>${post.content_type}</td>
                        <td>${this.escapeHtml((post.caption || '').slice(0, 30))}...</td>
                        <td>${post.reactions_count || 0}</td>
                        <td>${post.comments_count || 0}</td>
                        <td>${this.formatDate(post.created_at)}</td>
                        <td>
                            <div class="action-btns">
                                <button class="action-btn" onclick="AdminPanel.viewPost(${post.id})">Ver</button>
                                <button class="action-btn warning" onclick="AdminPanel.warnPostAuthor(${post.id})">Advertir</button>
                                <button class="action-btn danger" onclick="AdminPanel.deletePost(${post.id})">Eliminar</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Error al cargar publicaciones</td></tr>';
        }
    },
    
    async loadReportedContent() {
        const container = document.getElementById('reportedContentList');
        container.innerHTML = '<div class="empty-state">Cargando contenido reportado...</div>';
        
        try {
            const response = await this.fetchAPI('/api/admin/content/reported');
            
            if (response.success && response.posts) {
                if (response.posts.length === 0) {
                    container.innerHTML = '<div class="empty-state">No hay contenido reportado</div>';
                    return;
                }
                
                container.innerHTML = response.posts.map(post => `
                    <div class="report-item">
                        <div class="report-content">
                            <div class="report-header">
                                <strong>Publicacion #${post.id}</strong>
                                <span class="status-badge warning">${post.report_count || 0} reportes</span>
                            </div>
                            <p>${this.escapeHtml((post.caption || 'Sin texto').slice(0, 100))}...</p>
                            <div class="report-meta">
                                <span>Autor: @${this.escapeHtml(post.username || 'N/A')}</span>
                                <span>Tipo: ${post.content_type}</span>
                                <span>${this.formatDate(post.created_at)}</span>
                            </div>
                        </div>
                        <div class="report-actions">
                            <button class="action-btn" onclick="AdminPanel.viewPost(${post.id})">Ver</button>
                            <button class="action-btn warning" onclick="AdminPanel.warnPostAuthor(${post.id})">Advertir</button>
                            <button class="action-btn danger" onclick="AdminPanel.deletePost(${post.id})">Eliminar</button>
                            <button class="action-btn danger" onclick="AdminPanel.banPostAuthor(${post.id})">Banear Autor</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading reported content:', error);
            container.innerHTML = '<div class="empty-state">Error al cargar contenido reportado</div>';
        }
    },
    
    async loadStories() {
        const tbody = document.getElementById('storiesTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Cargando stories...</td></tr>';
        
        try {
            const status = document.getElementById('storiesStatusFilter')?.value || 'active';
            const response = await this.fetchAPI(`/api/admin/stories?status=${status}`);
            
            if (response.success && response.stories) {
                if (response.stories.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="7">No hay stories</td></tr>';
                    return;
                }
                
                tbody.innerHTML = response.stories.map(story => `
                    <tr>
                        <td>${story.id}</td>
                        <td>@${this.escapeHtml(story.username || 'N/A')}</td>
                        <td>${story.media_type || 'image'}</td>
                        <td>${story.views_count || 0}</td>
                        <td>${this.formatDateTime(story.expires_at)}</td>
                        <td>
                            <span class="status-badge ${story.is_active ? 'active' : 'inactive'}">
                                ${story.is_active ? 'Activa' : 'Expirada'}
                            </span>
                        </td>
                        <td>
                            <div class="action-btns">
                                <button class="action-btn danger" onclick="AdminPanel.deleteStory(${story.id})">Eliminar</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading stories:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Error al cargar stories</td></tr>';
        }
    },
    
    async loadHashtags() {
        const tbody = document.getElementById('hashtagsTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="5">Cargando hashtags...</td></tr>';
        
        const search = document.getElementById('hashtagSearch')?.value || '';
        const statusFilter = document.getElementById('hashtagStatusFilter')?.value || '';
        
        try {
            let url = '/api/admin/hashtags?limit=50';
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
            
            const response = await this.fetchAPI(url);
            
            if (response.success && response.hashtags) {
                const hashtags = response.hashtags;
                
                if (hashtags.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="5">No hay hashtags</td></tr>';
                    return;
                }
                
                tbody.innerHTML = hashtags.map(tag => `
                    <tr>
                        <td>${tag.id}</td>
                        <td>#${this.escapeHtml(tag.tag || tag.name || '')}</td>
                        <td>${tag.posts_count || tag.usage_count || 0}</td>
                        <td>
                            <span class="status-badge ${tag.is_blocked ? 'danger' : (tag.is_promoted ? 'success' : 'active')}">
                                ${tag.is_blocked ? 'Bloqueado' : (tag.is_promoted ? 'Promovido' : 'Activo')}
                            </span>
                        </td>
                        <td>
                            <div class="action-btns">
                                ${tag.is_blocked 
                                    ? `<button class="action-btn success" onclick="AdminPanel.unblockHashtag(${tag.id})">Desbloquear</button>`
                                    : `<button class="action-btn danger" onclick="AdminPanel.blockHashtag(${tag.id})">Bloquear</button>`
                                }
                                ${!tag.is_blocked && !tag.is_promoted 
                                    ? `<button class="action-btn" onclick="AdminPanel.promoteHashtag(${tag.id})">Promover</button>`
                                    : ''
                                }
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading hashtags:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="5">Error al cargar hashtags</td></tr>';
        }
    },
    
    async warnPostAuthor(postId) {
        const reason = prompt('Ingrese el motivo de la advertencia:');
        if (!reason) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/content/posts/${postId}/warn`, {
                method: 'POST',
                body: JSON.stringify({ reason })
            });
            
            if (response.success) {
                this.showToast('Advertencia enviada al autor', 'success');
            } else {
                this.showToast(response.error || 'Error al enviar advertencia', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al enviar advertencia', 'error');
        }
    },
    
    async banPostAuthor(postId) {
        if (!confirm('Esta accion baneara permanentemente al autor de esta publicacion. Esta seguro?')) {
            return;
        }
        
        const reason = prompt('Ingrese el motivo del ban:');
        if (!reason) return;
        
        try {
            const response = await this.fetchAPI(`/api/admin/content/posts/${postId}/ban-author`, {
                method: 'POST',
                body: JSON.stringify({ reason })
            });
            
            if (response.success) {
                this.showToast('Autor baneado exitosamente', 'success');
                this.loadReportedContent();
            } else {
                this.showToast(response.error || 'Error al banear autor', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al banear autor', 'error');
        }
    },
    
    async deleteStory(storyId) {
        if (!confirm('Esta seguro de eliminar esta story?')) {
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/stories/${storyId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Story eliminada', 'success');
                this.loadStories();
            } else {
                this.showToast(response.error || 'Error al eliminar story', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al eliminar story', 'error');
        }
    },
    
    async blockHashtag(hashtagId) {
        if (!confirm('Esta seguro de bloquear este hashtag?')) {
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/hashtags/${hashtagId}/block`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Hashtag bloqueado', 'success');
                this.loadHashtags();
            } else {
                this.showToast(response.error || 'Error al bloquear hashtag', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al bloquear hashtag', 'error');
        }
    },
    
    async unblockHashtag(hashtagId) {
        try {
            const response = await this.fetchAPI(`/api/admin/hashtags/${hashtagId}/unblock`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Hashtag desbloqueado', 'success');
                this.loadHashtags();
            } else {
                this.showToast(response.error || 'Error al desbloquear hashtag', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al desbloquear hashtag', 'error');
        }
    },
    
    async promoteHashtag(hashtagId) {
        try {
            const response = await this.fetchAPI(`/api/admin/hashtags/${hashtagId}/promote`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Hashtag promovido', 'success');
                this.loadHashtags();
            } else {
                this.showToast(response.error || 'Error al promover hashtag', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al promover hashtag', 'error');
        }
    },
    
    async loadReports(status = 'pending') {
        const container = document.getElementById('reportsList');
        container.innerHTML = '<div class="empty-state">Cargando reportes...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/reports?status=${status}`);
            
            if (response.success && response.reports) {
                document.getElementById('reportsCount').textContent = response.reports.length;
                
                if (response.reports.length === 0) {
                    const statusText = status === 'pending' ? 'pendientes' : 
                                      status === 'reviewed' ? 'revisados' : 'descartados';
                    container.innerHTML = `<div class="empty-state">No hay reportes ${statusText}</div>`;
                    return;
                }
                
                container.innerHTML = response.reports.map(report => `
                    <div class="report-item">
                        <div class="report-content">
                            <div class="report-header">
                                <strong>Reporte #${report.id}</strong>
                                <span class="status-badge ${report.status === 'pending' ? 'warning' : report.status === 'reviewed' ? 'success' : 'inactive'}">${this.getReportStatusText(report.status)}</span>
                                ${report.content_type ? `<span class="content-type-badge">${report.content_type}</span>` : ''}
                            </div>
                            <div class="report-reason">
                                <strong>Motivo:</strong> ${this.escapeHtml(report.reason)}
                            </div>
                            ${report.content_preview ? `
                                <div class="report-preview">
                                    <strong>Contenido:</strong> ${this.escapeHtml(report.content_preview.slice(0, 150))}${report.content_preview.length > 150 ? '...' : ''}
                                </div>
                            ` : ''}
                            <div class="report-meta">
                                <span><strong>Reportado por:</strong> @${this.escapeHtml(report.reporter_username || 'Anónimo')}</span>
                                ${report.reported_username ? `<span><strong>Autor:</strong> @${this.escapeHtml(report.reported_username)}</span>` : ''}
                                <span><strong>Fecha:</strong> ${this.formatDateTime(report.created_at)}</span>
                                ${report.post_id ? `<span><strong>Post ID:</strong> #${report.post_id}</span>` : ''}
                            </div>
                        </div>
                        <div class="report-actions">
                            ${report.post_id ? `<button class="action-btn" onclick="AdminPanel.viewPost(${report.post_id})">Ver Publicacion</button>` : ''}
                            ${status === 'pending' ? `
                                <button class="action-btn success" onclick="AdminPanel.reviewReport(${report.id}, 'reviewed')">Resolver</button>
                                <button class="action-btn warning" onclick="AdminPanel.reviewReport(${report.id}, 'dismissed')">Descartar</button>
                                ${report.post_id ? `<button class="action-btn danger" onclick="AdminPanel.deletePostAndResolveReport(${report.post_id}, ${report.id})">Eliminar Post</button>` : ''}
                            ` : `
                                <span class="resolved-info">Resuelto: ${this.formatDateTime(report.resolved_at || report.updated_at)}</span>
                            `}
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            container.innerHTML = '<div class="empty-state">Error al cargar reportes</div>';
        }
    },
    
    getReportStatusText(status) {
        switch(status) {
            case 'pending': return 'Pendiente';
            case 'reviewed': return 'Resuelto';
            case 'dismissed': return 'Descartado';
            default: return status;
        }
    },
    
    async reviewReport(reportId, status) {
        try {
            const response = await this.fetchAPI(`/api/admin/reports/${reportId}`, {
                method: 'PUT',
                body: JSON.stringify({ status })
            });
            
            if (response.success) {
                this.showToast('Reporte actualizado', 'success');
                this.loadReports();
            } else {
                this.showToast(response.error || 'Error al actualizar reporte', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al actualizar reporte', 'error');
        }
    },
    
    async deletePostAndResolveReport(postId, reportId) {
        if (!confirm('¿Está seguro de eliminar esta publicación y resolver el reporte?')) {
            return;
        }
        
        try {
            const deleteResponse = await this.fetchAPI(`/api/admin/content/posts/${postId}`, {
                method: 'DELETE'
            });
            
            if (!deleteResponse.success) {
                this.showToast(deleteResponse.error || 'Error al eliminar publicación', 'error');
                return;
            }
            
            const resolveResponse = await this.fetchAPI(`/api/admin/reports/${reportId}`, {
                method: 'PUT',
                body: JSON.stringify({ status: 'reviewed' })
            });
            
            if (resolveResponse.success) {
                this.showToast('Publicación eliminada y reporte resuelto', 'success');
                this.loadReports();
            } else {
                this.showToast('Publicación eliminada, pero error al resolver reporte', 'warning');
                this.loadReports();
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al procesar la solicitud', 'error');
        }
    },
    
    async viewPost(postId) {
        const modal = document.getElementById('userDetailModal');
        const content = document.getElementById('userDetailContent');
        
        content.innerHTML = 'Cargando publicación...';
        modal.classList.add('active');
        
        try {
            const response = await this.fetchAPI(`/api/admin/content/posts?limit=100`);
            
            if (response.success && response.posts) {
                const post = response.posts.find(p => p.id === postId);
                
                if (post) {
                    content.innerHTML = `
                        <div class="user-detail-header">
                            <h3>Publicación #${post.id}</h3>
                        </div>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Autor</label>
                                <div class="value">@${this.escapeHtml(post.username || 'N/A')}</div>
                            </div>
                            <div class="detail-item">
                                <label>Tipo</label>
                                <div class="value">${post.content_type}</div>
                            </div>
                            <div class="detail-item">
                                <label>Reacciones</label>
                                <div class="value">${post.reactions_count || 0}</div>
                            </div>
                            <div class="detail-item">
                                <label>Comentarios</label>
                                <div class="value">${post.comments_count || 0}</div>
                            </div>
                            <div class="detail-item" style="grid-column: 1 / -1;">
                                <label>Caption</label>
                                <div class="value" style="white-space: pre-wrap;">${this.escapeHtml(post.caption || 'Sin texto')}</div>
                            </div>
                            <div class="detail-item">
                                <label>Fecha</label>
                                <div class="value">${this.formatDateTime(post.created_at)}</div>
                            </div>
                            <div class="detail-item">
                                <label>Estado</label>
                                <div class="value">${post.is_active ? 'Activo' : 'Eliminado'}</div>
                            </div>
                        </div>
                        <div class="user-actions">
                            <button class="btn-secondary" onclick="AdminPanel.deletePost(${post.id})">Eliminar Publicación</button>
                        </div>
                    `;
                } else {
                    content.innerHTML = '<div class="empty-state">Publicación no encontrada</div>';
                }
            }
        } catch (error) {
            console.error('Error:', error);
            content.innerHTML = '<div class="empty-state">Error al cargar publicación</div>';
        }
    },
    
    async deletePost(postId) {
        if (!confirm('¿Estás seguro de eliminar esta publicación? Esta acción no se puede deshacer.')) {
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/content/posts/${postId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Publicación eliminada', 'success');
                document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
                this.loadContent();
            } else {
                this.showToast(response.error || 'Error al eliminar publicación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al eliminar publicación', 'error');
        }
    },
    
    logsCurrentType: 'admin',
    logsPage: 1,
    logsPerPage: 20,
    logsTotalPages: 1,
    
    async loadLogs(logType = null) {
        if (logType) {
            this.logsCurrentType = logType;
            this.logsPage = 1;
        }
        
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Cargando logs...</td></tr>';
        
        const suspiciousSection = document.getElementById('suspiciousIPsSection');
        if (suspiciousSection) {
            suspiciousSection.style.display = this.logsCurrentType === 'logins' ? 'block' : 'none';
        }
        
        try {
            await this.loadLogsStats();
            
            if (this.logsCurrentType === 'admin') {
                await this.loadAdminLogs();
            } else if (this.logsCurrentType === 'security') {
                await this.loadSecurityLogs();
            } else if (this.logsCurrentType === 'logins') {
                await this.loadLoginLogs();
            } else if (this.logsCurrentType === 'errors') {
                await this.loadErrorLogs();
            } else if (this.logsCurrentType === 'config') {
                await this.loadConfigHistory();
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar logs</td></tr>';
        }
    },
    
    async loadLogsStats() {
        try {
            const [adminStats, securityStats] = await Promise.all([
                this.fetchAPI('/api/admin/logs/admin?page=1&per_page=1'),
                this.fetchAPI('/api/admin/logs/security?page=1&per_page=1')
            ]);
            
            document.getElementById('logsAdminCount').textContent = this.formatNumber(adminStats.total || 0);
            document.getElementById('logsSecurityCount').textContent = this.formatNumber(securityStats.total || 0);
            
            let warningsCount = 0;
            let errorsCount = 0;
            
            if (securityStats.activityTypes) {
                securityStats.activityTypes.forEach(at => {
                    if (at.activity_type.includes('FAILED') || at.activity_type.includes('BLOCKED')) {
                        warningsCount += at.count;
                    }
                    if (at.activity_type.includes('ERROR') || at.activity_type.includes('LOCKOUT')) {
                        errorsCount += at.count;
                    }
                });
            }
            
            document.getElementById('logsWarningsCount').textContent = this.formatNumber(warningsCount);
            document.getElementById('logsErrorsCount').textContent = this.formatNumber(errorsCount);
        } catch (error) {
            console.error('Error loading logs stats:', error);
        }
    },
    
    async loadAdminLogs() {
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Administrador</th>
                <th>Acción</th>
                <th>Objetivo</th>
                <th>Descripción</th>
                <th>IP</th>
            </tr>
        `;
        
        const search = document.getElementById('logSearch')?.value || '';
        const actionFilter = document.getElementById('logActionFilter')?.value || '';
        const dateFrom = document.getElementById('logDateFrom')?.value || '';
        const dateTo = document.getElementById('logDateTo')?.value || '';
        
        let url = `/api/admin/logs/admin?page=${this.logsPage}&per_page=${this.logsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (actionFilter) url += `&action_type=${encodeURIComponent(actionFilter)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        
        const response = await this.fetchAPI(url);
        
        if (response.success && response.logs) {
            this.logsTotalPages = response.pages || 1;
            this.updateLogsPagination();
            this.updateAdminActionFilter(response.actionTypes || []);
            
            if (response.logs.length === 0) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay logs disponibles</td></tr>';
                return;
            }
            
            tbody.innerHTML = response.logs.map(log => `
                <tr>
                    <td>${this.formatDateTime(log.created_at)}</td>
                    <td>
                        <div class="user-cell">
                            <div class="user-avatar-sm">${(log.admin_name || 'A')[0].toUpperCase()}</div>
                            <span>${this.escapeHtml(log.admin_name || 'Admin')}</span>
                        </div>
                    </td>
                    <td><span class="action-badge ${this.getActionBadgeClass(log.action_type)}">${this.formatActionType(log.action_type)}</span></td>
                    <td>${log.target_type ? `<span class="target-type">${log.target_type}</span> ${log.target_id || ''}` : '-'}</td>
                    <td class="log-description">${this.escapeHtml(log.description || '-')}</td>
                    <td><code class="ip-address">${log.ip_address || '-'}</code></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar logs</td></tr>';
        }
    },
    
    async loadSecurityLogs() {
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Usuario</th>
                <th>Tipo Actividad</th>
                <th>Descripción</th>
                <th>Dispositivo</th>
                <th>IP</th>
            </tr>
        `;
        
        const search = document.getElementById('logSearch')?.value || '';
        const actionFilter = document.getElementById('logActionFilter')?.value || '';
        const dateFrom = document.getElementById('logDateFrom')?.value || '';
        const dateTo = document.getElementById('logDateTo')?.value || '';
        
        let url = `/api/admin/logs/security?page=${this.logsPage}&per_page=${this.logsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (actionFilter) url += `&activity_type=${encodeURIComponent(actionFilter)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        
        const response = await this.fetchAPI(url);
        
        if (response.success && response.logs) {
            this.logsTotalPages = response.pages || 1;
            this.updateLogsPagination();
            this.updateSecurityActivityFilter(response.activityTypes || []);
            
            if (response.logs.length === 0) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay logs de seguridad</td></tr>';
                return;
            }
            
            tbody.innerHTML = response.logs.map(log => `
                <tr class="${this.getSecurityRowClass(log.activity_type)}">
                    <td>${this.formatDateTime(log.created_at)}</td>
                    <td>${log.user_id || '-'}</td>
                    <td><span class="security-badge ${this.getSecurityBadgeClass(log.activity_type)}">${this.formatActivityType(log.activity_type)}</span></td>
                    <td class="log-description">${this.escapeHtml(log.description || '-')}</td>
                    <td><code class="device-id">${log.device_id ? log.device_id.substring(0, 8) + '...' : '-'}</code></td>
                    <td><code class="ip-address">${log.ip_address || '-'}</code></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar logs de seguridad</td></tr>';
        }
    },
    
    async loadLoginLogs() {
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Usuario</th>
                <th>Tipo</th>
                <th>Descripción</th>
                <th>Dispositivo</th>
                <th>IP</th>
            </tr>
        `;
        
        const search = document.getElementById('logSearch')?.value || '';
        const statusFilter = document.getElementById('logActionFilter')?.value || '';
        const dateFrom = document.getElementById('logDateFrom')?.value || '';
        const dateTo = document.getElementById('logDateTo')?.value || '';
        
        let url = `/api/admin/logs/logins?page=${this.logsPage}&per_page=${this.logsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        
        const response = await this.fetchAPI(url);
        
        if (response.success && response.logs) {
            this.logsTotalPages = response.pages || 1;
            this.updateLogsPagination();
            this.updateLoginStatusFilter(response.loginStats || []);
            this.renderSuspiciousIPs(response.suspiciousIPs || []);
            
            if (response.logs.length === 0) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay logs de login</td></tr>';
                return;
            }
            
            tbody.innerHTML = response.logs.map(log => `
                <tr class="${this.getSecurityRowClass(log.activity_type)}">
                    <td>${this.formatDateTime(log.created_at)}</td>
                    <td>${log.user_id || '-'}</td>
                    <td><span class="security-badge ${this.getSecurityBadgeClass(log.activity_type)}">${this.formatActivityType(log.activity_type)}</span></td>
                    <td class="log-description">${this.escapeHtml(log.description || '-')}</td>
                    <td><code class="device-id">${log.device_id ? log.device_id.substring(0, 8) + '...' : '-'}</code></td>
                    <td><code class="ip-address">${log.ip_address || '-'}</code></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar logs de login</td></tr>';
        }
    },
    
    async loadErrorLogs() {
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Nivel</th>
                <th>Endpoint</th>
                <th>Mensaje</th>
                <th>Estado</th>
                <th>Acción</th>
            </tr>
        `;
        
        const search = document.getElementById('logSearch')?.value || '';
        const levelFilter = document.getElementById('logActionFilter')?.value || '';
        const dateFrom = document.getElementById('logDateFrom')?.value || '';
        const dateTo = document.getElementById('logDateTo')?.value || '';
        
        let url = `/api/admin/logs/errors?page=${this.logsPage}&per_page=${this.logsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (levelFilter) url += `&level=${encodeURIComponent(levelFilter)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        
        const response = await this.fetchAPI(url);
        
        if (response.success && response.logs) {
            this.logsTotalPages = response.pages || 1;
            this.updateLogsPagination();
            this.updateErrorLevelFilter(response.errorLevels || []);
            
            if (response.logs.length === 0) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay errores del sistema</td></tr>';
                return;
            }
            
            tbody.innerHTML = response.logs.map(log => `
                <tr class="${log.is_resolved ? '' : 'log-row-warning'}">
                    <td>${this.formatDateTime(log.created_at)}</td>
                    <td><span class="error-level-badge ${log.error_level}">${log.error_level.toUpperCase()}</span></td>
                    <td><code>${this.escapeHtml(log.endpoint || '-')}</code></td>
                    <td class="log-description" title="${this.escapeHtml(log.stack_trace || '')}">${this.escapeHtml(log.error_message || '-')}</td>
                    <td><span class="status-badge ${log.is_resolved ? 'resolved' : 'pending'}">${log.is_resolved ? 'Resuelto' : 'Pendiente'}</span></td>
                    <td>
                        ${!log.is_resolved ? `<button class="btn-sm btn-success" onclick="AdminPanel.resolveError(${log.id})">Resolver</button>` : `<span class="resolved-by">${this.escapeHtml(log.resolved_by || '')}</span>`}
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar errores del sistema</td></tr>';
        }
    },
    
    async loadConfigHistory() {
        const tbody = document.getElementById('logsTableBody');
        const thead = document.getElementById('logsTableHead');
        
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Configuración</th>
                <th>Valor Anterior</th>
                <th>Valor Nuevo</th>
                <th>Cambiado Por</th>
                <th>IP</th>
            </tr>
        `;
        
        const search = document.getElementById('logSearch')?.value || '';
        const keyFilter = document.getElementById('logActionFilter')?.value || '';
        const dateFrom = document.getElementById('logDateFrom')?.value || '';
        const dateTo = document.getElementById('logDateTo')?.value || '';
        
        let url = `/api/admin/logs/config-history?page=${this.logsPage}&per_page=${this.logsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (keyFilter) url += `&key=${encodeURIComponent(keyFilter)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        
        const response = await this.fetchAPI(url);
        
        if (response.success && response.logs) {
            this.logsTotalPages = response.pages || 1;
            this.updateLogsPagination();
            this.updateConfigKeyFilter(response.configKeys || []);
            
            if (response.logs.length === 0) {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay historial de configuración</td></tr>';
                return;
            }
            
            tbody.innerHTML = response.logs.map(log => `
                <tr>
                    <td>${this.formatDateTime(log.created_at)}</td>
                    <td><code class="config-key">${this.escapeHtml(log.config_key)}</code></td>
                    <td class="old-value">${this.escapeHtml(log.old_value || '-')}</td>
                    <td class="new-value">${this.escapeHtml(log.new_value || '-')}</td>
                    <td>${this.escapeHtml(log.changed_by_name || 'Sistema')}</td>
                    <td><code class="ip-address">${log.ip_address || '-'}</code></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar historial de configuración</td></tr>';
        }
    },
    
    async resolveError(errorId) {
        try {
            const response = await this.fetchAPI(`/api/admin/logs/errors/${errorId}/resolve`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Error marcado como resuelto', 'success');
                this.loadErrorLogs();
            } else {
                this.showToast(response.error || 'Error al resolver', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al resolver', 'error');
        }
    },
    
    updateLoginStatusFilter(loginStats) {
        const filter = document.getElementById('logActionFilter');
        if (!filter || this.logsCurrentType !== 'logins') return;
        
        filter.innerHTML = `
            <option value="">Todos los estados</option>
            <option value="success">Exitosos</option>
            <option value="failed">Fallidos</option>
            <option value="blocked">Bloqueados</option>
        `;
    },
    
    updateErrorLevelFilter(errorLevels) {
        const filter = document.getElementById('logActionFilter');
        if (!filter || this.logsCurrentType !== 'errors') return;
        
        const currentValue = filter.value;
        filter.innerHTML = '<option value="">Todos los niveles</option>';
        errorLevels.forEach(el => {
            filter.innerHTML += `<option value="${el.error_level}" ${el.error_level === currentValue ? 'selected' : ''}>${el.error_level.toUpperCase()} (${el.count})</option>`;
        });
    },
    
    updateConfigKeyFilter(configKeys) {
        const filter = document.getElementById('logActionFilter');
        if (!filter || this.logsCurrentType !== 'config') return;
        
        const currentValue = filter.value;
        filter.innerHTML = '<option value="">Todas las claves</option>';
        configKeys.forEach(ck => {
            filter.innerHTML += `<option value="${ck.config_key}" ${ck.config_key === currentValue ? 'selected' : ''}>${ck.config_key} (${ck.count})</option>`;
        });
    },
    
    renderSuspiciousIPs(suspiciousIPs) {
        const container = document.getElementById('suspiciousIPsList');
        if (!container) return;
        
        if (!suspiciousIPs || suspiciousIPs.length === 0) {
            container.innerHTML = '<div class="empty-state">No hay IPs sospechosas en las últimas 24h</div>';
            return;
        }
        
        container.innerHTML = suspiciousIPs.map(ip => `
            <div class="suspicious-ip-item">
                <code class="ip-address">${ip.ip_address}</code>
                <span class="attempts-badge danger">${ip.attempts} intentos fallidos</span>
                <button class="btn-sm btn-danger" onclick="AdminPanel.blockIP('${ip.ip_address}')">Bloquear</button>
            </div>
        `).join('');
    },
    
    async blockIP(ipAddress) {
        if (!confirm(`¿Bloquear la IP ${ipAddress}?`)) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/blocked-ips', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_address: ipAddress, reason: 'Demasiados intentos fallidos de login' })
            });
            
            if (response.success) {
                this.showToast('IP bloqueada', 'success');
                this.loadLoginLogs();
            } else {
                this.showToast(response.error || 'Error al bloquear IP', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al bloquear IP', 'error');
        }
    },
    
    updateLogsPagination() {
        const prevBtn = document.getElementById('logsPrevBtn');
        const nextBtn = document.getElementById('logsNextBtn');
        const pageInfo = document.getElementById('logsPageInfo');
        
        if (prevBtn) prevBtn.disabled = this.logsPage <= 1;
        if (nextBtn) nextBtn.disabled = this.logsPage >= this.logsTotalPages;
        if (pageInfo) pageInfo.textContent = `Página ${this.logsPage} de ${this.logsTotalPages}`;
    },
    
    updateAdminActionFilter(actionTypes) {
        const filter = document.getElementById('logActionFilter');
        if (!filter || this.logsCurrentType !== 'admin') return;
        
        const currentValue = filter.value;
        filter.innerHTML = '<option value="">Todas las acciones</option>';
        actionTypes.forEach(at => {
            filter.innerHTML += `<option value="${at.action_type}" ${at.action_type === currentValue ? 'selected' : ''}>${this.formatActionType(at.action_type)} (${at.count})</option>`;
        });
    },
    
    updateSecurityActivityFilter(activityTypes) {
        const filter = document.getElementById('logActionFilter');
        if (!filter || this.logsCurrentType !== 'security') return;
        
        const currentValue = filter.value;
        filter.innerHTML = '<option value="">Todos los tipos</option>';
        activityTypes.forEach(at => {
            filter.innerHTML += `<option value="${at.activity_type}" ${at.activity_type === currentValue ? 'selected' : ''}>${this.formatActivityType(at.activity_type)} (${at.count})</option>`;
        });
    },
    
    formatActionType(actionType) {
        const actionMap = {
            'user_ban': 'Baneo Usuario',
            'user_unban': 'Desbaneo Usuario',
            'user_warn': 'Advertencia',
            'post_delete': 'Eliminar Post',
            'story_delete': 'Eliminar Story',
            'hashtag_block': 'Bloquear Hashtag',
            'hashtag_unblock': 'Desbloquear Hashtag',
            'withdrawal_approve': 'Aprobar Retiro',
            'withdrawal_reject': 'Rechazar Retiro',
            'bot_activate': 'Activar Bot',
            'bot_deactivate': 'Desactivar Bot',
            'settings_update': 'Actualizar Config',
            'login': 'Inicio Sesión'
        };
        return actionMap[actionType] || actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },
    
    formatActivityType(activityType) {
        const activityMap = {
            'WALLET_ACCESS': 'Acceso Wallet',
            'WALLET_FAILED_ATTEMPT': 'Intento Fallido',
            'WALLET_LOCKOUT': 'Bloqueo Wallet',
            'WALLET_UNLOCK': 'Desbloqueo Wallet',
            'DEVICE_TRUST': 'Dispositivo Confiable',
            'DEVICE_UNTRUST': 'Remover Dispositivo',
            'SECURITY_CODE_GENERATE': 'Generar Código',
            'SECURITY_CODE_VERIFY': 'Verificar Código',
            'LOGIN_SUCCESS': 'Login Exitoso',
            'LOGIN_FAILED': 'Login Fallido',
            'SUSPICIOUS_ACTIVITY': 'Actividad Sospechosa',
            'IP_BLOCKED': 'IP Bloqueada'
        };
        return activityMap[activityType] || activityType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },
    
    getActionBadgeClass(actionType) {
        if (actionType.includes('ban') || actionType.includes('delete') || actionType.includes('reject')) {
            return 'danger';
        }
        if (actionType.includes('warn') || actionType.includes('block')) {
            return 'warning';
        }
        if (actionType.includes('approve') || actionType.includes('activate') || actionType.includes('unban')) {
            return 'success';
        }
        return 'info';
    },
    
    getSecurityBadgeClass(activityType) {
        if (activityType.includes('LOCKOUT') || activityType.includes('BLOCKED') || activityType.includes('SUSPICIOUS')) {
            return 'danger';
        }
        if (activityType.includes('FAILED')) {
            return 'warning';
        }
        if (activityType.includes('SUCCESS') || activityType.includes('TRUST') || activityType.includes('VERIFY')) {
            return 'success';
        }
        return 'info';
    },
    
    getSecurityRowClass(activityType) {
        if (activityType.includes('LOCKOUT') || activityType.includes('BLOCKED')) {
            return 'log-row-danger';
        }
        if (activityType.includes('FAILED') || activityType.includes('SUSPICIOUS')) {
            return 'log-row-warning';
        }
        return '';
    },
    
    async exportLogs(format = 'csv') {
        try {
            const logType = this.logsCurrentType;
            const dateFrom = document.getElementById('logDateFrom')?.value || '';
            const dateTo = document.getElementById('logDateTo')?.value || '';
            
            let url = `/api/admin/logs/export?type=${logType}&format=${format}`;
            if (dateFrom) url += `&date_from=${dateFrom}`;
            if (dateTo) url += `&date_to=${dateTo}`;
            
            this.showToast('Preparando exportación...', 'info');
            
            const response = await fetch(url, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || '',
                    'X-Admin-Token': localStorage.getItem('admin_token') || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('Error en la exportación');
            }
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `logs_${logType}_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            this.showToast('Exportación completada', 'success');
        } catch (error) {
            console.error('Error exporting logs:', error);
            this.showToast('Error al exportar logs', 'error');
        }
    },
    
    setupLogsEventListeners() {
        document.querySelectorAll('.logs-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.logs-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.loadLogs(btn.dataset.log);
            });
        });
        
        document.getElementById('logSearch')?.addEventListener('input', this.debounce(() => {
            this.logsPage = 1;
            this.loadLogs();
        }, 500));
        
        document.getElementById('logActionFilter')?.addEventListener('change', () => {
            this.logsPage = 1;
            this.loadLogs();
        });
        
        document.getElementById('logDateFrom')?.addEventListener('change', () => {
            this.logsPage = 1;
            this.loadLogs();
        });
        
        document.getElementById('logDateTo')?.addEventListener('change', () => {
            this.logsPage = 1;
            this.loadLogs();
        });
        
        document.getElementById('refreshLogsBtn')?.addEventListener('click', () => {
            this.loadLogs();
            this.showToast('Logs actualizados', 'success');
        });
        
        document.getElementById('logsPrevBtn')?.addEventListener('click', () => {
            if (this.logsPage > 1) {
                this.logsPage--;
                this.loadLogs();
            }
        });
        
        document.getElementById('logsNextBtn')?.addEventListener('click', () => {
            if (this.logsPage < this.logsTotalPages) {
                this.logsPage++;
                this.loadLogs();
            }
        });
        
        document.getElementById('exportLogsBtn')?.addEventListener('click', () => {
            const menu = document.getElementById('exportLogsMenu');
            if (menu) {
                menu.classList.toggle('show');
            }
        });
        
        document.querySelectorAll('.export-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                this.exportLogs(format);
                document.getElementById('exportLogsMenu')?.classList.remove('show');
            });
        });
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.export-dropdown')) {
                document.getElementById('exportLogsMenu')?.classList.remove('show');
            }
        });
    },
    
    async loadSettings() {
        try {
            const [settingsRes, statusRes] = await Promise.all([
                this.fetchAPI('/api/admin/settings'),
                this.fetchAPI('/api/admin/system-status')
            ]);
            
            if (settingsRes.success) {
                const s = settingsRes;
                this.setInputValue('configB3CPrice', s.b3cPriceUSD || 0.10);
                this.setInputValue('txCommission', s.transactionFeePercent || 5);
                this.setInputValue('minWithdrawal', s.minWithdrawal || 10);
                this.setInputValue('minDepositTON', s.minDepositTON || 0.5);
                
                this.setInputValue('vnMinPriceB3C', s.vnMinPriceB3C || 25);
                this.setInputValue('vnMargin', s.vnMargin || 30);
                this.setInputValue('smsTimeout', s.smsTimeout || 180);
                
                this.setInputValue('rateLimitPerMin', s.rateLimitPerMin || 60);
                this.setInputValue('autoBlockAfter', s.autoBlockAfter || 3);
                this.setInputValue('blockDuration', s.blockDuration || 24);
                
                const maintenanceModeEl = document.getElementById('maintenanceMode');
                const maintenanceMessageEl = document.getElementById('maintenanceMessage');
                const maintenanceEndTimeEl = document.getElementById('maintenanceEndTime');
                
                if (maintenanceModeEl) maintenanceModeEl.checked = s.maintenanceMode || false;
                if (maintenanceMessageEl) maintenanceMessageEl.value = s.maintenanceMessage || '';
                if (maintenanceEndTimeEl && s.maintenanceEndTime) {
                    maintenanceEndTimeEl.value = s.maintenanceEndTime.slice(0, 16);
                }
            }
            
            this.updateSystemStatus(statusRes);
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    },
    
    setInputValue(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value;
    },
    
    updateSystemStatus(statusRes) {
        if (!statusRes.success) return;
        
        const status = statusRes.status || {};
        
        const updateStatusEl = (id, data) => {
            const el = document.getElementById(id);
            if (el && data) {
                el.textContent = data.message || data.status;
                el.className = `status-indicator ${data.status === 'ok' ? 'ok' : data.status === 'warning' ? 'warning' : 'error'}`;
            }
        };
        
        updateStatusEl('dbStatus', status.database);
        updateStatusEl('tonStatus', status.toncenter);
        updateStatusEl('smsStatus', status.smspool);
        updateStatusEl('walletPoolStatus', status.walletPool);
        updateStatusEl('hotWalletStatus', status.hotWallet);
        
        const lastCheckEl = document.getElementById('lastStatusCheck');
        if (lastCheckEl) {
            lastCheckEl.textContent = new Date().toLocaleTimeString();
        }
        
        if (statusRes.secrets) {
            const secretsList = document.getElementById('secretsList');
            if (secretsList) {
                const secretsHtml = Object.entries(statusRes.secrets).map(([name, configured]) => `
                    <div class="secret-item">
                        <span class="secret-name">${this.escapeHtml(name)}</span>
                        <span class="secret-status ${configured ? 'configured' : 'missing'}">
                            ${configured ? '✓ Configurado' : '✗ No configurado'}
                        </span>
                    </div>
                `).join('');
                SafeDOM.setHTML(secretsList, secretsHtml);
            }
        }
    },
    
    async refreshSystemStatus() {
        try {
            this.showToast('Verificando estado del sistema...', 'info');
            const statusRes = await this.fetchAPI('/api/admin/system-status?refresh=true');
            this.updateSystemStatus(statusRes);
            this.showToast('Estado actualizado', 'success');
        } catch (error) {
            console.error('Error refreshing status:', error);
            this.showToast('Error al actualizar estado', 'error');
        }
    },
    
    async saveSystemConfig() {
        try {
            const data = {
                b3cPriceUSD: parseFloat(document.getElementById('configB3CPrice')?.value) || 0.10,
                transactionFeePercent: parseFloat(document.getElementById('txCommission')?.value) || 5,
                minWithdrawal: parseFloat(document.getElementById('minWithdrawal')?.value) || 10,
                minDepositTON: parseFloat(document.getElementById('minDepositTON')?.value) || 0.5,
                
                vnMinPriceB3C: parseInt(document.getElementById('vnMinPriceB3C')?.value) || 25,
                vnMargin: parseInt(document.getElementById('vnMargin')?.value) || 30,
                smsTimeout: parseInt(document.getElementById('smsTimeout')?.value) || 180,
                
                rateLimitPerMin: parseInt(document.getElementById('rateLimitPerMin')?.value) || 60,
                autoBlockAfter: parseInt(document.getElementById('autoBlockAfter')?.value) || 3,
                blockDuration: parseInt(document.getElementById('blockDuration')?.value) || 24,
                
                maintenanceMode: document.getElementById('maintenanceMode')?.checked || false,
                maintenanceMessage: document.getElementById('maintenanceMessage')?.value || '',
                maintenanceEndTime: document.getElementById('maintenanceEndTime')?.value || null
            };
            
            const response = await this.fetchAPI('/api/admin/settings', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            if (response.success) {
                this.showToast('Configuración guardada correctamente', 'success');
            } else {
                this.showToast(response.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('Error al guardar configuración', 'error');
        }
    },
    
    async toggleMaintenance() {
        const isActive = document.getElementById('maintenanceMode')?.checked;
        const message = document.getElementById('maintenanceMessage')?.value || 'Estamos realizando mantenimiento. Volveremos pronto.';
        
        try {
            const response = await this.fetchAPI('/api/admin/maintenance', {
                method: 'POST',
                body: JSON.stringify({ active: isActive, message })
            });
            
            if (response.success) {
                this.showToast(isActive ? 'Modo mantenimiento activado' : 'Modo mantenimiento desactivado', isActive ? 'warning' : 'success');
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error toggling maintenance:', error);
            this.showToast('Error al cambiar modo mantenimiento', 'error');
        }
    },
    
    async saveSettings() {
        await this.saveSystemConfig();
    },
    
    async loadMaintenance() {
        try {
            const response = await this.fetchAPI('/api/admin/server-status');
            
            if (response.success) {
                const s = response;
                document.getElementById('serverUptime').textContent = s.uptime || '-';
                
                const memoryPct = s.memoryPercent || 0;
                const cpuPct = s.cpuPercent || 0;
                const diskPct = s.diskPercent || 0;
                
                document.getElementById('memoryUsage').textContent = `${memoryPct}%`;
                document.getElementById('cpuUsage').textContent = `${cpuPct}%`;
                document.getElementById('diskUsage').textContent = `${diskPct}%`;
                
                const memoryBar = document.getElementById('memoryBar');
                const cpuBar = document.getElementById('cpuBar');
                const diskBar = document.getElementById('diskBar');
                
                if (memoryBar) {
                    memoryBar.style.width = `${memoryPct}%`;
                    memoryBar.className = `bar-fill ${memoryPct > 80 ? 'danger' : memoryPct > 60 ? 'warning' : ''}`;
                }
                if (cpuBar) {
                    cpuBar.style.width = `${cpuPct}%`;
                    cpuBar.className = `bar-fill ${cpuPct > 80 ? 'danger' : cpuPct > 60 ? 'warning' : ''}`;
                }
                if (diskBar) {
                    diskBar.style.width = `${diskPct}%`;
                    diskBar.className = `bar-fill ${diskPct > 80 ? 'danger' : diskPct > 60 ? 'warning' : ''}`;
                }
                
                document.getElementById('dbConnections').textContent = s.dbConnections || 0;
                document.getElementById('lastBackupTime').textContent = s.lastBackup || 'No disponible';
                document.getElementById('dbSize').textContent = s.dbSize || '-';
                document.getElementById('errorsLast24h').textContent = s.errorsLast24h || 0;
                document.getElementById('warningsLast24h').textContent = s.warningsLast24h || 0;
                document.getElementById('logsSize').textContent = s.logsSize || '-';
            }
        } catch (error) {
            console.error('Error loading maintenance:', error);
        }
    },
    
    async refreshServerStatus() {
        this.showToast('Actualizando estado del servidor...', 'info');
        await this.loadMaintenance();
        this.showToast('Estado actualizado', 'success');
    },
    
    async createBackup() {
        if (!confirm('¿Crear un backup de la base de datos?')) return;
        
        try {
            this.showToast('Creando backup...', 'info');
            const response = await this.fetchAPI('/api/admin/backup/create', { method: 'POST' });
            
            if (response.success) {
                this.showToast(`Backup creado: ${response.filename || 'OK'}`, 'success');
                this.loadMaintenance();
            } else {
                this.showToast(response.error || 'Error al crear backup', 'error');
            }
        } catch (error) {
            console.error('Error creating backup:', error);
            this.showToast('Error al crear backup', 'error');
        }
    },
    
    async showBackupHistory() {
        try {
            const response = await this.fetchAPI('/api/admin/backup/history');
            
            if (response.success && response.backups) {
                const html = response.backups.length > 0 
                    ? response.backups.map(b => `<div class="backup-item">${b.filename} - ${b.date} - ${b.size}</div>`).join('')
                    : '<p>No hay backups disponibles</p>';
                
                alert('Historial de Backups:\n' + (response.backups.map(b => `${b.filename} (${b.size})`).join('\n') || 'No hay backups'));
            }
        } catch (error) {
            console.error('Error loading backup history:', error);
            this.showToast('Error al cargar historial', 'error');
        }
    },
    
    async clearCache() {
        if (!confirm('¿Limpiar la caché del sistema?')) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/maintenance/clear-cache', { method: 'POST' });
            
            if (response.success) {
                this.showToast('Caché limpiada correctamente', 'success');
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error clearing cache:', error);
            this.showToast('Error al limpiar caché', 'error');
        }
    },
    
    async optimizeDatabase() {
        if (!confirm('¿Optimizar la base de datos? Esto puede tomar unos segundos.')) return;
        
        try {
            this.showToast('Optimizando base de datos...', 'info');
            const response = await this.fetchAPI('/api/admin/maintenance/optimize-db', { method: 'POST' });
            
            if (response.success) {
                this.showToast('Base de datos optimizada', 'success');
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error optimizing database:', error);
            this.showToast('Error al optimizar', 'error');
        }
    },
    
    async cleanupOldSessions() {
        if (!confirm('¿Limpiar sesiones inactivas (más de 30 días)?')) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/maintenance/cleanup-sessions', { method: 'POST' });
            
            if (response.success) {
                this.showToast(`${response.deleted || 0} sesiones eliminadas`, 'success');
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error cleaning sessions:', error);
            this.showToast('Error al limpiar sesiones', 'error');
        }
    },
    
    async cleanupOldData() {
        if (!confirm('¿Limpiar datos antiguos (logs, notificaciones, etc. de más de 90 días)? Esta acción no se puede deshacer.')) return;
        
        try {
            this.showToast('Limpiando datos antiguos...', 'info');
            const response = await this.fetchAPI('/api/admin/maintenance/cleanup-old-data', { method: 'POST' });
            
            if (response.success) {
                this.showToast(`Datos limpiados: ${response.summary || 'OK'}`, 'success');
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error cleaning old data:', error);
            this.showToast('Error al limpiar datos', 'error');
        }
    },
    
    async downloadLogs() {
        try {
            window.open('/api/admin/logs/download', '_blank');
        } catch (error) {
            console.error('Error downloading logs:', error);
            this.showToast('Error al descargar logs', 'error');
        }
    },
    
    async clearLogs() {
        if (!confirm('¿Limpiar los logs del sistema? Esta acción no se puede deshacer.')) return;
        
        try {
            const response = await this.fetchAPI('/api/admin/maintenance/clear-logs', { method: 'POST' });
            
            if (response.success) {
                this.showToast('Logs limpiados correctamente', 'success');
                this.loadMaintenance();
            } else {
                this.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error clearing logs:', error);
            this.showToast('Error al limpiar logs', 'error');
        }
    },
    
    async loadRealtime() {
        try {
            const response = await this.fetchAPI('/api/admin/realtime/online');
            
            if (response.success) {
                document.getElementById('onlineCount').textContent = response.count || 0;
                
                const usersList = document.getElementById('onlineUsersList');
                if (response.users && response.users.length > 0) {
                    usersList.innerHTML = response.users.map(u => `
                        <div class="online-user-item" onclick="AdminPanel.viewUser('${u.user_id}')">
                            <span class="online-status ${u.status}"></span>
                            <div class="user-avatar-sm">${(u.first_name || 'U')[0].toUpperCase()}</div>
                            <div class="user-info">
                                <span class="user-name">${this.escapeHtml(u.first_name || 'Usuario')}</span>
                                <span class="user-username">@${this.escapeHtml(u.username || 'N/A')}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    usersList.innerHTML = '<div class="empty-state">No hay usuarios conectados</div>';
                }
            }
        } catch (error) {
            console.error('Error loading realtime:', error);
        }
    },
    
    async loadRecentActivity() {
        try {
            const response = await this.fetchAPI('/api/admin/dashboard/activity');
            if (response.success) {
                this.renderActivity(response.data);
            }
        } catch (error) {
            console.error('Error loading activity:', error);
        }
    },
    
    async adjustBalance(userId) {
        const amount = prompt('Ingresa la cantidad de B3C (positivo para agregar, negativo para restar):');
        if (amount === null) return;
        
        const numAmount = parseFloat(amount);
        if (isNaN(numAmount) || numAmount === 0) {
            this.showToast('Cantidad inválida', 'error');
            return;
        }
        
        const reason = prompt('Razón del ajuste (opcional):') || 'Ajuste manual del admin';
        
        try {
            const response = await this.fetchAPI('/api/admin/user/credits', {
                method: 'POST',
                body: JSON.stringify({ 
                    userId: userId, 
                    amount: numAmount,
                    reason: reason
                })
            });
            
            if (response.success) {
                this.showToast(`Balance ajustado: ${numAmount > 0 ? '+' : ''}${numAmount} B3C`, 'success');
                this.loadUsers();
                this.viewUser(userId);
            } else {
                this.showToast(response.error || 'Error al ajustar balance', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al ajustar balance', 'error');
        }
    },
    
    async viewUserTransactions(userId) {
        const modal = document.getElementById('userDetailModal');
        const content = document.getElementById('userDetailContent');
        
        content.innerHTML = 'Cargando transacciones...';
        modal.classList.add('active');
        
        try {
            const response = await this.fetchAPI(`/api/admin/transactions?user_id=${userId}&limit=50`);
            
            if (response.success && response.transactions) {
                if (response.transactions.length === 0) {
                    content.innerHTML = `
                        <div class="user-detail-header">
                            <h3>Transacciones del Usuario</h3>
                        </div>
                        <div class="empty-state">Este usuario no tiene transacciones</div>
                        <div class="user-actions">
                            <button class="btn-secondary" onclick="AdminPanel.viewUser('${userId}')">Volver al Perfil</button>
                        </div>
                    `;
                    return;
                }
                
                const typeLabels = {
                    buy: 'Compra B3C',
                    sell: 'Venta B3C',
                    transfer: 'Transferencia',
                    withdrawal: 'Retiro',
                    deposit: 'Depósito'
                };
                
                content.innerHTML = `
                    <div class="user-detail-header">
                        <h3>Transacciones del Usuario (${response.transactions.length})</h3>
                    </div>
                    <div class="user-tx-list" style="max-height: 400px; overflow-y: auto;">
                        ${response.transactions.map(tx => `
                            <div class="tx-item" style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span class="tx-type">${typeLabels[tx.type] || tx.type}</span>
                                    <span class="tx-amount">${this.formatNumber(tx.amount, 4)} ${tx.currency || 'B3C'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #848E9C;">
                                    <span class="status-badge ${tx.status}" style="font-size: 10px;">${tx.status}</span>
                                    <span>${this.formatDateTime(tx.created_at)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="user-actions">
                        <button class="btn-secondary" onclick="AdminPanel.viewUser('${userId}')">Volver al Perfil</button>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">Error al cargar transacciones</div>';
            }
        } catch (error) {
            console.error('Error loading user transactions:', error);
            content.innerHTML = '<div class="empty-state">Error al cargar transacciones</div>';
        }
    },
    
    async exportUsers() {
        try {
            const response = await this.fetchAPI('/api/admin/users/export');
            if (response.success && response.csv) {
                this.downloadCSV(response.csv, 'usuarios_bunk3r.csv');
                this.showToast('Exportación completada', 'success');
            } else {
                this.showToast(response.error || 'Error al exportar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al exportar', 'error');
        }
    },
    
    async exportTransactions() {
        try {
            const response = await this.fetchAPI('/api/admin/transactions/export');
            if (response.success && response.csv) {
                this.downloadCSV(response.csv, 'transacciones_bunk3r.csv');
                this.showToast('Exportación completada', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error al exportar', 'error');
        }
    },
    
    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    openTxHash(hash) {
        window.open(`https://tonscan.org/tx/${hash}`, '_blank');
    },
    
    async viewTransaction(txId) {
        const modal = document.getElementById('transactionDetailModal');
        const content = document.getElementById('transactionDetailContent');
        
        modal.classList.add('active');
        content.innerHTML = '<div class="loading-spinner">Cargando...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/transactions/${txId}`);
            
            if (response.success && response.transaction) {
                const tx = response.transaction;
                const statusClass = tx.status === 'completed' ? 'success' : (tx.status === 'pending' ? 'warning' : 'danger');
                
                content.innerHTML = `
                    <div class="tx-detail-grid">
                        <div class="tx-detail-header">
                            <div class="tx-type-badge ${tx.type}">${this.escapeHtml(tx.type_label)}</div>
                            <div class="tx-amount ${tx.type.includes('out') || tx.type === 'withdrawal' || tx.type === 'fee' ? 'negative' : 'positive'}">
                                ${tx.type.includes('out') || tx.type === 'withdrawal' || tx.type === 'fee' ? '-' : '+'}${tx.amount.toFixed(2)} ${tx.currency}
                            </div>
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Información General</h4>
                            <div class="detail-row">
                                <span class="detail-label">ID Transacción:</span>
                                <span class="detail-value">#${tx.id}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Estado:</span>
                                <span class="detail-value"><span class="status-badge ${statusClass}">${tx.status}</span></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Fecha:</span>
                                <span class="detail-value">${this.formatDateTime(tx.created_at)}</span>
                            </div>
                            ${tx.description ? `
                            <div class="detail-row">
                                <span class="detail-label">Descripción:</span>
                                <span class="detail-value">${this.escapeHtml(tx.description)}</span>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Usuario</h4>
                            <div class="detail-row">
                                <span class="detail-label">Username:</span>
                                <span class="detail-value">@${this.escapeHtml(tx.username)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Nombre:</span>
                                <span class="detail-value">${this.escapeHtml(tx.user_name)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Telegram ID:</span>
                                <span class="detail-value">${tx.telegram_id || 'N/A'}</span>
                            </div>
                        </div>
                        
                        ${tx.balance_before !== null || tx.balance_after !== null ? `
                        <div class="tx-detail-section">
                            <h4>Balance</h4>
                            ${tx.balance_before !== null ? `
                            <div class="detail-row">
                                <span class="detail-label">Balance Anterior:</span>
                                <span class="detail-value">${tx.balance_before.toFixed(2)} B3C</span>
                            </div>
                            ` : ''}
                            ${tx.balance_after !== null ? `
                            <div class="detail-row">
                                <span class="detail-label">Balance Posterior:</span>
                                <span class="detail-value">${tx.balance_after.toFixed(2)} B3C</span>
                            </div>
                            ` : ''}
                        </div>
                        ` : ''}
                        
                        ${tx.tx_hash ? `
                        <div class="tx-detail-section">
                            <h4>Blockchain</h4>
                            <div class="detail-row">
                                <span class="detail-label">TX Hash:</span>
                                <span class="detail-value tx-hash-full">
                                    <code>${this.escapeHtml(tx.tx_hash)}</code>
                                </span>
                            </div>
                            <div class="detail-actions">
                                <button class="btn-primary btn-sm" onclick="AdminPanel.openTxHash('${tx.tx_hash}')">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                        <polyline points="15 3 21 3 21 9"></polyline>
                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                    </svg>
                                    Ver en TonScan
                                </button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                content.innerHTML = `<div class="error-state">Error: ${response.error || 'No se pudo cargar la transacción'}</div>`;
            }
        } catch (error) {
            console.error('Error loading transaction:', error);
            content.innerHTML = '<div class="error-state">Error al cargar los datos</div>';
        }
    },
    
    async loadPurchases() {
        const tbody = document.getElementById('purchasesTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="9">Cargando compras...</td></tr>';
        
        try {
            const status = document.getElementById('purchaseStatusFilter')?.value || '';
            const response = await this.fetchAPI(`/api/admin/purchases?status=${status}`);
            
            if (response.success) {
                this.renderPurchasesTable(response.purchases);
                
                if (response.stats) {
                    document.getElementById('purchasesTotal').textContent = response.stats.totalPurchases || 0;
                    document.getElementById('purchasesPending').textContent = response.stats.pendingCount || 0;
                    document.getElementById('purchasesConfirmed').textContent = response.stats.confirmedCount || 0;
                    document.getElementById('purchasesTotalTon').textContent = this.formatNumber(response.stats.totalTon || 0, 4);
                }
            } else {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="9">Error al cargar compras</td></tr>';
            }
        } catch (error) {
            console.error('Error loading purchases:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="9">Error al cargar compras</td></tr>';
        }
    },
    
    renderPurchasesTable(purchases) {
        const tbody = document.getElementById('purchasesTableBody');
        
        if (!purchases || purchases.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="9">No se encontraron compras</td></tr>';
            return;
        }
        
        tbody.innerHTML = purchases.map(p => {
            const statusClass = p.status === 'confirmed' ? 'success' : 
                               (p.status === 'pending' ? 'warning' : 'danger');
            const walletShort = p.depositWallet ? 
                `${p.depositWallet.slice(0, 8)}...${p.depositWallet.slice(-6)}` : '-';
            const txHashShort = p.txHash ? 
                `${p.txHash.slice(0, 10)}...` : '-';
            
            return `
                <tr>
                    <td><code>${this.escapeHtml(p.purchaseId.slice(0, 8))}...</code></td>
                    <td>
                        <div class="user-cell">
                            <span class="username">@${this.escapeHtml(p.username)}</span>
                        </div>
                    </td>
                    <td>${this.formatNumber(p.tonAmount, 4)} TON</td>
                    <td>${this.formatNumber(p.b3cAmount, 2)} B3C</td>
                    <td><span class="status-badge ${statusClass}">${p.statusLabel}</span></td>
                    <td>
                        ${p.depositWallet ? 
                            `<span class="wallet-address" onclick="AdminPanel.copyToClipboard('${p.depositWallet}')" title="${p.depositWallet}">${walletShort}</span>` 
                            : '-'}
                    </td>
                    <td>
                        ${p.txHash ? 
                            `<span class="tx-hash" onclick="AdminPanel.openTxHash('${p.txHash}')">${txHashShort}</span>` 
                            : '-'}
                    </td>
                    <td>${this.formatDate(p.createdAt)}</td>
                    <td>
                        <div class="action-btns">
                            <button class="action-btn" onclick="AdminPanel.viewPurchase('${p.purchaseId}')">Ver</button>
                            ${p.status === 'pending' ? 
                                `<button class="action-btn credit" onclick="AdminPanel.creditPurchase('${p.purchaseId}')">Acreditar</button>` 
                                : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },
    
    async viewPurchase(purchaseId) {
        const modal = document.getElementById('purchaseDetailModal');
        const content = document.getElementById('purchaseDetailContent');
        
        modal.classList.add('active');
        content.innerHTML = '<div class="loading-spinner">Cargando...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/purchases/${purchaseId}`);
            
            if (response.success && response.purchase) {
                const p = response.purchase;
                const statusClass = p.status === 'confirmed' ? 'success' : 
                                   (p.status === 'pending' ? 'warning' : 'danger');
                
                content.innerHTML = `
                    <div class="tx-detail-grid">
                        <div class="tx-detail-header">
                            <div class="tx-type-badge buy">Compra B3C</div>
                            <span class="status-badge ${statusClass}">${p.statusLabel}</span>
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Información de la Compra</h4>
                            <div class="detail-row">
                                <span class="detail-label">ID Compra:</span>
                                <span class="detail-value"><code>${this.escapeHtml(p.purchaseId)}</code></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">TON Enviados:</span>
                                <span class="detail-value">${p.tonAmount.toFixed(4)} TON</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">B3C a Recibir:</span>
                                <span class="detail-value">${p.b3cAmount.toFixed(2)} B3C</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Comisión:</span>
                                <span class="detail-value">${p.commissionTon.toFixed(4)} TON</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Fecha:</span>
                                <span class="detail-value">${this.formatDateTime(p.createdAt)}</span>
                            </div>
                            ${p.confirmedAt ? `
                            <div class="detail-row">
                                <span class="detail-label">Confirmada:</span>
                                <span class="detail-value">${this.formatDateTime(p.confirmedAt)}</span>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Usuario</h4>
                            <div class="detail-row">
                                <span class="detail-label">Username:</span>
                                <span class="detail-value">@${this.escapeHtml(p.username)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Nombre:</span>
                                <span class="detail-value">${this.escapeHtml(p.userFullName)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Telegram ID:</span>
                                <span class="detail-value">${p.telegramId || 'N/A'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Balance Actual:</span>
                                <span class="detail-value">${p.userBalance.toFixed(2)} B3C</span>
                            </div>
                        </div>
                        
                        ${p.depositWallet ? `
                        <div class="tx-detail-section">
                            <h4>Wallet de Depósito</h4>
                            <div class="detail-row">
                                <span class="detail-label">Dirección:</span>
                                <span class="detail-value wallet-full">
                                    <code>${this.escapeHtml(p.depositWallet)}</code>
                                </span>
                            </div>
                            ${p.expectedAmount ? `
                            <div class="detail-row">
                                <span class="detail-label">Monto Esperado:</span>
                                <span class="detail-value">${p.expectedAmount.toFixed(4)} TON</span>
                            </div>
                            ` : ''}
                            ${p.depositAmount ? `
                            <div class="detail-row">
                                <span class="detail-label">Monto Recibido:</span>
                                <span class="detail-value">${p.depositAmount.toFixed(4)} TON</span>
                            </div>
                            ` : ''}
                            <div class="detail-row">
                                <span class="detail-label">Estado Wallet:</span>
                                <span class="detail-value">${p.walletStatus || 'N/A'}</span>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${p.txHash ? `
                        <div class="tx-detail-section">
                            <h4>Blockchain</h4>
                            <div class="detail-row">
                                <span class="detail-label">TX Hash:</span>
                                <span class="detail-value tx-hash-full">
                                    <code>${this.escapeHtml(p.txHash)}</code>
                                </span>
                            </div>
                            <div class="detail-actions">
                                <button class="btn-primary btn-sm" onclick="AdminPanel.openTxHash('${p.txHash}')">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                        <polyline points="15 3 21 3 21 9"></polyline>
                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                    </svg>
                                    Ver en TonScan
                                </button>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${p.status === 'pending' ? `
                        <div class="tx-detail-section">
                            <h4>Acciones</h4>
                            <button class="btn-primary btn-full" onclick="AdminPanel.creditPurchase('${p.purchaseId}')">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                                Acreditar Manualmente
                            </button>
                            <p class="action-warning">Esta acción añadirá ${p.b3cAmount.toFixed(2)} B3C al balance del usuario.</p>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                content.innerHTML = `<div class="error-state">Error: ${response.error || 'No se pudo cargar la compra'}</div>`;
            }
        } catch (error) {
            console.error('Error loading purchase:', error);
            content.innerHTML = '<div class="error-state">Error al cargar los datos</div>';
        }
    },
    
    async creditPurchase(purchaseId) {
        if (!confirm('¿Estás seguro de acreditar manualmente esta compra? Esta acción añadirá B3C al balance del usuario.')) {
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/purchases/${purchaseId}/credit`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(response.message || 'Compra acreditada correctamente', 'success');
                document.getElementById('purchaseDetailModal').classList.remove('active');
                this.loadPurchases();
            } else {
                this.showToast(response.error || 'Error al acreditar la compra', 'error');
            }
        } catch (error) {
            console.error('Error crediting purchase:', error);
            this.showToast('Error al acreditar la compra', 'error');
        }
    },
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado al portapapeles', 'success');
        }).catch(() => {
            this.showToast('Error al copiar', 'error');
        });
    },
    
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboard();
            } else if (this.currentSection === 'realtime') {
                this.loadRealtime();
            }
        }, 30000);
    },
    
    getDemoSessionToken() {
        return localStorage.getItem('demo_session_token') || null;
    },
    
    getAdminSessionToken() {
        return localStorage.getItem('admin_session_token') || null;
    },
    
    isTelegramMode() {
        return window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData && window.Telegram.WebApp.initData.length > 0;
    },
    
    getTelegramInitData() {
        if (this.isTelegramMode()) {
            return window.Telegram.WebApp.initData;
        }
        return null;
    },
    
    async fetchAPI(url, options = {}) {
        const isTelegram = this.isTelegramMode();
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (isTelegram) {
            headers['X-Telegram-Init-Data'] = this.getTelegramInitData();
            const adminToken = this.getAdminSessionToken();
            if (adminToken) {
                headers['X-Admin-Session'] = adminToken;
            }
        } else {
            headers['X-Demo-Mode'] = 'true';
            const demoToken = this.getDemoSessionToken();
            if (demoToken) {
                headers['X-Demo-Session'] = demoToken;
            }
        }
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });
            
            if (response.status === 401) {
                this.show2FAModal();
                return { success: false, error: 'Se requiere verificación 2FA' };
            }
            
            const data = await response.json();
            
            if (data.code === 'DEMO_2FA_REQUIRED' || data.requiresDemo2FA) {
                this.show2FAModal();
                return { success: false, error: 'Se requiere verificación 2FA' };
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: error.message };
        }
    },
    
    show2FAModal() {
        if (document.getElementById('admin2FAModal')) return;
        
        const isTelegram = this.isTelegramMode();
        const title = isTelegram ? 'Verificación 2FA' : 'Acceso Demo';
        const message = isTelegram 
            ? 'Ingresa el código de tu Google Authenticator para acceder al panel de administración.'
            : 'Ingresa la contraseña de administrador para acceder al modo demo.';
        const placeholder = isTelegram ? 'Código de 6 dígitos' : 'Contraseña';
        const inputType = isTelegram ? 'text' : 'password';
        const maxLength = isTelegram ? '6' : '50';
        const letterSpacing = isTelegram ? 'letter-spacing: 8px;' : '';
        
        const modal = document.createElement('div');
        modal.id = 'admin2FAModal';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.8);';
        modal.innerHTML = `
            <div style="background: #1E2329; border-radius: 16px; max-width: 400px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
                <div style="padding: 20px 24px; border-bottom: 1px solid #2B3139;">
                    <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: #EAECEF;">${title}</h2>
                </div>
                <div style="padding: 24px;">
                    <p style="color: #848E9C; margin: 0 0 16px 0; font-size: 14px;">
                        ${message}
                    </p>
                    <input type="${inputType}" id="admin2FACode" placeholder="${placeholder}" 
                           style="width: 100%; padding: 12px; font-size: 18px; text-align: center; ${letterSpacing} border: 1px solid #2B3139; border-radius: 8px; background: #0B0E11; color: #EAECEF; box-sizing: border-box;"
                           maxlength="${maxLength}" autocomplete="off">
                    <button id="admin2FASubmit" style="width: 100%; margin-top: 16px; padding: 12px; background: #F0B90B; color: #000; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                        Acceder
                    </button>
                    <p id="admin2FAError" style="color: #F6465D; margin-top: 12px; display: none; text-align: center; font-size: 14px;"></p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        document.getElementById('admin2FACode').focus();
        
        document.getElementById('admin2FASubmit').addEventListener('click', () => this.verify2FA());
        document.getElementById('admin2FACode').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.verify2FA();
        });
    },
    
    async verify2FA() {
        const code = document.getElementById('admin2FACode').value.trim();
        const errorEl = document.getElementById('admin2FAError');
        
        if (!code || code.length !== 6) {
            errorEl.textContent = 'Ingresa un código de 6 dígitos';
            errorEl.style.display = 'block';
            return;
        }
        
        try {
            const isTelegram = this.isTelegramMode();
            const endpoint = isTelegram ? '/api/admin/2fa/verify' : '/api/demo/2fa/verify';
            const headers = { 'Content-Type': 'application/json' };
            
            if (isTelegram) {
                headers['X-Telegram-Init-Data'] = this.getTelegramInitData();
            } else {
                headers['X-Demo-Mode'] = 'true';
            }
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ code })
            });
            
            const data = await response.json();
            
            const token = data.sessionToken || data.session_token;
            if (data.success && token) {
                if (isTelegram) {
                    this.adminSessionToken = token;
                    localStorage.setItem('admin_session_token', token);
                } else {
                    this.demoSessionToken = token;
                    localStorage.setItem('demo_session_token', token);
                }
                document.getElementById('admin2FAModal').remove();
                this.showToast('Verificación exitosa', 'success');
                this.loadSectionData(this.currentSection);
            } else {
                errorEl.textContent = data.error || 'Código incorrecto';
                errorEl.style.display = 'block';
            }
        } catch (error) {
            errorEl.textContent = 'Error de conexión';
            errorEl.style.display = 'block';
        }
    },
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span class="toast-message">${this.escapeHtml(message)}</span>`;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 4000);
    },
    
    formatNumber(num, decimals = 0) {
        if (num === null || num === undefined) return '-';
        const n = parseFloat(num);
        if (isNaN(n)) return '-';
        
        if (n >= 1000000) {
            return (n / 1000000).toFixed(1) + 'M';
        } else if (n >= 1000) {
            return (n / 1000).toFixed(1) + 'K';
        }
        return n.toFixed(decimals).replace(/\.?0+$/, '');
    },
    
    formatDate(dateStr) {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
        } catch {
            return '-';
        }
    },
    
    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleString('es-ES', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return '-';
        }
    },
    
    timeAgo(dateStr) {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            const seconds = Math.floor((new Date() - date) / 1000);
            
            if (seconds < 60) return 'Hace un momento';
            if (seconds < 3600) return `Hace ${Math.floor(seconds / 60)} min`;
            if (seconds < 86400) return `Hace ${Math.floor(seconds / 3600)} h`;
            return `Hace ${Math.floor(seconds / 86400)} días`;
        } catch {
            return '-';
        }
    },
    
    formatDuration(seconds) {
        if (!seconds) return '-';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    },
    
    getLast30Days() {
        const days = [];
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            days.push(date.getDate().toString());
        }
        return days;
    },
    
    getActivityIcon(type) {
        const icons = {
            login: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>',
            transaction: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
            post: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
            register: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>'
        };
        return icons[type] || icons.login;
    },
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    async loadWithdrawals() {
        const tbody = document.getElementById('withdrawalsTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Cargando retiros...</td></tr>';
        
        try {
            const status = document.getElementById('withdrawalStatusFilter')?.value || '';
            const response = await this.fetchAPI(`/api/admin/b3c/withdrawals?status=${status}`);
            
            if (response.success) {
                this.renderWithdrawalsTable(response.withdrawals);
                
                if (response.stats) {
                    document.getElementById('withdrawalsTotal').textContent = response.stats.totalWithdrawals || 0;
                    document.getElementById('withdrawalsPending').textContent = response.stats.pendingCount || 0;
                    document.getElementById('withdrawalsProcessed').textContent = response.stats.processedCount || 0;
                    document.getElementById('withdrawalsTotalB3C').textContent = this.formatNumber(response.stats.totalB3C || 0, 2);
                }
            } else {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Error al cargar retiros</td></tr>';
            }
        } catch (error) {
            console.error('Error loading withdrawals:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">Error al cargar retiros</td></tr>';
        }
    },
    
    renderWithdrawalsTable(withdrawals) {
        const tbody = document.getElementById('withdrawalsTableBody');
        
        if (!withdrawals || withdrawals.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No se encontraron retiros</td></tr>';
            return;
        }
        
        tbody.innerHTML = withdrawals.map(w => {
            const statusClass = w.status === 'completed' ? 'success' : 
                               (w.status === 'pending' ? 'warning' : 
                               (w.status === 'processing' ? 'info' : 'danger'));
            const statusLabel = w.status === 'completed' ? 'Completado' :
                               (w.status === 'pending' ? 'Pendiente' :
                               (w.status === 'processing' ? 'Procesando' : 
                               (w.status === 'rejected' ? 'Rechazado' : w.status)));
            const destination = w.destination || w.destinationWallet || '';
            const walletShort = destination ? 
                `${destination.slice(0, 8)}...${destination.slice(-6)}` : '-';
            const withdrawalId = w.id || w.withdrawalId;
            const b3cAmount = w.amount || w.b3cAmount || 0;
            const createdAt = w.createdAt || w.created_at;
            
            return `
                <tr>
                    <td><code>${this.escapeHtml(withdrawalId.toString().slice(0, 8))}...</code></td>
                    <td>
                        <div class="user-cell">
                            <span class="username">@${this.escapeHtml(w.username || 'unknown')}</span>
                        </div>
                    </td>
                    <td>${this.formatNumber(b3cAmount, 2)} B3C</td>
                    <td>${this.formatNumber(w.tonAmount || 0, 4)} TON</td>
                    <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    <td>
                        ${destination ? 
                            `<span class="wallet-address" onclick="AdminPanel.copyToClipboard('${destination}')" title="${destination}">${walletShort}</span>` 
                            : '-'}
                    </td>
                    <td>${this.formatDate(createdAt)}</td>
                    <td>
                        <div class="action-btns">
                            <button class="action-btn" onclick="AdminPanel.viewWithdrawal('${withdrawalId}')">Ver</button>
                            ${w.status === 'pending' ? `
                                <button class="action-btn process" onclick="AdminPanel.openProcessWithdrawal('${withdrawalId}')">Procesar</button>
                                <button class="action-btn reject" onclick="AdminPanel.openRejectWithdrawal('${withdrawalId}')">Rechazar</button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },
    
    async viewWithdrawal(withdrawalId) {
        const modal = document.getElementById('withdrawalDetailModal');
        const content = document.getElementById('withdrawalDetailContent');
        
        modal.classList.add('active');
        content.innerHTML = '<div class="loading-spinner">Cargando...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/b3c/withdrawals/${withdrawalId}`);
            
            if (response.success && response.withdrawal) {
                const w = response.withdrawal;
                const statusClass = w.status === 'completed' ? 'success' : 
                                   (w.status === 'pending' ? 'warning' : 
                                   (w.status === 'processing' ? 'info' : 'danger'));
                const statusLabel = w.status === 'completed' ? 'Completado' :
                                   (w.status === 'pending' ? 'Pendiente' :
                                   (w.status === 'processing' ? 'Procesando' : 
                                   (w.status === 'rejected' ? 'Rechazado' : w.status)));
                
                content.innerHTML = `
                    <div class="tx-detail-grid">
                        <div class="tx-detail-header">
                            <div class="tx-type-badge withdrawal">Retiro B3C</div>
                            <span class="status-badge ${statusClass}">${statusLabel}</span>
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Información del Retiro</h4>
                            <div class="detail-row">
                                <span class="detail-label">ID Retiro:</span>
                                <span class="detail-value"><code>${this.escapeHtml(w.withdrawalId || w.id)}</code></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">B3C a Retirar:</span>
                                <span class="detail-value">${(w.b3cAmount || 0).toFixed(2)} B3C</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">TON a Recibir:</span>
                                <span class="detail-value">${(w.tonAmount || 0).toFixed(4)} TON</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Comisión:</span>
                                <span class="detail-value">${(w.commission || 0).toFixed(4)} TON</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Fecha Solicitud:</span>
                                <span class="detail-value">${this.formatDateTime(w.createdAt)}</span>
                            </div>
                            ${w.processedAt ? `
                            <div class="detail-row">
                                <span class="detail-label">Fecha Procesado:</span>
                                <span class="detail-value">${this.formatDateTime(w.processedAt)}</span>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Usuario</h4>
                            <div class="detail-row">
                                <span class="detail-label">Username:</span>
                                <span class="detail-value">@${this.escapeHtml(w.username)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Nombre:</span>
                                <span class="detail-value">${this.escapeHtml(w.userFullName || w.userName || '')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Telegram ID:</span>
                                <span class="detail-value">${w.telegramId || 'N/A'}</span>
                            </div>
                        </div>
                        
                        ${w.destinationWallet ? `
                        <div class="tx-detail-section">
                            <h4>Wallet de Destino</h4>
                            <div class="detail-row">
                                <span class="detail-label">Dirección:</span>
                                <span class="detail-value wallet-full">
                                    <code>${this.escapeHtml(w.destinationWallet)}</code>
                                </span>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${w.txHash ? `
                        <div class="tx-detail-section">
                            <h4>Blockchain</h4>
                            <div class="detail-row">
                                <span class="detail-label">TX Hash:</span>
                                <span class="detail-value tx-hash-full">
                                    <code>${this.escapeHtml(w.txHash)}</code>
                                </span>
                            </div>
                            <div class="detail-actions">
                                <button class="btn-primary btn-sm" onclick="AdminPanel.openTxHash('${w.txHash}')">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                        <polyline points="15 3 21 3 21 9"></polyline>
                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                    </svg>
                                    Ver en TonScan
                                </button>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${w.rejectionReason ? `
                        <div class="tx-detail-section">
                            <h4>Motivo de Rechazo</h4>
                            <div class="detail-row">
                                <span class="detail-value rejection-reason">${this.escapeHtml(w.rejectionReason)}</span>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${w.status === 'pending' ? `
                        <div class="tx-detail-section">
                            <h4>Acciones</h4>
                            <div class="action-buttons-row">
                                <button class="btn-primary" onclick="AdminPanel.openProcessWithdrawal('${w.withdrawalId || w.id}')">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    Procesar Retiro
                                </button>
                                <button class="btn-danger" onclick="AdminPanel.openRejectWithdrawal('${w.withdrawalId || w.id}')">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    Rechazar
                                </button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                content.innerHTML = `<div class="error-state">Error: ${response.error || 'No se pudo cargar el retiro'}</div>`;
            }
        } catch (error) {
            console.error('Error loading withdrawal:', error);
            content.innerHTML = '<div class="error-state">Error al cargar los datos</div>';
        }
    },
    
    openProcessWithdrawal(withdrawalId) {
        const modal = document.getElementById('processWithdrawalModal');
        modal.dataset.withdrawalId = withdrawalId;
        document.getElementById('processWithdrawalTxHash').value = '';
        modal.classList.add('active');
    },
    
    async processWithdrawal() {
        const modal = document.getElementById('processWithdrawalModal');
        const withdrawalId = modal.dataset.withdrawalId;
        const txHash = document.getElementById('processWithdrawalTxHash').value.trim();
        
        if (!txHash) {
            this.showToast('Ingresa el hash de la transacción', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/b3c/withdrawals/${withdrawalId}/process`, {
                method: 'POST',
                body: JSON.stringify({ txHash: txHash, action: 'complete' })
            });
            
            if (response.success) {
                this.showToast(response.message || 'Retiro procesado correctamente', 'success');
                document.getElementById('processWithdrawalModal').classList.remove('active');
                document.getElementById('withdrawalDetailModal').classList.remove('active');
                this.loadWithdrawals();
            } else {
                this.showToast(response.error || 'Error al procesar el retiro', 'error');
            }
        } catch (error) {
            console.error('Error processing withdrawal:', error);
            this.showToast('Error al procesar el retiro', 'error');
        }
    },
    
    openRejectWithdrawal(withdrawalId) {
        const modal = document.getElementById('rejectWithdrawalModal');
        modal.dataset.withdrawalId = withdrawalId;
        document.getElementById('rejectWithdrawalReason').value = '';
        modal.classList.add('active');
    },
    
    async rejectWithdrawal() {
        const modal = document.getElementById('rejectWithdrawalModal');
        const withdrawalId = modal.dataset.withdrawalId;
        const reason = document.getElementById('rejectWithdrawalReason').value.trim();
        
        if (!reason) {
            this.showToast('Ingresa el motivo del rechazo', 'error');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/b3c/withdrawals/${withdrawalId}/process`, {
                method: 'POST',
                body: JSON.stringify({ action: 'reject', reason: reason })
            });
            
            if (response.success) {
                this.showToast(response.message || 'Retiro rechazado', 'success');
                document.getElementById('rejectWithdrawalModal').classList.remove('active');
                document.getElementById('withdrawalDetailModal').classList.remove('active');
                this.loadWithdrawals();
            } else {
                this.showToast(response.error || 'Error al rechazar el retiro', 'error');
            }
        } catch (error) {
            console.error('Error rejecting withdrawal:', error);
            this.showToast('Error al rechazar el retiro', 'error');
        }
    },
    
    async loadP2PTransfers() {
        const tbody = document.getElementById('p2pTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Cargando transferencias...</td></tr>';
        
        try {
            const filter = document.getElementById('p2pFilter')?.value || '';
            const search = document.getElementById('p2pSearch')?.value || '';
            const response = await this.fetchAPI(`/api/admin/transfers?filter=${filter}&search=${encodeURIComponent(search)}`);
            
            if (response.success) {
                this.renderP2PTable(response.transfers);
                
                if (response.stats) {
                    document.getElementById('p2pTotal').textContent = response.stats.totalTransfers || 0;
                    document.getElementById('p2pToday').textContent = response.stats.todayCount || 0;
                    document.getElementById('p2pSuspicious').textContent = response.stats.suspiciousCount || 0;
                    document.getElementById('p2pTotalB3C').textContent = this.formatNumber(response.stats.totalB3C || 0, 2);
                }
            } else {
                tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Error al cargar transferencias</td></tr>';
            }
        } catch (error) {
            console.error('Error loading P2P transfers:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Error al cargar transferencias</td></tr>';
        }
    },
    
    renderP2PTable(transfers) {
        const tbody = document.getElementById('p2pTableBody');
        
        if (!transfers || transfers.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="7">No se encontraron transferencias</td></tr>';
            return;
        }
        
        tbody.innerHTML = transfers.map(t => {
            const isSuspicious = t.isSuspicious || t.is_suspicious;
            const suspiciousClass = isSuspicious ? 'suspicious' : '';
            
            return `
                <tr class="${suspiciousClass}">
                    <td><code>${this.escapeHtml((t.transferId || t.id).toString().slice(0, 8))}...</code></td>
                    <td>
                        <div class="user-cell">
                            <span class="username">@${this.escapeHtml(t.fromUsername)}</span>
                        </div>
                    </td>
                    <td>
                        <div class="user-cell">
                            <span class="username">@${this.escapeHtml(t.toUsername)}</span>
                        </div>
                    </td>
                    <td>${this.formatNumber(t.amount, 2)} B3C</td>
                    <td>
                        ${isSuspicious ? 
                            `<span class="status-badge danger" title="${this.escapeHtml(t.suspiciousReason || 'Actividad sospechosa')}">Sospechoso</span>` 
                            : '<span class="status-badge success">Normal</span>'}
                    </td>
                    <td>${this.formatDateTime(t.createdAt)}</td>
                    <td>
                        <div class="action-btns">
                            <button class="action-btn" onclick="AdminPanel.viewP2PTransfer('${t.transferId || t.id}')">Ver</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },
    
    async viewP2PTransfer(transferId) {
        const modal = document.getElementById('p2pDetailModal');
        const content = document.getElementById('p2pDetailContent');
        
        if (!modal) {
            this.showToast('Modal no disponible', 'error');
            return;
        }
        
        modal.classList.add('active');
        content.innerHTML = '<div class="loading-spinner">Cargando...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/transfers/${transferId}`);
            
            if (response.success && response.transfer) {
                const t = response.transfer;
                const isSuspicious = t.isSuspicious || t.is_suspicious;
                
                content.innerHTML = `
                    <div class="tx-detail-grid">
                        <div class="tx-detail-header">
                            <div class="tx-type-badge transfer">Transferencia P2P</div>
                            ${isSuspicious ? 
                                '<span class="status-badge danger">Sospechoso</span>' 
                                : '<span class="status-badge success">Normal</span>'}
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Información de la Transferencia</h4>
                            <div class="detail-row">
                                <span class="detail-label">ID Transferencia:</span>
                                <span class="detail-value"><code>${this.escapeHtml(t.transferId || t.id)}</code></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Monto:</span>
                                <span class="detail-value">${(t.amount || 0).toFixed(2)} B3C</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Fecha:</span>
                                <span class="detail-value">${this.formatDateTime(t.createdAt)}</span>
                            </div>
                            ${t.note ? `
                            <div class="detail-row">
                                <span class="detail-label">Nota:</span>
                                <span class="detail-value">${this.escapeHtml(t.note)}</span>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Remitente</h4>
                            <div class="detail-row">
                                <span class="detail-label">Username:</span>
                                <span class="detail-value">@${this.escapeHtml(t.fromUsername)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Nombre:</span>
                                <span class="detail-value">${this.escapeHtml(t.fromUserName || '')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Telegram ID:</span>
                                <span class="detail-value">${t.fromTelegramId || 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="tx-detail-section">
                            <h4>Destinatario</h4>
                            <div class="detail-row">
                                <span class="detail-label">Username:</span>
                                <span class="detail-value">@${this.escapeHtml(t.toUsername)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Nombre:</span>
                                <span class="detail-value">${this.escapeHtml(t.toUserName || '')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Telegram ID:</span>
                                <span class="detail-value">${t.toTelegramId || 'N/A'}</span>
                            </div>
                        </div>
                        
                        ${isSuspicious ? `
                        <div class="tx-detail-section suspicious-section">
                            <h4>Alerta de Actividad Sospechosa</h4>
                            <div class="detail-row">
                                <span class="detail-value suspicious-reason">${this.escapeHtml(t.suspiciousReason || 'Detectada actividad inusual en esta transferencia')}</span>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                content.innerHTML = `<div class="error-state">Error: ${response.error || 'No se pudo cargar la transferencia'}</div>`;
            }
        } catch (error) {
            console.error('Error loading P2P transfer:', error);
            content.innerHTML = '<div class="error-state">Error al cargar los datos</div>';
        }
    },
    
    openTxHash(txHash) {
        if (txHash) {
            window.open(`https://tonscan.org/tx/${txHash}`, '_blank');
        }
    },
    
    async loadPeriodStats() {
        const fromDate = document.getElementById('periodDateFrom')?.value;
        const toDate = document.getElementById('periodDateTo')?.value;
        
        if (!fromDate || !toDate) {
            this.showToast('Selecciona un rango de fechas', 'warning');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/financial/period-stats?from=${fromDate}&to=${toDate}`);
            
            if (response.success && response.data) {
                const data = response.data;
                
                document.getElementById('periodTxCount').textContent = this.formatNumber(data.totalTransactions || 0);
                document.getElementById('periodB3CVolume').textContent = this.formatNumber(data.totalB3CVolume || 0, 2);
                document.getElementById('periodPurchases').textContent = this.formatNumber(data.purchases?.count || 0);
                document.getElementById('periodPurchasesTon').textContent = `${this.formatNumber(data.purchases?.tonAmount || 0, 4)} TON`;
                document.getElementById('periodWithdrawals').textContent = this.formatNumber(data.withdrawals?.count || 0);
                document.getElementById('periodWithdrawalsB3C').textContent = `${this.formatNumber(data.withdrawals?.b3cAmount || 0, 2)} B3C`;
                document.getElementById('periodTransfers').textContent = this.formatNumber(data.transfers?.count || 0);
                document.getElementById('periodTransfersB3C').textContent = `${this.formatNumber(data.transfers?.b3cAmount || 0, 2)} B3C`;
                document.getElementById('periodCommissions').textContent = this.formatNumber(data.totalCommissions || 0, 4);
                
                this.initPeriodCharts(data);
                
                this.showToast('Estadísticas cargadas', 'success');
            } else {
                this.showToast(response.error || 'Error al cargar estadísticas', 'error');
            }
        } catch (error) {
            console.error('Error loading period stats:', error);
            this.showToast('Error al cargar estadísticas', 'error');
        }
    },
    
    initPeriodCharts(data) {
        const volumeCtx = document.getElementById('periodVolumeChart');
        const typeCtx = document.getElementById('periodTypeChart');
        
        if (volumeCtx && data.dailyVolume) {
            if (this.charts.periodVolume) {
                this.charts.periodVolume.destroy();
            }
            
            const labels = data.dailyVolume.map(d => d.date);
            const values = data.dailyVolume.map(d => d.volume);
            
            this.charts.periodVolume = new Chart(volumeCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Volumen B3C',
                        data: values,
                        backgroundColor: 'rgba(240, 185, 11, 0.6)',
                        borderColor: '#F0B90B',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#848E9C', maxRotation: 45 }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#848E9C' }
                        }
                    }
                }
            });
        }
        
        if (typeCtx && data.byType) {
            if (this.charts.periodType) {
                this.charts.periodType.destroy();
            }
            
            const typeLabels = {
                purchases: 'Compras',
                withdrawals: 'Retiros',
                transfers: 'Transferencias'
            };
            
            const labels = Object.keys(data.byType).map(k => typeLabels[k] || k);
            const values = Object.values(data.byType);
            const colors = ['#F0B90B', '#e74c3c', '#3498db', '#27ae60'];
            
            this.charts.periodType = new Chart(typeCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors.slice(0, values.length),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#EAECEF' }
                        }
                    }
                }
            });
        }
    },
    
    async exportPeriodCSV() {
        const fromDate = document.getElementById('periodDateFrom')?.value;
        const toDate = document.getElementById('periodDateTo')?.value;
        
        if (!fromDate || !toDate) {
            this.showToast('Selecciona un rango de fechas', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/financial/period-stats/export?from=${fromDate}&to=${toDate}&format=csv`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transacciones_${fromDate}_${toDate}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.showToast('CSV exportado correctamente', 'success');
            } else {
                this.showToast('Error al exportar CSV', 'error');
            }
        } catch (error) {
            console.error('Error exporting CSV:', error);
            this.showToast('Error al exportar CSV', 'error');
        }
    },
    
    async exportPeriodReport() {
        const fromDate = document.getElementById('periodDateFrom')?.value;
        const toDate = document.getElementById('periodDateTo')?.value;
        
        if (!fromDate || !toDate) {
            this.showToast('Selecciona un rango de fechas', 'warning');
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/financial/period-stats?from=${fromDate}&to=${toDate}`);
            
            if (response.success && response.data) {
                const data = response.data;
                
                const reportContent = `
REPORTE DE TRANSACCIONES - BUNK3R
================================
Período: ${fromDate} a ${toDate}
Generado: ${new Date().toLocaleString('es-ES')}

RESUMEN GENERAL
---------------
Total de transacciones: ${data.totalTransactions || 0}
Volumen total B3C: ${(data.totalB3CVolume || 0).toFixed(2)} B3C
Comisiones generadas: ${(data.totalCommissions || 0).toFixed(4)} TON

COMPRAS B3C
-----------
Cantidad: ${data.purchases?.count || 0}
Monto TON recibido: ${(data.purchases?.tonAmount || 0).toFixed(4)} TON
B3C entregados: ${(data.purchases?.b3cAmount || 0).toFixed(2)} B3C

RETIROS
-------
Cantidad: ${data.withdrawals?.count || 0}
B3C retirados: ${(data.withdrawals?.b3cAmount || 0).toFixed(2)} B3C
Pendientes: ${data.withdrawals?.pending || 0}
Completados: ${data.withdrawals?.completed || 0}

TRANSFERENCIAS P2P
------------------
Cantidad: ${data.transfers?.count || 0}
Volumen: ${(data.transfers?.b3cAmount || 0).toFixed(2)} B3C

================================
Fin del reporte
                `.trim();
                
                const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `reporte_${fromDate}_${toDate}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.showToast('Reporte generado correctamente', 'success');
            } else {
                this.showToast('Error al generar reporte', 'error');
            }
        } catch (error) {
            console.error('Error generating report:', error);
            this.showToast('Error al generar reporte', 'error');
        }
    },
    
    vnPage: 1,
    vnPerPage: 20,
    vnListenersInitialized: false,
    vnTotalOrders: 0,
    
    async loadVirtualNumbers() {
        try {
            const [stats, orders] = await Promise.all([
                this.fetchAPI('/api/admin/vn/stats'),
                this.fetchAPI(`/api/admin/vn/orders?page=${this.vnPage}&per_page=${this.vnPerPage}`)
            ]);
            
            if (stats.success && stats.data) {
                document.getElementById('vnTotalPurchases').textContent = this.formatNumber(stats.data.total_purchases || 0);
                document.getElementById('vnTotalRevenue').textContent = this.formatNumber(stats.data.total_revenue || 0);
                document.getElementById('vnActiveNumbers').textContent = this.formatNumber(stats.data.active_numbers || 0);
                document.getElementById('smsPoolBalance').textContent = '$' + this.formatNumber(stats.data.smspool_balance || 0, 2);
                document.getElementById('smsPoolBalanceDisplay').textContent = '$' + this.formatNumber(stats.data.smspool_balance || 0, 2);
                
                if (stats.data.smspool_balance < 10) {
                    document.getElementById('smsPoolAlert').style.display = 'flex';
                } else {
                    document.getElementById('smsPoolAlert').style.display = 'none';
                }
                
                this.renderVNTopServices(stats.data.top_services || []);
                this.renderVNTopCountries(stats.data.top_countries || []);
                this.populateVNServiceFilter(stats.data.top_services || []);
            }
            
            if (orders.success) {
                this.vnTotalOrders = orders.total || orders.data?.length || 0;
                this.renderVNOrders(orders.data || []);
            }
            
            if (!this.vnListenersInitialized) {
                this.setupVNEventListeners();
                this.vnListenersInitialized = true;
            }
            
        } catch (error) {
            console.error('Error loading virtual numbers:', error);
            this.showToast('Error al cargar números virtuales', 'error');
        }
    },
    
    populateVNServiceFilter(services) {
        const select = document.getElementById('vnServiceFilter');
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Todos los servicios</option>';
        
        services.forEach(service => {
            const name = service.name || service.service;
            if (name) {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            }
        });
        
        if (currentValue) {
            select.value = currentValue;
        }
    },
    
    setupVNEventListeners() {
        document.getElementById('refreshVNBtn')?.addEventListener('click', () => {
            this.loadVirtualNumbers();
        });
        
        document.getElementById('vnStatusFilter')?.addEventListener('change', () => {
            this.vnPage = 1;
            this.loadVNOrders();
        });
        
        document.getElementById('vnServiceFilter')?.addEventListener('change', () => {
            this.vnPage = 1;
            this.loadVNOrders();
        });
        
        document.getElementById('vnPrevBtn')?.addEventListener('click', () => {
            if (this.vnPage > 1) {
                this.vnPage--;
                this.loadVNOrders();
            }
        });
        
        document.getElementById('vnNextBtn')?.addEventListener('click', () => {
            if (!document.getElementById('vnNextBtn').disabled) {
                this.vnPage++;
                this.loadVNOrders();
            }
        });
    },
    
    botsListenersInitialized: false,
    botsPurchasePage: 1,
    botsPurchasePerPage: 10,
    
    async loadBots() {
        try {
            const period = document.getElementById('botsChartPeriod')?.value || '30';
            
            const [botsRes, statsRes, usageRes, revenueRes] = await Promise.all([
                this.fetchAPI('/api/admin/bots'),
                this.fetchAPI('/api/admin/bots/stats'),
                this.fetchAPI(`/api/admin/bots/usage?days=${period}`),
                this.fetchAPI('/api/admin/bots/revenue')
            ]);
            
            if (statsRes.success && statsRes.summary) {
                document.getElementById('botsTotalCount').textContent = this.formatNumber(statsRes.summary.totalBots || 0);
                document.getElementById('botsActiveCount').textContent = this.formatNumber(statsRes.summary.activeBots || 0);
                document.getElementById('botsUsersCount').textContent = this.formatNumber(statsRes.summary.totalUsersUsingBots || 0);
                
                const totalRevenue = (statsRes.botStats || []).reduce((sum, bot) => sum + (bot.total_revenue || 0), 0);
                document.getElementById('botsTotalRevenue').textContent = this.formatNumber(totalRevenue);
                
                this.renderBotStats(statsRes.botStats || []);
            }
            
            if (botsRes.success) {
                this.renderBotsTable(botsRes.bots || []);
            }
            
            if (usageRes.success) {
                this.initBotsUsageChart(usageRes.data || []);
            }
            
            if (revenueRes.success) {
                this.renderBotsRevenue(revenueRes.data || {});
            }
            
            this.loadBotsPurchaseHistory();
            
            if (!this.botsListenersInitialized) {
                this.setupBotsEventListeners();
                this.botsListenersInitialized = true;
            }
            
        } catch (error) {
            console.error('Error loading bots:', error);
            this.showToast('Error al cargar bots', 'error');
        }
    },
    
    initBotsUsageChart(usageData) {
        const ctx = document.getElementById('botsUsageChart');
        if (!ctx) return;
        
        const labels = usageData.map(d => d.date);
        const data = usageData.map(d => d.count);
        
        if (this.charts.botsUsage) {
            this.charts.botsUsage.data.labels = labels;
            this.charts.botsUsage.data.datasets[0].data = data;
            this.charts.botsUsage.update();
        } else {
            this.charts.botsUsage = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Activaciones de Bots',
                        data: data,
                        borderColor: '#8B5CF6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#8B5CF6'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#848E9C', maxTicksLimit: 10 }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#848E9C' },
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    },
    
    renderBotsRevenue(revenueData) {
        document.getElementById('botsRevenueTotal').textContent = this.formatNumber(revenueData.total || 0) + ' B3C';
        document.getElementById('botsRevenueMonth').textContent = this.formatNumber(revenueData.month || 0) + ' B3C';
        document.getElementById('botsRevenueWeek').textContent = this.formatNumber(revenueData.week || 0) + ' B3C';
        
        const breakdown = revenueData.breakdown || [];
        const container = document.getElementById('botsRevenueBreakdown');
        
        if (!breakdown || breakdown.length === 0) {
            container.innerHTML = '<div class="empty-state">No hay datos de ingresos por bot</div>';
            return;
        }
        
        container.innerHTML = breakdown.map(bot => `
            <div class="revenue-breakdown-item">
                <div class="revenue-breakdown-icon">${this.escapeHtml(bot.icon || '🤖')}</div>
                <div class="revenue-breakdown-info">
                    <div class="revenue-breakdown-name">${this.escapeHtml(bot.name || '-')}</div>
                    <div class="revenue-breakdown-amount">${this.formatNumber(bot.revenue || 0)} B3C</div>
                    <div class="revenue-breakdown-count">${this.formatNumber(bot.count || 0)} compras</div>
                </div>
            </div>
        `).join('');
    },
    
    async loadBotsPurchaseHistory() {
        try {
            const response = await this.fetchAPI(`/api/admin/bots/purchases?page=${this.botsPurchasePage}&per_page=${this.botsPurchasePerPage}`);
            
            if (response.success) {
                this.renderBotsPurchaseHistory(response.data || [], response.total || 0);
            }
        } catch (error) {
            console.error('Error loading purchase history:', error);
        }
    },
    
    renderBotsPurchaseHistory(purchases, total) {
        const tbody = document.getElementById('botsPurchaseHistoryBody');
        const pageInfo = document.getElementById('botsPurchasePageInfo');
        const prevBtn = document.getElementById('botsPurchasePrevBtn');
        const nextBtn = document.getElementById('botsPurchaseNextBtn');
        
        if (!tbody) return;
        
        if (!purchases || purchases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">No hay compras de bots registradas</td></tr>';
            if (prevBtn) prevBtn.disabled = true;
            if (nextBtn) nextBtn.disabled = true;
            if (pageInfo) pageInfo.textContent = 'Sin resultados';
            return;
        }
        
        tbody.innerHTML = purchases.map(p => `
            <tr>
                <td>${this.formatDate(p.created_at)}</td>
                <td>${this.escapeHtml(p.username || p.user_id || '-')}</td>
                <td>
                    <span class="bot-purchase-name">
                        ${this.escapeHtml(p.icon || '🤖')} ${this.escapeHtml(p.bot_name || '-')}
                    </span>
                </td>
                <td class="price-cell">${this.formatNumber(p.price || 0)} B3C</td>
            </tr>
        `).join('');
        
        const totalPages = Math.ceil(total / this.botsPurchasePerPage) || 1;
        if (pageInfo) pageInfo.textContent = `Pagina ${this.botsPurchasePage} de ${totalPages}`;
        if (prevBtn) prevBtn.disabled = this.botsPurchasePage <= 1;
        if (nextBtn) nextBtn.disabled = this.botsPurchasePage >= totalPages;
    },
    
    renderBotsTable(bots) {
        const tbody = document.getElementById('botsTableBody');
        if (!tbody) return;
        
        const filter = document.getElementById('botStatusFilter')?.value || '';
        let filteredBots = bots;
        
        if (filter === 'active') {
            filteredBots = bots.filter(b => b.is_available);
        } else if (filter === 'inactive') {
            filteredBots = bots.filter(b => !b.is_available);
        }
        
        if (filteredBots.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-cell">No hay bots registrados</td></tr>';
            return;
        }
        
        tbody.innerHTML = filteredBots.map(bot => `
            <tr data-bot-id="${bot.id}">
                <td>${bot.id}</td>
                <td class="bot-icon">${this.escapeHtml(bot.icon || '🤖')}</td>
                <td class="bot-name">${this.escapeHtml(bot.bot_name || '-')}</td>
                <td>${this.escapeHtml(bot.bot_type || '-')}</td>
                <td class="description-cell" title="${this.escapeHtml(bot.description || '')}">${this.escapeHtml(this.truncate(bot.description || '-', 40))}</td>
                <td class="price-cell">${this.formatNumber(bot.price || 0)} B3C</td>
                <td class="users-cell">${this.formatNumber(bot.users_count || 0)}</td>
                <td>
                    <span class="status-badge ${bot.is_available ? 'active' : 'inactive'}">
                        ${bot.is_available ? 'Activo' : 'Inactivo'}
                    </span>
                </td>
                <td class="actions-cell">
                    <button class="action-btn toggle-btn" data-bot-id="${bot.id}" title="${bot.is_available ? 'Desactivar' : 'Activar'}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${bot.is_available ? 
                                '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line>' :
                                '<circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line>'}
                        </svg>
                    </button>
                    <button class="action-btn edit-btn" data-bot-id="${bot.id}" title="Editar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="action-btn delete-btn danger" data-bot-id="${bot.id}" title="Eliminar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');
        
        tbody.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => this.toggleBot(btn.dataset.botId));
        });
        
        tbody.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', () => this.showEditBotModal(btn.dataset.botId));
        });
        
        tbody.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => this.deleteBot(btn.dataset.botId));
        });
    },
    
    renderBotStats(botStats) {
        const container = document.getElementById('botStatsContainer');
        if (!container) return;
        
        if (botStats.length === 0) {
            container.innerHTML = '<div class="empty-state">No hay estadísticas disponibles</div>';
            return;
        }
        
        container.innerHTML = `
            <div class="bot-stats-list">
                ${botStats.map(bot => `
                    <div class="bot-stat-item">
                        <div class="bot-stat-icon">${this.escapeHtml(bot.icon || '🤖')}</div>
                        <div class="bot-stat-info">
                            <span class="bot-stat-name">${this.escapeHtml(bot.bot_name || '-')}</span>
                            <div class="bot-stat-details">
                                <span class="stat-detail"><strong>${this.formatNumber(bot.total_users || 0)}</strong> usuarios</span>
                                <span class="stat-detail"><strong>${this.formatNumber(bot.active_users || 0)}</strong> activos</span>
                                <span class="stat-detail"><strong>${this.formatNumber(bot.total_revenue || 0)}</strong> B3C</span>
                            </div>
                        </div>
                        <span class="status-badge ${bot.is_available ? 'active' : 'inactive'}">${bot.is_available ? 'Activo' : 'Inactivo'}</span>
                    </div>
                `).join('')}
            </div>
        `;
    },
    
    setupBotsEventListeners() {
        document.getElementById('refreshBotsBtn')?.addEventListener('click', () => {
            this.loadBots();
        });
        
        document.getElementById('botStatusFilter')?.addEventListener('change', () => {
            this.loadBots();
        });
        
        document.getElementById('createBotBtn')?.addEventListener('click', () => {
            this.showCreateBotModal();
        });
        
        document.getElementById('botsChartPeriod')?.addEventListener('change', () => {
            this.loadBots();
        });
        
        document.getElementById('botsPurchasePrevBtn')?.addEventListener('click', () => {
            if (this.botsPurchasePage > 1) {
                this.botsPurchasePage--;
                this.loadBotsPurchaseHistory();
            }
        });
        
        document.getElementById('botsPurchaseNextBtn')?.addEventListener('click', () => {
            this.botsPurchasePage++;
            this.loadBotsPurchaseHistory();
        });
    },
    
    showCreateBotModal() {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.id = 'createBotModal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Crear Nuevo Bot</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Nombre del Bot</label>
                        <input type="text" id="newBotName" placeholder="Ej: Bot de Trading">
                    </div>
                    <div class="form-group">
                        <label>Tipo</label>
                        <input type="text" id="newBotType" placeholder="Ej: trading" value="general">
                    </div>
                    <div class="form-group">
                        <label>Descripción</label>
                        <textarea id="newBotDescription" rows="3" placeholder="Descripción del bot..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Icono (emoji)</label>
                        <input type="text" id="newBotIcon" placeholder="🤖" value="🤖" maxlength="4">
                    </div>
                    <div class="form-group">
                        <label>Precio (B3C)</label>
                        <input type="number" id="newBotPrice" placeholder="0" value="0" min="0">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary modal-cancel">Cancelar</button>
                    <button class="btn-primary" id="confirmCreateBot">Crear Bot</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
        modal.querySelector('.modal-overlay').addEventListener('click', () => modal.remove());
        modal.querySelector('.modal-cancel').addEventListener('click', () => modal.remove());
        
        modal.querySelector('#confirmCreateBot').addEventListener('click', async () => {
            const name = document.getElementById('newBotName').value.trim();
            const type = document.getElementById('newBotType').value.trim() || 'general';
            const description = document.getElementById('newBotDescription').value.trim();
            const icon = document.getElementById('newBotIcon').value.trim() || '🤖';
            const price = parseInt(document.getElementById('newBotPrice').value) || 0;
            
            if (!name) {
                this.showToast('El nombre es requerido', 'error');
                return;
            }
            
            try {
                const response = await this.fetchAPI('/api/admin/bots', {
                    method: 'POST',
                    body: JSON.stringify({ name, type, description, icon, price })
                });
                
                if (response.success) {
                    this.showToast('Bot creado correctamente', 'success');
                    modal.remove();
                    this.loadBots();
                } else {
                    this.showToast(response.error || 'Error al crear bot', 'error');
                }
            } catch (error) {
                console.error('Error creating bot:', error);
                this.showToast('Error al crear bot', 'error');
            }
        });
    },
    
    async showEditBotModal(botId) {
        try {
            const response = await this.fetchAPI('/api/admin/bots');
            if (!response.success) {
                this.showToast('Error al cargar datos del bot', 'error');
                return;
            }
            
            const bot = response.bots.find(b => b.id == botId);
            if (!bot) {
                this.showToast('Bot no encontrado', 'error');
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.id = 'editBotModal';
            modal.innerHTML = `
                <div class="modal-overlay"></div>
                <div class="modal-content" style="max-width: 600px;">
                    <div class="modal-header">
                        <h3>${this.escapeHtml(bot.icon || '🤖')} ${this.escapeHtml(bot.bot_name)}</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="bot-modal-tabs">
                            <button class="bot-modal-tab active" data-tab="config">Configuración</button>
                            <button class="bot-modal-tab" data-tab="logs">Logs de Actividad</button>
                        </div>
                        
                        <div class="bot-modal-panel active" id="botConfigPanel">
                            <div class="form-group">
                                <label>Nombre del Bot</label>
                                <input type="text" id="editBotName" value="${this.escapeHtml(bot.bot_name || '')}">
                            </div>
                            <div class="form-group">
                                <label>Descripción</label>
                                <textarea id="editBotDescription" rows="3">${this.escapeHtml(bot.description || '')}</textarea>
                            </div>
                            <div class="form-group">
                                <label>Icono (emoji)</label>
                                <input type="text" id="editBotIcon" value="${this.escapeHtml(bot.icon || '🤖')}" maxlength="4">
                            </div>
                            <div class="form-group">
                                <label>Precio (B3C)</label>
                                <input type="number" id="editBotPrice" value="${bot.price || 0}" min="0">
                            </div>
                        </div>
                        
                        <div class="bot-modal-panel" id="botLogsPanel">
                            <div class="bot-logs-stats">
                                <div class="bot-log-stat">
                                    <span class="bot-log-stat-value" id="botLogsTotalUsers">-</span>
                                    <span class="bot-log-stat-label">Total Usuarios</span>
                                </div>
                                <div class="bot-log-stat">
                                    <span class="bot-log-stat-value" id="botLogsActiveUsers">-</span>
                                    <span class="bot-log-stat-label">Activos</span>
                                </div>
                                <div class="bot-log-stat">
                                    <span class="bot-log-stat-value" id="botLogsTodayUsers">-</span>
                                    <span class="bot-log-stat-label">Hoy</span>
                                </div>
                            </div>
                            <div class="bot-logs-list" id="botLogsList">
                                <div class="bot-logs-empty">Cargando logs...</div>
                            </div>
                            <div class="bot-logs-pagination" id="botLogsPagination" style="display: none;">
                                <button id="botLogsPrev" disabled>Anterior</button>
                                <span id="botLogsPageInfo">1 / 1</span>
                                <button id="botLogsNext" disabled>Siguiente</button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary modal-cancel">Cancelar</button>
                        <button class="btn-primary" id="confirmEditBot">Guardar Cambios</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            let botLogsPage = 1;
            const botLogsPerPage = 20;
            let botLogsTotal = 0;
            
            modal.querySelectorAll('.bot-modal-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    modal.querySelectorAll('.bot-modal-tab').forEach(t => t.classList.remove('active'));
                    modal.querySelectorAll('.bot-modal-panel').forEach(p => p.classList.remove('active'));
                    tab.classList.add('active');
                    const tabName = tab.dataset.tab;
                    if (tabName === 'config') {
                        modal.querySelector('#botConfigPanel').classList.add('active');
                    } else if (tabName === 'logs') {
                        modal.querySelector('#botLogsPanel').classList.add('active');
                        loadBotLogs();
                    }
                });
            });
            
            const loadBotLogs = async () => {
                try {
                    const logsResponse = await this.fetchAPI(`/api/admin/bots/${botId}/logs?page=${botLogsPage}&per_page=${botLogsPerPage}`);
                    if (logsResponse.success) {
                        botLogsTotal = logsResponse.total || 0;
                        const activeCount = logsResponse.active_count || 0;
                        const todayCount = logsResponse.today_count || 0;
                        
                        document.getElementById('botLogsTotalUsers').textContent = botLogsTotal;
                        document.getElementById('botLogsActiveUsers').textContent = activeCount;
                        document.getElementById('botLogsTodayUsers').textContent = todayCount;
                        
                        this.renderBotLogs(logsResponse.data || []);
                        
                        const totalPages = Math.ceil(botLogsTotal / botLogsPerPage) || 1;
                        document.getElementById('botLogsPageInfo').textContent = `${botLogsPage} / ${totalPages}`;
                        document.getElementById('botLogsPrev').disabled = botLogsPage <= 1;
                        document.getElementById('botLogsNext').disabled = botLogsPage >= totalPages;
                        
                        if (botLogsTotal > botLogsPerPage) {
                            document.getElementById('botLogsPagination').style.display = 'flex';
                        }
                    }
                } catch (error) {
                    console.error('Error loading bot logs:', error);
                    document.getElementById('botLogsList').innerHTML = '<div class="bot-logs-empty">Error al cargar logs</div>';
                }
            };
            
            modal.querySelector('#botLogsPrev')?.addEventListener('click', () => {
                if (botLogsPage > 1) {
                    botLogsPage--;
                    loadBotLogs();
                }
            });
            
            modal.querySelector('#botLogsNext')?.addEventListener('click', () => {
                const totalPages = Math.ceil(botLogsTotal / botLogsPerPage);
                if (botLogsPage < totalPages) {
                    botLogsPage++;
                    loadBotLogs();
                }
            });
            
            modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
            modal.querySelector('.modal-overlay').addEventListener('click', () => modal.remove());
            modal.querySelector('.modal-cancel').addEventListener('click', () => modal.remove());
            
            modal.querySelector('#confirmEditBot').addEventListener('click', async () => {
                const name = document.getElementById('editBotName').value.trim();
                const description = document.getElementById('editBotDescription').value.trim();
                const icon = document.getElementById('editBotIcon').value.trim() || '🤖';
                const price = parseInt(document.getElementById('editBotPrice').value) || 0;
                
                if (!name) {
                    this.showToast('El nombre es requerido', 'error');
                    return;
                }
                
                try {
                    const response = await this.fetchAPI(`/api/admin/bots/${botId}`, {
                        method: 'PUT',
                        body: JSON.stringify({ name, description, icon, price })
                    });
                    
                    if (response.success) {
                        this.showToast('Bot actualizado correctamente', 'success');
                        modal.remove();
                        this.loadBots();
                    } else {
                        this.showToast(response.error || 'Error al actualizar bot', 'error');
                    }
                } catch (error) {
                    console.error('Error updating bot:', error);
                    this.showToast('Error al actualizar bot', 'error');
                }
            });
        } catch (error) {
            console.error('Error loading bot for edit:', error);
            this.showToast('Error al cargar datos del bot', 'error');
        }
    },
    
    renderBotLogs(logs) {
        const container = document.getElementById('botLogsList');
        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="bot-logs-empty">No hay logs de actividad para este bot</div>';
            return;
        }
        
        container.innerHTML = logs.map(log => {
            const username = log.username || log.first_name || `Usuario ${log.user_id}`;
            const isActive = log.is_active;
            const iconClass = isActive ? 'active' : 'inactive';
            const statusClass = isActive ? 'active' : 'inactive';
            const statusText = isActive ? 'Activo' : 'Inactivo';
            const icon = log.icon || '🤖';
            
            return `
                <div class="bot-log-item">
                    <div class="bot-log-icon ${iconClass}">${icon}</div>
                    <div class="bot-log-content">
                        <div class="bot-log-user">@${this.escapeHtml(username)}</div>
                        <div class="bot-log-action">Adquirió el bot</div>
                    </div>
                    <span class="bot-log-status ${statusClass}">${statusText}</span>
                    <div class="bot-log-time">${this.timeAgo(log.created_at)}</div>
                </div>
            `;
        }).join('');
    },
    
    async toggleBot(botId) {
        try {
            const response = await this.fetchAPI(`/api/admin/bots/${botId}/toggle`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast(response.message || 'Estado actualizado', 'success');
                this.loadBots();
            } else {
                this.showToast(response.error || 'Error al cambiar estado', 'error');
            }
        } catch (error) {
            console.error('Error toggling bot:', error);
            this.showToast('Error al cambiar estado del bot', 'error');
        }
    },
    
    async deleteBot(botId) {
        if (!confirm('¿Estás seguro de eliminar este bot? Esta acción no se puede deshacer.')) {
            return;
        }
        
        try {
            const response = await this.fetchAPI(`/api/admin/bots/${botId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Bot eliminado correctamente', 'success');
                this.loadBots();
            } else {
                this.showToast(response.error || 'Error al eliminar bot', 'error');
            }
        } catch (error) {
            console.error('Error deleting bot:', error);
            this.showToast('Error al eliminar bot', 'error');
        }
    },
    
    truncate(str, maxLength) {
        if (!str || str.length <= maxLength) return str;
        return str.substring(0, maxLength) + '...';
    },
    
    async loadVNOrders() {
        const status = document.getElementById('vnStatusFilter')?.value || '';
        const service = document.getElementById('vnServiceFilter')?.value || '';
        
        try {
            const response = await this.fetchAPI(`/api/admin/vn/orders?page=${this.vnPage}&per_page=${this.vnPerPage}&status=${status}&service=${service}`);
            
            if (response.success) {
                this.vnTotalOrders = response.total || response.data?.length || 0;
                this.renderVNOrders(response.data || []);
            }
        } catch (error) {
            console.error('Error loading VN orders:', error);
        }
    },
    
    renderVNTopServices(services) {
        const container = document.getElementById('vnTopServices');
        if (!services || services.length === 0) {
            container.innerHTML = '<div class="empty-state">Sin datos de servicios</div>';
            return;
        }
        
        container.innerHTML = services.slice(0, 5).map(service => `
            <div class="service-item">
                <span class="service-name">${this.escapeHtml(service.name || service.service)}</span>
                <span class="service-count">${service.count || 0}</span>
            </div>
        `).join('');
    },
    
    renderVNTopCountries(countries) {
        const container = document.getElementById('vnTopCountries');
        if (!countries || countries.length === 0) {
            container.innerHTML = '<div class="empty-state">Sin datos de países</div>';
            return;
        }
        
        container.innerHTML = countries.slice(0, 5).map(country => `
            <div class="country-item">
                <span class="country-name">${this.escapeHtml(country.name || country.country)}</span>
                <span class="country-count">${country.count || 0}</span>
            </div>
        `).join('');
    },
    
    renderVNOrders(orders) {
        const tbody = document.getElementById('vnOrdersTableBody');
        const pageInfo = document.getElementById('vnPageInfo');
        const prevBtn = document.getElementById('vnPrevBtn');
        const nextBtn = document.getElementById('vnNextBtn');
        
        if (!tbody) return;
        
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No hay compras de números virtuales</td></tr>';
            if (prevBtn) prevBtn.disabled = true;
            if (nextBtn) nextBtn.disabled = true;
            if (pageInfo) pageInfo.textContent = this.vnPage === 1 ? 'Sin resultados' : 'Página ' + this.vnPage;
            return;
        }
        
        tbody.innerHTML = orders.map(order => `
            <tr>
                <td>${order.id}</td>
                <td>
                    <a href="#" class="user-link" data-user-id="${order.user_id}">${this.escapeHtml(order.username || order.user_id)}</a>
                </td>
                <td class="monospace">${this.escapeHtml(order.phone_number || '-')}</td>
                <td>${this.escapeHtml(order.service || '-')}</td>
                <td>${this.escapeHtml(order.country || '-')}</td>
                <td>${this.formatNumber(order.cost || 0, 2)} B3C</td>
                <td><span class="status-badge ${this.getVNStatusClass(order.status)}">${this.getVNStatusLabel(order.status)}</span></td>
                <td>${order.sms_received ? '<span class="status-badge success">Sí</span>' : '<span class="status-badge pending">No</span>'}</td>
                <td>${this.formatDate(order.created_at)}</td>
            </tr>
        `).join('');
        
        const isLastPage = orders.length < this.vnPerPage;
        if (prevBtn) prevBtn.disabled = this.vnPage <= 1;
        if (nextBtn) nextBtn.disabled = isLastPage;
        if (pageInfo) pageInfo.textContent = `Página ${this.vnPage}`;
    },
    
    getVNStatusClass(status) {
        const classes = {
            'active': 'info',
            'received': 'success',
            'cancelled': 'danger',
            'expired': 'warning',
            'pending': 'pending'
        };
        return classes[status] || 'default';
    },
    
    getVNStatusLabel(status) {
        const labels = {
            'active': 'Activo',
            'received': 'Recibido',
            'cancelled': 'Cancelado',
            'expired': 'Expirado',
            'pending': 'Pendiente'
        };
        return labels[status] || status;
    },
    
    async loadAnalytics() {
        try {
            const [usersRes, usageRes, conversionRes] = await Promise.all([
                this.fetchAPI('/api/admin/analytics/users'),
                this.fetchAPI('/api/admin/analytics/usage'),
                this.fetchAPI('/api/admin/analytics/conversion')
            ]);
            
            if (usersRes.success) {
                document.getElementById('analyticsActiveToday').textContent = this.formatNumber(usersRes.activeToday);
                document.getElementById('analyticsActiveWeek').textContent = this.formatNumber(usersRes.activeWeek);
                document.getElementById('analyticsActiveMonth').textContent = this.formatNumber(usersRes.activeMonth);
                document.getElementById('analyticsRetention').textContent = usersRes.retentionRate + '%';
                
                this.renderNewUsersChart(usersRes.newUsersChart || []);
                this.renderUsersByCountry(usersRes.usersByCountry || []);
                this.renderUsersByDevice(usersRes.usersByDevice || []);
            }
            
            if (usageRes.success) {
                this.renderHourlyActivity(usageRes.hourlyActivity || []);
                this.renderTopSections(usageRes.topSections || []);
                this.renderDailyActivity(usageRes.dailyActivity || []);
            }
            
            if (conversionRes.success) {
                document.getElementById('b3cConversionRate').textContent = conversionRes.b3cConversionRate + '%';
                document.getElementById('vnConversionRate').textContent = conversionRes.vnConversionRate + '%';
                document.getElementById('publishConversionRate').textContent = conversionRes.publishRate + '%';
                document.getElementById('usersPurchasedB3C').textContent = this.formatNumber(conversionRes.usersPurchasedB3C) + ' usuarios';
                document.getElementById('usersUsedVN').textContent = this.formatNumber(conversionRes.usersUsedVN) + ' usuarios';
                document.getElementById('usersPublished').textContent = this.formatNumber(conversionRes.usersPublished) + ' usuarios';
                document.getElementById('totalRevenueTON').textContent = this.formatNumber(conversionRes.totalRevenueTON, 4) + ' TON';
                
                this.renderConversionFunnel(conversionRes.funnel || []);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    },
    
    renderNewUsersChart(data) {
        const container = document.getElementById('newUsersChartBars');
        if (!container || !data.length) {
            if (container) container.innerHTML = '<div class="empty-chart">Sin datos</div>';
            return;
        }
        
        const maxCount = Math.max(...data.map(d => d.count), 1);
        container.innerHTML = data.map(item => {
            const height = (item.count / maxCount) * 100;
            const date = new Date(item.date);
            const day = date.getDate();
            return `<div class="chart-bar" style="height: ${height}%" title="${item.date}: ${item.count} usuarios"><span class="bar-label">${day}</span></div>`;
        }).join('');
    },
    
    renderUsersByCountry(data) {
        const tbody = document.getElementById('usersByCountryTable');
        if (!tbody) return;
        
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="2">Sin datos</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.slice(0, 10).map(item => `
            <tr>
                <td>${this.escapeHtml(item.country)}</td>
                <td>${this.formatNumber(item.count)}</td>
            </tr>
        `).join('');
    },
    
    renderUsersByDevice(data) {
        const tbody = document.getElementById('usersByDeviceTable');
        if (!tbody) return;
        
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="2">Sin datos</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(item => `
            <tr>
                <td>${this.escapeHtml(item.device)}</td>
                <td>${this.formatNumber(item.count)}</td>
            </tr>
        `).join('');
    },
    
    renderHourlyActivity(data) {
        const container = document.getElementById('hourlyActivityBars');
        if (!container) return;
        
        if (!data.length) {
            container.innerHTML = '<div class="empty-chart">Sin datos</div>';
            return;
        }
        
        const maxCount = Math.max(...data.map(d => d.count), 1);
        const hours = Array(24).fill(0);
        data.forEach(d => hours[d.hour] = d.count);
        
        container.innerHTML = hours.map((count, hour) => {
            const width = (count / maxCount) * 100;
            return `<div class="chart-bar-h" style="width: ${width}%" title="${hour}:00 - ${count} acciones"><span class="bar-label-h">${hour}h</span></div>`;
        }).join('');
    },
    
    renderTopSections(data) {
        const tbody = document.getElementById('topSectionsTable');
        if (!tbody) return;
        
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="2">Sin datos</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.slice(0, 10).map(item => `
            <tr>
                <td>${this.escapeHtml(item.section || 'N/A')}</td>
                <td>${this.formatNumber(item.count)}</td>
            </tr>
        `).join('');
    },
    
    renderDailyActivity(data) {
        const tbody = document.getElementById('dailyActivityTable');
        if (!tbody) return;
        
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="2">Sin datos</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(item => `
            <tr>
                <td>${this.escapeHtml(item.day)}</td>
                <td>${this.formatNumber(item.count)}</td>
            </tr>
        `).join('');
    },
    
    renderConversionFunnel(data) {
        const container = document.getElementById('conversionFunnel');
        if (!container) return;
        
        if (!data.length) {
            container.innerHTML = '<div class="empty-funnel">Sin datos de conversión</div>';
            return;
        }
        
        const maxCount = data[0]?.count || 1;
        container.innerHTML = data.map((item, index) => {
            const width = 100 - (index * 15);
            return `
                <div class="funnel-stage" style="width: ${width}%">
                    <div class="funnel-bar" style="background: linear-gradient(90deg, #F0B90B ${item.rate}%, #2a2e35 ${item.rate}%);">
                        <span class="funnel-label">${this.escapeHtml(item.stage)}</span>
                        <span class="funnel-value">${this.formatNumber(item.count)} (${item.rate}%)</span>
                    </div>
                </div>
            `;
        }).join('');
    },
    
    initAnalyticsTabs() {
        document.querySelectorAll('.analytics-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.analytics-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const tab = btn.dataset.analytics;
                document.querySelectorAll('.analytics-panel').forEach(p => p.classList.remove('active'));
                document.getElementById(`analytics-${tab}`)?.classList.add('active');
            });
        });
    },
    
    getAuthHeaders() {
        const token = this.getDemoSessionToken();
        const headers = {
            'Content-Type': 'application/json',
            'X-Demo-Mode': 'true'
        };
        
        if (token) {
            headers['X-Demo-Session'] = token;
        }
        
        return headers;
    }
};

const SupportModule = {
    currentTicket: null,
    
    init() {
        this.bindEvents();
        this.loadTickets();
        this.loadFAQs();
        this.loadMassMessages();
    },
    
    bindEvents() {
        document.getElementById('ticketStatusFilter')?.addEventListener('change', () => this.loadTickets());
        document.getElementById('ticketSearch')?.addEventListener('input', debounce(() => this.loadTickets(), 300));
        
        document.getElementById('faqCategoryFilter')?.addEventListener('change', () => this.loadFAQs());
        document.getElementById('addFaqBtn')?.addEventListener('click', () => this.showFAQModal());
        
        document.querySelectorAll('.mass-msg-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchMassMessageTab(e.target.dataset.tab));
        });
        
        document.getElementById('sendMassMessageBtn')?.addEventListener('click', () => this.sendMassMessage());
        document.getElementById('scheduleMassMessageBtn')?.addEventListener('click', () => this.scheduleMassMessage());
        
        document.getElementById('sendTicketReply')?.addEventListener('click', () => this.sendTicketReply());
    },
    
    async loadTickets() {
        const status = document.getElementById('ticketStatusFilter')?.value || 'all';
        const search = document.getElementById('ticketSearch')?.value || '';
        
        try {
            const response = await fetch(`/api/admin/support/tickets?status=${status}&search=${encodeURIComponent(search)}`, {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.renderTicketsList(data.tickets);
                this.updateTicketStats(data.stats);
            }
        } catch (error) {
            console.error('Error loading tickets:', error);
        }
    },
    
    renderTicketsList(tickets) {
        const container = document.getElementById('ticketsList');
        if (!container) return;
        
        if (!tickets || tickets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-ticket-alt"></i>
                    <p>No hay tickets para mostrar</p>
                </div>`;
            return;
        }
        
        container.innerHTML = tickets.map(ticket => `
            <div class="ticket-item ${this.currentTicket?.id === ticket.id ? 'active' : ''}" 
                 onclick="SupportModule.selectTicket(${ticket.id})">
                <div class="ticket-header">
                    <span class="ticket-id">#${ticket.id}</span>
                    <span class="ticket-status status-${ticket.status}">${this.getStatusLabel(ticket.status)}</span>
                </div>
                <div class="ticket-subject">${AdminPanel.escapeHtml(ticket.subject)}</div>
                <div class="ticket-meta">
                    <span class="ticket-user"><i class="fas fa-user"></i> ${AdminPanel.escapeHtml(ticket.user_name || 'Usuario')}</span>
                    <span class="ticket-date"><i class="fas fa-clock"></i> ${this.formatDate(ticket.created_at)}</span>
                </div>
                ${ticket.priority === 'high' ? '<span class="ticket-priority high"><i class="fas fa-exclamation-triangle"></i> Alta</span>' : ''}
            </div>
        `).join('');
    },
    
    updateTicketStats(stats) {
        if (!stats) return;
        const openEl = document.querySelector('.stat-open');
        const pendingEl = document.querySelector('.stat-pending');
        const resolvedEl = document.querySelector('.stat-resolved');
        const avgTimeEl = document.querySelector('.stat-avg-time');
        
        if (openEl) openEl.textContent = stats.open || 0;
        if (pendingEl) pendingEl.textContent = stats.pending || 0;
        if (resolvedEl) resolvedEl.textContent = stats.resolved || 0;
        if (avgTimeEl) avgTimeEl.textContent = stats.avg_response_time || '0h';
    },
    
    getStatusLabel(status) {
        const labels = {
            'open': 'Abierto',
            'pending': 'Pendiente',
            'in_progress': 'En Progreso',
            'resolved': 'Resuelto',
            'closed': 'Cerrado'
        };
        return labels[status] || status;
    },
    
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = (now - date) / 1000;
        
        if (diff < 60) return 'Hace un momento';
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `Hace ${Math.floor(diff / 3600)}h`;
        if (diff < 604800) return `Hace ${Math.floor(diff / 86400)}d`;
        
        return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    },
    
    async selectTicket(ticketId) {
        try {
            const response = await fetch(`/api/admin/support/tickets/${ticketId}`, {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.currentTicket = data.ticket;
                this.renderTicketDetail(data.ticket);
                
                document.querySelectorAll('.ticket-item').forEach(item => item.classList.remove('active'));
                document.querySelector(`.ticket-item[onclick*="${ticketId}"]`)?.classList.add('active');
            }
        } catch (error) {
            console.error('Error loading ticket detail:', error);
        }
    },
    
    renderTicketDetail(ticket) {
        const container = document.getElementById('ticketDetail');
        if (!container) return;
        
        container.innerHTML = `
            <div class="ticket-detail-header">
                <h3>${AdminPanel.escapeHtml(ticket.subject)}</h3>
                <div class="ticket-detail-meta">
                    <span class="ticket-status status-${ticket.status}">${this.getStatusLabel(ticket.status)}</span>
                    <span class="ticket-priority ${ticket.priority}">${ticket.priority === 'high' ? 'Alta' : ticket.priority === 'medium' ? 'Media' : 'Baja'}</span>
                </div>
            </div>
            
            <div class="ticket-user-info">
                <div class="user-avatar">
                    ${ticket.user_photo ? `<img src="${ticket.user_photo}" alt="">` : '<i class="fas fa-user"></i>'}
                </div>
                <div class="user-details">
                    <span class="user-name">${AdminPanel.escapeHtml(ticket.user_name || 'Usuario')}</span>
                    <span class="user-id">ID: ${ticket.user_id}</span>
                </div>
            </div>
            
            <div class="ticket-messages" id="ticketMessages">
                ${this.renderTicketMessages(ticket.messages || [])}
            </div>
            
            <div class="ticket-reply-box">
                <div class="reply-templates">
                    <select id="replyTemplateSelect" onchange="SupportModule.applyTemplate(this.value)">
                        <option value="">Plantilla rápida...</option>
                    </select>
                </div>
                <textarea id="ticketReplyText" placeholder="Escribe tu respuesta..." rows="3"></textarea>
                <div class="reply-actions">
                    <select id="ticketStatusChange">
                        <option value="">Sin cambiar estado</option>
                        <option value="pending">Pendiente</option>
                        <option value="in_progress">En Progreso</option>
                        <option value="resolved">Resuelto</option>
                        <option value="closed">Cerrado</option>
                    </select>
                    <button id="sendTicketReply" class="btn-primary">
                        <i class="fas fa-paper-plane"></i> Enviar
                    </button>
                </div>
            </div>
        `;
        
        this.loadResponseTemplates();
    },
    
    renderTicketMessages(messages) {
        if (!messages || messages.length === 0) {
            return '<div class="no-messages">Sin mensajes</div>';
        }
        
        return messages.map(msg => `
            <div class="ticket-message ${msg.is_admin ? 'admin-message' : 'user-message'}">
                <div class="message-header">
                    <span class="message-sender">${msg.is_admin ? 'Soporte' : AdminPanel.escapeHtml(msg.sender_name || 'Usuario')}</span>
                    <span class="message-time">${this.formatDate(msg.created_at)}</span>
                </div>
                <div class="message-content">${AdminPanel.escapeHtml(msg.message)}</div>
            </div>
        `).join('');
    },
    
    async loadResponseTemplates() {
        try {
            const response = await fetch('/api/admin/support/templates', {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                const select = document.getElementById('replyTemplateSelect');
                if (select) {
                    select.innerHTML = '<option value="">Plantilla rápida...</option>' +
                        data.templates.map(t => `<option value="${t.id}">${AdminPanel.escapeHtml(t.name)}</option>`).join('');
                }
                this.responseTemplates = data.templates;
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    },
    
    applyTemplate(templateId) {
        if (!templateId) return;
        const template = this.responseTemplates?.find(t => t.id == templateId);
        if (template) {
            document.getElementById('ticketReplyText').value = template.content;
        }
    },
    
    async sendTicketReply() {
        if (!this.currentTicket) return;
        
        const message = document.getElementById('ticketReplyText')?.value?.trim();
        const newStatus = document.getElementById('ticketStatusChange')?.value;
        
        if (!message) {
            AdminPanel.showNotification('Escribe un mensaje', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/support/tickets/${this.currentTicket.id}/reply`, {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message, status: newStatus || undefined })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Respuesta enviada', 'success');
                document.getElementById('ticketReplyText').value = '';
                document.getElementById('ticketStatusChange').value = '';
                this.selectTicket(this.currentTicket.id);
                this.loadTickets();
            } else {
                AdminPanel.showNotification(data.error || 'Error al enviar', 'error');
            }
        } catch (error) {
            console.error('Error sending reply:', error);
            AdminPanel.showNotification('Error de conexión', 'error');
        }
    },
    
    async loadFAQs() {
        const category = document.getElementById('faqCategoryFilter')?.value || '';
        
        try {
            const response = await fetch(`/api/admin/faq?category=${encodeURIComponent(category)}`, {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.renderFAQList(data.faqs);
            }
        } catch (error) {
            console.error('Error loading FAQs:', error);
        }
    },
    
    renderFAQList(faqs) {
        const container = document.getElementById('faqList');
        if (!container) return;
        
        if (!faqs || faqs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-question-circle"></i>
                    <p>No hay FAQs creadas</p>
                    <button class="btn-primary" onclick="SupportModule.showFAQModal()">Crear primera FAQ</button>
                </div>`;
            return;
        }
        
        container.innerHTML = faqs.map(faq => `
            <div class="faq-item ${faq.is_published ? 'published' : 'draft'}">
                <div class="faq-content">
                    <div class="faq-question">${AdminPanel.escapeHtml(faq.question)}</div>
                    <div class="faq-answer">${AdminPanel.escapeHtml(faq.answer).substring(0, 100)}...</div>
                    <div class="faq-meta">
                        <span class="faq-category">${AdminPanel.escapeHtml(faq.category)}</span>
                        <span class="faq-status">${faq.is_published ? 'Publicada' : 'Borrador'}</span>
                    </div>
                </div>
                <div class="faq-actions">
                    <button class="btn-icon" onclick="SupportModule.editFAQ(${faq.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon" onclick="SupportModule.toggleFAQPublish(${faq.id}, ${!faq.is_published})" 
                            title="${faq.is_published ? 'Despublicar' : 'Publicar'}">
                        <i class="fas fa-${faq.is_published ? 'eye-slash' : 'eye'}"></i>
                    </button>
                    <button class="btn-icon danger" onclick="SupportModule.deleteFAQ(${faq.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    showFAQModal(faq = null) {
        const modal = document.getElementById('faqModal');
        if (!modal) return;
        
        const form = modal.querySelector('#faqForm');
        if (form) form.reset();
        
        document.getElementById('faqModalTitle').textContent = faq ? 'Editar FAQ' : 'Nueva FAQ';
        document.getElementById('faqId').value = faq?.id || '';
        document.getElementById('faqQuestion').value = faq?.question || '';
        document.getElementById('faqAnswer').value = faq?.answer || '';
        document.getElementById('faqCategory').value = faq?.category || 'general';
        document.getElementById('faqPublished').checked = faq?.is_published ?? true;
        
        modal.classList.add('active');
    },
    
    closeFAQModal() {
        document.getElementById('faqModal')?.classList.remove('active');
    },
    
    async saveFAQ() {
        const id = document.getElementById('faqId')?.value;
        const question = document.getElementById('faqQuestion')?.value?.trim();
        const answer = document.getElementById('faqAnswer')?.value?.trim();
        const category = document.getElementById('faqCategory')?.value;
        const is_published = document.getElementById('faqPublished')?.checked;
        
        if (!question || !answer) {
            AdminPanel.showNotification('Completa pregunta y respuesta', 'error');
            return;
        }
        
        try {
            const url = id ? `/api/admin/faq/${id}` : '/api/admin/faq';
            const method = id ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question, answer, category, is_published })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification(id ? 'FAQ actualizada' : 'FAQ creada', 'success');
                this.closeFAQModal();
                this.loadFAQs();
            } else {
                AdminPanel.showNotification(data.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error saving FAQ:', error);
            AdminPanel.showNotification('Error de conexión', 'error');
        }
    },
    
    async editFAQ(faqId) {
        try {
            const response = await fetch(`/api/admin/faq?id=${faqId}`, {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success && data.faqs.length > 0) {
                const faq = data.faqs.find(f => f.id == faqId);
                if (faq) this.showFAQModal(faq);
            }
        } catch (error) {
            console.error('Error loading FAQ:', error);
        }
    },
    
    async toggleFAQPublish(faqId, publish) {
        try {
            const response = await fetch(`/api/admin/faq/${faqId}`, {
                method: 'PUT',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_published: publish })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification(publish ? 'FAQ publicada' : 'FAQ despublicada', 'success');
                this.loadFAQs();
            }
        } catch (error) {
            console.error('Error toggling FAQ:', error);
        }
    },
    
    async deleteFAQ(faqId) {
        if (!confirm('¿Eliminar esta FAQ?')) return;
        
        try {
            const response = await fetch(`/api/admin/faq/${faqId}`, {
                method: 'DELETE',
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('FAQ eliminada', 'success');
                this.loadFAQs();
            }
        } catch (error) {
            console.error('Error deleting FAQ:', error);
        }
    },
    
    switchMassMessageTab(tab) {
        document.querySelectorAll('.mass-msg-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`.mass-msg-tab[data-tab="${tab}"]`)?.classList.add('active');
        
        document.querySelectorAll('.mass-msg-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`massMsg-${tab}`)?.classList.add('active');
        
        if (tab === 'history') {
            this.loadMassMessages();
        } else if (tab === 'scheduled') {
            this.loadScheduledMessages();
        }
    },
    
    async loadMassMessages() {
        try {
            const response = await fetch('/api/admin/messages', {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.renderMessageHistory(data.messages);
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    },
    
    renderMessageHistory(messages) {
        const container = document.getElementById('messageHistory');
        if (!container) return;
        
        if (!messages || messages.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-envelope"></i>
                    <p>No hay mensajes enviados</p>
                </div>`;
            return;
        }
        
        container.innerHTML = messages.map(msg => `
            <div class="message-history-item">
                <div class="message-header">
                    <span class="message-title">${AdminPanel.escapeHtml(msg.title)}</span>
                    <span class="message-status status-${msg.status}">${this.getMessageStatus(msg.status)}</span>
                </div>
                <div class="message-preview">${AdminPanel.escapeHtml(msg.content).substring(0, 100)}...</div>
                <div class="message-meta">
                    <span><i class="fas fa-users"></i> ${msg.recipients_count || 0} destinatarios</span>
                    <span><i class="fas fa-clock"></i> ${this.formatDate(msg.created_at)}</span>
                </div>
            </div>
        `).join('');
    },
    
    getMessageStatus(status) {
        const labels = {
            'sent': 'Enviado',
            'scheduled': 'Programado',
            'sending': 'Enviando...',
            'cancelled': 'Cancelado'
        };
        return labels[status] || status;
    },
    
    async loadScheduledMessages() {
        try {
            const response = await fetch('/api/admin/messages/scheduled', {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.renderScheduledMessages(data.messages);
            }
        } catch (error) {
            console.error('Error loading scheduled messages:', error);
        }
    },
    
    renderScheduledMessages(messages) {
        const container = document.getElementById('scheduledMessages');
        if (!container) return;
        
        if (!messages || messages.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <p>No hay mensajes programados</p>
                </div>`;
            return;
        }
        
        container.innerHTML = messages.map(msg => `
            <div class="scheduled-message-item">
                <div class="message-info">
                    <div class="message-title">${AdminPanel.escapeHtml(msg.title)}</div>
                    <div class="message-scheduled-time">
                        <i class="fas fa-calendar"></i> 
                        ${new Date(msg.scheduled_at).toLocaleString('es-ES')}
                    </div>
                </div>
                <button class="btn-danger-sm" onclick="SupportModule.cancelScheduledMessage(${msg.id})">
                    <i class="fas fa-times"></i> Cancelar
                </button>
            </div>
        `).join('');
    },
    
    async sendMassMessage() {
        const title = document.getElementById('massMessageTitle')?.value?.trim();
        const content = document.getElementById('massMessageContent')?.value?.trim();
        const targetGroup = document.getElementById('massMessageTarget')?.value;
        const messageType = document.getElementById('massMessageType')?.value;
        
        if (!title || !content) {
            AdminPanel.showNotification('Completa título y contenido', 'error');
            return;
        }
        
        if (!confirm('¿Enviar mensaje a todos los usuarios seleccionados?')) return;
        
        try {
            const response = await fetch('/api/admin/messages', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    content,
                    target_group: targetGroup,
                    message_type: messageType,
                    send_type: 'now'
                })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification(`Mensaje enviado a ${data.recipients_count} usuarios`, 'success');
                document.getElementById('massMessageTitle').value = '';
                document.getElementById('massMessageContent').value = '';
                this.loadMassMessages();
            } else {
                AdminPanel.showNotification(data.error || 'Error al enviar', 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            AdminPanel.showNotification('Error de conexión', 'error');
        }
    },
    
    async scheduleMassMessage() {
        const title = document.getElementById('massMessageTitle')?.value?.trim();
        const content = document.getElementById('massMessageContent')?.value?.trim();
        const targetGroup = document.getElementById('massMessageTarget')?.value;
        const messageType = document.getElementById('massMessageType')?.value;
        const scheduledAt = document.getElementById('massMessageScheduleTime')?.value;
        
        if (!title || !content) {
            AdminPanel.showNotification('Completa título y contenido', 'error');
            return;
        }
        
        if (!scheduledAt) {
            AdminPanel.showNotification('Selecciona fecha y hora', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/admin/messages', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    content,
                    target_group: targetGroup,
                    message_type: messageType,
                    send_type: 'scheduled',
                    scheduled_at: scheduledAt
                })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Mensaje programado correctamente', 'success');
                document.getElementById('massMessageTitle').value = '';
                document.getElementById('massMessageContent').value = '';
                document.getElementById('massMessageScheduleTime').value = '';
                this.switchMassMessageTab('scheduled');
            } else {
                AdminPanel.showNotification(data.error || 'Error al programar', 'error');
            }
        } catch (error) {
            console.error('Error scheduling message:', error);
            AdminPanel.showNotification('Error de conexión', 'error');
        }
    },
    
    async cancelScheduledMessage(messageId) {
        if (!confirm('¿Cancelar este mensaje programado?')) return;
        
        try {
            const response = await fetch(`/api/admin/messages/${messageId}/cancel`, {
                method: 'POST',
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Mensaje cancelado', 'success');
                this.loadScheduledMessages();
            }
        } catch (error) {
            console.error('Error cancelling message:', error);
        }
    }
};

const NotificationsModule = {
    async loadNotifications() {
        const typeFilter = document.getElementById('notifTypeFilter')?.value || '';
        const readFilter = document.getElementById('notifReadFilter')?.value || '';
        
        try {
            let url = '/api/admin/notifications?';
            if (typeFilter) url += `type=${typeFilter}&`;
            if (readFilter) url += `is_read=${readFilter === 'read'}&`;
            
            const response = await fetch(url, {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                this.renderNotifications(data.notifications);
                const unreadCount = data.notifications.filter(n => !n.is_read).length;
                const countEl = document.getElementById('adminNotifCount');
                if (countEl) countEl.textContent = unreadCount;
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    },
    
    renderNotifications(notifications) {
        const container = document.getElementById('adminNotificationsList');
        if (!container) return;
        
        if (!notifications || notifications.length === 0) {
            container.innerHTML = '<div class="empty-state">Sin notificaciones</div>';
            return;
        }
        
        const typeIcons = {
            large_purchase: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
            pending_withdrawal: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
            system_error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            content_report: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
            user_banned: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>',
            low_balance: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="M2 10h20"></path></svg>',
            new_user: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>',
            new_ticket: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        };
        
        container.innerHTML = notifications.map(notif => `
            <div class="admin-notif-item ${notif.is_read ? 'read' : 'unread'}" data-id="${notif.id}">
                <div class="notif-icon ${notif.type}">
                    ${typeIcons[notif.type] || typeIcons.system_error}
                </div>
                <div class="notif-content">
                    <div class="notif-title">${AdminPanel.escapeHtml(notif.title)}</div>
                    <div class="notif-message">${AdminPanel.escapeHtml(notif.message)}</div>
                    <div class="notif-time">${AdminPanel.timeAgo(notif.created_at)}</div>
                </div>
                <div class="notif-actions">
                    ${!notif.is_read ? `<button class="btn-icon" onclick="NotificationsModule.markAsRead(${notif.id})" title="Marcar como leida"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg></button>` : ''}
                    <button class="btn-icon danger" onclick="NotificationsModule.deleteNotification(${notif.id})" title="Eliminar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
                </div>
            </div>
        `).join('');
    },
    
    async markAsRead(notifId) {
        try {
            const response = await fetch('/api/admin/notifications/mark-read', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notification_id: notifId })
            });
            const data = await response.json();
            if (data.success) {
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    },
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/admin/notifications/mark-read', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ all: true })
            });
            const data = await response.json();
            if (data.success) {
                this.loadNotifications();
                AdminPanel.showNotification('Todas las notificaciones marcadas como leidas', 'success');
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    },
    
    async deleteNotification(notifId) {
        if (!confirm('Eliminar esta notificacion?')) return;
        
        try {
            const response = await fetch('/api/admin/notifications/delete', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notification_id: notifId })
            });
            const data = await response.json();
            if (data.success) {
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    },
    
    async loadTelegramSettings() {
        try {
            const response = await fetch('/api/admin/telegram/settings', {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success && data.settings) {
                const s = data.settings;
                document.getElementById('toggleLargePurchase').checked = s.notify_large_purchase !== false;
                document.getElementById('togglePendingWithdrawal').checked = s.notify_pending_withdrawal !== false;
                document.getElementById('toggleSystemError').checked = s.notify_system_error !== false;
                document.getElementById('toggleContentReport').checked = s.notify_content_report !== false;
                document.getElementById('toggleUserBanned').checked = s.notify_user_banned !== false;
                document.getElementById('toggleLowBalance').checked = s.notify_low_balance !== false;
                document.getElementById('toggleNewUser').checked = s.notify_new_user === true;
                document.getElementById('toggleNewTicket').checked = s.notify_new_ticket !== false;
                document.getElementById('thresholdLargePurchase').value = s.large_purchase_threshold || 1000;
                document.getElementById('thresholdLowBalance').value = s.low_balance_threshold || 10;
            }
            
            this.verifyTelegram();
        } catch (error) {
            console.error('Error loading telegram settings:', error);
        }
    },
    
    async saveSettings() {
        const settings = {
            notify_large_purchase: document.getElementById('toggleLargePurchase').checked,
            notify_pending_withdrawal: document.getElementById('togglePendingWithdrawal').checked,
            notify_system_error: document.getElementById('toggleSystemError').checked,
            notify_content_report: document.getElementById('toggleContentReport').checked,
            notify_user_banned: document.getElementById('toggleUserBanned').checked,
            notify_low_balance: document.getElementById('toggleLowBalance').checked,
            notify_new_user: document.getElementById('toggleNewUser').checked,
            notify_new_ticket: document.getElementById('toggleNewTicket').checked,
            large_purchase_threshold: parseInt(document.getElementById('thresholdLargePurchase').value) || 1000,
            low_balance_threshold: parseFloat(document.getElementById('thresholdLowBalance').value) || 10
        };
        
        try {
            const response = await fetch('/api/admin/telegram/settings', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Configuracion guardada', 'success');
            } else {
                AdminPanel.showNotification(data.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            AdminPanel.showNotification('Error de conexion', 'error');
        }
    },
    
    async verifyTelegram() {
        const statusEl = document.getElementById('telegramStatus');
        const infoEl = document.getElementById('telegramInfo');
        
        try {
            const response = await fetch('/api/admin/telegram/verify', {
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success && data.connected) {
                statusEl.innerHTML = '<span class="status-dot connected"></span><span>Conectado</span>';
                infoEl.innerHTML = `<p><strong>Bot:</strong> @${data.bot_username || 'N/A'}</p><p><strong>Chat ID:</strong> ${data.chat_id || 'Configurado'}</p>`;
            } else {
                statusEl.innerHTML = '<span class="status-dot disconnected"></span><span>Desconectado</span>';
                infoEl.innerHTML = `<p>${data.error || 'Bot no configurado'}</p><p>Configura las variables de entorno:</p><code>TELEGRAM_BOT_TOKEN</code><br><code>TELEGRAM_ADMIN_CHAT_ID</code>`;
            }
        } catch (error) {
            console.error('Error verifying telegram:', error);
            statusEl.innerHTML = '<span class="status-dot disconnected"></span><span>Error</span>';
        }
    },
    
    async sendTestMessage() {
        try {
            const response = await fetch('/api/admin/telegram/test', {
                method: 'POST',
                headers: AdminPanel.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Mensaje de prueba enviado a Telegram', 'success');
            } else {
                AdminPanel.showNotification(data.error || 'Error al enviar mensaje', 'error');
            }
        } catch (error) {
            console.error('Error sending test message:', error);
            AdminPanel.showNotification('Error de conexion', 'error');
        }
    },
    
    async sendCustomMessage() {
        const message = document.getElementById('customTelegramMessage')?.value?.trim();
        if (!message) {
            AdminPanel.showNotification('Escribe un mensaje', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/admin/telegram/send', {
                method: 'POST',
                headers: {
                    ...AdminPanel.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            
            if (data.success) {
                AdminPanel.showNotification('Mensaje enviado', 'success');
                document.getElementById('customTelegramMessage').value = '';
            } else {
                AdminPanel.showNotification(data.error || 'Error al enviar', 'error');
            }
        } catch (error) {
            console.error('Error sending custom message:', error);
            AdminPanel.showNotification('Error de conexion', 'error');
        }
    }
};

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const RiskScoreModule = {
    data: [],
    
    async init() {
        await this.loadData();
        this.setupFilters();
    },
    
    async loadData() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/risk-scores');
            if (response.success) {
                this.data = response.users || [];
                this.updateStats();
                this.renderTable();
            }
        } catch (error) {
            console.error('Error loading risk scores:', error);
        }
    },
    
    async refreshData() {
        await this.loadData();
        AdminPanel.showToast('Datos actualizados', 'success');
    },
    
    updateStats() {
        const counts = { low: 0, medium: 0, high: 0, critical: 0 };
        this.data.forEach(user => {
            const level = this.getRiskLevel(user.riskScore);
            counts[level]++;
        });
        
        document.getElementById('riskLowCount').textContent = counts.low;
        document.getElementById('riskMediumCount').textContent = counts.medium;
        document.getElementById('riskHighCount').textContent = counts.high;
        document.getElementById('riskCriticalCount').textContent = counts.critical;
    },
    
    getRiskLevel(score) {
        if (score <= 25) return 'low';
        if (score <= 50) return 'medium';
        if (score <= 75) return 'high';
        return 'critical';
    },
    
    getRiskLevelText(level) {
        const texts = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Critico' };
        return texts[level] || level;
    },
    
    renderTable(filteredData = null) {
        const tbody = document.getElementById('riskScoreTableBody');
        const data = filteredData || this.data;
        
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-row">No hay datos de riesgo</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(user => {
            const level = this.getRiskLevel(user.riskScore);
            const factors = user.riskFactors || [];
            
            return `
                <tr>
                    <td>
                        <div class="user-info-cell">
                            <span class="user-name">${AdminPanel.escapeHtml(user.firstName || '')} ${AdminPanel.escapeHtml(user.lastName || '')}</span>
                            <span class="user-username">@${AdminPanel.escapeHtml(user.username || 'N/A')}</span>
                        </div>
                    </td>
                    <td>
                        <span class="risk-score-badge ${level}">${user.riskScore}</span>
                    </td>
                    <td>
                        <span class="status-badge ${level}">${this.getRiskLevelText(level)}</span>
                    </td>
                    <td>
                        <div class="risk-factors-tags">
                            ${factors.slice(0, 3).map(f => `<span class="risk-factor-tag">${AdminPanel.escapeHtml(f)}</span>`).join('')}
                            ${factors.length > 3 ? `<span class="risk-factor-tag">+${factors.length - 3}</span>` : ''}
                        </div>
                    </td>
                    <td>${AdminPanel.formatDateTime(user.lastScoreChange)}</td>
                    <td>
                        <div class="action-btns">
                            <button class="action-btn" onclick="RiskScoreModule.viewDetails(${user.telegramId})">Ver</button>
                            <button class="action-btn" onclick="RiskScoreModule.adjustScore(${user.telegramId})">Ajustar</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },
    
    setupFilters() {
        const searchInput = document.getElementById('riskUserSearch');
        const levelFilter = document.getElementById('riskLevelFilter');
        
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => this.applyFilters(), 300));
        }
        if (levelFilter) {
            levelFilter.addEventListener('change', () => this.applyFilters());
        }
    },
    
    applyFilters() {
        const search = document.getElementById('riskUserSearch')?.value?.toLowerCase() || '';
        const level = document.getElementById('riskLevelFilter')?.value || '';
        
        let filtered = this.data;
        
        if (search) {
            filtered = filtered.filter(u => 
                (u.username || '').toLowerCase().includes(search) ||
                (u.firstName || '').toLowerCase().includes(search)
            );
        }
        
        if (level) {
            filtered = filtered.filter(u => this.getRiskLevel(u.riskScore) === level);
        }
        
        this.renderTable(filtered);
    },
    
    async viewDetails(telegramId) {
        AdminPanel.showToast('Cargando detalles de riesgo...', 'info');
    },
    
    async adjustScore(telegramId) {
        const newScore = prompt('Ingresa el nuevo score de riesgo (0-100):');
        if (newScore === null) return;
        
        const score = parseInt(newScore);
        if (isNaN(score) || score < 0 || score > 100) {
            AdminPanel.showToast('Score invalido', 'error');
            return;
        }
        
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/risk-scores/adjust', {
                method: 'POST',
                body: JSON.stringify({ telegramId, score })
            });
            
            if (response.success) {
                AdminPanel.showToast('Score actualizado', 'success');
                this.loadData();
            } else {
                AdminPanel.showToast(response.error || 'Error', 'error');
            }
        } catch (error) {
            console.error('Error adjusting score:', error);
            AdminPanel.showToast('Error de conexion', 'error');
        }
    },
    
    exportData() {
        const csv = this.data.map(u => 
            `${u.telegramId},${u.username || ''},${u.firstName || ''},${u.riskScore},${this.getRiskLevel(u.riskScore)}`
        ).join('\n');
        
        const blob = new Blob(['TelegramID,Username,Name,Score,Level\n' + csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'risk_scores_export.csv';
        a.click();
    }
};

const RelatedAccountsModule = {
    groups: [],
    
    async init() {
        await this.loadGroups();
        this.setupFilters();
    },
    
    async loadGroups() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/related-accounts');
            if (response.success) {
                this.groups = response.groups || [];
                this.renderGroups();
                document.getElementById('relatedGroupsCount').textContent = this.groups.length;
            }
        } catch (error) {
            console.error('Error loading related accounts:', error);
        }
    },
    
    async runScan() {
        AdminPanel.showToast('Ejecutando escaneo...', 'info');
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/related-accounts/scan', { method: 'POST' });
            if (response.success) {
                AdminPanel.showToast('Escaneo completado', 'success');
                this.loadGroups();
            }
        } catch (error) {
            console.error('Error running scan:', error);
        }
    },
    
    renderGroups(filteredData = null) {
        const container = document.getElementById('relatedGroupsList');
        const data = filteredData || this.groups;
        
        if (!data.length) {
            container.innerHTML = '<div class="empty-state">No se encontraron grupos relacionados</div>';
            return;
        }
        
        container.innerHTML = data.map((group, index) => `
            <div class="related-group-item" onclick="RelatedAccountsModule.selectGroup(${index})">
                <div class="related-group-header">
                    <span class="related-group-id">Grupo #${group.id || index + 1}</span>
                    <span class="status-badge ${group.status || 'pending'}">${group.status === 'confirmed' ? 'Confirmado' : group.status === 'false_positive' ? 'Falso Positivo' : 'Pendiente'}</span>
                </div>
                <div class="related-group-accounts">${group.accounts?.length || 0} cuentas relacionadas</div>
                <div class="related-group-reason">${AdminPanel.escapeHtml(group.reason || 'IP/Dispositivo similar')}</div>
            </div>
        `).join('');
    },
    
    selectGroup(index) {
        const group = this.groups[index];
        if (!group) return;
        
        document.querySelectorAll('.related-group-item').forEach((el, i) => {
            el.classList.toggle('active', i === index);
        });
        
        const detail = document.getElementById('relatedDetailContent');
        detail.innerHTML = `
            <div class="group-detail">
                <h4>Cuentas en este Grupo</h4>
                <div class="accounts-list">
                    ${(group.accounts || []).map(acc => `
                        <div class="account-item">
                            <div class="account-info">
                                <span class="account-name">${AdminPanel.escapeHtml(acc.firstName || '')} @${AdminPanel.escapeHtml(acc.username || 'N/A')}</span>
                                <span class="account-id">ID: ${acc.telegramId}</span>
                            </div>
                            <button class="btn-icon" onclick="AdminPanel.showUserDetail(${acc.telegramId})">Ver</button>
                        </div>
                    `).join('')}
                </div>
                <div class="detection-info">
                    <h5>Metodo de Deteccion</h5>
                    <p>${AdminPanel.escapeHtml(group.reason || 'Similitud de IP o dispositivo')}</p>
                    <p><strong>Confianza:</strong> ${group.confidence || 0}%</p>
                </div>
                <div class="group-actions">
                    <button class="btn-primary" onclick="RelatedAccountsModule.confirmGroup(${index})">Confirmar</button>
                    <button class="btn-secondary" onclick="RelatedAccountsModule.markFalsePositive(${index})">Falso Positivo</button>
                </div>
            </div>
        `;
    },
    
    setupFilters() {
        const filter = document.getElementById('relatedStatusFilter');
        if (filter) {
            filter.addEventListener('change', () => {
                const status = filter.value;
                const filtered = status ? this.groups.filter(g => g.status === status) : this.groups;
                this.renderGroups(filtered);
            });
        }
    },
    
    async confirmGroup(index) {
        AdminPanel.showToast('Grupo confirmado', 'success');
        this.groups[index].status = 'confirmed';
        this.renderGroups();
    },
    
    async markFalsePositive(index) {
        AdminPanel.showToast('Marcado como falso positivo', 'success');
        this.groups[index].status = 'false_positive';
        this.renderGroups();
    }
};

const AnomaliesModule = {
    anomalies: [],
    
    async init() {
        await this.loadData();
    },
    
    async loadData() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/anomalies');
            if (response.success) {
                this.anomalies = response.anomalies || [];
                this.updateStats();
                this.renderAnomalies();
            }
        } catch (error) {
            console.error('Error loading anomalies:', error);
        }
    },
    
    async refreshData() {
        await this.loadData();
        AdminPanel.showToast('Anomalias actualizadas', 'success');
    },
    
    updateStats() {
        const today = new Date().toDateString();
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        
        const todayCount = this.anomalies.filter(a => new Date(a.detectedAt).toDateString() === today).length;
        const weekCount = this.anomalies.filter(a => new Date(a.detectedAt) >= weekAgo).length;
        const unresolvedCount = this.anomalies.filter(a => !a.resolved).length;
        
        document.getElementById('anomaliesTodayCount').textContent = todayCount;
        document.getElementById('anomaliesWeekCount').textContent = weekCount;
        document.getElementById('anomaliesUnresolvedCount').textContent = unresolvedCount;
        document.getElementById('anomaliesCount').textContent = unresolvedCount;
    },
    
    renderAnomalies(showHistory = false) {
        const container = document.getElementById('anomaliesList');
        const data = showHistory ? this.anomalies : this.anomalies.filter(a => !a.resolved);
        
        if (!data.length) {
            container.innerHTML = '<div class="empty-state">No hay anomalias detectadas</div>';
            return;
        }
        
        container.innerHTML = data.map(anomaly => `
            <div class="anomaly-item ${anomaly.severity || 'warning'}">
                <div class="anomaly-icon ${anomaly.severity || 'warning'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div class="anomaly-content">
                    <div class="anomaly-title">${AdminPanel.escapeHtml(anomaly.title)}</div>
                    <div class="anomaly-description">${AdminPanel.escapeHtml(anomaly.description)}</div>
                    <div class="anomaly-meta">
                        <span>Usuario: @${AdminPanel.escapeHtml(anomaly.username || 'N/A')}</span>
                        <span>${AdminPanel.formatDateTime(anomaly.detectedAt)}</span>
                    </div>
                </div>
                <div class="anomaly-actions">
                    <button class="btn-icon" onclick="AnomaliesModule.investigate('${anomaly.id}')" title="Investigar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </button>
                    <button class="btn-icon" onclick="AnomaliesModule.resolve('${anomaly.id}')" title="Resolver">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    configureThresholds() {
        AdminPanel.showToast('Configuracion de umbrales', 'info');
    },
    
    investigate(id) {
        AdminPanel.showToast('Abriendo investigacion...', 'info');
    },
    
    async resolve(id) {
        const anomaly = this.anomalies.find(a => a.id === id);
        if (anomaly) {
            anomaly.resolved = true;
            this.updateStats();
            this.renderAnomalies();
            AdminPanel.showToast('Anomalia resuelta', 'success');
        }
    }
};

const TagsModule = {
    tags: [],
    selectedTag: null,
    
    async init() {
        await this.loadTags();
    },
    
    async loadTags() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/tags');
            if (response.success) {
                this.tags = response.tags || [];
                this.renderTags();
            }
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    },
    
    renderTags() {
        const container = document.getElementById('tagsList');
        
        if (!this.tags.length) {
            container.innerHTML = '<div class="empty-state">No hay etiquetas creadas</div>';
            return;
        }
        
        container.innerHTML = this.tags.map(tag => `
            <div class="tag-item" style="background: ${tag.color || '#666'}22; color: ${tag.color || '#666'}" 
                 onclick="TagsModule.selectTag('${tag.id}')">
                <span>${AdminPanel.escapeHtml(tag.name)}</span>
                <span class="tag-count">${tag.usersCount || 0}</span>
            </div>
        `).join('');
    },
    
    async selectTag(tagId) {
        this.selectedTag = this.tags.find(t => t.id === tagId);
        if (!this.selectedTag) return;
        
        document.getElementById('currentTagName').textContent = this.selectedTag.name;
        
        try {
            const response = await AdminPanel.fetchAPI(`/api/admin/tags/${tagId}/users`);
            if (response.success) {
                this.renderTagUsers(response.users || []);
            }
        } catch (error) {
            console.error('Error loading tag users:', error);
        }
    },
    
    renderTagUsers(users) {
        const container = document.getElementById('tagsUsersList');
        
        if (!users.length) {
            container.innerHTML = '<div class="empty-state">No hay usuarios con esta etiqueta</div>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-item">
                <div class="user-info">
                    <span class="user-name">${AdminPanel.escapeHtml(user.firstName || '')} @${AdminPanel.escapeHtml(user.username || 'N/A')}</span>
                </div>
                <button class="btn-icon" onclick="TagsModule.removeUserTag(${user.telegramId})" title="Quitar etiqueta">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
            </div>
        `).join('');
    },
    
    showCreateModal() {
        const name = prompt('Nombre de la etiqueta:');
        if (!name) return;
        
        const color = prompt('Color (hex, ej: #ff0000):', '#d4af37');
        if (!color) return;
        
        this.createTag(name, color);
    },
    
    async createTag(name, color) {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/tags', {
                method: 'POST',
                body: JSON.stringify({ name, color })
            });
            
            if (response.success) {
                AdminPanel.showToast('Etiqueta creada', 'success');
                this.loadTags();
            }
        } catch (error) {
            console.error('Error creating tag:', error);
        }
    },
    
    async removeUserTag(telegramId) {
        if (!this.selectedTag) return;
        
        try {
            await AdminPanel.fetchAPI(`/api/admin/tags/${this.selectedTag.id}/users/${telegramId}`, {
                method: 'DELETE'
            });
            AdminPanel.showToast('Etiqueta removida', 'success');
            this.selectTag(this.selectedTag.id);
        } catch (error) {
            console.error('Error removing tag:', error);
        }
    }
};

const VerificationsModule = {
    verifications: [],
    
    async init() {
        await this.loadData();
        this.setupFilters();
    },
    
    async loadData() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/verifications');
            if (response.success) {
                this.verifications = response.verifications || [];
                this.updateStats();
                this.renderQueue();
            }
        } catch (error) {
            console.error('Error loading verifications:', error);
        }
    },
    
    async refreshData() {
        await this.loadData();
        AdminPanel.showToast('Verificaciones actualizadas', 'success');
    },
    
    updateStats() {
        const pending = this.verifications.filter(v => v.status === 'pending').length;
        const approved = this.verifications.filter(v => v.status === 'approved').length;
        const rejected = this.verifications.filter(v => v.status === 'rejected').length;
        
        document.getElementById('verifPendingCount').textContent = pending;
        document.getElementById('verifApprovedCount').textContent = approved;
        document.getElementById('verifRejectedCount').textContent = rejected;
        document.getElementById('verificationsCount').textContent = pending;
    },
    
    renderQueue(filteredData = null) {
        const container = document.getElementById('verificationsQueue');
        const data = filteredData || this.verifications.filter(v => v.status === 'pending');
        
        if (!data.length) {
            container.innerHTML = '<div class="empty-state">No hay verificaciones pendientes</div>';
            return;
        }
        
        container.innerHTML = data.map((v, index) => `
            <div class="verification-item" onclick="VerificationsModule.selectVerification(${index})">
                <div class="verif-header">
                    <span class="verif-type">${this.getTypeLabel(v.type)}</span>
                    <span class="status-badge ${v.status}">${this.getStatusLabel(v.status)}</span>
                </div>
                <div class="verif-user">@${AdminPanel.escapeHtml(v.username || 'N/A')}</div>
                <div class="verif-date">${AdminPanel.formatDateTime(v.createdAt)}</div>
            </div>
        `).join('');
    },
    
    getTypeLabel(type) {
        const labels = { identity: 'Identidad', address: 'Direccion', phone: 'Telefono', payment: 'Pago' };
        return labels[type] || type;
    },
    
    getStatusLabel(status) {
        const labels = { pending: 'Pendiente', approved: 'Aprobado', rejected: 'Rechazado' };
        return labels[status] || status;
    },
    
    selectVerification(index) {
        const v = this.verifications[index];
        if (!v) return;
        
        document.querySelectorAll('.verification-item').forEach((el, i) => {
            el.classList.toggle('active', i === index);
        });
        
        const panel = document.getElementById('verificationDetailPanel');
        panel.innerHTML = `
            <div class="verif-detail">
                <h4>${this.getTypeLabel(v.type)}</h4>
                <div class="detail-section">
                    <p><strong>Usuario:</strong> @${AdminPanel.escapeHtml(v.username || 'N/A')}</p>
                    <p><strong>Telegram ID:</strong> ${v.telegramId}</p>
                    <p><strong>Fecha:</strong> ${AdminPanel.formatDateTime(v.createdAt)}</p>
                </div>
                ${v.documents ? `
                <div class="detail-section">
                    <h5>Documentos</h5>
                    <div class="documents-grid">
                        ${v.documents.map(doc => `<img src="${doc}" class="doc-preview" onclick="window.open('${doc}')">`).join('')}
                    </div>
                </div>
                ` : ''}
                <div class="verif-actions">
                    <button class="btn-primary" onclick="VerificationsModule.approve(${index})">Aprobar</button>
                    <button class="btn-danger" onclick="VerificationsModule.reject(${index})">Rechazar</button>
                </div>
            </div>
        `;
    },
    
    setupFilters() {
        const typeFilter = document.getElementById('verifTypeFilter');
        const statusFilter = document.getElementById('verifStatusFilter');
        
        if (typeFilter) {
            typeFilter.addEventListener('change', () => this.applyFilters());
        }
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.applyFilters());
        }
    },
    
    applyFilters() {
        const type = document.getElementById('verifTypeFilter')?.value || '';
        const status = document.getElementById('verifStatusFilter')?.value || '';
        
        let filtered = this.verifications;
        if (type) filtered = filtered.filter(v => v.type === type);
        if (status) filtered = filtered.filter(v => v.status === status);
        
        this.renderQueue(filtered);
    },
    
    async approve(index) {
        const v = this.verifications[index];
        if (v) {
            v.status = 'approved';
            this.updateStats();
            this.renderQueue();
            AdminPanel.showToast('Verificacion aprobada', 'success');
        }
    },
    
    async reject(index) {
        const v = this.verifications[index];
        if (v) {
            v.status = 'rejected';
            this.updateStats();
            this.renderQueue();
            AdminPanel.showToast('Verificacion rechazada', 'info');
        }
    }
};

const ShadowModule = {
    sessions: [],
    
    async init() {
        await this.loadSessions();
    },
    
    async loadSessions() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/shadow-sessions');
            if (response.success) {
                this.sessions = response.sessions || [];
                this.renderSessions();
            }
        } catch (error) {
            console.error('Error loading shadow sessions:', error);
        }
    },
    
    async searchUser() {
        const query = document.getElementById('shadowUserSearch')?.value?.trim();
        if (!query) {
            AdminPanel.showToast('Ingresa un ID o username', 'warning');
            return;
        }
        
        try {
            const response = await AdminPanel.fetchAPI(`/api/admin/users/search?q=${encodeURIComponent(query)}`);
            if (response.success && response.users?.length) {
                this.showSearchResults(response.users);
            } else {
                AdminPanel.showToast('Usuario no encontrado', 'warning');
            }
        } catch (error) {
            console.error('Error searching user:', error);
        }
    },
    
    showSearchResults(users) {
        const container = document.getElementById('shadowSearchResults');
        container.style.display = 'block';
        
        container.innerHTML = users.map(user => `
            <div class="shadow-result-item">
                <div class="user-info">
                    <span class="user-name">${AdminPanel.escapeHtml(user.firstName || '')} @${AdminPanel.escapeHtml(user.username || 'N/A')}</span>
                    <span class="user-id">ID: ${user.telegramId}</span>
                </div>
                <button class="btn-primary" onclick="ShadowModule.startSession(${user.telegramId})">Impersonar</button>
            </div>
        `).join('');
    },
    
    async startSession(telegramId) {
        AdminPanel.showToast('Iniciando sesion shadow...', 'info');
        
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/shadow-sessions/start', {
                method: 'POST',
                body: JSON.stringify({ telegramId })
            });
            
            if (response.success && response.sessionUrl) {
                window.open(response.sessionUrl, '_blank');
                this.loadSessions();
            } else {
                AdminPanel.showToast(response.error || 'Error al iniciar sesion', 'error');
            }
        } catch (error) {
            console.error('Error starting shadow session:', error);
        }
    },
    
    renderSessions() {
        const container = document.getElementById('shadowSessionsList');
        
        if (!this.sessions.length) {
            container.innerHTML = '<div class="empty-state">Sin sesiones recientes</div>';
            return;
        }
        
        container.innerHTML = this.sessions.map(s => `
            <div class="session-item">
                <div class="session-info">
                    <span class="session-user">@${AdminPanel.escapeHtml(s.username || 'N/A')}</span>
                    <span class="session-admin">por ${AdminPanel.escapeHtml(s.adminUsername || 'Admin')}</span>
                </div>
                <div class="session-time">${AdminPanel.formatDateTime(s.startedAt)}</div>
            </div>
        `).join('');
    }
};

const MarketplaceModule = {
    listings: [],
    sales: [],
    
    async init() {
        await this.loadData();
        this.setupTabs();
    },
    
    async loadData() {
        try {
            const response = await AdminPanel.fetchAPI('/api/admin/marketplace');
            if (response.success) {
                this.listings = response.listings || [];
                this.sales = response.sales || [];
                this.updateStats();
                this.renderContent('pending');
            }
        } catch (error) {
            console.error('Error loading marketplace:', error);
        }
    },
    
    updateStats() {
        const active = this.listings.filter(l => l.status === 'active').length;
        const pending = this.listings.filter(l => l.status === 'pending').length;
        const totalSales = this.sales.length;
        const revenue = this.sales.reduce((sum, s) => sum + (s.commission || 0), 0);
        
        document.getElementById('marketActiveListings').textContent = active;
        document.getElementById('marketPendingApproval').textContent = pending;
        document.getElementById('marketTotalSales').textContent = totalSales;
        document.getElementById('marketRevenue').textContent = revenue.toFixed(4);
    },
    
    setupTabs() {
        document.querySelectorAll('#section-marketplace .marketplace-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#section-marketplace .marketplace-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.renderContent(btn.dataset.tab);
            });
        });
    },
    
    renderContent(tab) {
        const container = document.getElementById('marketplaceContent');
        
        if (tab === 'pending') {
            const pending = this.listings.filter(l => l.status === 'pending');
            container.innerHTML = this.renderListings(pending, true);
        } else if (tab === 'active') {
            const active = this.listings.filter(l => l.status === 'active');
            container.innerHTML = this.renderListings(active, false);
        } else if (tab === 'sales') {
            container.innerHTML = this.renderSales();
        }
    },
    
    renderListings(listings, showApproval) {
        if (!listings.length) {
            return '<div class="empty-state">No hay listings</div>';
        }
        
        return listings.map(l => `
            <div class="listing-item">
                <div class="listing-image-placeholder"></div>
                <div class="listing-info">
                    <div class="listing-title">${AdminPanel.escapeHtml(l.title || 'Sin titulo')}</div>
                    <div class="listing-price">${l.price || 0} ${l.currency || 'B3C'}</div>
                    <div class="listing-seller">@${AdminPanel.escapeHtml(l.sellerUsername || 'N/A')}</div>
                </div>
                <div class="listing-actions">
                    ${showApproval ? `
                        <button class="btn-primary btn-sm" onclick="MarketplaceModule.approveListing('${l.id}')">Aprobar</button>
                        <button class="btn-danger btn-sm" onclick="MarketplaceModule.rejectListing('${l.id}')">Rechazar</button>
                    ` : `
                        <button class="btn-secondary btn-sm" onclick="MarketplaceModule.viewListing('${l.id}')">Ver</button>
                    `}
                </div>
            </div>
        `).join('');
    },
    
    renderSales() {
        if (!this.sales.length) {
            return '<div class="empty-state">No hay ventas registradas</div>';
        }
        
        return `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Producto</th>
                        <th>Vendedor</th>
                        <th>Comprador</th>
                        <th>Monto</th>
                        <th>Comision</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.sales.map(s => `
                        <tr>
                            <td>${AdminPanel.formatDateTime(s.createdAt)}</td>
                            <td>${AdminPanel.escapeHtml(s.productTitle || 'N/A')}</td>
                            <td>@${AdminPanel.escapeHtml(s.sellerUsername || 'N/A')}</td>
                            <td>@${AdminPanel.escapeHtml(s.buyerUsername || 'N/A')}</td>
                            <td>${s.amount || 0} ${s.currency || 'B3C'}</td>
                            <td>${(s.commission || 0).toFixed(4)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },
    
    async approveListing(id) {
        const listing = this.listings.find(l => l.id === id);
        if (listing) {
            listing.status = 'active';
            this.updateStats();
            this.renderContent('pending');
            AdminPanel.showToast('Listing aprobado', 'success');
        }
    },
    
    async rejectListing(id) {
        const listing = this.listings.find(l => l.id === id);
        if (listing) {
            listing.status = 'rejected';
            this.updateStats();
            this.renderContent('pending');
            AdminPanel.showToast('Listing rechazado', 'info');
        }
    },
    
    viewListing(id) {
        AdminPanel.showToast('Abriendo detalle...', 'info');
    },
    
    configureCommissions() {
        AdminPanel.showToast('Configuracion de comisiones', 'info');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AdminPanel.init();
    
    const supportNav = document.querySelector('[data-section="support"]');
    if (supportNav) {
        supportNav.addEventListener('click', () => {
            setTimeout(() => SupportModule.init(), 100);
        });
    }
    
    const faqNav = document.querySelector('[data-section="faq"]');
    if (faqNav) {
        faqNav.addEventListener('click', () => {
            setTimeout(() => SupportModule.loadFAQs(), 100);
        });
    }
    
    const massMessagesNav = document.querySelector('[data-section="massmessages"]');
    if (massMessagesNav) {
        massMessagesNav.addEventListener('click', () => {
            setTimeout(() => SupportModule.loadMassMessages(), 100);
        });
    }
    
    const riskScoreNav = document.querySelector('[data-section="riskscore"]');
    if (riskScoreNav) {
        riskScoreNav.addEventListener('click', () => {
            setTimeout(() => RiskScoreModule.init(), 100);
        });
    }
    
    const relatedAccountsNav = document.querySelector('[data-section="relatedaccounts"]');
    if (relatedAccountsNav) {
        relatedAccountsNav.addEventListener('click', () => {
            setTimeout(() => RelatedAccountsModule.init(), 100);
        });
    }
    
    const anomaliesNav = document.querySelector('[data-section="anomalies"]');
    if (anomaliesNav) {
        anomaliesNav.addEventListener('click', () => {
            setTimeout(() => AnomaliesModule.init(), 100);
        });
    }
    
    const userTagsNav = document.querySelector('[data-section="usertags"]');
    if (userTagsNav) {
        userTagsNav.addEventListener('click', () => {
            setTimeout(() => TagsModule.init(), 100);
        });
    }
    
    const verificationsNav = document.querySelector('[data-section="verifications"]');
    if (verificationsNav) {
        verificationsNav.addEventListener('click', () => {
            setTimeout(() => VerificationsModule.init(), 100);
        });
    }
    
    const shadowModeNav = document.querySelector('[data-section="shadowmode"]');
    if (shadowModeNav) {
        shadowModeNav.addEventListener('click', () => {
            setTimeout(() => ShadowModule.init(), 100);
        });
    }
    
    const marketplaceNav = document.querySelector('[data-section="marketplace"]');
    if (marketplaceNav) {
        marketplaceNav.addEventListener('click', () => {
            setTimeout(() => MarketplaceModule.init(), 100);
        });
    }
});
