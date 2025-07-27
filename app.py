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
    return {
        "status": "healthy", 
        "service": "discord-bot", 
        "uptime": True,
        "timestamp": time.time(),
        "message": "Bot deployment is active"
    }

@keep_alive_app.route('/keepalive')
def keepalive():
    """Special endpoint for external monitoring services"""
    return {"alive": True, "timestamp": time.time()}

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

def external_ping_sources():
    """List of external ping services that can help keep deployment alive"""
    return [
        "https://uptime.betterstack.com/api/v1/heartbeat/",  # Better Stack
        "https://hc-ping.com/",  # Healthchecks.io style
        "https://cronitor.io/ping/",  # Cronitor style
    ]

def self_ping_loop():
    """Continuously ping self and register with external services to prevent sleeping"""
    logger.info("🚀 Starting enhanced keep-alive system...")
    
    while True:
        try:
            time.sleep(180)  # Ping every 3 minutes for better reliability
            
            # Self-ping our own endpoints
            success = False
            endpoints = ['http://localhost:5000/', 'http://localhost:8080/ping']
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=8)
                    if response.status_code == 200:
                        logger.info(f"💓 Self-ping successful: {endpoint}")
                        success = True
                        break
                except Exception as e:
                    logger.warning(f"Self-ping failed for {endpoint}: {e}")
                    continue
            
            if not success:
                logger.warning("❌ All self-ping attempts failed")
            
            # Additional technique: Make a simple HTTP request to a reliable external service
            # This creates network activity that helps prevent sleeping
            try:
                requests.get('https://httpbin.org/uuid', timeout=5)
                logger.debug("External network activity completed")
            except:
                pass  # Ignore external request failures
                
        except Exception as e:
            logger.error(f"Critical keep-alive error: {e}")
            time.sleep(30)  # Shorter retry on critical error

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