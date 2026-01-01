/**
 * Analytica Desktop - Renderer Process
 */

// Navigation
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const viewId = btn.dataset.view;
        switchView(viewId);
    });
});

function switchView(viewId) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-view="${viewId}"]`).classList.add('active');
    
    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${viewId}`).classList.add('active');
}

// Listen for menu actions
if (window.analytica) {
    window.analytica.onMenuAction((action, data) => {
        console.log('Menu action:', action);
        switch (action) {
            case 'tool-investment': switchView('investment'); break;
            case 'tool-budget': switchView('budget'); break;
            case 'tool-forecast': switchView('forecast'); break;
            case 'tool-dsl': switchView('dsl'); break;
            case 'about': showAbout(); break;
        }
    });
}

// Investment Analysis
async function runInvestmentAnalysis() {
    const initial = parseFloat(document.getElementById('initial-investment').value);
    const rate = parseFloat(document.getElementById('discount-rate').value) / 100;
    const flows = document.getElementById('cash-flows').value
        .split(',')
        .map(v => parseFloat(v.trim()))
        .filter(v => !isNaN(v));
    
    const dsl = `
        investment.analyze(
            initial_investment=${initial},
            discount_rate=${rate},
            cash_flows=[${flows.join(',')}]
        )
        | view.card(value="npv", title="NPV", icon="💰", style="success")
        | view.card(value="roi", title="ROI %", icon="📈", style="info")
        | view.card(value="irr", title="IRR %", icon="📊", style="default")
        | view.card(value="payback_period", title="Payback (years)", icon="⏱️", style="warning")
        | view.table(columns=["initial_investment", "discount_rate", "periods", "npv", "roi"])
    `;
    
    try {
        const result = await window.analytica.executeDSL(dsl, {});
        renderResults('investment-results', result);
        
        // Show notification
        if (result.data && result.data.npv > 0) {
            window.analytica.notify('Investment Analysis Complete', `NPV: ${formatCurrency(result.data.npv)}`);
        }
    } catch (error) {
        showError('investment-results', error.message);
    }
}

// DSL Editor
async function validateDSL() {
    const dsl = document.getElementById('dsl-input').value;
    const result = await window.analytica.validateDSL(dsl);
    
    const resultsEl = document.getElementById('dsl-results');
    if (result.valid) {
        resultsEl.innerHTML = '<div class="success-msg">✅ DSL is valid</div>';
    } else {
        resultsEl.innerHTML = `<div class="error-msg">❌ ${result.error || 'Invalid DSL'}</div>`;
    }
}

async function executeDSL() {
    const dsl = document.getElementById('dsl-input').value;
    
    try {
        const result = await window.analytica.executeDSL(dsl, {});
        renderResults('dsl-results', result);
    } catch (error) {
        showError('dsl-results', error.message);
    }
}

// Rendering
function renderResults(containerId, result) {
    const container = document.getElementById(containerId);
    
    if (result.error) {
        showError(containerId, result.error);
        return;
    }
    
    let html = '';
    
    // Render cards
    if (result.views) {
        const cards = result.views.filter(v => v.type === 'card');
        if (cards.length > 0) {
            html += '<div class="cards-grid">';
            cards.forEach(card => {
                const value = result.data[card.value_field] || card.computed_value || 0;
                const formatted = formatValue(value, card.format);
                html += `
                    <div class="result-card card-${card.style || 'default'}">
                        <div class="card-icon">${card.icon || '📊'}</div>
                        <div class="card-value">${formatted}</div>
                        <div class="card-title">${card.title}</div>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        // Render tables
        const tables = result.views.filter(v => v.type === 'table');
        tables.forEach(table => {
            html += `<div class="result-table"><h3>${table.title || 'Data'}</h3><table><thead><tr>`;
            table.columns.forEach(col => {
                html += `<th>${col.header || col.field}</th>`;
            });
            html += '</tr></thead><tbody><tr>';
            table.columns.forEach(col => {
                const val = result.data[col.field] || '-';
                html += `<td>${formatValue(val)}</td>`;
            });
            html += '</tr></tbody></table></div>';
        });
    }
    
    // Raw data
    html += `<details class="raw-data"><summary>Raw JSON</summary><pre>${JSON.stringify(result, null, 2)}</pre></details>`;
    
    container.innerHTML = html;
}

function showError(containerId, message) {
    document.getElementById(containerId).innerHTML = `
        <div class="error-msg">❌ Error: ${message}</div>
    `;
}

function formatValue(value, format) {
    if (typeof value !== 'number') return value;
    
    if (format === 'currency' || value > 1000) {
        return formatCurrency(value);
    }
    if (format === 'percent' || (value >= 0 && value <= 1)) {
        return `${(value * 100).toFixed(1)}%`;
    }
    return value.toFixed(2);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pl-PL', { 
        style: 'currency', 
        currency: 'PLN',
        maximumFractionDigits: 0
    }).format(value);
}

function showAbout() {
    alert(`Analytica Desktop v${window.analytica?.version || '1.0.0'}\n\nBuilt with Analytica DSL\nPlatform: ${window.analytica?.platform || 'unknown'}`);
}

// Initialize
console.log('Analytica Desktop initialized');
