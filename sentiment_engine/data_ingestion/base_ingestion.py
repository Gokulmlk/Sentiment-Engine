"""
Base class for data ingestion sources
"""

import time
import threading
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from collections import deque

from ..core.data_models import SentimentData, DataSource
from ..core.sentiment_analyzer import SentimentAnalyzer
from ..utils.exceptions import DataIngestionError

logger = logging.getLogger(__name__)

class BaseIngestionSource(ABC):
    """Base class for all data ingestion sources"""
    
    def __init__(self, sentiment_analyzer: SentimentAnalyzer, config: Dict[str, Any]):
        self.sentiment_analyzer = sentiment_analyzer
        self.config = config
        self.running = False
        self.data_queue = deque(maxlen=config.get('queue_size', 1000))
        self.processed_count = 0
        self.error_count = 0
        self.thread: Optional[threading.Thread] = None
        
    @property
    @abstractmethod
    def source_type(self) -> DataSource:
        """Return the data source type"""
        pass
    
    @abstractmethod
    def fetch_data(self) -> str:
        """Fetch data from the source - to be implemented by subclasses"""
        pass
    
    def start(self):
        """Start the data ingestion thread"""
        if self.running:
            logger.warning(f"{self.source_type.value} ingestion already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._ingestion_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started {self.source_type.value} data ingestion")
    
    def stop(self):
        """Stop the data ingestion thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped {self.source_type.value} data ingestion. "
                   f"Processed: {self.processed_count}, Errors: {self.error_count}")
    
    def _ingestion_loop(self):
        """Main ingestion loop"""
        while self.running:
            try:
                content = self.fetch_data()
                if content:
                    self._process_content(content)
                
                # Rate limiting
                sleep_time = self.config.get('rate_limit_delay', 1.0)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"{self.source_type.value} ingestion error: {e}")
                time.sleep(5)  # Longer delay on error
    
    def _process_content(self, content: str):
        """Process and analyze content"""
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
            
            logger.debug(f"Processed {self.source_type.value}: "
                        f"sentiment={sentiment_score:.2f}, F&G={fear_greed_score:.0f}")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Content processing error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return {
            'source': self.source_type.value,
            'running': self.running,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'queue_size': len(self.data_queue),
            'error_rate': self.error_count / max(self.processed_count, 1) * 100
        }