import { configure, Atom, createClient } from '/ui/sdk/analytica.js';

const el = (id) => document.getElementById(id);

const apiBaseUrlInput = el('apiBaseUrl');
const reloadBtn = el('reload');
const pipelineNameInput = el('pipelineName');
const domainOverrideInput = el('domainOverride');
const variablesJsonTextarea = el('variablesJson');
const inputDataJsonTextarea = el('inputDataJson');
const stepsEl = el('steps');
const addStepBtn = el('addStep');
const dslPreviewTextarea = el('dslPreview');
const outputPre = el('output');
const statusEl = el('status');
const domainSubtitleEl = el('domainSubtitle');

const btnParse = el('btnParse');
const btnValidate = el('btnValidate');
const btnExecute = el('btnExecute');

let atoms = null; // { type: [actions...] }
let steps = [];  // [{type, action, paramsJson}]

function getDefaultApiBaseUrl() {
  // Works behind nginx (same origin) and with direct port URLs.
  const url = new URL(window.location.href);
  return `${url.protocol}//${url.host}`;
}

function getStoredApiBaseUrl() {
  return window.localStorage.getItem('analytica_ui_api_base_url') || '';
}

function setStoredApiBaseUrl(v) {
  window.localStorage.setItem('analytica_ui_api_base_url', v);
}

function safeJsonParse(text, fallback = null) {
  if (!text || !text.trim()) return fallback;
  return JSON.parse(text);
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function setStatus(ok, text) {
  statusEl.innerHTML = '';
  const badge = document.createElement('span');
  badge.className = `badge ${ok ? 'ok' : 'err'}`;
  badge.textContent = text;
  statusEl.appendChild(badge);
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg = (data && data.detail) ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

async function loadDomainInfo() {
  try {
    const apiBaseUrl = apiBaseUrlInput.value;
    const info = await fetchJson(`${apiBaseUrl}/v1/domain`);
    domainSubtitleEl.textContent = `${info.display_name} (${info.domain})`;
  } catch (e) {
    domainSubtitleEl.textContent = '';
  }
}

async function loadAtoms() {
  const apiBaseUrl = apiBaseUrlInput.value;
  atoms = await fetchJson(`${apiBaseUrl}/api/v1/atoms`);
}

function getAtomTypes() {
  return atoms ? Object.keys(atoms).sort() : [];
}

function getActionsForType(type) {
  if (!atoms || !atoms[type]) return [];
  return [...atoms[type]].sort();
}

function defaultParamsFor(type, action) {
  // Minimal defaults for common atoms (editable as JSON)
  const key = `${type}.${action}`;
  const defaults = {
    'data.load': { source: 'sales.csv' },
    'data.query': { sql: 'SELECT 1' },
    'data.fetch': { url: 'https://api.example.com/data', method: 'GET' },
    'transform.filter': { year: 2024 },
    'transform.sort': { by: 'amount', order: 'desc' },
    'transform.limit': { n: 10 },
    'metrics.sum': { field: 'amount' },
    'metrics.avg': { field: 'amount' },
    'metrics.calculate': { metrics: ['sum', 'avg'], field: 'amount' },
    'report.generate': { format: 'pdf', template: 'monthly_report' },
    'report.send': { to: ['team@company.pl'] },
    'alert.threshold': { field: 'utilization', operator: 'gt', value: 0.9 },
    'alert.send': { channel: 'slack', message: 'Alert triggered' },
    'budget.load': { budget_id: 'budget_2024' },
    'budget.create': { name: 'Budget 2025' },
    'investment.analyze': { discount_rate: 0.12, initial_investment: 500000, cash_flows: [150000, 180000] },
    'investment.npv': { rate: 0.1 },
    'forecast.predict': { periods: 90, model: 'prophet' },
    'export.to_json': {},
    'export.to_csv': { path: 'out.csv' }
  };

  return defaults[key] || {};
}

function addStep(initial = null) {
  const type = initial?.type || getAtomTypes()[0] || 'data';
  const action = initial?.action || (getActionsForType(type)[0] || 'load');
  const paramsObj = initial?.paramsObj || defaultParamsFor(type, action);

  steps.push({
    type,
    action,
    paramsJson: pretty(paramsObj)
  });
  renderSteps();
}

function deleteStep(idx) {
  steps.splice(idx, 1);
  renderSteps();
}

function moveStep(idx, dir) {
  const j = idx + dir;
  if (j < 0 || j >= steps.length) return;
  const tmp = steps[idx];
  steps[idx] = steps[j];
  steps[j] = tmp;
  renderSteps();
}

function buildDSL() {
  const name = pipelineNameInput.value.trim();

  let vars = {};
  try {
    vars = safeJsonParse(variablesJsonTextarea.value, {});
    if (vars === null || typeof vars !== 'object' || Array.isArray(vars)) {
      throw new Error('Variables must be a JSON object');
    }
  } catch (e) {
    throw new Error(`Invalid variables JSON: ${e.message}`);
  }

  const atomDSL = steps.map((s) => {
    let params = {};
    try {
      params = safeJsonParse(s.paramsJson, {});
      if (params === null || typeof params !== 'object' || Array.isArray(params)) {
        throw new Error('Params must be a JSON object');
      }
    } catch (e) {
      throw new Error(`Invalid params JSON in ${s.type}.${s.action}: ${e.message}`);
    }

    return new Atom(s.type, s.action, params).toDSL();
  }).join(' | ');

  // Keep DSL self-contained: embed variables as $key = <json>
  const lines = [];
  const hasHeader = !!name;
  if (hasHeader) lines.push(`@pipeline ${name}:`);

  for (const [k, v] of Object.entries(vars)) {
    const prefix = hasHeader ? '  ' : '';
    lines.push(`${prefix}$${k} = ${JSON.stringify(v)}`);
  }

  if (hasHeader) {
    lines.push(`  ${atomDSL}`);
    return lines.join('\n');
  }

  return [...lines, atomDSL].filter(Boolean).join('\n');
}

function renderSteps() {
  stepsEl.innerHTML = '';

  steps.forEach((s, idx) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'step';

    const top = document.createElement('div');
    top.className = 'step-top';

    const typeField = document.createElement('label');
    typeField.className = 'field';
    const typeLabel = document.createElement('span');
    typeLabel.className = 'label';
    typeLabel.textContent = 'Atom type';
    const typeSelect = document.createElement('select');
    typeSelect.className = 'select';

    for (const t of getAtomTypes()) {
      const opt = document.createElement('option');
      opt.value = t;
      opt.textContent = t;
      if (t === s.type) opt.selected = true;
      typeSelect.appendChild(opt);
    }

    typeSelect.addEventListener('change', () => {
      s.type = typeSelect.value;
      s.action = getActionsForType(s.type)[0] || '';
      s.paramsJson = pretty(defaultParamsFor(s.type, s.action));
      renderSteps();
    });

    typeField.appendChild(typeLabel);
    typeField.appendChild(typeSelect);

    const actionField = document.createElement('label');
    actionField.className = 'field';
    const actionLabel = document.createElement('span');
    actionLabel.className = 'label';
    actionLabel.textContent = 'Action';
    const actionSelect = document.createElement('select');
    actionSelect.className = 'select';

    for (const a of getActionsForType(s.type)) {
      const opt = document.createElement('option');
      opt.value = a;
      opt.textContent = a;
      if (a === s.action) opt.selected = true;
      actionSelect.appendChild(opt);
    }

    actionSelect.addEventListener('change', () => {
      s.action = actionSelect.value;
      s.paramsJson = pretty(defaultParamsFor(s.type, s.action));
      renderSteps();
    });

    actionField.appendChild(actionLabel);
    actionField.appendChild(actionSelect);

    const stepActions = document.createElement('div');
    stepActions.className = 'step-actions';

    const upBtn = document.createElement('button');
    upBtn.className = 'button button-secondary';
    upBtn.textContent = 'Up';
    upBtn.disabled = idx === 0;
    upBtn.addEventListener('click', () => moveStep(idx, -1));

    const downBtn = document.createElement('button');
    downBtn.className = 'button button-secondary';
    downBtn.textContent = 'Down';
    downBtn.disabled = idx === steps.length - 1;
    downBtn.addEventListener('click', () => moveStep(idx, +1));

    const delBtn = document.createElement('button');
    delBtn.className = 'button button-secondary';
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => deleteStep(idx));

    stepActions.appendChild(upBtn);
    stepActions.appendChild(downBtn);
    stepActions.appendChild(delBtn);

    top.appendChild(typeField);
    top.appendChild(actionField);
    top.appendChild(stepActions);

    const paramsField = document.createElement('label');
    paramsField.className = 'field';
    const paramsLabel = document.createElement('span');
    paramsLabel.className = 'label';
    paramsLabel.textContent = 'Params (JSON object)';
    const paramsTextarea = document.createElement('textarea');
    paramsTextarea.className = 'textarea';
    paramsTextarea.rows = 6;
    paramsTextarea.spellcheck = false;
    paramsTextarea.value = s.paramsJson;

    paramsTextarea.addEventListener('input', () => {
      s.paramsJson = paramsTextarea.value;
      updateDslPreview();
    });

    paramsField.appendChild(paramsLabel);
    paramsField.appendChild(paramsTextarea);

    wrapper.appendChild(top);
    wrapper.appendChild(paramsField);
    stepsEl.appendChild(wrapper);
  });

  updateDslPreview();
}

function updateDslPreview() {
  try {
    dslPreviewTextarea.value = buildDSL();
    setStatus(true, 'Ready');
  } catch (e) {
    dslPreviewTextarea.value = '';
    setStatus(false, e.message);
  }
}

async function execute(action) {
  // Validate before executing
  if (steps.length === 0) {
    outputPre.textContent = 'Error: No pipeline steps defined.\n\nAdd at least one step to your pipeline.';
    setStatus(false, 'No steps');
    return;
  }

  try {
    const apiBaseUrl = apiBaseUrlInput.value;
    if (!apiBaseUrl) {
      outputPre.textContent = 'Error: API base URL is required.\n\nPlease enter a valid API URL.';
      setStatus(false, 'No API URL');
      return;
    }

    configure({ apiUrl: apiBaseUrl, domain: null });
    const client = createClient(apiBaseUrl);

    // Build DSL with validation
    let dsl;
    try {
      dsl = buildDSL();
    } catch (buildError) {
      outputPre.textContent = `DSL Build Error:\n\n${buildError.message}\n\nPlease check your step parameters.`;
      setStatus(false, 'Build Error');
      return;
    }
    dslPreviewTextarea.value = dsl;

    let variables = {};
    let inputData = null;

    // Parse input data with validation
    try {
      inputData = safeJsonParse(inputDataJsonTextarea.value, null);
    } catch (jsonError) {
      outputPre.textContent = `Invalid Input Data JSON:\n\n${jsonError.message}\n\nPlease check your input data format.`;
      setStatus(false, 'JSON Error');
      return;
    }

    const domain = domainOverrideInput.value.trim() || null;

    // Show loading state
    outputPre.textContent = `${action.charAt(0).toUpperCase() + action.slice(1)}ing pipeline...`;
    setStatus(true, 'Loading...');

    if (action === 'parse') {
      const res = await client.parse(dsl);
      outputPre.textContent = pretty(res);
      setStatus(true, 'Parsed');
      return;
    }

    if (action === 'validate') {
      const res = await client.validate(dsl);
      const errors = res.errors || [];
      const warnings = res.warnings || [];
      
      let output = pretty(res);
      if (errors.length > 0) {
        output += '\n\n--- Errors ---\n' + errors.map(e => `• ${e}`).join('\n');
      }
      if (warnings.length > 0) {
        output += '\n\n--- Warnings ---\n' + warnings.map(w => `⚠ ${w}`).join('\n');
      }
      
      outputPre.textContent = output;
      setStatus(!!res.valid, res.valid ? 'Valid ✓' : `Invalid (${errors.length} errors)`);
      return;
    }

    if (action === 'execute') {
      const startTime = performance.now();
      const res = await client.run(dsl, { variables, inputData, domain });
      const duration = (performance.now() - startTime).toFixed(0);
      
      let output = pretty(res);
      output += `\n\n--- Execution Info ---\nDuration: ${duration}ms`;
      if (res.execution_time_ms) {
        output += `\nServer time: ${res.execution_time_ms.toFixed(2)}ms`;
      }
      if (res.logs && res.logs.length > 0) {
        output += `\n\n--- Logs ---\n${res.logs.join('\n')}`;
      }
      
      outputPre.textContent = output;
      setStatus(res.status === 'success', res.status === 'success' ? `Done (${duration}ms)` : res.status || 'Error');
      return;
    }
  } catch (e) {
    // Format error message nicely
    let errorMsg = '';
    if (e.message && e.message.includes('fetch')) {
      errorMsg = `Connection Error:\n\nCannot connect to API at ${apiBaseUrlInput.value}\n\nPlease check:\n• API server is running\n• URL is correct\n• No CORS issues`;
    } else if (e.message && e.message.includes('JSON')) {
      errorMsg = `Response Error:\n\n${e.message}\n\nThe server returned an invalid response.`;
    } else {
      errorMsg = `Error:\n\n${e.message || e}\n\n${e.stack || ''}`;
    }
    
    outputPre.textContent = errorMsg;
    setStatus(false, e.message ? e.message.substring(0, 30) : 'Error');
  }
}

function hydrateFromQuery() {
  const u = new URL(window.location.href);
  const api = u.searchParams.get('api');
  const domain = u.searchParams.get('domain');
  if (api) apiBaseUrlInput.value = api;
  if (domain) domainOverrideInput.value = domain;
}

// Pipeline templates
const TEMPLATES = {
  sales: {
    name: 'Sales Analysis',
    steps: [
      { type: 'data', action: 'load', paramsObj: { source: 'sales.csv' } },
      { type: 'transform', action: 'filter', paramsObj: { year: 2024 } },
      { type: 'transform', action: 'sort', paramsObj: { by: 'amount', order: 'desc' } },
      { type: 'metrics', action: 'calculate', paramsObj: { metrics: ['sum', 'avg', 'count'], field: 'amount' } },
      { type: 'report', action: 'generate', paramsObj: { format: 'html', template: 'sales_summary' } }
    ]
  },
  budget: {
    name: 'Budget Variance',
    steps: [
      { type: 'budget', action: 'create', paramsObj: { name: 'Q1 2025', scenario: 'realistic' } },
      { type: 'budget', action: 'variance', paramsObj: { planned: 100000, actual: 95000 } },
      { type: 'alert', action: 'threshold', paramsObj: { metric: 'variance', operator: 'gt', threshold: 10 } },
      { type: 'report', action: 'generate', paramsObj: { format: 'html', template: 'budget_variance' } }
    ]
  },
  investment: {
    name: 'ROI Calculator',
    steps: [
      { type: 'investment', action: 'analyze', paramsObj: { 
        name: 'New Project',
        initial_investment: 100000, 
        discount_rate: 0.12, 
        cash_flows: [30000, 40000, 50000, 60000] 
      }},
      { type: 'investment', action: 'roi', paramsObj: { initial_investment: 100000, total_returns: 180000 } },
      { type: 'report', action: 'generate', paramsObj: { format: 'html', template: 'investment_analysis' } }
    ]
  },
  forecast: {
    name: 'Forecast Pipeline',
    steps: [
      { type: 'data', action: 'load', paramsObj: { source: 'historical_data.csv' } },
      { type: 'forecast', action: 'predict', paramsObj: { periods: 30, method: 'linear' } },
      { type: 'forecast', action: 'trend', paramsObj: {} },
      { type: 'report', action: 'generate', paramsObj: { format: 'html', template: 'forecast_report' } }
    ]
  },
  alert: {
    name: 'Alert Setup',
    steps: [
      { type: 'data', action: 'from_input', paramsObj: {} },
      { type: 'metrics', action: 'sum', paramsObj: { field: 'value' } },
      { type: 'alert', action: 'threshold', paramsObj: { metric: 'total', operator: 'gt', threshold: 1000000 } },
      { type: 'alert', action: 'send', paramsObj: { channel: 'email', recipient: 'team@company.pl', message: 'Threshold exceeded!' } }
    ]
  }
};

function loadTemplate(templateId) {
  const template = TEMPLATES[templateId];
  if (!template) return;
  
  // Clear current steps
  steps = [];
  
  // Add template steps
  for (const step of template.steps) {
    addStep(step);
  }
  
  pipelineNameInput.value = template.name.toLowerCase().replace(/\s+/g, '_');
  updateDslPreview();
  setStatus(true, `Loaded: ${template.name}`);
}

function initTemplates() {
  document.querySelectorAll('.template-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const templateId = btn.dataset.template;
      loadTemplate(templateId);
    });
  });
}

function init() {
  apiBaseUrlInput.value = getStoredApiBaseUrl() || getDefaultApiBaseUrl();
  hydrateFromQuery();

  reloadBtn.addEventListener('click', async () => {
    setStoredApiBaseUrl(apiBaseUrlInput.value);
    await boot();
  });

  apiBaseUrlInput.addEventListener('change', () => {
    setStoredApiBaseUrl(apiBaseUrlInput.value);
  });

  variablesJsonTextarea.addEventListener('input', updateDslPreview);
  inputDataJsonTextarea.addEventListener('input', updateDslPreview);
  pipelineNameInput.addEventListener('input', updateDslPreview);
  domainOverrideInput.addEventListener('input', updateDslPreview);

  addStepBtn.addEventListener('click', () => addStep());

  btnParse.addEventListener('click', () => execute('parse'));
  btnValidate.addEventListener('click', () => execute('validate'));
  btnExecute.addEventListener('click', () => execute('execute'));
  
  // Initialize templates
  initTemplates();
}

async function boot() {
  outputPre.textContent = '';
  setStatus(true, 'Loading...');

  try {
    await loadDomainInfo();
    await loadAtoms();

    if (steps.length === 0) {
      // Initial example pipeline
      addStep({ type: 'data', action: 'load', paramsObj: { source: 'sales.csv' } });
      addStep({ type: 'transform', action: 'filter', paramsObj: { year: 2024 } });
      addStep({ type: 'metrics', action: 'calculate', paramsObj: { metrics: ['sum', 'avg', 'count'], field: 'amount' } });
    } else {
      renderSteps();
    }

    setStatus(true, 'Ready');
  } catch (e) {
    outputPre.textContent = String(e && e.stack ? e.stack : e);
    setStatus(false, e.message || 'Failed to load');
  }
}

init();
boot();
