#!/usr/bin/env python3
"""
Deployment entry point for Discord Points Bot
This file is used by Replit deployment to start the bot and web server
"""

import os
import sys
import logging

# Setup logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    logger.info("🚀 Starting Discord Points Bot deployment...")
    logger.info("📂 Working directory: %s", os.getcwd())
    logger.info("🔧 Python path: %s", sys.path[0])
    
    try:
        # Import and run the main bot function
        from bot import main
        logger.info("✅ Bot module imported successfully")
        main()
    except ImportError as e:
        logger.error("❌ Failed to import bot module: %s", e)
        raise
    except Exception as e:
        logger.error("❌ Critical error starting bot: %s", e)
        raise