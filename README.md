# ZyraX 🌌

**ZyraX** is a powerful, modular, and asynchronous Telegram Bot built with Python and Pyrogram. Designed for scalability, it features a plugin-based architecture allowing it to handle everything from group moderation to AI image generation.

## 🚀 Features

### 🛡️ Moderation & Administration
- **Ban/Kick/Mute**: Full user control with `ChatPermissions`.
- **Warnings**: Database-backed warn system with auto-ban thresholds.
- **Admin Tools**: Promote/Demote users, Admin lists.
- **Federations**: Cross-chat ban system (`/fban`) to protect communities.

### 🤖 AI & Automation
- **ChatGPT Integration**: Chat with AI using `/ask`.
- **Image Generation**: Creates images via DALL-E with `/imagine`.
- **Filters**: Auto-replies based on keywords (Text & Media).
- **Notes**: Save and retrieve commonly used messages/media.
- **Anti-Flood**: Automated spam protection with configurable limits.

### 🎮 Fun & Tournaments
- **Tournament System**: Create and manage bracket-style tournaments automatically.
- **Games**: Interactive Dice, Darts, RPS.
- **Entertainment**: Meme and Joke generators.

### 🔌 Connectivity
- **Bridge**: Built-in Webhook receiver for external integrations (GitHub, Trello scripts).
- **Dynamic Loading**: Hot-pluggable modules with auto-discovery.

## 🛠️ Tech Stack
- **Language**: Python 3.11+
- **Framework**: [Pyrogram](https://docs.pyrogram.org/) (MTProto)
- **Database**: MongoDB (Motor Async Driver)
- **Deployment**: Docker & Docker Compose

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- MongoDB (Local or Atlas)
- Telegram API Credentials (`API_ID`, `API_HASH`)
- Bot Token (from @BotFather)

### Option A: Docker (Recommended)
1. **Clone the repository**
   ```bash
   git clone https://github.com/bipash25/ZyraX.git
   cd ZyraX
   ```
2. **Configure Environment**
   Rename `.env.sample` to `.env` and fill in your details:
   ```env
   API_ID=12345
   API_HASH=abcdef...
   BOT_TOKEN=123:ABC...
   MONGO_URL=mongodb://mongo:27017 # Use exact string if using Docker
   OPENAI_API_KEY=sk-... # Optional (For AI)
   OWNER_ID=123456789
   ```
3. **Run with Compose**
   ```bash
   docker-compose up -d
   ```

### Option B: Local Setup
1. **Clone and Install Dependencies**
   ```bash
   git clone https://github.com/bipash25/ZyraX.git
   cd ZyraX
   pip install -r requirements.txt
   ```
2. **Configure Environment**
   Edit `.env` as above (Set `MONGO_URL` to your local instance, e.g., `mongodb://localhost:27017`).
3. **Run the Bot**
   ```bash
   python -m zyrax
   ```

## 📝 Commands
| Module | Command | Description |
|--------|---------|-------------|
| **Admin** | `/promote`, `/demote` | Manage admins |
| **Bans** | `/ban`, `/mute`, `/kick` | User control |
| **AI** | `/ask`, `/imagine` | AI features |
| **Tourney**| `/tourney`, `/bracket` | Tournament system |
| **Feds** | `/newfed`, `/fban` | Federation management |
| **Notes** | `/save`, `/get` | Saved snippets |

## 🤝 Contributing
Contributions are welcome! This project uses a modular design—simply add a new `.py` file to `zyrax/modules/` with `__mod_name__` and `__help__` variables, and it will load automatically.

## 📄 License
This project is licensed under the MIT License.
