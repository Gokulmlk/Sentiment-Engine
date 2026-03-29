"""
REST API routes for the sentiment engine
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Any

from ..core.engine import FearGreedEngine
from ..utils.exceptions import SentimentEngineError

def create_app(engine: FearGreedEngine) -> Flask:
    """Create Flask application with routes"""
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy' if engine.running else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/v1/market/summary', methods=['GET'])
    def get_market_summary():
        """Get market sentiment summary"""
        try:
            summary = engine.get_market_summary()
            return jsonify(summary.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/market/assets/<asset>', methods=['GET'])
    def get_asset_analysis(asset: str):
        """Get analysis for specific asset"""
        try:
            analysis = engine.get_asset_analysis(asset)
            return jsonify(analysis.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/signals/recent', methods=['GET'])
    def get_recent_signals():
        """Get recent trading signals"""
        try:
            count = request.args.get('count', 10, type=int)
            signals = engine.signal_generator.get_recent_signals(count)
            return jsonify([signal.to_dict() for signal in signals])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/signals/analytics', methods=['GET'])
    def get_signal_analytics():
        """Get signal performance analytics"""
        try:
            analytics = engine.get_signal_analytics()
            return jsonify(analytics)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/fear-greed', methods=['GET'])
    def get_fear_greed_breakdown():
        """Get detailed fear/greed analysis"""
        try:
            breakdown = engine.get_fear_greed_breakdown()
            return jsonify(breakdown)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/sentiment/analyze', methods=['POST'])
    def analyze_text():
        """Analyze sentiment of provided text"""
        try:
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({'error': 'Text field required'}), 400
            
            result = engine.sentiment_analyzer.get_sentiment_breakdown(data['text'])
            result['analysis_timestamp'] = datetime.now().isoformat()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/export', methods=['GET'])
    def export_data():
        """Export recent data"""
        try:
            hours = request.args.get('hours', 1, type=int)
            export_data = engine.export_data(hours)
            return jsonify(export_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app