"""
Fear & Greed Sentiment Engine
==============================
Real-time sentiment analysis system for generating trading signals
based on social media, news, and financial data.

Version: 2.0 (Real API Integration)
- Twitter API v2 via tweepy
- Reddit API via praw
- News via newsapi-python
- Falls back to simulation if API keys not set

Setup:
  1. pip install tweepy praw newsapi-python python-dotenv
  2. Create .env file with your API keys (see .env.example)
  3. python demo.py
"""

import time
import threading
import logging
import json
import random
import statistics
import os
from datetime import datetime
from collections import deque, defaultdict, Counter
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Load .env if present ──────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Optional real API libraries ───────────────────────────
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False


# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("exports", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/sentiment_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FearGreedEngine")


# ─────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────

@dataclass
class SentimentData:
    timestamp: datetime
    source: str
    asset: str
    raw_text: str
    sentiment_score: float
    confidence: float
    fear_greed_score: float
    keywords_found: list = field(default_factory=list)
    engagement: int = 0


@dataclass
class TradeSignal:
    timestamp: datetime
    asset: str
    signal_type: str
    confidence: float
    strength: float
    expected_duration: str
    risk_level: str
    reasoning: str
    fear_greed_at_signal: float
    sentiment_score: float


# ─────────────────────────────────────────────
# NLP Word Lists
# ─────────────────────────────────────────────

POSITIVE_WORDS = {
    "bullish", "moon", "pump", "buy", "long", "rally", "breakout", "surge",
    "gain", "profit", "win", "up", "rise", "growth", "strong", "bull",
    "opportunity", "recovery", "rebound", "support", "accumulate", "hodl",
    "outperform", "upgrade", "beat", "exceed", "positive", "optimistic",
    "uptrend", "momentum", "explosive", "soar", "skyrocket", "double",
    "ath", "alltime", "high", "record", "boost", "confidence", "adoption"
}

NEGATIVE_WORDS = {
    "bearish", "dump", "crash", "sell", "short", "drop", "fall", "fear",
    "loss", "down", "decline", "weak", "bear", "resist", "capitulate",
    "panic", "correction", "breakdown", "plunge", "collapse", "rekt",
    "bubble", "overvalued", "risk", "danger", "warning", "caution",
    "underperform", "downgrade", "miss", "negative", "pessimistic",
    "downtrend", "reversal", "liquidation", "margin", "call", "bankrupt"
}

GREED_KEYWORDS = {
    "moon", "lambo", "rich", "millionaire", "profit", "gain", "buy", "long",
    "pump", "rally", "bull", "opportunity", "fomo", "accumulate", "hodl",
    "breakout", "surge", "explosive", "soar", "ath", "record", "boom"
}

FEAR_KEYWORDS = {
    "crash", "dump", "bear", "sell", "panic", "fear", "risk", "loss",
    "bubble", "collapse", "rekt", "bankrupt", "scam", "fraud", "hack",
    "regulation", "ban", "fine", "lawsuit", "investigation", "warning"
}

ASSETS  = ["BTC", "ETH", "SOL", "TSLA", "SPY", "AAPL", "NVDA", "DOGE", "BNB", "ADA"]
SOURCES = ["twitter", "reddit", "news", "financial"]

CRYPTO_SUBREDDITS = "CryptoCurrency+Bitcoin+ethereum+solana+dogecoin"
STOCK_SUBREDDITS  = "stocks+investing+wallstreetbets+StockMarket"


# ─────────────────────────────────────────────
# Sentiment Analyzer
# ─────────────────────────────────────────────

class SentimentAnalyzer:
    """
    NLP processing engine for text sentiment scoring.
    Uses keyword-based analysis with confidence weighting.

    Formula:
      sentiment  = (positive - negative) / max(total_sentiment_words, 1)
      confidence = min(sentiment_words / total_words * 3, 1.0)
      fear_greed = (greed_keywords / max(total_emotion_keywords, 1)) * 100
    """

    def __init__(self):
        self.logger = logging.getLogger("SentimentAnalyzer")
        self.analyzed_count = 0

    def analyze(self, text: str, asset: str = "MARKET") -> dict:
        words = set(text.lower().split())

        positive_matches = words & POSITIVE_WORDS
        negative_matches = words & NEGATIVE_WORDS
        greed_matches    = words & GREED_KEYWORDS
        fear_matches     = words & FEAR_KEYWORDS

        pos_count       = len(positive_matches)
        neg_count       = len(negative_matches)
        total_sentiment = pos_count + neg_count
        total_emotion   = len(greed_matches) + len(fear_matches)
        total_words     = max(len(text.split()), 1)

        sentiment_score = (pos_count - neg_count) / max(total_sentiment, 1)
        confidence      = min(total_sentiment / total_words * 3, 1.0)
        fear_greed      = (len(greed_matches) / max(total_emotion, 1)) * 100 if total_emotion > 0 else 50.0

        self.analyzed_count += 1

        return {
            "sentiment_score":  round(sentiment_score, 4),
            "confidence":       round(confidence, 4),
            "fear_greed_score": round(fear_greed, 2),
            "keywords_found":   list(positive_matches | negative_matches),
            "positive_count":   pos_count,
            "negative_count":   neg_count,
        }


# ─────────────────────────────────────────────
# Data Ingestion Engine
# ─────────────────────────────────────────────

class DataIngestionEngine:
    """
    Multi-source data ingestion engine.

    Automatically uses real APIs when keys are present in environment:
      TWITTER_BEARER_TOKEN              → Twitter/X API v2  (tweepy)
      REDDIT_CLIENT_ID + SECRET         → Reddit API        (praw)
      NEWS_API_KEY                      → NewsAPI.org       (newsapi-python)

    Falls back gracefully to simulation for any missing key.

    Rate-limit delays (real APIs):
      Twitter  : ~2.5 s   (500k tweets/month free tier)
      Reddit   : ~1.5 s   (60 req/min)
      NewsAPI  : ~18 s    (100 req/day free tier)
    """

    TWEET_TEMPLATES = [
        "{asset} is going to the moon! 🚀 #crypto #bullish",
        "Selling all my {asset} right now. Crash incoming!",
        "Just bought more {asset}. Strong support at these levels.",
        "{asset} breakout confirmed! This is going to explode 🔥",
        "{asset} looking bearish. Bears in control now.",
        "HODLing {asset} through this dip. Diamond hands 💎",
        "{asset} dump continuing. Panic selling everywhere!",
        "Huge opportunity in {asset}! Accumulate before the pump.",
        "{asset} rally starting. Don't miss this breakout!",
        "Warning: {asset} showing weakness. Risk management critical.",
        "The {asset} bubble is about to pop. Be careful.",
        "{asset} momentum building. Could see new ATH soon!",
    ]

    REDDIT_TEMPLATES = [
        "{asset} Daily Discussion: Bullish or Bearish?",
        "Why I think {asset} will crash 80% from here",
        "{asset} technical analysis: Major breakout incoming",
        "Should I sell my {asset} now? Down 30% and scared",
        "{asset} fundamentals are stronger than ever. HODL",
        "The {asset} pump is fake. Smart money is dumping",
        "I bought {asset} at the top. What do I do?",
        "{asset} adoption growing rapidly. Bullish long term",
        "Panic selling {asset}? This is exactly when to buy",
        "{asset} chart looks extremely bearish right now",
    ]

    NEWS_TEMPLATES = [
        "{asset} surges {pct}% amid institutional buying",
        "{asset} drops {pct}% as market sentiment turns bearish",
        "Major exchange lists {asset}, triggering price rally",
        "Regulators announce investigation into {asset} trading",
        "{asset} reaches new all-time high as adoption grows",
        "Large {asset} holder moves {amount}M to exchange",
        "{asset} network upgrade boosts confidence, price rises",
        "Analysts warn of {asset} bubble as prices soar",
        "{asset} outperforms broader market amid uncertainty",
        "Flash crash wipes out {pct}% of {asset} gains",
    ]

    def __init__(self, data_queue: deque, analyzer: SentimentAnalyzer):
        self.data_queue     = data_queue
        self.analyzer       = analyzer
        self.running        = False
        self.threads        = []
        self.ingested_count = defaultdict(int)
        self.logger         = logging.getLogger("DataIngestion")

        # ── Detect available real API credentials ────────
        self.twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.reddit_id     = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_agent  = os.getenv("REDDIT_USER_AGENT", "FearGreedEngine/2.0")
        self.news_key      = os.getenv("NEWS_API_KEY")

        self.use_twitter = TWEEPY_AVAILABLE  and bool(self.twitter_token)
        self.use_reddit  = PRAW_AVAILABLE    and bool(self.reddit_id) and bool(self.reddit_secret)
        self.use_news    = NEWSAPI_AVAILABLE and bool(self.news_key)

        for name, live in [("Twitter", self.use_twitter),
                            ("Reddit",  self.use_reddit),
                            ("NewsAPI", self.use_news)]:
            self.logger.info(f"  {name:<10} {'✅ LIVE' if live else '🔶 SIMULATED'}")

        # Lazy-init API clients (created once, reused across calls)
        self._twitter_client = None
        self._reddit_client  = None
        self._news_client    = None

    # ── Start / Stop ─────────────────────────────────────

    def start(self):
        self.running = True
        for source in SOURCES:
            t = threading.Thread(target=self._ingest_loop, args=(source,), daemon=True)
            t.name = f"Ingest-{source}"
            t.start()
            self.threads.append(t)
        self.logger.info(f"Started {len(SOURCES)} ingestion threads")

    def stop(self):
        self.running = False
        self.logger.info("Ingestion engine stopped")

    # ── Main loop per source ──────────────────────────────

    def _ingest_loop(self, source: str):
        delays = {
            "twitter":   2.5 if self.use_twitter else 0.3,
            "reddit":    1.5 if self.use_reddit  else 0.8,
            "news":     18.0 if self.use_news    else 1.5,
            "financial": 0.5,
        }
        delay = delays.get(source, 1.0)

        while self.running:
            try:
                messages = self._fetch_messages(source, count=random.randint(2, 6))
                for msg in messages:
                    if len(self.data_queue) < self.data_queue.maxlen:
                        self.data_queue.append(msg)
                        self.ingested_count[source] += 1
                time.sleep(delay + random.uniform(0, 0.3))
            except Exception as e:
                self.logger.error(f"Ingestion error ({source}): {e}")
                time.sleep(5)

    # ── Dispatcher ───────────────────────────────────────

    def _fetch_messages(self, source: str, count: int) -> list:
        if source == "twitter":
            return self._fetch_twitter(count) if self.use_twitter else self._simulate(source, count)
        elif source == "reddit":
            return self._fetch_reddit(count)  if self.use_reddit  else self._simulate(source, count)
        elif source == "news":
            return self._fetch_news(count)    if self.use_news    else self._simulate(source, count)
        else:
            return self._simulate(source, count)

    # ── Real: Twitter / X API v2 ─────────────────────────

    def _get_twitter_client(self):
        if self._twitter_client is None:
            self._twitter_client = tweepy.Client(
                bearer_token=self.twitter_token,
                wait_on_rate_limit=True
            )
        return self._twitter_client

    def _fetch_twitter(self, count: int) -> list:
        asset = random.choice(ASSETS)
        query = f"({asset} OR #{asset.lower()}) (crypto OR stock OR market) -is:retweet lang:en"
        try:
            client   = self._get_twitter_client()
            response = client.search_recent_tweets(
                query=query,
                max_results=max(10, min(count, 100)),
                tweet_fields=["public_metrics", "created_at"]
            )
            messages = []
            for tweet in (response.data or []):
                result = self.analyzer.analyze(tweet.text, asset)
                messages.append(SentimentData(
                    timestamp=datetime.now(),
                    source="twitter",
                    asset=asset,
                    raw_text=tweet.text,
                    sentiment_score=result["sentiment_score"],
                    confidence=result["confidence"],
                    fear_greed_score=result["fear_greed_score"],
                    keywords_found=result["keywords_found"],
                    engagement=tweet.public_metrics.get("like_count", 0)
                ))
            return messages
        except Exception as e:
            self.logger.warning(f"Twitter API error → simulation: {e}")
            return self._simulate("twitter", count)

    # ── Real: Reddit API ──────────────────────────────────

    def _get_reddit_client(self):
        if self._reddit_client is None:
            self._reddit_client = praw.Reddit(
                client_id=self.reddit_id,
                client_secret=self.reddit_secret,
                user_agent=self.reddit_agent
            )
        return self._reddit_client

    def _fetch_reddit(self, count: int) -> list:
        asset         = random.choice(ASSETS)
        crypto_assets = {"BTC", "ETH", "SOL", "DOGE", "BNB", "ADA"}
        sub           = CRYPTO_SUBREDDITS if asset in crypto_assets else STOCK_SUBREDDITS
        try:
            reddit    = self._get_reddit_client()
            subreddit = reddit.subreddit(sub)
            messages  = []
            for post in subreddit.search(asset, limit=count, sort="new", time_filter="day"):
                text   = f"{post.title} {post.selftext}"[:600]
                result = self.analyzer.analyze(text, asset)
                messages.append(SentimentData(
                    timestamp=datetime.now(),
                    source="reddit",
                    asset=asset,
                    raw_text=text,
                    sentiment_score=result["sentiment_score"],
                    confidence=result["confidence"],
                    fear_greed_score=result["fear_greed_score"],
                    keywords_found=result["keywords_found"],
                    engagement=post.score
                ))
            return messages
        except Exception as e:
            self.logger.warning(f"Reddit API error → simulation: {e}")
            return self._simulate("reddit", count)

    # ── Real: NewsAPI ─────────────────────────────────────

    def _get_news_client(self):
        if self._news_client is None:
            self._news_client = NewsApiClient(api_key=self.news_key)
        return self._news_client

    def _fetch_news(self, count: int) -> list:
        asset = random.choice(ASSETS)
        try:
            client   = self._get_news_client()
            response = client.get_everything(
                q=asset,
                language="en",
                sort_by="publishedAt",
                page_size=min(count, 20)
            )
            messages = []
            for article in response.get("articles", []):
                text = f"{article['title']} {article.get('description', '')}".strip()
                if not text:
                    continue
                result = self.analyzer.analyze(text, asset)
                messages.append(SentimentData(
                    timestamp=datetime.now(),
                    source="news",
                    asset=asset,
                    raw_text=text,
                    sentiment_score=result["sentiment_score"],
                    confidence=result["confidence"],
                    fear_greed_score=result["fear_greed_score"],
                    keywords_found=result["keywords_found"],
                    engagement=0
                ))
            return messages
        except Exception as e:
            self.logger.warning(f"NewsAPI error → simulation: {e}")
            return self._simulate("news", count)

    # ── Simulation fallback ───────────────────────────────

    def _simulate(self, source: str, count: int) -> list:
        messages = []
        for _ in range(count):
            asset  = random.choice(ASSETS)
            text   = self._sim_text(source, asset)
            result = self.analyzer.analyze(text, asset)
            noise  = random.uniform(-0.05, 0.05)
            messages.append(SentimentData(
                timestamp=datetime.now(),
                source=source,
                asset=asset,
                raw_text=text,
                sentiment_score=max(-1.0, min(1.0, result["sentiment_score"] + noise)),
                confidence=result["confidence"],
                fear_greed_score=result["fear_greed_score"],
                keywords_found=result["keywords_found"],
                engagement=random.randint(0, 5000)
            ))
        return messages

    def _sim_text(self, source: str, asset: str) -> str:
        pct    = random.randint(2, 25)
        amount = random.randint(10, 500)
        if source == "twitter":
            return random.choice(self.TWEET_TEMPLATES).format(asset=asset)
        elif source == "reddit":
            return random.choice(self.REDDIT_TEMPLATES).format(asset=asset)
        elif source == "news":
            return random.choice(self.NEWS_TEMPLATES).format(asset=asset, pct=pct, amount=amount)
        return f"{asset} price {'up' if random.random() > 0.5 else 'down'} {pct}% volume surge detected"


# ─────────────────────────────────────────────
# Signal Generator
# ─────────────────────────────────────────────

class SignalGenerator:
    """
    Generates BUY / SELL / HOLD signals using multi-factor analysis:
    - Sentiment momentum
    - Fear/Greed index
    - Confidence weighting
    - Volatility assessment
    - Engagement weighting
    """

    BUY_THRESHOLD        = 0.3
    SELL_THRESHOLD       = -0.3
    CONFIDENCE_THRESHOLD = 0.4
    COOLDOWN_MINUTES     = 5
    MIN_DATA_POINTS      = 5

    def __init__(self):
        self.signals: deque         = deque(maxlen=500)
        self.last_signal_time: dict = {}
        self.logger = logging.getLogger("SignalGenerator")

    def evaluate(self, asset: str, history: list) -> Optional[TradeSignal]:
        if len(history) < self.MIN_DATA_POINTS:
            return None

        last = self.last_signal_time.get(asset)
        if last and (datetime.now() - last).seconds < self.COOLDOWN_MINUTES * 60:
            return None

        recent      = history[-20:]
        scores      = [d.sentiment_score  for d in recent]
        fg_scores   = [d.fear_greed_score for d in recent]
        confidences = [d.confidence       for d in recent]
        engagements = [d.engagement       for d in recent]

        avg_sentiment  = statistics.mean(scores)
        avg_fg         = statistics.mean(fg_scores)
        avg_confidence = statistics.mean(confidences)

        if len(scores) >= 10:
            momentum = statistics.mean(scores[-5:]) - statistics.mean(scores[-10:-5])
        else:
            momentum = 0

        total_eng          = sum(engagements) or 1
        weighted_sentiment = sum(s * e for s, e in zip(scores, engagements)) / total_eng

        try:
            volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        except statistics.StatisticsError:
            volatility = 0

        combined = (avg_sentiment * 0.4 + weighted_sentiment * 0.3 + momentum * 0.3)

        if avg_confidence < self.CONFIDENCE_THRESHOLD:
            return None

        risk     = "Low" if volatility < 0.2 else "Medium" if volatility < 0.4 else "High"
        duration = "Short-term" if abs(momentum) > 0.1 else "Medium-term"

        if combined >= self.BUY_THRESHOLD:
            sig_type  = "BUY"
            strength  = min(combined / 0.8, 1.0)
            reasoning = (
                f"Positive sentiment momentum ({avg_sentiment:.2f}), "
                f"Fear/Greed at {avg_fg:.1f} (Greed), "
                f"momentum {momentum:+.3f}"
            )
        elif combined <= self.SELL_THRESHOLD:
            sig_type  = "SELL"
            strength  = min(abs(combined) / 0.8, 1.0)
            reasoning = (
                f"Negative sentiment momentum ({avg_sentiment:.2f}), "
                f"Fear/Greed at {avg_fg:.1f} (Fear), "
                f"momentum {momentum:+.3f}"
            )
        else:
            return None

        signal = TradeSignal(
            timestamp=datetime.now(),
            asset=asset,
            signal_type=sig_type,
            confidence=round(avg_confidence, 3),
            strength=round(strength, 3),
            expected_duration=duration,
            risk_level=risk,
            reasoning=reasoning,
            fear_greed_at_signal=round(avg_fg, 2),
            sentiment_score=round(combined, 4)
        )

        self.signals.append(signal)
        self.last_signal_time[asset] = datetime.now()
        self.logger.info(f"Signal: {sig_type} {asset} | conf={avg_confidence:.2f} | strength={strength:.2f}")
        return signal

    def get_recent_signals(self, n: int = 10) -> list:
        return list(self.signals)[-n:]

    def get_signal_stats(self) -> dict:
        all_sig = list(self.signals)
        if not all_sig:
            return {"total": 0, "buy": 0, "sell": 0}
        return {
            "total":          len(all_sig),
            "buy":            sum(1 for s in all_sig if s.signal_type == "BUY"),
            "sell":           sum(1 for s in all_sig if s.signal_type == "SELL"),
            "avg_confidence": round(statistics.mean(s.confidence for s in all_sig), 3),
        }


# ─────────────────────────────────────────────
# Fear & Greed Engine (Main)
# ─────────────────────────────────────────────

class FearGreedEngine:
    """
    Central coordination hub for the sentiment analysis system.

    Threading Architecture:
      Main Thread
        ├── Data Ingestion Thread Pool (Twitter, Reddit, News, Financial)
        ├── Processing Thread (Sentiment → Asset history)
        ├── Signal Generation Thread
        └── Analytics Thread
    """

    def __init__(self, config: dict = None):
        self.config  = config or {}
        self.running = False

        self.data_queue: deque   = deque(maxlen=self.config.get("max_queue_size", 2000))
        self.asset_history: dict = defaultdict(lambda: deque(maxlen=500))
        self.signals: list       = []
        self.performance_metrics: dict = {}

        self.analyzer         = SentimentAnalyzer()
        self.ingestion        = DataIngestionEngine(self.data_queue, self.analyzer)
        self.signal_generator = SignalGenerator()

        self.start_time: Optional[datetime] = None
        self.messages_processed = 0
        self.lock = threading.Lock()

        self.logger = logging.getLogger("FearGreedEngine")
        self.logger.info("Fear & Greed Engine initialized")

    # ── Start / Stop ─────────────────────────

    def start_engine(self):
        self.running    = True
        self.start_time = datetime.now()
        self.ingestion.start()
        threading.Thread(target=self._processing_loop, daemon=True, name="Processor").start()
        threading.Thread(target=self._signal_loop,     daemon=True, name="SignalGen").start()
        threading.Thread(target=self._analytics_loop,  daemon=True, name="Analytics").start()
        self.logger.info("✅ All engine components started")

    def stop_engine(self):
        self.running = False
        self.ingestion.stop()
        self.logger.info("Engine stopped")

    # ── Internal Loops ───────────────────────

    def _processing_loop(self):
        batch_size = self.config.get("batch_size", 50)
        interval   = self.config.get("processing_interval", 0.1)
        while self.running:
            processed = 0
            while self.data_queue and processed < batch_size:
                data = self.data_queue.popleft()
                with self.lock:
                    self.asset_history[data.asset].append(data)
                    self.messages_processed += 1
                processed += 1
            time.sleep(interval)

    def _signal_loop(self):
        while self.running:
            for asset in ASSETS:
                with self.lock:
                    history = list(self.asset_history[asset])
                signal = self.signal_generator.evaluate(asset, history)
                if signal:
                    with self.lock:
                        self.signals.append(signal)
            time.sleep(2)

    def _analytics_loop(self):
        interval = self.config.get("metrics_interval", 300)
        while self.running:
            self._compute_performance_metrics()
            time.sleep(interval)

    def _compute_performance_metrics(self):
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        rate   = self.messages_processed / max(uptime / 60, 0.001)
        self.performance_metrics = {
            "uptime_seconds":          round(uptime, 1),
            "messages_processed":      self.messages_processed,
            "processing_rate_per_min": round(rate, 2),
            "signals_generated":       len(self.signals),
            "assets_tracked":          len(self.asset_history),
            "queue_size":              len(self.data_queue),
        }

    # ── Public API ────────────────────────────

    def get_market_summary(self) -> dict:
        all_data = []
        with self.lock:
            for hist in self.asset_history.values():
                all_data.extend(list(hist)[-50:])

        if not all_data:
            return {"status": "warming_up", "message": "Collecting data, please wait..."}

        scores    = [d.sentiment_score  for d in all_data]
        fg_scores = [d.fear_greed_score for d in all_data]
        avg_sent  = statistics.mean(scores)
        avg_fg    = statistics.mean(fg_scores)

        q         = max(len(scores) // 4, 1)
        trend_val = statistics.mean(scores[-q:]) - statistics.mean(scores[:q])
        trend     = "increasing" if trend_val > 0.05 else "decreasing" if trend_val < -0.05 else "stable"

        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        rate   = self.messages_processed / max(uptime / 60, 0.001)

        return {
            "timestamp":                datetime.now().isoformat(),
            "market_mood":              self._score_to_mood(avg_sent, avg_fg),
            "sentiment_score":          round(avg_sent, 4),
            "sentiment_trend":          trend,
            "fear_greed_index":         round(avg_fg, 2),
            "fear_greed_level":         self._fg_to_level(avg_fg),
            "data_points_analyzed":     len(all_data),
            "total_messages_processed": self.messages_processed,
            "processing_rate":          round(rate, 2),
        }

    def get_asset_analysis(self, asset: str) -> dict:
        asset = asset.upper()
        with self.lock:
            history = list(self.asset_history.get(asset, []))

        if not history:
            return {"asset": asset, "status": "no_data"}

        recent      = history[-50:]
        scores      = [d.sentiment_score  for d in recent]
        fg_scores   = [d.fear_greed_score for d in recent]
        confidences = [d.confidence       for d in recent]

        avg_sent = statistics.mean(scores)
        avg_fg   = statistics.mean(fg_scores)
        avg_conf = statistics.mean(confidences)

        source_scores = defaultdict(list)
        for d in recent:
            source_scores[d.source].append(d.sentiment_score)
        source_avg = {s: round(statistics.mean(v), 3) for s, v in source_scores.items()}

        if avg_sent > 0.3 and avg_conf > 0.5:
            rec = "BUY — Strong positive sentiment with high confidence"
        elif avg_sent < -0.3 and avg_conf > 0.5:
            rec = "SELL — Strong negative sentiment with high confidence"
        else:
            rec = "HOLD — Insufficient signal strength or mixed sentiment"

        all_kw = []
        for d in recent:
            all_kw.extend(d.keywords_found)
        top_kw = [kw for kw, _ in Counter(all_kw).most_common(10)]

        return {
            "asset":            asset,
            "timestamp":        datetime.now().isoformat(),
            "sentiment_score":  round(avg_sent, 4),
            "fear_greed_index": round(avg_fg, 2),
            "fear_greed_level": self._fg_to_level(avg_fg),
            "confidence":       round(avg_conf, 3),
            "recommendation":   rec,
            "data_points":      len(recent),
            "source_sentiment": source_avg,
            "top_keywords":     top_kw,
        }

    def get_all_assets(self) -> dict:
        result = {}
        for asset in ASSETS:
            with self.lock:
                history = list(self.asset_history.get(asset, []))
            if history:
                scores = [d.sentiment_score  for d in history[-20:]]
                fg     = [d.fear_greed_score for d in history[-20:]]
                result[asset] = {
                    "sentiment":   round(statistics.mean(scores), 3),
                    "fear_greed":  round(statistics.mean(fg), 1),
                    "level":       self._fg_to_level(statistics.mean(fg)),
                    "data_points": len(history),
                }
        return result

    def get_fear_greed_index(self) -> dict:
        summary = self.get_market_summary()
        if "fear_greed_index" not in summary:
            return {"status": "warming_up"}
        fg = summary["fear_greed_index"]
        return {
            "index":          fg,
            "level":          self._fg_to_level(fg),
            "interpretation": self._fg_interpretation(fg),
            "timestamp":      datetime.now().isoformat(),
        }

    def export_data(self, filename: str = None) -> str:
        if not filename:
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/fear_greed_export_{ts}.json"

        def _serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Not serializable: {type(obj)}")

        export = {
            "export_timestamp":    datetime.now().isoformat(),
            "market_summary":      self.get_market_summary(),
            "all_assets":          self.get_all_assets(),
            "recent_signals":      [asdict(s) for s in self.signal_generator.get_recent_signals(20)],
            "signal_stats":        self.signal_generator.get_signal_stats(),
            "performance_metrics": self.performance_metrics,
        }

        with open(filename, "w") as f:
            json.dump(export, f, indent=2, default=_serial)

        self.logger.info(f"Data exported to {filename}")
        return filename

    # ── Helpers ───────────────────────────────

    @staticmethod
    def _score_to_mood(sentiment: float, fg: float) -> str:
        if sentiment > 0.5 and fg > 65:  return "Extremely Bullish"
        if sentiment > 0.3 and fg > 55:  return "Bullish"
        if sentiment > 0.1:              return "Cautiously Bullish"
        if sentiment < -0.5 and fg < 35: return "Extremely Bearish"
        if sentiment < -0.3 and fg < 45: return "Bearish"
        if sentiment < -0.1:             return "Cautiously Bearish"
        return "Neutral"

    @staticmethod
    def _fg_to_level(score: float) -> str:
        if score < 25: return "Extreme Fear"
        if score < 45: return "Fear"
        if score < 55: return "Neutral"
        if score < 75: return "Greed"
        return "Extreme Greed"

    @staticmethod
    def _fg_interpretation(score: float) -> str:
        if score < 25: return "Extreme Fear — contrarian buy opportunity may exist"
        if score < 45: return "Fear — cautious approach recommended"
        if score < 55: return "Neutral — balanced sentiment, wait for direction"
        if score < 75: return "Greed — monitor for potential reversal"
        return "Extreme Greed — consider taking profits"




