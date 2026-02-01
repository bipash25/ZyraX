# ZyraX — Continuation & Expansion Plan

> **Document purpose:** This plan picks up exactly where the current codebase leaves off. Everything confirmed by the README as already shipped is marked clearly. Everything else is the remaining roadmap, re-prioritized around the existing architecture (Pyrogram / MongoDB / FastAPI).

---

## 1. Current State — What's Already Built

The following is extracted directly from the README and represents the confirmed, shipped baseline. No assumptions are made beyond what is explicitly documented.

### 1.1 Architecture & Infrastructure ✅

| Layer | What's In Place |
|---|---|
| Language & Runtime | Python 3.11+ |
| Telegram Framework | **Pyrogram** (MTProto protocol, not Bot API) |
| Database | **MongoDB** via Motor (async driver) |
| Cache | **Redis** |
| Web Dashboard | **FastAPI + Jinja2 + TailwindCSS** — live at `localhost:8080` |
| Deployment | **Docker + Docker Compose** |
| Module System | Auto-discovery plugin architecture — drop a `.py` into `zyrax/modules/`, define `__mod_name__` and `__help__`, it loads automatically |

### 1.2 Shipped Modules & Commands ✅

| Module | Confirmed Features |
|---|---|
| **Moderation** | `/ban`, `/kick`, `/mute` (with `ChatPermissions`), `/promote`, `/demote`, admin lists |
| **Warnings** | Database-backed warn system with configurable auto-ban thresholds |
| **Federations** | `/newfed`, `/fban` — cross-chat ban system |
| **Notes** | `/save`, `/get` — save and retrieve messages/media |
| **Filters** | Auto-reply on keyword triggers (text and media) |
| **Anti-Flood** | Configurable spam protection |
| **AI — Chat** | `/ask` — ChatGPT integration |
| **AI — Images** | `/imagine` — DALL-E image generation |
| **Tournaments** | `/tourney`, `/bracket` — bracket-style tournament creation and management |
| **Games** | Dice, Darts, Rock-Paper-Scissors |
| **Entertainment** | Meme generator, Joke generator |
| **Webhooks** | Webhook receiver for external integrations (GitHub, Trello, etc.) |
| **Dashboard** | Web UI with real-time stats (command usage, active chats, user growth) |
| **Premium System** | Monetization / subscription management pages in the dashboard |

### 1.3 Key Architectural Decisions Already Made

These are locked in by the existing codebase. The continuation plan works *with* them, not around them.

- **Pyrogram over python-telegram-bot.** Pyrogram uses the MTProto protocol directly, which gives access to features the Bot API does not (e.g., reading messages without being mentioned, accessing full chat history). This is a significant advantage for analytics, filters, and moderation — but it also means the bot runs as a *user client* alongside a bot token, which has different rate-limit and permission characteristics than a pure Bot API bot.
- **MongoDB over PostgreSQL.** The original project plan specified PostgreSQL + SQLAlchemy. The actual build chose MongoDB + Motor. This is a document-oriented model — it's faster to iterate on schemas (no migrations needed), and it fits naturally for the nested, per-group configuration data ZyraX stores. The continuation plan operates entirely within MongoDB.
- **FastAPI dashboard already exists.** A full web frontend is already shipped. New analytics, moderation logs, and admin features should be surfaced here rather than building a parallel system.
- **Plugin auto-discovery is live.** Every new module is just a file. No registration step, no import map to update. This dramatically reduces the per-feature effort for everything that follows.

---

## 2. Gap Analysis — What Remains

This section maps the original 500+ feature list against the confirmed baseline. Features are grouped by the module they belong to, and each is tagged with a priority tier.

**Tier Legend:**
- 🔴 **T1 — Essential** — Core functionality gaps; should be closed immediately
- 🟠 **T2 — Important** — High-value features that deepen the existing modules
- 🟢 **T3 — Enhanced** — Significant new capability areas
- 🔵 **T4 — Premium** — Advanced or resource-intensive features

---

### 2.1 Moderation & Security — Gaps

Already shipped: ban, kick, mute, promote, demote, warns with auto-ban, anti-flood, federations (basic).

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 1 | `/unban`, `/unmute` commands | 🔴 T1 | Basic inverse actions — must exist alongside ban/mute |
| 2 | Temporary bans and mutes with duration (`/tban 2h`) | 🔴 T1 | Auto-lift after duration; tracked in DB |
| 3 | Soft ban (ban + immediate unban to clear messages) | 🔴 T1 | Common moderation technique |
| 4 | `/warn` removal and reset (`/unwarn`, `/resetwarns`) | 🔴 T1 | Warn system exists but removal commands are not documented |
| 5 | Silent warnings (no public notification) | 🟠 T2 | `/swarn` — warn via private message only |
| 6 | Warning notes (attach a reason visible to admins) | 🟠 T2 | Stored per-warn in the DB document |
| 7 | Report system (`/report`) | 🟠 T2 | Flags a message for admin review; optionally notifies admins |
| 8 | Anti-raid mode (temporary group lockdown) | 🟠 T2 | Triggered manually or auto on mass-join detection |
| 9 | Join captcha (math, button, image, question) | 🟠 T2 | Currently only anti-flood exists; captcha is a separate layer |
| 10 | Captcha timeout + auto-kick | 🟠 T2 | If not solved within N seconds, kick the user |
| 11 | Anti-bot join (auto-remove bots unless admin) | 🟠 T2 | |
| 12 | Anti-forward (block forwarded messages from channels) | 🟠 T2 | |
| 13 | Anti-external links (configurable whitelist) | 🟠 T2 | Scam/phishing/malware link scanning |
| 14 | Anti-sticker / GIF / media / emoji spam | 🟠 T2 | Anti-flood exists but media-type-specific limits do not |
| 15 | Mention spam / hashtag spam protection | 🟠 T2 | |
| 16 | Caps lock detection | 🟠 T2 | |
| 17 | Profanity filter with custom word lists | 🟠 T2 | |
| 18 | Regex-based content filtering | 🟠 T2 | Filters exist for auto-reply; this is for moderation blocking |
| 19 | Slowmode configuration | 🟠 T2 | |
| 20 | Message length limits | 🟠 T2 | |
| 21 | Auto-delete service messages (join/leave) | 🟠 T2 | |
| 22 | Voice / video message blocking | 🟠 T2 | |
| 23 | Anonymous admin actions | 🟢 T3 | Actions appear as "Group Admin" not the real username |
| 24 | Federation — fed-wide warnings | 🟢 T3 | `/fban` exists; `/fwarn` does not |
| 25 | Federation — import/export ban lists | 🟢 T3 | |
| 26 | Federation — broadcast messages | 🟢 T3 | |
| 27 | Federation — admin management & statistics | 🟢 T3 | |

---

### 2.2 User Management — Gaps

No user management module is documented in the README beyond promote/demote.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 28 | User info command (`/info`) — ID, username, join date | 🔴 T1 | Fundamental utility |
| 29 | User statistics (messages sent, warnings received) | 🟠 T2 | Requires message counting via Pyrogram |
| 30 | First seen / last seen tracking | 🟠 T2 | |
| 31 | Karma / reputation system (`/karma`, `+1`) | 🟠 T2 | |
| 32 | User levels and ranks (activity-based) | 🟢 T3 | Ties into XP / economy later |
| 33 | Badges and achievements | 🟢 T3 | |
| 34 | Leaderboards (most active, highest karma) | 🟢 T3 | |
| 35 | VIP / Premium user system | 🟢 T3 | Ties into the existing Premium/monetization dashboard |
| 36 | Blacklist / whitelist users | 🟠 T2 | |
| 37 | Admin notes on users (`/addnote @user`) | 🟠 T2 | Different from message notes — these are per-user annotations |
| 38 | User tags system | 🟢 T3 | |

---

### 2.3 Welcome & Member Management — Gaps

No welcome/goodbye system is documented.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 39 | Welcome messages (text, media, buttons) | 🔴 T1 | One of the most-used bot features in any group |
| 40 | Goodbye messages | 🔴 T1 | |
| 41 | Custom welcome message editor (`/setwelcome`) | 🔴 T1 | With variable support: `{first}`, `{username}`, `{mention}` |
| 42 | Rules command (`/rules`) with private-button option | 🔴 T1 | |
| 43 | Welcome mute (new users muted until they click a button) | 🟠 T2 | |
| 44 | Clean welcome (auto-delete old welcome messages) | 🟠 T2 | |
| 45 | New user media lockout (can't send media for X minutes) | 🟠 T2 | |
| 46 | Random welcome messages (rotate from a pool) | 🟢 T3 | |

---

### 2.4 Notes & Filters — Gaps

`/save` and `/get` exist. Filters (auto-reply) exist. But the system is basic.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 47 | Private notes (admin-only visibility) | 🟠 T2 | |
| 48 | Button notes (inline keyboard attached to the note) | 🟠 T2 | |
| 49 | Fillings / variables in notes (`{first}`, `{mention}`, etc.) | 🟠 T2 | |
| 50 | List all notes (`/notes`) | 🟠 T2 | |
| 51 | Import / export notes (JSON) | 🟢 T3 | |
| 52 | Regex filter support | 🟠 T2 | |
| 53 | Filter statistics (how often each filter fires) | 🟢 T3 | |
| 54 | Blacklist system (block words → action: delete/warn/ban/mute/kick) | 🟠 T2 | Distinct from profanity filter — this is configurable per-action |

---

### 2.5 Games & Economy — Gaps

Dice, Darts, and RPS exist. Tournaments exist. Everything else is missing.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 55 | Trivia quiz with categories | 🟠 T2 | High-engagement; needs an API or bundled question set |
| 56 | Hangman | 🟠 T2 | |
| 57 | Word scramble | 🟠 T2 | |
| 58 | Guess the number | 🟠 T2 | |
| 59 | Truth or Dare | 🟠 T2 | Needs a content database |
| 60 | Would You Rather | 🟠 T2 | |
| 61 | Tic-Tac-Toe (two-player, inline) | 🟠 T2 | |
| 62 | 20 Questions | 🟠 T2 | |
| 63 | Riddles | 🟠 T2 | |
| 64 | Connect Four | 🟢 T3 | Two-player grid game |
| 65 | Blackjack / 21 | 🟢 T3 | |
| 66 | Poker | 🟢 T3 | |
| 67 | Chess (PGN notation, two-player) | 🟢 T3 | |
| 68 | Russian Roulette | 🟢 T3 | |
| 69 | Slot machine | 🟢 T3 | Ties into economy |
| 70 | Daily challenges | 🟢 T3 | |
| 71 | Per-game leaderboards | 🟢 T3 | |
| 72 | Full economy system (currency, bank, shop, gambling, auctions, trading) | 🟢 T3 | Large feature set — see Phase 4 |
| 73 | Leveling & XP system with prestige | 🟢 T3 | |

---

### 2.6 Fun & Entertainment — Gaps

Meme and joke generators exist. Everything else is missing.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 74 | Random facts, quotes, dad jokes, puns | 🟠 T2 | |
| 75 | Random dog/cat/anime pictures | 🟠 T2 | Public APIs available |
| 76 | Coinflip, 8ball, fortune cookie, horoscope | 🟠 T2 | |
| 77 | Ship / love calculator | 🟠 T2 | |
| 78 | Action commands (slap, hug, kiss, pat) with GIFs | 🟠 T2 | |
| 79 | Text manipulation (reverse, Morse, leetspeak, Zalgo, mock, ASCII art, etc.) | 🟠 T2 | |
| 80 | Story / poem / rap battle / roast generators | 🟢 T3 | Can leverage the existing `/ask` ChatGPT integration |
| 81 | Choose between options (`/choose a, b, c`) | 🟠 T2 | |

---

### 2.7 Utilities — Gaps

No utility module is documented.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 82 | Wikipedia search | 🟠 T2 | |
| 83 | Weather (current + forecast) | 🟠 T2 | |
| 84 | Translation (multi-language) | 🟠 T2 | |
| 85 | Currency converter (real-time) | 🟠 T2 | |
| 86 | Crypto prices | 🟠 T2 | |
| 87 | Calculator (scientific) | 🟠 T2 | |
| 88 | Unit converter | 🟠 T2 | |
| 89 | QR code generator / reader | 🟠 T2 | |
| 90 | URL shortener / expander | 🟢 T3 | |
| 91 | Reminder system | 🟠 T2 | Needs a scheduler — can use the existing Redis + a worker loop |
| 92 | Poll creator (advanced, anonymous) | 🟠 T2 | |
| 93 | To-do list | 🟠 T2 | |
| 94 | Password / hash generator | 🟠 T2 | |
| 95 | Age / BMI / tip / loan calculators | 🟠 T2 | |
| 96 | Time zone converter | 🟠 T2 | |
| 97 | News headlines (by category/country) | 🟢 T3 | |
| 98 | IP / WHOIS / DNS lookup | 🟢 T3 | |
| 99 | GitHub repo info | 🟢 T3 | |
| 100 | Package / flight tracking | 🟢 T3 | |
| 101 | IMDB / anime / recipe / book / lyrics search | 🟢 T3 | |

---

### 2.8 Media Tools — Gaps

No media processing module is documented.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 102 | Image → sticker converter | 🟠 T2 | |
| 103 | OCR (text extraction from images) | 🟠 T2 | |
| 104 | Image resize / compress | 🟠 T2 | |
| 105 | Video → GIF / GIF → video | 🟢 T3 | Needs FFmpeg |
| 106 | Remove image background | 🟢 T3 | API-based |
| 107 | Meme generator (template-based) | 🟢 T3 | |
| 108 | Social media downloaders (YouTube, Instagram, TikTok, Twitter) | 🟢 T3 | yt-dlp based |
| 109 | AI image upscaling | 🔵 T4 | GPU-dependent |

---

### 2.9 Analytics & Logging — Gaps

The dashboard shows real-time stats (command usage, active chats, user growth). But the underlying analytics engine and logging system are not detailed.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 110 | Per-user message counts & most-active users | 🟠 T2 | |
| 111 | Activity heatmap (most active hours/days) | 🟢 T3 | |
| 112 | Word cloud generator | 🟢 T3 | |
| 113 | Group growth tracking & join/leave stats | 🟠 T2 | |
| 114 | Deleted / edited messages log | 🟠 T2 | Pyrogram can capture these |
| 115 | Admin action audit log | 🟠 T2 | |
| 116 | Export logs as CSV / JSON | 🟢 T3 | |
| 117 | Visual charts in dashboard (beyond current stats) | 🟢 T3 | |

---

### 2.10 AI & Automation — Gaps

`/ask` (ChatGPT) and `/imagine` (DALL-E) exist. Webhook receiver exists.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 118 | AI-based toxicity / NSFW detection for auto-moderation | 🟢 T3 | Can use OpenAI moderation API |
| 119 | Sentiment analysis | 🟢 T3 | |
| 120 | Auto-translation in multilingual groups | 🟢 T3 | |
| 121 | Document / long-text summarization | 🟢 T3 | Extension of `/ask` |
| 122 | Scheduled messages (cron-style) | 🟢 T3 | |
| 123 | RSS feed reader → auto-post | 🟢 T3 | |
| 124 | GitHub / GitLab / Twitch / YouTube webhook events | 🟢 T3 | Webhook receiver exists; needs event parsing per service |
| 125 | Trigger-action automation system | 🔵 T4 | |
| 126 | Local Stable Diffusion (GPU, as fallback/supplement to DALL-E) | 🔵 T4 | GT 730 — SD 1.5 only |

---

### 2.11 Music — Gaps

No music module exists.

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 127 | Voice chat music player (YouTube, Spotify, SoundCloud) | 🟢 T3 | Pyrogram supports voice chats natively — significant advantage over Bot API |
| 128 | Queue management (add, skip, pause, resume, stop, shuffle, loop) | 🟢 T3 | |
| 129 | Volume control / seek | 🟢 T3 | |
| 130 | Now playing + lyrics display | 🟢 T3 | |
| 131 | Audio download | 🟢 T3 | |
| 132 | Audio processing (trim, merge, speed, pitch, format convert) | 🔵 T4 | FFmpeg-based |
| 133 | Radio stream support | 🔵 T4 | |

---

### 2.12 Security & Privacy — Gaps

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 134 | GDPR compliance (data export + deletion) | 🟢 T3 | |
| 135 | 2FA for owner/super-admin commands | 🟢 T3 | |
| 136 | Audit log for all admin actions | 🟠 T2 | Ties into #115 |
| 137 | Security alerts for suspicious activity | 🟢 T3 | |
| 138 | Encrypted backup system | 🟢 T3 | MongoDB has built-in backup tools; encrypt at rest |

---

### 2.13 Social & Community — Gaps

| # | Missing Feature | Tier | Notes |
|---|---|---|---|
| 139 | Birthday reminders | 🟠 T2 | |
| 140 | Group events calendar | 🟢 T3 | |
| 141 | Suggestion box / anonymous feedback | 🟢 T3 | |
| 142 | Secret Santa organizer | 🔵 T4 | |
| 143 | Collaborative stories | 🔵 T4 | |
| 144 | Hall of fame / Wall of shame | 🔵 T4 | |

---

## 3. Revised Roadmap

The roadmap below is structured around the *existing* architecture. Every phase assumes the plugin auto-discovery system, MongoDB, Pyrogram, and the FastAPI dashboard are already in place and functional.

Each phase ends with a **Dashboard Integration checkpoint** — new features get surfaced in the web UI where relevant.

---

### Phase 1 — Close the Critical Gaps (Weeks 1–2)

**Goal:** Fill every T1 gap. After this phase, ZyraX has no embarrassing missing basics.

**Moderation completions:**
- `/unban`, `/unmute`
- Temporary bans and mutes with duration parsing (`/tban 2h @user`)
- Soft ban
- `/unwarn`, `/resetwarns`

**User & welcome system (new modules):**
- `/info` — user ID, username, join date, first seen
- Welcome and goodbye messages with variable support (`{first}`, `{username}`, `{mention}`, `{chatname}`)
- `/setwelcome`, `/setgoodbye`, `/delwelcome`, `/delgoodbye`
- `/rules` with private-button option

**Module files to create:**
- `zyrax/modules/welcome.py`
- `zyrax/modules/userinfo.py`

**Testing:** Each command tested in a private group. Temporary bans verified to auto-lift. Welcome messages verified with variables populated correctly.

---

### Phase 2 — Anti-Spam Suite & Moderation Depth (Weeks 3–5)

**Goal:** Turn the moderation system from "basic" to "production-hardened." This is what keeps groups safe from raids, spam bots, and link scammers.

**New modules / expansions:**
- **Captcha system** — button-based (default), math, custom question. Configurable timeout with auto-kick. (`zyrax/modules/captcha.py`)
- **Anti-spam expansion** — per-type limits on stickers, GIFs, media, emojis, mentions, hashtags. Each type is independently configurable per group.
- **Link scanning** — scam/phishing/malware URL detection (via a public blocklist API or a curated list). Anti-forward from channels. Anti-external links with a whitelist.
- **Content filters** — caps lock detection, repeated characters, profanity filter with custom word lists, regex-based blocking (distinct from auto-reply filters).
- **Blacklist system** — `/blacklist add <word> <action>` where action is delete / warn / ban / mute / kick. (`zyrax/modules/blacklist.py`)
- **Report system** — `/report` flags a message and notifies group admins.
- **Anti-raid mode** — manual trigger (`/raid on`) or auto-trigger on mass-join; locks the group for a configurable duration.
- **Silent warnings** — `/swarn @user <reason>` — warns via DM only.
- **Warning notes** — reason text stored and retrievable per warning.
- **Slowmode & message length limits** — configurable per group.
- **Auto-delete** — service messages (join/leave), voice messages, video messages (configurable).

**Dashboard integration:** Add a "Moderation Log" page showing recent bans, kicks, warns, and reports with timestamps and admin who performed the action.

---

### Phase 3 — Notes, Filters & User Depth (Weeks 6–7)

**Goal:** Make the notes and filters system robust. Build the user identity layer that games and economy will sit on top of.

**Notes & filters expansion:**
- Private notes (admin-only)
- Button notes (inline keyboards)
- Variable fillings in notes
- `/notes` list command
- Regex filter support
- Filter hit statistics (tracked in MongoDB, surfaced in dashboard)
- Import / export notes as JSON

**User system expansion:**
- First seen / last seen tracking (stored on every message event)
- Message count per user (incremented via a Pyrogram message handler — this is where Pyrogram's ability to see all messages pays off)
- Karma system — `+1` or `/karma @user` to give karma; `/karma` to check your own
- Blacklist / whitelist users
- Admin notes on users (`/addnote @user <text>`, `/notes @user`)
- Welcome mute system (new users muted until they click a verification button)
- New user media lockout (configurable cooldown before media is allowed)

**Dashboard integration:** User profiles visible in the dashboard with stats, karma, and admin notes.

---

### Phase 4 — Games & Economy (Weeks 8–11)

**Goal:** The engagement layer. These features drive daily active usage and community interaction.

**New games** (each as a sub-module within `zyrax/modules/games/`):
- Trivia (categories, scoring, streak tracking) — uses a public trivia API or bundled JSON question sets
- Hangman
- Word scramble
- Guess the number
- Tic-Tac-Toe (two-player, rendered as a text grid with inline keyboard buttons)
- Truth or Dare (content database required — bundle a starter set, extend via API)
- Would You Rather
- 20 Questions
- Riddles (bundled set)
- Connect Four (two-player grid)
- Blackjack / 21
- Poker (simplified — Texas Hold'em, bot-managed deck)
- Chess (PGN notation, two-player, board rendered as text or image)
- Russian Roulette
- Slot machine
- Daily challenges (one per day, ties into economy rewards)

**Per-game leaderboards:** Each game tracks wins/scores in MongoDB. A unified `/leaderboard` command with game filter. Leaderboard page added to dashboard.

**Economy system** (new module: `zyrax/modules/economy.py`):
- Virtual currency (ZyraCoins)
- Daily and hourly rewards
- `/work` — earn coins (random amount + cooldown)
- `/beg` — chance to earn or lose coins
- `/rob @user` — attempt to steal coins (chance of failure + penalty)
- `/gamble <amount>` — coin flip bet
- `/lottery` — buy tickets, periodic draw
- `/bank` — deposit / withdraw (safe from robbery)
- `/shop` — buy items (cosmetic badges, XP boosts, etc.)
- `/inventory` — view owned items
- `/gift @user <amount>` — transfer coins
- `/trade` — item trading between users
- `/auction` — list items for auction; other users bid
- Rich list leaderboard

**Leveling system:**
- XP earned from messages (configurable rate per group)
- Level-up notifications with a customizable message
- Level-based role assignment (auto-promote at certain levels)
- Prestige system (reset level for a permanent badge)
- Profile card generator (text-based summary of user stats)

**Dashboard integration:** Economy stats page — total coins in circulation, most active traders, shop inventory management.

---

### Phase 5 — Fun, Utilities & Media (Weeks 12–14)

**Goal:** Make ZyraX genuinely useful beyond moderation and games. This is the "do everything" phase.

**Fun commands** (new module: `zyrax/modules/fun.py`):
- Random facts, quotes, dad jokes, puns, shower thoughts
- Random dog / cat / anime pictures (public APIs)
- Coinflip, 8ball, fortune cookie, horoscope
- Ship / love calculator
- Action commands with GIFs (slap, hug, kiss, pat) — sourced from a GIF API
- `/choose a, b, c` — pick one at random
- Text manipulation suite: reverse, Morse code, binary, leetspeak, Zalgo, mock (sPoNgEbOb), uppercase/lowercase, bubble text, cursive, strikethrough
- Story / poem / roast / rap battle generators — routed through the existing `/ask` ChatGPT backend, so no new AI integration needed

**Utilities** (new module: `zyrax/modules/utilities.py`):
- Wikipedia search (`/wiki <query>`)
- Weather — current + 5-day forecast (`/weather <city>`)
- Translation (`/translate <lang> <text>`) — Google Translate API or DeepL
- Currency converter — real-time rates (`/convert 100 USD EUR`)
- Crypto prices (`/crypto BTC`)
- Scientific calculator (`/calc <expression>`)
- Unit converter (`/unit 5km mi`)
- QR code generator and reader
- Reminder system (`/remind 2h do the thing`) — scheduled via a lightweight async loop or APScheduler; stored in MongoDB
- Advanced polls (`/poll` with multiple options, anonymous mode, deadline)
- To-do list (`/todo add`, `/todo list`, `/todo done`)
- Password generator, hash generator (MD5, SHA256, etc.)
- Age / BMI / tip / loan calculators
- Time zone converter
- Birthday reminders (set via `/birthday`, auto-notify on the day)

**Media tools** (new module: `zyrax/modules/media.py`):
- Image → sticker (`/tosticker`)
- OCR — extract text from images (`/ocr`) — via Google Cloud Vision API or a free alternative
- Image resize and compress
- Video → GIF and GIF → video (FFmpeg)
- Meme generator — template-based with overlaid text
- Social media downloaders — YouTube, Instagram, TikTok, Twitter via yt-dlp (`/dl <url>`)

**Dashboard integration:** Media processing queue visible in the dashboard. Utility command usage stats added to the analytics page.

---

### Phase 6 — Analytics, Logging & Dashboard Expansion (Weeks 15–16)

**Goal:** Turn the existing dashboard from a basic stats view into a full admin and analytics platform.

**Analytics engine:**
- Per-user message counts tracked on every message event (Pyrogram handler)
- Most active users ranking — per group and global
- Activity heatmap — hour-of-day × day-of-week matrix, stored as aggregated counts in MongoDB
- Group growth chart — join count minus leave count over time
- Join / leave event logging with timestamps
- Command usage statistics (already partially exists per the README — expand to per-group breakdown)

**Logging system:**
- Deleted messages log (Pyrogram fires an event on message deletion — capture and store)
- Edited messages log (capture original + edited text)
- Admin action audit log (every ban, kick, mute, promote, etc. logged with actor + target + timestamp + reason)
- Pin / unpin log
- Export any log as CSV or JSON (`/exportlogs <type> <days>`)

**Dashboard expansions:**
- Visual charts for all analytics (use a JS charting library — Chart.js or Recharts — already compatible with the FastAPI + Jinja2 stack)
- Moderation log page with filters (by action type, by admin, by date range)
- User profile pages (stats, karma, warnings, notes — admin-only)
- Log export buttons on every log page
- Activity heatmap visualization

---

### Phase 7 — AI Depth & Automation (Weeks 17–18)

**Goal:** Expand the AI layer beyond chat and image generation. Build the automation backbone.

**AI expansions:**
- AI-powered moderation — use OpenAI's Moderation API to auto-flag or auto-delete toxic / NSFW content. Configurable sensitivity per group.
- Sentiment analysis on messages (optional, per-group opt-in) — surfaced in analytics
- Auto-translation in multilingual groups — detect language, translate to group's primary language, post as a reply
- Document / long-text summarization — `/summarize` with pasted text or a forwarded long message. Routes through ChatGPT.
- Smart reply suggestions — when a message is detected as a question, suggest a reply (shown only to the sender, not posted)

**Automation system** (expand `zyrax/modules/` with `automation.py`):
- Scheduled messages — `/schedule <date/time> <message>` — stored in MongoDB, fired by an async scheduler
- RSS feed reader — `/rss add <url>` — polls feeds on a configurable interval, auto-posts new items to the group
- Webhook event parsing — the webhook receiver already exists; add structured handlers for GitHub (push, PR, issue), GitLab, Twitch (stream live), YouTube (new video). Each event type is formatted and posted to the group.
- Auto-response templates — `/autoresponse add <trigger> <response>` — more structured than filters; supports variables and conditions

---

### Phase 8 — Music Player (Weeks 19–20)

**Goal:** Full voice chat music player. This is placed last because it is the most resource-intensive feature (audio streaming + FFmpeg processing + sustained connection to voice chats) and benefits from the bot being stable and well-monitored first.

**Why Pyrogram is an advantage here:** Pyrogram can join voice chats as a user client and stream audio directly. The Bot API cannot do this. This is one of the key reasons the existing codebase chose Pyrogram.

**Music module** (`zyrax/modules/music.py`):
- Play from YouTube, Spotify links (resolved to YouTube), SoundCloud, and direct audio URLs
- Audio extraction via yt-dlp; streaming via FFmpeg piped to Pyrogram's voice chat API
- Queue management — add, remove, reorder, clear, shuffle
- Playback controls — play, pause, resume, stop, skip, previous
- Volume control and seek to timestamp
- Loop modes — loop one, loop queue, no loop
- Shuffle toggle
- Now playing — current track info, duration, progress bar (text-based)
- Lyrics display — via a lyrics API (`/lyrics` or auto-fetch for now playing)
- Audio download — `/dl` (already partially covered by the media module; music module adds queue-aware downloading)
- Radio stream support — `/radio <stream_url>` — play an HLS or MP3 stream

**Dashboard integration:** Music player status visible in dashboard (currently playing track, queue length, active voice chats).

---

### Phase 9 — Security Hardening & Launch Polish (Weeks 21–22)

**Goal:** Production-ready. Every security control in place, documentation complete, stress-tested.

- **GDPR compliance module** — `/mydata` exports all data about the requesting user as JSON. `/deletedata` purges all personal data. Privacy policy and ToS commands.
- **2FA for owner commands** — owner must confirm sensitive actions (promote to super-admin, change bot config) via a second factor (e.g., a code sent to a designated admin chat).
- **Security alerts** — automated notifications to the owner chat on: mass ban (>5 in 1 minute), new admin promotion, config changes, failed auth attempts.
- **Encrypted backups** — automated nightly MongoDB dumps, encrypted with AES-256, stored locally and optionally pushed to cloud storage.
- **Audit log finalization** — every admin action across every module is logged. No exceptions.
- **Multi-language finalization** — 50+ locales. All user-facing strings externalized to JSON locale files. Auto-detection on first interaction.
- **Per-group customization** — enable/disable any module per group. Custom command prefixes. Command aliases. Embed colors and branding.
- **Documentation** — README updated. Per-module docs in a `/docs` folder. Configuration reference. Deployment guide for fresh installs.
- **Stress test** — simulate 500+ concurrent users across 20 groups. Verify no memory leaks, no deadlocks, no dropped messages under load.
- **Production deployment** — final Docker Compose up. Monitoring confirmed. Alerts configured. 24-hour watch period.

---

## 4. Effort Summary

| Phase | Weeks | Theme | New Modules | Key Risk |
|---|---|---|---|---|
| 1 | 1–2 | Close Critical Gaps | `welcome.py`, `userinfo.py` | None — straightforward completions |
| 2 | 3–5 | Anti-Spam & Mod Depth | `captcha.py`, `blacklist.py` | Link scanning accuracy (false positives) |
| 3 | 6–7 | Notes, Filters & User Depth | (expansions to existing) | Karma abuse (mitigated by rate limits) |
| 4 | 8–11 | Games & Economy | `games/`, `economy.py` | Largest phase — economy balance tuning |
| 5 | 12–14 | Fun, Utilities & Media | `fun.py`, `utilities.py`, `media.py` | API rate limits on external services |
| 6 | 15–16 | Analytics & Dashboard | (dashboard expansions) | MongoDB aggregation performance at scale |
| 7 | 17–18 | AI & Automation | `automation.py` | OpenAI API costs / latency |
| 8 | 19–20 | Music Player | `music.py` | FFmpeg + voice chat stability |
| 9 | 21–22 | Security & Launch | (cross-cutting) | None — this is hardening, not new features |

---

## 5. Notes on the Existing Tech Choices

A few points worth keeping in mind as development continues:

**MongoDB schema flexibility is an asset.** New fields can be added to any document without a migration. When adding karma, XP, or economy data to user documents, just write the new fields. Motor's async driver keeps this non-blocking. The trade-off is that there are no foreign-key constraints — referential integrity must be enforced in application code.

**Pyrogram's MTProto access is the single biggest architectural advantage.** It lets ZyraX see all messages in a group (not just those directed at the bot), join voice chats and stream audio, and access chat history. This makes the analytics engine, the music player, and the message-counting system all significantly easier to build than they would be on a pure Bot API bot.

**The plugin auto-discovery system means every new module is one file.** No registration, no import maps, no configuration changes to activate a new feature. This should remain the pattern for every new module in this roadmap. The convention is: one `.py` file per logical feature area, with `__mod_name__` and `__help__` defined at the top.

**The FastAPI dashboard is already the right place for admin features.** Don't build a second admin interface. Every new feature that has an admin dimension (moderation logs, user profiles, economy management, analytics) should be surfaced as a new route or page in the existing dashboard.

**Redis is already in the stack.** Use it aggressively for: rate limiting (per-user, per-command cooldowns), caching expensive API responses (weather, crypto prices), session state for multi-step commands (like captcha verification or game turns), and as a simple pub/sub channel if any cross-process communication is needed later.
