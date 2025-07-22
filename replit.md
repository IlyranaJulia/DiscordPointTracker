# Discord Points Bot

## Overview

This is a comprehensive Discord bot built with Python that manages member points within Discord servers. The bot provides a complete points management system with user commands for checking balances and leaderboards, plus administrative commands for managing points. It uses SQLite for data persistence and includes comprehensive error handling, logging, and input validation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Bot Layer**: Discord.py-based bot handling commands and Discord interactions
- **Database Layer**: SQLite database with async operations for data persistence
- **Configuration Layer**: Environment-based configuration management
- **Logging Layer**: Comprehensive logging system for monitoring and debugging

## Recent Changes (2025-07-22)
- **Enhanced Database Schema**: Added transactions, achievements, and user_stats tables
- **Advanced Web Dashboard**: Multi-section admin interface with database management
- **Transaction Logging**: Complete audit trail for all point operations
- **Achievement System**: User achievements with bonus point rewards
- **Analytics Dashboard**: User statistics and database administration tools
- **Order Processing System**: Automated point distribution via email verification
- **SendGrid Integration**: Professional email notifications for order rewards
- **CSV Order Import**: Bulk processing of customer order data files
- **Mass Order Processing**: System ready to process customer orders with verification codes
- **Claim System**: !claim command enables customers to redeem points using verification codes
- **Points Calculation**: Automatic calculation based on order amount (1 amount = 1 point exactly)
- **Database Reset**: All points and verification codes cleared for official program launch

## Key Components

### 1. Bot Core (`bot.py`)
- **Purpose**: Main bot application using discord.py commands framework
- **Architecture Decision**: Uses discord.py's commands extension for structured command handling
- **Key Features**:
  - Custom command prefix configuration
  - Global error handling
  - Bot status management
  - Async database integration

### 2. Database Management (`database.py`)
- **Purpose**: Handles all database operations with SQLite
- **Architecture Decision**: Uses aiosqlite for async database operations to prevent blocking
- **Enhanced Schema Design** (Updated 2025-07-22):
  - `points` table: user_id, balance, created_at, updated_at
  - `transactions` table: Complete audit trail with admin tracking
  - `achievements` table: User achievement system with points rewards
  - `user_stats` table: Comprehensive user analytics and activity tracking
  - Database indexes for performance optimization
  - Automatic triggers for timestamp and statistics updates

### 3. Configuration (`config.py`)
- **Purpose**: Centralized configuration management
- **Architecture Decision**: Environment variable-based configuration with fallback defaults
- **Key Settings**:
  - Bot token and command prefix
  - Points transaction limits
  - Database path configuration
  - Feature flags for optional functionality

### 4. Web Dashboard Features (Enhanced 2025-07-22)
- **Points Management**: Silent point operations with reason tracking
- **Database Administration**: Real-time statistics and transaction monitoring  
- **Achievement System**: Create and manage user achievements
- **User Analytics**: Detailed user activity and performance metrics
- **Multi-section Interface**: Tabbed navigation for different admin functions

## Data Flow

1. **User Command Flow**:
   - Discord user sends command → Bot receives message → Command parser validates → Database query → Response sent

2. **Admin Command Flow**:
   - Admin sends command → Permission check → Input validation → Database transaction → Audit log → Response

3. **Database Operations**:
   - All database operations are async to prevent bot blocking
   - Automatic timestamp tracking for audit purposes
   - Connection management with proper error handling

## External Dependencies

### Core Dependencies
- **discord.py**: Discord API wrapper for bot functionality
- **aiosqlite**: Async SQLite database operations with enhanced schema
- **flask**: Web dashboard for administrative management
- **python-dotenv**: Environment variable management
- **Python standard library**: logging, asyncio, os, typing

### Discord API Integration
- **Required Intents**: Message content intent for command processing
- **Optional Intents**: Server members intent for enhanced user handling
- **Permissions**: Administrator permission required for point management commands

## Deployment Strategy

### Environment Configuration
- Bot token must be provided via `BOT_TOKEN` environment variable
- All configuration customizable through environment variables
- Fallback defaults provided for development

### Database Strategy
- **Choice**: SQLite for simplicity and zero-configuration deployment
- **Rationale**: Single-file database perfect for Discord bot use case
- **Scalability**: Suitable for typical Discord server sizes
- **Backup**: Optional backup functionality via configuration flags

### Logging Strategy
- **Dual Output**: File logging and console output
- **Log Levels**: Configurable via environment variables
- **Format**: Timestamp, logger name, level, and message for debugging

### Error Handling
- **Global Error Handler**: Catches and logs all command errors
- **Input Validation**: Comprehensive validation for all user inputs
- **Database Error Recovery**: Proper connection management and error recovery

The architecture prioritizes simplicity, reliability, and ease of deployment while providing comprehensive functionality for Discord server point management.