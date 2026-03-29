"""
Fear & Greed Sentiment Engine - Test Suite
==========================================
Run with: python -m pytest tests/ -v
       or: python tests/test_engine.py
"""

import sys
import os
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fear_greed_engine import (
    FearGreedEngine, SentimentAnalyzer, SignalGenerator,
    SentimentData, TradeSignal
)
from datetime import datetime


class TestSentimentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_text(self):
        result = self.analyzer.analyze("BTC is going to the moon! Buy buy buy! Bullish rally breakout!")
        self.assertGreater(result["sentiment_score"], 0)
        self.assertGreater(result["fear_greed_score"], 50)

    def test_negative_text(self):
        result = self.analyzer.analyze("BTC crash incoming! Sell everything! Bear market dump!")
        self.assertLess(result["sentiment_score"], 0)
        self.assertLess(result["fear_greed_score"], 50)

    def test_neutral_text(self):
        result = self.analyzer.analyze("BTC is a cryptocurrency that exists.")
        self.assertEqual(result["sentiment_score"], 0)
        self.assertEqual(result["confidence"], 0.0)

    def test_confidence_range(self):
        result = self.analyzer.analyze("buy sell pump dump moon crash rally bear bull")
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_fg_range(self):
        result = self.analyzer.analyze("moon pump buy rally boom")
        self.assertGreaterEqual(result["fear_greed_score"], 0)
        self.assertLessEqual(result["fear_greed_score"], 100)

    def test_count_increments(self):
        before = self.analyzer.analyzed_count
        self.analyzer.analyze("some text")
        self.assertEqual(self.analyzer.analyzed_count, before + 1)


class TestSignalGenerator(unittest.TestCase):

    def setUp(self):
        self.gen = SignalGenerator()

    def _make_sentiment(self, score, fg=70, confidence=0.7):
        return SentimentData(
            timestamp=datetime.now(),
            source="test",
            asset="BTC",
            raw_text="test",
            sentiment_score=score,
            confidence=confidence,
            fear_greed_score=fg,
            engagement=100
        )

    def test_no_signal_insufficient_data(self):
        history = [self._make_sentiment(0.5) for _ in range(3)]
        result = self.gen.evaluate("BTC", history)
        self.assertIsNone(result)

    def test_buy_signal(self):
        history = [self._make_sentiment(0.6, 70, 0.8) for _ in range(20)]
        result = self.gen.evaluate("BTC", history)
        self.assertIsNotNone(result)
        self.assertEqual(result.signal_type, "BUY")

    def test_sell_signal(self):
        history = [self._make_sentiment(-0.6, 30, 0.8) for _ in range(20)]
        result = self.gen.evaluate("ETH", history)
        self.assertIsNotNone(result)
        self.assertEqual(result.signal_type, "SELL")

    def test_no_signal_low_confidence(self):
        history = [self._make_sentiment(0.9, 80, 0.1) for _ in range(20)]
        result = self.gen.evaluate("SOL", history)
        self.assertIsNone(result)

    def test_cooldown(self):
        history = [self._make_sentiment(0.7, 75, 0.9) for _ in range(20)]
        sig1 = self.gen.evaluate("TSLA", history)
        sig2 = self.gen.evaluate("TSLA", history)
        self.assertIsNotNone(sig1)
        self.assertIsNone(sig2)  # cooldown

    def test_signal_fields(self):
        history = [self._make_sentiment(0.7, 75, 0.9) for _ in range(20)]
        sig = self.gen.evaluate("AAPL", history)
        self.assertIsNotNone(sig)
        self.assertIn(sig.signal_type, ["BUY", "SELL", "HOLD"])
        self.assertIn(sig.risk_level, ["Low", "Medium", "High"])
        self.assertGreaterEqual(sig.confidence, 0)
        self.assertLessEqual(sig.confidence, 1)


class TestFearGreedEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = FearGreedEngine()
        cls.engine.start_engine()
        time.sleep(5)  # Let data accumulate

    @classmethod
    def tearDownClass(cls):
        cls.engine.stop_engine()

    def test_engine_starts(self):
        self.assertTrue(self.engine.running)

    def test_messages_being_processed(self):
        self.assertGreater(self.engine.messages_processed, 0)

    def test_market_summary_structure(self):
        summary = self.engine.get_market_summary()
        if "status" not in summary:
            self.assertIn("market_mood", summary)
            self.assertIn("sentiment_score", summary)
            self.assertIn("fear_greed_index", summary)

    def test_fear_greed_range(self):
        summary = self.engine.get_market_summary()
        if "fear_greed_index" in summary:
            self.assertGreaterEqual(summary["fear_greed_index"], 0)
            self.assertLessEqual(summary["fear_greed_index"], 100)

    def test_asset_analysis_btc(self):
        time.sleep(2)
        result = self.engine.get_asset_analysis("BTC")
        if "status" not in result:
            self.assertEqual(result["asset"], "BTC")
            self.assertIn("sentiment_score", result)
            self.assertIn("recommendation", result)

    def test_all_assets_returns_dict(self):
        result = self.engine.get_all_assets()
        self.assertIsInstance(result, dict)

    def test_fear_greed_index(self):
        result = self.engine.get_fear_greed_index()
        if "status" not in result:
            self.assertIn("index", result)
            self.assertIn("level", result)

    def test_export(self):
        fname = self.engine.export_data()
        self.assertTrue(os.path.exists(fname))
        with open(fname) as f:
            data = json.load(f)
        self.assertIn("market_summary", data)
        os.remove(fname)

    def test_mood_helper(self):
        self.assertEqual(FearGreedEngine._score_to_mood(0.6, 70), "Extremely Bullish")
        self.assertEqual(FearGreedEngine._score_to_mood(-0.6, 30), "Extremely Bearish")
        self.assertEqual(FearGreedEngine._score_to_mood(0.0, 50), "Neutral")

    def test_fg_level_helper(self):
        self.assertEqual(FearGreedEngine._fg_to_level(10), "Extreme Fear")
        self.assertEqual(FearGreedEngine._fg_to_level(35), "Fear")
        self.assertEqual(FearGreedEngine._fg_to_level(50), "Neutral")
        self.assertEqual(FearGreedEngine._fg_to_level(65), "Greed")
        self.assertEqual(FearGreedEngine._fg_to_level(90), "Extreme Greed")


import json

if __name__ == "__main__":
    print("\n🧪 Fear & Greed Engine — Test Suite")
    print("=" * 50)
    unittest.main(verbosity=2)
