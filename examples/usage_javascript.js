/**
 * ANALYTICA DSL - JavaScript Usage Examples
 * ==========================================
 */

import { Pipeline, Analytica, configure, createStream } from '@analytica/sdk';

// Configure SDK
configure({
  apiUrl: 'http://localhost:8080',
  domain: 'planbudzetu.pl'
});

// ============================================================
// BASIC EXAMPLES
// ============================================================

// Example 1: Simple pipeline with fluent API
async function basicExample() {
  const result = await Pipeline()
    .data.load('sales.csv')
    .transform.filter({ year: 2024 })
    .metrics.sum('amount')
    .execute();
  
  console.log('Result:', result);
}

// Example 2: Using DSL string
async function dslStringExample() {
  const result = await Analytica.run(
    'data.load("sales.csv") | transform.filter(year=2024) | metrics.sum("amount")'
  );
  console.log('Result:', result);
}

// Example 3: With variables
async function variablesExample() {
  const result = await Pipeline()
    .var('year', 2024)
    .var('threshold', 10000)
    .data.load('sales')
    .transform.filter({ year: '$year' })
    .alert.threshold('amount', 'gt', '$threshold')
    .execute();
  
  console.log('Result:', result);
}

// ============================================================
// BUDGET EXAMPLES (planbudzetu.pl)
// ============================================================

// Example 4: Budget report
async function budgetReportExample() {
  const result = await Pipeline('planbudzetu.pl')
    .name('monthly_budget_report')
    .var('month', '2024-01')
    .budget.load('budget_2024')
    .budget.variance()
    .report.generate('pdf', 'monthly_budget')
    .execute();
  
  console.log('Budget report:', result);
}

// Example 5: Budget vs Actual
async function budgetVsActualExample() {
  const result = await Pipeline()
    .budget.load('budget_q1_2024')
    .budget.compare('actual')
    .metrics.variance('amount')
    .report.generate('xlsx')
    .report.send(['finance@company.pl'])
    .execute();
  
  console.log('Comparison:', result);
}

// Example 6: Expense categorization
async function expenseCategorization() {
  const result = await Pipeline()
    .data.load('expenses_2024')
    .budget.categorize('category')
    .transform.aggregate('category', 'sum')
    .transform.sort('amount', 'desc')
    .transform.limit(10)
    .execute();
  
  console.log('Top expenses:', result);
}

// ============================================================
// INVESTMENT EXAMPLES (planinwestycji.pl)
// ============================================================

// Example 7: ROI Analysis
async function roiAnalysisExample() {
  const investmentData = {
    initial_investment: 500000,
    cash_flows: [
      { period: 1, amount: 150000 },
      { period: 2, amount: 180000 },
      { period: 3, amount: 200000 },
      { period: 4, amount: 220000 },
      { period: 5, amount: 250000 }
    ]
  };
  
  const result = await Pipeline('planinwestycji.pl')
    .data.fromInput(investmentData)
    .investment.analyze({ discount_rate: 0.12 })
    .investment.roi()
    .investment.npv(0.1)
    .investment.payback()
    .execute();
  
  console.log('Investment analysis:', result);
  console.log(`ROI: ${result.result.roi}%`);
  console.log(`NPV: ${result.result.npv} PLN`);
  console.log(`Payback: ${result.result.payback_period} years`);
}

// Example 8: Scenario comparison
async function scenarioComparisonExample() {
  const scenarios = ['optimistic', 'realistic', 'pessimistic'];
  const results = {};
  
  for (const scenario of scenarios) {
    const multiplier = scenario === 'optimistic' ? 1.2 : 
                      scenario === 'pessimistic' ? 0.8 : 1.0;
    
    const result = await Pipeline()
      .data.load('investment_proposal')
      .investment.scenario(scenario, multiplier)
      .investment.analyze({ discount_rate: 0.1 })
      .execute();
    
    results[scenario] = result;
  }
  
  console.log('Scenario comparison:', results);
}

// ============================================================
// MULTI-PLAN EXAMPLES (multiplan.pl)
// ============================================================

// Example 9: Multi-scenario planning
async function multiScenarioPlanningExample() {
  const result = await Pipeline('multiplan.pl')
    .budget.load('budget_2025')
    .investment.scenario('growth', 1.15)
    .budget.variance()
    .forecast.predict(12, 'prophet')
    .report.generate('xlsx', 'scenario_planning')
    .execute();
  
  console.log('Scenario planning:', result);
}

// Example 10: Rolling forecast
async function rollingForecastExample() {
  const result = await Pipeline()
    .data.load('actuals_ytd')
    .forecast.predict(6, 'prophet')
    .forecast.confidence(0.95)
    .budget.compare('planned')
    .report.generate('xlsx', 'rolling_forecast')
    .execute();
  
  console.log('Rolling forecast:', result);
}

// ============================================================
// ALERT EXAMPLES (alerts.pl)
// ============================================================

// Example 11: Budget threshold alert
async function budgetAlertExample() {
  const result = await Pipeline('alerts.pl')
    .budget.load('current_budget')
    .metrics.calculate(['sum'], 'actual')
    .alert.threshold('utilization', 'gt', 0.9)
    .alert.send('slack', 'Budget threshold exceeded!')
    .execute();
  
  console.log('Alert result:', result);
}

// ============================================================
// FORECAST EXAMPLES (estymacja.pl)
// ============================================================

// Example 12: Sales forecast
async function salesForecastExample() {
  const result = await Pipeline('estymacja.pl')
    .data.load('historical_sales')
    .forecast.predict(90, 'prophet')
    .forecast.trend()
    .forecast.seasonality()
    .forecast.confidence(0.95)
    .report.generate('pdf', 'forecast_report')
    .execute();
  
  console.log('Sales forecast:', result);
}

// ============================================================
// STREAMING EXAMPLE
// ============================================================

// Example 13: Real-time streaming
async function streamingExample() {
  const stream = createStream();
  
  await stream.connect();
  
  stream
    .on('step_start', (data) => {
      console.log(`Starting step ${data.step}: ${data.atom}`);
    })
    .on('step_complete', (data) => {
      console.log(`Completed step ${data.step}:`, data.result);
    })
    .on('complete', (data) => {
      console.log('Pipeline complete:', data.result);
    })
    .on('error', (data) => {
      console.error('Error:', data.message);
    });
  
  stream.execute(
    'data.load("sales") | transform.filter(year=2024) | metrics.sum("amount")',
    { year: 2024 }
  );
}

// ============================================================
// STORED PIPELINES
// ============================================================

// Example 14: Save and run stored pipeline
async function storedPipelineExample() {
  // Save pipeline
  const saved = await Analytica.savePipeline({
    name: 'monthly_report',
    description: 'Monthly financial report',
    dsl: 'budget.load("budget") | budget.variance() | report.generate("pdf")',
    domain: 'planbudzetu.pl',
    tags: ['monthly', 'finance', 'report']
  });
  
  console.log('Saved pipeline:', saved);
  
  // Run it later
  const result = await Analytica.runPipeline(saved.id, {
    month: '2024-12'
  });
  
  console.log('Run result:', result);
}

// ============================================================
// EXPORT EXAMPLES
// ============================================================

// Example 15: Export to multiple formats
async function exportExample() {
  // Get DSL string
  const pipeline = Pipeline()
    .data.load('financials')
    .transform.filter({ year: 2024 })
    .metrics.calculate(['sum', 'avg', 'count']);
  
  console.log('DSL:', pipeline.toDSL());
  console.log('JSON:', pipeline.toJSON());
  
  // Execute and export
  const result = await pipeline
    .export.toCsv('output.csv')
    .execute();
  
  console.log('Export result:', result);
}

// ============================================================
// COMPLEX PIPELINE
// ============================================================

// Example 16: Full financial analysis
async function fullAnalysisExample() {
  const result = await Pipeline()
    .name('full_analysis')
    .var('year', 2024)
    .var('budget_id', 'budget_2024')
    
    // Load and filter data
    .data.load('financials')
    .transform.filter({ year: '$year' })
    
    // Calculate metrics
    .metrics.calculate(['sum', 'avg', 'count', 'min', 'max'])
    
    // Budget comparison
    .budget.compare('actual')
    .budget.variance()
    
    // Generate forecast
    .forecast.predict(6)
    .forecast.confidence(0.9)
    
    // Alert on variance
    .alert.threshold('variance_pct', 'gt', 10)
    
    // Generate report
    .report.generate('pdf', 'full_analysis')
    .report.send(['finance@company.pl'])
    
    // Export data
    .export.toExcel('analysis_2024.xlsx')
    
    .execute();
  
  console.log('Full analysis:', result);
}

// ============================================================
// RUN EXAMPLES
// ============================================================

async function main() {
  console.log('=== ANALYTICA DSL Examples ===\n');
  
  try {
    // Run examples
    await basicExample();
    await roiAnalysisExample();
    await budgetReportExample();
    await salesForecastExample();
    
    console.log('\nAll examples completed successfully!');
  } catch (error) {
    console.error('Error:', error);
  }
}

main();

// Export for use in other modules
export {
  basicExample,
  roiAnalysisExample,
  budgetReportExample,
  scenarioComparisonExample,
  salesForecastExample,
  fullAnalysisExample
};
