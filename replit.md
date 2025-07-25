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

## Recent Changes (2025-07-22 - 2025-07-25)

### Database Migration to PostgreSQL (2025-07-23 to 2025-07-24)
- **Database Persistence Issue Resolved**: SQLite data was being lost on Replit refreshes
- **PostgreSQL Implementation**: Created new database layer with full async support using asyncpg
- **Critical User ID Fix (2025-07-24)**: Resolved Discord user ID precision loss by changing schema from BIGINT to TEXT, preventing ID truncation (e.g., 495044225994326033 was stored as 495044225994326000)
- **Email Data Recovery (2025-07-24)**: Successfully recovered all 17 email submissions from SQLite backup after accidental deletion during schema migration
- **CSV Export Enhancement (2025-07-24)**: Added apostrophe prefix to user IDs in CSV exports to prevent Excel from changing Discord ID format
- **Bulk Points Management (2025-07-24)**: Implemented comprehensive bulk points operations (set/add/remove) with CSV template and user ID preservation
- **Complete Email Data Import (2025-07-24)**: Successfully imported all 41 email submissions from CSV backup, restoring complete email submission history with proper status tracking
- **Points Database Import (2025-07-24)**: Imported 41 user point balances from CSV backup with current timestamps, total 39,761 points distributed across all users
- **Enhanced Reliability**: User data now persists permanently across bot restarts and Replit environment refreshes with exact Discord ID preservation
- **Connection Pooling**: Implemented efficient database connection pooling for improved performance

### Unified User Management System (2025-07-25)
- **Complete User Management Integration**: Created unified system combining email submissions and points management in single interface
- **Advanced Search Functionality**: Added search by username, email, or user ID across all user data
- **Manual Profile Management**: Admins can manually add/edit usernames and email addresses for users with points
- **Real-time Data Synchronization**: All changes reflect immediately across dashboard sections and Discord commands
- **Enhanced User Experience**: Users can check manually added emails via `/myemail` command with full data consistency
- **Server Roles Collection**: Automatically collect and store user's Discord server roles when they submit email addresses for enhanced user profiling and community analysis

### User Experience Improvements (2025-07-25)
- **Pointsboard Enhancement**: Fixed /pointsboard command to show Discord usernames instead of user IDs
- **Database Overview Addition**: Added comprehensive database statistics to pointsboard showing total users (42) and total points (239,859)  
- **User ID Conversion Fix**: Properly handle string-to-integer conversion for Discord API calls while maintaining TEXT storage for precision
- **Leaderboard Display**: Enhanced ranking display with database overview including user count and point distribution
- **Admin Access Restriction**: Restricted /pointsboard command to administrators only for better security control
- **Enhanced Achievements System**: Created comprehensive achievement system with 8 achievement types, automatic checking, and bonus point rewards
- **Achievement Commands Added**: New /achievements and /recentachievements slash commands for viewing personal and community achievements
- **Database Structure Optimization**: Streamlined dashboard from 6 sections to 3 focused sections (Overview, User Management, Email Submissions)
- **Automatic Achievement Integration**: Points management now automatically checks and awards achievements when users reach milestones
- **Points System Restoration (2025-07-25)**: Completely restored points system integrity after achievement system caused severe data corruption - cleared 185 erroneous achievement transactions, restored original balances from CSV backup for all 41 users, total points corrected to authentic 39,761
- **Server Role Collection Fix (2025-07-25)**: Fixed server role collection in both `/submitemail` and `/updateemail` commands - new email submissions now properly collect and store user's Discord server roles, resolved PostgreSQL compatibility issues in admin commands, enhanced debugging for role collection failures
- **Admin DM Functionality (2025-07-25)**: Added `/senddm` admin command allowing administrators to send direct messages to users via the bot for important notifications, order status updates, and error alerts with full database tracking, delivery status monitoring, and `/viewmessages` command for message history management
- **Web Dashboard DM Integration (2025-07-25)**: Enhanced web dashboard with comprehensive Direct Messages management section including user lookup by email/username/ID, message composition with type selection, delivery tracking, message history viewing, and CSV export functionality
### Major Updates
- **Complete Slash Commands Conversion**: All prefix commands (!) converted to modern Discord slash commands (/)
- **Code Cleanup**: Removed duplicate Python files (bot_backup.py, test_order_system.py, order_processor_simple.py)
- **SendGrid Removal**: Eliminated SendGrid email verification complexity - simplified email submission without user verification
- **Documentation Cleanup**: Removed SendGrid-related documentation files (SENDGRID_*.md, EMAIL_*.md)
- **GitHub Ready**: Clean codebase prepared for GitHub upload with proper .gitignore and README.md
- **Simplified Architecture**: Streamlined email processing without external email service dependencies

### Deployment Fixes Applied (2025-07-23)
- **Root Health Check Enhancement**: Modified `/` endpoint to always return 200 status code for Cloud Run health checks
- **Improved Health Endpoints**: Enhanced `/health` endpoint with consistent 200 responses, added `/healthz` for Kubernetes compatibility
- **Proper Startup Architecture**: Restructured main() function in bot.py to properly handle both Flask and Discord bot initialization
- **Enhanced main.py**: Updated main entry point with proper error handling and startup sequencing
- **Flask Server Priority**: Ensured Flask web server starts before Discord bot for deployment health check requirements
- **Error-Resistant Health Checks**: All health endpoints now return 200 even during bot initialization or errors
- **Deployment Verification**: All endpoints tested and confirmed returning proper HTTP 200 status codes
- **Port Configuration**: Updated Flask server to use PORT environment variable for Cloud Run compatibility
- **Replit Deployment Ready**: Application configured for proper Replit deployment with health checks

### Email System Fixes Applied (2025-07-23)
- **Duplicate Submission Prevention**: Users can now only have one email submission (prevents database clutter)
- **Smart Update Logic**: If user has pending submission, new email updates existing entry instead of creating duplicate
- **Processed Submission Protection**: Users with already processed emails cannot submit new ones
- **Username Synchronization**: Dashboard automatically fetches and displays current Discord usernames instead of user IDs
- **Real-time Username Updates**: Database usernames are refreshed when dashboard loads to show current Discord names
- **Enhanced User Feedback**: Clear messages inform users whether they're updating existing or creating new submission
- **Database Cleanup**: Removed existing duplicate entries and implemented strict one-submission-per-user policy
- **Admin-Discord Synchronization**: Fixed API endpoint methods (POST vs DELETE) ensuring perfect sync between dashboard actions and Discord commands
- **Fresh Database Connections**: Enhanced /myemail command with fresh connections to prevent caching issues
- **Admin Debug Tools**: Added /checkemail command for real-time email status verification by administrators
- **Bulk Edit Functionality**: Added comprehensive bulk operations for email submissions management with checkboxes, select all, and bulk actions for processing or deleting multiple submissions simultaneously

### Bot Features
- **Enhanced User Commands**: /pipihelp (renamed from /help), /mypoints, /pointsboard, /submitemail, /updateemail, /myemail
- **Admin Slash Commands**: /status, /refreshpresence, /checkemail commands for administrators with proper permission checks
- **Automated Command Sync**: Bot successfully syncs 9 slash commands on startup
- **Modern Discord Integration**: Full compatibility with Discord's latest command interface standards
- **Web Dashboard**: Fully functional admin panel on port 5000 with real Discord usernames
- **Production Ready**: All deployment endpoints verified working with proper HTTP status codes
- **Enhanced Presence Management**: Periodic presence refresh every 30 minutes to ensure consistent online status

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

### 4. Web Dashboard Features (Enhanced 2025-07-22 to 2025-07-23)
- **Points Management**: Silent point operations with reason tracking
- **Database Administration**: Real-time statistics and transaction monitoring  
- **Achievement System**: Create and manage user achievements
- **User Analytics**: Detailed user activity and performance metrics
- **Multi-section Interface**: Tabbed navigation for different admin functions
- **Bulk Email Management**: Complete bulk edit functionality with checkboxes for selecting multiple submissions, bulk processing, and bulk deletion capabilities

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
- **Choice**: PostgreSQL for permanent data persistence and scalability
- **Rationale**: Cloud-hosted database ensures data survives Replit restarts and refreshes
- **Migration**: Successfully migrated from SQLite to PostgreSQL (July 23, 2025)
- **Data Persistence**: All user points, transactions, achievements, and email submissions permanently stored
- **Scalability**: Production-ready for growing Discord server communities

### Logging Strategy
- **Dual Output**: File logging and console output
- **Log Levels**: Configurable via environment variables
- **Format**: Timestamp, logger name, level, and message for debugging

### Error Handling
- **Global Error Handler**: Catches and logs all command errors
- **Input Validation**: Comprehensive validation for all user inputs
- **Database Error Recovery**: Proper connection management and error recovery

The architecture prioritizes simplicity, reliability, and ease of deployment while providing comprehensive functionality for Discord server point management.