"""
Custom exceptions for the sentiment engine
"""

class SentimentEngineError(Exception):
    """Base exception for sentiment engine"""
    pass

class SentimentAnalysisError(SentimentEngineError):
    """Exception raised during sentiment analysis"""
    pass

class DataIngestionError(SentimentEngineError):
    """Exception raised during data ingestion"""
    pass

class TwitterAPIError(DataIngestionError):
    """Exception raised for Twitter API issues"""
    pass

class RedditAPIError(DataIngestionError):
    """Exception raised for Reddit API issues"""
    pass

class NewsAPIError(DataIngestionError):
    """Exception raised for News API issues"""
    pass

class SignalGenerationError(SentimentEngineError):
    """Exception raised during signal generation"""
    pass

class ConfigurationError(SentimentEngineError):
    """Exception raised for configuration issues"""
    pass

class DatabaseError(SentimentEngineError):
    """Exception raised for database issues"""
    pass