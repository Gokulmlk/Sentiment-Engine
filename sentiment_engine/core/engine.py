"""
Main Fear & Greed Sentiment Engine - FIXED VERSION
"""

import threading
import time
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import deque, defaultdict

from .sentiment_analyzer import SentimentAnalyzer
from .signal_generator import SignalGenerator
from .data_models import SentimentData, TradeSignal, MarketSummary, AssetAnalysis
from ..utils.exceptions import SentimentEngineError

logger = logging.getLogger(__name__)

class FearGreedEngine:
    """Main sentiment engine coordinating all components"""
    
    def __init__(self, settings: Union[Dict, object] = None):
        """Initialize the Fear & Greed Engine with flexible settings"""
        self.settings = self._normalize_settings(settings)
        self.running = False
        self.start_time = None
        
        # Initialize core components
        self.sentiment_analyzer = SentimentAnalyzer(self.settings.get('sentiment', {}))
        self.signal_generator = SignalGenerator(self.settings.get('signals', {}))
        
        # Initialize data ingestion sources
        self.data_sources = {}
        self._initialize_data_sources()
        
        # Analytics storage
        self.market_sentiment_history = deque(maxlen=2000)
        self.fear_greed_history = deque(maxlen=2000)
        
        # Performance metrics
        self.performance_metrics = {
            'processed_messages': 0,
            'generated_signals': 0,
            'processing_errors': 0,
            'uptime_seconds': 0
        }
        
        # Threading
        self.main_thread = None
        self.analytics_thread = None
        
        logger.info("Fear & Greed Engine initialized")
    
    def _normalize_settings(self, settings: Union[Dict, object, None]) -> Dict:
        """Convert settings to dictionary format"""
        if settings is None:
            return self._get_default_settings()
        
        # If it's already a dictionary, return as-is
        if isinstance(settings, dict):
            return settings
        
        # If it's an object with attributes, convert to dict
        if hasattr(settings, '__dict__'):
            normalized = {}
            
            # Convert each attribute to dict
            for attr_name in dir(settings):
                if not attr_name.startswith('_'):
                    attr_value = getattr(settings, attr_name)
                    if hasattr(attr_value, '__dict__') and not callable(attr_value):
                        # Convert nested objects to dict
                        normalized[attr_name] = {
                            sub_attr: getattr(attr_value, sub_attr)
                            for sub_attr in dir(attr_value)
                            if not sub_attr.startswith('_') and not callable(getattr(attr_value, sub_attr))
                        }
                    elif not callable(attr_value):
                        normalized[attr_name] = attr_value
            
            return normalized
        
        # Fallback to default settings
        return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """Get default settings if none provided"""
        return {
            'sentiment': {},
            'signals': {
                'buy_threshold': 0.3,
                'sell_threshold': -0.3,
                'confidence_threshold': 0.4,
                'signal_cooldown_minutes': 5,
                'min_data_points': 5
            },
            'data_sources': {
                'twitter_enabled': True,
                'reddit_enabled': True,
                'news_enabled': True,
                'mock_data': True,
                'rate_limits': {
                    'twitter': 100,
                    'reddit': 60,
                    'news': 1000
                }
            },
            'processing': {
                'max_queue_size': 2000,
                'batch_size': 50,
                'processing_interval': 0.1
            },
            'api_keys': {
                'twitter_bearer_token': None,
                'reddit_client_id': None,
                'reddit_client_secret': None,
                'news_api_key': None
            }
        }
    
    def _initialize_data_sources(self):
        """Initialize data ingestion sources"""
        try:
            data_config = self.settings.get('data_sources', {})
            api_keys = self.settings.get('api_keys', {})
            
            # Twitter ingestion
            if data_config.get('twitter_enabled', True):
                twitter_config = {
                    'bearer_token': api_keys.get('twitter_bearer_token'),
                    'mock_data': data_config.get('mock_data', True),
                    'rate_limit_delay': 2.0,
                    'search_terms': ['bitcoin', 'ethereum', 'crypto', 'stocks', 'trading']
                }
                try:
                    from ..data_ingestion.twitter_ingestion import TwitterIngestionSource
                    self.data_sources['twitter'] = TwitterIngestionSource(
                        self.sentiment_analyzer, twitter_config
                    )
                except ImportError:
                    logger.warning("TwitterIngestionSource not available, using mock data")
                    self._create_mock_source('twitter')
            
            # Reddit ingestion
            if data_config.get('reddit_enabled', True):
                reddit_config = {
                    'client_id': api_keys.get('reddit_client_id'),
                    'client_secret': api_keys.get('reddit_client_secret'),
                    'mock_data': data_config.get('mock_data', True),
                    'rate_limit_delay': 3.0,
                    'subreddits': ['investing', 'cryptocurrency', 'stocks', 'wallstreetbets']
                }
                try:
                    from ..data_ingestion.reddit_ingestion import RedditIngestionSource
                    self.data_sources['reddit'] = RedditIngestionSource(
                        self.sentiment_analyzer, reddit_config
                    )
                except ImportError:
                    logger.warning("RedditIngestionSource not available, using mock data")
                    self._create_mock_source('reddit')
            
            # News ingestion
            if data_config.get('news_enabled', True):
                news_config = {
                    'api_key': api_keys.get('news_api_key'),
                    'mock_data': data_config.get('mock_data', True),
                    'rate_limit_delay': 5.0,
                    'sources': ['reuters', 'bloomberg', 'cnbc']
                }
                try:
                    from ..data_ingestion.news_ingestion import NewsIngestionSource
                    self.data_sources['news'] = NewsIngestionSource(
                        self.sentiment_analyzer, news_config
                    )
                except ImportError:
                    logger.warning("NewsIngestionSource not available, using mock data")
                    self._create_mock_source('news')
            
            logger.info(f"Initialized {len(self.data_sources)} data sources")
            
        except Exception as e:
            logger.error(f"Error initializing data sources: {e}")
            # Create at least one mock source for demo purposes
            self._create_mock_source('demo')
    
    def _create_mock_source(self, source_name: str):
        """Create a simple mock data source for demo purposes"""
        from ..core.data_models import DataSource, SentimentData
        import random
        
        class MockSource:
            def __init__(self, sentiment_analyzer, config):
                self.sentiment_analyzer = sentiment_analyzer
                self.config = config
                self.running = False
                self.data_queue = deque(maxlen=1000)
                self.processed_count = 0
                self.error_count = 0
                self.thread = None
                
                self.mock_data = [
                    "🚀 Bitcoin breaking $50k resistance! This bull run is just getting started #BTC #crypto",
                    "⚠️ Market looking shaky. Major correction incoming? Time to take profits #bearish",
                    "TSLA earnings absolutely crushed expectations! $1000 PT looking realistic 📈",
                    "VIX spiking to dangerous levels. Black swan event brewing? #volatility #SPY",
                    "Ethereum 2.0 upgrade complete! ETH to the moon! 🌙 #ETH #DeFi",
                    "Fed hawkish tone causing panic selling across all sectors. Cash is king right now",
                    "Diamond hands paying off! 💎🙌 HODL through the FUD #crypto #bitcoin",
                    "This feels like 2008 all over again. Recession warning signals everywhere",
                    "FOMO kicking in hard! Everyone rushing into crypto markets #FOMO #altcoins",
                    "Technical analysis shows SPY ready for major breakout above 450 resistance"
                ]
            
            @property
            def source_type(self):
                return DataSource.TWITTER if source_name == 'twitter' else DataSource.REDDIT if source_name == 'reddit' else DataSource.NEWS
            
            def start(self):
                if self.running:
                    return
                self.running = True
                self.thread = threading.Thread(target=self._mock_loop, daemon=True)
                self.thread.start()
                logger.info(f"Started mock {source_name} source")
            
            def stop(self):
                self.running = False
                if self.thread:
                    self.thread.join(timeout=5)
                logger.info(f"Stopped mock {source_name} source")
            
            def _mock_loop(self):
                while self.running:
                    try:
                        content = random.choice(self.mock_data)
                        self._process_content(content)
                        time.sleep(random.uniform(2, 5))
                    except Exception as e:
                        logger.error(f"Mock source error: {e}")
                        time.sleep(5)
            
            def _process_content(self, content: str):
                try:
                    sentiment_score, confidence, fear_greed_score = self.sentiment_analyzer.analyze_sentiment(content)
                    asset_mentions = self.sentiment_analyzer.extract_assets(content)
                    
                    sentiment_data = SentimentData(
                        timestamp=datetime.now(),
                        source=self.source_type,
                        content=content,
                        sentiment_score=sentiment_score,
                        confidence=confidence,
                        asset_mentions=asset_mentions,
                        fear_greed_score=fear_greed_score
                    )
                    
                    self.data_queue.append(sentiment_data)
                    self.processed_count += 1
                    
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Mock content processing error: {e}")
        
        self.data_sources[source_name] = MockSource(self.sentiment_analyzer, {})
    
    def start_engine(self):
        """Start the sentiment analysis engine"""
        if self.running:
            logger.warning("Engine already running")
            return
        
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # Start data ingestion sources
            for name, source in self.data_sources.items():
                try:
                    source.start()
                    logger.info(f"Started {name} data source")
                except Exception as e:
                    logger.error(f"Failed to start {name} data source: {e}")
            
            # Start main processing thread
            self.main_thread = threading.Thread(target=self._main_processing_loop, daemon=True)
            self.main_thread.start()
            
            # Start analytics thread
            self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
            self.analytics_thread.start()
            
            logger.info("Fear & Greed Sentiment Engine started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            self.running = False
            raise SentimentEngineError(f"Engine startup failed: {e}")
    
    def stop_engine(self):
        """Stop the sentiment engine"""
        if not self.running:
            logger.warning("Engine not running")
            return
        
        try:
            logger.info("Stopping Fear & Greed Engine...")
            self.running = False
            
            # Stop data sources
            for name, source in self.data_sources.items():
                try:
                    source.stop()
                    logger.info(f"Stopped {name} data source")
                except Exception as e:
                    logger.error(f"Error stopping {name} data source: {e}")
            
            # Wait for threads to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=5)
            
            if self.analytics_thread and self.analytics_thread.is_alive():
                self.analytics_thread.join(timeout=5)
            
            # Calculate final uptime
            if self.start_time:
                uptime = datetime.now() - self.start_time
                self.performance_metrics['uptime_seconds'] = uptime.total_seconds()
                logger.info(f"Engine stopped. Total uptime: {uptime}")
            
        except Exception as e:
            logger.error(f"Error during engine shutdown: {e}")
    
    def _main_processing_loop(self):
        """Main processing loop for sentiment data"""
        logger.info("Started main processing loop")
        
        while self.running:
            try:
                processed_this_cycle = 0
                
                # Process data from all sources
                for source_name, source in self.data_sources.items():
                    if hasattr(source, 'data_queue'):
                        while source.data_queue and processed_this_cycle < 50:
                            try:
                                sentiment_data = source.data_queue.popleft()
                                self._process_sentiment_data(sentiment_data)
                                processed_this_cycle += 1
                                self.performance_metrics['processed_messages'] += 1
                                
                            except Exception as e:
                                self.performance_metrics['processing_errors'] += 1
                                logger.error(f"Error processing sentiment data: {e}")
                
                # Small delay to prevent CPU spinning
                time.sleep(self.settings.get('processing', {}).get('processing_interval', 0.1))
                
            except Exception as e:
                self.performance_metrics['processing_errors'] += 1
                logger.error(f"Error in main processing loop: {e}")
                time.sleep(1)
    
    def _process_sentiment_data(self, sentiment_data: SentimentData):
        """Process individual sentiment data"""
        try:
            # Update analytics
            self.market_sentiment_history.append(sentiment_data.sentiment_score)
            self.fear_greed_history.append(sentiment_data.fear_greed_score)
            
            # Generate signals
            self.signal_generator.process_sentiment_data(sentiment_data)
            
            logger.debug(f"Processed sentiment: {sentiment_data.sentiment_score:.3f}, "
                        f"F&G: {sentiment_data.fear_greed_score:.1f}")
            
        except Exception as e:
            logger.error(f"Error processing sentiment data: {e}")
            raise
    
    def _analytics_loop(self):
        """Periodic analytics and cleanup"""
        logger.info("Started analytics loop")
        
        while self.running:
            try:
                # Update performance metrics
                self.performance_metrics['generated_signals'] = len(self.signal_generator.signals)
                
                if self.start_time:
                    uptime = datetime.now() - self.start_time
                    self.performance_metrics['uptime_seconds'] = uptime.total_seconds()
                
                # Log performance metrics every 5 minutes
                time.sleep(300)
                if self.running:  # Check if still running after sleep
                    self._log_performance_metrics()
                
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
                time.sleep(60)
    
    def _log_performance_metrics(self):
        """Log current performance metrics"""
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            # Calculate processing rate
            processing_rate = 0
            if uptime.total_seconds() > 0:
                processing_rate = self.performance_metrics['processed_messages'] / (uptime.total_seconds() / 60)
            
            logger.info(f"Performance Metrics - "
                       f"Uptime: {uptime}, "
                       f"Messages: {self.performance_metrics['processed_messages']}, "
                       f"Signals: {self.performance_metrics['generated_signals']}, "
                       f"Errors: {self.performance_metrics['processing_errors']}, "
                       f"Rate: {processing_rate:.1f} msgs/min")
            
        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")
    
    def get_market_summary(self) -> MarketSummary:
        """Get comprehensive market sentiment summary"""
        try:
            if not self.market_sentiment_history:
                return MarketSummary(
                    timestamp=datetime.now(),
                    market_mood="No Data",
                    sentiment_score=0.0,
                    sentiment_trend="unknown",
                    fear_greed_index=50.0,
                    fear_greed_level="Neutral",
                    data_points_analyzed=0,
                    processing_rate=0.0,
                    recent_signals_count=0
                )
            
            # Recent data analysis (last 100 data points)
            recent_sentiment = list(self.market_sentiment_history)[-100:]
            recent_fear_greed = list(self.fear_greed_history)[-100:]
            
            # Calculate metrics
            avg_sentiment = statistics.mean(recent_sentiment)
            sentiment_trend = self._calculate_trend(recent_sentiment)
            avg_fear_greed = statistics.mean(recent_fear_greed)
            
            # Determine market conditions
            market_mood = self._determine_market_mood(avg_sentiment, sentiment_trend)
            fear_greed_level = self._determine_fear_greed_level(avg_fear_greed)
            
            # Calculate processing rate
            processing_rate = self._calculate_processing_rate()
            
            # Get recent signals count
            recent_signals = self.signal_generator.get_recent_signals(20)
            
            return MarketSummary(
                timestamp=datetime.now(),
                market_mood=market_mood,
                sentiment_score=round(avg_sentiment, 3),
                sentiment_trend=sentiment_trend,
                fear_greed_index=round(avg_fear_greed, 1),
                fear_greed_level=fear_greed_level,
                data_points_analyzed=len(recent_sentiment),
                processing_rate=round(processing_rate, 2),
                recent_signals_count=len(recent_signals)
            )
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            raise SentimentEngineError(f"Failed to generate market summary: {e}")
    
    def get_asset_analysis(self, asset: str) -> AssetAnalysis:
        """Get detailed analysis for specific asset"""
        try:
            asset_upper = asset.upper()
            
            if asset_upper not in self.signal_generator.sentiment_history:
                return AssetAnalysis(
                    asset=asset_upper,
                    sentiment_score=0.0,
                    sentiment_trend="unknown",
                    confidence=0.0,
                    fear_greed_score=50.0,
                    volatility=0.0,
                    data_points=0,
                    recommendation="No data available"
                )
            
            asset_data = list(self.signal_generator.sentiment_history[asset_upper])[-50:]
            
            if not asset_data:
                return AssetAnalysis(
                    asset=asset_upper,
                    sentiment_score=0.0,
                    sentiment_trend="unknown",
                    confidence=0.0,
                    fear_greed_score=50.0,
                    volatility=0.0,
                    data_points=0,
                    recommendation="No recent data"
                )
            
            # Calculate asset-specific metrics
            sentiments = [d.sentiment_score for d in asset_data]
            confidences = [d.confidence for d in asset_data]
            fear_greed_scores = [d.fear_greed_score for d in asset_data]
            
            avg_sentiment = statistics.mean(sentiments)
            avg_confidence = statistics.mean(confidences)
            avg_fear_greed = statistics.mean(fear_greed_scores)
            sentiment_volatility = statistics.stdev(sentiments) if len(sentiments) > 1 else 0
            
            # Calculate trends
            sentiment_trend = self._calculate_trend(sentiments)
            
            # Find recent signals for this asset
            recent_signals = [s for s in self.signal_generator.get_recent_signals(20) 
                             if s.asset.upper() == asset_upper]
            
            # Asset recommendation
            recommendation = self._generate_asset_recommendation(
                avg_sentiment, sentiment_trend, avg_fear_greed, sentiment_volatility
            )
            
            return AssetAnalysis(
                asset=asset_upper,
                sentiment_score=round(avg_sentiment, 3),
                sentiment_trend=sentiment_trend,
                confidence=round(avg_confidence, 3),
                fear_greed_score=round(avg_fear_greed, 1),
                volatility=round(sentiment_volatility, 3),
                data_points=len(asset_data),
                recommendation=recommendation,
                last_signal=recent_signals[-1].signal_type.value if recent_signals else None,
                last_signal_time=recent_signals[-1].timestamp if recent_signals else None,
                sources=list(set([d.source.value for d in asset_data]))
            )
            
        except Exception as e:
            logger.error(f"Error analyzing asset {asset}: {e}")
            raise SentimentEngineError(f"Failed to analyze asset {asset}: {e}")
    
    def get_fear_greed_breakdown(self) -> Dict[str, Any]:
        """Get detailed fear and greed analysis"""
        try:
            if not self.fear_greed_history:
                return {"error": "No fear/greed data available"}
            
            recent_scores = list(self.fear_greed_history)[-100:]
            
            # Calculate distribution
            extreme_fear = sum(1 for score in recent_scores if score <= 25)
            fear = sum(1 for score in recent_scores if 25 < score <= 45)
            neutral = sum(1 for score in recent_scores if 45 < score <= 55)
            greed = sum(1 for score in recent_scores if 55 < score <= 75)
            extreme_greed = sum(1 for score in recent_scores if score > 75)
            
            total = len(recent_scores)
            
            return {
                "current_index": round(recent_scores[-1], 1) if recent_scores else 50,
                "average_index": round(statistics.mean(recent_scores), 1),
                "trend": self._calculate_trend(recent_scores),
                "distribution": {
                    "extreme_fear": round(extreme_fear / total * 100, 1),
                    "fear": round(fear / total * 100, 1),
                    "neutral": round(neutral / total * 100, 1),
                    "greed": round(greed / total * 100, 1),
                    "extreme_greed": round(extreme_greed / total * 100, 1)
                },
                "interpretation": self._interpret_fear_greed_distribution(
                    extreme_fear, fear, neutral, greed, extreme_greed, total
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting fear/greed breakdown: {e}")
            return {"error": f"Failed to generate fear/greed breakdown: {e}"}
    
    def get_signal_analytics(self) -> Dict[str, Any]:
        """Get comprehensive signal analytics"""
        try:
            recent_signals = self.signal_generator.get_recent_signals(50)
            
            if not recent_signals:
                return {"message": "No signals generated yet"}
            
            # Signal distribution
            buy_signals = sum(1 for s in recent_signals if s.signal_type.value == "BUY")
            sell_signals = sum(1 for s in recent_signals if s.signal_type.value == "SELL")
            
            # Asset distribution
            asset_counts = defaultdict(int)
            for signal in recent_signals:
                asset_counts[signal.asset] += 1
            
            # Risk distribution
            risk_counts = defaultdict(int)
            for signal in recent_signals:
                risk_counts[signal.risk_level.value] += 1
            
            # Average metrics
            avg_confidence = statistics.mean([s.confidence for s in recent_signals])
            avg_strength = statistics.mean([s.strength for s in recent_signals])
            
            return {
                "total_signals": len(recent_signals),
                "signal_distribution": {
                    "buy_signals": buy_signals,
                    "sell_signals": sell_signals,
                    "buy_percentage": round(buy_signals / len(recent_signals) * 100, 1),
                    "sell_percentage": round(sell_signals / len(recent_signals) * 100, 1)
                },
                "asset_distribution": dict(sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "risk_distribution": dict(risk_counts),
                "average_confidence": round(avg_confidence, 3),
                "average_strength": round(avg_strength, 3),
                "performance_metrics": self.signal_generator.get_signal_performance()
            }
            
        except Exception as e:
            logger.error(f"Error getting signal analytics: {e}")
            return {"error": f"Failed to generate signal analytics: {e}"}
    
    def export_data(self, hours: int = 1) -> Dict[str, Any]:
        """Export recent data for analysis"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Export recent sentiment data
            recent_sentiment_data = []
            for source_name, source in self.data_sources.items():
                if hasattr(source, 'data_queue'):
                    for data in list(source.data_queue):
                        if data.timestamp >= cutoff_time:
                            recent_sentiment_data.append(data.to_dict())
            
            # Export recent signals
            recent_signals_data = []
            for signal in self.signal_generator.signals:
                if signal.timestamp >= cutoff_time:
                    recent_signals_data.append(signal.to_dict())
            
            return {
                "export_timestamp": datetime.now().isoformat(),
                "export_period_hours": hours,
                "sentiment_data": recent_sentiment_data,
                "signals_data": recent_signals_data,
                "summary": {
                    "sentiment_records": len(recent_sentiment_data),
                    "signal_records": len(recent_signals_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {"error": f"Failed to export data: {e}"}
    
    # Helper methods
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 5:
            return "insufficient_data"
        
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        diff = second_half - first_half
        
        if abs(diff) < 0.05:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _determine_market_mood(self, sentiment: float, trend: str) -> str:
        """Determine overall market mood"""
        if sentiment > 0.4:
            return "Strong Bullish" if trend == "increasing" else "Bullish"
        elif sentiment > 0.1:
            return "Cautiously Bullish" if trend == "increasing" else "Neutral Positive"
        elif sentiment > -0.1:
            return "Neutral"
        elif sentiment > -0.4:
            return "Cautiously Bearish" if trend == "decreasing" else "Neutral Negative"
        else:
            return "Strong Bearish" if trend == "decreasing" else "Bearish"
    
    def _determine_fear_greed_level(self, score: float) -> str:
        """Determine fear/greed level from score"""
        if score <= 25:
            return "Extreme Fear"
        elif score <= 45:
            return "Fear"
        elif score <= 55:
            return "Neutral"
        elif score <= 75:
            return "Greed"
        else:
            return "Extreme Greed"
    
    def _calculate_processing_rate(self) -> float:
        """Calculate messages per minute processing rate"""
        if not self.start_time:
            return 0.0
        
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        if uptime_minutes == 0:
            return 0.0
        
        return self.performance_metrics['processed_messages'] / uptime_minutes
    
    def _generate_asset_recommendation(self, sentiment: float, trend: str, fear_greed: float, volatility: float) -> str:
        """Generate trading recommendation for asset"""
        if volatility > 0.5:
            return "High volatility - proceed with caution"
        
        if sentiment > 0.3 and trend == "increasing":
            if fear_greed < 80:
                return "Strong buy signal - positive momentum"
            else:
                return "Caution - high sentiment but extreme greed levels"
        elif sentiment < -0.3 and trend == "decreasing":
            if fear_greed > 20:
                return "Strong sell signal - negative momentum"
            else:
                return "Potential buy opportunity - extreme fear may indicate oversold"
        elif abs(sentiment) < 0.1:
            return "Neutral - wait for clearer signals"
        else:
            return "Mixed signals - monitor closely"
    
    def _interpret_fear_greed_distribution(self, extreme_fear: int, fear: int, neutral: int, greed: int, extreme_greed: int, total: int) -> str:
        """Interpret fear/greed distribution"""
        if extreme_fear / total > 0.5:
            return "Market dominated by extreme fear - potential buying opportunity"
        elif extreme_greed / total > 0.5:
            return "Market dominated by extreme greed - consider taking profits"
        elif (fear + extreme_fear) / total > 0.6:
            return "Fear prevalent - contrarian buying opportunity may emerge"
        elif (greed + extreme_greed) / total > 0.6:
            return "Greed prevalent - market may be due for correction"
        else:
            return "Balanced sentiment distribution - stable market conditions"