"""
Fear & Greed Sentiment Engine - Interactive CLI Dashboard
=========================================================
"""

import time
import os
import sys
import json
from datetime import datetime

# ✅ FIX 1: Force UTF-8 (prevents emoji + box crash)
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

# Add parent dir to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fear_greed_engine import FearGreedEngine, ASSETS


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def red(t): return color(t, "91")
def green(t): return color(t, "92")
def yellow(t): return color(t, "93")
def cyan(t): return color(t, "96")
def bold(t): return color(t, "1")
def dim(t): return color(t, "2")


def fg_color(score):
    if score < 25: return red
    elif score < 45: return lambda t: color(t, "33")
    elif score < 55: return lambda t: color(t, "37")
    elif score < 75: return yellow
    else: return green


def sentiment_color(score):
    if score > 0.2: return green
    elif score < -0.2: return red
    return yellow


def draw_bar(value, max_val=100, width=30, fill="█", empty="░"):
    filled = int((value / max_val) * width)
    bar = fill * filled + empty * (width - filled)
    return bar


def render_dashboard(engine: FearGreedEngine):
    clear()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(bold(cyan("╔══════════════════════════════════════════════════════════════╗")))
    print(bold(cyan("║       FEAR & GREED SENTIMENT ENGINE  —  Live Dashboard       ║")))
    print(bold(cyan("╚══════════════════════════════════════════════════════════════╝")))
    print(dim(f"  Updated: {now}  |  Press Ctrl+C to exit\n"))

    # ── Market Summary ──
    summary = engine.get_market_summary()
    if "status" in summary:
        print(yellow("  ⏳ Warming up... collecting initial data"))
        return

    fg_idx = summary["fear_greed_index"]
    fg_fn = fg_color(fg_idx)
    mood_fn = green if "Bullish" in summary["market_mood"] else red if "Bearish" in summary["market_mood"] else yellow

    print(bold("  📊 MARKET OVERVIEW"))
    print(f"  {'Market Mood':<22} {mood_fn(bold(summary['market_mood']))}")

    # ✅ FIX 2: Proper f-string handling
    score = summary['sentiment_score']
    formatted_score = f"{score:+.4f}"
    print(f"  {'Sentiment Score':<22} {sentiment_color(score)(formatted_score)}")

    print(f"  {'Trend':<22} {summary['sentiment_trend']}")
    print(f"  {'Messages Processed':<22} {summary['total_messages_processed']:,}")
    print(f"  {'Processing Rate':<22} {summary['processing_rate']:.1f} msg/min")

    print()
    print(bold("  🧠 FEAR & GREED INDEX"))
    bar = draw_bar(fg_idx)
    print(f"  {fg_fn(f'{fg_idx:5.1f}')}  [{fg_fn(bar)}]")
    print(f"  Level: {fg_fn(bold(summary['fear_greed_level']))}")
    print()

    # ── Asset Table ──
    assets_data = engine.get_all_assets()
    print(bold("  💹 ASSET SENTIMENT OVERVIEW"))
    print(f"  {'Asset':<8} {'Sentiment':>10} {'F&G Index':>10} {'Level':<16} {'Data Pts':>8}")
    print("  " + "─" * 60)

    for asset, data in sorted(assets_data.items(), key=lambda x: -abs(x[1]['sentiment'])):
        s = data['sentiment']
        fg = data['fear_greed']

        s_str = f"{s:+.3f}"
        s_colored = sentiment_color(s)(s_str)

        fg_str = f"{fg:.1f}"
        fg_col = fg_color(fg)(fg_str)

        level = fg_color(fg)(data['level'])

        print(f"  {asset:<8} {s_colored:>18} {fg_col:>18}  {level:<22} {data['data_points']:>8}")

    print()

    # ── Recent Signals ──
    signals = engine.signal_generator.get_recent_signals(8)
    if signals:
        print(bold("  🔔 RECENT TRADE SIGNALS"))
        print(f"  {'Time':<10} {'Asset':<6} {'Signal':<6} {'Conf':>6} {'Strength':>9} {'Risk':<8}")
        print("  " + "─" * 55)

        for sig in reversed(signals):
            ts = sig.timestamp.strftime("%H:%M:%S")
            sig_fn = green if sig.signal_type == "BUY" else red

            print(
                f"  {ts:<10} {sig.asset:<6} {sig_fn(sig.signal_type):<14} "
                f"{sig.confidence:>5.0%} {sig.strength:>8.0%}  {sig.risk_level:<8}"
            )
    else:
        print(bold("  🔔 RECENT SIGNALS"))
        print(dim("  No signals yet — engine is warming up..."))

    # ── Signal Stats ──
    stats = engine.signal_generator.get_signal_stats()
    if stats["total"] > 0:
        print()
        print(bold("  📈 SIGNAL STATISTICS"))
        print(f"  Total: {stats['total']}  |  "
              f"{green('BUY: ' + str(stats['buy']))}  |  "
              f"{red('SELL: ' + str(stats['sell']))}  |  "
              f"Avg Confidence: {stats.get('avg_confidence', 0):.1%}")

    print()
    print(dim("  Commands: [e] Export data  [a <ASSET>] Asset detail  [q] Quit"))


def asset_detail(engine: FearGreedEngine, asset: str):
    data = engine.get_asset_analysis(asset)
    if "status" in data:
        print(red(f"\n  No data yet for {asset}. Try again in a moment.\n"))
        return

    print()
    print(bold(f"  📋 DETAILED ANALYSIS: {data['asset']}"))
    print(f"  {'Sentiment Score':<25} {data['sentiment_score']:+.4f}")
    print(f"  {'Fear & Greed Index':<25} {data['fear_greed_index']} ({data['fear_greed_level']})")
    print(f"  {'Confidence':<25} {data['confidence']:.1%}")
    print(f"  {'Recommendation':<25} {data['recommendation']}")
    print(f"  {'Data Points':<25} {data['data_points']}")

    print()
    print(bold("  Source Sentiment Breakdown:"))
    for src, val in data.get("source_sentiment", {}).items():
        col = sentiment_color(val)
        print(f"    {src:<12} {col(f'{val:+.3f}')}")

    print()
    print(f"  Top Keywords: {', '.join(data.get('top_keywords', []))}")
    print()
    input(dim("  Press Enter to return to dashboard..."))


def main():
    print(bold(cyan("\n🚀 Starting Fear & Greed Sentiment Engine...\n")))

    engine = FearGreedEngine(config={
        "max_queue_size": 2000,
        "batch_size": 50,
        "processing_interval": 0.1,
        "metrics_interval": 60
    })

    engine.start_engine()
    print(green("  ✅ Engine started. Collecting data...\n"))
    time.sleep(3)

    try:
        while True:
            render_dashboard(engine)

            # ✅ FIX 3: Windows-safe input handling
            if os.name == 'nt':
                time.sleep(4)
                continue
            else:
                import select
                print("\n  > ", end="", flush=True)
                rlist, _, _ = select.select([sys.stdin], [], [], 4)
                if rlist:
                    cmd = sys.stdin.readline().strip().lower()

                    if cmd == "q":
                        break
                    elif cmd == "e":
                        fname = engine.export_data()
                        print(green(f"\nExported to {fname}"))
                        time.sleep(2)
                    elif cmd.startswith("a "):
                        asset_detail(engine, cmd[2:].strip().upper())

    except (KeyboardInterrupt, EOFError):
        pass

    print(bold(yellow("\n\n  Stopping engine...")))
    engine.stop_engine()
    fname = engine.export_data()
    print(green(f"  Final data exported to: {fname}"))
    print(bold(cyan("  Goodbye!")))


if __name__ == "__main__":
    main()