#!/usr/bin/env python3
import asyncio
import sqlite3
import os
from database_postgresql import PostgreSQLPointsDatabase

async def recover_email_submissions():
    """Recover email submissions from SQLite backup to PostgreSQL"""
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect('points.db')
    cursor = sqlite_conn.cursor()
    
    # Get all email submissions
    cursor.execute("""
        SELECT discord_user_id, discord_username, email_address, submitted_at, 
               status, processed_at, admin_notes 
        FROM email_submissions
    """)
    
    submissions = cursor.fetchall()
    sqlite_conn.close()
    
    print(f"Found {len(submissions)} email submissions to recover...")
    
    # Connect to PostgreSQL
    db = PostgreSQLPointsDatabase()
    await db.initialize()
    
    async with db.pool.acquire() as conn:
        for submission in submissions:
            discord_user_id, discord_username, email_address, submitted_at, status, processed_at, admin_notes = submission
            
            try:
                await conn.execute("""
                    INSERT INTO email_submissions 
                    (discord_user_id, discord_username, email_address, submitted_at, status, processed_at, admin_notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, str(discord_user_id), discord_username, email_address, submitted_at, status, processed_at, admin_notes)
                
                print(f"✓ Recovered: {discord_username} ({email_address})")
                
            except Exception as e:
                print(f"✗ Error recovering {discord_username}: {e}")
    
    await db.close()
    print(f"\n✅ Recovery complete! Restored {len(submissions)} email submissions.")

if __name__ == "__main__":
    asyncio.run(recover_email_submissions())