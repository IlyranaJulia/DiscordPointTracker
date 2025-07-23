#!/usr/bin/env python3
"""
Alternative entry point for Replit deployment
This file provides a simpler entry point that might work better with Replit's deployment system
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
if __name__ == "__main__":
    from bot import main
    main()