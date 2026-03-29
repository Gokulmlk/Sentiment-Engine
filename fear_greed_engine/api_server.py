"""
Fear & Greed Sentiment Engine - REST API Server
================================================
"""

import sys
import os

# ✅ FIX: Force UTF-8 encoding (prevents emoji crash on Windows)
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

import time
import json
import threading
from datetime import datetime

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fear_greed_engine import FearGreedEngine

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
except ImportError:
    print("\n❌ Flask not installed. Run:")
    print("   pip install flask flask-cors\n")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Global engine instance
engine = FearGreedEngine()
engine_started = False


def start_engine_once():
    global engine_started
    if not engine_started:
        engine.start_engine()
        engine_started = True
        time.sleep(3)  # warm up


def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object not serializable: {type(obj)}")


@app.before_request
def ensure_engine():
    start_engine_once()


# ── Routes ──────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime_seconds": (datetime.now() - engine.start_time).total_seconds() if engine.start_time else 0,
        "messages_processed": engine.messages_processed,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/summary")
def market_summary():
    return jsonify(engine.get_market_summary())


@app.route("/api/fear-greed")
def fear_greed():
    return jsonify(engine.get_fear_greed_index())


@app.route("/api/assets")
def all_assets():
    return jsonify(engine.get_all_assets())


@app.route("/api/asset/<symbol>")
def asset_analysis(symbol):
    return jsonify(engine.get_asset_analysis(symbol.upper()))


@app.route("/api/signals")
def signals():
    n = request.args.get("n", 20, type=int)
    raw = engine.signal_generator.get_recent_signals(n)
    result = []
    for s in raw:
        d = {
            "timestamp": s.timestamp.isoformat(),
            "asset": s.asset,
            "signal_type": s.signal_type,
            "confidence": s.confidence,
            "strength": s.strength,
            "expected_duration": s.expected_duration,
            "risk_level": s.risk_level,
            "reasoning": s.reasoning,
            "fear_greed_at_signal": s.fear_greed_at_signal,
            "sentiment_score": s.sentiment_score
        }
        result.append(d)
    return jsonify(result)


@app.route("/api/signals/stats")
def signal_stats():
    return jsonify(engine.signal_generator.get_signal_stats())


@app.route("/api/export", methods=["POST"])
def export():
    fname = engine.export_data()
    return jsonify({"status": "success", "file": fname})


@app.route("/")
def index():
    return """
    <html><body style="font-family:monospace;padding:30px;background:#0d1117;color:#e2e8f0">
    <h2>⚡ Fear & Greed Sentiment Engine API</h2>
    <p>Available endpoints:</p>
    <ul>
      <li><a href="/api/health" style="color:#00e5ff">GET /api/health</a></li>
      <li><a href="/api/summary" style="color:#00e5ff">GET /api/summary</a></li>
      <li><a href="/api/fear-greed" style="color:#00e5ff">GET /api/fear-greed</a></li>
      <li><a href="/api/assets" style="color:#00e5ff">GET /api/assets</a></li>
      <li><a href="/api/asset/BTC" style="color:#00e5ff">GET /api/asset/&lt;SYMBOL&gt;</a></li>
      <li><a href="/api/signals" style="color:#00e5ff">GET /api/signals</a></li>
      <li><a href="/api/signals/stats" style="color:#00e5ff">GET /api/signals/stats</a></li>
      <li>POST /api/export</li>
    </ul>
    </body></html>
    """


if __name__ == "__main__":
    print("\n⚡ Fear & Greed Sentiment Engine — API Server")
    print("=" * 50)
    print("Starting engine...")
    start_engine_once()
    print("✅ Engine running")
    print("\nAPI available at: http://localhost:3000")
    print("Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=3000, debug=False)