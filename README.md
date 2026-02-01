# ZyraX 🚀

> A modular, powerful, and secure Telegram bot built with **Pyrogram**, **MongoDB**, and **FastAPI**.

## 🌟 Features

### 🛡️ Moderation & Security
*   **Ban/Kick/Mute:** Robust user management with time duration support (`/tban 1d`).
*   **Anti-Spam:** CAPTCHA verification for new members (`/captcha`), Blacklist (`/blacklist`), and Anti-Flood.
*   **Logging:** Comprehensive audit logs for all admin actions.
*   **Reports:** Users can report messages to admins (`/report`).

### 🤖 AI & Automation
*   **Gemini Integration:** Chat with Google's Gemini AI (`/ask`).
*   **Auto-Moderation:** AI-powered toxicity detection (using Gemini/OpenAI).
*   **Image Generation:** Create images with DALL-E (`/imagine`).
*   **RSS:** Track RSS feeds (`/rss`).

### 🎮 Fun & Economy
*   **Economy:** Earn coins, daily rewards, and transfer funds (`/balance`, `/pay`, `/work`).
*   **Games:** Trivia (`/trivia`), Number Guessing (`/guess`), Dice, RPS.
*   **Levels:** XP system with levels and leaderboards (`/rank`, `/top`).
*   **Fun:** Quotes, Jokes, Memes, Urban Dictionary.

### 🎵 Media & Utilities
*   **Music Player:** Stream high-quality audio (`/play`).
*   **Tools:** Weather, IP Lookup, Sticker Converter, Video Downloader (`/dl`).

### 📊 Dashboard
*   **Web Interface:** Real-time statistics and logs.
*   **Analytics:** Hourly/Daily activity charts.

## 🚀 Deployment

### Prerequisites
*   Docker & Docker Compose
*   Telegram API ID & Hash
*   Bot Token
*   MongoDB & Redis (handled by Docker)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/ZyraX.git
    cd ZyraX
    ```

2.  **Configure Environment:**
    Create a `.env` file based on `.env.example`:
    ```env
    API_ID=your_api_id
    API_HASH=your_api_hash
    BOT_TOKEN=your_bot_token
    MONGO_URL=mongodb://mongo:27017
    REDIS_URL=redis://redis:6379
    OWNER_ID=your_id
    OPENAI_API_KEY=optional_key
    GEMINI_API_KEYS=key1,key2
    ```

3.  **Run with Docker:**
    ```bash
    docker-compose up -d --build
    ```

## 📚 Documentation

## 📝 Commands

### 🛡️ Admin & Moderation
*   `/ban`, `/mute`, `/kick`, `/unban`, `/unmute` - User control.
*   `/tban <time>`, `/tmute <time>` - Temporary ban/mute.
*   `/promote`, `/demote` - Manage admins.
*   `/adminlist` - List admins.
*   `/warn`, `/unwarn`, `/resetwarns` - Warning system.
*   `/blacklist` - Manage banned words.
*   `/captcha [on/off]` - Toggle join verification.
*   `/setflood` - Configure anti-flood.

### 🤖 AI & Automation
*   `/ask <query>` - Chat with Gemini AI.
*   `/imagine <prompt>` - Generate images (DALL-E).
*   `/rss add <url>` - Subscribe to RSS feeds.
*   `/tr <lang> <text>` - Translate text.

### 🎮 Economy & Games
*   `/balance`, `/daily`, `/work` - Economy basics.
*   `/pay <user> <amount>` - Transfer coins.
*   `/rich` - Leaderboard.
*   `/trivia` - Play trivia.
*   `/guess` - Number guessing game.
*   `/dice`, `/dart`, `/rps` - Telegram games.

### 🎵 Media & Fun
*   `/play <song>` - Play music in voice chat.
*   `/stop`, `/skip`, `/pause`, `/resume` - Music controls.
*   `/dl <url>` - Download video/audio from social media.
*   `/tosticker` - Convert image to sticker.
*   `/quote`, `/joke`, `/meme` - Fun content.
*   `/weather <city>`, `/ip <addr>` - Utilities.

### ⚙️ Settings
*   `/setwelcome`, `/setgoodbye` - Custom greetings.
*   `/welcomemode <text/image>` - Toggle image welcome.
*   `/newfed`, `/joinfed`, `/fban` - Federation management.
*   `/save`, `/get`, `/notes` - Notes system.
*   `/filter`, `/stop` - Auto-reply filters.

## 🔒 Privacy & GDPR

*   **Export Data:** Use `/mydata` to get a JSON export of your stored data.
*   **Delete Data:** Use `/deletedata` to permanently purge your data.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

MIT License
