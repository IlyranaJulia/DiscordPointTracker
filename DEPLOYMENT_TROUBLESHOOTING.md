# Fly.io Deployment Troubleshooting Guide

## Common "Stuck" Deployment Issues

### 1. Build Process Issues
**Symptoms:** Deployment hangs during Docker build
**Causes:**
- Large file sizes (bot.py is 70KB)
- Network timeouts during dependency installation
- Memory limits during build

**Solutions:**
```bash
# Check deployment logs
fly logs --app discord-points-bot

# Monitor deployment progress
fly status --app discord-points-bot

# Cancel stuck deployment
fly apps restart discord-points-bot
```

### 2. Memory Configuration Issues
**Symptoms:** App starts then crashes or becomes unresponsive
**Current Config:** 1GB memory in fly.toml

**Fix if needed:**
```bash
# Increase memory if deployment keeps failing
fly scale memory 2048 --app discord-points-bot
```

### 3. Health Check Failures
**Symptoms:** Deployment completes but app shows as unhealthy
**Cause:** Web server not responding on expected port

**Solution:** Ensure Flask runs on port 5000 (already configured)

### 4. Volume Mount Issues
**Symptoms:** Database errors after deployment
**Cause:** Persistent volume not properly mounted

**Fix:**
```bash
# Check if volume exists
fly volumes list --app discord-points-bot

# Create volume if missing
fly volumes create discord_bot_data --region sjc --size 1 --app discord-points-bot
```

## Quick Deployment Fixes

### Option 1: Restart Deployment
```bash
fly apps restart discord-points-bot
fly deploy --app discord-points-bot
```

### Option 2: Deploy with More Resources
```bash
# Temporarily increase resources
fly scale memory 2048 --app discord-points-bot
fly deploy --app discord-points-bot
# Scale back down after successful deployment
fly scale memory 1024 --app discord-points-bot
```

### Option 3: Deploy Without Build Cache
```bash
fly deploy --no-cache --app discord-points-bot
```

## Checking Deployment Status

### View Real-time Logs
```bash
fly logs --app discord-points-bot
```

### Check App Status
```bash
fly status --app discord-points-bot
```

### Test App Health
```bash
# Check if web dashboard is accessible
curl https://discord-points-bot.fly.dev
```

## Expected Deployment Time
- **Normal:** 3-5 minutes
- **First deployment:** 5-10 minutes (building Docker image)
- **Stuck:** >15 minutes without progress

## Signs of Successful Deployment
- Logs show: "Bot is ready! Logged in as pipi-bot"
- Web dashboard accessible at https://your-app.fly.dev
- App status shows "running"
- 7 slash commands synced successfully

## If Still Stuck
Try this sequence:
1. `fly logs` - Check for specific error messages
2. `fly apps restart` - Force restart
3. `fly deploy --no-cache` - Clean deployment
4. Contact me with specific error messages if issues persist

Most deployment "stuck" issues resolve with a restart or clean deploy.