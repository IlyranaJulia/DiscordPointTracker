# Discord Points Bot

## Overview

This Python-based Discord bot provides a comprehensive points management system for Discord servers. It allows members to check balances and leaderboards, while administrators can manage points, email submissions, and user data. The project aims to offer a reliable, scalable, and user-friendly solution for tracking member engagement and rewarding participation within Discord communities, leveraging a PostgreSQL database for permanent data persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The bot employs a modular architecture designed for clear separation of concerns, reliability, and scalability.

- **Bot Core**: Built with `discord.py`, handling all Discord interactions, commands (fully converted to slash commands), and presence management. It includes global error handling and syncs commands on startup.
- **Database Management**: Utilizes PostgreSQL for robust and permanent data persistence. It features an enhanced schema for `points`, `transactions`, `achievements`, and `user_stats` tables, with async operations to prevent blocking. Data is stored with exact Discord ID preservation and connection pooling for performance.
- **Configuration**: Centralized, environment variable-based configuration (`config.py`) with fallback defaults for bot token, transaction limits, and feature flags.
- **Web Dashboard**: A Flask-based administrative panel providing a multi-section interface for:
    - **Points Management**: Silent point operations with reason tracking.
    - **Database Administration**: Real-time statistics, transaction monitoring, and bulk operations.
    - **User Management**: Unified system for email submissions and points, including advanced search, manual profile management, and direct user creation (without requiring Discord commands).
    - **Achievement System**: Creation and management of user achievements with automatic checking and bonus point rewards.
    - **Direct Messaging**: Admin-initiated DMs to users with tracking, and automatic DM notifications for point changes or email processing.
- **Deployment Strategy**: Configured for 24/7 operation on Replit with an enhanced keep-alive system (self-ping, multiple health endpoints) and external monitoring integration (UptimeRobot). It prioritizes Flask server startup for health checks and uses `interaction.response.defer()` for slash commands to prevent timeouts.
- **Logging & Error Handling**: Comprehensive logging (file and console output) and global error handling with input validation and database error recovery.

## External Dependencies

- **discord.py**: Primary Discord API wrapper.
- **asyncpg**: Asynchronous PostgreSQL driver.
- **Flask**: Web framework for the administrative dashboard.
- **python-dotenv**: For managing environment variables.
- **PostgreSQL**: Cloud-hosted relational database for data persistence.
- **Python standard library**: Essential modules like `logging`, `asyncio`, `os`, and `typing`.
- **UptimeRobot**: External monitoring service for ensuring 24/7 bot uptime.