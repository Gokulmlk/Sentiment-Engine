# ⚡ Fear & Greed Sentiment Engine

Real-time sentiment analysis engine for generating trading signals based on
multi-source data (Twitter, Reddit, News, Financial feeds).

---

## 📁 Project Structure

```
fear_greed_engine/
├── fear_greed_engine.py   ← Core engine (all logic here)
├── demo.py                ← Quick demo — run this first!
├── dashboard.py           ← Live terminal dashboard
├── api_server.py          ← REST API server (Flask)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── tests/
│   └── test_engine.py
├── logs/                  ← Auto-created on first run
└── exports/               ← Auto-created on first run
```

---

## 🚀 Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Minimum:** No extra packages needed for demo/dashboard (pure stdlib).  
> Flask is only needed for `api_server.py`.

### 2. Run the demo

```bash
python demo.py
```

Runs for ~30 seconds, prints market summary, asset analysis, signals, and exports a JSON file.

### 3. Live terminal dashboard

```bash
python dashboard.py
```

Interactive live-updating dashboard. Commands while running:
- `e` → Export current data to JSON
- `a BTC` → Show detailed BTC analysis
- `q` → Quit

### 4. REST API server

```bash
pip install flask flask-cors
python api_server.py
```

Then open: **http://localhost:5000**

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + uptime |
| GET | `/api/summary` | Full market overview |
| GET | `/api/fear-greed` | Current Fear & Greed Index |
| GET | `/api/assets` | All assets overview |
| GET | `/api/asset/BTC` | Asset-specific analysis |
| GET | `/api/signals?n=20` | Recent trade signals |
| GET | `/api/signals/stats` | Signal statistics |
| POST | `/api/export` | Export data to file |

### Example API response: `/api/summary`

```json
{
  "timestamp": "2025-07-15T14:30:00",
  "market_mood": "Cautiously Bullish",
  "sentiment_score": 0.234,
  "sentiment_trend": "increasing",
  "fear_greed_index": 67.5,
  "fear_greed_level": "Greed",
  "data_points_analyzed": 150,
  "total_messages_processed": 1247,
  "processing_rate": 312.5
}
```

---

## 🐳 Docker

### Build and run

```bash
docker build -t fear-greed-engine .
docker run -p 5000:5000 fear-greed-engine
```

### Docker Compose (recommended)

```bash
docker-compose up -d
```

Logs and exports are mounted as volumes.

---

## 🧪 Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Or directly
python tests/test_engine.py
```

---

## 🔧 Use the Engine in Your Code

```python
from fear_greed_engine import FearGreedEngine

# Initialize
engine = FearGreedEngine()
engine.start_engine()

import time
time.sleep(10)  # Let data accumulate

# Market summary
summary = engine.get_market_summary()
print(f"Mood: {summary['market_mood']}")
print(f"Fear/Greed: {summary['fear_greed_index']}")

# Asset analysis
btc = engine.get_asset_analysis("BTC")
print(f"BTC recommendation: {btc['recommendation']}")

# Trade signals
signals = engine.signal_generator.get_recent_signals(5)
for sig in signals:
    print(f"{sig.signal_type} {sig.asset} | conf={sig.confidence:.0%}")

# Export
engine.export_data("my_export.json")

engine.stop_engine()
```

---

## 📊 Fear & Greed Index Scale

| Score | Level | Interpretation |
|-------|-------|---------------|
| 0–25 | Extreme Fear | Contrarian buy opportunity |
| 25–45 | Fear | Cautious approach |
| 45–55 | Neutral | Balanced sentiment |
| 55–75 | Greed | Monitor for reversal |
| 75–100 | Extreme Greed | Consider taking profits |

---

## 🔌 Signal Interpretation

| Signal | Meaning | Action |
|--------|---------|--------|
| BUY | Positive sentiment momentum | Consider long position |
| SELL | Negative sentiment momentum | Consider short position |
| HOLD | Neutral / insufficient confidence | Wait for clearer signal |

**Confidence levels:**
- High (80%+) — Strong sentiment consensus
- Medium (50–80%) — Moderate agreement
- Low (<50%) — Weak or conflicting signals

---

## 🔑 Production: Real API Keys

To connect real data sources, replace the simulation methods in
`DataIngestionEngine` with actual API calls:

```bash
# In your .env file:
TWITTER_BEARER_TOKEN=your_token_here
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
NEWS_API_KEY=your_news_api_key
```

Then modify `_fetch_messages()` in `DataIngestionEngine` to call real APIs
using `tweepy`, `praw`, and `newsapi-python`.

---

## ⚙️ Configuration

```python
engine = FearGreedEngine(config={
    "max_queue_size": 2000,       # Max items in processing queue
    "batch_size": 50,             # Items processed per batch
    "processing_interval": 0.1,   # Seconds between batches
    "metrics_interval": 300       # Seconds between analytics snapshots
})
```

Signal thresholds (edit `SignalGenerator` class):
- `BUY_THRESHOLD = 0.3` — Minimum positive score to trigger BUY
- `SELL_THRESHOLD = -0.3` — Maximum negative score to trigger SELL
- `CONFIDENCE_THRESHOLD = 0.4` — Minimum confidence required
- `COOLDOWN_MINUTES = 5` — Minimum time between signals per asset

---

## 📋 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Processing Rate | 100–500 msg/min | Simulation mode |
| Memory Usage | 50–200MB | Depends on history size |
| Signal Precision | ~65% | Simulation baseline |
| Uptime | 99.5% | With proper error handling |

---

## ⚠️ Disclaimer

This is a **simulation engine** for educational and development purposes.
The sentiment data is synthetically generated. Do not use this for actual
financial decisions without connecting real data sources and conducting
thorough backtesting.

---

*Fear & Greed Sentiment Engine v1.0 — Built with Python 3.8+*
