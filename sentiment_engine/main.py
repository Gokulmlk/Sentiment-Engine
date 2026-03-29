"""
Main entry point for the Fear & Greed Sentiment Engine
"""

import argparse
import sys
import time
from pathlib import Path

from sentiment_engine.core.engine import FearGreedEngine
from sentiment_engine.config.settings import get_settings
from sentiment_engine.utils.helpers import setup_logging

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Fear & Greed Sentiment Engine')
    parser.add_argument('--config', '-c', default='development', 
                       help='Configuration environment (development/production/testing)')
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode with mock data')
    parser.add_argument('--api', action='store_true',
                       help='Start REST API server')
    parser.add_argument('--duration', type=int, default=0,
                       help='Run duration in seconds (0 = infinite)')
    
    args = parser.parse_args()
    
    # Load configuration
    settings = get_settings(args.config)
    
    # Setup logging
    setup_logging(settings.logging)
    
    # Initialize engine
    engine = FearGreedEngine(settings)
    
    try:
        if args.api:
            from sentiment_engine.api.routes import create_app
            app = create_app(engine)
            app.run(host='0.0.0.0', port=8080, debug=settings.debug)
        else:
            run_engine(engine, args.duration, args.demo)
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        engine.stop_engine()

def run_engine(engine, duration=0, demo=False):
    """Run the sentiment engine"""
    print("🚀 Starting Fear & Greed Sentiment Engine")
    
    engine.start_engine()
    
    start_time = time.time()
    
    try:
        while True:
            time.sleep(5)
            
            # Print status update
            summary = engine.get_market_summary()
            print(f"📊 Mood: {summary.get('market_mood', 'Unknown')} | "
                  f"Sentiment: {summary.get('sentiment_score', 0):.3f} | "
                  f"F&G: {summary.get('fear_greed_index', 50):.1f}")
            
            # Check duration limit
            if duration > 0 and (time.time() - start_time) >= duration:
                break
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()