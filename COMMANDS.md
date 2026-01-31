# ZyraX Bot - Command Reference

**Generated:** 2025-10-05 08:11:50

Complete list of all bot commands organized by category.

## 📋 Table of Contents

- [Admin](#admin)
- [Antiflood](#antiflood)
- [Antiraid](#antiraid)
- [Approval](#approval)
- [Blocklists](#blocklists)
- [Captcha](#captcha)
- [Economy](#economy)
- [Federation](#federation)
- [Filters](#filters)
- [Fun](#fun)
- [Greetings](#greetings)
- [Leveling](#leveling)
- [Locks](#locks)
- [Logs](#logs)
- [Misc](#misc)
- [Moderation](#moderation)
- [Notes](#notes)
- [Owner](#owner)
- [Pins](#pins)
- [Profile](#profile)
- [Reports](#reports)
- [Rules](#rules)

---

## 📊 Statistics

- **Total Commands:** 124
- **Categories:** 22

## Admin

*4 commands in this category*

### `/adminlist`

**Description:** Show list of chat administrators

**Usage:** `/adminlist`

**Aliases:** `/admins`, `/staff`

---

### `/demote`

**Description:** Remove administrator privileges from a user

**Usage:** `/demote <reply|@username|ID>`

---

### `/promote`

**Description:** Promote a user to administrator

**Usage:** `/promote <reply|@username|ID> [custom title]`

**Aliases:** `/admin`

---

### `/slowmode`

**Description:** Set slowmode delay (Telegram native)

**Usage:** `/slowmode <seconds> - 0-21600 seconds`

**Aliases:** `/slow`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_restrict_members`

---

## Antiflood

*2 commands in this category*

### `/setflood`

**Description:** Set message flood limit

**Usage:** `/setflood <number> - Set max messages in timeframe
/setflood 0 or off - Disable antiflood`

**Aliases:** `/flood`

---

### `/setfloodmode`

**Description:** Set action for flood violators

**Usage:** `/setfloodmode <mode> - Set flood action
Modes: ban, mute, kick, tban, tmute`

**Aliases:** `/floodmode`

---

## Antiraid

*1 commands in this category*

### `/antiraid`

**Description:** Configure antiraid protection

**Usage:** `/antiraid <on/off> - Enable/disable raid protection
/antiraid - Check current status`

**Aliases:** `/setantiraid`, `/raidmode`

---

## Approval

*4 commands in this category*

### `/approve`

**Description:** Approve a user to bypass restrictions

**Usage:** `/approve <reply/username/mention/userid> - Whitelist user`

---

### `/approved`

**Description:** List all approved users in chat

**Usage:** `/approved - Show whitelisted users`

---

### `/unapprove`

**Description:** Remove user from approval whitelist

**Usage:** `/unapprove <reply/username/mention/userid>`

---

### `/unapproveall`

**Description:** Remove all users from approval whitelist

**Usage:** `/unapproveall - Clear all approvals`

---

## Blocklists

*3 commands in this category*

### `/addblocklist`

**Description:** Add word/phrase to blocklist

**Usage:** `/addblocklist <word/phrase> [reason]

Supports wildcards:
• ? = any single character
• * = any characters`

**Aliases:** `/addbl`

---

### `/blocklist`

**Description:** List all blocked words/phrases

**Usage:** `/blocklist - Show all blocklist triggers`

**Aliases:** `/blocklists`, `/bl`

---

### `/rmblocklist`

**Description:** Remove word/phrase from blocklist

**Usage:** `/rmblocklist <word/phrase>`

**Aliases:** `/removebl`, `/delbl`

---

## Captcha

*6 commands in this category*

### `/captcha`

**Description:** Configure captcha verification for new members

**Usage:** `/captcha <on/off> - Enable/disable captcha
/captcha - Check current settings`

**Aliases:** `/setcaptcha`

---

### `/captchamode`

**Description:** Set captcha verification type

**Usage:** `/captchamode <mode> - Set verification mode
Modes: math, button, text`

**Aliases:** `/setcaptchamode`

---

### `/captchastats`

**Description:** View captcha statistics

**Usage:** `/captchastats`

**Aliases:** `/captcha_stats`, `/captcha_statistics`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_restrict_members`

---

### `/pendingcaptcha`

**Description:** List users awaiting captcha verification

**Usage:** `/pendingcaptcha`

**Aliases:** `/pending_captcha`, `/captcha_pending`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_restrict_members`

---

### `/verify`

**Description:** Manually verify a user (skip captcha)

**Usage:** `/verify <reply/username/mention/userid>`

**Aliases:** `/manualverify`, `/skipcaptcha`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_restrict_members`

---

### `/whitelist`

**Description:** Whitelist/unwhitelist user from captcha

**Usage:** `/whitelist <user> or /unwhitelist <user>`

**Aliases:** `/unwhitelist`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_restrict_members`

---

## Economy

*7 commands in this category*

### `/balance`

**Description:** Check your or another user's balance

**Usage:** `/balance [@user]`

**Aliases:** `/bal`, `/wallet`, `/coins`

---

### `/daily`

**Description:** Claim your daily reward

**Usage:** `/daily - Claim 500 coins (once per day)`

**Aliases:** `/dailyreward`, `/claim`

---

### `/gamble`

**Description:** Gamble coins on a coin flip (50/50)

**Usage:** `/gamble <amount> - Double or nothing!`

**Aliases:** `/bet`

---

### `/richest`

**Description:** Show richest users by coins

**Usage:** `/richest - Show top 10 by coins`

**Aliases:** `/topmoney`, `/wealthiest`

---

### `/slots`

**Description:** Play the slot machine

**Usage:** `/slots <bet> - Bet coins to play`

**Aliases:** `/slot`

---

### `/transfer`

**Description:** Transfer coins to another user

**Usage:** `/transfer <@user> <amount>`

**Aliases:** `/pay`, `/send`, `/give`

---

### `/work`

**Description:** Work to earn coins (1 hour cooldown)

**Usage:** `/work - Earn 50-200 coins`

**Aliases:** `/job`

---

## Federation

*11 commands in this category*

### `/chatfed`

**Description:** Show this chat's federation

**Usage:** `/chatfed`

**Aliases:** `/thisfed`

---

### `/fban`

**Description:** Ban a user across all chats in the federation

**Usage:** `/fban <reply|@username|ID> [reason]`

**Aliases:** `/fedban`

---

### `/fedadmins`

**Description:** List federation admins

**Usage:** `/fedadmins [federation_id]`

**Aliases:** `/fadmins`

---

### `/feddemote`

**Description:** Demote a federation admin

**Usage:** `/feddemote <reply|@username|ID>`

**Aliases:** `/fdemote`

---

### `/fedinfo`

**Description:** Show federation information

**Usage:** `/fedinfo [federation_id]`

**Aliases:** `/federation_info`

---

### `/fedpromote`

**Description:** Promote a user to federation admin

**Usage:** `/fedpromote <reply|@username|ID>`

**Aliases:** `/fpromote`

---

### `/joinfed`

**Description:** Connect this chat to a federation

**Usage:** `/joinfed <federation_id>`

**Aliases:** `/connectfed`

---

### `/leavefed`

**Description:** Disconnect this chat from its federation

**Usage:** `/leavefed`

**Aliases:** `/disconnectfed`

---

### `/myfeds`

**Description:** Show federations you own or admin

**Usage:** `/myfeds`

**Aliases:** `/myfederations`

---

### `/newfed`

**Description:** Create a new federation

**Usage:** `/newfed <federation_name>`

**Aliases:** `/createfed`

---

### `/unfban`

**Description:** Unban a user from the federation

**Usage:** `/unfban <reply|@username|ID>`

**Aliases:** `/fedunban`

---

## Filters

*4 commands in this category*

### `/filter`

**Description:** Create a custom filter that auto-replies to trigger words

**Usage:** `/filter <trigger> - Reply to a message to set it as the response

<b>Features:</b>
• Supports text, media, buttons
• Use variables: {first}, {last}, {mention}, {username}
• Add buttons: [Text](buttonurl://url)
• Use :same for same row: [Text](buttonurl://url:same)

<b>Examples:</b>
• <code>/filter hello</code> - Reply with welcome message
• <code>/filter rules</code> - Reply with rules text`

---

### `/filters`

**Description:** List all active filters in the chat

**Usage:** `/filters - Show all filter triggers`

---

### `/stop`

**Description:** Remove a filter trigger

**Usage:** `/stop <trigger> - Delete the specified filter`

---

### `/stopall`

**Description:** Remove all filters from the chat

**Usage:** `/stopall - Delete all filter triggers`

---

## Fun

*12 commands in this category*

### `/8ball`

**Description:** Ask the magic 8-ball a question

**Usage:** `/8ball <question>`

**Aliases:** `/eightball`, `/fortune`

---

### `/choose`

**Description:** Randomly choose from options

**Usage:** `/choose <option1> <option2> ...`

**Aliases:** `/pick`, `/choice`

---

### `/coinflip`

**Description:** Flip a coin - heads or tails

**Usage:** `/coinflip`

**Aliases:** `/flip`, `/coin`

---

### `/compliment`

**Description:** Compliment someone

**Usage:** `/compliment [@user]`

**Aliases:** `/praise`, `/nice`

---

### `/fact`

**Description:** Get a random interesting fact

**Usage:** `/fact - Random fact`

**Aliases:** `/funfact`

---

### `/joke`

**Description:** Get a random joke

**Usage:** `/joke - Random joke`

---

### `/quote`

**Description:** Get an inspirational quote

**Usage:** `/quote - Random quote`

**Aliases:** `/inspire`

---

### `/roast`

**Description:** Roast someone (in good fun!)

**Usage:** `/roast [@user]`

**Aliases:** `/burn`

---

### `/roll`

**Description:** Roll dice or generate random numbers

**Usage:** `/roll [max] or /roll [min] [max]`

**Aliases:** `/dice`, `/rand`

---

### `/rps`

**Description:** Play Rock Paper Scissors

**Usage:** `/rps <rock/paper/scissors>`

**Aliases:** `/rockpaperscissors`

---

### `/ship`

**Description:** Check compatibility between two users

**Usage:** `/ship @user1 @user2`

**Aliases:** `/love`, `/compatibility`

---

### `/trivia`

**Description:** Answer trivia questions to earn coins

**Usage:** `/trivia - Random question (earn 50-200 coins)`

**Aliases:** `/quiz`

---

## Greetings

*7 commands in this category*

### `/cleanwelcome`

**Description:** Auto-delete welcome messages after 5 minutes

**Usage:** `/cleanwelcome <on/off>`

**Aliases:** `/cwelcome`, `/cleanwelcomes`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_delete_messages`

---

### `/goodbye`

**Description:** Toggle goodbye messages on/off

**Usage:** `/goodbye <on/off>`

**Aliases:** `/bye`, `/farewell`, `/goodbyes`, `/byebye`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_change_info`

---

### `/resetgoodbye`

**Description:** Reset goodbye message to default

**Usage:** `/resetgoodbye`

**Aliases:** `/resetbye`, `/cleargoodbye`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_change_info`

---

### `/resetwelcome`

**Description:** Reset welcome message to default

**Usage:** `/resetwelcome`

**Aliases:** `/resetwel`, `/clearwelcome`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_change_info`

---

### `/setgoodbye`

**Description:** Set a custom goodbye message

**Usage:** `/setgoodbye <text> or reply to a message`

**Aliases:** `/setbye`, `/goodbyemsg`, `/byemsg`

**Permission:** Admin only 🔒

**Scope:** Groups only 👥

**Required Permissions:** `can_change_info`

---

### `/setwelcome`

**Description:** Set a custom welcome message for new members

**Usage:** `/setwelcome - Reply to a message to set it as welcome

<b>Supported variables:</b>
• {first} - User's first name
• {last} - User's last name
• {fullname} - Full name
• {username} - Username with @
• {mention} - Mention user
• {id} - User ID
• {chatname} - Chat name
• {count} - Member count

<b>Buttons:</b> [Text](buttonurl://url)`

**Aliases:** `/setwelcomemsg`, `/welcomemsg`

---

### `/welcome`

**Description:** Enable/disable welcome messages for new members

**Usage:** `/welcome <on/off> - Toggle welcome messages
/welcome - Show current welcome message

To set a custom welcome message, use /setwelcome`

---

## Leveling

*4 commands in this category*

### `/leaderboard`

**Description:** Show top users by XP

**Usage:** `/leaderboard - Show top 10 users`

**Aliases:** `/top`, `/lb`, `/top10`

---

### `/rank`

**Description:** Show your or another user's rank and stats

**Usage:** `/rank [@user]`

**Aliases:** `/level`, `/xp`, `/myrank`

---

### `/setxp`

**Description:** Set a user's XP (admin only)

**Usage:** `/setxp <@user> <amount>`

---

### `/topchat`

**Description:** Show top users in this chat by XP

**Usage:** `/topchat - Show top 10 in this chat`

**Aliases:** `/chatleaderboard`, `/chatlb`

**Scope:** Groups only 👥

---

## Locks

*6 commands in this category*

### `/lock`

**Description:** Lock a content type to restrict it

**Usage:** `/lock <type> - Lock a content type
/lock media - Lock all media
/lock all - Lock everything`

---

### `/lockchat`

**Description:** Lock the chat - only admins can send messages

**Usage:** `/lockchat - Restrict all messages from non-admins`

**Aliases:** `/lockall`

---

### `/locks`

**Description:** Show current lock status

**Usage:** `/locks - Show all locked content types`

---

### `/locktypes`

**Description:** Show all available lock types

**Usage:** `/locktypes - List all lockable content types`

---

### `/unlock`

**Description:** Unlock a content type to allow it

**Usage:** `/unlock <type> - Unlock a content type
/unlock media - Unlock all media
/unlock all - Unlock everything`

---

### `/unlockchat`

**Description:** Unlock the chat - remove all locks

**Usage:** `/unlockchat - Remove all content restrictions`

**Aliases:** `/unlockall`

---

## Logs

*3 commands in this category*

### `/setlog`

**Description:** Set log channel for admin actions

**Usage:** `/setlog - Use in the log channel you want to set`

**Aliases:** `/set_log`

---

### `/setlogchannel`

**Description:** Set log channel by ID

**Usage:** `/setlogchannel <channel_id>`

---

### `/unsetlog`

**Description:** Remove log channel

**Usage:** `/unsetlog - Stop logging to channel`

---

## Misc

*4 commands in this category*

### `/help`

**Description:** Show available commands and their usage

**Usage:** `/help [command_name]`

**Aliases:** `/commands`

---

### `/id`

**Description:** Get user and chat ID information

**Usage:** `/id [reply|@username|ID]`

**Aliases:** `/info`

---

### `/ping`

**Description:** Check if bot is responsive

**Usage:** `/ping`

---

### `/start`

**Description:** Start the bot and get welcome message

**Usage:** `/start`

---

## Moderation

*12 commands in this category*

### `/ban`

**Description:** Ban a user from the chat

**Usage:** `/ban <reply|@username|ID> [duration] [reason]
/tban <reply|@username|ID> <duration> [reason] - Temporary ban
/sban <reply|@username|ID> [duration] [reason] - Silent ban (no message)
/dban <reply|@username|ID> [duration] [reason] - Delete message and ban`

**Aliases:** `/tban`, `/sban`, `/dban`

---

### `/kick`

**Description:** Kick a user from the chat

**Usage:** `/kick <reply|@username|ID> [reason]
/skick <reply|@username|ID> [reason] - Silent kick (no message)
/dkick <reply|@username|ID> [reason] - Delete message and kick`

**Aliases:** `/skick`, `/dkick`

---

### `/mute`

**Description:** Mute a user in the chat

**Usage:** `/mute <reply|@username|ID> [duration] [reason]
/tmute <reply|@username|ID> <duration> [reason] - Temporary mute
/smute <reply|@username|ID> [duration] [reason] - Silent mute (no message)
/dmute <reply|@username|ID> [duration] [reason] - Delete message and mute`

**Aliases:** `/tmute`, `/smute`, `/dmute`

---

### `/purge`

**Description:** Delete messages in bulk

**Usage:** `/purge - Reply to a message to delete all messages from that message to latest
/del - Reply to a message to delete only that message`

**Aliases:** `/del`

---

### `/resetwarn`

**Description:** Clear all warnings from a user

**Usage:** `/resetwarn <reply|@username|ID>`

**Aliases:** `/resetwarns`, `/clearwarnings`

---

### `/rmwarn`

**Description:** Remove the last warning from a user

**Usage:** `/rmwarn <reply|@username|ID>`

**Aliases:** `/unwarn`, `/removewarn`

---

### `/unban`

**Description:** Unban a user from the chat

**Usage:** `/unban <reply|@username|ID>`

**Aliases:** `/pardon`

---

### `/unmute`

**Description:** Unmute a user in the chat

**Usage:** `/unmute <reply|@username|ID>`

---

### `/warn`

**Description:** Warn a user

**Usage:** `/warn <reply|@username|ID> [reason]`

**Aliases:** `/swarn`

---

### `/warnlimit`

**Description:** Set warning limit before action is taken

**Usage:** `/warnlimit <number>`

**Aliases:** `/setwarnlimit`, `/maxwarns`

---

### `/warnmode`

**Description:** Set action when warning limit is reached

**Usage:** `/warnmode <ban|kick|mute>`

**Aliases:** `/setwarnmode`

---

### `/warns`

**Description:** Show warnings for a user

**Usage:** `/warns [reply|@username|ID]`

**Aliases:** `/warnings`

---

## Notes

*5 commands in this category*

### `/clear`

**Description:** Remove a saved note

**Usage:** `/clear <notename> - Delete the specified note`

---

### `/clearall`

**Description:** Remove all notes from the chat

**Usage:** `/clearall - Delete all saved notes`

---

### `/get`

**Description:** Retrieve a saved note

**Usage:** `/get <notename> - Get the specified note

You can also use #notename as a shortcut`

---

### `/notes`

**Description:** List all saved notes in the chat

**Usage:** `/notes - Show all note names`

---

### `/save`

**Description:** Save a note that can be retrieved later

**Usage:** `/save <notename> - Reply to a message to save it as a note

<b>Features:</b>
• Supports text, media, buttons
• Use variables: {first}, {last}, {mention}, {username}
• Add buttons: [Text](buttonurl://url)
• Retrieve with /get or #notename

<b>Examples:</b>
• <code>/save rules</code> - Save chat rules
• <code>/save welcome</code> - Save welcome message`

---

## Owner

*16 commands in this category*

### `/botinfo`

**Description:** Get detailed bot information

**Usage:** `/botinfo`

**Aliases:** `/about`, `/botdetails`

---

### `/broadcast`

**Description:** Broadcast a message to all chats/users

**Usage:** `/broadcast <chats|users|all> <message>
Reply to a message with /broadcast <target>`

**Aliases:** `/announce`

---

### `/chatlist`

**Description:** List all chats bot is in

**Usage:** `/chatlist`

**Aliases:** `/chats`, `/listchats`

---

### `/clearcache`

**Description:** Clear bot cache

**Usage:** `/clearcache`

**Aliases:** `/cc`, `/flushcache`

---

### `/dbbackup`

**Description:** Create and send database backup

**Usage:** `/dbbackup`

**Aliases:** `/fullbackup`, `/dbexport`

---

### `/eval`

**Description:** Execute Python code (DANGEROUS)

**Usage:** `/eval <code>`

**Aliases:** `/exec`, `/py`

---

### `/gban`

**Description:** Globally ban a user from all chats

**Usage:** `/gban <reply|@username|ID> [reason]`

**Aliases:** `/globalban`

---

### `/gbanlist`

**Description:** List all globally banned users

**Usage:** `/gbanlist`

**Aliases:** `/gbans`, `/globalbans`

---

### `/leavechat`

**Description:** Make bot leave a specific chat

**Usage:** `/leavechat <chat_id>`

**Aliases:** `/leave`

---

### `/logs`

**Description:** Get recent bot logs

**Usage:** `/logs [lines]`

**Aliases:** `/getlogs`, `/log`

---

### `/maintenance`

**Description:** Enable/disable maintenance mode

**Usage:** `/maintenance <on|off> [reason]`

**Aliases:** `/maint`

---

### `/ownerping`

**Description:** Check bot latency (owner)

**Usage:** `/ownerping`

**Aliases:** `/opping`, `/botlatency`

---

### `/shell`

**Description:** Execute shell commands (EXTREMELY DANGEROUS)

**Usage:** `/shell <command>`

**Aliases:** `/sh`, `/bash`

---

### `/stats`

**Description:** Get detailed bot statistics

**Usage:** `/stats`

**Aliases:** `/botstats`, `/statistics`

---

### `/sysinfo`

**Description:** Get system resource usage

**Usage:** `/sysinfo`

**Aliases:** `/system`, `/health`

---

### `/ungban`

**Description:** Remove global ban from a user

**Usage:** `/ungban <reply|@username|ID>`

**Aliases:** `/unglobalban`

---

## Pins

*5 commands in this category*

### `/permapin`

**Description:** Pin a message permanently (prevents channel auto-unpin)

**Usage:** `/permapin [notify] - Reply to a message to pin it permanently
/permapin [notify] - Pin with notification (default: silent)

This prevents the message from being unpinned by linked channels`

---

### `/pin`

**Description:** Pin a message in the chat

**Usage:** `/pin [notify] - Reply to a message to pin it
/pin [notify] - Pin with notification (default: silent)`

---

### `/unpermapin`

**Description:** Disable permanent pin for the current message

**Usage:** `/unpermapin - Disable permapin protection`

---

### `/unpin`

**Description:** Unpin the current pinned message

**Usage:** `/unpin - Unpin the currently pinned message
/unpin - Reply to a pinned message to unpin it specifically`

---

### `/unpinall`

**Description:** Unpin all pinned messages in the chat

**Usage:** `/unpinall - Remove all pinned messages`

---

## Profile

*3 commands in this category*

### `/profile`

**Description:** View user profile

**Usage:** `/profile [@user] - View profile`

**Aliases:** `/me`, `/myprofile`

---

### `/rep`

**Description:** Give reputation point (1 per 24h)

**Usage:** `/rep <user> - Give +1 rep`

**Aliases:** `/reputation`

**Scope:** Groups only 👥

---

### `/setbio`

**Description:** Set your profile bio

**Usage:** `/setbio <text> - Max 200 characters`

**Aliases:** `/bio`

---

## Reports

*1 commands in this category*

### `/reports`

**Description:** Toggle user reports in chat

**Usage:** `/reports <on/off> - Enable/disable user reports`

**Aliases:** `/report_toggle`

---

## Rules

*4 commands in this category*

### `/privaterules`

**Description:** Toggle sending rules in PM instead of chat

**Usage:** `/privaterules <on/off> - Toggle private rules`

**Aliases:** `/private_rules`

---

### `/resetrules`

**Description:** Clear chat rules

**Usage:** `/resetrules - Remove the chat rules`

**Aliases:** `/clear_rules`

---

### `/rules`

**Description:** View chat rules

**Usage:** `/rules - Show the chat rules`

---

### `/setrules`

**Description:** Set chat rules

**Usage:** `/setrules <text> - Reply to message or provide text

Example:
/setrules 1. Be respectful
2. No spam
3. No NSFW content`

**Aliases:** `/set_rules`

---

## 📝 Notes

- Commands marked with 🔒 require admin permissions
- Commands marked with 👑 are owner-only
- Commands marked with 👥 work only in groups
- Use `/help <command>` to get detailed help for a specific command

---

*This documentation was automatically generated from command source files.*
