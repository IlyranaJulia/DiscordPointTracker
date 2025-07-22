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
            
            # Create transactions table for audit trail
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    admin_id INTEGER,
                    reason TEXT,
                    old_balance INTEGER NOT NULL,
                    new_balance INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES points (user_id)
                )
            ''')
            
            # Create achievements table
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_name TEXT NOT NULL,
                    points_earned INTEGER DEFAULT 0,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES points (user_id)
                )
            ''')
            
            # Create user_stats table
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_points_earned INTEGER DEFAULT 0,
                    total_points_spent INTEGER DEFAULT 0,
                    highest_balance INTEGER DEFAULT 0,
                    transactions_count INTEGER DEFAULT 0,
                    achievements_count INTEGER DEFAULT 0,
                    first_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES points (user_id)
                )
            ''')
            
            # Create indexes for faster queries
            await self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_balance 
                ON points(balance DESC)
            ''')
            
            await self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_user 
                ON transactions(user_id, created_at DESC)
            ''')
            
            await self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_achievements_user 
                ON achievements(user_id, earned_at DESC)
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
            
            # Create trigger to update user stats on points change
            await self.conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_stats_on_points
                AFTER UPDATE ON points
                BEGIN
                    INSERT OR REPLACE INTO user_stats (
                        user_id, total_points_earned, total_points_spent, 
                        highest_balance, transactions_count, last_activity,
                        first_activity
                    )
                    VALUES (
                        NEW.user_id,
                        COALESCE((SELECT total_points_earned FROM user_stats WHERE user_id = NEW.user_id), 0) +
                        CASE WHEN NEW.balance > OLD.balance THEN NEW.balance - OLD.balance ELSE 0 END,
                        COALESCE((SELECT total_points_spent FROM user_stats WHERE user_id = NEW.user_id), 0) +
                        CASE WHEN NEW.balance < OLD.balance THEN OLD.balance - NEW.balance ELSE 0 END,
                        MAX(NEW.balance, COALESCE((SELECT highest_balance FROM user_stats WHERE user_id = NEW.user_id), 0)),
                        COALESCE((SELECT transactions_count FROM user_stats WHERE user_id = NEW.user_id), 0) + 1,
                        CURRENT_TIMESTAMP,
                        COALESCE((SELECT first_activity FROM user_stats WHERE user_id = NEW.user_id), CURRENT_TIMESTAMP)
                    );
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
            
    async def update_points(self, user_id: int, amount: int, admin_id: int = None, reason: str = None) -> bool:
        """Update points for a user (add or subtract) with transaction logging"""
        try:
            if not self.conn:
                await self.initialize()
                
            current_balance = await self.get_points(user_id)
            new_balance = current_balance + amount
            
            # Prevent negative balances
            if new_balance < 0:
                new_balance = 0
                
            # Determine transaction type
            if amount > 0:
                transaction_type = "add"
            elif amount < 0:
                transaction_type = "remove"
            else:
                transaction_type = "no_change"
                
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
            
            # Log transaction
            await self.conn.execute('''
                INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, transaction_type, admin_id, reason, current_balance, new_balance))
                
            await self.conn.commit()
            logger.info(f"Updated points for user {user_id}: {current_balance} -> {new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating points for user {user_id}: {e}")
            return False
            
    async def set_points(self, user_id: int, amount: int, admin_id: int = None, reason: str = None) -> bool:
        """Set points for a user to a specific amount with transaction logging"""
        try:
            if not self.conn:
                await self.initialize()
                
            current_balance = await self.get_points(user_id)
            
            await self.conn.execute(
                "INSERT OR REPLACE INTO points (user_id, balance) VALUES (?, ?)",
                (user_id, amount)
            )
            
            # Log transaction
            await self.conn.execute('''
                INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount - current_balance, "set", admin_id, reason, current_balance, amount))
            
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
            
    async def get_transactions(self, user_id: int = None, limit: int = 50) -> List[Tuple]:
        """Get transaction history for a user or all users"""
        try:
            if not self.conn:
                await self.initialize()
            
            if user_id:
                query = '''
                    SELECT id, user_id, amount, transaction_type, admin_id, reason, 
                           old_balance, new_balance, created_at
                    FROM transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                '''
                params = (user_id, limit)
            else:
                query = '''
                    SELECT id, user_id, amount, transaction_type, admin_id, reason, 
                           old_balance, new_balance, created_at
                    FROM transactions 
                    ORDER BY created_at DESC 
                    LIMIT ?
                '''
                params = (limit,)
            
            async with self.conn.execute(query, params) as cursor:
                return await cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []

    async def get_user_stats(self, user_id: int) -> Optional[Tuple]:
        """Get detailed stats for a user"""
        try:
            if not self.conn:
                await self.initialize()
                
            async with self.conn.execute('''
                SELECT total_points_earned, total_points_spent, highest_balance, 
                       transactions_count, achievements_count, first_activity, last_activity
                FROM user_stats 
                WHERE user_id = ?
            ''', (user_id,)) as cursor:
                return await cursor.fetchone()
                
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return None

    async def add_achievement(self, user_id: int, achievement_type: str, achievement_name: str, points_earned: int = 0) -> bool:
        """Add an achievement for a user"""
        try:
            if not self.conn:
                await self.initialize()
                
            await self.conn.execute('''
                INSERT INTO achievements (user_id, achievement_type, achievement_name, points_earned)
                VALUES (?, ?, ?, ?)
            ''', (user_id, achievement_type, achievement_name, points_earned))
            
            # Update achievements count in user_stats
            await self.conn.execute('''
                INSERT OR REPLACE INTO user_stats (
                    user_id, achievements_count, last_activity,
                    total_points_earned, total_points_spent, highest_balance, 
                    transactions_count, first_activity
                )
                VALUES (
                    ?, 
                    COALESCE((SELECT achievements_count FROM user_stats WHERE user_id = ?), 0) + 1,
                    CURRENT_TIMESTAMP,
                    COALESCE((SELECT total_points_earned FROM user_stats WHERE user_id = ?), 0),
                    COALESCE((SELECT total_points_spent FROM user_stats WHERE user_id = ?), 0),
                    COALESCE((SELECT highest_balance FROM user_stats WHERE user_id = ?), 0),
                    COALESCE((SELECT transactions_count FROM user_stats WHERE user_id = ?), 0),
                    COALESCE((SELECT first_activity FROM user_stats WHERE user_id = ?), CURRENT_TIMESTAMP)
                )
            ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
            
            await self.conn.commit()
            logger.info(f"Added achievement '{achievement_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding achievement for user {user_id}: {e}")
            return False

    async def get_achievements(self, user_id: int = None, limit: int = 50) -> List[Tuple]:
        """Get achievements for a user or all users"""
        try:
            if not self.conn:
                await self.initialize()
            
            if user_id:
                query = '''
                    SELECT id, user_id, achievement_type, achievement_name, 
                           points_earned, earned_at
                    FROM achievements 
                    WHERE user_id = ? 
                    ORDER BY earned_at DESC 
                    LIMIT ?
                '''
                params = (user_id, limit)
            else:
                query = '''
                    SELECT id, user_id, achievement_type, achievement_name, 
                           points_earned, earned_at
                    FROM achievements 
                    ORDER BY earned_at DESC 
                    LIMIT ?
                '''
                params = (limit,)
            
            async with self.conn.execute(query, params) as cursor:
                return await cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting achievements: {e}")
            return []

    async def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        try:
            if not self.conn:
                await self.initialize()
            
            stats = {}
            
            # Total users
            async with self.conn.execute("SELECT COUNT(*) FROM points") as cursor:
                result = await cursor.fetchone()
                stats['total_users'] = result[0] if result else 0
            
            # Total transactions
            async with self.conn.execute("SELECT COUNT(*) FROM transactions") as cursor:
                result = await cursor.fetchone()
                stats['total_transactions'] = result[0] if result else 0
            
            # Total achievements
            async with self.conn.execute("SELECT COUNT(*) FROM achievements") as cursor:
                result = await cursor.fetchone()
                stats['total_achievements'] = result[0] if result else 0
            
            # Total points in circulation
            async with self.conn.execute("SELECT SUM(balance) FROM points") as cursor:
                result = await cursor.fetchone()
                stats['total_points'] = result[0] if result and result[0] else 0
            
            # Most active user
            async with self.conn.execute('''
                SELECT user_id, transactions_count 
                FROM user_stats 
                ORDER BY transactions_count DESC 
                LIMIT 1
            ''') as cursor:
                result = await cursor.fetchone()
                if result:
                    stats['most_active_user'] = {'user_id': result[0], 'transactions': result[1]}
                else:
                    stats['most_active_user'] = None
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    async def close(self):
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
