# Fly.io Deployment Guide - Discord Points Bot

This guide will help you deploy the Discord Points Bot to Fly.io for 24/7 online operation.

## Updates (2025-07-22)
- Removed SendGrid dependencies for simplified deployment
- Optimized memory configuration (1GB)
- Added persistent storage volume
- Simplified email processing workflow

## Prerequisites

1. **Fly.io Account** - Sign up at https://fly.io
2. **Fly CLI Tool** - Install flyctl
3. **Discord Bot Token** - Obtain from Discord Developer Portal

## Deployment Steps

### 1. Install Fly CLI
```bash
# Windows
iwr https://fly.io/install.ps1 -useb | iex

# macOS/Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login to Fly.io
```bash
fly auth login
```

### 3. Prepare Project Files
Ensure these files are ready:
- `bot.py` - Main bot application
- `fly.toml` - Fly.io configuration (optimized)
- `Dockerfile` - Docker configuration
- `deploy_requirements.txt` - Dependencies list (SendGrid removed)

### 4. Create Fly Application
```bash
fly apps create discord-points-bot
```

### 5. Create Persistent Storage Volume
```bash
fly volumes create discord_bot_data --region sjc --size 1
```

### 6. Set Environment Variables
```bash
fly secrets set BOT_TOKEN="your_discord_bot_token"
```

### 7. Deploy Application
```bash
fly deploy
```

## Configuration Details

### fly.toml Optimized Configuration
```toml
app = "discord-points-bot"
primary_region = "sjc"

[env]
  PORT = "5000"
  PYTHONUNBUFFERED = "1"

[http_services]
  internal_port = 5000
  auto_stop_machines = false    # Keep 24/7 online
  auto_start_machines = true
  min_machines_running = 1      # Minimum 1 machine running
  max_machines_running = 2      # Maximum 2 machines

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024             # 1GB memory for stable operation

[mount]
  source = "discord_bot_data"   # Persistent storage
  destination = "/data"
```

### Key Optimizations
- **Memory increased to 1GB** - Ensures stable bot operation
- **Auto-stop disabled** - Guarantees 24/7 availability
- **Persistent storage** - SQLite database won't be lost
- **Health checks** - Automatic bot status monitoring

## Monitoring and Maintenance

### View Logs
```bash
fly logs
```

### Check Application Status
```bash
fly status
```

### Restart Application
```bash
fly apps restart discord-points-bot
```

### Scale Resources (if needed)
```bash
fly scale memory 2048    # Increase to 2GB memory
fly scale count 2        # Run 2 instances
```

## Cost Estimation

Basic configuration (1GB memory, 1 instance):
- Approximately $5-10/month
- Includes sufficient CPU and network traffic
- Persistent storage has minimal additional cost

## Troubleshooting

### Common Issues

1. **Bot Offline**
   ```bash
   fly logs --app discord-points-bot
   ```

2. **Database Issues**
   - Check if storage volume is properly mounted
   - Verify database path `/data/points.db`

3. **Memory Issues**
   ```bash
   fly scale memory 2048
   ```

4. **Token Errors**
   ```bash
   fly secrets set BOT_TOKEN="new_token"
   ```

## Feature Confirmation

After deployment, the bot should support:
- 7 slash commands: /pipihelp, /mypoints, /pointsboard, etc.
- Web admin dashboard (https://your-app.fly.dev)
- SQLite database persistence
- 24/7 online operation
- Simplified email submission (no SendGrid verification required)

Your Discord bot will run 24/7 on Fly.io after successful deployment!