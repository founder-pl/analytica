/**
 * ANALYTICA DSL - JavaScript SDK
 * ===============================
 * 
 * Fluent API for building and executing analytics pipelines
 * Works in browser and Node.js
 * 
 * Usage:
 *   import { Pipeline, Analytica } from '@analytica/sdk';
 *   
 *   // Fluent builder
 *   const result = await Pipeline()
 *     .data.load('sales.csv')
 *     .transform.filter({ year: 2024 })
 *     .metrics.sum('amount')
 *     .execute();
 *   
 *   // DSL string
 *   const result = await Analytica.run('data.load("sales") | metrics.sum("amount")');
 */

// ============================================================
// CONFIGURATION
// ============================================================

const DEFAULT_CONFIG = {
  apiUrl: 'http://localhost:8080',
  timeout: 30000,
  domain: null,
  headers: {}
};

let config = { ...DEFAULT_CONFIG };

/**
 * Configure the SDK
 * @param {Object} options Configuration options
 */
export function configure(options) {
  config = { ...config, ...options };
}

// ============================================================
// ATOM DEFINITIONS
// ============================================================

const ATOM_TYPES = {
  DATA: 'data',
  TRANSFORM: 'transform',
  FILTER: 'filter',
  AGGREGATE: 'aggregate',
  METRICS: 'metrics',
  REPORT: 'report',
  ALERT: 'alert',
  BUDGET: 'budget',
  INVESTMENT: 'investment',
  FORECAST: 'forecast',
  EXPORT: 'export',
  VALIDATE: 'validate',
  MERGE: 'merge',
  CACHE: 'cache'
};

// ============================================================
// ATOM CLASS
// ============================================================

class Atom {
  constructor(type, action, params = {}) {
    this.type = type;
    this.action = action;
    this.params = params;
  }

  toDict() {
    return {
      type: this.type,
      action: this.action,
      params: this.params
    };
  }

  toDSL() {
    const paramStr = Object.entries(this.params)
      .map(([k, v]) => {
        if (k.startsWith('_')) return null;
        const val = typeof v === 'string' ? `"${v}"` : JSON.stringify(v);
        return `${k}=${val}`;
      })
      .filter(Boolean)
      .join(', ');
    
    return `${this.type}.${this.action}(${paramStr})`;
  }
}

// ============================================================
// PIPELINE BUILDER
// ============================================================

class PipelineBuilder {
  constructor(domain = null) {
    this._steps = [];
    this._variables = {};
    this._name = 'pipeline';
    this._domain = domain || config.domain;
  }

  /**
   * Set pipeline name
   */
  name(name) {
    this._name = name;
    return this;
  }

  /**
   * Set variable
   */
  var(name, value) {
    this._variables[name] = value;
    return this;
  }

  /**
   * Set multiple variables
   */
  vars(variables) {
    Object.assign(this._variables, variables);
    return this;
  }

  /**
   * Add a step to the pipeline
   * @private
   */
  _addStep(type, action, params = {}) {
    this._steps.push(new Atom(type, action, params));
    return this;
  }

  // ============================================================
  // DATA OPERATIONS
  // ============================================================

  get data() {
    const self = this;
    return {
      load(source, params = {}) {
        return self._addStep('data', 'load', { source, ...params });
      },
      query(sql, params = {}) {
        return self._addStep('data', 'query', { sql, ...params });
      },
      fetch(url, params = {}) {
        return self._addStep('data', 'fetch', { url, ...params });
      },
      fromInput(data = null) {
        return self._addStep('data', 'from_input', { data });
      }
    };
  }

  // ============================================================
  // TRANSFORM OPERATIONS
  // ============================================================

  get transform() {
    const self = this;
    return {
      filter(conditions) {
        return self._addStep('transform', 'filter', conditions);
      },
      map(func, field = null) {
        return self._addStep('transform', 'map', { func, field });
      },
      sort(by, order = 'asc') {
        return self._addStep('transform', 'sort', { by, order });
      },
      limit(n) {
        return self._addStep('transform', 'limit', { n });
      },
      groupBy(...fields) {
        return self._addStep('transform', 'group_by', { fields });
      },
      aggregate(by, func = 'sum') {
        return self._addStep('transform', 'aggregate', { by, func });
      },
      select(...fields) {
        return self._addStep('transform', 'select', { fields });
      },
      rename(mapping) {
        return self._addStep('transform', 'rename', mapping);
      }
    };
  }

  // ============================================================
  // METRICS OPERATIONS
  // ============================================================

  get metrics() {
    const self = this;
    return {
      calculate(metrics, field = null) {
        return self._addStep('metrics', 'calculate', { metrics, field });
      },
      sum(field) {
        return self._addStep('metrics', 'sum', { field });
      },
      avg(field) {
        return self._addStep('metrics', 'avg', { field });
      },
      count() {
        return self._addStep('metrics', 'count', {});
      },
      variance(field) {
        return self._addStep('metrics', 'variance', { field });
      },
      percentile(field, p = 50) {
        return self._addStep('metrics', 'percentile', { field, p });
      }
    };
  }

  // ============================================================
  // REPORT OPERATIONS
  // ============================================================

  get report() {
    const self = this;
    return {
      generate(format = 'pdf', template = null) {
        return self._addStep('report', 'generate', { format, template });
      },
      schedule(cron, recipients = []) {
        return self._addStep('report', 'schedule', { cron, recipients });
      },
      send(to, params = {}) {
        return self._addStep('report', 'send', { to, ...params });
      }
    };
  }

  // ============================================================
  // ALERT OPERATIONS
  // ============================================================

  get alert() {
    const self = this;
    return {
      when(condition) {
        return self._addStep('alert', 'when', { condition });
      },
      send(channel, message = null) {
        return self._addStep('alert', 'send', { channel, message });
      },
      threshold(field, operator, value) {
        return self._addStep('alert', 'threshold', { field, operator, value });
      }
    };
  }

  // ============================================================
  // BUDGET OPERATIONS
  // ============================================================

  get budget() {
    const self = this;
    return {
      create(name, params = {}) {
        return self._addStep('budget', 'create', { name, ...params });
      },
      load(budgetId) {
        return self._addStep('budget', 'load', { budget_id: budgetId });
      },
      compare(scenario = 'actual') {
        return self._addStep('budget', 'compare', { scenario });
      },
      variance() {
        return self._addStep('budget', 'variance', {});
      },
      categorize(by) {
        return self._addStep('budget', 'categorize', { by });
      }
    };
  }

  // ============================================================
  // INVESTMENT OPERATIONS
  // ============================================================

  get investment() {
    const self = this;
    return {
      analyze(params = {}) {
        return self._addStep('investment', 'analyze', params);
      },
      roi() {
        return self._addStep('investment', 'roi', {});
      },
      npv(rate = 0.1) {
        return self._addStep('investment', 'npv', { rate });
      },
      irr() {
        return self._addStep('investment', 'irr', {});
      },
      payback() {
        return self._addStep('investment', 'payback', {});
      },
      scenario(name, multiplier = 1.0) {
        return self._addStep('investment', 'scenario', { name, multiplier });
      }
    };
  }

  // ============================================================
  // FORECAST OPERATIONS
  // ============================================================

  get forecast() {
    const self = this;
    return {
      predict(periods = 30, model = 'prophet') {
        return self._addStep('forecast', 'predict', { periods, model });
      },
      trend() {
        return self._addStep('forecast', 'trend', {});
      },
      seasonality() {
        return self._addStep('forecast', 'seasonality', {});
      },
      confidence(level = 0.95) {
        return self._addStep('forecast', 'confidence', { level });
      }
    };
  }

  // ============================================================
  // EXPORT OPERATIONS
  // ============================================================

  get export() {
    const self = this;
    return {
      toCsv(path = null) {
        return self._addStep('export', 'to_csv', { path });
      },
      toJson(path = null) {
        return self._addStep('export', 'to_json', { path });
      },
      toExcel(path = null) {
        return self._addStep('export', 'to_excel', { path });
      },
      toApi(url, method = 'POST') {
        return self._addStep('export', 'to_api', { url, method });
      }
    };
  }

  // ============================================================
  // BUILD & EXECUTE
  // ============================================================

  /**
   * Build pipeline definition
   */
  build() {
    return {
      name: this._name,
      steps: this._steps.map(s => s.toDict()),
      variables: this._variables,
      domain: this._domain
    };
  }

  /**
   * Convert to DSL string
   */
  toDSL() {
    const steps = this._steps.map(s => s.toDSL()).join(' | ');
    
    let dsl = '';
    if (this._name !== 'pipeline') {
      dsl += `@pipeline ${this._name}:\n`;
    }
    
    for (const [key, val] of Object.entries(this._variables)) {
      dsl += `$${key} = ${JSON.stringify(val)}\n`;
    }
    
    dsl += steps;
    return dsl;
  }

  /**
   * Convert to JSON
   */
  toJSON() {
    return JSON.stringify(this.build(), null, 2);
  }

  /**
   * Execute the pipeline via API
   * @param {Object} options Execution options
   * @returns {Promise<Object>} Execution result
   */
  async execute(options = {}) {
    const { inputData = null, variables = {} } = options;
    
    const payload = {
      dsl: this.toDSL(),
      variables: { ...this._variables, ...variables },
      input_data: inputData,
      domain: this._domain
    };

    const response = await fetch(`${config.apiUrl}/api/v1/pipeline/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Pipeline execution failed');
    }

    return response.json();
  }

  /**
   * Execute locally (in browser/Node.js)
   * Requires atoms to be registered locally
   */
  executeLocal(inputData = null) {
    // Local execution implementation
    // Would need local atom registry
    throw new Error('Local execution not yet implemented');
  }
}

// ============================================================
// ANALYTICA CLIENT
// ============================================================

class AnalyticaClient {
  constructor(apiUrl = null) {
    this.apiUrl = apiUrl || config.apiUrl;
  }

  /**
   * Run a DSL string
   */
  async run(dsl, options = {}) {
    const { variables = {}, inputData = null, domain = null } = options;

    const response = await fetch(`${this.apiUrl}/api/v1/pipeline/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      },
      body: JSON.stringify({
        dsl,
        variables,
        input_data: inputData,
        domain
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Pipeline execution failed');
    }

    return response.json();
  }

  /**
   * Parse a DSL string
   */
  async parse(dsl) {
    const response = await fetch(`${this.apiUrl}/api/v1/pipeline/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dsl })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Parse failed');
    }

    return response.json();
  }

  /**
   * Validate a DSL string
   */
  async validate(dsl) {
    const response = await fetch(`${this.apiUrl}/api/v1/pipeline/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dsl })
    });

    return response.json();
  }

  /**
   * List available atoms
   */
  async atoms() {
    const response = await fetch(`${this.apiUrl}/api/v1/atoms`);
    return response.json();
  }

  /**
   * Execute a single atom
   */
  async executeAtom(type, action, params = {}, inputData = null) {
    const response = await fetch(`${this.apiUrl}/api/v1/atoms/${type}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        params,
        input_data: inputData
      })
    });

    return response.json();
  }

  /**
   * List stored pipelines
   */
  async listPipelines(options = {}) {
    const { domain = null, tag = null } = options;
    let url = `${this.apiUrl}/api/v1/pipelines`;
    
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    if (tag) params.append('tag', tag);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const response = await fetch(url);
    return response.json();
  }

  /**
   * Save a pipeline
   */
  async savePipeline(pipeline) {
    const response = await fetch(`${this.apiUrl}/api/v1/pipelines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pipeline)
    });

    return response.json();
  }

  /**
   * Run a stored pipeline
   */
  async runPipeline(pipelineId, variables = {}, inputData = null) {
    const response = await fetch(
      `${this.apiUrl}/api/v1/pipelines/${pipelineId}/run`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables, input_data: inputData })
      }
    );

    return response.json();
  }
}

// ============================================================
// WEBSOCKET CLIENT FOR STREAMING
// ============================================================

class PipelineStream {
  constructor(apiUrl = null) {
    this.apiUrl = (apiUrl || config.apiUrl).replace('http', 'ws');
    this.ws = null;
    this.handlers = {};
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.apiUrl}/ws/pipeline`);
      
      this.ws.onopen = () => resolve(this);
      this.ws.onerror = (err) => reject(err);
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const handler = this.handlers[data.type];
        if (handler) handler(data);
      };
    });
  }

  on(event, handler) {
    this.handlers[event] = handler;
    return this;
  }

  execute(dsl, variables = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      action: 'execute',
      dsl,
      variables
    }));

    return this;
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// ============================================================
// FACTORY FUNCTIONS
// ============================================================

/**
 * Create a new pipeline builder
 */
export function Pipeline(domain = null) {
  return new PipelineBuilder(domain);
}

/**
 * Create Analytica client
 */
export function createClient(apiUrl = null) {
  return new AnalyticaClient(apiUrl);
}

/**
 * Create streaming client
 */
export function createStream(apiUrl = null) {
  return new PipelineStream(apiUrl);
}

// Singleton client
export const Analytica = new AnalyticaClient();

// ============================================================
// EXPORTS
// ============================================================

export {
  PipelineBuilder,
  AnalyticaClient,
  PipelineStream,
  Atom,
  ATOM_TYPES
};

// Default export
export default {
  Pipeline,
  Analytica,
  configure,
  createClient,
  createStream
};
