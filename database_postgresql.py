import asyncpg
import logging
import os
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class PostgreSQLPointsDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.pool = None
        
    async def initialize(self):
        """Initialize the PostgreSQL database connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=20)
            
            async with self.pool.acquire() as conn:
                # Create points table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS points (
                        user_id TEXT PRIMARY KEY,
                        balance INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create transactions table for audit trail
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        transaction_type TEXT NOT NULL,
                        admin_id INTEGER,
                        reason TEXT,
                        old_balance INTEGER NOT NULL,
                        new_balance INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create achievements table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS achievements (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        achievement_type TEXT NOT NULL,
                        achievement_name TEXT NOT NULL,
                        points_earned INTEGER DEFAULT 0,
                        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_stats table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id TEXT PRIMARY KEY,
                        total_points_earned INTEGER DEFAULT 0,
                        total_points_spent INTEGER DEFAULT 0,
                        highest_balance INTEGER DEFAULT 0,
                        transactions_count INTEGER DEFAULT 0,
                        achievements_count INTEGER DEFAULT 0,
                        first_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create email_submissions table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS email_submissions (
                        id SERIAL PRIMARY KEY,
                        discord_user_id TEXT NOT NULL,
                        discord_username TEXT NOT NULL,
                        email_address TEXT NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        processed_at TIMESTAMP,
                        admin_notes TEXT
                    )
                ''')
                
                # Create indexes for better performance
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_points_balance ON points(balance DESC)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_email_user ON email_submissions(discord_user_id)')
                
            logger.info("PostgreSQL database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def get_points(self, user_id) -> int:
        """Get points for a user"""
        try:
            # Ensure user_id is string for TEXT field
            user_id_str = str(user_id)
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT balance FROM points WHERE user_id = $1', user_id_str)
                return result if result is not None else 0
        except Exception as e:
            logger.error(f"Error getting points for user {user_id}: {e}")
            return 0
    
    async def update_points(self, user_id, amount: int, admin_id: int = None, reason: str = None) -> bool:
        """Update points for a user with transaction logging"""
        try:
            user_id_str = str(user_id)
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Get current balance
                    current_balance = await conn.fetchval('SELECT balance FROM points WHERE user_id = $1', user_id_str)
                    if current_balance is None:
                        current_balance = 0
                        # Insert new user
                        await conn.execute('''
                            INSERT INTO points (user_id, balance, created_at, updated_at) 
                            VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', user_id, amount)
                        
                        # Insert user stats
                        await conn.execute('''
                            INSERT INTO user_stats (user_id, total_points_earned, transactions_count, first_activity, last_activity)
                            VALUES ($1, $2, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', user_id, max(0, amount))
                    else:
                        new_balance = current_balance + amount
                        # Update existing user
                        await conn.execute('''
                            UPDATE points 
                            SET balance = $1, updated_at = CURRENT_TIMESTAMP 
                            WHERE user_id = $2
                        ''', new_balance, user_id)
                        
                        # Update user stats
                        points_earned = max(0, amount) if amount > 0 else 0
                        await conn.execute('''
                            UPDATE user_stats 
                            SET total_points_earned = total_points_earned + $1,
                                transactions_count = transactions_count + 1,
                                last_activity = CURRENT_TIMESTAMP,
                                highest_balance = GREATEST(highest_balance, $2)
                            WHERE user_id = $3
                        ''', points_earned, current_balance + amount, user_id)
                    
                    # Log transaction
                    transaction_type = "add" if amount > 0 else "remove"
                    await conn.execute('''
                        INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''', user_id, amount, transaction_type, admin_id, reason, current_balance, current_balance + amount)
                    
            return True
        except Exception as e:
            logger.error(f"Error updating points for user {user_id}: {e}")
            return False

    async def set_points(self, user_id, amount: int, admin_id: int = None, reason: str = None) -> bool:
        """Set points for a user to a specific amount"""
        try:
            user_id_str = str(user_id)
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Get current balance
                    current_balance = await conn.fetchval('SELECT balance FROM points WHERE user_id = $1', user_id_str)
                    if current_balance is None:
                        current_balance = 0
                        # Insert new user with specified points
                        await conn.execute('''
                            INSERT INTO points (user_id, balance, created_at, updated_at) 
                            VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', user_id_str, amount)
                        
                        # Insert user stats
                        await conn.execute('''
                            INSERT INTO user_stats (user_id, total_points_earned, transactions_count, first_activity, last_activity)
                            VALUES ($1, $2, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', user_id_str, max(0, amount))
                        transaction_amount = amount
                    else:
                        # Update existing user to specific amount
                        await conn.execute('''
                            UPDATE points 
                            SET balance = $1, updated_at = CURRENT_TIMESTAMP 
                            WHERE user_id = $2
                        ''', amount, user_id_str)
                        
                        # Update user stats
                        transaction_amount = amount - current_balance
                        points_earned = max(0, transaction_amount) if transaction_amount > 0 else 0
                        await conn.execute('''
                            UPDATE user_stats 
                            SET total_points_earned = total_points_earned + $1,
                                transactions_count = transactions_count + 1,
                                last_activity = CURRENT_TIMESTAMP,
                                highest_balance = GREATEST(highest_balance, $2)
                            WHERE user_id = $3
                        ''', points_earned, amount, user_id_str)
                    
                    # Log transaction  
                    transaction_type = "set"
                    await conn.execute('''
                        INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''', user_id_str, transaction_amount, transaction_type, admin_id, reason or "Points set", current_balance, amount)
                    
            return True
        except Exception as e:
            logger.error(f"Error setting points for user {user_id}: {e}")
            return False
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Get top users by points"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('SELECT user_id, balance FROM points WHERE balance > 0 ORDER BY balance DESC LIMIT $1', limit)
                return [(row['user_id'], row['balance']) for row in rows]
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def get_transactions(self, user_id: int = None, limit: int = 10) -> List[Tuple]:
        """Get transaction history"""
        try:
            async with self.pool.acquire() as conn:
                if user_id:
                    rows = await conn.fetch('''
                        SELECT id, user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance, created_at
                        FROM transactions WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
                    ''', user_id, limit)
                else:
                    rows = await conn.fetch('''
                        SELECT id, user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance, created_at
                        FROM transactions ORDER BY created_at DESC LIMIT $1
                    ''', limit)
                return [tuple(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
    
    async def add_achievement(self, user_id: int, achievement_type: str, achievement_name: str, points_earned: int = 0) -> bool:
        """Add an achievement for a user"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Add achievement
                    await conn.execute('''
                        INSERT INTO achievements (user_id, achievement_type, achievement_name, points_earned)
                        VALUES ($1, $2, $3, $4)
                    ''', user_id, achievement_type, achievement_name, points_earned)
                    
                    # Update user stats
                    await conn.execute('''
                        UPDATE user_stats 
                        SET achievements_count = achievements_count + 1,
                            last_activity = CURRENT_TIMESTAMP
                        WHERE user_id = $1
                    ''', user_id)
                    
            return True
        except Exception as e:
            logger.error(f"Error adding achievement for user {user_id}: {e}")
            return False
    
    async def get_user_analytics(self, user_id: int) -> Optional[Tuple]:
        """Get comprehensive analytics for a user"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    SELECT total_points_earned, total_points_spent, highest_balance,
                           transactions_count, achievements_count, first_activity, last_activity
                    FROM user_stats WHERE user_id = $1
                ''', user_id)
                return tuple(result) if result else None
        except Exception as e:
            logger.error(f"Error getting user analytics for {user_id}: {e}")
            return None
    
    async def get_email_submissions(self):
        """Get all email submissions"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT id, discord_user_id, discord_username, email_address, 
                           submitted_at, status, processed_at, admin_notes, server_roles
                    FROM email_submissions 
                    ORDER BY submitted_at DESC
                ''')
                return [tuple(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting email submissions: {e}")
            return []
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results (for SELECT) or status (for non-SELECT)"""
        try:
            async with self.pool.acquire() as conn:
                query_lower = query.strip().lower()
                if query_lower.startswith('select'):
                    # For SELECT queries, return results
                    result = await conn.fetch(query, *args)
                    return [tuple(row) for row in result]
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE), return status
                    result = await conn.execute(query, *args)
                    return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            if query.strip().lower().startswith('select'):
                return []
            else:
                return None
    
    async def get_total_users(self) -> int:
        """Get total number of users"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT COUNT(*) FROM points')
                return result if result else 0
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0
    
    async def get_total_points(self) -> int:
        """Get total points across all users"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT SUM(balance) FROM points')
                return result if result else 0
        except Exception as e:
            logger.error(f"Error getting total points: {e}")
            return 0
    
    async def get_database_stats(self) -> dict:
        """Get comprehensive database statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Get table row counts
                points_count = await conn.fetchval('SELECT COUNT(*) FROM points')
                transactions_count = await conn.fetchval('SELECT COUNT(*) FROM transactions')
                achievements_count = await conn.fetchval('SELECT COUNT(*) FROM achievements')
                
                # Get total points
                total_points = await conn.fetchval('SELECT SUM(balance) FROM points')
                
                return {
                    'tables': {
                        'points': {'rows': points_count or 0},
                        'transactions': {'rows': transactions_count or 0},
                        'achievements': {'rows': achievements_count or 0}
                    },
                    'total_points': total_points or 0
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                'tables': {
                    'points': {'rows': 0},
                    'transactions': {'rows': 0},
                    'achievements': {'rows': 0}
                },
                'total_points': 0
            }
    
    async def get_achievements(self, limit: int = 10) -> List[Tuple]:
        """Get recent achievements"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT user_id, achievement_type, achievement_name, points_earned, earned_at
                    FROM achievements 
                    ORDER BY earned_at DESC 
                    LIMIT $1
                ''', limit)
                return [tuple(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting achievements: {e}")
            return []
    
    async def close(self):
        """Close the database connection"""
        if self.pool:
            await self.pool.close()
            self.pool = None