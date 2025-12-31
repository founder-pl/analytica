-- ANALYTICA Framework - Database Initialization
-- Multi-tenant schema for all domains

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Organizations (tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(100),
    plan VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    sso_provider VARCHAR(50),
    sso_id VARCHAR(255),
    settings JSONB DEFAULT '{}',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Domain configurations
CREATE TABLE domain_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(100) UNIQUE NOT NULL,
    org_id UUID REFERENCES organizations(id),
    config JSONB NOT NULL DEFAULT '{}',
    theme JSONB DEFAULT '{}',
    enabled_modules TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- DATA SOURCES
-- ============================================================

-- Integration connections
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- ifirma, fakturownia, excel, etc.
    credentials_encrypted BYTEA,
    settings JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Datasets
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    connection_id UUID REFERENCES connections(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schema JSONB,
    refresh_schedule VARCHAR(100),
    last_refresh TIMESTAMP WITH TIME ZONE,
    row_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- REPORTS MODULE
-- ============================================================

CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(100),
    config JSONB NOT NULL DEFAULT '{}',
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES report_templates(id),
    domain VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    format VARCHAR(50) DEFAULT 'pdf',
    status VARCHAR(50) DEFAULT 'pending',
    file_url TEXT,
    schedule VARCHAR(100),
    last_generated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- ============================================================
-- ALERTS MODULE
-- ============================================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metric VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL, -- gt, lt, eq, change_pct
    threshold DECIMAL(20, 4) NOT NULL,
    channels TEXT[] DEFAULT '{email}',
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_value DECIMAL(20, 4),
    threshold_value DECIMAL(20, 4),
    channels_notified TEXT[],
    status VARCHAR(50) DEFAULT 'sent'
);

-- ============================================================
-- BUDGET MODULE (multiplan.pl, planbudzetu.pl)
-- ============================================================

CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    scenario VARCHAR(100) DEFAULT 'realistic',
    status VARCHAR(50) DEFAULT 'draft',
    total_planned DECIMAL(20, 2) DEFAULT 0,
    total_actual DECIMAL(20, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'PLN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id)
);

CREATE TABLE budget_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES budget_categories(id),
    color VARCHAR(7),
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE budget_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID REFERENCES budgets(id) ON DELETE CASCADE,
    category_id UUID REFERENCES budget_categories(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    planned_amount DECIMAL(20, 2) NOT NULL DEFAULT 0,
    actual_amount DECIMAL(20, 2) DEFAULT 0,
    period_month INTEGER, -- 1-12 for monthly breakdown
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE budget_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID REFERENCES budgets(id) ON DELETE CASCADE,
    budget_item_id UUID REFERENCES budget_items(id),
    category_id UUID REFERENCES budget_categories(id),
    transaction_date DATE NOT NULL,
    amount DECIMAL(20, 2) NOT NULL,
    description TEXT,
    vendor VARCHAR(255),
    reference VARCHAR(255),
    imported_from VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INVESTMENT MODULE (planinwestycji.pl)
-- ============================================================

CREATE TABLE investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    domain VARCHAR(100) DEFAULT 'planinwestycji.pl',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    investment_type VARCHAR(100), -- capex, rd, marketing, hr, digital
    initial_investment DECIMAL(20, 2) NOT NULL,
    discount_rate DECIMAL(10, 4) DEFAULT 0.1,
    currency VARCHAR(3) DEFAULT 'PLN',
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    -- Calculated metrics (cached)
    roi DECIMAL(10, 2),
    npv DECIMAL(20, 2),
    irr DECIMAL(10, 4),
    payback_period DECIMAL(10, 2),
    profitability_index DECIMAL(10, 4),
    risk_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id)
);

CREATE TABLE investment_cash_flows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investment_id UUID REFERENCES investments(id) ON DELETE CASCADE,
    period INTEGER NOT NULL, -- 0 = initial, 1+ = future periods
    period_date DATE,
    amount DECIMAL(20, 2) NOT NULL,
    description TEXT,
    probability DECIMAL(5, 2) DEFAULT 1.0, -- for scenario analysis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE investment_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investment_id UUID REFERENCES investments(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- optimistic, realistic, pessimistic
    multiplier DECIMAL(5, 2) DEFAULT 1.0,
    roi DECIMAL(10, 2),
    npv DECIMAL(20, 2),
    risk_assessment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- FORECAST MODULE
-- ============================================================

CREATE TABLE forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES datasets(id),
    domain VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    model_type VARCHAR(100) DEFAULT 'prophet',
    parameters JSONB DEFAULT '{}',
    periods INTEGER DEFAULT 30,
    confidence DECIMAL(5, 2) DEFAULT 0.95,
    status VARCHAR(50) DEFAULT 'pending',
    results JSONB,
    metrics JSONB, -- MAE, RMSE, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================
-- BILLING
-- ============================================================

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    domain VARCHAR(100),
    metric VARCHAR(100) NOT NULL, -- reports, alerts, forecasts, voice_minutes
    value INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_users_org ON users(org_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_connections_org ON connections(org_id);
CREATE INDEX idx_datasets_org ON datasets(org_id);
CREATE INDEX idx_reports_org ON reports(org_id);
CREATE INDEX idx_reports_domain ON reports(domain);
CREATE INDEX idx_alerts_org ON alerts(org_id);
CREATE INDEX idx_alerts_domain ON alerts(domain);
CREATE INDEX idx_budgets_org ON budgets(org_id);
CREATE INDEX idx_budgets_domain ON budgets(domain);
CREATE INDEX idx_budget_items_budget ON budget_items(budget_id);
CREATE INDEX idx_investments_org ON investments(org_id);
CREATE INDEX idx_forecasts_org ON forecasts(org_id);
CREATE INDEX idx_usage_org_date ON usage_records(org_id, recorded_at);

-- ============================================================
-- DEFAULT DATA
-- ============================================================

-- Insert default budget categories
INSERT INTO budget_categories (id, org_id, name, color, sort_order) VALUES
    (uuid_generate_v4(), NULL, 'Wynagrodzenia', '#EF4444', 1),
    (uuid_generate_v4(), NULL, 'Usługi zewnętrzne', '#F97316', 2),
    (uuid_generate_v4(), NULL, 'Marketing', '#F59E0B', 3),
    (uuid_generate_v4(), NULL, 'IT i oprogramowanie', '#10B981', 4),
    (uuid_generate_v4(), NULL, 'Biuro i administracja', '#3B82F6', 5),
    (uuid_generate_v4(), NULL, 'Podróże służbowe', '#8B5CF6', 6),
    (uuid_generate_v4(), NULL, 'Szkolenia', '#EC4899', 7),
    (uuid_generate_v4(), NULL, 'Pozostałe', '#6B7280', 8);

-- Insert default report templates
INSERT INTO report_templates (domain, name, template_type, config, is_system) VALUES
    ('multiplan.pl', 'Budżet vs Realizacja', 'budget_vs_actual', '{"sections": ["summary", "categories", "variance", "trends"]}', TRUE),
    ('multiplan.pl', 'Porównanie scenariuszy', 'scenario_comparison', '{"sections": ["scenarios", "metrics", "recommendation"]}', TRUE),
    ('planbudzetu.pl', 'Raport miesięczny', 'monthly_budget', '{"sections": ["income", "expenses", "balance", "categories"]}', TRUE),
    ('planbudzetu.pl', 'Analiza wydatków', 'expense_analysis', '{"sections": ["by_category", "by_vendor", "trends"]}', TRUE),
    ('planinwestycji.pl', 'Propozycja inwestycyjna', 'investment_proposal', '{"sections": ["summary", "roi", "npv", "risk", "recommendation"]}', TRUE),
    ('planinwestycji.pl', 'Analiza ROI', 'roi_analysis', '{"sections": ["metrics", "scenarios", "sensitivity"]}', TRUE);

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_organizations_timestamp BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_connections_timestamp BEFORE UPDATE ON connections FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_datasets_timestamp BEFORE UPDATE ON datasets FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMIT;
