#!/usr/bin/env python3
"""
Simple run script for deployment testing
"""

import os
from flask import Flask, jsonify
import threading
import asyncio

# Simple Flask app for testing deployment
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Discord Points Bot</h1>
    <p>Status: Running ✅</p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "discord-bot-simple",
        "message": "Service is running"
    })

def run_simple():
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    print("Starting simple Flask app for deployment test...")
    run_simple()