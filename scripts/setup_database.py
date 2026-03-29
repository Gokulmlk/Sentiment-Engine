#!/usr/bin/env python3
"""
Database setup script
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sentiment_engine.config.settings import get_settings

def setup_database():
    """Setup database tables and initial data"""
    print("Setting up database...")
    
    settings = get_settings("production")
    engine = create_engine(settings.database.url)
    
    # Create tables
    create_tables_sql = """
    -- Sentiment data table
    CREATE TABLE IF NOT EXISTS sentiment_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        source VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        sentiment_score DECIMAL(5,3),
        confidence DECIMAL(5,3),
        fear_greed_score DECIMAL(5,1),
        asset_mentions TEXT[],
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Trade signals table
    CREATE TABLE IF NOT EXISTS trade_signals (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        asset VARCHAR(20) NOT NULL,
        signal_type VARCHAR(10) NOT NULL,
        confidence DECIMAL(5,3),
        strength DECIMAL(5,3),
        risk_level VARCHAR(10),
        reasoning TEXT,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Performance metrics table
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id SERIAL PRIMARY KEY,
        metric_name VARCHAR(100) NOT NULL,
        metric_value DECIMAL(10,3),
        timestamp TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_sentiment_data_timestamp ON sentiment_data(timestamp);
    CREATE INDEX IF NOT EXISTS idx_sentiment_data_source ON sentiment_data(source);
    CREATE INDEX IF NOT EXISTS idx_trade_signals_timestamp ON trade_signals(timestamp);
    CREATE INDEX IF NOT EXISTS idx_trade_signals_asset ON trade_signals(asset);
    CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        
        print("✅ Database setup completed successfully")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()