#!/usr/bin/env python3
"""
Alternative main entry point that ensures bot stays online 24/7
This version uses a simpler approach with better keep-alive mechanisms
"""

import os
import sys
import time
import threading
import requests
import logging
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "discord-points-bot",
        "message": "Bot is running 24/7",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": True})

@app.route('/ping')
def ping():
    return "pong"

def run_web_server():
    """Run Flask web server for keep-alive"""
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Web server error: {e}")

def keep_alive_worker():
    """Worker thread to keep the deployment active"""
    while True:
        try:
            # Wait 4 minutes between pings
            time.sleep(240)
            
            # Try to ping our own health endpoint
            port = int(os.environ.get('PORT', 5000))
            url = f'http://localhost:{port}/health'
            
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                logger.info("Keep-alive ping successful")
            else:
                logger.warning(f"Keep-alive ping returned status: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
            # Continue the loop even if ping fails

def start_discord_bot():
    """Start the Discord bot in a separate thread"""
    try:
        from bot import main as bot_main
        logger.info("Starting Discord bot...")
        bot_main()
    except Exception as e:
        logger.error(f"Discord bot error: {e}")
        raise

if __name__ == '__main__':
    logger.info("Starting Discord Points Bot with improved keep-alive...")
    
    # Start keep-alive worker in background
    keep_alive_thread = threading.Thread(target=keep_alive_worker, daemon=True)
    keep_alive_thread.start()
    logger.info("Keep-alive worker started")
    
    # Start Discord bot in background
    bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()
    logger.info("Discord bot thread started")
    
    # Run web server on main thread (keeps the process alive)
    logger.info("Starting web server for deployment health checks...")
    run_web_server()