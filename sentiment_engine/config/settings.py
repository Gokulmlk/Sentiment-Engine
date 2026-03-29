"""
Configuration management for the sentiment engine
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///sentiment_engine.db"
    pool_size: int = 20
    max_overflow: int = 30
    echo: bool = False

@dataclass
class RedisConfig:
    url: str = "redis://localhost:6379"
    decode_responses: bool = True
    socket_keepalive: bool = True

@dataclass
class APIConfig:
    twitter_bearer_token: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    news_api_key: Optional[str] = None
    alpha_vantage_key: Optional[str] = None

@dataclass
class ProcessingConfig:
    max_queue_size: int = 2000
    batch_size: int = 50
    processing_interval: float = 0.1
    worker_threads: int = 4

@dataclass
class SignalConfig:
    buy_threshold: float = 0.3
    sell_threshold: float = -0.3
    confidence_threshold: float = 0.4
    cooldown_minutes: int = 5
    min_data_points: int = 5
    momentum_weight: float = 0.3
    volume_weight: float = 0.2
    fear_greed_weight: float = 0.3

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class DataSourceConfig:
    twitter_enabled: bool = True
    reddit_enabled: bool = True
    news_enabled: bool = True
    mock_data: bool = False
    rate_limits: Dict[str, int] = field(default_factory=lambda: {
        'twitter': 100,  # per 15 minutes
        'reddit': 60,    # per minute
        'news': 1000     # per day
    })

@dataclass
class Settings:
    environment: str = "development"
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    api_keys: APIConfig = field(default_factory=APIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)

def get_settings(environment: str = "development") -> Settings:
    """Load settings for the specified environment"""
    
    # Base configuration
    settings = Settings()
    settings.environment = environment
    
    # Load from YAML config file
    config_file = Path(__file__).parent.parent.parent / "configs" / f"{environment}.yml"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
            _update_settings_from_dict(settings, config_data)
    
    # Override with environment variables
    _load_from_environment(settings)
    
    return settings

def _update_settings_from_dict(settings: Settings, config_data: Dict[str, Any]):
    """Update settings from configuration dictionary"""
    for section, values in config_data.items():
        if hasattr(settings, section) and isinstance(values, dict):
            section_obj = getattr(settings, section)
            for key, value in values.items():
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)

def _load_from_environment(settings: Settings):
    """Load configuration from environment variables"""
    
    # API Keys
    settings.api_keys.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    settings.api_keys.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    settings.api_keys.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    settings.api_keys.news_api_key = os.getenv('NEWS_API_KEY')
    settings.api_keys.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
    
    # Database
    if os.getenv('DATABASE_URL'):
        settings.database.url = os.getenv('DATABASE_URL')
    
    # Redis
    if os.getenv('REDIS_URL'):
        settings.redis.url = os.getenv('REDIS_URL')
    
    # Logging
    if os.getenv('LOG_LEVEL'):
        settings.logging.level = os.getenv('LOG_LEVEL')
    if os.getenv('LOG_FILE'):
        settings.logging.file = os.getenv('LOG_FILE')
    
    # Debug mode
    if os.getenv('DEBUG'):
        settings.debug = os.getenv('DEBUG').lower() in ('true', '1', 'yes')