# ZyraX Features Guide

**Complete overview of all bot features and capabilities**

---

## 🛡️ Protection & Security

### Antiflood System
Automatic flood detection with configurable limits and actions.

**Commands:**
- `/setflood <count>` - Set message limit (0-200)
- `/floodmode <mode>` - Set action: ban/mute/kick/tban/tmute

**How it works:**
- Tracks message rate per user
- Triggers action when limit exceeded
- Approved users bypass flood checks

### Antiraid System
Mass join attack protection with time-based auto-disable.

**Commands:**
- `/antiraid <on/off/duration>` - Toggle raid protection
- Duration format: `1h`, `6h`, `1d`, etc.

**Features:**
- Monitors join rate
- Auto-kicks suspicious joins
- Temporary activation with auto-disable

### Captcha System
Multi-mode verification (Math, Button, Text) for new members.

**Commands:**
- `/captcha <on/off>` - Toggle captcha verification
- `/captchamode <type>` - Set mode: math/button/text
- `/verify <user>` - Manually verify user (bypass captcha)
- `/whitelist <user>` - Permanently whitelist from captcha
- `/unwhitelist <user>` - Remove from whitelist
- `/captchastats` - View captcha statistics
- `/pendingcaptcha` - List users awaiting verification

**Features:**
- Three verification modes
- Auto-kick on timeout
- Attempt limiting (max 3)
- Whitelist system for trusted users

### Approval System
Whitelist trusted users to bypass all restrictions.

**Commands:**
- `/approve <user>` - Approve user
- `/unapprove <user>` - Remove approval
- `/approved` - List approved users
- `/unapproveall` - Clear all approvals

### Content Locks
Restrict 26+ content types (media, URLs, forwards, etc.).

**Commands:**
- `/lock <type>` - Lock content type
- `/unlock <type>` - Unlock content type
- `/locks` - Show active locks
- `/locktypes` - List all 26 lock types

**Lock types include:**
- Media: photo, video, audio, document, sticker, animation, voice, video_note
- Content: url, forward, mention, hashtag, command, text
- Other: poll, location, contact, game, invoice, invite, pin, info

---

## 👥 Administration

### Admin Management
Manage admin privileges with custom titles.

**Commands:**
- `/promote <user> [title]` - Promote user to admin
- `/demote <user>` - Remove admin privileges
- `/adminlist` - List all administrators
- `/admincache` - Refresh admin list cache

### Permission System
Fine-grained permission checking for all commands.

---

## 🔨 Moderation

### Ban System
Permanent, temporary, silent, and delete variants.

**Commands:**
- `/ban <user> [reason]` - Permanently ban user
- `/tban <time> <user> [reason]` - Temporarily ban (e.g., `/tban 1h @user`)
- `/sban <user> [reason]` - Silent ban (no notification)
- `/dban <user> [reason]` - Ban and delete command message
- `/unban <user>` - Unban user

### Mute System
Restrict messaging with timed options.

**Commands:**
- `/mute <user> [reason]` - Permanently mute user
- `/tmute <time> <user> [reason]` - Temporarily mute
- `/smute <user> [reason]` - Silent mute
- `/dmute <user> [reason]` - Mute and delete command
- `/unmute <user>` - Unmute user

### Kick System
Remove users from the group.

**Commands:**
- `/kick <user> [reason]` - Kick user from group
- `/skick <user> [reason]` - Silent kick
- `/dkick <user> [reason]` - Kick and delete command

### Warning System
Progressive warning system with configurable actions.

**Commands:**
- `/warn <user> [reason]` - Issue warning to user
- `/warns [user]` - Show user's warnings
- `/rmwarn <user>` - Remove last warning
- `/resetwarn <user>` - Clear all warnings
- `/warnmode <mode>` - Set action: ban/kick/mute
- `/warnlimit <number>` - Set warning threshold

### Message Management
Bulk message deletion with range support.

**Commands:**
- `/purge` - Delete messages (reply to start message)
- `/del` - Delete single message (reply to message)

**Time format:** Supports `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks)

---

## 📝 Content Management

### Filters
Custom triggers with media, buttons, and markdown support.

**Commands:**
- `/filter <trigger>` - Create auto-reply (reply to message)
- `/filters` - List all active filters
- `/stop <trigger>` - Remove filter
- `/stopall` - Remove all filters

**Features:**
- Text and media support
- Button support: `[Text](buttonurl://url)`
- Variable filling: `{first}`, `{mention}`, `{chatname}`, etc.

### Notes
Save and retrieve information with hashtag triggers.

**Commands:**
- `/save <name>` - Save note (reply to message)
- `/get <name>` - Retrieve note
- `#notename` - Quick retrieve with hashtag
- `/notes` - List all notes
- `/clear <name>` - Delete note
- `/clearall` - Delete all notes

**Features:**
- Text and media support
- Hashtag triggers for quick access
- Variable support

### Greetings
Customizable welcome/goodbye messages with auto-delete.

**Commands:**
- `/welcome <on/off>` - Toggle welcome messages
- `/setwelcome` - Set custom welcome (reply to message)
- `/resetwelcome` - Reset to default
- `/goodbye <on/off>` - Toggle goodbye messages
- `/setgoodbye` - Set custom goodbye (reply to message)
- `/resetgoodbye` - Reset to default
- `/cleanwelcome <on/off>` - Auto-delete welcomes after 5 minutes

**Variables:**
- `{first}` - First name
- `{last}` - Last name
- `{fullname}` - Full name
- `{username}` - Username with @
- `{mention}` - HTML mention
- `{id}` - User ID
- `{chatname}` - Chat name
- `{count}` - Member count

### Pins
Advanced pin management with permanent pin feature.

**Commands:**
- `/pin [notify]` - Pin message (reply to message)
- `/unpin` - Unpin current message
- `/unpinall` - Unpin all messages
- `/permapin [notify]` - Permanent pin (auto re-pin)
- `/unpermapin` - Disable permanent pin

### Rules
Set and display group rules with private rules option.

**Commands:**
- `/rules` - Display chat rules
- `/setrules` - Set chat rules (reply to message)
- `/resetrules` - Clear chat rules
- `/privaterules <on/off>` - Send rules in PM

### Blocklists
Word filtering with wildcard patterns.

**Commands:**
- `/addblocklist <word>` - Add word to blocklist (supports `?` and `*` wildcards)
- `/rmblocklist <word>` - Remove word from blocklist
- `/blocklist` - Show all blocked words
- `/blocklistmode <mode>` - Set action: delete/ban/mute
- `/blocklistdelete <on/off>` - Toggle auto-delete

---

## 🌐 Federation System

Cross-group ban sharing for multiple chats.

### Core Management
**Commands:**
- `/newfed <name>` - Create a new federation
- `/joinfed <fed_id>` - Connect chat to federation
- `/leavefed` - Disconnect from federation

### Ban Management
**Commands:**
- `/fban <user> [reason]` - Ban user across all federated chats
- `/unfban <user>` - Unban user from federation

### Information
**Commands:**
- `/fedinfo [fed_id]` - Show federation details
- `/fedadmins [fed_id]` - List federation administrators
- `/myfeds` - Show federations you own/admin
- `/chatfed` - Show current chat's federation

### Admin Management
**Commands:**
- `/fedpromote <user>` - Promote user to fed admin (owner only)
- `/feddemote <user>` - Demote fed admin (owner only)

---

## 📊 Engagement & Gamification

### Leveling System
XP tracking with automatic level-ups.

**Commands:**
- `/rank [@user]` - View rank, level, and XP
- `/leaderboard` or `/top` - Top 10 users by XP
- `/topchat` - Chat-specific leaderboard
- `/setxp <user> <amount>` - Set user's XP (admin only)

### Economy System
Virtual currency with multiple earning methods.

**Commands:**
- `/balance [@user]` - Check coin balance
- `/daily` - Claim daily reward (24h cooldown)
- `/transfer <user> <amount>` - Send coins to another user
- `/work` - Earn 50-200 coins (1h cooldown)
- `/slots <bet>` - Play slot machine
- `/gamble <amount>` - 50/50 coin flip bet
- `/richest` - Top 10 users by coins

**Earning methods:**
- Daily rewards
- Work command with level bonus
- Gambling (slots, coinflip)
- Trivia questions with coin rewards

### Profile System
User profiles with bio, reputation, and stats.

**Commands:**
- `/profile [@user]` - View user profile card
- `/setbio <text>` - Set your bio (max 200 chars)
- `/rep <user>` - Give +1 reputation (24h cooldown per user)

**Profile shows:**
- Level, XP, coins, reputation
- Messages sent, marriage status
- XP rank, wealth rank

### Fun Commands
Games, jokes, facts, quotes, and more.

**Commands:**
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

---

## 🛠️ Advanced Moderation

### Log Channels
Comprehensive action logging to channels.

**Commands:**
- `/setlog` - Set current chat as log channel
- `/setlogchannel` - Get log channel info
- `/unsetlog` - Remove log channel

### Reports
User reporting system with @admin mentions.

**Commands:**
- `/report [reason]` - Report a message (reply to message)
- `@admin` - Quick admin mention to report issues

### Backup & Restore
Import/Export chat settings.

**Commands:**
- `/export` - Export all chat settings to JSON
- `/import` - Import settings (reply to exported file)

---

## 🎮 Misc Commands

**Commands:**
- `/start` - Start the bot
- `/help [command]` - Show help menu
- `/id` - Get user/chat ID
- `/info [@user]` - Get user information
- `/ping` - Check bot latency

---

## 📊 Bot Statistics

**Total Commands:** 110+  
**Categories:** 16  
**Middleware:** 12  
**Protection Systems:** 6  
**Engagement Features:** 4

---

## 💡 Pro Tips

1. **Combine features** - Use antiflood + captcha + locks for maximum protection
2. **Approved users** - Bypass all restrictions for trusted members
3. **Federation** - Manage multiple groups with shared ban lists
4. **Custom welcome** - Create engaging welcome messages with variables
5. **Filters** - Automate responses to common questions
6. **Notes** - Store important information with hashtag triggers
7. **Warnings** - Progressive discipline system
8. **Economy** - Keep users engaged with leveling and coins

---

**For detailed command usage and examples, see [Quick Reference](quick-reference.md)**
