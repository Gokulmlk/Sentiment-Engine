"""
Reddit data ingestion implementation
"""

import requests
import base64
from typing import Optional
import time

from .base_ingestion import BaseIngestionSource
from ..core.data_models import DataSource
from ..utils.exceptions import RedditAPIError

class RedditIngestionSource(BaseIngestionSource):
    """Reddit API data ingestion"""
    
    @property
    def source_type(self) -> DataSource:
        return DataSource.REDDIT
    
    def __init__(self, sentiment_analyzer, config):
        super().__init__(sentiment_analyzer, config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.subreddits = config.get('subreddits', ['investing', 'cryptocurrency', 'stocks', 'wallstreetbets'])
        self.access_token = None
        self.token_expires_at = 0
        
        if not (self.client_id and self.client_secret):
            print("Reddit API credentials not configured, using mock data")
    
    def fetch_data(self) -> Optional[str]:
        """Fetch data from Reddit API"""
        try:
            if self.config.get('mock_data', False) or not (self.client_id and self.client_secret):
                return self._get_mock_data()
            
            return self._fetch_real_reddit_data()
            
        except Exception as e:
            print(f"Reddit API Error: {e}")
            return self._get_mock_data()
    
    def _get_access_token(self) -> str:
        """Get Reddit API access token"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "User-Agent": "SentimentEngine/1.0"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            self.token_expires_at = time.time() + token_data['expires_in'] - 60
            
            return self.access_token
        except Exception as e:
            print(f"Failed to get Reddit token: {e}")
            raise
    
    def _fetch_real_reddit_data(self) -> Optional[str]:
        """Fetch real data from Reddit API"""
        try:
            token = self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "SentimentEngine/1.0"
            }
            
            # Randomly select a subreddit
            import random
            subreddit = random.choice(self.subreddits)
            
            response = requests.get(
                f"https://oauth.reddit.com/r/{subreddit}/hot",
                headers=headers,
                params={"limit": 5},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'children' in data['data'] and data['data']['children']:
                # Get a random post
                post = random.choice(data['data']['children'])['data']
                
                # Combine title and selftext if available
                content = post['title']
                if post.get('selftext'):
                    content += " " + post['selftext'][:500]
                
                print(f"🤖 Got real Reddit data: {content[:50]}...")
                return content
            
            return None
            
        except Exception as e:
            print(f"Reddit API request failed: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> str:
        """Get mock Reddit data for testing"""
        mock_posts = [
            "DD: Why I believe we're entering the biggest bull market in history",
            "🐻 Bear case for tech stocks - overvaluation everywhere you look",
            "Market sentiment extremely bearish. Contrarian buying opportunity?",
            "YOLO update: All in on growth stocks, can't go tits up! 🚀",
            "Panic selling in small caps. Great opportunity for value investors"
        ]
        
        import random
        return random.choice(mock_posts)