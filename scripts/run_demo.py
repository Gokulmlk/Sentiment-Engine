#!/usr/bin/env python3
"""
Demo script for the Fear & Greed Sentiment Engine - DEBUG VERSION
"""

print("🚀 Script started...")
print("📁 Working directory:", os.getcwd() if 'os' in globals() else "Unknown")

import sys
import time
import os
from pathlib import Path

print("📦 Imports successful...")

# Add parent directory to path to import sentiment_engine
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"📂 Project root: {project_root}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
    print(f"🔧 USE_MOCK_DATA: {os.getenv('USE_MOCK_DATA')}")
except ImportError:
    print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading .env: {e}")

# Rest of your script...
def create_demo_settings():
    print("⚙️ Creating demo settings...")
    # ... rest of function