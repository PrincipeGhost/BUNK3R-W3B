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
        
        const usersPeriod = document.getElementById('usersChartPeriod')?.value || '30';
        const txPeriod = parseInt(document.getElementById('txChartPeriod')?.value || '7');
        
        try {
            const chartData = await this.fetchAPI(`/api/admin/dashboard/charts?period=${usersPeriod}`);
            
            if (chartData.success && chartData.data) {
                const usersLabels = chartData.data.users.map(d => d.label);
                const usersData = chartData.data.users.map(d => d.count);
                const txLabels = chartData.data.transactions.slice(-txPeriod).map(d => d.label);
                const txData = chartData.data.transactions.slice(-txPeriod).map(d => d.count);
                
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
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.initFallbackCharts(usersCtx, txCtx);
        }
    },
    
    initFallbackCharts(usersCtx, txCtx) {
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
        
        content.innerHTML = 'Cargando...';
        modal.classList.add('active');
        
        try {
            const response = await this.fetchAPI(`/api/admin/user/${userId}`);
            
            if (response.success && response.user) {
                const user = response.user;
                content.innerHTML = `
                    <div class="user-detail-header">
                        <div class="user-detail-avatar">${(user.first_name || 'U')[0].toUpperCase()}</div>
                        <div class="user-detail-info">
                            <h3>${this.escapeHtml(user.first_name || 'Sin nombre')}</h3>
                            <div class="username">@${this.escapeHtml(user.username || 'N/A')}</div>
                            <div class="user-id">ID: ${user.user_id}</div>
                        </div>
                    </div>
                    
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
                    </div>
                    
                    <div class="user-actions">
                        <button class="btn-secondary" onclick="AdminPanel.adjustBalance('${user.user_id}')">
                            Ajustar Balance
                        </button>
                        <button class="btn-secondary" onclick="AdminPanel.viewUserTransactions('${user.user_id}')">
                            Ver Transacciones
                        </button>
                        <button class="btn-danger" onclick="AdminPanel.banUser('${user.user_id}', ${!user.is_banned})">
                            ${user.is_banned ? 'Desbanear' : 'Banear Usuario'}
                        </button>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">Error al cargar usuario</div>';
            }
        } catch (error) {
            console.error('Error loading user:', error);
            content.innerHTML = '<div class="empty-state">Error al cargar usuario</div>';
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
            const [hotWallet, poolStats, depositWallets] = await Promise.all([
                this.fetchAPI('/api/admin/wallets/hot'),
                this.fetchAPI('/api/admin/wallet-pool/stats'),
                this.fetchAPI('/api/admin/wallets/deposits')
            ]);
            
            if (hotWallet.success) {
                document.getElementById('hwBalance').textContent = this.formatNumber(hotWallet.balance || 0, 4);
                document.getElementById('hwAddress').textContent = hotWallet.address || '-';
                document.getElementById('hotWalletLink').href = `https://tonscan.org/address/${hotWallet.address}`;
                
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
                this.renderDepositWallets(depositWallets.wallets);
            }
            
        } catch (error) {
            console.error('Error loading wallets:', error);
        }
    },
    
    renderDepositWallets(wallets) {
        const tbody = document.getElementById('depositWalletsBody');
        
        if (!wallets || wallets.length === 0) {
            tbody.innerHTML = '<tr class="loading-row"><td colspan="6">No hay wallets de depósito</td></tr>';
            return;
        }
        
        tbody.innerHTML = wallets.map(w => `
            <tr>
                <td style="font-family: monospace; font-size: 11px;">${w.wallet_address?.slice(0, 20)}...</td>
                <td><span class="status-badge ${w.status}">${w.status}</span></td>
                <td>${w.assigned_to_user_id || '-'}</td>
                <td>${w.expected_amount ? this.formatNumber(w.expected_amount, 4) + ' TON' : '-'}</td>
                <td>${w.balance ? this.formatNumber(w.balance, 4) + ' TON' : '-'}</td>
                <td>${this.formatDate(w.created_at)}</td>
            </tr>
        `).join('');
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
        try {
            const response = await this.fetchAPI('/api/admin/content/stats');
            
            if (response.success) {
                document.getElementById('totalPosts').textContent = this.formatNumber(response.totalPosts || 0);
                document.getElementById('postsToday').textContent = this.formatNumber(response.postsToday || 0);
                document.getElementById('totalMedia').textContent = this.formatNumber(response.totalMedia || 0);
            }
            
            const postsResponse = await this.fetchAPI('/api/admin/content/posts?limit=50');
            
            if (postsResponse.success && postsResponse.posts) {
                const tbody = document.getElementById('contentTableBody');
                
                if (postsResponse.posts.length === 0) {
                    tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No hay publicaciones</td></tr>';
                    return;
                }
                
                tbody.innerHTML = postsResponse.posts.map(post => `
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
                                <button class="action-btn danger" onclick="AdminPanel.deletePost(${post.id})">Eliminar</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading content:', error);
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
                    container.innerHTML = '<div class="empty-state">No hay reportes pendientes</div>';
                    return;
                }
                
                container.innerHTML = response.reports.map(report => `
                    <div class="report-item">
                        <div class="report-content">
                            <div class="report-header">
                                <strong>Reporte #${report.id}</strong>
                                <span class="status-badge ${report.status}">${report.status}</span>
                            </div>
                            <p>${this.escapeHtml(report.reason)}</p>
                            <div class="report-meta">
                                <span>Reportado por: ${this.escapeHtml(report.reporter_username || 'Anónimo')}</span>
                                <span>${this.formatDate(report.created_at)}</span>
                            </div>
                        </div>
                        <div class="report-actions">
                            <button class="action-btn" onclick="AdminPanel.reviewReport(${report.id}, 'reviewed')">Aprobar</button>
                            <button class="action-btn danger" onclick="AdminPanel.reviewReport(${report.id}, 'dismissed')">Descartar</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            container.innerHTML = '<div class="empty-state">Error al cargar reportes</div>';
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
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AdminPanel.init();
});
