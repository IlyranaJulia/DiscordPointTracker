# Discord Points Bot

A comprehensive Discord bot that transforms community interactions into an engaging points-based gamification system. Features user-friendly commands, privacy-focused design, and a powerful web dashboard for administration.

## Features

- ✅ Check points balance for yourself or other users
- ✅ Add points to members (Admin only)
- ✅ Remove points from members (Admin only)
- ✅ Set points to specific amounts (Admin only)
- ✅ View points leaderboard
- ✅ Comprehensive error handling and input validation
- ✅ SQLite database with proper connection management
- ✅ Logging system for debugging and monitoring
- ✅ Help command with detailed usage information
- ✅ Bot status and statistics

## Commands

### User Commands
- `!mypoints` - Check your points balance (sent via DM for privacy)
- `!pointsboard [limit]` - Show the points leaderboard
- `!submitemail <email>` - Submit your order email address
- `!updateemail <email>` - Update your submitted email address  
- `!myemail` - Check your email submission status
- `!pipihelp` - Show all available commands

### Admin Interface
- **Web Dashboard**: All point management (add/remove/set points)
- **Email Management**: Process user email submissions
- **Database Tools**: Export data, view statistics, manage users

## Setup Instructions

### 1. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following intents:
   - Message Content Intent
   - Server Members Intent (optional, for better user handling)

### 2. Bot Permissions
When inviting the bot to your server, make sure it has these permissions:
- Send Messages
- Use Slash Commands (optional for future updates)
- Read Message History
- Add Reactions (optional)
- Embed Links

### 3. Environment Configuration
1. Copy `.env.example` to `.env`
2. Fill in your bot token:
   ```bash
   BOT_TOKEN=your_actual_discord_bot_token_here
   ```
3. Adjust other settings as needed

### 4. Installation & Running

#### Option 1: Direct Python
```bash
# Install required packages
pip install discord.py aiosqlite python-dotenv

# Run the bot
python bot.py
