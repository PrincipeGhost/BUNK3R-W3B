let tg = window.Telegram?.WebApp;
let initData = '';
let currentUser = null;
let userBalance = 0;
let selectedCountry = null;
let selectedService = null;
let countriesData = [];
let servicesData = [];
let activeOrders = [];
let checkInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    if (tg) {
        tg.ready();
        tg.expand();
        initData = tg.initData || '';
        tg.MainButton.hide();
    }
    
    if (!initData) {
        const urlParams = new URLSearchParams(window.location.search);
        initData = urlParams.get('initData') || '';
    }
    
    if (!initData) {
        console.error('No Telegram init data available');
        showToast('Error de autenticacion', 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }
    
    initApp();
});

async function initApp() {
    try {
        await loadUserBalance();
        await loadCountries();
        await loadActiveOrders();
        
        setupSearchFilters();
        
        startPolling();
    } catch (error) {
        console.error('Error initializing app:', error);
        showToast('Error al cargar', 'error');
    }
}

function setupSearchFilters() {
    const countrySearch = document.getElementById('country-search');
    const serviceSearch = document.getElementById('service-search');
    
    countrySearch.addEventListener('input', (e) => {
        filterItems('countries-list', countriesData, e.target.value, 'country');
    });
    
    serviceSearch.addEventListener('input', (e) => {
        filterItems('services-list', servicesData, e.target.value, 'service');
    });
}

function filterItems(containerId, data, query, type) {
    const container = document.getElementById(containerId);
    const filtered = data.filter(item => {
        const name = item.name?.toLowerCase() || '';
        return name.includes(query.toLowerCase());
    });
    
    if (type === 'country') {
        renderCountries(filtered);
    } else {
        renderServices(filtered);
    }
}

async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': initData
    };
    
    const response = await fetch(endpoint, {
        ...options,
        headers: { ...headers, ...options.headers }
    });
    
    return response.json();
}

async function loadUserBalance() {
    try {
        const result = await apiCall('/api/wallet/balance');
        if (result.success) {
            userBalance = result.balance || 0;
            document.getElementById('balance-amount').textContent = userBalance.toFixed(2);
        }
    } catch (error) {
        console.error('Error loading balance:', error);
    }
}

async function loadCountries() {
    const container = document.getElementById('countries-list');
    container.innerHTML = '<div class="empty-state"><div class="spinner"></div><p>Cargando...</p></div>';
    
    try {
        const result = await apiCall('/api/vn/countries?provider=smspool');
        if (result.success && result.countries) {
            countriesData = result.countries;
            renderCountries(countriesData);
        } else {
            container.innerHTML = '<div class="empty-state"><p>No hay paises disponibles</p></div>';
        }
    } catch (error) {
        console.error('Error loading countries:', error);
        container.innerHTML = '<div class="empty-state"><p>Error al cargar paises</p></div>';
    }
}

function renderCountries(countries) {
    const container = document.getElementById('countries-list');
    
    if (!countries || countries.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No se encontraron paises</p></div>';
        return;
    }
    
    container.innerHTML = countries.map(country => `
        <div class="country-item ${selectedCountry?.id === country.id ? 'selected' : ''}" 
             onclick="selectCountry('${country.id}', '${country.name}', '${country.flag || '🌍'}')">
            <div class="item-left">
                <span class="item-flag">${country.flag || '🌍'}</span>
                <span class="item-name">${country.name}</span>
            </div>
        </div>
    `).join('');
}

async function selectCountry(id, name, flag) {
    selectedCountry = { id, name, flag };
    selectedService = null;
    
    document.querySelectorAll('.country-item').forEach(el => el.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    document.getElementById('services-section').classList.remove('hidden');
    updatePurchaseButton();
    
    await loadServices(id);
}

async function loadServices(countryId) {
    const container = document.getElementById('services-list');
    container.innerHTML = '<div class="empty-state"><div class="spinner"></div><p>Cargando...</p></div>';
    
    try {
        const result = await apiCall(`/api/vn/services?provider=smspool&country=${countryId}`);
        if (result.success && result.services) {
            servicesData = result.services;
            renderServices(servicesData);
        } else {
            container.innerHTML = '<div class="empty-state"><p>No hay servicios disponibles</p></div>';
        }
    } catch (error) {
        console.error('Error loading services:', error);
        container.innerHTML = '<div class="empty-state"><p>Error al cargar servicios</p></div>';
    }
}

function renderServices(services) {
    const container = document.getElementById('services-list');
    
    if (!services || services.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No se encontraron servicios</p></div>';
        return;
    }
    
    container.innerHTML = services.map(service => `
        <div class="service-item ${selectedService?.id === service.id ? 'selected' : ''}" 
             onclick="selectService('${service.id}', '${service.name}', '${service.icon || '📱'}', ${service.price_bunkercoin || 0})">
            <div class="item-left">
                <span class="item-icon">${service.icon || '📱'}</span>
                <span class="item-name">${service.name}</span>
            </div>
            <div class="item-price">
                <span>🪙</span>
                <span>${(service.price_bunkercoin || 0).toFixed(2)}</span>
            </div>
        </div>
    `).join('');
}

function selectService(id, name, icon, price) {
    selectedService = { id, name, icon, price };
    
    document.querySelectorAll('.service-item').forEach(el => el.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    updatePurchaseButton();
}

function updatePurchaseButton() {
    const btn = document.getElementById('purchase-btn');
    
    if (selectedCountry && selectedService) {
        btn.disabled = false;
        btn.innerHTML = `
            <span>Comprar ${selectedService.name}</span>
            <span>🪙 ${selectedService.price.toFixed(2)}</span>
        `;
    } else if (selectedCountry) {
        btn.disabled = true;
        btn.innerHTML = '<span>Selecciona un servicio</span>';
    } else {
        btn.disabled = true;
        btn.innerHTML = '<span>Selecciona pais y servicio</span>';
    }
}

async function purchaseNumber() {
    if (!selectedCountry || !selectedService) {
        showToast('Selecciona pais y servicio', 'error');
        return;
    }
    
    if (userBalance < selectedService.price) {
        showToast('Saldo insuficiente', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const result = await apiCall('/api/vn/purchase', {
            method: 'POST',
            body: JSON.stringify({
                provider: 'smspool',
                country: selectedCountry.id,
                service: selectedService.id,
                countryName: selectedCountry.name,
                serviceName: selectedService.name
            })
        });
        
        if (result.success) {
            showToast('Numero comprado!', 'success');
            userBalance -= selectedService.price;
            document.getElementById('balance-amount').textContent = userBalance.toFixed(2);
            
            selectedCountry = null;
            selectedService = null;
            document.querySelectorAll('.country-item, .service-item').forEach(el => el.classList.remove('selected'));
            document.getElementById('services-section').classList.add('hidden');
            updatePurchaseButton();
            
            switchTab('active');
            await loadActiveOrders();
        } else {
            showToast(result.error || 'Error al comprar', 'error');
        }
    } catch (error) {
        console.error('Error purchasing:', error);
        showToast('Error de conexion', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadActiveOrders() {
    const container = document.getElementById('active-numbers-list');
    
    try {
        const result = await apiCall('/api/vn/active');
        if (result.success) {
            activeOrders = result.orders || [];
            renderActiveOrders(activeOrders);
        }
    } catch (error) {
        console.error('Error loading active orders:', error);
    }
}

function renderActiveOrders(orders) {
    const container = document.getElementById('active-numbers-list');
    
    if (!orders || orders.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📱</div>
                <h4>No hay numeros activos</h4>
                <p>Compra un numero para recibir SMS</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = orders.map(order => `
        <div class="number-card" data-order-id="${order.id}">
            <div class="number-header">
                <div class="number-service">
                    <div class="number-service-icon">📱</div>
                    <div class="number-service-info">
                        <h4>${order.service}</h4>
                        <span>${order.country}</span>
                    </div>
                </div>
                <div class="number-status ${order.status === 'received' ? 'status-received' : 'status-pending'}">
                    ${order.status === 'received' ? '✅ Recibido' : '⏳ Esperando'}
                </div>
            </div>
            
            <div class="phone-display">
                <span class="phone-number">${order.phoneNumber || 'Asignando...'}</span>
                <button class="copy-btn" onclick="copyToClipboard('${order.phoneNumber}')">
                    📋
                </button>
            </div>
            
            ${order.status === 'pending' || order.status === 'active' ? `
                <div class="waiting-indicator">
                    <div class="spinner"></div>
                    <span class="waiting-text">Esperando SMS...</span>
                </div>
            ` : ''}
            
            ${order.smsCode ? `
                <div class="sms-code-display">
                    <div class="sms-code-label">Codigo recibido</div>
                    <div class="sms-code">${order.smsCode}</div>
                    <button class="copy-btn" onclick="copyToClipboard('${order.smsCode}')" style="margin-top: 10px; width: auto; padding: 8px 16px; border-radius: 8px;">
                        📋 Copiar
                    </button>
                </div>
            ` : ''}
            
            ${order.status !== 'received' ? `
                <div class="number-actions">
                    <button class="action-btn primary" onclick="checkSMS('${order.id}')">
                        🔄 Verificar
                    </button>
                    <button class="action-btn danger" onclick="cancelOrder('${order.id}')">
                        ❌ Cancelar
                    </button>
                </div>
            ` : ''}
        </div>
    `).join('');
}

async function checkSMS(orderId) {
    try {
        const result = await apiCall(`/api/vn/check/${orderId}`);
        
        if (result.success) {
            if (result.status === 'received' && result.sms_code) {
                showToast('SMS recibido!', 'success');
                await loadActiveOrders();
            } else {
                showToast('Aun esperando SMS...', 'info');
            }
        } else {
            showToast(result.error || 'Error al verificar', 'error');
        }
    } catch (error) {
        console.error('Error checking SMS:', error);
        showToast('Error de conexion', 'error');
    }
}

async function cancelOrder(orderId) {
    if (!confirm('¿Cancelar este numero? Se procesara un reembolso parcial.')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const result = await apiCall(`/api/vn/cancel/${orderId}`, {
            method: 'POST'
        });
        
        if (result.success) {
            showToast(`Cancelado. Reembolso: ${result.refunded_amount?.toFixed(2) || 0} 🪙`, 'success');
            await loadUserBalance();
            await loadActiveOrders();
        } else {
            showToast(result.error || 'Error al cancelar', 'error');
        }
    } catch (error) {
        console.error('Error cancelling:', error);
        showToast('Error de conexion', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadHistory() {
    const container = document.getElementById('history-list');
    
    try {
        const result = await apiCall('/api/vn/history?limit=50');
        if (result.success) {
            renderHistory(result.orders || []);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function renderHistory(orders) {
    const container = document.getElementById('history-list');
    
    if (!orders || orders.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <h4>Sin historial</h4>
                <p>Tus compras apareceran aqui</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = orders.map(order => {
        const statusColors = {
            'received': 'background: rgba(72,187,120,0.2); color: #48bb78;',
            'cancelled': 'background: rgba(252,129,129,0.2); color: #fc8181;',
            'expired': 'background: rgba(160,174,192,0.2); color: #a0aec0;',
            'active': 'background: rgba(246,173,85,0.2); color: #f6ad55;',
            'pending': 'background: rgba(246,173,85,0.2); color: #f6ad55;'
        };
        
        const statusLabels = {
            'received': 'Recibido',
            'cancelled': 'Cancelado',
            'expired': 'Expirado',
            'active': 'Activo',
            'pending': 'Pendiente'
        };
        
        return `
            <div class="history-item">
                <div class="history-left">
                    <div class="history-icon">📱</div>
                    <div class="history-info">
                        <h5>${order.service}</h5>
                        <span>${order.country} • ${order.phoneNumber || 'N/A'}</span>
                    </div>
                </div>
                <div class="history-right">
                    <div class="history-cost">-${order.cost?.toFixed(2) || 0} 🪙</div>
                    <div class="history-status" style="${statusColors[order.status] || ''}">
                        ${statusLabels[order.status] || order.status}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    document.getElementById('tab-purchase').classList.toggle('hidden', tabName !== 'purchase');
    document.getElementById('tab-active').classList.toggle('hidden', tabName !== 'active');
    document.getElementById('tab-history').classList.toggle('hidden', tabName !== 'history');
    
    if (tabName === 'active') {
        loadActiveOrders();
    } else if (tabName === 'history') {
        loadHistory();
    }
}

function startPolling() {
    if (checkInterval) {
        clearInterval(checkInterval);
    }
    
    checkInterval = setInterval(async () => {
        const activeTab = document.querySelector('.tab.active')?.dataset.tab;
        if (activeTab === 'active' && activeOrders.length > 0) {
            for (const order of activeOrders) {
                if (order.status === 'pending' || order.status === 'active') {
                    try {
                        const result = await apiCall(`/api/vn/check/${order.id}`);
                        if (result.success && result.status === 'received') {
                            showToast('SMS recibido!', 'success');
                            await loadActiveOrders();
                            break;
                        }
                    } catch (e) {
                        console.error('Polling error:', e);
                    }
                }
            }
        }
    }, 5000);
}

function copyToClipboard(text) {
    if (!text) return;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => showToast('Copiado!', 'success'))
            .catch(() => fallbackCopy(text));
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showToast('Copiado!', 'success');
    } catch (e) {
        showToast('No se pudo copiar', 'error');
    }
    document.body.removeChild(textarea);
}

function showLoading(show) {
    document.getElementById('loading-overlay').classList.toggle('hidden', !show);
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function goBack() {
    if (tg) {
        tg.close();
    } else {
        window.location.href = '/';
    }
}

window.addEventListener('beforeunload', () => {
    if (checkInterval) {
        clearInterval(checkInterval);
    }
});
