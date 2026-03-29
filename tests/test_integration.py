"""
Integration tests for the sentiment engine
"""

import unittest
import time
import threading
from datetime import datetime

from sentiment_engine.core.engine import FearGreedEngine
from sentiment_engine.config.settings import Settings, DataSourceConfig

class TestEngineIntegration(unittest.TestCase):
    
    def setUp(self):
        # Create test configuration
        settings = Settings()
        settings.data_sources = DataSourceConfig(
            twitter_enabled=True,
            reddit_enabled=True,
            news_enabled=True,
            mock_data=True  # Use mock data for testing
        )
        settings.processing.max_queue_size = 100
        
        self.engine = FearGreedEngine(settings)
    
    def tearDown(self):
        if self.engine.running:
            self.engine.stop_engine()
    
    def test_engine_start_stop(self):
        """Test engine startup and shutdown"""
        self.assertFalse(self.engine.running)
        
        self.engine.start_engine()
        self.assertTrue(self.engine.running)
        
        # Wait a moment for initialization
        time.sleep(1)
        
        self.engine.stop_engine()
        self.assertFalse(self.engine.running)
    
    def test_data_processing_flow(self):
        """Test end-to-end data processing"""
        self.engine.start_engine()
        
        # Wait for some data to be processed
        time.sleep(5)
        
        # Check that data has been processed
        summary = self.engine.get_market_summary()
        self.assertIsNotNone(summary)
        self.assertIn('market_mood', summary.to_dict())
        self.assertGreater(summary.data_points_analyzed, 0)
        
        self.engine.stop_engine()
    
    def test_signal_generation(self):
        """Test signal generation"""
        self.engine.start_engine()
        
        # Wait for signals to be generated
        time.sleep(10)
        
        signals = self.engine.signal_generator.get_recent_signals(20)
        
        # Should have generated some signals
        self.assertGreater(len(signals), 0)
        
        # Check signal structure
        if signals:
            signal = signals[0]
            self.assertIsNotNone(signal.asset)
            self.assertIn(signal.signal_type.value, ['BUY', 'SELL', 'HOLD'])
            self.assertGreaterEqual(signal.confidence, 0)
            self.assertLessEqual(signal.confidence, 1)
        
        self.engine.stop_engine()
    
    def test_asset_analysis(self):
        """Test asset-specific analysis"""
        self.engine.start_engine()
        
        # Wait for data processing
        time.sleep(5)
        
        # Add some test data for BTC
        from sentiment_engine.core.data_models import SentimentData, DataSource
        test_data = SentimentData(
            timestamp=datetime.now(),
            source=DataSource.TWITTER,
            content="Bitcoin is very bullish today!",
            sentiment_score=0.8,
            confidence=0.9,
            asset_mentions=['BTC'],
            fear_greed_score=75.0
        )
        
        self.engine.signal_generator.process_sentiment_data(test_data)
        
        # Test asset analysis
        analysis = self.engine.get_asset_analysis('BTC')
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.asset, 'BTC')
        
        self.engine.stop_engine()
    
    def test_fear_greed_calculation(self):
        """Test fear and greed index calculation"""
        self.engine.start_engine()
        
        # Wait for data
        time.sleep(5)
        
        fear_greed = self.engine.get_fear_greed_breakdown()
        self.assertIsNotNone(fear_greed)
        self.assertIn('current_index', fear_greed)
        self.assertGreaterEqual(fear_greed['current_index'], 0)
        self.assertLessEqual(fear_greed['current_index'], 100)
        
        self.engine.stop_engine()
    
    def test_export_functionality(self):
        """Test data export functionality"""
        self.engine.start_engine()
        
        # Wait for some data
        time.sleep(5)
        
        export_data = self.engine.export_data(hours=1)
        self.assertIsNotNone(export_data)
        self.assertIn('export_timestamp', export_data)
        self.assertIn('sentiment_data', export_data)
        self.assertIn('signals_data', export_data)
        
        self.engine.stop_engine()

if __name__ == '__main__':
    unittest.main()