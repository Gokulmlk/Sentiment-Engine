"""
Utility helper functions
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any

def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    if config.get('file'):
        log_file = Path(config['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.get('level', 'INFO')))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.get('format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if configured)
    if config.get('file'):
        file_handler = logging.handlers.RotatingFileHandler(
            config['file'],
            maxBytes=config.get('max_bytes', 10*1024*1024),
            backupCount=config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def format_number(value: float, decimals: int = 2) -> str:
    """Format number with specified decimal places"""
    return f"{value:.{decimals}f}"

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0 if new_value == 0 else float('inf')
    return ((new_value - old_value) / old_value) * 100

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def validate_asset_symbol(symbol: str) -> bool:
    """Validate asset symbol format"""
    if not symbol:
        return False
    
    # Basic validation - alphanumeric, 1-10 characters
    return symbol.isalnum() and 1 <= len(symbol) <= 10