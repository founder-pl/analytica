/**
 * Analytica Web Dashboard
 * Built with DSL-driven architecture
 */

// Configuration
const API_BASE = window.API_URL || 'http://localhost:18000';
const REFRESH_INTERVAL = 30000; // 30 seconds

// Initialize dashboard
async function initDashboard() {
    console.log('🚀 Initializing Analytica Dashboard...');
    
    try {
        // Load view renderer
        const { createViewRenderer } = await import(`${API_BASE}/ui/view-renderer.js`);
        
        // Create renderers for each section
        window.renderers = {
            kpi: createViewRenderer(document.getElementById('kpi-cards')),
            revenueChart: createViewRenderer(document.getElementById('revenue-chart')),
            ordersChart: createViewRenderer(document.getElementById('orders-chart')),
            table: createViewRenderer(document.getElementById('data-table'))
        };
        
        // Initial load
        await refreshDashboard();
        
        // Auto-refresh
        setInterval(refreshDashboard, REFRESH_INTERVAL);
        
        updateStatus('connected');
    } catch (error) {
        console.error('Dashboard init error:', error);
        updateStatus('error');
    }
}

// Refresh dashboard data
async function refreshDashboard() {
    updateStatus('loading');
    
    try {
        // Execute main dashboard DSL pipeline
        const dsl = `
            data.load("/landing/sample-data/ecommerce.json")
            | view.card(value="total_revenue", title="Total Revenue", icon="💰", style="success")
            | view.card(value="orders_count", title="Orders", icon="📦", style="info")
            | view.card(value="average_order", title="Avg Order", icon="📊", style="default")
            | view.chart(type="bar", x="month", y="revenue", title="Monthly Revenue", data_path="monthly")
            | view.table(columns=["month", "revenue", "orders"], title="Monthly Details", data_path="monthly")
        `;
        
        const response = await fetch(`${API_BASE}/api/v1/pipeline/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dsl })
        });
        
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        
        const result = await response.json();
        
        // Render views
        if (result.views && result.views.length > 0) {
            renderDashboard(result);
        }
        
        updateStatus('connected');
        console.log('✅ Dashboard updated');
        
    } catch (error) {
        console.error('Refresh error:', error);
        updateStatus('error');
    }
}

// Render dashboard sections
function renderDashboard(result) {
    const container = document.getElementById('kpi-cards');
    container.innerHTML = '';
    
    // Render KPI cards
    const cards = result.views.filter(v => v.type === 'card');
    cards.forEach(card => {
        const cardEl = createCardElement(card, result.data);
        container.appendChild(cardEl);
    });
    
    // Render charts
    const charts = result.views.filter(v => v.type === 'chart');
    if (charts[0]) {
        window.renderers.revenueChart.render({ data: result.data, views: [charts[0]] });
    }
    
    // Render table
    const tables = result.views.filter(v => v.type === 'table');
    if (tables[0]) {
        window.renderers.table.render({ data: result.data, views: tables });
    }
}

// Create card element
function createCardElement(spec, data) {
    const card = document.createElement('div');
    card.className = `kpi-card kpi-${spec.style || 'default'}`;
    
    const value = data[spec.value_field] || spec.computed_value || 0;
    const formattedValue = formatValue(value, spec.format);
    
    card.innerHTML = `
        <div class="kpi-icon">${spec.icon || '📊'}</div>
        <div class="kpi-content">
            <div class="kpi-value">${formattedValue}</div>
            <div class="kpi-title">${spec.title}</div>
        </div>
    `;
    
    return card;
}

// Format value based on type
function formatValue(value, format) {
    if (typeof value !== 'number') return value;
    
    switch (format) {
        case 'currency':
            return new Intl.NumberFormat('pl-PL', { 
                style: 'currency', 
                currency: 'PLN' 
            }).format(value);
        case 'percent':
            return `${value.toFixed(1)}%`;
        default:
            return new Intl.NumberFormat('pl-PL').format(value);
    }
}

// Update connection status
function updateStatus(state) {
    const statusEl = document.getElementById('status');
    const states = {
        connected: { text: '● Connected', class: 'status-ok' },
        loading: { text: '◐ Loading...', class: 'status-loading' },
        error: { text: '● Disconnected', class: 'status-error' }
    };
    
    const s = states[state] || states.error;
    statusEl.textContent = s.text;
    statusEl.className = `status ${s.class}`;
}

// Expose refresh function globally
window.refreshDashboard = refreshDashboard;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initDashboard);
