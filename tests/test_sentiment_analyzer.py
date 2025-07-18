"""
Tests for the sentiment analyzer
"""

import unittest
from datetime import datetime

from sentiment_engine.core.sentiment_analyzer import SentimentAnalyzer
from sentiment_engine.utils.exceptions import SentimentAnalysisError

class TestSentimentAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment(self):
        """Test positive sentiment analysis"""
        text = "Bitcoin is going to the moon! Very bullish and optimistic!"
        sentiment, confidence, fear_greed = self.analyzer.analyze_sentiment(text)
        
        self.assertGreater(sentiment, 0.3)
        self.assertGreater(confidence, 0.2)
        self.assertGreater(fear_greed, 60)  # Should be on greed side
    
    def test_negative_sentiment(self):
        """Test negative sentiment analysis"""
        text = "Market crash incoming! Very bearish and scary times ahead!"
        sentiment, confidence, fear_greed = self.analyzer.analyze_sentiment(text)
        
        self.assertLess(sentiment, -0.3)
        self.assertGreater(confidence, 0.2)
        self.assertLess(fear_greed, 40)  # Should be on fear side
    
    def test_neutral_sentiment(self):
        """Test neutral sentiment analysis"""
        text = "The weather is nice today and I had lunch."
        sentiment, confidence, fear_greed = self.analyzer.analyze_sentiment(text)
        
        self.assertAlmostEqual(sentiment, 0, delta=0.2)
        self.assertLess(confidence, 0.3)  # Low confidence for neutral
        self.assertAlmostEqual(fear_greed, 50, delta=10)  # Near neutral
    
    def test_asset_extraction(self):
        """Test asset mention extraction"""
        text = "BTC and ETH are performing well, TSLA earnings beat expectations"
        assets = self.analyzer.extract_assets(text)
        
        self.assertIn("BTC", assets)
        self.assertIn("ETH", assets)
        self.assertIn("TSLA", assets)
    
    def test_sentiment_modifiers(self):
        """Test sentiment modifiers (amplifiers, diminishers, negators)"""
        # Test amplifier
        text1 = "Very bullish on Bitcoin"
        sentiment1, _, _ = self.analyzer.analyze_sentiment(text1)
        
        # Test without amplifier
        text2 = "Bullish on Bitcoin"
        sentiment2, _, _ = self.analyzer.analyze_sentiment(text2)
        
        self.assertGreater(sentiment1, sentiment2)
        
        # Test negator
        text3 = "Not bullish on Bitcoin"
        sentiment3, _, _ = self.analyzer.analyze_sentiment(text3)
        
        self.assertLess(sentiment3, sentiment2)
    
    def test_empty_text(self):
        """Test handling of empty text"""
        sentiment, confidence, fear_greed = self.analyzer.analyze_sentiment("")
        
        self.assertEqual(sentiment, 0)
        self.assertEqual(confidence, 0)
        self.assertEqual(fear_greed, 50)
    
    def test_batch_analysis(self):
        """Test batch analysis of multiple texts"""
        texts = [
            "Bitcoin to the moon!",
            "Market crash coming!",
            "Neutral market conditions"
        ]
        
        results = self.analyzer.batch_analyze(texts)
        
        self.assertEqual(len(results), 3)
        self.assertGreater(results[0]['sentiment_score'], 0)
        self.assertLess(results[1]['sentiment_score'], 0)
        self.assertAlmostEqual(results[2]['sentiment_score'], 0, delta=0.3)
    
    def test_sentiment_breakdown(self):
        """Test detailed sentiment breakdown"""
        text = "Bitcoin is very bullish! TSLA also looking strong."
        breakdown = self.analyzer.get_sentiment_breakdown(text)
        
        self.assertIn('sentiment_score', breakdown)
        self.assertIn('confidence', breakdown)
        self.assertIn('fear_greed_score', breakdown)
        self.assertIn('assets_mentioned', breakdown)
        self.assertIn('word_count', breakdown)
        
        self.assertIn('BTC', breakdown['assets_mentioned'])
        self.assertIn('TSLA', breakdown['assets_mentioned'])

if __name__ == '__main__':
    unittest.main()