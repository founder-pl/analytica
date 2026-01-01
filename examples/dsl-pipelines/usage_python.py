"""
ANALYTICA DSL - Python Usage Examples
======================================
"""

import asyncio
from analytica import Pipeline, Analytica, configure, run

# Configure SDK
configure(
    api_url='http://localhost:8080',
    domain='planbudzetu.pl',
    local_execution=True  # Use local DSL engine
)


# ============================================================
# BASIC EXAMPLES
# ============================================================

def basic_example():
    """Example 1: Simple pipeline with fluent API"""
    result = (Pipeline()
        .data.load('sales.csv')
        .transform.filter(year=2024)
        .metrics.sum('amount')
        .execute())
    
    print('Result:', result)
    return result


def dsl_string_example():
    """Example 2: Using DSL string"""
    result = run(
        'data.load("sales.csv") | transform.filter(year=2024) | metrics.sum("amount")'
    )
    print('Result:', result)
    return result


def variables_example():
    """Example 3: With variables"""
    result = (Pipeline()
        .var('year', 2024)
        .var('threshold', 10000)
        .data.load('sales')
        .transform.filter(year='$year')
        .alert.threshold('amount', 'gt', '$threshold')
        .execute())
    
    print('Result:', result)
    return result


# ============================================================
# BUDGET EXAMPLES (planbudzetu.pl)
# ============================================================

def budget_report_example():
    """Example 4: Budget report"""
    result = (Pipeline('planbudzetu.pl')
        .name('monthly_budget_report')
        .var('month', '2024-01')
        .budget.load('budget_2024')
        .budget.variance()
        .report.generate('pdf', 'monthly_budget')
        .execute())
    
    print('Budget report:', result)
    return result


def budget_vs_actual_example():
    """Example 5: Budget vs Actual"""
    result = (Pipeline()
        .budget.load('budget_q1_2024')
        .budget.compare('actual')
        .metrics.variance('amount')
        .report.generate('xlsx')
        .report.send(['finance@company.pl'])
        .execute())
    
    print('Comparison:', result)
    return result


def expense_categorization_example():
    """Example 6: Expense categorization"""
    result = (Pipeline()
        .data.load('expenses_2024')
        .budget.categorize('category')
        .transform.aggregate('category', 'sum')
        .transform.sort('amount', 'desc')
        .transform.limit(10)
        .execute())
    
    print('Top expenses:', result)
    return result


# ============================================================
# INVESTMENT EXAMPLES (planinwestycji.pl)
# ============================================================

def roi_analysis_example():
    """Example 7: ROI Analysis"""
    investment_data = {
        'initial_investment': 500000,
        'cash_flows': [
            {'period': 1, 'amount': 150000},
            {'period': 2, 'amount': 180000},
            {'period': 3, 'amount': 200000},
            {'period': 4, 'amount': 220000},
            {'period': 5, 'amount': 250000}
        ]
    }
    
    result = (Pipeline('planinwestycji.pl')
        .data.from_input(investment_data)
        .investment.analyze(discount_rate=0.12)
        .investment.roi()
        .investment.npv(0.1)
        .investment.payback()
        .execute())
    
    print('Investment analysis:', result)
    
    if result.get('status') == 'success':
        data = result.get('result', {})
        print(f"ROI: {data.get('roi', 'N/A')}%")
        print(f"NPV: {data.get('npv', 'N/A')} PLN")
        print(f"Payback: {data.get('payback_period', 'N/A')} years")
    
    return result


def scenario_comparison_example():
    """Example 8: Scenario comparison"""
    scenarios = ['optimistic', 'realistic', 'pessimistic']
    results = {}
    
    for scenario in scenarios:
        multiplier = 1.2 if scenario == 'optimistic' else (0.8 if scenario == 'pessimistic' else 1.0)
        
        result = (Pipeline()
            .data.load('investment_proposal')
            .investment.scenario(scenario, multiplier)
            .investment.analyze(discount_rate=0.1)
            .execute())
        
        results[scenario] = result
    
    print('Scenario comparison:', results)
    return results


# ============================================================
# MULTI-PLAN EXAMPLES (multiplan.pl)
# ============================================================

def multi_scenario_planning_example():
    """Example 9: Multi-scenario planning"""
    result = (Pipeline('multiplan.pl')
        .budget.load('budget_2025')
        .investment.scenario('growth', 1.15)
        .budget.variance()
        .forecast.predict(12, 'prophet')
        .report.generate('xlsx', 'scenario_planning')
        .execute())
    
    print('Scenario planning:', result)
    return result


def rolling_forecast_example():
    """Example 10: Rolling forecast"""
    result = (Pipeline()
        .data.load('actuals_ytd')
        .forecast.predict(6, 'prophet')
        .forecast.confidence(0.95)
        .budget.compare('planned')
        .report.generate('xlsx', 'rolling_forecast')
        .execute())
    
    print('Rolling forecast:', result)
    return result


# ============================================================
# ALERT EXAMPLES (alerts.pl)
# ============================================================

def budget_alert_example():
    """Example 11: Budget threshold alert"""
    result = (Pipeline('alerts.pl')
        .budget.load('current_budget')
        .metrics.calculate(['sum'], 'actual')
        .alert.threshold('utilization', 'gt', 0.9)
        .alert.send('slack', 'Budget threshold exceeded!')
        .execute())
    
    print('Alert result:', result)
    return result


# ============================================================
# FORECAST EXAMPLES (estymacja.pl)
# ============================================================

def sales_forecast_example():
    """Example 12: Sales forecast"""
    result = (Pipeline('estymacja.pl')
        .data.load('historical_sales')
        .forecast.predict(90, 'prophet')
        .forecast.trend()
        .forecast.seasonality()
        .forecast.confidence(0.95)
        .report.generate('pdf', 'forecast_report')
        .execute())
    
    print('Sales forecast:', result)
    return result


# ============================================================
# ASYNC EXAMPLES
# ============================================================

async def async_example():
    """Example 13: Async execution"""
    result = await (Pipeline()
        .data.load('sales')
        .metrics.calculate(['sum', 'avg'])
        .execute_async())
    
    print('Async result:', result)
    return result


async def parallel_pipelines_example():
    """Example 14: Parallel pipeline execution"""
    pipelines = [
        Pipeline().data.load('sales').metrics.sum('amount'),
        Pipeline().data.load('costs').metrics.sum('amount'),
        Pipeline().data.load('revenue').metrics.avg('amount')
    ]
    
    results = await asyncio.gather(
        *[p.execute_async() for p in pipelines]
    )
    
    print('Parallel results:', results)
    return results


# ============================================================
# STORED PIPELINES
# ============================================================

def stored_pipeline_example():
    """Example 15: Save and run stored pipeline"""
    # Save pipeline
    saved = Analytica.save_pipeline(
        name='monthly_report',
        dsl='budget.load("budget") | budget.variance() | report.generate("pdf")',
        description='Monthly financial report',
        domain='planbudzetu.pl',
        tags=['monthly', 'finance', 'report']
    )
    
    print('Saved pipeline:', saved)
    
    # Run it later
    result = Analytica.run_pipeline(
        saved['id'],
        variables={'month': '2024-12'}
    )
    
    print('Run result:', result)
    return result


# ============================================================
# EXPORT EXAMPLES
# ============================================================

def export_example():
    """Example 16: Export to multiple formats"""
    pipeline = (Pipeline()
        .data.load('financials')
        .transform.filter(year=2024)
        .metrics.calculate(['sum', 'avg', 'count']))
    
    # Get DSL representation
    print('DSL:', pipeline.to_dsl())
    print('JSON:', pipeline.to_json())
    
    # Execute and export
    result = (pipeline
        .export.to_csv('output.csv')
        .execute())
    
    print('Export result:', result)
    return result


# ============================================================
# COMPLEX PIPELINE
# ============================================================

def full_analysis_example():
    """Example 17: Full financial analysis"""
    result = (Pipeline()
        .name('full_analysis')
        .var('year', 2024)
        .var('budget_id', 'budget_2024')
        
        # Load and filter data
        .data.load('financials')
        .transform.filter(year='$year')
        
        # Calculate metrics
        .metrics.calculate(['sum', 'avg', 'count', 'min', 'max'])
        
        # Budget comparison
        .budget.compare('actual')
        .budget.variance()
        
        # Generate forecast
        .forecast.predict(6)
        .forecast.confidence(0.9)
        
        # Alert on variance
        .alert.threshold('variance_pct', 'gt', 10)
        
        # Generate report
        .report.generate('pdf', 'full_analysis')
        .report.send(['finance@company.pl'])
        
        # Export data
        .export.to_excel('analysis_2024.xlsx')
        
        .execute())
    
    print('Full analysis:', result)
    return result


# ============================================================
# DATA TRANSFORMATION
# ============================================================

def data_transformation_example():
    """Example 18: Complex data transformation"""
    result = (Pipeline()
        .data.load('transactions')
        .transform.filter(amount_gt=0, status='completed')
        .transform.rename(trx_date='date', trx_amount='amount')
        .transform.select('date', 'amount', 'category', 'vendor')
        .transform.group_by('category', 'vendor')
        .transform.aggregate('amount', 'sum')
        .transform.sort('total', 'desc')
        .transform.limit(20)
        .execute())
    
    print('Transformed data:', result)
    return result


# ============================================================
# USING WITH PANDAS
# ============================================================

def pandas_integration_example():
    """Example 19: Integration with pandas"""
    import pandas as pd
    
    # Create sample data
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=12, freq='M'),
        'revenue': [100000, 120000, 115000, 130000, 125000, 140000,
                   145000, 150000, 155000, 160000, 170000, 180000],
        'costs': [80000, 85000, 82000, 90000, 88000, 95000,
                 98000, 100000, 105000, 110000, 115000, 120000]
    })
    
    # Use pipeline with pandas data
    result = (Pipeline()
        .data.from_input(df.to_dict('records'))
        .metrics.calculate(['sum', 'avg'], 'revenue')
        .execute())
    
    print('Pandas result:', result)
    return result


# ============================================================
# CLI SIMULATION
# ============================================================

def cli_usage_example():
    """Example 20: CLI-like usage"""
    import sys
    
    # Simulate CLI arguments
    dsl_command = 'data.load("sales") | metrics.sum("amount")'
    
    # Parse and execute
    result = Analytica.parse(dsl_command)
    print('Parsed:', result)
    
    # Validate
    validation = Analytica.validate(dsl_command)
    print('Validation:', validation)
    
    # Execute
    if validation.get('valid', False):
        execution = run(dsl_command)
        print('Result:', execution)


# ============================================================
# RUN ALL EXAMPLES
# ============================================================

def main():
    """Run all examples"""
    print('=== ANALYTICA DSL Python Examples ===\n')
    
    examples = [
        ('Basic Example', basic_example),
        ('Variables Example', variables_example),
        ('ROI Analysis', roi_analysis_example),
        ('Budget Report', budget_report_example),
        ('Sales Forecast', sales_forecast_example),
        ('Full Analysis', full_analysis_example),
    ]
    
    for name, func in examples:
        print(f'\n--- {name} ---')
        try:
            func()
        except Exception as e:
            print(f'Error: {e}')
    
    # Async examples
    print('\n--- Async Examples ---')
    asyncio.run(async_example())
    
    print('\n=== All examples completed! ===')


if __name__ == '__main__':
    main()
