"""
Data models for the sentiment engine
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class DataSource(Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWS = "news"
    CUSTOM = "custom"

@dataclass
class SentimentData:
    """Data class for sentiment analysis results"""
    timestamp: datetime
    source: DataSource
    content: str
    sentiment_score: float  # -1 to 1
    confidence: float       # 0 to 1
    asset_mentions: List[str]
    fear_greed_score: float  # 0-100 scale
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'content': self.content,
            'sentiment_score': self.sentiment_score,
            'confidence': self.confidence,
            'asset_mentions': self.asset_mentions,
            'fear_greed_score': self.fear_greed_score,
            'metadata': self.metadata or {}
        }

@dataclass
class TradeSignal:
    """Data class for trade signals"""
    timestamp: datetime
    asset: str
    signal_type: SignalType
    confidence: float           # 0 to 1
    strength: float            # 0 to 1
    expected_duration: str
    risk_level: RiskLevel
    reasoning: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'asset': self.asset,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'strength': self.strength,
            'expected_duration': self.expected_duration,
            'risk_level': self.risk_level.value,
            'reasoning': self.reasoning,
            'metadata': self.metadata or {}
        }

@dataclass
class MarketSummary:
    """Market sentiment summary data"""
    timestamp: datetime
    market_mood: str
    sentiment_score: float
    sentiment_trend: str
    fear_greed_index: float
    fear_greed_level: str
    data_points_analyzed: int
    processing_rate: float
    recent_signals_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'market_mood': self.market_mood,
            'sentiment_score': self.sentiment_score,
            'sentiment_trend': self.sentiment_trend,
            'fear_greed_index': self.fear_greed_index,
            'fear_greed_level': self.fear_greed_level,
            'data_points_analyzed': self.data_points_analyzed,
            'processing_rate': self.processing_rate,
            'recent_signals_count': self.recent_signals_count
        }

@dataclass
class AssetAnalysis:
    """Asset-specific analysis data"""
    asset: str
    sentiment_score: float
    sentiment_trend: str
    confidence: float
    fear_greed_score: float
    volatility: float
    data_points: int
    recommendation: str
    last_signal: Optional[str] = None
    last_signal_time: Optional[datetime] = None
    sources: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'sentiment_score': self.sentiment_score,
            'sentiment_trend': self.sentiment_trend,
            'confidence': self.confidence,
            'fear_greed_score': self.fear_greed_score,
            'volatility': self.volatility,
            'data_points': self.data_points,
            'recommendation': self.recommendation,
            'last_signal': self.last_signal,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'sources': self.sources or []}