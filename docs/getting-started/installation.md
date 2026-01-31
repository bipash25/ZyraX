# ZyraX Bot - Installation Guide

**Complete guide to get your bot running**

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11 or higher** installed
- ✅ **MongoDB** (local installation or MongoDB Atlas account)
- ✅ **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- ✅ **Your Telegram User ID** from [@userinfobot](https://t.me/userinfobot)
- ✅ **Telegram API credentials** from [my.telegram.org](https://my.telegram.org) (optional but recommended)

---

## 🚀 Installation Steps

### Step 1: Clone or Download the Project

```bash
# If using git
git clone https://github.com/bipash25/ZyraX.git
cd ZyraX

# Or download and extract the ZIP file
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite text editor
# Windows: notepad .env
# Linux/Mac: nano .env
```

**Edit `.env` file with your credentials:**

```env
# Required Settings
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
OWNER_ID=YOUR_TELEGRAM_USER_ID
MONGO_URI=mongodb://localhost:27017/zyrax

# Optional but Recommended (for MTProto features)
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
ENABLE_MTPROTO=true

# Optional (Redis caching)
ENABLE_REDIS=false
REDIS_HOST=localhost
REDIS_PORT=6379
```

**How to get your credentials:**

1. **BOT_TOKEN**: 
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy the token provided

2. **OWNER_ID**: 
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - It will show your user ID

3. **API_ID & API_HASH**:
   - Go to [my.telegram.org](https://my.telegram.org)
   - Login with your phone number
   - Go to "API development tools"
   - Create an application
   - Copy the api_id and api_hash

### Step 5: Setup Database

Choose one of the following options:

#### Option A: Local MongoDB

**On Linux:**
```bash
# Install MongoDB
sudo apt update
sudo apt install mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify it's running
sudo systemctl status mongod
```

**On macOS:**
```bash
# Install via Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

**On Windows:**
- Download and install MongoDB from [mongodb.com](https://www.mongodb.com/try/download/community)
- MongoDB will run as a Windows service automatically

**Using Docker:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

#### Option B: MongoDB Atlas (Cloud)

See [MongoDB Atlas Setup Guide](mongodb-atlas.md) for detailed instructions.

### Step 6: Run the Bot

```bash
# Make sure virtual environment is activated
python bot.py
```

You should see:
```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                  ███████╗██╗   ██╗██████╗  █████╗ ██╗  ██╗   ║
║                  ╚══███╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗╚██╗██╔╝   ║
║                    ███╔╝  ╚████╔╝ ██████╔╝███████║ ╚███╔╝    ║
║                   ███╔╝    ╚██╔╝  ██╔══██╗██╔══██║ ██╔██╗    ║
║                  ███████╗   ██║   ██║  ██║██║  ██║██╔╝ ██╗   ║
║                  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

✓ Connected to MongoDB database: zyrax
✓ Loaded 110+ commands across 16 categories
🚀 @YourBotUsername is now ONLINE!
```

---

## ✅ Verification

Test your bot:

1. **Open Telegram** and find your bot
2. **Send `/start`** - You should get a welcome message
3. **Send `/ping`** - Bot should respond with latency
4. **Send `/help`** - View available commands
5. **Add to a test group** as admin and test moderation commands

---

## 🔧 Troubleshooting

### Bot doesn't start

**Problem:** "BOT_TOKEN not found" or similar
- **Solution:** Ensure `.env` file exists and contains valid credentials
- Check for typos in variable names

**Problem:** "Cannot connect to MongoDB"
- **Solution:** 
  - Ensure MongoDB is running: `sudo systemctl status mongod` (Linux)
  - Check MONGO_URI in `.env` is correct
  - For Atlas: Verify IP is whitelisted and credentials are correct

**Problem:** "Module not found" errors
- **Solution:** 
  ```bash
  # Ensure virtual environment is activated
  source venv/bin/activate  # Linux/Mac
  # or venv\Scripts\activate on Windows
  
  # Reinstall dependencies
  pip install -r requirements.txt
  ```

### Bot starts but doesn't respond

**Problem:** Bot is online but doesn't reply to commands
- **Solution:** 
  - Ensure bot has permission to read messages in groups
  - Make bot an admin in the group
  - Check logs in `data/logs/bot.log` for errors

### MTProto not working

**Problem:** "MTProto disabled" warning
- **Solution:** 
  - Add TELEGRAM_API_ID and TELEGRAM_API_HASH to `.env`
  - Set `ENABLE_MTPROTO=true` in `.env`
  - Restart the bot

### Permission Errors

**In groups, the bot needs admin permissions:**
- ✅ Delete messages (for `/purge`, `/del`)
- ✅ Ban users (for `/ban`, `/kick`)
- ✅ Restrict members (for `/mute`, locks)
- ✅ Pin messages (for `/pin`)
- ✅ Invite users (for antiraid)

---

## 📂 Project Structure Overview

```
ZyraX/
├── bot.py              # Main entry point - START HERE
├── config.py           # Configuration loader
├── requirements.txt    # Dependencies
├── .env               # Your credentials (gitignored)
│
├── core/              # Core bot infrastructure
│   ├── application.py # Main application manager
│   ├── database.py    # MongoDB connection
│   ├── cache.py       # Cache system
│   ├── loader.py      # Dynamic command loader
│   └── ...
│
├── handlers/          # Command handlers (110+ commands)
│   ├── admin/        # Admin management
│   ├── moderation/   # Ban, mute, warn, kick
│   ├── protection/   # Antiflood, antiraid, captcha
│   ├── filters/      # Custom filters
│   ├── notes/        # Notes system
│   ├── greetings/    # Welcome/goodbye
│   └── ...
│
├── middleware/        # Request processing pipeline
│   ├── antiflood_check.py
│   ├── captcha_handler.py
│   └── ...
│
├── utils/            # Utility functions
│   ├── user_resolver.py
│   ├── time_parser.py
│   └── ...
│
└── data/             # Runtime data (auto-created)
    ├── logs/         # Log files
    └── sessions/     # Pyrogram sessions
```

---

## 🔄 Keeping Your Bot Running

### Using systemd (Linux)

Create `/etc/systemd/system/zyrax.service`:

```ini
[Unit]
Description=ZyraX Telegram Bot
After=network.target mongodb.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ZyraX
ExecStart=/path/to/ZyraX/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable zyrax
sudo systemctl start zyrax
sudo systemctl status zyrax
```

### Using PM2 (Recommended for Production)

See [Deployment Guide](deployment.md) for detailed PM2 setup instructions.

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t zyrax-bot .
docker run -d --name zyrax --env-file .env zyrax-bot
```

---

## 🎯 Next Steps

Now that your bot is running:

1. **Test basic commands** (`/start`, `/ping`, `/help`)
2. **Add bot to a test group** as admin
3. **Configure protection** (`/setflood`, `/captcha`, `/antiraid`)
4. **Review** [Architecture](../development/architecture.md) for technical details
5. **Check** [Command Reference](../user-guide/quick-reference.md) for all commands
6. **Deploy** using [Deployment Guide](deployment.md) for production

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `data/logs/bot.log` or `tail -f data/logs/bot.log`
2. **Enable debug mode**: Set `LOG_LEVEL=DEBUG` in `.env`
3. **Review documentation** in the `docs/` directory
4. **Check GitHub Issues**: See if others have faced similar problems

---

## ✨ Congratulations!

Your ZyraX bot is now up and running! 🎉

**Explore the features:**
- 110+ commands across 16 categories
- Advanced moderation tools
- Anti-spam protection
- Custom filters and notes
- Captcha verification
- Federation system
- And much more!

**Happy Botting!** 🤖
