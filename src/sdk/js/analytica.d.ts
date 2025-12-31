/**
 * ANALYTICA DSL - TypeScript Definitions
 */

export interface SDKConfig {
  apiUrl: string;
  timeout: number;
  domain?: string;
  headers: Record<string, string>;
}

export interface AtomDict {
  type: string;
  action: string;
  params: Record<string, any>;
}

export interface PipelineDefinition {
  name: string;
  steps: AtomDict[];
  variables: Record<string, any>;
  domain?: string;
}

export interface ExecutionResult {
  execution_id: string;
  status: 'success' | 'error' | 'pending';
  result: any;
  logs: Array<{ level: string; message: string }>;
  errors: Array<{ type: string; message: string }>;
  execution_time_ms?: number;
}

export interface ParseResult {
  name: string;
  steps: Array<{ atom: AtomDict; condition?: string; on_error: string }>;
  variables: Record<string, any>;
  dsl_normalized: string;
  json_representation: PipelineDefinition;
}

export interface ValidateResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface StoredPipeline {
  id: string;
  name: string;
  description: string;
  dsl: string;
  variables: Record<string, any>;
  domain?: string;
  created_at: string;
  updated_at: string;
  tags: string[];
}

// Atom class
export class Atom {
  type: string;
  action: string;
  params: Record<string, any>;
  
  constructor(type: string, action: string, params?: Record<string, any>);
  toDict(): AtomDict;
  toDSL(): string;
}

// Data builder
export interface DataBuilder {
  load(source: string, params?: Record<string, any>): PipelineBuilder;
  query(sql: string, params?: Record<string, any>): PipelineBuilder;
  fetch(url: string, params?: Record<string, any>): PipelineBuilder;
  fromInput(data?: any): PipelineBuilder;
}

// Transform builder
export interface TransformBuilder {
  filter(conditions: Record<string, any>): PipelineBuilder;
  map(func: string, field?: string): PipelineBuilder;
  sort(by: string, order?: 'asc' | 'desc'): PipelineBuilder;
  limit(n: number): PipelineBuilder;
  groupBy(...fields: string[]): PipelineBuilder;
  aggregate(by: string, func?: string): PipelineBuilder;
  select(...fields: string[]): PipelineBuilder;
  rename(mapping: Record<string, string>): PipelineBuilder;
}

// Metrics builder
export interface MetricsBuilder {
  calculate(metrics: string[], field?: string): PipelineBuilder;
  sum(field: string): PipelineBuilder;
  avg(field: string): PipelineBuilder;
  count(): PipelineBuilder;
  variance(field: string): PipelineBuilder;
  percentile(field: string, p?: number): PipelineBuilder;
}

// Report builder
export interface ReportBuilder {
  generate(format?: string, template?: string): PipelineBuilder;
  schedule(cron: string, recipients?: string[]): PipelineBuilder;
  send(to: string[], params?: Record<string, any>): PipelineBuilder;
}

// Alert builder
export interface AlertBuilder {
  when(condition: string): PipelineBuilder;
  send(channel: string, message?: string): PipelineBuilder;
  threshold(field: string, operator: string, value: number): PipelineBuilder;
}

// Budget builder
export interface BudgetBuilder {
  create(name: string, params?: Record<string, any>): PipelineBuilder;
  load(budgetId: string): PipelineBuilder;
  compare(scenario?: string): PipelineBuilder;
  variance(): PipelineBuilder;
  categorize(by: string): PipelineBuilder;
}

// Investment builder
export interface InvestmentBuilder {
  analyze(params?: Record<string, any>): PipelineBuilder;
  roi(): PipelineBuilder;
  npv(rate?: number): PipelineBuilder;
  irr(): PipelineBuilder;
  payback(): PipelineBuilder;
  scenario(name: string, multiplier?: number): PipelineBuilder;
}

// Forecast builder
export interface ForecastBuilder {
  predict(periods?: number, model?: string): PipelineBuilder;
  trend(): PipelineBuilder;
  seasonality(): PipelineBuilder;
  confidence(level?: number): PipelineBuilder;
}

// Export builder
export interface ExportBuilder {
  toCsv(path?: string): PipelineBuilder;
  toJson(path?: string): PipelineBuilder;
  toExcel(path?: string): PipelineBuilder;
  toApi(url: string, method?: string): PipelineBuilder;
}

// Pipeline builder
export class PipelineBuilder {
  constructor(domain?: string);
  
  name(name: string): PipelineBuilder;
  var(name: string, value: any): PipelineBuilder;
  vars(variables: Record<string, any>): PipelineBuilder;
  
  readonly data: DataBuilder;
  readonly transform: TransformBuilder;
  readonly metrics: MetricsBuilder;
  readonly report: ReportBuilder;
  readonly alert: AlertBuilder;
  readonly budget: BudgetBuilder;
  readonly investment: InvestmentBuilder;
  readonly forecast: ForecastBuilder;
  readonly export: ExportBuilder;
  
  build(): PipelineDefinition;
  toDSL(): string;
  toJSON(): string;
  
  execute(options?: {
    inputData?: any;
    variables?: Record<string, any>;
  }): Promise<ExecutionResult>;
}

// Analytica client
export class AnalyticaClient {
  constructor(apiUrl?: string);
  
  run(dsl: string, options?: {
    variables?: Record<string, any>;
    inputData?: any;
    domain?: string;
  }): Promise<ExecutionResult>;
  
  parse(dsl: string): Promise<ParseResult>;
  validate(dsl: string): Promise<ValidateResult>;
  atoms(): Promise<Record<string, string[]>>;
  
  executeAtom(
    type: string, 
    action: string, 
    params?: Record<string, any>,
    inputData?: any
  ): Promise<any>;
  
  listPipelines(options?: {
    domain?: string;
    tag?: string;
  }): Promise<StoredPipeline[]>;
  
  savePipeline(pipeline: Partial<StoredPipeline>): Promise<StoredPipeline>;
  runPipeline(pipelineId: string, variables?: Record<string, any>, inputData?: any): Promise<ExecutionResult>;
}

// Pipeline stream
export class PipelineStream {
  constructor(apiUrl?: string);
  
  connect(): Promise<PipelineStream>;
  on(event: 'step_start' | 'step_complete' | 'complete' | 'error', handler: (data: any) => void): PipelineStream;
  execute(dsl: string, variables?: Record<string, any>): PipelineStream;
  close(): void;
}

// Factory functions
export function Pipeline(domain?: string): PipelineBuilder;
export function createClient(apiUrl?: string): AnalyticaClient;
export function createStream(apiUrl?: string): PipelineStream;
export function configure(options: Partial<SDKConfig>): void;

// Singleton client
export const Analytica: AnalyticaClient;

// Atom types enum
export const ATOM_TYPES: {
  DATA: 'data';
  TRANSFORM: 'transform';
  FILTER: 'filter';
  AGGREGATE: 'aggregate';
  METRICS: 'metrics';
  REPORT: 'report';
  ALERT: 'alert';
  BUDGET: 'budget';
  INVESTMENT: 'investment';
  FORECAST: 'forecast';
  EXPORT: 'export';
  VALIDATE: 'validate';
  MERGE: 'merge';
  CACHE: 'cache';
};

// Default export
declare const _default: {
  Pipeline: typeof Pipeline;
  Analytica: AnalyticaClient;
  configure: typeof configure;
  createClient: typeof createClient;
  createStream: typeof createStream;
};

export default _default;
