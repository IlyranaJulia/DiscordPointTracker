import sqlite3
import aiosqlite
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class PointsDatabase:
    def __init__(self, db_path: str = "points.db"):
        self.db_path = db_path
        self.conn = None
        
    async def initialize(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            
            # Create points table
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS points (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            await self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_balance 
                ON points(balance DESC)
            ''')
            
            # Create trigger to update the updated_at timestamp
            await self.conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_points_timestamp 
                AFTER UPDATE ON points
                BEGIN
                    UPDATE points SET updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = NEW.user_id;
                END;
            ''')
            
            await self.conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
            
    async def get_points(self, user_id: int) -> int:
        """Get points balance for a user"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute(
                "SELECT balance FROM points WHERE user_id = ?", 
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting points for user {user_id}: {e}")
            return 0
            
    async def update_points(self, user_id: int, amount: int) -> bool:
        """Update points for a user (add or subtract)"""
        try:
            if not self.conn:
                await self.initialize()
                
            current_balance = await self.get_points(user_id)
            new_balance = current_balance + amount
            
            # Prevent negative balances
            if new_balance < 0:
                new_balance = 0
                
            if current_balance == 0 and amount > 0:
                # Insert new user
                await self.conn.execute(
                    "INSERT INTO points (user_id, balance) VALUES (?, ?)",
                    (user_id, new_balance)
                )
            else:
                # Update existing user
                await self.conn.execute(
                    "INSERT OR REPLACE INTO points (user_id, balance) VALUES (?, ?)",
                    (user_id, new_balance)
                )
                
            await self.conn.commit()
            logger.info(f"Updated points for user {user_id}: {current_balance} -> {new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating points for user {user_id}: {e}")
            return False
            
    async def set_points(self, user_id: int, amount: int) -> bool:
        """Set points for a user to a specific amount"""
        try:
            if not self.conn:
                await self.initialize()
                
            await self.conn.execute(
                "INSERT OR REPLACE INTO points (user_id, balance) VALUES (?, ?)",
                (user_id, amount)
            )
            
            await self.conn.commit()
            logger.info(f"Set points for user {user_id} to {amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting points for user {user_id}: {e}")
            return False
            
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Get top users by points"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute(
                "SELECT user_id, balance FROM points WHERE balance > 0 ORDER BY balance DESC LIMIT ?",
                (limit,)
            ) as cursor:
                results = await cursor.fetchall()
                return results
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
            
    async def get_total_users(self) -> int:
        """Get total number of users with points"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute(
                "SELECT COUNT(*) FROM points WHERE balance > 0"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0
            
    async def get_total_points(self) -> int:
        """Get sum of all points in the system"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute(
                "SELECT SUM(balance) FROM points"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 0
                
        except Exception as e:
            logger.error(f"Error getting total points: {e}")
            return 0
            
    async def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get a user's rank in the leaderboard"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute('''
                SELECT COUNT(*) + 1 as rank 
                FROM points 
                WHERE balance > (SELECT balance FROM points WHERE user_id = ?)
            ''', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error getting user rank for {user_id}: {e}")
            return None
            
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user's points record"""
        try:
            if not self.conn:
                await self.initialize()
                
            await self.conn.execute(
                "DELETE FROM points WHERE user_id = ?",
                (user_id,)
            )
            
            await self.conn.commit()
            logger.info(f"Deleted points record for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
            
    async def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            if not self.conn:
                await self.initialize()
                
            # Create backup connection
            backup_conn = await aiosqlite.connect(backup_path)
            
            # Copy database
            await self.conn.backup(backup_conn)
            await backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
            
    async def close(self):
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
