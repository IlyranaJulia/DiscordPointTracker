#!/usr/bin/env python3
"""
Import points data from CSV backup file into PostgreSQL database
"""

import csv
import asyncio
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def import_points_data():
    """Import points data from CSV file into PostgreSQL database"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        return
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        # Read CSV file
        csv_file = 'attached_assets/points_1753348417566.csv'
        
        print(f"Reading CSV file: {csv_file}")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            imported_count = 0
            updated_count = 0
            
            for row in reader:
                # Extract data from CSV row
                discord_username = row['Discord User'].strip()
                user_id = row['User ID'].strip()
                balance = row['balance'].strip()
                
                # Skip empty rows
                if not user_id or not balance:
                    continue
                
                # Convert balance to integer
                try:
                    balance = int(balance)
                except ValueError:
                    print(f"Warning: Invalid balance '{balance}' for user {discord_username}")
                    balance = 0
                
                # Check if user already exists in points table
                existing = await conn.fetchrow(
                    'SELECT balance FROM points WHERE user_id = $1',
                    user_id
                )
                
                current_timestamp = datetime.now()
                
                if existing:
                    # Update existing record with new balance and current timestamp
                    await conn.execute('''
                        UPDATE points 
                        SET balance = $1, 
                            updated_at = $2
                        WHERE user_id = $3
                    ''', balance, current_timestamp, user_id)
                    updated_count += 1
                    print(f"Updated: {discord_username} ({user_id}) - Balance: {balance}")
                else:
                    # Insert new record with current timestamps
                    await conn.execute('''
                        INSERT INTO points 
                        (user_id, balance, created_at, updated_at)
                        VALUES ($1, $2, $3, $4)
                    ''', user_id, balance, current_timestamp, current_timestamp)
                    
                    # Also initialize user_stats if it doesn't exist
                    stats_exists = await conn.fetchrow(
                        'SELECT user_id FROM user_stats WHERE user_id = $1',
                        user_id
                    )
                    
                    if not stats_exists:
                        await conn.execute('''
                            INSERT INTO user_stats 
                            (user_id, total_points_earned, transactions_count, first_activity, last_activity, highest_balance)
                            VALUES ($1, $2, 1, $3, $4, $5)
                        ''', user_id, max(0, balance), current_timestamp, current_timestamp, balance)
                    
                    imported_count += 1
                    print(f"Imported: {discord_username} ({user_id}) - Balance: {balance}")
        
        print(f"\nImport completed!")
        print(f"New records imported: {imported_count}")
        print(f"Existing records updated: {updated_count}")
        print(f"Total processed: {imported_count + updated_count}")
        
        # Show final count and top balances
        total_count = await conn.fetchval('SELECT COUNT(*) FROM points')
        print(f"Total points records in database: {total_count}")
        
        # Show top 5 balances
        top_balances = await conn.fetch('''
            SELECT user_id, balance 
            FROM points 
            ORDER BY balance DESC 
            LIMIT 5
        ''')
        
        print("\nTop 5 balances:")
        for record in top_balances:
            print(f"  User {record['user_id']}: {record['balance']} points")
        
    except Exception as e:
        print(f"Error during import: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_points_data())