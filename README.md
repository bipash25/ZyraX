# ZyraX - All-in-One Telegram Group Management Bot

<div align="center">

![ZyraX Banner](https://via.placeholder.com/800x200/667eea/ffffff?text=ZyraX+Bot)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PTB](https://img.shields.io/badge/python--telegram--bot-v20+-blue.svg)](https://python-telegram-bot.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-success.svg)]()

**A powerful, feature-rich Telegram bot for managing groups with advanced moderation, anti-spam protection, and community engagement tools.**

[Features](#-features) • [Installation](#-quick-start) • [Deployment](#-deployment) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

### 🛡️ Protection & Security
- **Antiflood** - Automatic flood detection with configurable limits and actions
- **Antiraid** - Mass join attack protection with time-based auto-disable
- **Captcha System** - Multi-mode verification (Math, Button, Text) for new members
- **Approval System** - Whitelist trusted users to bypass all restrictions
- **Content Locks** - ✅ Restrict 26+ content types (media, URLs, forwards, etc.)

### 👥 Administration
- **Promote/Demote** - Manage admin privileges with custom titles
- **Admin Cache** - Efficient admin list caching with MTProto
- **Permission System** - Fine-grained permission checking for all commands

### 🔨 Moderation
- **Ban System** - Permanent, temporary, silent, and delete variants
- **Mute System** - Restrict messaging with timed options
- **Kick** - Remove users from the group
- **Purge** - Bulk message deletion with range support
- **Warnings** - ✅ **NEW!** Progressive warning system with configurable actions

### 📝 Content Management
- **Filters** - ✅ Custom triggers with media, buttons, and markdown support
- **Notes** - ✅ Save and retrieve information with hashtag triggers
- **Greetings** - ✅ Customizable welcome/goodbye messages with auto-delete
- **Pins** - ✅ Advanced pin management with permanent pin feature
- **Rules** - ✅ Set and display group rules with private rules option
- **Blocklists** - ✅ Word filtering with wildcard patterns

### 🌐 Federation System ✅
- **Cross-Group Bans** - ✅ Share ban lists across multiple groups
- **Fed Management** - ✅ Create and manage your own federations (11 commands)
- **Fed Admins** - ✅ Promote/demote federation administrators
- **Auto-Ban** - ✅ Automatic enforcement of federation bans

### 📊 Engagement & Gamification ✅ **NEW!**
- **Leveling System** - ✅ XP tracking with automatic level-ups (6 commands)
- **Economy System** - ✅ Virtual currency with multiple earning methods (8 commands)
  - Daily rewards, work, gambling (slots, coinflip), transfers
  - Trivia questions with coin rewards
- **Profile System** - ✅ **NEW!** User profiles with bio, reputation, and stats (3 commands)
- **Fun Commands** - ✅ **NEW!** Games, jokes, facts, quotes, and more (12 commands)
  - Rock-Paper-Scissors, trivia, ship calculator
  - Jokes, facts, quotes, roasts, compliments

### 🛡️ Advanced Moderation ✅
- **Logs** - ✅ Comprehensive action logging to channels
- **Reports** - ✅ User reporting system with @admin mentions
- **Backup** - ✅ Import/Export chat settings

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **MongoDB Atlas** account (free tier available)
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **Telegram API Credentials** from [my.telegram.org](https://my.telegram.org)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ZyraX.git
cd ZyraX
```

2. **Create virtual environment**
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.template .env
nano .env  # Edit with your credentials
```

Required configuration:
- `BOT_TOKEN` - From @BotFather
- `OWNER_ID` - Your Telegram user ID
- `TELEGRAM_API_ID` - From my.telegram.org
- `TELEGRAM_API_HASH` - From my.telegram.org
- `MONGO_URI` - MongoDB connection string

5. **Run the bot**
```bash
python bot.py
```

---

## 🌐 Deployment

### Production Deployment with PM2

**ZyraX supports production deployment using PM2 process manager:**

1. **Setup PM2 configuration**
```bash
cp ecosystem.config.example.js ecosystem.config.js
nano ecosystem.config.js  # Update paths
```

2. **Start with PM2**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable auto-start on boot
```

3. **Monitor**
```bash
pm2 status
pm2 logs zyrax
pm2 monit
```

**📖 Full deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions including:
- MongoDB Atlas setup
- Server configuration
- Security best practices
- Backup & restore procedures
- Troubleshooting guide

---

## 📚 Documentation

### Getting Started
- **[Installation Guide](docs/getting-started/installation.md)** - Complete installation and setup instructions
- **[Deployment Guide](docs/getting-started/deployment.md)** - Production deployment with PM2 and MongoDB Atlas
- **[MongoDB Atlas Setup](docs/getting-started/mongodb-atlas.md)** - Cloud database configuration

### User Guide
- **[Features Overview](docs/user-guide/features.md)** - Complete feature documentation
- **[Quick Reference](docs/user-guide/quick-reference.md)** - Command quick reference card

### Development
- **[Architecture](docs/development/architecture.md)** - Technical design and implementation details
- **[Roadmap](docs/development/roadmap.md)** - Development roadmap and visual guides
- **[Implementation Guide](docs/development/implementation-guide.md)** - Code examples and patterns

### Command Reference

#### Admin Commands
- `/promote` - Promote user to admin with custom title
- `/demote` - Remove admin privileges
- `/adminlist` - List all administrators with permissions

#### Moderation Commands
- `/ban` - Permanently ban user
- `/tban <time>` - Temporarily ban user (e.g., `/tban 1h`)
- `/sban` - Silent ban (no notification)
- `/dban` - Ban and delete command message
- `/unban` - Unban user
- `/mute` - Mute user (restrict messaging)
- `/tmute <time>` - Temporarily mute user
- `/smute` - Silent mute
- `/dmute` - Mute and delete command
- `/unmute` - Unmute user
- `/kick` - Kick user from group
- `/purge` - Delete messages (reply to start message)
- `/del` - Delete single message (reply to message)

#### Antiflood Commands
- `/setflood <number>` - Set flood limit (0-200 messages)
- `/setfloodmode <mode>` - Set action: ban/mute/kick/tban/tmute

#### Approval Commands
- `/approve` - Add user to whitelist
- `/unapprove` - Remove from whitelist
- `/approved` - List all approved users
- `/unapproveall` - Clear all approvals

#### Antiraid Commands
- `/antiraid on <hours>` - Enable raid protection (1-168 hours)
- `/antiraid off` - Disable raid protection

#### Captcha Commands
- `/captcha on/off` - Enable/disable verification
- `/captchamode <mode>` - Set mode: math/button/text
- `/verify <user>` - Manually verify user (skip captcha)
- `/whitelist <user>` - Permanently whitelist from captcha
- `/unwhitelist <user>` - Remove from whitelist
- `/captchastats` - View captcha statistics
- `/pendingcaptcha` - List users awaiting verification

#### Warning Commands ✨ NEW!
- `/warn <user> [reason]` - Issue warning to user
- `/warns [user]` - Show user's warnings
- `/rmwarn <user>` - Remove last warning
- `/resetwarn <user>` - Clear all warnings
- `/warnmode <ban|kick|mute>` - Set action on limit
- `/warnlimit <number>` - Set warning threshold

#### Lock Commands ✨ NEW!
- `/lock <type>` - Restrict content type
- `/unlock <type>` - Allow content type
- `/locks` - Show active locks
- `/locktypes` - List all 26 lock types

#### Filter Commands ✨ NEW!
- `/filter <trigger>` - Create auto-reply (reply to message)
- `/filters` - List all active filters
- `/stop <trigger>` - Remove filter
- `/stopall` - Remove all filters

#### Note Commands ✨ NEW!
- `/save <name>` - Save note (reply to message)
- `/get <name>` - Retrieve note
- `#notename` - Quick retrieve with hashtag
- `/notes` - List all notes
- `/clear <name>` - Delete note
- `/clearall` - Delete all notes

#### Greeting Commands ✨ NEW!
- `/welcome on/off` - Toggle welcome messages
- `/setwelcome` - Set custom welcome (reply to message)
- `/resetwelcome` - Reset to default
- `/goodbye on/off` - Toggle goodbye messages
- `/setgoodbye` - Set custom goodbye (reply to message)
- `/resetgoodbye` - Reset to default
- `/cleanwelcome on/off` - Auto-delete welcomes after 5 minutes

#### Pin Commands ✨
- `/pin [notify]` - Pin message (reply to message)
- `/unpin` - Unpin current message
- `/unpinall` - Unpin all messages
- `/permapin [notify]` - Permanent pin (auto re-pin)
- `/unpermapin` - Disable permanent pin

#### Rules Commands ✨
- `/rules` - Display chat rules
- `/setrules` - Set chat rules (reply to message)
- `/resetrules` - Clear chat rules
- `/privaterules on/off` - Send rules in PM

#### Reports Commands ✨
- `/report [reason]` - Report a message (reply to message)
- `@admin` - Quick admin mention to report issues

#### Blocklist Commands ✨
- `/addblocklist <word>` - Add word to blocklist
- `/rmblocklist <word>` - Remove word from blocklist
- `/blocklist` - Show all blocked words
- `/blocklistmode <delete|ban|mute>` - Set action for violations
- `/blocklistdelete on/off` - Toggle auto-delete

#### Log Commands ✨
- `/setlog` - Set current chat as log channel
- `/setlogchannel` - Get log channel info
- `/unsetlog` - Remove log channel

#### Backup Commands ✨
- `/export` - Export all chat settings to JSON
- `/import` - Import settings (reply to exported file)

#### Federation Commands ✨
- `/newfed <name>` - Create a new federation
- `/joinfed <fed_id>` - Connect chat to federation
- `/leavefed` - Disconnect from federation
- `/fban <user> [reason]` - Ban user across all federated chats
- `/unfban <user>` - Unban user from federation
- `/fedinfo [fed_id]` - Show federation details
- `/fedadmins [fed_id]` - List federation administrators
- `/fedpromote <user>` - Promote to federation admin
- `/feddemote <user>` - Demote federation admin
- `/myfeds` - List your federations
- `/chatfed` - Show current chat's federation

#### Leveling Commands ✨ **NEW!**
- `/rank [@user]` - View rank, level, and XP
- `/leaderboard` or `/top` - Top 10 users by XP
- `/topchat` - Chat-specific leaderboard
- `/setxp <user> <amount>` - Set user's XP (admin only)

#### Economy Commands ✨ **NEW!**
- `/balance [@user]` - Check coin balance
- `/daily` - Claim daily reward (24h cooldown)
- `/transfer <user> <amount>` - Send coins to another user
- `/work` - Earn 50-200 coins (1h cooldown)
- `/slots <bet>` - Play slot machine
- `/gamble <amount>` - 50/50 coin flip bet
- `/richest` - Top 10 users by coins

#### Profile Commands ✨ **NEW!**
- `/profile [@user]` - View user profile card
- `/setbio <text>` - Set your bio (max 200 chars)
- `/rep <user>` - Give +1 reputation (24h cooldown per user)

#### Fun Commands ✨ **NEW!**
- `/8ball <question>` - Magic 8-ball answers
- `/roll [dice]` - Roll dice (default: 1d6)
- `/coinflip` - Flip a coin
- `/choose <opt1> | <opt2> | ...` - Choose randomly
- `/joke` - Random joke
- `/fact` - Random interesting fact
- `/quote` - Inspirational quote
- `/roast [@user]` - Funny roast (in good fun!)
- `/compliment [@user]` - Compliment someone
- `/ship <user1> <user2>` - Love calculator
- `/rps <rock|paper|scissors>` - Rock Paper Scissors
- `/trivia` - Answer trivia for coins

#### Misc Commands
- `/start` - Start the bot
- `/help [command]` - Show help menu
- `/id` - Get user/chat ID
- `/info [@user]` - Get user information

#### Blocklist Commands ✨ NEW!
- `/addblocklist <word>` - Block word (supports wildcards: `?`, `*`)
- `/rmblocklist <word>` - Unblock word
- `/blocklist` - List blocked words

#### Log Commands ✨ NEW!
- `/setlog` - Setup guide for log channel
- `/setlogchannel <id>` - Set log channel by ID
- `/unsetlog` - Remove log channel

#### Backup Commands ✨ NEW!
- `/export` - Export chat settings to JSON
- `/import` - Import settings (reply to JSON file)

#### Federation Commands ✨🔥 NEW!
**Core Management:**
- `/newfed <name>` - Create a new federation
- `/joinfed <fed_id>` - Connect chat to federation
- `/leavefed` - Disconnect from federation

**Ban Management:**
- `/fban <user> [reason]` - Ban user across all federated chats
- `/unfban <user>` - Unban user from federation

**Information:**
- `/fedinfo [fed_id]` - Show federation details
- `/fedadmins [fed_id]` - List federation admins
- `/myfeds` - Show federations you own/admin
- `/chatfed` - Show current chat's federation

**Admin Management:**
- `/fedpromote <user>` - Promote user to fed admin (owner only)
- `/feddemote <user>` - Demote fed admin (owner only)

#### Misc Commands
- `/start` - Welcome message and bot info
- `/help` - Show available commands by category
- `/id` - Get user/chat IDs and info
- `/ping` - Check bot latency

---

## 🏗️ Project Structure

```
ZyraX/
├── bot.py                      # Main entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── ecosystem.config.example.js # PM2 configuration template
│
├── core/                      # Core infrastructure
│   ├── application.py         # Main bot orchestrator
│   ├── database.py           # MongoDB connection
│   ├── cache.py              # LRU + Redis caching
│   ├── mtproto.py            # Pyrogram MTProto client
│   ├── scheduler.py          # APScheduler setup
│   ├── loader.py             # Dynamic command loader
│   └── decorators.py         # Permission decorators
│
├── handlers/                  # Command handlers
│   ├── admin/                # Admin management
│   ├── moderation/           # Ban, mute, kick, purge
│   ├── warnings/             # ✨ Warning system
│   ├── antiflood/            # Flood protection
│   ├── approval/             # User whitelisting
│   ├── antiraid/             # Raid protection
│   ├── captcha/              # Verification system
│   ├── locks/                # ✨ Content locks
│   ├── filters/              # ✨ Auto-reply filters
│   ├── notes/                # ✨ Saved notes
│   ├── greetings/            # ✨ Welcome/goodbye
│   ├── pins/                 # ✨ Pin management
│   ├── rules/                # ✨ Rules module
│   ├── reports/              # ✨ Reporting system
│   ├── blocklists/           # ✨ Word filtering
│   ├── logs/                 # ✨ Log channels
│   ├── backup/               # ✨ Import/Export
│   ├── federation/           # ✨🔥 Federation system (11 cmds)
│   └── misc/                 # Help, ping, id, start
│
├── middleware/               # Request processing
│   ├── antiflood_check.py   # Rate limiting
│   ├── antiraid_check.py    # Join rate monitoring
│   └── captcha_handler.py   # New member verification
│
├── utils/                    # Utility functions
│   ├── user_resolver.py     # Multi-source user resolution
│   ├── time_parser.py       # Parse time strings
│   ├── captcha_generator.py # Generate captcha challenges
│   └── mtproto_resolver.py  # Username resolution via MTProto
│
└── data/                     # Runtime data
    ├── logs/                 # Application logs
    ├── sessions/             # Pyrogram sessions
    └── backups/              # Configuration backups
```

---

## 🛠️ Technology Stack

### Core
- **Python 3.12+** - Modern Python with async/await
- **python-telegram-bot v20+** - Telegram Bot API wrapper
- **Pyrogram** - MTProto client for advanced features

### Database & Caching
- **MongoDB Atlas** - Cloud database with automatic backups
- **Motor** - Async MongoDB driver for Python
- **Redis** *(Optional)* - High-performance caching

### Task Management
- **APScheduler** - Scheduled tasks (timed bans, captcha timeouts)
- **PM2** - Process management and monitoring

### Additional Libraries
- **aiohttp** - Async HTTP client
- **python-dotenv** - Environment variable management
- **Pillow** - Image processing for captcha generation

---

## 🎯 Development Roadmap

### ✅ Phase 1-4: Complete
- [x] Core infrastructure and dynamic command loader
- [x] Admin management (promote, demote, adminlist)
- [x] Moderation suite (ban, mute, kick, purge with variants)
- [x] **Warning system** with auto-actions (ban/kick/mute)
- [x] Antiflood system with configurable actions
- [x] Approval system for whitelisting users
- [x] Antiraid protection with auto-expiry
- [x] Multi-mode captcha verification with whitelisting
- [x] **Locks module** - 26+ content type restrictions
- [x] **Filters system** - Custom triggers with media/buttons
- [x] **Notes system** - Save/retrieve with hashtags
- [x] **Greetings** - Welcome/goodbye with auto-delete
- [x] **Pins** - Pin management with permapin
- [x] **Pydantic models** - Type-safe database schemas
- [x] PM2 deployment configuration
- [x] MongoDB Atlas integration

### ✅ Phase 5: Complete
- [x] Rules management
- [x] Blocklists (word filtering)
- [x] Reports (@admin mentions)

### ✅ Phase 6: Complete
- [x] Federation system (cross-group bans)
- [x] Log channels and action logging
- [x] Import/Export (backup system)

### ✅ Phase 7: Complete - **NEW!**
- [x] Leveling and XP system
- [x] Economy system with gambling
- [x] Profile system with bio and reputation
- [x] Fun commands and interactive games

### 📋 Phase 8: Planned
- [ ] Connections (remote group management from PM)
- [ ] Advanced stats tracking and analytics
- [ ] Shop system with items
- [ ] Achievement system
- [ ] More mini-games and entertainment

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Reporting Bugs
1. Check if the issue already exists
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs (if applicable)

### Submitting Features
1. Open an issue to discuss the feature
2. Wait for approval before coding
3. Follow the coding standards
4. Write tests for new features
5. Update documentation

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**📖 See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.**

---

## 📊 Bot Statistics

**Current Version:** 2.1.0 🎉  
**Total Commands:** 110+ ⬆️  
**Active Middleware:** 12 ⬆️  
**Protection Systems:** 6  
**Engagement Features:** 4 🆕  
**Architecture:** Direct MongoDB operations (no ORM)  
**Supported Languages:** English (more coming soon)

### Command Breakdown
- **Admin:** 4 commands
- **Moderation:** 6 commands (+ variants)
- **Warnings:** 6 commands ✨
- **Antiflood:** 2 commands
- **Approval:** 4 commands
- **Antiraid:** 1 command
- **Captcha:** 7 commands ✨
- **Locks:** 4 commands ✨
- **Filters:** 4 commands ✨
- **Notes:** 5 commands ✨
- **Greetings:** 7 commands ✨
- **Pins:** 5 commands ✨
- **Rules:** 4 commands ✨
- **Reports:** 2 commands ✨
- **Blocklists:** 3 commands ✨
- **Logs:** 3 commands ✨
- **Backup:** 2 commands ✨
- **Federation:** 11 commands ✨
- **Leveling:** 6 commands 🆕
- **Economy:** 8 commands 🆕
- **Profile:** 3 commands 🆕
- **Fun:** 12 commands 🆕
- **Misc:** 4 commands

---

## 🔒 Security

### Reporting Security Issues
**DO NOT** open public issues for security vulnerabilities.  
Email: security@example.com

### Security Features
- ✅ Environment variable encryption
- ✅ MongoDB Atlas with authentication
- ✅ Rate limiting on all commands
- ✅ Permission verification on every action
- ✅ Comprehensive action logging
- ✅ IP whitelisting for database access

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) - Excellent PTB wrapper
- [Pyrogram](https://docs.pyrogram.org/) - Elegant MTProto framework
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Reliable cloud database
- [PM2](https://pm2.keymetrics.io/) - Advanced process manager

---

## 📞 Support

**Need help?**
- 📖 Check [Documentation](DEPLOYMENT.md)
- 🐛 Report [Issues](https://github.com/yourusername/ZyraX/issues)
- 💬 Join our [Telegram Group](https://t.me/YourSupportGroup)
- 📧 Email: support@example.com

---

## 🌟 Star History

If you find this project helpful, please consider giving it a ⭐!

---

<div align="center">

**Made with ❤️ by [Your Name](https://github.com/yourusername)**

[⬆ Back to Top](#zyrax---all-in-one-telegram-group-management-bot)

</div>