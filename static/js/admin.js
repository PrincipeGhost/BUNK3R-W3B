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
            settings: 'Configuración'
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
        try {
            const [stats, activity, alerts] = await Promise.all([
                this.fetchAPI('/api/admin/dashboard/stats'),
                this.fetchAPI('/api/admin/dashboard/activity'),
                this.fetchAPI('/api/admin/dashboard/alerts')
            ]);
            
            if (stats.success) {
                this.updateMetrics(stats.data);
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
    
    loadFallbackDashboard() {
        document.getElementById('totalUsers').textContent = '-';
        document.getElementById('activeToday').textContent = '-';
        document.getElementById('totalB3C').textContent = '-';
        document.getElementById('hotWalletBalance').textContent = '-';
        document.getElementById('transactions24h').textContent = '-';
        document.getElementById('revenueToday').textContent = '-';
        
        document.getElementById('activityList').innerHTML = `
            <div class="empty-state">No se pudo cargar la actividad</div>
        `;
    },
    
    updateMetrics(data) {
        document.getElementById('totalUsers').textContent = this.formatNumber(data.totalUsers || 0);
        document.getElementById('activeToday').textContent = this.formatNumber(data.activeToday || 0);
        document.getElementById('totalB3C').textContent = this.formatNumber(data.totalB3C || 0);
        document.getElementById('hotWalletBalance').textContent = this.formatNumber(data.hotWalletBalance || 0, 2);
        document.getElementById('transactions24h').textContent = this.formatNumber(data.transactions24h || 0);
        document.getElementById('revenueToday').textContent = this.formatNumber(data.revenueToday || 0, 4);
        
        const usersChange = data.usersChange || 0;
        const changeEl = document.getElementById('usersChange');
        if (changeEl) {
            changeEl.className = `metric-change ${usersChange >= 0 ? 'positive' : 'negative'}`;
            changeEl.querySelector('span').textContent = `${usersChange >= 0 ? '+' : ''}${usersChange}%`;
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
        
        tbody.innerHTML = users.map(user => `
            <tr>
                <td><code>${user.user_id}</code></td>
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
                        <button class="action-btn" onclick="AdminPanel.viewUser('${user.user_id}')">Ver</button>
                        <button class="action-btn danger" onclick="AdminPanel.banUser('${user.user_id}', ${!user.is_banned})">
                            ${user.is_banned ? 'Desbanear' : 'Banear'}
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
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
                    
                    <div class="user-actions">
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
        const tbody = document.getElementById('sessionsTableBody');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Cargando sesiones...</td></tr>';
        
        try {
            const response = await this.fetchAPI('/api/admin/sessions');
            
            if (response.success && response.sessions) {
                document.getElementById('totalSessions').textContent = response.total || 0;
                document.getElementById('uniqueIPs').textContent = response.uniqueIPs || 0;
                
                if (response.sessions.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay sesiones activas</td></tr>';
                    return;
                }
                
                tbody.innerHTML = response.sessions.map(s => `
                    <tr>
                        <td>
                            <div class="user-cell">
                                <div class="user-avatar-sm">${(s.first_name || 'U')[0].toUpperCase()}</div>
                                <span>@${this.escapeHtml(s.username || 'N/A')}</span>
                            </div>
                        </td>
                        <td>${s.ip_address || '-'}</td>
                        <td>${this.escapeHtml(s.device_info?.slice(0, 30) || '-')}...</td>
                        <td>${this.timeAgo(s.last_activity)}</td>
                        <td>${this.formatDuration(s.duration)}</td>
                        <td>
                            <button class="action-btn danger" onclick="AdminPanel.terminateSession('${s.session_id}')">
                                Cerrar
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">Error al cargar sesiones</td></tr>';
        }
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
            const response = await this.fetchAPI('/api/admin/settings');
            
            if (response.success) {
                document.getElementById('currentB3CPrice').textContent = `$${response.b3cPrice || 0.10}`;
                document.getElementById('txCommission').value = response.commission || 5;
                document.getElementById('minWithdrawal').value = response.minWithdrawal || 10;
                document.getElementById('maintenanceMode').checked = response.maintenanceMode || false;
                document.getElementById('maintenanceMessage').value = response.maintenanceMessage || '';
                
                if (response.systemStatus) {
                    document.getElementById('dbStatus').textContent = response.systemStatus.database ? 'Conectada' : 'Error';
                    document.getElementById('dbStatus').className = `status-indicator ${response.systemStatus.database ? 'ok' : 'error'}`;
                    
                    document.getElementById('tonStatus').textContent = response.systemStatus.tonCenter ? 'Conectado' : 'Error';
                    document.getElementById('tonStatus').className = `status-indicator ${response.systemStatus.tonCenter ? 'ok' : 'error'}`;
                    
                    document.getElementById('smsStatus').textContent = response.systemStatus.smsPool ? 'Conectado' : 'Error';
                    document.getElementById('smsStatus').className = `status-indicator ${response.systemStatus.smsPool ? 'ok' : 'error'}`;
                }
                
                if (response.secrets) {
                    const secretsList = document.getElementById('secretsList');
                    secretsList.innerHTML = response.secrets.map(s => `
                        <div class="secret-item">
                            <span class="secret-name">${s.name}</span>
                            <span class="secret-status ${s.configured ? 'configured' : 'missing'}">
                                ${s.configured ? 'Configurado' : 'No configurado'}
                            </span>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
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
    
    async fetchAPI(url, options = {}) {
        const token = this.getDemoSessionToken();
        const headers = {
            'Content-Type': 'application/json',
            'X-Demo-Mode': 'true'
        };
        
        if (token) {
            headers['X-Demo-Session'] = token;
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
        
        const modal = document.createElement('div');
        modal.id = 'admin2FAModal';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.8);';
        modal.innerHTML = `
            <div style="background: #1E2329; border-radius: 16px; max-width: 400px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
                <div style="padding: 20px 24px; border-bottom: 1px solid #2B3139;">
                    <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: #EAECEF;">Verificación 2FA</h2>
                </div>
                <div style="padding: 24px;">
                    <p style="color: #848E9C; margin: 0 0 16px 0; font-size: 14px;">
                        Ingresa el código 2FA que aparece en la consola del servidor (Logs).
                    </p>
                    <input type="text" id="admin2FACode" placeholder="Código de 6 dígitos" 
                           style="width: 100%; padding: 12px; font-size: 18px; text-align: center; letter-spacing: 8px; border: 1px solid #2B3139; border-radius: 8px; background: #0B0E11; color: #EAECEF; box-sizing: border-box;"
                           maxlength="6" autocomplete="off">
                    <button id="admin2FASubmit" style="width: 100%; margin-top: 16px; padding: 12px; background: #F0B90B; color: #000; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                        Verificar
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
            const response = await fetch('/api/demo/2fa/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Demo-Mode': 'true' },
                body: JSON.stringify({ code })
            });
            
            const data = await response.json();
            
            const token = data.sessionToken || data.session_token;
            if (data.success && token) {
                this.demoSessionToken = token;
                localStorage.setItem('demo_session_token', token);
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
});
