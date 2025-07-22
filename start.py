#!/usr/bin/env python3
"""
Discord Bot Startup Script
This script ensures proper environment setup and starts the Discord bot with Flask web server.
"""
import os
import sys
import subprocess

def main():
    """Main startup function with environment validation"""
    print("Starting Discord Points Bot...")
    
    # Check for required environment variables
    required_vars = ['BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == 'your_bot_token_here':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your deployment environment.")
        return 1
    
    # Set default SESSION_SECRET if not provided
    if not os.getenv('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'default_session_secret_change_in_production'
        print("WARNING: Using default SESSION_SECRET. Set a secure secret for production.")
    
    # Start the main bot application
    try:
        import bot
        print("Bot application imported successfully.")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to start bot: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())