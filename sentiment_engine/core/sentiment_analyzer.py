"""
Advanced sentiment analysis engine
"""

import re
import statistics
from typing import Dict, List, Tuple, Set
from collections import defaultdict

from ..utils.exceptions import SentimentAnalysisError

class SentimentAnalyzer:
    """Advanced NLP-based sentiment analysis engine"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._initialize_word_sets()
        self._initialize_patterns()
        
    def _initialize_word_sets(self):
        """Initialize sentiment keyword sets"""
        # Comprehensive sentiment keywords
        self.positive_words = {
            'bullish', 'moon', 'rocket', 'pump', 'gains', 'profit', 'up', 'rise',
            'surge', 'rally', 'boom', 'bull', 'green', 'diamond', 'hodl', 'buy',
            'strong', 'breakout', 'support', 'momentum', 'uptrend', 'recovery',
            'optimistic', 'confidence', 'growth', 'expansion', 'breakthrough'
        }
        
        self.negative_words = {
            'bearish', 'crash', 'dump', 'loss', 'down', 'fall', 'drop', 'bear',
            'red', 'panic', 'sell', 'fear', 'disaster', 'collapse', 'bubble',
            'weak', 'breakdown', 'resistance', 'decline', 'downtrend', 'recession',
            'pessimistic', 'uncertainty', 'volatility', 'correction', 'selloff'
        }
        
        self.fear_keywords = {
            'panic', 'crash', 'fear', 'disaster', 'collapse', 'bubble', 'correction',
            'recession', 'crisis', 'volatility', 'uncertainty', 'risk', 'danger',
            'threat', 'warning', 'concern', 'worry', 'anxiety', 'stress', 'trouble'
        }
        
        self.greed_keywords = {
            'moon', 'rocket', 'fomo', 'gains', 'profit', 'bull', 'rally', 'surge',
            'euphoria', 'bubble', 'mania', 'speculation', 'hype', 'excitement',
            'enthusiasm', 'optimism', 'confidence', 'aggressive', 'ambitious'
        }
        
        # Sentiment modifiers
        self.amplifiers = {'very', 'extremely', 'highly', 'super', 'really', 'absolutely'}
        self.diminishers = {'slightly', 'somewhat', 'maybe', 'perhaps', 'possibly', 'might'}
        self.negators = {'not', 'no', 'never', 'none', 'nothing', 'neither', 'without'}
        
    def _initialize_patterns(self):
        """Initialize asset recognition patterns"""
        self.asset_patterns = {
            'crypto': r'\b(BTC|ETH|bitcoin|ethereum|crypto|cryptocurrency|ADA|DOT|LINK|UNI|DOGE|SHIB|MATIC|AVAX|SOL|XRP)\b',
            'stocks': r'\b([A-Z]{1,5}|TSLA|AAPL|GOOGL|MSFT|AMZN|NVDA|META|NFLX|AMD|INTC|CRM|PYPL)\b',
            'indices': r'\b(SPY|QQQ|DIA|IWM|VIX|S&P|DOW|NASDAQ|Russell|NDX)\b',
            'forex': r'\b(USD|EUR|GBP|JPY|CHF|CAD|AUD|NZD|EURUSD|GBPUSD|USDJPY)\b'
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[float, float, float]:
        """
        Advanced sentiment analysis of text
        Returns: (sentiment_score, confidence, fear_greed_score)
        """
        if not text or not text.strip():
            return 0.0, 0.0, 50.0
            
        try:
            text_lower = text.lower()
            words = re.findall(r'\b\w+\b', text_lower)
            
            if not words:
                return 0.0, 0.0, 50.0
            
            # Count sentiment words with modifiers
            positive_score, negative_score = self._calculate_sentiment_scores(words)
            fear_score, greed_score = self._calculate_emotion_scores(words)
            
            # Calculate final scores
            sentiment_score = self._calculate_final_sentiment(positive_score, negative_score)
            confidence = self._calculate_confidence(positive_score, negative_score, len(words))
            fear_greed_score = self._calculate_fear_greed_score(fear_score, greed_score)
            
            return sentiment_score, confidence, fear_greed_score
            
        except Exception as e:
            raise SentimentAnalysisError(f"Error analyzing sentiment: {e}")
    
    def _calculate_sentiment_scores(self, words: List[str]) -> Tuple[float, float]:
        """Calculate positive and negative sentiment scores"""
        positive_score = 0.0
        negative_score = 0.0
        
        for i, word in enumerate(words):
            modifier = self._get_modifier(words, i)
            
            if word in self.positive_words:
                positive_score += modifier
            elif word in self.negative_words:
                negative_score += modifier
                
        return positive_score, negative_score
    
    def _calculate_emotion_scores(self, words: List[str]) -> Tuple[float, float]:
        """Calculate fear and greed emotion scores"""
        fear_score = 0.0
        greed_score = 0.0
        
        for i, word in enumerate(words):
            modifier = abs(self._get_modifier(words, i))
            
            if word in self.fear_keywords:
                fear_score += modifier
            elif word in self.greed_keywords:
                greed_score += modifier
                
        return fear_score, greed_score
    
    def _get_modifier(self, words: List[str], index: int) -> float:
        """Get sentiment modifier for word at index"""
        modifier = 1.0
        
        if index > 0:
            prev_word = words[index - 1]
            if prev_word in self.amplifiers:
                modifier = 1.5
            elif prev_word in self.diminishers:
                modifier = 0.5
            elif prev_word in self.negators:
                modifier = -1.0
                
        return modifier
    
    def _calculate_final_sentiment(self, positive_score: float, negative_score: float) -> float:
        """Calculate final sentiment score (-1 to 1)"""
        total_sentiment = abs(positive_score) + abs(negative_score)
        
        if total_sentiment == 0:
            return 0.0
            
        return (positive_score - negative_score) / total_sentiment
    
    def _calculate_confidence(self, positive_score: float, negative_score: float, word_count: int) -> float:
        """Calculate confidence score (0 to 1)"""
        total_sentiment = abs(positive_score) + abs(negative_score)
        
        if total_sentiment == 0:
            return 0.1
            
        # Confidence based on sentiment word density
        confidence = min(total_sentiment / word_count * 3, 1.0)
        return max(confidence, 0.1)  # Minimum confidence
    
    def _calculate_fear_greed_score(self, fear_score: float, greed_score: float) -> float:
        """Calculate fear/greed score (0-100)"""
        total_emotion = fear_score + greed_score
        
        if total_emotion == 0:
            return 50.0  # Neutral
            
        return (greed_score / total_emotion) * 100
    
    def extract_assets(self, text: str) -> List[str]:
        """Extract mentioned financial assets from text"""
        assets = []
        
        for asset_type, pattern in self.asset_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            assets.extend(matches)
            
        return list(set([asset.upper() for asset in assets]))
    
    def get_sentiment_breakdown(self, text: str) -> Dict:
        """Get detailed sentiment breakdown"""
        sentiment_score, confidence, fear_greed_score = self.analyze_sentiment(text)
        assets = self.extract_assets(text)
        
        return {
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'fear_greed_score': fear_greed_score,
            'assets_mentioned': assets,
            'word_count': len(text.split()),
            'analysis_timestamp': None  # Will be set by caller
        }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts in batch"""
        results = []
        
        for text in texts:
            try:
                result = self.get_sentiment_breakdown(text)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
                
        return results