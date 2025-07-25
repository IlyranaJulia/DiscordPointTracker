#!/usr/bin/env python3
"""
Update historical email submissions with current Discord server roles
"""

import asyncio
import os
import logging
from database_postgresql import PostgreSQLPointsDatabase
import discord
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_historical_roles():
    """Update existing email submissions with current Discord server roles"""
    
    # Initialize database
    db = PostgreSQLPointsDatabase()
    await db.initialize()
    
    # Initialize Discord bot
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f'Bot connected as {bot.user}')
        
        try:
            # Get all email submissions without roles
            query = """
                SELECT discord_user_id, discord_username, email_address 
                FROM email_submissions 
                WHERE server_roles IS NULL OR server_roles = ''
                ORDER BY submitted_at
            """
            
            submissions = await db.execute_query(query)
            logger.info(f"Found {len(submissions)} submissions to update")
            
            # Get the guild (server)
            guild = None
            for g in bot.guilds:
                guild = g
                break
                
            if not guild:
                logger.error("Bot is not in any guild")
                return
                
            logger.info(f"Working with guild: {guild.name}")
            
            updated_count = 0
            
            for user_id, username, email in submissions:
                try:
                    # Convert user_id to int for Discord API
                    discord_user_id = int(user_id)
                    
                    # Get member from guild
                    member = guild.get_member(discord_user_id)
                    
                    if member:
                        # Get roles (exclude @everyone)
                        roles = [role.name for role in member.roles if role.name != "@everyone"]
                        roles_str = ", ".join(roles) if roles else ""
                        
                        # Update database using PostgreSQL syntax
                        update_query = """
                            UPDATE email_submissions 
                            SET server_roles = $1 
                            WHERE discord_user_id = $2
                        """
                        
                        await db.execute_query(update_query, (roles_str, user_id))
                        
                        logger.info(f"Updated {username} ({user_id}): {roles_str or 'No roles'}")
                        updated_count += 1
                        
                    else:
                        logger.warning(f"Member {username} ({user_id}) not found in guild")
                        
                except Exception as e:
                    logger.error(f"Error updating {username} ({user_id}): {e}")
                    continue
            
            logger.info(f"Successfully updated {updated_count} submissions with server roles")
            
        except Exception as e:
            logger.error(f"Error in role update process: {e}")
        
        finally:
            await db.close()
            await bot.close()
    
    # Start the bot
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN not found in environment variables")
        return
        
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(update_historical_roles())