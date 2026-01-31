# ZyraX 🌌

**ZyraX** is a powerful, modular, and asynchronous Telegram Bot built with Python and Pyrogram. Designed for scalability, it features a plugin-based architecture allowing it to handle everything from group moderation to AI image generation.

Now features a **Web Dashboard** for real-time analytics and management!

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

### 📊 Dashboard & Analytics (New!)
- **Web Interface**: Manage your bot via a beautiful web UI.
- **Real-Time Stats**: View command usage, active chats, and user growth.
- **Premium System**: Built-in monetization pages for subscription management.

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
- **Web**: FastAPI + Jinja2 + TailwindCSS
- **Database**: MongoDB (Motor Async Driver) + Redis (Caching)
- **Deployment**: Docker & Docker Compose

---

## 📦 Installation Guide

### Prerequisites
Before you begin, ensure you have usage access to:
1.  **Python 3.11+**: [Download Here](https://www.python.org/downloads/)
2.  **MongoDB**: [Community Server](https://www.mongodb.com/try/download/community) or [MongoDB Atlas](https://www.mongodb.com/atlas) (Cloud).
3.  **Redis**: [Redis.io](https://redis.io/download) (For caching & stats).
4.  **Telegram API**: Get `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
5.  **Bot Token**: Get it from [@BotFather](https://t.me/BotFather).

---

### Windows Tutorial 🪟

1.  **Clone the Repository**
    Open PowerShell or Command Prompt:
    ```powershell
    git clone https://github.com/bipash25/ZyraX.git
    cd ZyraX
    ```

2.  **Create Virtual Environment**
    It's recommended to use a virtual environment:
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate
    ```

3.  **Install Dependencies**
    ```powershell
    pip install -r requirements.txt
    ```

4.  **Configuration**
    Copy the sample config:
    ```powershell
    copy .env.sample .env
    ```
    Open `.env` in Notepad (or VS Code) and fill in your details:
    ```env
    API_ID=123456
    API_HASH=your_api_hash
    BOT_TOKEN=123:ABC...
    MONGO_URL=mongodb://localhost:27017
    REDIS_URL=redis://localhost:6379
    OPENAI_API_KEY=sk-... (Optional)
    OWNER_ID=123456789
    ```

5.  **Run the Bot**
    ```powershell
    python -m zyrax
    ```
    *The bot will start, and the Dashboard will be live at `http://localhost:8080`.*

---

### macOS / Linux Tutorial 🐧

1.  **Clone the Repository**
    Open Terminal:
    ```bash
    git clone https://github.com/bipash25/ZyraX.git
    cd ZyraX
    ```

2.  **Create Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**
    Copy the sample config:
    ```bash
    cp .env.sample .env
    ```
    Edit `.env` using `nano` or your preferred editor:
    ```bash
    nano .env
    ```
    Fill in your API credentials (as shown in the Windows section).

5.  **Run the Bot**
    ```bash
    python3 -m zyrax
    ```

---

### Option C: Docker (Cross-Platform) 🐳

If you have Docker installed, this is the easiest method.

1.  **Clone and Config**
    ```bash
    git clone https://github.com/bipash25/ZyraX.git
    cd ZyraX
    mv .env.sample .env
    # Edit .env with your credentials
    ```

2.  **Run**
    ```bash
    docker-compose up -d
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
| **Web** | `http://localhost:8080/` | View Dashboard |

## 🤝 Contributing
Contributions are welcome! This project uses a modular design—simply add a new `.py` file to `zyrax/modules/` with `__mod_name__` and `__help__` variables, and it will load automatically.

## 📄 License
This project is licensed under the MIT License.
