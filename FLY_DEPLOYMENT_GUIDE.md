# Deploy Discord Bot to Fly.io

## Prerequisites
1. Install Fly.io CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Sign up for Fly.io account
3. Have your GitHub repository ready

## Step 1: Setup Fly.io
```bash
# Install flyctl (if not already installed)
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
flyctl auth login
```

## Step 2: Prepare Your App
Your bot is already configured with:
✅ `fly.toml` - Fly.io configuration
✅ `Dockerfile` - Container setup
✅ `deploy_requirements.txt` - Python dependencies
✅ Environment variable support

## Step 3: Deploy
```bash
# Clone your GitHub repo locally
git clone https://github.com/IlyranaJulia/DiscordPointTracker.git
cd DiscordPointTracker

# Create and deploy the app
flyctl launch --no-deploy

# Set your environment secrets
flyctl secrets set BOT_TOKEN="your_discord_bot_token_here"
flyctl secrets set SENDGRID_API_KEY="your_sendgrid_api_key_here"

# Deploy the app
flyctl deploy
```

## Step 4: Configure Domain (Optional)
```bash
# Add custom domain (if you have one)
flyctl certs create your-domain.com
```

## Step 5: Monitor Your Bot
```bash
# Check app status
flyctl status

# View logs
flyctl logs

# Scale if needed
flyctl scale count 1
```

## Important Configuration Details

### Fly.toml Features:
- **Auto-restart**: Machines auto-start and stay running
- **Health checks**: Monitors bot health every 30 seconds
- **Resource limits**: 512MB RAM, 1 CPU core (adjustable)
- **Port 5000**: Web dashboard accessible

### Environment Variables:
- `BOT_TOKEN` - Your Discord bot token (required)
- `SENDGRID_API_KEY` - For email notifications (optional)
- `DATABASE_PATH` - Set to `/data/points.db` for persistence

### Persistent Storage:
The database will be stored in `/data/points.db` and persists across deployments.

## Costs:
- Fly.io free tier: 3 shared CPUs, 256MB RAM
- Your bot uses: 1 CPU, 512MB RAM
- Estimated cost: ~$2-5/month

## Troubleshooting:
```bash
# If deployment fails
flyctl logs

# Connect to your app
flyctl ssh console

# Restart the app
flyctl machine restart
```

Your Discord bot will be available 24/7 at: https://your-app-name.fly.dev