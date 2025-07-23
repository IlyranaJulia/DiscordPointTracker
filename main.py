#!/usr/bin/env python3
"""
Main entry point for Replit deployment
This file is automatically detected by Replit as the run command
Properly starts both Flask web server and Discord bot for deployment
"""

def main():
    """Main entry point that properly starts both Flask web server and Discord bot"""
    try:
        from bot import main as bot_main
        bot_main()
    except Exception as e:
        print(f"Error starting Discord bot: {e}")
        raise

if __name__ == "__main__":
    main()