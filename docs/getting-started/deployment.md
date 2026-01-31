# ZyraX Bot - Deployment Guide

## Overview

This guide covers deploying ZyraX bot to production using **PM2** process manager and **MongoDB Atlas** cloud database.

---

## Prerequisites

### System Requirements
- **OS:** Linux/macOS (Ubuntu 20.04+ recommended)
- **Python:** 3.12+
- **Node.js:** 16+ (for PM2)
- **RAM:** Minimum 512MB, Recommended 1GB+
- **Storage:** Minimum 2GB free space

### Required Accounts
- **Telegram:** Bot token from [@BotFather](https://t.me/BotFather)
- **MongoDB Atlas:** Free tier cluster ([sign up here](https://www.mongodb.com/cloud/atlas/register))
- **Telegram API:** API ID and Hash from [my.telegram.org](https://my.telegram.org)

---

## Step 1: Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Python 3.12
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.12 python3.12-venv python3.12-dev -y
```

### 1.3 Install PM2
```bash
# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Install PM2 globally
sudo npm install -g pm2
```

---

## Step 2: MongoDB Atlas Setup

### 2.1 Create Cluster
1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a new cluster (free tier: M0)
3. Choose your preferred region
4. Wait for cluster to deploy (~5 minutes)

### 2.2 Create Database User
1. Go to **Database Access** → **Add New Database User**
2. Choose **Password** authentication
3. Set username and strong password
4. Grant **Read and Write to any database** role
5. Click **Add User**

### 2.3 Whitelist IP Address
1. Go to **Network Access** → **Add IP Address**
2. For testing: Click **Allow Access from Anywhere** (0.0.0.0/0)
3. For production: Add your server's specific IP address
4. Click **Confirm**

### 2.4 Get Connection String
1. Click **Connect** on your cluster
2. Choose **Connect your application**
3. Select **Python** driver and version **3.12 or later**
4. Copy the connection string:
```
mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
```

---

## Step 3: Project Deployment

### 3.1 Clone Repository
```bash
cd ~
git clone https://github.com/yourusername/ZyraX.git
cd ZyraX
```

### 3.2 Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3.3 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Configure Environment
```bash
# Copy example and edit
cp .env.example .env
nano .env
```

**Update these values in `.env`:**
```bash
# Telegram Bot Configuration
BOT_TOKEN=7634351009:AAH9nYourBotTokenHere
BOT_USERNAME=YourBotUsername

# Telegram MTProto (from my.telegram.org)
API_ID=12345678
API_HASH=your_api_hash_here

# MongoDB Atlas Connection
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/zyrax?retryWrites=true&w=majority

# Bot Owner
OWNER_ID=1234567890

# Environment
ENVIRONMENT=production

# Redis (optional - leave commented for in-memory cache)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=
# REDIS_DB=0
```

**Important:** Replace:
- `username:password` with your MongoDB Atlas credentials
- `cluster` with your actual cluster name
- `BOT_TOKEN` with your bot token
- `API_ID` and `API_HASH` with your Telegram API credentials
- `OWNER_ID` with your Telegram user ID

---

## Step 4: PM2 Configuration

### 4.1 Create PM2 Config
```bash
# Copy example and edit
cp ecosystem.config.example.js ecosystem.config.js
nano ecosystem.config.js
```

**Update `cwd` path:**
```javascript
module.exports = {
  apps: [{
    name: 'zyrax',
    script: 'bot.py',
    interpreter: 'python3.12',
    cwd: '/home/yourusername/ZyraX',  // ← Change this to your path
    instances: 1,
    autorestart: true,
    watch: false,  // Set to true for development
    max_memory_restart: '500M',
    error_file: './data/logs/pm2-error.log',
    out_file: './data/logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
};
```

### 4.2 Create Log Directory
```bash
mkdir -p data/logs data/sessions data/backups
```

---

## Step 5: Start Bot

### 5.1 Start with PM2
```bash
# Activate virtual environment first
source venv/bin/activate

# Start bot
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs zyrax
```

### 5.2 Enable Auto-Start on Boot
```bash
# Generate startup script
pm2 startup

# Save current process list
pm2 save
```

---

## PM2 Management Commands

### Basic Commands
```bash
# View bot status
pm2 status

# View live logs
pm2 logs zyrax

# View last 200 lines
pm2 logs zyrax --lines 200

# Stop bot
pm2 stop zyrax

# Restart bot
pm2 restart zyrax

# Delete from PM2
pm2 delete zyrax

# Monitor resources
pm2 monit
```

### Advanced Commands
```bash
# Reload (zero-downtime restart)
pm2 reload zyrax

# Flush logs
pm2 flush

# View process info
pm2 info zyrax

# Show process list
pm2 list
```

---

## Step 6: Post-Deployment

### 6.1 Test Bot
1. Open Telegram and search for your bot
2. Send `/start` command
3. Check if bot responds
4. Test admin commands in your group

### 6.2 Monitor Logs
```bash
# Real-time logs
pm2 logs zyrax --lines 100

# Error logs only
tail -f data/logs/pm2-error.log

# Application logs
tail -f data/logs/bot.log
```

### 6.3 Verify Database Connection
```bash
# Check if data is being saved
pm2 logs zyrax | grep "Connected to MongoDB"
```

---

## Troubleshooting

### Bot Won't Start
```bash
# Check logs
pm2 logs zyrax --err

# Common issues:
# 1. Wrong Python version
python3.12 --version

# 2. Missing dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Invalid .env file
nano .env  # Check all values are set correctly
```

### Database Connection Issues
```bash
# Test MongoDB connection
python3.12 -c "from pymongo import MongoClient; client = MongoClient('your_mongo_uri'); print(client.server_info())"

# Common issues:
# 1. IP not whitelisted in MongoDB Atlas
# 2. Wrong username/password
# 3. Wrong database name in URI
```

### Bot Crashes Frequently
```bash
# Check memory usage
pm2 info zyrax

# Increase memory limit in ecosystem.config.js:
max_memory_restart: '1G',

# Restart with new config
pm2 restart zyrax
```

### Logs Not Showing
```bash
# Ensure log directory exists
mkdir -p data/logs

# Check PM2 log config
pm2 info zyrax | grep log

# Manually create log files
touch data/logs/pm2-error.log data/logs/pm2-out.log
pm2 restart zyrax
```

---

## Updating Bot

### Method 1: Git Pull (Recommended)
```bash
cd ~/ZyraX
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
pm2 restart zyrax
```

### Method 2: Manual Update
```bash
cd ~/ZyraX
# Upload new files via SFTP/SCP
source venv/bin/activate
pip install -r requirements.txt --upgrade
pm2 restart zyrax
```

---

## Backup & Restore

### Backup Database
```bash
# MongoDB Atlas provides automatic backups
# To create manual backup:
# 1. Go to Atlas dashboard
# 2. Click "Backup" → "Take Snapshot Now"
```

### Backup Configuration
```bash
# Backup .env and logs
tar -czf zyrax-backup-$(date +%Y%m%d).tar.gz .env data/
```

### Restore
```bash
# Extract backup
tar -xzf zyrax-backup-20251003.tar.gz

# Restart bot
pm2 restart zyrax
```

---

## Security Best Practices

### 1. Environment Variables
- ✅ Never commit `.env` to git
- ✅ Use strong MongoDB passwords (16+ characters)
- ✅ Rotate bot token if compromised
- ✅ Keep `OWNER_ID` private

### 2. Server Security
```bash
# Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Keep system updated
sudo apt update && sudo apt upgrade -y
```

### 3. MongoDB Atlas
- ✅ Use specific IP whitelist (not 0.0.0.0/0)
- ✅ Enable database encryption
- ✅ Regular backup verification
- ✅ Monitor access logs

### 4. PM2 Security
```bash
# Set proper file permissions
chmod 600 .env
chmod 644 ecosystem.config.js

# Run as non-root user
pm2 startup -u yourusername --hp /home/yourusername
```

---

## Performance Optimization

### 1. Enable Redis (Optional)
```bash
# Install Redis
sudo apt install redis-server -y

# Enable in .env
REDIS_HOST=localhost
REDIS_PORT=6379

# Restart bot
pm2 restart zyrax
```

### 2. Adjust Memory Limits
```javascript
// ecosystem.config.js
max_memory_restart: '1G',  // Increase for large groups
```

### 3. Log Rotation
```bash
# Install PM2 log rotation
pm2 install pm2-logrotate

# Configure
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

---

## Monitoring & Alerts

### 1. Setup PM2 Monitoring
```bash
# Link to PM2 Plus (optional)
pm2 link <secret> <public>

# Or use built-in monitor
pm2 monit
```

### 2. Health Check Script
```bash
#!/bin/bash
# healthcheck.sh
if ! pm2 describe zyrax > /dev/null; then
    echo "Bot is down! Restarting..."
    pm2 restart zyrax
fi
```

### 3. Add to Cron
```bash
crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * /home/yourusername/healthcheck.sh
```

---

## Migration from Local MongoDB

If you were using local MongoDB and want to migrate to Atlas:

### 1. Export Data
```bash
# Export all collections
mongodump --db zyrax --out backup/

# Or export specific collection
mongoexport --db zyrax --collection chats --out chats.json
```

### 2. Import to Atlas
```bash
# Get Atlas connection string
ATLAS_URI="mongodb+srv://username:password@cluster.mongodb.net/zyrax"

# Import all data
mongorestore --uri="$ATLAS_URI" backup/zyrax/

# Or import specific collection
mongoimport --uri="$ATLAS_URI" --collection chats --file chats.json
```

### 3. Update Configuration
```bash
# Update .env with Atlas URI
nano .env

# Restart bot
pm2 restart zyrax
```

---

## Support

**Issues?**
- Check logs: `pm2 logs zyrax`
- GitHub Issues: [Report a bug](https://github.com/yourusername/ZyraX/issues)
- Telegram: @YourSupportGroup

**Resources:**
- [PM2 Documentation](https://pm2.keymetrics.io/docs/)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
- [Python-Telegram-Bot Docs](https://docs.python-telegram-bot.org/)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.