#!/usr/bin/env python3
"""
Migration script to convert SQLite data to PostgreSQL and update bot.py
"""

import sqlite3
import asyncpg
import asyncio
import os
from datetime import datetime
import dateutil.parser

async def migrate_data():
    """Migrate existing SQLite data to PostgreSQL"""
    # Connect to PostgreSQL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to PostgreSQL
        pg_conn = await asyncpg.connect(database_url)
        
        # Check if SQLite database exists
        if not os.path.exists('points.db'):
            print("No SQLite database found to migrate")
            await pg_conn.close()
            return True
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect('points.db')
        sqlite_conn.row_factory = sqlite3.Row
        
        print("Starting data migration from SQLite to PostgreSQL...")
        
        # Migrate points table
        try:
            cursor = sqlite_conn.execute('SELECT * FROM points')
            points_data = cursor.fetchall()
            
            for row in points_data:
                await pg_conn.execute('''
                    INSERT INTO points (user_id, balance, created_at, updated_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET
                    balance = EXCLUDED.balance,
                    updated_at = EXCLUDED.updated_at
                ''', row['user_id'], row['balance'], row['created_at'], row['updated_at'])
            
            print(f"Migrated {len(points_data)} points records")
        except sqlite3.OperationalError:
            print("Points table doesn't exist in SQLite")
        
        # Migrate transactions table
        try:
            cursor = sqlite_conn.execute('SELECT * FROM transactions')
            transactions_data = cursor.fetchall()
            
            for row in transactions_data:
                await pg_conn.execute('''
                    INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, old_balance, new_balance, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ''', row['user_id'], row['amount'], row['transaction_type'], 
                    row['admin_id'], row['reason'], row['old_balance'], row['new_balance'], row['created_at'])
            
            print(f"Migrated {len(transactions_data)} transaction records")
        except sqlite3.OperationalError:
            print("Transactions table doesn't exist in SQLite")
        
        # Migrate email_submissions table
        try:
            cursor = sqlite_conn.execute('SELECT * FROM email_submissions')
            email_data = cursor.fetchall()
            
            for row in email_data:
                # Parse datetime strings to proper datetime objects
                submitted_at = dateutil.parser.parse(row['submitted_at']) if row['submitted_at'] else None
                processed_at = dateutil.parser.parse(row['processed_at']) if row['processed_at'] else None
                
                await pg_conn.execute('''
                    INSERT INTO email_submissions (discord_user_id, discord_username, email_address, submitted_at, status, processed_at, admin_notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', row['discord_user_id'], row['discord_username'], row['email_address'],
                    submitted_at, row['status'], processed_at, row['admin_notes'])
            
            print(f"Migrated {len(email_data)} email submission records")
        except sqlite3.OperationalError:
            print("Email submissions table doesn't exist in SQLite")
        
        # Close connections
        sqlite_conn.close()
        await pg_conn.close()
        
        print("Data migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(migrate_data())