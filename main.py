#!/usr/bin/env python3
"""
Main entry point for Replit deployment
This file is automatically detected by Replit as the run command
Properly starts both Flask web server and Discord bot for deployment
"""

import os
import sys

def main():
    """Main entry point that properly starts both Flask web server and Discord bot"""
    try:
        # Ensure we have the required environment variables
        print(f"Starting application with PORT={os.getenv('PORT', '5000')}")
        print(f"BOT_TOKEN configured: {'Yes' if os.getenv('BOT_TOKEN') else 'No'}")
        
        # Import and run the main bot application
        from bot import main as bot_main
        bot_main()
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Discord bot: {e}")
        raise

if __name__ == "__main__":
    main()