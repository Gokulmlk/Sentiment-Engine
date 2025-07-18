"""
Fear & Greed Sentiment Engine
A comprehensive sentiment analysis and trade signal generation system
"""

__version__ = "1.0.0"
__author__ = "Sentiment Engine Team"
__email__ = "team@sentimentengine.com"

from .core.engine import FearGreedEngine
from .core.sentiment_analyzer import SentimentAnalyzer
from .core.signal_generator import SignalGenerator
from .core.data_models import SentimentData, TradeSignal

__all__ = [
    'FearGreedEngine',
    'SentimentAnalyzer', 
    'SignalGenerator',
    'SentimentData',
    'TradeSignal'
]