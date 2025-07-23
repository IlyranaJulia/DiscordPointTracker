"""
WSGI entry point for production deployment
This file helps with certain deployment platforms that expect a wsgi.py
"""

import os
import sys
import threading

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from bot.py
from bot import app, bot, main as bot_main

def start_bot():
    """Start the Discord bot in a separate thread"""
    import asyncio
    try:
        # Create new event loop for the bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the bot
        async def run_bot():
            from config import Config
            if Config.BOT_TOKEN and Config.BOT_TOKEN != 'your_bot_token_here':
                await bot.start(Config.BOT_TOKEN)
        
        loop.run_until_complete(run_bot())
    except Exception as e:
        print(f"Bot startup error: {e}")

# Start Discord bot in background thread
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

# Export the Flask app for WSGI servers
application = app

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)