# Discord Points Bot

A powerful Discord bot for managing member points with modern slash commands and web admin dashboard.

## Features

- **Modern Slash Commands** - Full support for Discord's latest slash command interface
- **Points Management System** - Complete user points tracking and management
- **Leaderboard System** - Real-time display of user point rankings
- **Email Submission System** - Simplified email submission process without user verification
- **Web Admin Dashboard** - Administrators can manage points through web interface
- **SQLite Database** - Lightweight persistent data storage

## Slash Commands

- `/pipihelp` - Show all available commands
- `/mypoints` - Check your points balance
- `/pointsboard` - View points leaderboard
- `/submitemail` - Submit your order email address
- `/updateemail` - Update previously submitted email
- `/myemail` - Check email submission status
- `/status` - View bot status (administrators only)

## Quick Start

1. Clone the repository
```bash
git clone <repository-url>
cd discord-points-bot
```

2. Install dependencies
```bash
pip install discord.py aiosqlite flask python-dotenv
```

3. Configure environment variables
```bash
cp .env.example .env
# Edit .env file and add your BOT_TOKEN
```

4. Run the bot
```bash
python bot.py
```

## Deployment

Multiple deployment options supported:

- **Fly.io Deployment** - See `FLY_DEPLOYMENT_GUIDE.md`
- **Docker Deployment** - Use provided `Dockerfile`
- **Local Running** - Direct execution with `python bot.py`

## Technical Architecture

- **Python 3.11+**
- **discord.py 2.5+** - Discord API library
- **aiosqlite** - Async SQLite database
- **Flask** - Web admin dashboard
- **python-dotenv** - Environment variable management

## File Structure

```
├── bot.py                  # Main bot application
├── database.py            # Database management
├── config.py              # Configuration management
├── order_processor.py     # Order processing logic
├── pyproject.toml         # Project dependencies
├── fly.toml               # Fly.io configuration
├── Dockerfile             # Docker configuration
└── README.md              # Project documentation
```

## License

MIT License# DiscordPointTracker
