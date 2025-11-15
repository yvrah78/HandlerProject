// =====================================================
// PROJECT HANDLER - FRONTEND APPLICATION
// Complete functional implementation with backend integration
// =====================================================

// Configuration
const API_BASE_URL = (() => {
    if (window.location.hostname.includes('onrender.com')) {
        return 'https://project-handler-api.onrender.com';
    }
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    return `http://${window.location.hostname}:8000`;
})();

// =====================================================
// AUTHENTICATION MANAGEMENT
// =====================================================

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
    }

    isAuthenticated() {
        return !!this.token;
    }

    getToken() {
        return this.token;
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }

    clearToken() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
    }

    async login(username, password) {
        const response = await apiCall('/api/v1/auth/login', 'POST', {
            username,
            password
        }, false);

        if (response.access_token) {
            this.setToken(response.access_token);
            await this.loadUserInfo();
            return true;
        }
        return false;
    }

    async register(userData) {
        const response = await apiCall('/api/v1/auth/register', 'POST', userData, false);
        return response;
    }

    async loadUserInfo() {
        if (!this.isAuthenticated()) return null;

        try {
            this.user = await apiCall('/api/v1/auth/me', 'GET');
            return this.user;
        } catch (error) {
            console.error('Failed to load user info:', error);
            this.clearToken();
            return null;
        }
    }

    logout() {
        this.clearToken();
        showToast('Sesión cerrada exitosamente', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 500);
    }
}

// Global auth instance
const auth = new AuthManager();

// =====================================================
// API COMMUNICATION
// =====================================================

async function apiCall(endpoint, method = 'GET', data = null, requiresAuth = true) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json'
    };

    // Add authentication header if required
    if (requiresAuth && auth.isAuthenticated()) {
        headers['Authorization'] = `Bearer ${auth.getToken()}`;
    }

    const options = {
        method,
        headers
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);

        // Handle 401 Unauthorized
        if (response.status === 401 && requiresAuth) {
            auth.clearToken();
            showToast('Sesión expirada. Por favor inicia sesión nuevamente.', 'error');
            showLoginPage();
            throw new Error('Unauthorized');
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || 'Request failed');
        }

        return responseData;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// =====================================================
// CUSTOMERS API
// =====================================================

async function createCustomer(customerData) {
    return await apiCall('/api/v1/customers', 'POST', customerData);
}

async function listCustomers(page = 1, pageSize = 50, search = null) {
    let endpoint = `/api/v1/customers?page=${page}&page_size=${pageSize}`;
    if (search) {
        endpoint += `&search=${encodeURIComponent(search)}`;
    }
    return await apiCall(endpoint, 'GET');
}

async function getCustomer(customerId) {
    return await apiCall(`/api/v1/customers/${customerId}`, 'GET');
}

async function updateCustomer(customerId, customerData) {
    return await apiCall(`/api/v1/customers/${customerId}`, 'PUT', customerData);
}

async function deleteCustomer(customerId) {
    return await apiCall(`/api/v1/customers/${customerId}`, 'DELETE');
}

// =====================================================
// BOOKINGS API
// =====================================================

async function createBooking(bookingData) {
    return await apiCall('/api/v1/bookings', 'POST', bookingData);
}

async function listBookings(page = 1, pageSize = 50, customerId = null, status = null) {
    let endpoint = `/api/v1/bookings?page=${page}&page_size=${pageSize}`;
    if (customerId) {
        endpoint += `&customer_id=${customerId}`;
    }
    if (status) {
        endpoint += `&status=${status}`;
    }
    return await apiCall(endpoint, 'GET');
}

async function getBooking(bookingId) {
    return await apiCall(`/api/v1/bookings/${bookingId}`, 'GET');
}

async function updateBooking(bookingId, bookingData) {
    return await apiCall(`/api/v1/bookings/${bookingId}`, 'PUT', bookingData);
}

async function cancelBooking(bookingId, reason = null) {
    let endpoint = `/api/v1/bookings/${bookingId}`;
    if (reason) {
        endpoint += `?reason=${encodeURIComponent(reason)}`;
    }
    return await apiCall(endpoint, 'DELETE');
}

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', async () => {
    await initializeApp();
});

async function initializeApp() {
    // Check if user is authenticated
    if (!auth.isAuthenticated()) {
        showLoginPage();
        return;
    }

    // Load user info
    await auth.loadUserInfo();

    if (!auth.user) {
        showLoginPage();
        return;
    }

    // Setup authenticated app
    setupNavigation();
    setupForms();
    updateUIForAuthenticatedUser();
    await checkAPIStatus();
    await loadDashboardData();
}

function updateUIForAuthenticatedUser() {
    const headerActions = document.querySelector('.header-actions');

    // Add user info and logout button
    const userInfo = document.createElement('div');
    userInfo.className = 'user-info';
    userInfo.innerHTML = `
        <span class="user-name">👤 ${auth.user.full_name || auth.user.username}</span>
        <button class="btn btn-logout" onclick="handleLogout()">Cerrar Sesión</button>
    `;

    headerActions.insertBefore(userInfo, headerActions.firstChild);
}

// =====================================================
// LOGIN & REGISTER
// =====================================================

function showLoginPage() {
    const mainContent = document.querySelector('.main-content');
    mainContent.innerHTML = `
        <div class="auth-container">
            <div class="auth-card">
                <div class="logo">
                    <h2>📦 Project Handler</h2>
                    <p>Sistema de Gestión de Transporte</p>
                </div>

                <div id="loginForm" class="auth-form active">
                    <h3>Iniciar Sesión</h3>
                    <form onsubmit="handleLogin(event)">
                        <div class="form-group">
                            <label>Usuario</label>
                            <input type="text" id="login_username" required autofocus>
                        </div>
                        <div class="form-group">
                            <label>Contraseña</label>
                            <input type="password" id="login_password" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">Iniciar Sesión</button>
                    </form>
                    <p class="auth-switch">
                        ¿No tienes cuenta? <a href="#" onclick="showRegisterForm()">Regístrate aquí</a>
                    </p>
                </div>

                <div id="registerForm" class="auth-form">
                    <h3>Crear Cuenta</h3>
                    <form onsubmit="handleRegister(event)">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Nombre Completo</label>
                                <input type="text" id="register_fullname" required>
                            </div>
                            <div class="form-group">
                                <label>Usuario</label>
                                <input type="text" id="register_username" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Email</label>
                                <input type="email" id="register_email" required>
                            </div>
                            <div class="form-group">
                                <label>Teléfono</label>
                                <input type="tel" id="register_phone">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Contraseña</label>
                            <input type="password" id="register_password" required minlength="6">
                        </div>
                        <div class="form-group">
                            <label>Rol</label>
                            <select id="register_role" required>
                                <option value="user">Usuario</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">Registrarse</button>
                    </form>
                    <p class="auth-switch">
                        ¿Ya tienes cuenta? <a href="#" onclick="showLoginForm()">Inicia sesión aquí</a>
                    </p>
                </div>
            </div>
        </div>
    `;
}

function showRegisterForm() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('registerForm').classList.add('active');
}

function showLoginForm() {
    document.getElementById('registerForm').classList.remove('active');
    document.getElementById('loginForm').classList.add('active');
}

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('login_username').value;
    const password = document.getElementById('login_password').value;

    try {
        const success = await auth.login(username, password);
        if (success) {
            showToast('Inicio de sesión exitoso', 'success');
            window.location.reload();
        }
    } catch (error) {
        showToast(error.message || 'Error al iniciar sesión', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();

    const userData = {
        full_name: document.getElementById('register_fullname').value,
        username: document.getElementById('register_username').value,
        email: document.getElementById('register_email').value,
        phone: document.getElementById('register_phone').value || null,
        password: document.getElementById('register_password').value,
        role: document.getElementById('register_role').value
    };

    try {
        await auth.register(userData);
        showToast('Registro exitoso. Ahora puedes iniciar sesión.', 'success');
        showLoginForm();

        // Pre-fill username
        document.getElementById('login_username').value = userData.username;
    } catch (error) {
        showToast(error.message || 'Error al registrarse', 'error');
    }
}

function handleLogout() {
    auth.logout();
}

// =====================================================
// NAVIGATION
// =====================================================

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            await showPage(page);

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

async function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    const page = document.getElementById(`${pageName}-page`);
    if (page) {
        page.classList.add('active');

        const titles = {
            'dashboard': 'Dashboard',
            'bookings': 'Gestión de Bookings',
            'customers': 'Gestión de Clientes',
            'agents': 'Sistema Multi-Agente',
            'api': 'Documentación API'
        };
        document.getElementById('pageTitle').textContent = titles[pageName] || pageName;

        // Load data for specific pages
        if (pageName === 'bookings') {
            await loadBookingsList();
        } else if (pageName === 'customers') {
            await loadCustomersList();
        }
    }
}

// =====================================================
// API STATUS CHECK
// =====================================================

async function checkAPIStatus() {
    const statusDot = document.getElementById('apiStatus');
    const statusText = document.getElementById('apiStatusText');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`);
        const data = await response.json();

        if (response.ok && data.status === 'healthy') {
            statusDot.classList.remove('offline');
            statusText.textContent = 'API Conectada';
            return true;
        }
    } catch (error) {
        statusDot.classList.add('offline');
        statusText.textContent = 'API Desconectada';
        showToast('Error de conexión con la API', 'error');
        return false;
    }
}

// =====================================================
// DASHBOARD
// =====================================================

async function loadDashboardData() {
    try {
        // Load system info
        const infoResponse = await fetch(`${API_BASE_URL}/info`);
        const infoData = await infoResponse.json();

        if (infoResponse.ok) {
            displaySystemInfo(infoData);
        }

        // Load real statistics
        const [customersData, bookingsData] = await Promise.all([
            listCustomers(1, 1),
            listBookings(1, 1)
        ]);

        document.getElementById('totalCustomers').textContent = customersData.total || '0';
        document.getElementById('totalBookings').textContent = bookingsData.total || '0';
        document.getElementById('totalInvoices').textContent = '0'; // TODO: Implement invoices
        document.getElementById('activeAgents').textContent = infoData.agents?.length || '5';

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Error cargando datos del dashboard', 'error');
    }
}

function displaySystemInfo(data) {
    const systemInfoDiv = document.getElementById('systemInfo');
    systemInfoDiv.innerHTML = `
        <div style="display: grid; gap: 1rem;">
            <div><strong>Nombre:</strong> ${data.name || 'N/A'}</div>
            <div><strong>Versión:</strong> ${data.version || 'N/A'}</div>
            <div><strong>Descripción:</strong> ${data.description || 'N/A'}</div>
            <div>
                <strong>Características:</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    ${data.features?.map(f => `<li>${f}</li>`).join('') || '<li>No disponible</li>'}
                </ul>
            </div>
            <div>
                <strong>Agentes Disponibles:</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    ${data.agents?.map(a => `<li>${a}</li>`).join('') || '<li>No disponible</li>'}
                </ul>
            </div>
        </div>
    `;
}

// =====================================================
// FORMS SETUP
// =====================================================

function setupForms() {
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }

    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        customerForm.addEventListener('submit', handleCustomerSubmit);
    }
}

// =====================================================
// CUSTOMERS
// =====================================================

async function handleCustomerSubmit(e) {
    e.preventDefault();

    const customerData = {
        name: document.getElementById('customer_name').value,
        email: document.getElementById('customer_email').value,
        phone: document.getElementById('customer_phone').value,
        company: document.getElementById('customer_company').value || null,
        address: document.getElementById('customer_address').value || null
    };

    try {
        const result = await createCustomer(customerData);
        showToast('Cliente creado exitosamente', 'success');
        e.target.reset();

        // Reload customers list
        await loadCustomersList();
    } catch (error) {
        showToast(error.message || 'Error al crear cliente', 'error');
    }
}

async function loadCustomersList() {
    const customersList = document.getElementById('customersList');
    if (!customersList) return;

    customersList.innerHTML = '<p class="loading">Cargando clientes...</p>';

    try {
        const data = await listCustomers(1, 20);

        if (data.items.length === 0) {
            customersList.innerHTML = '<p class="text-muted">No hay clientes registrados aún.</p>';
            return;
        }

        const table = `
            <div class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Teléfono</th>
                            <th>Empresa</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(customer => `
                            <tr>
                                <td>${customer.id}</td>
                                <td>${customer.name}</td>
                                <td>${customer.email}</td>
                                <td>${customer.phone || '-'}</td>
                                <td>${customer.company || '-'}</td>
                                <td>
                                    <span class="badge ${customer.is_active ? 'badge-success' : 'badge-inactive'}">
                                        ${customer.is_active ? 'Activo' : 'Inactivo'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn-icon" onclick="viewCustomer(${customer.id})" title="Ver detalles">👁️</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div class="pagination-info">
                    Mostrando ${data.items.length} de ${data.total} clientes
                </div>
            </div>
        `;

        customersList.innerHTML = table;

    } catch (error) {
        customersList.innerHTML = '<p class="text-error">Error al cargar clientes</p>';
        console.error('Error loading customers:', error);
    }
}

async function viewCustomer(customerId) {
    try {
        const customer = await getCustomer(customerId);
        alert(`Cliente: ${customer.name}\nEmail: ${customer.email}\nTeléfono: ${customer.phone || 'N/A'}\nEmpresa: ${customer.company || 'N/A'}`);
    } catch (error) {
        showToast('Error al cargar detalles del cliente', 'error');
    }
}

// =====================================================
// BOOKINGS
// =====================================================

async function handleBookingSubmit(e) {
    e.preventDefault();

    const pickupDatetime = document.getElementById('booking_pickup').value;

    const bookingData = {
        customer_id: parseInt(document.getElementById('booking_customer_id').value),
        origin: document.getElementById('booking_origin').value,
        destination: document.getElementById('booking_destination').value,
        pickup_datetime: pickupDatetime,
        cargo_weight: parseFloat(document.getElementById('booking_weight').value) || null,
        cargo_description: document.getElementById('booking_description').value || null
    };

    try {
        const result = await createBooking(bookingData);
        showToast(`Booking creado exitosamente: ${result.booking_number}`, 'success');
        e.target.reset();

        // Reload bookings list
        await loadBookingsList();

        // Update dashboard stats
        await loadDashboardData();
    } catch (error) {
        showToast(error.message || 'Error al crear booking', 'error');
    }
}

async function loadBookingsList() {
    const bookingsList = document.getElementById('bookingsList');
    if (!bookingsList) return;

    bookingsList.innerHTML = '<p class="loading">Cargando bookings...</p>';

    try {
        const data = await listBookings(1, 20);

        if (data.items.length === 0) {
            bookingsList.innerHTML = '<p class="text-muted">No hay bookings registrados aún.</p>';
            return;
        }

        const statusColors = {
            'PENDING': 'badge-warning',
            'CONFIRMED': 'badge-info',
            'IN_TRANSIT': 'badge-primary',
            'COMPLETED': 'badge-success',
            'CANCELLED': 'badge-danger'
        };

        const statusLabels = {
            'PENDING': 'Pendiente',
            'CONFIRMED': 'Confirmado',
            'IN_TRANSIT': 'En Tránsito',
            'COMPLETED': 'Completado',
            'CANCELLED': 'Cancelado'
        };

        const table = `
            <div class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Número</th>
                            <th>Cliente ID</th>
                            <th>Origen</th>
                            <th>Destino</th>
                            <th>Fecha Recogida</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(booking => `
                            <tr>
                                <td><strong>${booking.booking_number}</strong></td>
                                <td>${booking.customer_id}</td>
                                <td>${booking.origin}</td>
                                <td>${booking.destination}</td>
                                <td>${formatDate(booking.pickup_datetime)}</td>
                                <td>
                                    <span class="badge ${statusColors[booking.status] || 'badge-secondary'}">
                                        ${statusLabels[booking.status] || booking.status}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn-icon" onclick="viewBooking(${booking.id})" title="Ver detalles">👁️</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div class="pagination-info">
                    Mostrando ${data.items.length} de ${data.total} bookings
                </div>
            </div>
        `;

        bookingsList.innerHTML = table;

    } catch (error) {
        bookingsList.innerHTML = '<p class="text-error">Error al cargar bookings</p>';
        console.error('Error loading bookings:', error);
    }
}

async function viewBooking(bookingId) {
    try {
        const booking = await getBooking(bookingId);
        const details = `
Booking: ${booking.booking_number}
Cliente ID: ${booking.customer_id}
Origen: ${booking.origin}
Destino: ${booking.destination}
Fecha Recogida: ${formatDate(booking.pickup_datetime)}
Peso: ${booking.cargo_weight ? booking.cargo_weight + ' kg' : 'N/A'}
Estado: ${booking.status}
        `.trim();
        alert(details);
    } catch (error) {
        showToast('Error al cargar detalles del booking', 'error');
    }
}

// =====================================================
// AGENTS (Demo - will be implemented in AI modules)
// =====================================================

async function testAgent(agentType) {
    const outputDiv = document.getElementById('agentTestOutput');
    const resultPre = document.getElementById('agentTestResult');

    outputDiv.style.display = 'block';
    resultPre.textContent = 'Probando agente...';
    outputDiv.scrollIntoView({ behavior: 'smooth' });

    const demoResponse = {
        success: true,
        agent: agentType,
        result: {
            message: `${agentType} agent ejecutado exitosamente (demo)`,
            status: 'completed',
            note: 'Los agentes se implementarán completamente en los módulos AI1-AI4'
        },
        timestamp: new Date().toISOString()
    };

    resultPre.textContent = JSON.stringify(demoResponse, null, 2);
    showToast(`Agente ${agentType} probado (demo)`, 'success');
}

// =====================================================
// UTILITY FUNCTIONS
// =====================================================

async function refreshPage() {
    showToast('Actualizando...', 'success');
    await checkAPIStatus();
    await loadDashboardData();

    // Reload current page data
    const activePage = document.querySelector('.page.active');
    if (activePage) {
        if (activePage.id === 'customers-page') {
            await loadCustomersList();
        } else if (activePage.id === 'bookings-page') {
            await loadBookingsList();
        }
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// =====================================================
// GLOBAL EXPORTS
// =====================================================

window.showPage = showPage;
window.refreshPage = refreshPage;
window.testAgent = testAgent;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.handleLogout = handleLogout;
window.showRegisterForm = showRegisterForm;
window.showLoginForm = showLoginForm;
window.viewCustomer = viewCustomer;
window.viewBooking = viewBooking;

console.log('Project Handler Frontend initialized');
console.log('API Base URL:', API_BASE_URL);
console.log('Authenticated:', auth.isAuthenticated());
