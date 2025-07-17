import discord
from discord.ext import commands
import logging
import asyncio
import sys
from config import Config
from database import PointsDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PointsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None  # We'll create a custom help command
        )
        
        self.db = PointsDatabase()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        await self.db.initialize()
        
    async def on_ready(self):
        """Called when the bot has successfully connected to Discord"""
        logger.info(f'Bot is ready! Logged in as {self.user} (ID: {self.user.id})')
        
        # Set bot status
        activity = discord.Game(name=f"{Config.COMMAND_PREFIX}pipihelp for commands")
        await self.change_presence(activity=activity)
        
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
            
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument. Use `{Config.COMMAND_PREFIX}pipihelp` for command usage.")
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided. Please check your input and try again.")
            
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("❌ User not found. Please mention a valid user.")
            
        else:
            logger.error(f"Unexpected error in command {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

# Initialize bot
bot = PointsBot()

@bot.command(name='points', aliases=['balance', 'p'])
async def check_points(ctx, member: discord.Member = None):
    """Check your points balance or another user's balance"""
    try:
        # If no member specified, check the command author's points
        target_user = member or ctx.author
        
        balance = await bot.db.get_points(target_user.id)
        
        if target_user == ctx.author:
            embed = discord.Embed(
                title="💰 Your Points Balance",
                description=f"You currently have **{balance:,} points**",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="💰 Points Balance",
                description=f"{target_user.mention} has **{balance:,} points**",
                color=discord.Color.blue()
            )
            
        embed.set_thumbnail(url=target_user.display_avatar.url)
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in check_points command: {e}")
        await ctx.send("❌ An error occurred while checking points balance.")

@bot.command(name='addpoints', aliases=['add'])
@commands.has_permissions(administrator=True)
async def add_points(ctx, member: discord.Member, amount: int):
    """Add points to a member (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        if amount > 1000000:  # Reasonable upper limit
            await ctx.send("❌ Point amount is too large. Maximum allowed is 1,000,000 points per transaction.")
            return
            
        # Add points
        await bot.db.update_points(member.id, amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Create success embed
        embed = discord.Embed(
            title="✅ Points Added Successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Added", value=f"{amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} added {amount} points to {member} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in add_points command: {e}")
        await ctx.send("❌ An error occurred while adding points.")

@bot.command(name='givepoints', aliases=['give'])
@commands.has_permissions(administrator=True)
async def give_points_by_name(ctx, username: str, amount: int):
    """Add points to a user by username (no mention needed) (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        if amount > 1000000:  # Reasonable upper limit
            await ctx.send("❌ Point amount is too large. Maximum allowed is 1,000,000 points per transaction.")
            return
        
        # Find member by username (case insensitive)
        member = None
        username_lower = username.lower()
        
        # Search through guild members with multiple strategies
        for guild_member in ctx.guild.members:
            # Exact match on display name or username
            if (guild_member.display_name.lower() == username_lower or 
                guild_member.name.lower() == username_lower):
                member = guild_member
                break
            # Partial match in display name or username
            elif (username_lower in guild_member.display_name.lower() or 
                  username_lower in guild_member.name.lower()):
                member = guild_member
                break
        
        if not member:
            # Try to find suggestions for similar usernames
            suggestions = []
            for guild_member in ctx.guild.members:
                if (username_lower in guild_member.display_name.lower() or 
                    username_lower in guild_member.name.lower() or
                    guild_member.display_name.lower().startswith(username_lower[:3]) or
                    guild_member.name.lower().startswith(username_lower[:3])):
                    suggestions.append(guild_member.display_name)
                    if len(suggestions) >= 3:
                        break
            
            error_msg = f"❌ Could not find user '{username}'."
            if suggestions:
                error_msg += f"\n💡 Did you mean: {', '.join(suggestions[:3])}?"
            else:
                error_msg += "\nMake sure they're in this server and the spelling is correct."
            
            await ctx.send(error_msg)
            return
            
        # Add points
        await bot.db.update_points(member.id, amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Create success embed
        embed = discord.Embed(
            title="✅ Points Added Successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Member", value=f"{member.display_name}", inline=True)
        embed.add_field(name="Points Added", value=f"{amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} gave {amount} points to {member.display_name} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in give_points_by_name command: {e}")
        await ctx.send("❌ An error occurred while adding points.")

@bot.command(name='removepoints', aliases=['remove', 'subtract'])
@commands.has_permissions(administrator=True)
async def remove_points(ctx, member: discord.Member, amount: int):
    """Remove points from a member (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        current_balance = await bot.db.get_points(member.id)
        
        # Check if user has enough points
        if current_balance < amount:
            embed = discord.Embed(
                title="⚠️ Insufficient Points",
                description=f"{member.mention} only has **{current_balance:,} points**.\nCannot remove **{amount:,} points**.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
            
        # Remove points
        await bot.db.update_points(member.id, -amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Create success embed
        embed = discord.Embed(
            title="❌ Points Removed Successfully",
            color=discord.Color.red()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Removed", value=f"{amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} removed {amount} points from {member} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in remove_points command: {e}")
        await ctx.send("❌ An error occurred while removing points.")

@bot.command(name='setpoints', aliases=['set'])
@commands.has_permissions(administrator=True)
async def set_points(ctx, member: discord.Member, amount: int):
    """Set a member's points to a specific amount (Admin only)"""
    try:
        # Validate amount
        if amount < 0:
            await ctx.send("❌ Point amount cannot be negative.")
            return
            
        if amount > 10000000:  # Reasonable upper limit
            await ctx.send("❌ Point amount is too large. Maximum allowed is 10,000,000 points.")
            return
            
        # Set points
        await bot.db.set_points(member.id, amount)
        
        # Create success embed
        embed = discord.Embed(
            title="🔧 Points Set Successfully",
            color=discord.Color.purple()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Set To", value=f"{amount:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} set {member}'s points to {amount} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in set_points command: {e}")
        await ctx.send("❌ An error occurred while setting points.")

@bot.command(name='pointsboard', aliases=['top', 'lb'])
async def leaderboard(ctx, limit: int = 10):
    """Show the points leaderboard"""
    try:
        # Validate limit
        if limit <= 0:
            limit = 10
        elif limit > 25:
            limit = 25
            
        top_users = await bot.db.get_leaderboard(limit)
        
        if not top_users:
            await ctx.send("📊 No users found in the leaderboard.")
            return
            
        embed = discord.Embed(
            title="🏆 Points Leaderboard",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, (user_id, balance) in enumerate(top_users, 1):
            # Try to get user from the current guild first, then global cache
            user = ctx.guild.get_member(user_id) if ctx.guild else None
            if not user:
                user = bot.get_user(user_id)
            
            if user:
                username = user.display_name
            else:
                # Try to fetch user from Discord API as last resort
                try:
                    user = await bot.fetch_user(user_id)
                    username = user.display_name
                except:
                    username = f"User {user_id}"
            
            # Add medals for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
                
            description += f"{medal} **{username}** - {balance:,} points\n"
            
        embed.description = description
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in leaderboard command: {e}")
        await ctx.send("❌ An error occurred while fetching the leaderboard.")

@bot.command(name='pipihelp', aliases=['ph'])
async def help_command(ctx):
    """Show help information for all commands"""
    embed = discord.Embed(
        title="🤖 Points Bot Help",
        description="Manage member points with these commands:",
        color=discord.Color.blue()
    )
    
    # User commands
    embed.add_field(
        name="👤 User Commands",
        value=f"`{Config.COMMAND_PREFIX}points [@user]` - Check your points or another user's points\n"
              f"`{Config.COMMAND_PREFIX}pointsboard [limit]` - Show points leaderboard",
        inline=False
    )
    
    # Admin commands
    embed.add_field(
        name="👑 Admin Commands",
        value=f"`{Config.COMMAND_PREFIX}addpoints @user <amount>` - Add points to a user\n"
              f"`{Config.COMMAND_PREFIX}givepoints <username> <amount>` - Add points by username\n"
              f"`{Config.COMMAND_PREFIX}removepoints @user <amount>` - Remove points from a user\n"
              f"`{Config.COMMAND_PREFIX}setpoints @user <amount>` - Set user's points to specific amount",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Information",
        value="• Admin commands require Administrator permission\n"
              "• Points cannot go below 0\n"
              "• Use command aliases for faster typing",
        inline=False
    )
    
    embed.set_footer(text=f"Bot made with ❤️ | Prefix: {Config.COMMAND_PREFIX}")
    
    await ctx.send(embed=embed)

@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def bot_status(ctx):
    """Show bot status and statistics (Admin only)"""
    try:
        total_users = await bot.db.get_total_users()
        total_points = await bot.db.get_total_points()
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🔌 Status", value="Online ✅", inline=True)
        embed.add_field(name="👥 Total Users", value=f"{total_users:,}", inline=True)
        embed.add_field(name="💰 Total Points", value=f"{total_points:,}", inline=True)
        embed.add_field(name="🌐 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🏠 Servers", value=f"{len(bot.guilds)}", inline=True)
        embed.add_field(name="👤 Users", value=f"{len(bot.users)}", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in bot_status command: {e}")
        await ctx.send("❌ An error occurred while fetching bot status.")

@bot.command(name='listusers')
@commands.has_permissions(administrator=True)
async def list_users(ctx):
    """List all server members for debugging (Admin only)"""
    try:
        members_list = []
        for member in ctx.guild.members:
            if not member.bot:  # Skip bots
                members_list.append(f"**{member.display_name}** (username: {member.name})")
        
        if not members_list:
            await ctx.send("No members found in this server.")
            return
            
        # Split into chunks if too many users
        chunk_size = 10
        for i in range(0, len(members_list), chunk_size):
            chunk = members_list[i:i + chunk_size]
            
            embed = discord.Embed(
                title=f"👥 Server Members ({i+1}-{min(i+chunk_size, len(members_list))} of {len(members_list)})",
                description="\n".join(chunk),
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)
            
            if len(members_list) > chunk_size and i + chunk_size < len(members_list):
                await asyncio.sleep(1)  # Small delay between messages
        
    except Exception as e:
        logger.error(f"Error in list_users command: {e}")
        await ctx.send("❌ An error occurred while listing users.")

async def main():
    """Main function to run the bot"""
    try:
        # Validate bot token
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "your_bot_token_here":
            logger.error("Bot token not configured! Please set BOT_TOKEN in your environment variables.")
            return
            
        # Start the bot
        async with bot:
            await bot.start(Config.BOT_TOKEN)
            
    except discord.LoginFailure:
        logger.error("Failed to login - Invalid bot token!")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Close database connection
        if bot.db:
            await bot.db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
