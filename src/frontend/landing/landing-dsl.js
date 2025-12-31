import { createViewRenderer } from '/ui/view-renderer.js';

function resolveApiBase() {
  let apiBase = null;
  try {
    const params = new URLSearchParams(window.location.search);
    apiBase = params.get('apiBase') || params.get('api') || null;
  } catch {}

  if (!apiBase) {
    try {
      apiBase = window.ANALYTICA_API_BASE_URL || null;
    } catch {}
  }

  if (!apiBase) {
    try {
      apiBase = window.localStorage.getItem('ANALYTICA_API_BASE_URL') || null;
    } catch {}
  }

  apiBase = (apiBase || window.location.origin || '').trim();
  if (!apiBase || apiBase === 'null' || window.location.protocol === 'file:') {
    apiBase = 'http://localhost:18000';
  }

  apiBase = apiBase.replace(/\/+$/, '');

  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('apiBase') || params.get('api')) {
      window.localStorage.setItem('ANALYTICA_API_BASE_URL', apiBase);
    }
  } catch {}

  return apiBase;
}

function getByPath(obj, path) {
  if (!path) return obj;
  const parts = String(path).split('.').filter(Boolean);
  let cur = obj;
  for (const p of parts) {
    if (cur === null || cur === undefined) return undefined;
    cur = cur[p];
  }
  return cur;
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`Failed to fetch ${url} (${resp.status})`);
  }
  return resp.json();
}

async function loadInputData(demoEl) {
  const inlineEl = demoEl.querySelector('[data-input]');
  if (inlineEl) {
    try {
      return JSON.parse(inlineEl.textContent || 'null');
    } catch {
      throw new Error('Invalid JSON in [data-input]');
    }
  }

  const sample = demoEl.dataset.sample;
  if (!sample) return null;

  const sampleUrl = new URL(sample, window.location.href).toString();
  const sampleData = await fetchJson(sampleUrl);
  const inputPath = demoEl.dataset.inputPath || '';
  const selected = getByPath(sampleData, inputPath);
  return selected === undefined ? sampleData : selected;
}

async function executePipeline(apiBase, dsl, inputData) {
  const response = await fetch(`${apiBase}/api/v1/pipeline/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dsl, input_data: inputData })
  });

  const raw = await response.text();
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    parsed = { status: 'error', errors: [{ type: 'InvalidJSON', message: raw }] };
  }

  if (!response.ok && parsed && parsed.detail) {
    throw new Error(parsed.detail);
  }

  return parsed;
}

function setStatus(el, kind, text) {
  if (!el) return;
  el.style.display = 'inline-block';
  el.className = kind === 'success' ? 'status-badge success' : kind === 'error' ? 'status-badge error' : 'status-badge running';
  el.textContent = text;
}

function initDemo(demoEl) {
  const apiBase = resolveApiBase();

  const runBtn = demoEl.querySelector('[data-run]');
  const statusEl = demoEl.querySelector('[data-status]');
  const jsonEl = demoEl.querySelector('[data-output-json]');
  const viewsEl = demoEl.querySelector('[data-output-views]');
  const dslEl = demoEl.querySelector('[data-dsl]');

  if (!runBtn || !dslEl || !viewsEl || !jsonEl) return;

  const viewRenderer = createViewRenderer(viewsEl);

  const run = async () => {
    const dsl = (dslEl.value ?? dslEl.textContent ?? '').trim();
    if (!dsl) {
      setStatus(statusEl, 'error', 'Brak DSL');
      return;
    }

    runBtn.disabled = true;
    setStatus(statusEl, 'running', 'Uruchamianie...');
    jsonEl.textContent = '';
    viewsEl.innerHTML = '';

    try {
      const inputData = await loadInputData(demoEl);
      const res = await executePipeline(apiBase, dsl, inputData);

      const payload = res.result || res;
      jsonEl.textContent = JSON.stringify(payload, null, 2);

      const ok = res.status === 'success' || (payload && payload.views);
      if (ok) {
        setStatus(statusEl, 'success', `OK${res.execution_time_ms ? ` (${res.execution_time_ms}ms)` : ''}`);
        viewRenderer.render(payload);
      } else {
        const msg = res.errors?.map(e => `${e.type}: ${e.message}`).join('\n') || 'Błąd wykonania';
        setStatus(statusEl, 'error', 'Błąd');
        viewsEl.innerHTML = `<div style="color:#dc2626; padding: 12px; background:#fee2e2; border-radius: 8px;">${msg}</div>`;
      }
    } catch (e) {
      setStatus(statusEl, 'error', 'Błąd');
      const msg = e && e.message ? e.message : String(e);
      viewsEl.innerHTML = `<div style="color:#dc2626; padding: 12px; background:#fee2e2; border-radius: 8px;">${msg}<div style="margin-top:8px; font-size: 12px; color:#7f1d1d;">API_BASE=${apiBase}</div></div>`;
    } finally {
      runBtn.disabled = false;
    }
  };

  runBtn.addEventListener('click', (e) => {
    e.preventDefault();
    run();
  });

  const autoRun = (demoEl.dataset.autoRun || '').toLowerCase();
  if (autoRun === '1' || autoRun === 'true' || autoRun === 'yes') {
    run();
  }
}

export function initLandingDslDemos() {
  document.querySelectorAll('[data-landing-dsl-demo]').forEach(initDemo);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLandingDslDemos);
} else {
  initLandingDslDemos();
}
