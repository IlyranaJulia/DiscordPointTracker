#!/usr/bin/env python3
"""
Enhanced Achievements System for Discord Points Bot
"""

import asyncio
from database_postgresql import PostgreSQLPointsDatabase
from datetime import datetime

# Define achievement types and their rewards
ACHIEVEMENT_TYPES = {
    'first_points': {
        'name': 'First Points Earned',
        'description': 'Earned your first points!',
        'points_reward': 50,
        'emoji': '🎉'
    },
    'milestone_100': {
        'name': '100 Points Milestone',
        'description': 'Reached 100 total points!',
        'points_reward': 25,
        'emoji': '💯'
    },
    'milestone_500': {
        'name': '500 Points Milestone', 
        'description': 'Reached 500 total points!',
        'points_reward': 75,
        'emoji': '🌟'
    },
    'milestone_1000': {
        'name': '1000 Points Milestone',
        'description': 'Reached 1000 total points!',
        'points_reward': 150,
        'emoji': '💎'
    },
    'high_roller': {
        'name': 'High Roller',
        'description': 'Accumulated over 2000 points!',
        'points_reward': 300,
        'emoji': '🎰'
    },
    'email_verified': {
        'name': 'Email Verified',
        'description': 'Successfully submitted and verified email!',
        'points_reward': 100,
        'emoji': '📧'
    },
    'early_adopter': {
        'name': 'Early Adopter',
        'description': 'One of the first 10 users to join!',
        'points_reward': 200,
        'emoji': '🚀'
    },
    'community_member': {
        'name': 'Community Member',
        'description': 'Active member with VIP role!',
        'points_reward': 150,
        'emoji': '👑'
    }
}

async def check_and_award_achievements(db, user_id: str, current_balance: int = None):
    """Check if user has earned any new achievements and award them"""
    
    if current_balance is None:
        current_balance = await db.get_points(user_id)
    
    # Get user's existing achievements
    async with db.pool.acquire() as conn:
        existing_achievements = await conn.fetch(
            "SELECT achievement_type FROM achievements WHERE user_id = $1",
            user_id
        )
        existing_types = {row['achievement_type'] for row in existing_achievements}
    
    new_achievements = []
    
    # Check milestone achievements
    if current_balance >= 100 and 'milestone_100' not in existing_types:
        new_achievements.append('milestone_100')
    
    if current_balance >= 500 and 'milestone_500' not in existing_types:
        new_achievements.append('milestone_500')
    
    if current_balance >= 1000 and 'milestone_1000' not in existing_types:
        new_achievements.append('milestone_1000')
    
    if current_balance >= 2000 and 'high_roller' not in existing_types:
        new_achievements.append('high_roller')
    
    # Check if user has any points for first_points achievement
    if current_balance > 0 and 'first_points' not in existing_types:
        new_achievements.append('first_points')
    
    # Check email verification achievement
    if 'email_verified' not in existing_types:
        async with db.pool.acquire() as conn:
            email_result = await conn.fetchrow(
                "SELECT status FROM email_submissions WHERE discord_user_id = $1 AND status = 'processed'",
                user_id
            )
            if email_result:
                new_achievements.append('email_verified')
    
    # Award new achievements
    for achievement_type in new_achievements:
        await award_achievement(db, user_id, achievement_type)
    
    return new_achievements

async def award_achievement(db, user_id: str, achievement_type: str):
    """Award a specific achievement to a user"""
    
    if achievement_type not in ACHIEVEMENT_TYPES:
        return False
    
    achievement_data = ACHIEVEMENT_TYPES[achievement_type]
    
    async with db.pool.acquire() as conn:
        # Insert achievement record
        await conn.execute('''
            INSERT INTO achievements (user_id, achievement_type, achievement_name, points_earned)
            VALUES ($1, $2, $3, $4)
        ''', user_id, achievement_type, achievement_data['name'], achievement_data['points_reward'])
        
        # Award bonus points
        if achievement_data['points_reward'] > 0:
            current_balance = await db.get_points(user_id)
            new_balance = current_balance + achievement_data['points_reward']
            
            # Update points
            await conn.execute('''
                INSERT INTO points (user_id, balance) VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET 
                    balance = $2, updated_at = CURRENT_TIMESTAMP
            ''', user_id, new_balance)
            
            # Log transaction
            await conn.execute('''
                INSERT INTO transactions (user_id, amount, transaction_type, reason, old_balance, new_balance)
                VALUES ($1, $2, 'achievement', $3, $4, $5)
            ''', user_id, achievement_data['points_reward'], 
            f"Achievement: {achievement_data['name']}", current_balance, new_balance)
    
    return True

async def get_user_achievements(db, user_id: str):
    """Get all achievements for a specific user"""
    
    async with db.pool.acquire() as conn:
        achievements = await conn.fetch('''
            SELECT achievement_type, achievement_name, points_earned, earned_at
            FROM achievements 
            WHERE user_id = $1 
            ORDER BY earned_at DESC
        ''', user_id)
    
    return [dict(row) for row in achievements]

async def get_recent_achievements(db, limit: int = 10):
    """Get recent achievements across all users"""
    
    async with db.pool.acquire() as conn:
        achievements = await conn.fetch('''
            SELECT user_id, achievement_type, achievement_name, points_earned, earned_at
            FROM achievements 
            ORDER BY earned_at DESC 
            LIMIT $1
        ''', limit)
    
    return [dict(row) for row in achievements]

async def initialize_achievements_for_existing_users():
    """Initialize achievements for all existing users based on their current stats"""
    
    db = PostgreSQLPointsDatabase()
    await db.initialize()
    
    try:
        # Get all users with points
        async with db.pool.acquire() as conn:
            users = await conn.fetch("SELECT user_id, balance FROM points")
        
        print(f"Checking achievements for {len(users)} users...")
        
        for user in users:
            user_id = user['user_id']
            balance = user['balance']
            
            new_achievements = await check_and_award_achievements(db, user_id, balance)
            if new_achievements:
                print(f"User {user_id}: Awarded {len(new_achievements)} achievements")
        
        print("Achievement initialization complete!")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(initialize_achievements_for_existing_users())