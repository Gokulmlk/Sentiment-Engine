"""
Advanced trade signal generation with multiple strategies
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque, defaultdict

from .data_models import SentimentData, TradeSignal, SignalType, RiskLevel
from ..utils.exceptions import SignalGenerationError

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Advanced trade signal generation with multiple strategies"""
    
    def __init__(self, config: Dict = None):
        """Initialize signal generator with configuration"""
        self.config = config or {}
        
        # Signal history and storage
        self.sentiment_history = defaultdict(lambda: deque(maxlen=200))
        self.signals = deque(maxlen=100)
        self.last_signal_time = defaultdict(lambda: datetime.min)
        self.signal_performance = []
        
        # Default configuration
        self.default_config = {
            'buy_threshold': 0.3,
            'sell_threshold': -0.3,
            'confidence_threshold': 0.4,
            'signal_cooldown_minutes': 5,
            'min_data_points': 5,
            'momentum_weight': 0.3,
            'volume_weight': 0.2,
            'fear_greed_weight': 0.3
        }
        
        # Merge with provided config
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        logger.info(f"Signal generator initialized with config: {self.config}")
    
    def update_config(self, new_config: Dict):
        """Update signal generation parameters"""
        self.config.update(new_config)
        logger.info(f"Signal generator config updated: {new_config}")
    
    def process_sentiment_data(self, sentiment_data: SentimentData):
        """Process sentiment data and generate signals"""
        try:
            # Store sentiment history for each mentioned asset
            for asset in sentiment_data.asset_mentions:
                self.sentiment_history[asset].append(sentiment_data)
                self._generate_signal(asset)
            
            # Also process for general market sentiment
            self.sentiment_history['MARKET'].append(sentiment_data)
            
        except Exception as e:
            logger.error(f"Error processing sentiment data: {e}")
            raise SignalGenerationError(f"Failed to process sentiment data: {e}")
    
    def _generate_signal(self, asset: str):
        """Generate trading signal for specific asset using multiple factors"""
        try:
            history = self.sentiment_history[asset]
            
            if len(history) < self.config['min_data_points']:
                return
            
            # Check cooldown period
            cooldown = timedelta(minutes=self.config['signal_cooldown_minutes'])
            if datetime.now() - self.last_signal_time[asset] < cooldown:
                return
            
            signal = self._calculate_signal(asset, history)
            if signal and signal.signal_type != SignalType.HOLD:
                self.signals.append(signal)
                self.last_signal_time[asset] = datetime.now()
                logger.info(f"Signal generated: {signal.signal_type.value} {signal.asset} "
                           f"(strength={signal.strength:.2f}, confidence={signal.confidence:.2f})")
        
        except Exception as e:
            logger.error(f"Signal generation error for {asset}: {e}")
    
    def _calculate_signal(self, asset: str, history: deque) -> Optional[TradeSignal]:
        """Calculate trading signal using multiple factors"""
        try:
            recent_data = list(history)[-20:]  # Last 20 data points
            
            # Calculate basic metrics
            sentiments = [d.sentiment_score for d in recent_data]
            confidences = [d.confidence for d in recent_data]
            fear_greed_scores = [d.fear_greed_score for d in recent_data]
            
            avg_sentiment = statistics.mean(sentiments)
            avg_confidence = statistics.mean(confidences)
            avg_fear_greed = statistics.mean(fear_greed_scores)
            
            # Calculate momentum (trend direction)
            momentum = 0
            if len(recent_data) >= 10:
                early_sentiment = statistics.mean(sentiments[:10])
                late_sentiment = statistics.mean(sentiments[-10:])
                momentum = late_sentiment - early_sentiment
            
            # Calculate volatility (signal stability)
            sentiment_volatility = statistics.stdev(sentiments) if len(sentiments) > 1 else 0
            
            # Multi-factor signal calculation
            base_score = avg_sentiment
            momentum_score = momentum * self.config['momentum_weight']
            fear_greed_adjustment = self._calculate_fear_greed_adjustment(avg_fear_greed)
            volatility_penalty = -sentiment_volatility * 0.2
            
            final_score = base_score + momentum_score + fear_greed_adjustment + volatility_penalty
            
            # Confidence calculation
            confidence = min(avg_confidence * (1 - sentiment_volatility), 1.0)
            
            # Signal generation logic
            if confidence < self.config['confidence_threshold']:
                return None
            
            signal_type = SignalType.HOLD
            strength = 0
            reasoning = []
            
            if final_score > self.config['buy_threshold']:
                signal_type = SignalType.BUY
                strength = min(final_score, 1.0)
                reasoning.append(f"Positive sentiment: {avg_sentiment:.2f}")
                if momentum > 0.1:
                    reasoning.append(f"Strong momentum: {momentum:.2f}")
            
            elif final_score < self.config['sell_threshold']:
                signal_type = SignalType.SELL
                strength = min(abs(final_score), 1.0)
                reasoning.append(f"Negative sentiment: {avg_sentiment:.2f}")
                if momentum < -0.1:
                    reasoning.append(f"Negative momentum: {momentum:.2f}")
            
            # Risk assessment
            risk_level = self._assess_risk(strength, sentiment_volatility, avg_fear_greed)
            
            # Expected duration based on signal strength and volatility
            duration = self._calculate_expected_duration(strength, sentiment_volatility)
            
            if signal_type != SignalType.HOLD:
                return TradeSignal(
                    timestamp=datetime.now(),
                    asset=asset,
                    signal_type=signal_type,
                    confidence=confidence,
                    strength=strength,
                    expected_duration=duration,
                    risk_level=risk_level,
                    reasoning="; ".join(reasoning)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating signal for {asset}: {e}")
            return None
    
    def _calculate_fear_greed_adjustment(self, fear_greed_score: float) -> float:
        """Calculate adjustment based on fear/greed levels (contrarian approach)"""
        if fear_greed_score > 80:  # Extreme greed
            return -0.2  # Contrarian sell signal
        elif fear_greed_score < 20:  # Extreme fear
            return 0.2   # Contrarian buy signal
        else:
            return 0  # No adjustment for neutral levels
    
    def _assess_risk(self, strength: float, volatility: float, fear_greed: float) -> RiskLevel:
        """Assess risk level of the signal"""
        risk_score = strength + volatility
        
        if fear_greed > 75 or fear_greed < 25:
            risk_score += 0.3  # Higher risk in extreme sentiment
        
        if risk_score > 1.0:
            return RiskLevel.HIGH
        elif risk_score > 0.6:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_expected_duration(self, strength: float, volatility: float) -> str:
        """Calculate expected signal duration"""
        if strength > 0.8 and volatility < 0.3:
            return "4-24 hours"
        elif strength > 0.5:
            return "1-6 hours"
        else:
            return "30min-2 hours"
    
    def get_recent_signals(self, count: int = 10) -> List[TradeSignal]:
        """Get recent trading signals"""
        try:
            return list(self.signals)[-count:]
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    def get_signal_performance(self) -> Dict:
        """Get signal performance metrics"""
        try:
            if not self.signal_performance:
                return {"message": "No performance data available yet"}
            
            total_signals = len(self.signal_performance)
            profitable_signals = sum(1 for p in self.signal_performance if p > 0)
            
            return {
                "total_signals": total_signals,
                "profitable_signals": profitable_signals,
                "win_rate": profitable_signals / total_signals if total_signals > 0 else 0,
                "average_return": statistics.mean(self.signal_performance) if self.signal_performance else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal performance: {e}")
            return {"error": f"Failed to calculate performance: {e}"}
    
    def add_signal_performance(self, performance: float):
        """Add signal performance data for tracking"""
        try:
            self.signal_performance.append(performance)
            # Keep only recent performance data
            if len(self.signal_performance) > 1000:
                self.signal_performance = self.signal_performance[-500:]
        except Exception as e:
            logger.error(f"Error adding signal performance: {e}")
    
    def get_asset_signal_history(self, asset: str, count: int = 20) -> List[TradeSignal]:
        """Get signal history for specific asset"""
        try:
            asset_signals = [s for s in self.signals if s.asset.upper() == asset.upper()]
            return asset_signals[-count:]
        except Exception as e:
            logger.error(f"Error getting asset signal history: {e}")
            return []
    
    def get_signal_statistics(self) -> Dict:
        """Get comprehensive signal statistics"""
        try:
            if not self.signals:
                return {"message": "No signals generated yet"}
            
            signals_list = list(self.signals)
            
            # Signal type distribution
            buy_count = sum(1 for s in signals_list if s.signal_type == SignalType.BUY)
            sell_count = sum(1 for s in signals_list if s.signal_type == SignalType.SELL)
            
            # Asset distribution
            asset_counts = defaultdict(int)
            for signal in signals_list:
                asset_counts[signal.asset] += 1
            
            # Risk distribution
            risk_counts = defaultdict(int)
            for signal in signals_list:
                risk_counts[signal.risk_level.value] += 1
            
            # Time distribution (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_signals = [s for s in signals_list if s.timestamp >= recent_cutoff]
            
            # Average metrics
            avg_confidence = statistics.mean([s.confidence for s in signals_list]) if signals_list else 0
            avg_strength = statistics.mean([s.strength for s in signals_list]) if signals_list else 0
            
            return {
                "total_signals": len(signals_list),
                "recent_24h_signals": len(recent_signals),
                "signal_types": {
                    "buy": buy_count,
                    "sell": sell_count,
                    "buy_percentage": round(buy_count / len(signals_list) * 100, 1) if signals_list else 0,
                    "sell_percentage": round(sell_count / len(signals_list) * 100, 1) if signals_list else 0
                },
                "top_assets": dict(sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "risk_distribution": dict(risk_counts),
                "average_confidence": round(avg_confidence, 3),
                "average_strength": round(avg_strength, 3),
                "signal_frequency": len(recent_signals) / 24 if recent_signals else 0  # signals per hour
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal statistics: {e}")
            return {"error": f"Failed to calculate statistics: {e}"}