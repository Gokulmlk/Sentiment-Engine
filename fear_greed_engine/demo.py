"""
Fear & Greed Sentiment Engine - Demo Script
============================================
Runs the engine for 60 seconds and prints results.
"""

import sys
import os

# ✅ FIX 1: Force UTF-8 (prevents emoji + arrow crash)
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

import logging

# ✅ FIX 2: Fix logging encoding
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fear_greed_engine import FearGreedEngine


def separator(title=""):
    line = "═" * 60
    if title:
        print(f"\n{'═'*5} {title} {'═'*(54-len(title))}")
    else:
        print(line)


def main():
    print("=" * 60)
    print("   FEAR & GREED SENTIMENT ENGINE — DEMO")
    print("=" * 60)

    # Initialize engine
    print("\n[1/4] Initializing engine...")
    engine = FearGreedEngine()

    # Start engine
    print("[2/4] Starting all components...")
    engine.start_engine()

    # Warm-up
    print("[3/4] Warming up (15 seconds of data collection)...")
    for i in range(15):
        print(f"      Collecting data... {i+1}/15s  "
              f"(queue: {len(engine.data_queue)} items, "
              f"processed: {engine.messages_processed})", end="\r")
        time.sleep(1)
    print()

    print("[4/4] Generating analysis...\n")

    # ── Market Summary ──
    separator("MARKET SUMMARY")
    summary = engine.get_market_summary()
    for k, v in summary.items():
        print(f"  {k:<30} {v}")

    # ── Fear & Greed Index ──
    separator("FEAR & GREED INDEX")
    fg = engine.get_fear_greed_index()
    for k, v in fg.items():
        print(f"  {k:<30} {v}")

    # ── All Assets Overview ──
    separator("ALL ASSETS OVERVIEW")
    assets = engine.get_all_assets()
    print(f"  {'Asset':<8} {'Sentiment':>10} {'F&G Index':>10} {'Level':<16} {'Data Pts':>8}")
    print("  " + "-" * 58)
    for asset, data in sorted(assets.items()):
        print(
            f"  {asset:<8} {data['sentiment']:>+10.3f} "
            f"{data['fear_greed']:>10.1f} "
            f"{data['level']:<16} "
            f"{data['data_points']:>8}"
        )

    # ── Asset Detail: BTC ──
    separator("DETAILED ANALYSIS: BTC")
    btc = engine.get_asset_analysis("BTC")
    for k, v in btc.items():
        if k != "source_sentiment":
            print(f"  {k:<30} {v}")
    print(f"  {'source_sentiment':<30}")
    for src, val in btc.get("source_sentiment", {}).items():
        print(f"    {src:<28} {val:+.3f}")

    # ── Run more to get signals ──
    separator("WAITING FOR SIGNALS (15s)")
    for i in range(15):
        print(f"      Processing... {i+1}/15s | Signals so far: {len(engine.signal_generator.signals)}", end="\r")
        time.sleep(1)
    print()

    # ── Trade Signals ──
    separator("RECENT TRADE SIGNALS")
    signals = engine.signal_generator.get_recent_signals(10)
    if signals:
        for sig in signals:
            print(f"\n  [{sig.signal_type}] {sig.asset}")
            print(f"    Confidence:  {sig.confidence:.1%}")
            print(f"    Strength:    {sig.strength:.1%}")
            print(f"    Risk Level:  {sig.risk_level}")
            print(f"    Duration:    {sig.expected_duration}")
            print(f"    F&G at time: {sig.fear_greed_at_signal}")
            print(f"    Reasoning:   {sig.reasoning}")
    else:
        print("  No signals generated yet. Run longer for signals.")

    # ── Signal Stats ──
    stats = engine.signal_generator.get_signal_stats()
    separator("SIGNAL STATISTICS")
    for k, v in stats.items():
        print(f"  {k:<30} {v}")

    # ── Export ──
    separator("EXPORTING DATA")
    export_file = engine.export_data()
    print(f"  Data exported to: {export_file}")

    # Stop
    engine.stop_engine()
    separator()
    print("\n  ✅ Demo complete!")
    print(f"  Check '{export_file}' for full exported data.")
    print(f"  Check 'logs/sentiment_engine.log' for detailed logs.")
    print("\n  Next steps:")
    print("    python dashboard.py    → Live terminal dashboard")
    print("    python api_server.py   → REST API server\n")


if __name__ == "__main__":
    main()