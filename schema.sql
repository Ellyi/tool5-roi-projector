CREATE TABLE IF NOT EXISTS roi_projections (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    email VARCHAR(255),
    process_name VARCHAR(255) NOT NULL,
    hours_per_week INTEGER NOT NULL,
    people_count INTEGER NOT NULL,
    hourly_cost DECIMAL(10,2) NOT NULL,
    current_tools_cost DECIMAL(10,2) DEFAULT 0,
    timeline_expectation VARCHAR(100),
    annual_cost_current DECIMAL(10,2) NOT NULL,
    annual_cost_with_ai DECIMAL(10,2) NOT NULL,
    annual_savings DECIMAL(10,2) NOT NULL,
    implementation_cost DECIMAL(10,2) NOT NULL,
    breakeven_months INTEGER NOT NULL,
    roi_percentage DECIMAL(10,2) NOT NULL,
    risk_level VARCHAR(50),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roi_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    frequency INTEGER DEFAULT 1,
    avg_savings DECIMAL(10,2),
    avg_roi DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(pattern_type, pattern_data)
);

CREATE TABLE IF NOT EXISTS roi_insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(50),
    insight_text TEXT NOT NULL,
    confidence DECIMAL(3,2),
    supporting_data JSONB,
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    projection_id INTEGER REFERENCES roi_projections(id),
    user_context JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roi_created ON roi_projections(created_at);
CREATE INDEX IF NOT EXISTS idx_roi_industry ON roi_projections(industry);
CREATE INDEX IF NOT EXISTS idx_roi_savings ON roi_projections(annual_savings);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON roi_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_insights_type ON roi_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_date ON roi_insights(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_expires_at ON sessions(expires_at);