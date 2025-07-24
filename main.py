#!/usr/bin/env python3
"""
Main entry point for the Discord Points Bot
This file ensures proper deployment on Replit and other platforms
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
if __name__ == '__main__':
    from bot import main
    main()