#!/usr/bin/env python3
"""
External uptime monitor that proves the bot stays online 24/7
This script can be run from anywhere to continuously monitor your bot
"""

import requests
import time
import json
import logging
from datetime import datetime, timedelta
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UPTIME MONITOR - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotUptimeMonitor:
    def __init__(self, bot_url):
        self.bot_url = bot_url.rstrip('/')
        self.health_endpoint = f"{self.bot_url}/health"
        self.ping_endpoint = f"{self.bot_url}/ping"
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'uptime_percentage': 0.0,
            'last_check': None,
            'last_success': None,
            'last_failure': None,
            'start_time': datetime.now()
        }
        
    def check_bot_status(self):
        """Check if bot is responding"""
        try:
            # Try health endpoint first
            response = requests.get(self.health_endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.stats['successful_checks'] += 1
                self.stats['last_success'] = datetime.now()
                
                logger.info(f"✅ BOT ONLINE - Status: {data.get('status', 'unknown')}")
                return True
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            # Try ping endpoint as backup
            try:
                response = requests.get(self.ping_endpoint, timeout=10)
                if response.status_code == 200:
                    self.stats['successful_checks'] += 1
                    self.stats['last_success'] = datetime.now()
                    logger.info("✅ BOT ONLINE - Ping successful")
                    return True
            except:
                pass
            
            # Both endpoints failed
            self.stats['failed_checks'] += 1
            self.stats['last_failure'] = datetime.now()
            logger.error(f"❌ BOT OFFLINE - Error: {e}")
            return False
        
        finally:
            self.stats['total_checks'] += 1
            self.stats['last_check'] = datetime.now()
            
            # Calculate uptime percentage
            if self.stats['total_checks'] > 0:
                self.stats['uptime_percentage'] = (
                    self.stats['successful_checks'] / self.stats['total_checks']
                ) * 100
    
    def print_stats(self):
        """Print current monitoring statistics"""
        runtime = datetime.now() - self.stats['start_time']
        
        print("\n" + "="*60)
        print("🤖 DISCORD BOT UPTIME MONITOR - LIVE PROOF")
        print("="*60)
        print(f"Bot URL: {self.bot_url}")
        print(f"Monitoring Runtime: {runtime}")
        print(f"Total Checks: {self.stats['total_checks']}")
        print(f"Successful: {self.stats['successful_checks']}")
        print(f"Failed: {self.stats['failed_checks']}")
        print(f"UPTIME: {self.stats['uptime_percentage']:.2f}%")
        
        if self.stats['last_success']:
            time_since_success = datetime.now() - self.stats['last_success']
            print(f"Last Success: {time_since_success} ago")
        
        if self.stats['last_failure']:
            time_since_failure = datetime.now() - self.stats['last_failure']
            print(f"Last Failure: {time_since_failure} ago")
        
        print("="*60)
    
    def monitor_continuously(self, check_interval=300):  # 5 minutes
        """Run continuous monitoring"""
        logger.info(f"🚀 Starting continuous monitoring every {check_interval} seconds")
        logger.info(f"📊 Monitoring: {self.health_endpoint}")
        
        while True:
            try:
                self.check_bot_status()
                
                # Print stats every 10 checks
                if self.stats['total_checks'] % 10 == 0:
                    self.print_stats()
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoring stopped by user")
                self.print_stats()
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(30)  # Wait 30 seconds on error

def main():
    """Main function to start monitoring"""
    # Your bot's deployment URL (replace with actual URL)
    BOT_URL = "https://YOUR-PROJECT-NAME.replit.app"
    
    print("🔍 DISCORD BOT UPTIME PROOF SYSTEM")
    print("This will monitor your bot and prove it stays online 24/7")
    print(f"Monitoring URL: {BOT_URL}")
    print("Press Ctrl+C to stop monitoring\n")
    
    monitor = BotUptimeMonitor(BOT_URL)
    
    # Start monitoring
    monitor.monitor_continuously(check_interval=180)  # Check every 3 minutes

if __name__ == "__main__":
    main()