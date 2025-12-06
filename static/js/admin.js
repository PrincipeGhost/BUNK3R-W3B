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
            logs: 'Logs',
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
            case 'logs':
                this.loadLogs();
                break;
            case 'settings':
                this.loadSettings();
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
        
        document.querySelectorAll('.logs-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.logs-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.loadLogs(btn.dataset.log);
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
    
    async loadLogs(logType = 'admin') {
        const container = document.getElementById('logsContainer');
        container.innerHTML = '<div class="log-entry">Cargando logs...</div>';
        
        try {
            const response = await this.fetchAPI(`/api/admin/logs?type=${logType}&limit=100`);
            
            if (response.success && response.logs) {
                if (response.logs.length === 0) {
                    container.innerHTML = '<div class="log-entry">No hay logs disponibles</div>';
                    return;
                }
                
                container.innerHTML = response.logs.map(log => `
                    <div class="log-entry">
                        <span class="log-time">${this.formatDateTime(log.timestamp)}</span>
                        <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
                        <span class="log-message">${this.escapeHtml(log.message)}</span>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            container.innerHTML = '<div class="log-entry">Error al cargar logs</div>';
        }
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
    
    async fetchAPI(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            'X-Demo-Mode': 'true'
        };
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: error.message };
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
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AdminPanel.init();
});
