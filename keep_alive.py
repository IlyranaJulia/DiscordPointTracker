#!/usr/bin/env python3
"""
Keep-alive server to prevent Replit from sleeping
This creates a simple HTTP server that responds to pings
"""

from flask import Flask
import threading
import time
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app for keep-alive
keep_alive_app = Flask('keep_alive')

@keep_alive_app.route('/')
def home():
    return "Bot is alive!"

@keep_alive_app.route('/ping')
def ping():
    return "pong"

@keep_alive_app.route('/status')
def status():
    return {"status": "alive", "timestamp": time.time()}

def run_keep_alive():
    """Run the keep-alive server on a different port"""
    try:
        port = int(os.environ.get('KEEP_ALIVE_PORT', 8080))
        keep_alive_app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Keep-alive server error: {e}")

def start_keep_alive():
    """Start the keep-alive server in a separate thread"""
    server_thread = threading.Thread(target=run_keep_alive, daemon=True)
    server_thread.start()
    logger.info("Keep-alive server started")

def self_ping():
    """Ping self every 5 minutes to stay alive"""
    while True:
        try:
            time.sleep(300)  # Wait 5 minutes
            port = int(os.environ.get('KEEP_ALIVE_PORT', 8080))
            requests.get(f'http://localhost:{port}/ping', timeout=10)
            logger.info("Self-ping successful")
        except Exception as e:
            logger.warning(f"Self-ping failed: {e}")

def start_self_ping():
    """Start self-pinging in a separate thread"""
    ping_thread = threading.Thread(target=self_ping, daemon=True)
    ping_thread.start()
    logger.info("Self-ping started")

if __name__ == '__main__':
    start_keep_alive()
    start_self_ping()
    # Keep the main thread alive
    while True:
        time.sleep(1)