"""
Twitter data ingestion implementation
"""

import requests
import json
from typing import Optional
from datetime import datetime

from .base_ingestion import BaseIngestionSource
from ..core.data_models import DataSource
from ..utils.exceptions import TwitterAPIError

class TwitterIngestionSource(BaseIngestionSource):
    """Twitter API data ingestion"""
    
    @property
    def source_type(self) -> DataSource:
        return DataSource.TWITTER
    
    def __init__(self, sentiment_analyzer, config):
        super().__init__(sentiment_analyzer, config)
        self.bearer_token = config.get('bearer_token')
        self.search_terms = config.get('search_terms', ['bitcoin', 'ethereum', 'crypto', 'stocks'])
        self.last_tweet_id = None
        
        if not self.bearer_token:
            raise TwitterAPIError("Twitter bearer token not configured")
    
    def fetch_data(self) -> Optional[str]:
        """Fetch data from Twitter API"""
        try:
            if self.config.get('mock_data', False):
                return self._get_mock_data()
            
            return self._fetch_real_twitter_data()
            
        except Exception as e:
            print(f"Twitter API Error: {e}")
            return self._get_mock_data()  # Fallback to mock data
    
    def _fetch_real_twitter_data(self) -> Optional[str]:
        """Fetch real data from Twitter API v2"""
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # Build search query
        query = " OR ".join(self.search_terms)
        params = {
            "query": f"({query}) -is:retweet lang:en",
            "tweet.fields": "created_at,public_metrics",
            "max_results": 10
        }
        
        if self.last_tweet_id:
            params["since_id"] = self.last_tweet_id
        
        try:
            response = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                print("Twitter rate limit reached, using mock data")
                return self._get_mock_data()
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and data['data']:
                # Get the most recent tweet
                tweet = data['data'][0]
                self.last_tweet_id = tweet['id']
                print(f"📱 Got real Twitter data: {tweet['text'][:50]}...")
                return tweet['text']
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Twitter API request failed: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> str:
        """Get mock Twitter data for testing"""
        mock_tweets = [
            "🚀 Bitcoin breaking $50k resistance! This bull run is just getting started #BTC #crypto",
            "⚠️ Market looking shaky. Major correction incoming? Time to take profits #bearish",
            "TSLA earnings absolutely crushed expectations! $1000 PT looking realistic 📈",
            "VIX spiking to dangerous levels. Black swan event brewing? #volatility #SPY",
            "Ethereum 2.0 upgrade complete! ETH to the moon! 🌙 #ETH #DeFi"
        ]
        
        import random
        return random.choice(mock_tweets)