#!/usr/bin/env python3
"""
Production deployment entry point for Discord Points Bot
This file ensures 24/7 operation with keep-alive mechanisms
"""

import os
import sys
import logging
import threading
import time
import requests
from flask import Flask

# Setup logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Keep-alive web server
keep_alive_app = Flask('keep_alive')

@keep_alive_app.route('/')
def home():
    return "Discord Points Bot is running 24/7"

@keep_alive_app.route('/ping')
def ping():
    return "pong"

@keep_alive_app.route('/health')
def health():
    return {"status": "healthy", "service": "discord-bot", "uptime": True}

def run_keep_alive_server():
    """Run keep-alive server on port 8080"""
    try:
        keep_alive_app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"Keep-alive server error: {e}")

def start_keep_alive():
    """Start keep-alive server in background thread"""
    server_thread = threading.Thread(target=run_keep_alive_server, daemon=True)
    server_thread.start()
    logger.info("🔄 Keep-alive server started on port 8080")

def self_ping_loop():
    """Continuously ping self to prevent sleeping"""
    while True:
        try:
            time.sleep(250)  # Ping every 4+ minutes
            requests.get('http://localhost:8080/ping', timeout=5)
            logger.info("💓 Self-ping successful - bot staying alive")
        except Exception as e:
            logger.warning(f"Self-ping failed (expected): {e}")

def start_self_ping():
    """Start self-ping in background thread"""
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()
    logger.info("🕰️ Self-ping loop started")

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    logger.info("🚀 Starting Discord Points Bot PRODUCTION deployment...")
    logger.info("📂 Working directory: %s", os.getcwd())
    logger.info("🔧 Python path: %s", sys.path[0])
    
    # Start keep-alive mechanisms
    start_keep_alive()
    start_self_ping()
    
    try:
        # Import and run the main bot function
        from bot import main
        logger.info("✅ Bot module imported successfully")
        logger.info("🌐 Keep-alive systems active - bot will stay online 24/7")
        main()
    except ImportError as e:
        logger.error("❌ Failed to import bot module: %s", e)
        raise
    except Exception as e:
        logger.error("❌ Critical error starting bot: %s", e)
        raise