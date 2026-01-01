# ANALYTICA Desktop - Investment Analysis Pipelines
# =================================================

# ============================================================
# QUICK ROI CALCULATOR
# ============================================================

@pipeline quick_roi:
    data.from_input()
    | investment.roi()
    | view.card(value="roi", title="Return on Investment", icon="📈", style="success", format="percent")


# ============================================================
# FULL INVESTMENT ANALYSIS
# ============================================================

@pipeline full_investment_analysis:
    $initial = 1000000
    $rate = 0.12
    $flows = [200000, 300000, 400000, 500000, 600000]
    
    investment.analyze(
        name="Investment Analysis",
        initial_investment=$initial,
        discount_rate=$rate,
        cash_flows=$flows
    )
    
    # Calculate all metrics
    | investment.npv(rate=$rate)
    | investment.irr()
    | investment.payback()
    
    # Generate views
    | view.card(value="npv", title="Net Present Value", icon="💰", style="success", format="currency")
    | view.card(value="roi", title="ROI", icon="📈", style="info", format="percent")
    | view.card(value="irr", title="Internal Rate of Return", icon="📊", style="default", format="percent")
    | view.card(value="payback_period", title="Payback Period", icon="⏱️", style="warning")
    | view.card(value="profitability_index", title="Profitability Index", icon="✅", style="info")
    
    # Cash flow chart
    | view.chart(type="bar", x="period", y="cash_flow", title="Annual Cash Flows")
    
    # Detailed table
    | view.table(
        columns=["period", "cash_flow", "cumulative", "discounted_cf", "cumulative_dcf"],
        title="Cash Flow Analysis"
    )


# ============================================================
# SCENARIO COMPARISON
# ============================================================

@pipeline scenario_comparison:
    $base_investment = 500000
    
    # Optimistic scenario
    investment.analyze(
        name="Optimistic",
        initial_investment=$base_investment,
        discount_rate=0.10,
        cash_flows=[150000, 200000, 250000, 300000]
    )
    | investment.scenario(name="optimistic", multiplier=1.2)
    
    # Pessimistic scenario
    | investment.analyze(
        name="Pessimistic",
        initial_investment=$base_investment,
        discount_rate=0.15,
        cash_flows=[100000, 120000, 140000, 160000]
    )
    | investment.scenario(name="pessimistic", multiplier=0.8)
    
    # Compare
    | view.chart(type="bar", x="scenario", y="npv", title="NPV by Scenario")
    | view.table(columns=["scenario", "npv", "roi", "payback_period"], title="Scenario Comparison")


# ============================================================
# REAL ESTATE INVESTMENT
# ============================================================

@pipeline real_estate_analysis:
    $purchase_price = 2000000
    $rental_income = [180000, 185000, 190000, 200000, 210000]
    $sale_price = 2500000
    
    investment.analyze(
        name="Real Estate Investment",
        initial_investment=$purchase_price,
        discount_rate=0.08,
        cash_flows=$rental_income
    )
    | investment.npv(rate=0.08)
    | investment.payback()
    
    | view.card(value="npv", title="Property NPV", icon="🏠", style="success", format="currency")
    | view.card(value="roi", title="ROI", icon="📈", style="info", format="percent")
    | view.chart(type="line", x="year", y="rental_income", title="Rental Income Projection")


# ============================================================
# STARTUP INVESTMENT
# ============================================================

@pipeline startup_investment:
    $seed_round = 500000
    $series_a = 2000000
    
    investment.analyze(
        name="Startup Investment",
        initial_investment=$seed_round,
        discount_rate=0.25,
        cash_flows=[-500000, -200000, 100000, 500000, 2000000, 5000000]
    )
    | investment.irr()
    
    | view.card(value="irr", title="Expected IRR", icon="🚀", style="success", format="percent")
    | view.chart(type="area", x="year", y="cash_flow", title="Cash Flow Timeline")
    
    # Risk alert
    | alert.threshold(metric="irr", operator="lt", threshold=0.15)


# ============================================================
# DESKTOP DEPLOYMENT
# ============================================================

@pipeline deploy_desktop_investment:
    deploy.desktop(
        framework="electron",
        platforms=["win", "mac", "linux"],
        release=true,
        url="http://localhost:18000"
    )
    | deploy.github_actions(
        workflow="build-investment-app",
        triggers=["push", "release"],
        branches=["main"]
    )
