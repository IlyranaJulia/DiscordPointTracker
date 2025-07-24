#!/usr/bin/env python3
"""
Import email submission data from CSV backup file into PostgreSQL database
"""

import csv
import asyncio
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def import_email_data():
    """Import email submissions from CSV file into PostgreSQL database"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        return
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        # Read CSV file
        csv_file = 'attached_assets/emailsubmissiondatabackup_1753347880581.csv'
        
        print(f"Reading CSV file: {csv_file}")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            imported_count = 0
            updated_count = 0
            
            for row in reader:
                # Extract data from CSV row
                discord_username = row['Discord User'].strip()
                user_id = row['User ID'].strip()
                email = row['Email'].strip()
                status = row['Status'].strip().lower()
                submitted_str = row['Submitted'].strip()
                
                # Skip empty rows
                if not user_id or not email:
                    continue
                
                # Parse submitted date (format: 2025/7/24 06:05:51)
                try:
                    submitted_at = datetime.strptime(submitted_str, '%Y/%m/%d %H:%M:%S')
                except ValueError:
                    print(f"Warning: Could not parse date '{submitted_str}' for user {discord_username}")
                    submitted_at = datetime.now()
                
                # Check if user already exists
                existing = await conn.fetchrow(
                    'SELECT id FROM email_submissions WHERE discord_user_id = $1',
                    user_id
                )
                
                if existing:
                    # Update existing record
                    await conn.execute('''
                        UPDATE email_submissions 
                        SET discord_username = $1, 
                            email_address = $2, 
                            status = $3, 
                            submitted_at = $4,
                            processed_at = CASE WHEN $3 = 'processed' THEN $4 ELSE processed_at END
                        WHERE discord_user_id = $5
                    ''', discord_username, email, status, submitted_at, user_id)
                    updated_count += 1
                    print(f"Updated: {discord_username} ({user_id}) - {email}")
                else:
                    # Insert new record
                    await conn.execute('''
                        INSERT INTO email_submissions 
                        (discord_user_id, discord_username, email_address, status, submitted_at, processed_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    ''', user_id, discord_username, email, status, submitted_at, 
                         submitted_at if status == 'processed' else None)
                    imported_count += 1
                    print(f"Imported: {discord_username} ({user_id}) - {email}")
        
        print(f"\nImport completed!")
        print(f"New records imported: {imported_count}")
        print(f"Existing records updated: {updated_count}")
        print(f"Total processed: {imported_count + updated_count}")
        
        # Show final count
        total_count = await conn.fetchval('SELECT COUNT(*) FROM email_submissions')
        print(f"Total email submissions in database: {total_count}")
        
    except Exception as e:
        print(f"Error during import: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_email_data())