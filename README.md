# Discord Points Bot

A comprehensive Discord bot for managing member points with add, remove, balance check, and leaderboard functionality.

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
- `!points [@user]` - Check your points or another user's points
- `!leaderboard [limit]` - Show points leaderboard (max 25 users)
- `!help` - Show help information

### Admin Commands (Requires Administrator permission)
- `!addpoints @user <amount>` - Add points to a user
- `!removepoints @user <amount>` - Remove points from a user
- `!setpoints @user <amount>` - Set user's points to specific amount
- `!status` - Show bot status and statistics

### Command Aliases
- `!points` = `!balance`, `!p`
- `!addpoints` = `!add`
- `!removepoints` = `!remove`, `!subtract`
- `!setpoints` = `!set`
- `!leaderboard` = `!top`, `!lb`
- `!help` = `!h`

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
