"""
News data ingestion implementation
"""

import requests
from typing import Optional
from datetime import datetime

from .base_ingestion import BaseIngestionSource
from ..core.data_models import DataSource
from ..utils.exceptions import NewsAPIError

class NewsIngestionSource(BaseIngestionSource):
    """News API data ingestion"""
    
    @property
    def source_type(self) -> DataSource:
        return DataSource.NEWS
    
    def __init__(self, sentiment_analyzer, config):
        super().__init__(sentiment_analyzer, config)
        self.api_key = config.get('api_key')
        self.sources = config.get('sources', ['reuters', 'bloomberg', 'cnbc'])
        self.categories = config.get('categories', ['business', 'technology'])
        
    def fetch_data(self) -> Optional[str]:
        """Fetch data from News API"""
        try:
            if self.config.get('mock_data', False):
                return self._get_mock_data()
            
            return self._fetch_real_news_data()
            
        except Exception as e:
            raise NewsAPIError(f"Error fetching news data: {e}")
    
    def _fetch_real_news_data(self) -> Optional[str]:
        """Fetch real data from News API"""
        if not self.api_key or self.api_key == 'demo':
            return self._get_mock_data()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "SentimentEngine/1.0"
        }
        
        # Build query for financial news
        query = "bitcoin OR ethereum OR stock market OR trading"
        
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5
        }
        
        response = requests.get(
            "https://newsapi.org/v2/everything",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 429:
            # Rate limited
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if 'articles' in data and data['articles']:
            # Get the most recent article
            article = data['articles'][0]
            title = article.get('title', '')
            description = article.get('description', '')
            
            # Combine title and description
            content = f"{title}. {description}" if description else title
            return content
        
        return None
    
    def _get_mock_data(self) -> str:
        """Get mock news data for testing"""
        mock_news = [
            "Federal Reserve signals more aggressive rate hikes ahead, markets tumble",
            "Inflation data comes in hot, investors flee to safe haven assets",
            "Tech earnings season exceeds expectations, Nasdaq surges 3%",
            "Geopolitical tensions escalate, oil prices spike to new highs",
            "Central bank digital currency announcement boosts crypto sector",
            "Consumer confidence plunges to lowest level since 2020",
            "Corporate buybacks reach record levels, supporting equity valuations",
            "Supply chain disruptions ease, manufacturing stocks rally",
            "Energy crisis deepens in Europe, renewable stocks benefit",
            "AI breakthrough announcement sends tech stocks soaring"
        ]
        
        import random
        return random.choice(mock_news)