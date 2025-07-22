import csv
import os
import logging
from typing import Dict, List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from database import PointsDatabase

logger = logging.getLogger(__name__)

class OrderProcessor:
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not self.sendgrid_key:
            logger.warning("SENDGRID_API_KEY not found. Email functionality will be disabled.")
        
        self.db = PointsDatabase()
        
    async def process_order_file(self, file_path: str, points_per_order: int = 100) -> Dict[str, any]:
        """Process a CSV order file and prepare point distribution"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            
            orders = []
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect the CSV format
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                # Common delimiters
                delimiter = ','
                if ';' in sample and sample.count(';') > sample.count(','):
                    delimiter = ';'
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):
                    # Look for email columns (case insensitive)
                    email = None
                    order_id = None
                    
                    for key, value in row.items():
                        key_lower = key.lower().strip()
                        if 'email' in key_lower or 'mail' in key_lower:
                            email = value.strip()
                        elif 'order' in key_lower or 'id' in key_lower:
                            order_id = value.strip()
                    
                    if email and '@' in email:
                        orders.append({
                            'email': email,
                            'order_id': order_id or f"Order-{row_num}",
                            'points': points_per_order,
                            'row': row_num
                        })
                    else:
                        logger.warning(f"Row {row_num}: No valid email found")
            
            return {
                "success": True,
                "orders_found": len(orders),
                "orders": orders,
                "message": f"Found {len(orders)} valid orders with email addresses"
            }
            
        except Exception as e:
            logger.error(f"Error processing order file: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_point_requests(self, orders: List[Dict], server_name: str = "Discord Server") -> Dict[str, any]:
        """Create point request records and send notification emails"""
        try:
            if not self.sendgrid_key:
                return {"success": False, "error": "SendGrid API key not configured"}
            
            # Initialize database
            await self.db.initialize()
            
            # Create point_requests table if it doesn't exist
            await self.db.conn.execute('''
                CREATE TABLE IF NOT EXISTS point_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    points_amount INTEGER NOT NULL,
                    discord_user_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    verification_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    UNIQUE(email, order_id)
                )
            ''')
            
            successful_emails = 0
            failed_emails = 0
            
            for order in orders:
                try:
                    # Generate verification code
                    import secrets
                    verification_code = secrets.token_urlsafe(8)
                    
                    # Insert request into database
                    await self.db.conn.execute('''
                        INSERT OR REPLACE INTO point_requests 
                        (email, order_id, points_amount, verification_code)
                        VALUES (?, ?, ?, ?)
                    ''', (order['email'], order['order_id'], order['points'], verification_code))
                    
                    # Send email notification
                    if await self.send_point_notification(
                        order['email'], 
                        order['order_id'], 
                        order['points'], 
                        verification_code,
                        server_name
                    ):
                        successful_emails += 1
                    else:
                        failed_emails += 1
                        
                except Exception as e:
                    logger.error(f"Error processing order {order['order_id']}: {e}")
                    failed_emails += 1
            
            await self.db.conn.commit()
            await self.db.close()
            
            return {
                "success": True,
                "emails_sent": successful_emails,
                "emails_failed": failed_emails,
                "message": f"Sent {successful_emails} notifications, {failed_emails} failed"
            }
            
        except Exception as e:
            logger.error(f"Error creating point requests: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_point_notification(self, email: str, order_id: str, points: int, verification_code: str, server_name: str) -> bool:
        """Send email notification about available points"""
        try:
            sg = SendGridAPIClient(self.sendgrid_key)
            
            # Email content
            subject = f"Discord Points Available - Order {order_id}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #5865F2;">Discord Points Available!</h2>
                
                <p>Hello!</p>
                
                <p>Your order <strong>{order_id}</strong> qualifies for <strong>{points} Discord points</strong> in our {server_name}!</p>
                
                <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>How to claim your points:</h3>
                    <ol>
                        <li>Join our Discord server if you haven't already</li>
                        <li>Use this command in any channel:</li>
                        <code style="background: #2f3136; color: #ffffff; padding: 10px; display: block; border-radius: 4px; margin: 10px 0;">
                            !claim {verification_code}
                        </code>
                        <li>Your {points} points will be added automatically!</li>
                    </ol>
                </div>
                
                <p><strong>Verification Code:</strong> <code>{verification_code}</code></p>
                
                <p style="color: #666; font-size: 14px;">
                    This code is unique to your order and can only be used once.
                    If you have any questions, please contact our support team.
                </p>
                
                <hr style="margin: 30px 0;">
                <p style="color: #888; font-size: 12px;">
                    This email was sent because your order qualifies for Discord points.
                    If you believe this was sent in error, please ignore this message.
                </p>
            </div>
            """
            
            text_content = f"""
            Discord Points Available!
            
            Your order {order_id} qualifies for {points} Discord points in our {server_name}!
            
            To claim your points:
            1. Join our Discord server
            2. Use the command: !claim {verification_code}
            3. Your {points} points will be added automatically!
            
            Verification Code: {verification_code}
            
            This code is unique to your order and can only be used once.
            """
            
            message = Mail(
                from_email=Email("noreply@yourdomain.com"),  # Replace with your verified sender
                to_emails=To(email),
                subject=subject
            )
            
            message.content = [
                Content("text/plain", text_content),
                Content("text/html", html_content)
            ]
            
            response = sg.send(message)
            logger.info(f"Email sent to {email} for order {order_id}, status: {response.status_code}")
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return False
    
    async def process_claim(self, verification_code: str, discord_user_id: int) -> Dict[str, any]:
        """Process a point claim using verification code"""
        try:
            await self.db.initialize()
            
            # Find pending request
            async with self.db.conn.execute('''
                SELECT email, order_id, points_amount, status 
                FROM point_requests 
                WHERE verification_code = ? AND status = 'pending'
            ''', (verification_code,)) as cursor:
                request = await cursor.fetchone()
            
            if not request:
                return {"success": False, "error": "Invalid or already used verification code"}
            
            email, order_id, points_amount, status = request
            
            # Update request status and assign user
            await self.db.conn.execute('''
                UPDATE point_requests 
                SET status = 'completed', discord_user_id = ?, processed_at = CURRENT_TIMESTAMP
                WHERE verification_code = ?
            ''', (discord_user_id, verification_code))
            
            # Add points to user
            success = await self.db.update_points(
                discord_user_id, 
                points_amount, 
                0,  # System admin ID
                f"Order reward: {order_id}"
            )
            
            if success:
                await self.db.conn.commit()
                new_balance = await self.db.get_points(discord_user_id)
                
                return {
                    "success": True,
                    "points_added": points_amount,
                    "new_balance": new_balance,
                    "order_id": order_id,
                    "message": f"Successfully claimed {points_amount} points for order {order_id}!"
                }
            else:
                return {"success": False, "error": "Failed to add points to account"}
            
        except Exception as e:
            logger.error(f"Error processing claim {verification_code}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self.db.close()
    
    async def get_pending_requests(self, limit: int = 50) -> List[Dict]:
        """Get list of pending point requests"""
        try:
            await self.db.initialize()
            
            async with self.db.conn.execute('''
                SELECT email, order_id, points_amount, verification_code, created_at
                FROM point_requests 
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,)) as cursor:
                requests = await cursor.fetchall()
            
            return [
                {
                    "email": req[0],
                    "order_id": req[1],
                    "points_amount": req[2],
                    "verification_code": req[3],
                    "created_at": req[4]
                }
                for req in requests
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
        finally:
            await self.db.close()