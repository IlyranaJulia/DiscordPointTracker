#!/usr/bin/env python3
"""
Simple Order Processor - No Email Required
Processes order files and creates Discord commands for manual point distribution
"""

import csv
import random
import string
import json
import os
from datetime import datetime
import aiosqlite

class SimpleOrderProcessor:
    def __init__(self):
        self.db_path = "points.db"
    
    async def process_order_file(self, file_path, points_per_order=100):
        """Process CSV file and create point distribution commands"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File {file_path} not found"}
            
            orders = []
            
            # Detect CSV delimiter
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                delimiter = ','
                if sample.count(';') > sample.count(','):
                    delimiter = ';'
                elif sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):
                    # Look for email and amount columns
                    email = None
                    order_amount = None
                    
                    for key, value in row.items():
                        key_lower = key.lower().strip()
                        if 'email' in key_lower or 'mail' in key_lower:
                            email = value.strip()
                        elif any(term in key_lower for term in ['amount', 'total', 'price', 'cost']):
                            try:
                                order_amount = float(str(value).replace('$', '').replace(',', '').strip())
                            except:
                                order_amount = None
                    
                    if email and '@' in email:
                        # Calculate points based on order amount if available
                        calculated_points = points_per_order
                        if order_amount and order_amount > 0:
                            # 1 point per dollar, minimum of points_per_order
                            calculated_points = max(int(order_amount), points_per_order)
                        
                        # Generate verification code
                        verification_code = self.generate_verification_code()
                        
                        orders.append({
                            'email': email,
                            'order_id': f"Order-{row_num-1}",
                            'order_amount': order_amount or 0,
                            'points': calculated_points,
                            'verification_code': verification_code,
                            'row': row_num
                        })
            
            if not orders:
                return {"success": False, "error": "No valid orders found in file"}
            
            # Save to database for manual processing
            await self.save_orders_to_db(orders)
            
            # Generate Discord commands file
            commands_file = await self.generate_discord_commands(orders)
            
            return {
                "success": True,
                "orders_found": len(orders),
                "orders": orders,
                "commands_file": commands_file,
                "message": f"Processed {len(orders)} orders successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_verification_code(self):
        """Generate unique verification code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    async def save_orders_to_db(self, orders):
        """Save orders to database for tracking"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create table if not exists
            await db.execute('''
                CREATE TABLE IF NOT EXISTS point_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    points_amount INTEGER NOT NULL,
                    verification_code TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    discord_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            ''')
            
            # Insert orders
            for order in orders:
                await db.execute('''
                    INSERT INTO point_requests 
                    (email, order_id, points_amount, verification_code, status)
                    VALUES (?, ?, ?, ?, 'pending')
                ''', (
                    order['email'],
                    order['order_id'],
                    order['points'],
                    order['verification_code']
                ))
            
            await db.commit()
    
    async def generate_discord_commands(self, orders):
        """Generate file with Discord commands for manual distribution"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"discord_commands_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Discord Point Distribution Commands\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Orders: {len(orders)}\n\n")
            
            f.write("OPTION 1: Manual Email + Discord Commands\n")
            f.write("-" * 40 + "\n")
            f.write("Send these emails to customers, then use the Discord commands:\n\n")
            
            for i, order in enumerate(orders, 1):
                f.write(f"Order {i}:\n")
                f.write(f"  Email to: {order['email']}\n")
                f.write(f"  Subject: Discord Points Available - {order['order_id']}\n")
                f.write(f"  Message: Your order qualifies for {order['points']} Discord points!\n")
                f.write(f"           Use this code in Discord: !claim {order['verification_code']}\n")
                f.write(f"  Discord Command: !claim {order['verification_code']}\n")
                f.write(f"  Points: {order['points']}\n\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("OPTION 2: Direct Discord Commands (if you know usernames)\n")
            f.write("-" * 50 + "\n")
            f.write("Use these if you know Discord usernames:\n\n")
            
            for i, order in enumerate(orders, 1):
                f.write(f"# Order {i}: {order['email']} - {order['points']} points\n")
                f.write(f"!silentadd @username {order['points']}\n\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("VERIFICATION CODES FOR REFERENCE:\n")
            f.write("-" * 30 + "\n")
            
            for order in orders:
                f.write(f"{order['verification_code']} -> {order['email']} ({order['points']} points)\n")
        
        return filename
    
    async def process_claim(self, verification_code, discord_user_id):
        """Process a claim using verification code"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Find the request
                cursor = await db.execute('''
                    SELECT email, order_id, points_amount, status 
                    FROM point_requests 
                    WHERE verification_code = ?
                ''', (verification_code,))
                
                request = await cursor.fetchone()
                
                if not request:
                    return {"success": False, "error": "Invalid verification code"}
                
                email, order_id, points_amount, status = request
                
                if status != 'pending':
                    return {"success": False, "error": "This code has already been used"}
                
                # Update the request as processed
                await db.execute('''
                    UPDATE point_requests 
                    SET status = 'completed', discord_user_id = ?, processed_at = CURRENT_TIMESTAMP
                    WHERE verification_code = ?
                ''', (discord_user_id, verification_code))
                
                # Add points to user
                await db.execute('''
                    INSERT OR IGNORE INTO points (user_id, balance) VALUES (?, 0)
                ''', (discord_user_id,))
                
                await db.execute('''
                    UPDATE points SET balance = balance + ? WHERE user_id = ?
                ''', (points_amount, discord_user_id))
                
                # Get new balance
                cursor = await db.execute('''
                    SELECT balance FROM points WHERE user_id = ?
                ''', (discord_user_id,))
                
                new_balance = await cursor.fetchone()
                new_balance = new_balance[0] if new_balance else points_amount
                
                await db.commit()
                
                return {
                    "success": True,
                    "message": f"Successfully claimed {points_amount} points for order {order_id}!",
                    "points_added": points_amount,
                    "new_balance": new_balance,
                    "order_id": order_id
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_pending_requests(self):
        """Get all pending point requests"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT email, order_id, points_amount, verification_code, created_at
                    FROM point_requests 
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                ''')
                
                requests = await cursor.fetchall()
                
                return [
                    {
                        "email": row[0],
                        "order_id": row[1],
                        "points": row[2],
                        "code": row[3],
                        "created": row[4]
                    }
                    for row in requests
                ]
                
        except Exception as e:
            return []