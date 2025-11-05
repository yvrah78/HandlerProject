// Configuration
// Use the server IP for remote access, or localhost for local development
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'http://21.0.0.158:8000';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize application
async function initializeApp() {
    setupNavigation();
    setupForms();
    await checkAPIStatus();
    await loadDashboardData();
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            showPage(page);

            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show selected page
    const page = document.getElementById(`${pageName}-page`);
    if (page) {
        page.classList.add('active');

        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'bookings': 'Gestión de Bookings',
            'customers': 'Gestión de Clientes',
            'agents': 'Sistema Multi-Agente',
            'api': 'Documentación API'
        };
        document.getElementById('pageTitle').textContent = titles[pageName] || pageName;
    }
}

// API Status Check
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
        showToast('Error de conexión con la API. Asegúrate de que el servidor esté corriendo.', 'error');
        return false;
    }
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        // Get system info
        const infoResponse = await fetch(`${API_BASE_URL}/info`);
        const infoData = await infoResponse.json();

        if (infoResponse.ok) {
            displaySystemInfo(infoData);
        }

        // Update stats (these will be real data when endpoints are implemented)
        document.getElementById('totalBookings').textContent = '0';
        document.getElementById('totalCustomers').textContent = '0';
        document.getElementById('totalInvoices').textContent = '0';
        document.getElementById('activeAgents').textContent = infoData.agents?.length || '5';

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function displaySystemInfo(data) {
    const systemInfoDiv = document.getElementById('systemInfo');
    systemInfoDiv.innerHTML = `
        <div style="display: grid; gap: 1rem;">
            <div>
                <strong>Nombre:</strong> ${data.name || 'N/A'}
            </div>
            <div>
                <strong>Versión:</strong> ${data.version || 'N/A'}
            </div>
            <div>
                <strong>Descripción:</strong> ${data.description || 'N/A'}
            </div>
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

// Setup Forms
function setupForms() {
    // Booking Form
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }

    // Customer Form
    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        customerForm.addEventListener('submit', handleCustomerSubmit);
    }
}

// Handle Booking Submission (Demo)
async function handleBookingSubmit(e) {
    e.preventDefault();

    const bookingData = {
        customer_id: parseInt(document.getElementById('booking_customer_id').value),
        origin: document.getElementById('booking_origin').value,
        destination: document.getElementById('booking_destination').value,
        pickup_datetime: document.getElementById('booking_pickup').value,
        cargo_weight: parseFloat(document.getElementById('booking_weight').value) || null,
        cargo_description: document.getElementById('booking_description').value || null
    };

    console.log('Booking Data:', bookingData);

    // Note: This is a demo. The actual endpoint will be implemented in Module F4
    showToast('Booking creado (demo). Los endpoints CRUD se implementarán en el Módulo F4.', 'success');

    // Reset form
    e.target.reset();

    // In a real implementation, you would do:
    // try {
    //     const response = await fetch(`${API_BASE_URL}/api/v1/bookings`, {
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify(bookingData)
    //     });
    //     const result = await response.json();
    //     if (response.ok) {
    //         showToast('Booking creado exitosamente', 'success');
    //         e.target.reset();
    //     }
    // } catch (error) {
    //     showToast('Error al crear booking', 'error');
    // }
}

// Handle Customer Submission (Demo)
async function handleCustomerSubmit(e) {
    e.preventDefault();

    const customerData = {
        name: document.getElementById('customer_name').value,
        email: document.getElementById('customer_email').value,
        phone: document.getElementById('customer_phone').value,
        company: document.getElementById('customer_company').value || null,
        address: document.getElementById('customer_address').value || null
    };

    console.log('Customer Data:', customerData);

    // Note: This is a demo. The actual endpoint will be implemented in Module F4
    showToast('Cliente creado (demo). Los endpoints CRUD se implementarán en el Módulo F4.', 'success');

    // Reset form
    e.target.reset();

    // In a real implementation, you would do:
    // try {
    //     const response = await fetch(`${API_BASE_URL}/api/v1/customers`, {
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify(customerData)
    //     });
    //     const result = await response.json();
    //     if (response.ok) {
    //         showToast('Cliente creado exitosamente', 'success');
    //         e.target.reset();
    //     }
    // } catch (error) {
    //     showToast('Error al crear cliente', 'error');
    // }
}

// Test Agent
async function testAgent(agentType) {
    const outputDiv = document.getElementById('agentTestOutput');
    const resultPre = document.getElementById('agentTestResult');

    outputDiv.style.display = 'block';
    resultPre.textContent = 'Probando agente...';

    // Scroll to output
    outputDiv.scrollIntoView({ behavior: 'smooth' });

    // Demo test data for each agent type
    const testData = {
        'coordinator': {
            task_type: 'communications',
            data: {
                communication_type: 'email',
                recipient: 'test@example.com',
                message: 'Test message'
            }
        },
        'communications': {
            communication_type: 'email',
            recipient: 'test@example.com',
            message: 'Test email from Communications Agent'
        },
        'financial': {
            operation_type: 'quotation',
            customer_id: 1,
            amount: 500.00
        },
        'operations': {
            operation_type: 'route_planning',
            origin: 'New York, NY',
            destination: 'Boston, MA'
        },
        'analytics': {
            report_type: 'performance',
            time_period: 'monthly',
            metrics: ['bookings', 'revenue', 'efficiency']
        }
    };

    const testInput = testData[agentType] || {};

    try {
        // Note: Agent execution endpoints will be implemented in Module AI4
        // For now, we'll show a demo response

        const demoResponse = {
            success: true,
            agent: agentType,
            result: {
                message: `${agentType} agent ejecutado exitosamente (demo)`,
                input_received: testInput,
                status: 'completed',
                note: 'Los agentes se implementarán completamente en los módulos AI1-AI4'
            },
            timestamp: new Date().toISOString()
        };

        resultPre.textContent = JSON.stringify(demoResponse, null, 2);
        showToast(`Agente ${agentType} probado exitosamente (demo)`, 'success');

        // In a real implementation, you would do:
        // const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentType}/execute`, {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(testInput)
        // });
        // const result = await response.json();
        // resultPre.textContent = JSON.stringify(result, null, 2);

    } catch (error) {
        resultPre.textContent = `Error: ${error.message}`;
        showToast('Error al probar agente', 'error');
    }
}

// Refresh Page
async function refreshPage() {
    showToast('Actualizando...', 'success');
    await checkAPIStatus();
    await loadDashboardData();
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Utility Functions
function formatDate(dateString) {
    return new Date(dateString).toLocaleString('es-ES');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Export functions for inline onclick handlers
window.showPage = showPage;
window.refreshPage = refreshPage;
window.testAgent = testAgent;

console.log('Project Handler Frontend initialized');
console.log('API Base URL:', API_BASE_URL);
