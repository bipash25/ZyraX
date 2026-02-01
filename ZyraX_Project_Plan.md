# ZyraX

**@ZyraXRobot**

All-in-One Telegram Bot

---

## Comprehensive Project Plan

500+ Features | 20-Week Roadmap | Full Technical Specification

*Prepared: February 1, 2026*

---

## 1. Executive Summary

ZyraX is a feature-rich, all-in-one Telegram bot designed to serve as the definitive group management, entertainment, and community-building tool. Spanning 500+ discrete features across moderation, user management, games, economy, AI integration, music playback, and deep analytics, ZyraX is architected as a modular, async-first Python application — optimized to run efficiently on the provided VPS while delivering a professional-grade user experience.

The project is structured into a 20-week phased roadmap, beginning with a hardened foundation of moderation and anti-spam (the features groups rely on most), and progressively layering in engagement systems, AI capabilities, and advanced integrations. Every phase is designed to deliver a fully functional, testable milestone — so ZyraX can go live incrementally if needed.

---

## 2. VPS Hardware Analysis & Constraints

The following table summarizes the server specifications extracted from the provided system info. Each constraint and its implications for ZyraX are addressed directly below.

| Component | Specification |
|---|---|
| Hostname | gpu-jwce |
| OS | Ubuntu 22.04.5 LTS (Jammy) |
| Kernel | Linux 5.15.0-168-generic |
| CPU | 8× Intel Xeon E3-12xx v2 (Ivy Bridge) |
| RAM | 15 GiB Total / ~14 GiB Available |
| Storage | 125 GB LVM (54 GB free after OS) |
| GPU | NVIDIA GeForce GT 730 — 2 GB VRAM, CUDA 11.4 |
| Virtualization | KVM (QEMU) |
| Driver | NVIDIA 470.256.02 |

### 2.1 CPU Assessment

Eight virtual cores provide solid multi-tasking headroom. Python's asyncio event loop will handle thousands of concurrent Telegram updates on a single core, while Celery workers can utilize the remaining cores for CPU-bound background tasks (image processing, analytics aggregation). No CPU bottleneck is anticipated for the projected user base.

### 2.2 RAM Assessment

15 GiB total (14 GiB available) is generous for this workload. The bot process, PostgreSQL, Redis, and Celery workers will comfortably coexist under 6–8 GiB of combined usage. The largest memory consumer will be Stable Diffusion model loading (~1.5 GiB), which can be loaded on demand and unloaded after use to keep the baseline footprint low.

### 2.3 Storage Assessment

54 GiB of free space is sufficient for the bot's lifetime operational needs, provided a disciplined log-rotation and media-cleanup policy is in place. Database storage will grow slowly (estimated 2–5 GB/year for a mid-sized community). The primary storage consumers are downloaded media (music, images) and log files, both of which will be managed with automated retention policies.

### 2.4 GPU Assessment — Key Constraint

The GT 730 with 2 GB VRAM is the tightest constraint on the platform. It is sufficient for running Stable Diffusion 1.5 (the standard 512×512 model fits in ~1.8 GB VRAM), but is not viable for larger models (SDXL, SD 2.1+). The mitigation strategy is threefold: use only SD 1.5 locally, implement an automatic fallback to the OpenAI DALL-E API for high-resolution or complex prompts, and load/unload the model dynamically to avoid holding VRAM when not in use.

---

## 3. Feature Prioritization — Tier Matrix

The 500+ features are organized into four priority tiers. Tier 1 features ship in Phase 1–2 and form the non-negotiable baseline. Each subsequent tier adds depth while respecting hardware constraints and development time.

| Tier | Priority | Core Features |
|---|---|---|
| Tier 1 | Essential | Moderation, anti-spam, user management, welcome/goodbye, notes, rules, basic utilities |
| Tier 2 | Important | Federation system, advanced filters, games & fun commands, analytics & logging, music playback |
| Tier 3 | Enhanced | AI/ChatGPT integration, economy system, automation & webhooks, advanced media tools |
| Tier 4 | Premium | Advanced AI (image gen, summarization), third-party bridges (Discord/WhatsApp), developer tools & plugin system |

---

## 4. Module & Feature Breakdown

ZyraX is divided into 15 self-contained modules. Each module owns its own command handlers, database models, and configuration. This table maps every module to its feature count and scope.

| Module | Features | Scope Summary |
|---|---|---|
| Moderation | ~85 | Kick, ban, unban, mute, unmute, temp bans/mutes, soft ban, warn system with auto-thresholds, silent warns, reports, anti-flood, anti-raid, captcha (math/button/image/question), anti-bot join, anti-forward, anti-links, anti-sticker/GIF/media/emoji spam, anti-RTL/CJK/Cyrillic, caps lock, mention/hashtag spam, profanity filter, scam/phishing/malware link detection, regex filtering |
| User Mgmt | ~40 | User info & stats, activity tracking, first/last seen, karma & reputation, leveling & ranks, badges & achievements, leaderboards, custom roles, VIP system, blacklist/whitelist, admin notes, user tags, profile cards |
| Welcome | ~15 | Custom welcome/goodbye (text + media + buttons), random welcome messages, rules integration, welcome mute, human verification, auto-delete join messages, new user media lockout, clean welcome (auto-delete) |
| Notes/Filters | ~20 | Save/get/delete notes, private notes, button notes, fillings (variables), media notes, regex filters, filter stats, import/export, sticker notes, voice note responses |
| Games | ~22 | Trivia (categories), word scramble, guess the number, truth or dare, would you rather, tic-tac-toe, RPS, hangman, 20 questions, riddles, chess, connect four, blackjack, poker, Russian roulette, dice, slot machine, daily challenges, per-game leaderboards |
| Economy | ~18 | Daily/hourly rewards, work/beg/rob, gamble, lottery, auction house, trading, bank & interest, loans, taxes, shop & inventory, item gifting, richest leaderboard |
| Fun | ~35 | Memes (Reddit), jokes, facts, quotes, pet/anime pics, coinflip, 8ball, horoscope, ship/love calc, action GIFs, text tools (reverse, Morse, leetspeak, Zalgo, mock, ASCII art), generators (roast, compliment, story, rap battle, band name, superhero) |
| Utilities | ~55 | Wikipedia/Google/YouTube search, image search, Urban Dictionary, translate, currency/crypto/stock prices, weather, news, dictionary/thesaurus, IP/WHOIS/DNS lookup, QR code gen/read, URL shortener, website screenshot, GitHub info, package/flight tracking, IMDB/anime/recipe/book/lyrics search, color converter |
| Media Tools | ~20 | Image↔sticker, video↔GIF, OCR, background removal, image filters/resize/compress, collage, meme gen, PDF↔images, social media downloaders, reverse image search, face detection, AI upscale |
| Analytics | ~18 | Per-user message counts, most active users/hours, word cloud, group growth, join/leave stats, command usage, media stats, language stats, activity heatmap, visual charts, CSV/JSON export |
| AI Module | ~12 | ChatGPT conversations, AI moderation (toxicity/NSFW/spam scoring), sentiment analysis, auto-translation, smart replies, topic detection, document summarization, AI image generation (local SD) |
| Music | ~18 | Play YouTube/Spotify/SoundCloud/direct links, queue management, skip/pause/resume/stop, volume/seek, loop/shuffle, now playing + lyrics, radio streams, audio download, trim/merge/speed/pitch/format conversion, TTS (multi-voice) |
| Automation | ~15 | Scheduled messages, auto-pin, RSS feeds, GitHub/GitLab/Twitter/YouTube/Twitch webhooks, IFTTT/Zapier integration, auto-response templates, trigger-action system |
| Federation | ~14 | Create/manage feds, subscribe groups, fed-wide bans & warnings, import/export ban lists, fed admin management, fed broadcasts, fed statistics |
| Security | ~12 | Anonymous admin actions, private group mode, GDPR tools, user data encryption, 2FA for admin, IP whitelist, rate limiting, audit logs, security alerts, encrypted backups |

---

## 5. Technology Stack

Every technology choice is justified by the VPS constraints, the async-heavy nature of Telegram bots, and the need to support 500+ features without architectural rewrites as the project grows.

| Layer | Technology | Rationale |
|---|---|---|
| Runtime | Python 3.11+ | Primary language; asyncio-native for high concurrency |
| Telegram Framework | python-telegram-bot v20+ | Async-first, full Bot API coverage, robust error handling |
| Database | PostgreSQL 15 + SQLAlchemy ORM | Relational data (users, groups, bans, notes); ACID compliance |
| Cache / Sessions | Redis 7 | In-memory cache, rate limiting, session storage, pub/sub |
| Task Queue | Celery + Redis Broker | Background jobs: scheduled messages, analytics, AI calls |
| AI / NLP | OpenAI API (GPT-4o-mini) | ChatGPT conversations, toxicity detection, summarization |
| Image Generation | Stable Diffusion (local GPU) | AI image gen via GT 730 — lightweight models (SD 1.5) |
| Music Streaming | yt-dlp + FFmpeg | Audio extraction from YouTube/SoundCloud; stream to voice chats |
| Web Dashboard | FastAPI + React (optional) | Admin panel for analytics, moderation logs, group settings |
| Containerization | Docker + Docker Compose | Isolated services; reproducible deployment; easy scaling |
| Monitoring | Prometheus + Grafana | Real-time metrics: CPU, RAM, GPU, API latency, error rates |
| Logging | Structured JSON (loguru) | Centralized logs with severity, correlation IDs, export to CSV/JSON |

---

## 6. System Architecture

ZyraX follows a layered, event-driven architecture. Incoming Telegram updates flow through a middleware pipeline (authentication, rate limiting, language detection, logging) before being dispatched to the appropriate module handler. Long-running or scheduled tasks are offloaded to Celery workers. All state is persisted in PostgreSQL, with Redis serving as the caching and message-broker layer.

### 6.1 Data Flow

- Telegram sends an update (message, callback query, etc.) to the bot via webhook or polling.
- The middleware stack processes the update: checks rate limits, identifies the user/group, detects language, and logs the event.
- The dispatcher routes the update to the correct module based on the command or trigger.
- The module handler executes business logic, reads/writes to PostgreSQL via SQLAlchemy, and caches frequently accessed data in Redis.
- If the task is long-running (e.g., AI image generation, analytics report), it is enqueued to a Celery worker, and the bot sends an immediate "processing…" response.
- The worker completes the task and the result is delivered back to the chat.

### 6.2 Service Boundaries

- **Bot Service** — The main async process. Handles all real-time Telegram interactions. Stateless between requests (all state in DB/Redis).
- **Worker Service** — One or more Celery worker processes. Handles AI calls, scheduled messages, analytics cron jobs, media downloads, and image generation.
- **Database Service** — PostgreSQL. Single source of truth for all persistent data. Accessed only via the ORM — never raw queries from application code.
- **Cache Service** — Redis. Rate-limit counters, session tokens, frequently queried user/group configs, Celery task broker, and pub/sub for cross-service communication.
- **Dashboard Service (Optional)** — A FastAPI backend + React frontend for admin analytics and moderation log review. Connects to the same PostgreSQL instance (read-only replica preferred in production).

---

## 7. Project Directory Structure

The project follows a module-per-feature convention. Every module is independently testable and can be enabled or disabled via configuration — critical for the per-group customization feature.

| Path | Purpose |
|---|---|
| `zyra/` | Project root — Docker Compose, .env, README |
| `zyra/bot/` | Main bot package |
| `zyra/bot/main.py` | Application entry point; initializes updater & dispatcher |
| `zyra/bot/config.py` | Environment-based config loader (all secrets from .env) |
| `zyra/bot/database/` | SQLAlchemy models, migrations (Alembic), DB connection pool |
| `zyra/bot/modules/` | Feature modules — each module is self-contained |
| `zyra/bot/modules/moderation/` | Kick, ban, mute, warn, reports, anti-spam, federation |
| `zyra/bot/modules/users/` | User info, roles, karma, levels, badges, profiles |
| `zyra/bot/modules/games/` | All game logic (trivia, chess, tic-tac-toe, economy) |
| `zyra/bot/modules/fun/` | Memes, jokes, text manipulation, random commands |
| `zyra/bot/modules/utilities/` | Search, calculators, converters, media tools |
| `zyra/bot/modules/analytics/` | Stats collection, heatmaps, reports, log exports |
| `zyra/bot/modules/ai/` | ChatGPT wrapper, toxicity detection, image generation |
| `zyra/bot/modules/music/` | Voice chat player, queue, audio processing |
| `zyra/bot/modules/automation/` | Scheduled msgs, webhooks, RSS, trigger-action |
| `zyra/bot/modules/economy/` | Currency, shop, bank, gambling, auctions |
| `zyra/bot/utils/` | Shared helpers: rate limiter, decorator cache, formatters |
| `zyra/bot/middlewares/` | Auth checks, rate limiting, language detection, logging |
| `zyra/workers/` | Celery workers for background task processing |
| `zyra/dashboard/` | Optional FastAPI + React admin panel |
| `zyra/tests/` | Unit & integration tests (pytest) |
| `zyra/docker-compose.yml` | Orchestrates: bot, workers, PostgreSQL, Redis, dashboard |
| `zyra/migrations/` | Alembic DB migration scripts |

---

## 8. Development Roadmap — 20-Week Phased Plan

Each phase delivers a fully functional, independently deployable milestone. Testing and documentation are baked into every phase — not deferred to the end.

| Phase | Timeline | Theme | Key Deliverables |
|---|---|---|---|
| Phase 1 | Weeks 1–3 | Foundation | Project scaffolding, Telegram Bot API setup, database (PostgreSQL + Redis), core config system, logging, Docker containerization, basic moderation (kick/ban/mute/warn), anti-flood, join captcha, welcome/goodbye messages, notes & filters, group rules, admin panel basics |
| Phase 2 | Weeks 4–6 | Core Mod & Users | Warn thresholds & auto-actions, soft ban, silent warnings, report system, anti-spam suite (link/sticker/media/emoji), blacklist system, user info & stats, role management, new member controls, federation system foundation, slowmode & message limits |
| Phase 3 | Weeks 7–9 | Fun & Engagement | Games (trivia, tic-tac-toe, RPS, hangman, blackjack, connect four), economy system (currency, shop, bank, gambling), leveling & XP system, leaderboards, fun commands (8ball, coinflip, ship, slap/hug), text manipulation tools, memes & random commands |
| Phase 4 | Weeks 10–12 | Utilities & Analytics | Search & fetch tools (Wikipedia, weather, translate, currency), media tools (OCR, sticker conversion, image resize), calculators & converters, productivity tools (reminders, polls, todo), analytics dashboard, full logging system, export capabilities |
| Phase 5 | Weeks 13–15 | AI & Automation | ChatGPT integration (conversation mode), AI moderation (toxicity, NSFW, spam scoring), scheduled messages & RSS feeds, webhook integrations (GitHub, Twitch, YouTube), auto-response templates, trigger-action automation, sentiment analysis |
| Phase 6 | Weeks 16–18 | Music & Advanced | Voice chat music player (YouTube, Spotify, SoundCloud), queue management & controls, audio processing tools, advanced federation features, third-party bridges (Discord), plugin system & module marketplace, performance optimization & load testing |
| Phase 7 | Weeks 19–20 | Polish & Launch | AI image generation, advanced customization, multi-language finalization (50+ locales), security hardening (2FA, audit logs, encryption), GDPR compliance tools, documentation, stress testing, production deployment, monitoring setup, public launch |

### 8.1 Phase Details

#### Phase 1 — Foundation (Weeks 1–3)

This phase establishes everything the bot needs to exist and be useful from day one. The focus is on correctness and security — not feature breadth.

- Set up the Git repository, CI pipeline (GitHub Actions or equivalent), and Docker Compose environment.
- Integrate the Telegram Bot API; register @ZyraXRobot; configure webhook or long-polling.
- Implement the database layer: PostgreSQL with Alembic migrations; define core models (User, Group, Admin, Config).
- Build the middleware stack: rate limiting, auth, logging, error handling.
- Ship core moderation: kick, ban, unban, mute, unmute, temporary actions with durations.
- Ship anti-flood and basic captcha (button-based).
- Ship welcome/goodbye messages with customizable text and buttons.
- Ship the notes and filters system (save, get, delete, regex filters).
- Ship group rules command and admin list.

#### Phase 2 — Core Moderation & User Systems (Weeks 4–6)

This phase hardens the moderation system and builds the user-facing identity layer that underpins games and economy in later phases.

- Expand the warn system: configurable thresholds, auto-action on threshold, silent warnings, warning notes.
- Add soft ban, report system, and anonymous admin mode.
- Ship the full anti-spam suite: link detection (scam, phishing, malware), sticker/GIF/media/emoji spam, mention spam, hashtag spam, caps lock, repeated characters.
- Ship the blacklist system with configurable actions (delete, warn, ban, mute, kick) and regex support.
- Build user profiles: info, stats, activity tracking, first/last seen.
- Build the role and permission system: custom roles, VIP, promote/demote, granular permissions.
- Ship the federation system: create, subscribe, fed-bans, fed-warns, import/export.
- Add slowmode, message length limits, and new-user media lockout.

#### Phase 3 — Games & Economy (Weeks 7–9)

Engagement features. These are the features that keep users coming back daily and create community interaction.

- Ship core games: trivia (with categories and scoring), tic-tac-toe, RPS, hangman, blackjack, connect four, word scramble, guess the number.
- Ship advanced games: riddles, 20 questions, truth or dare, would you rather, chess (PGN), poker, Russian roulette, dice, slot machine.
- Build the per-game leaderboard and achievements system.
- Ship the economy system: daily/hourly rewards, work, beg, rob, gamble, lottery, shop, inventory, bank, loans, auctions, trading.
- Build the leveling system: XP from messages, level-up notifications, custom level roles, prestige, profile card generation.
- Ship daily challenges that tie games and economy together.

#### Phase 4 — Utilities & Analytics (Weeks 10–12)

The utility layer makes ZyraX genuinely useful for information lookup and productivity — not just entertainment.

- Ship search commands: Wikipedia, Google, YouTube, image search, Urban Dictionary, dictionary, thesaurus.
- Ship real-time data: weather, currency converter, crypto prices, stock market, news headlines.
- Ship developer/network tools: IP lookup, WHOIS, DNS, QR code gen/read, URL shortener, website screenshot, GitHub info.
- Ship media tools: image↔sticker, OCR, background removal, resize, compress, PDF↔image, social media downloaders.
- Ship productivity tools: reminders, to-do lists, advanced polls (anonymous, multiple choice), countdown timers, calculators (scientific, BMI, tip, loan, unit converter), password/hash generators.
- Build the analytics engine: per-user and per-group stats, most-active tracking, word cloud, activity heatmap, growth charts.
- Build the full logging system with admin action log, deleted/edited message log, and CSV/JSON export.

#### Phase 5 — AI & Automation (Weeks 13–15)

This phase integrates external AI services and builds the automation backbone that powers scheduled content and third-party integrations.

- Integrate OpenAI API: ChatGPT conversation mode (per-user context), toxicity detection, NSFW content screening, spam probability scoring.
- Build AI-powered moderation: automatic content screening in configurable groups, sentiment analysis, topic detection and auto-tagging.
- Ship document summarization (paste or upload text/PDF, get a summary).
- Build the automation system: scheduled messages (cron-style), RSS feed reader with auto-posting, trigger-action rules.
- Integrate webhooks: GitHub/GitLab (push, PR, issue events), Twitch stream alerts, YouTube channel notifications, Twitter feed.
- Ship auto-response templates and smart reply suggestions.

#### Phase 6 — Music & Advanced Features (Weeks 16–18)

Music is one of the most resource-intensive features (audio streaming + FFmpeg processing). It is placed here to allow the bot's baseline to stabilize before adding this load.

- Build the voice chat music player: play from YouTube, Spotify links, SoundCloud, and direct URLs via yt-dlp + FFmpeg.
- Build queue management: add, remove, reorder, shuffle, loop, skip, pause, resume, stop, volume, seek.
- Ship now-playing info and lyrics display (via lyrics API).
- Ship audio processing tools: trim, merge, speed change, pitch shift, format conversion, equalizer presets, extract audio from video.
- Ship radio stream support.
- Expand federation features: fed-wide broadcasts, advanced fed statistics.
- Build the plugin system: a module marketplace concept where community-contributed modules can be loaded at runtime.
- Initiate the Discord bridge (relay messages between a Telegram group and a Discord server).
- Performance optimization pass: profile hot paths, optimize DB queries, tune Redis TTLs, load test with simulated traffic.

#### Phase 7 — Polish & Production Launch (Weeks 19–20)

The final phase closes the loop: everything is hardened, documented, tested at scale, and launched.

- Ship AI image generation: integrate Stable Diffusion 1.5 locally (GPU); automatic fallback to DALL-E API for complex/large requests.
- Finalize multi-language support: 50+ locales, auto-detection, per-user language preference, localized help menus.
- Complete the customization layer: per-group module enable/disable, custom command prefixes, aliases, embed colors, branding.
- Security hardening: full audit of all endpoints; enable 2FA for owner commands; verify encrypted backups; run dependency scan.
- GDPR compliance: data export and deletion flows; privacy policy and ToS commands; opt-out mechanism.
- Write comprehensive documentation: README, per-module docs, configuration reference, deployment guide.
- Stress test: simulate 500+ concurrent users across 20 groups; verify no memory leaks or deadlocks.
- Production deployment: execute the deployment checklist (see Section 11); enable monitoring and alerting.
- Public launch: share @ZyraXRobot; monitor for 24–48 hours; hotfix any critical issues.

---

## 9. Resource & Capacity Estimation

The table below projects disk and RAM usage as each service layer is added. All figures are conservative estimates based on typical workloads for similar bot deployments. The VPS has 54 GB free disk and 14 GB available RAM — both provide comfortable headroom above peak estimates.

| Service Layer | Disk Usage | RAM Usage | Cumulative Disk |
|---|---|---|---|
| Base Bot (mod + users + notes) | ~300 MB | ~1.5 GB | ~2 GB |
| + Games & Economy Engine | ~150 MB | ~500 MB | ~2.5 GB |
| + Analytics & Logging | ~100 MB | ~300 MB | ~3 GB |
| + AI (OpenAI API calls) | ~50 MB | ~400 MB | ~3.5 GB |
| + Music Player (yt-dlp) | ~200 MB | ~1 GB | ~5 GB |
| + Stable Diffusion (GPU) | ~2 GB | ~1.5 GB | ~8 GB |
| **Peak Estimated Total** | **~2.8 GB** | **~5.2 GB** | **~15 GB** |

Key observations: the base bot with all core features consumes under 4 GB of disk and under 3 GB of RAM. Stable Diffusion is the single largest addition. Music caching (yt-dlp downloads) grows over time but is managed by automatic cleanup of files older than 24 hours. Total peak usage remains well within the VPS capacity with margin for growth.

---

## 10. Risk Register & Mitigation

Every identified risk is paired with a concrete mitigation strategy. High-likelihood risks have been addressed in the architecture itself — not left as future work.

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| GT 730 VRAM limit (2 GB) | High | Medium | Use lightweight SD 1.5 models only; offload to CPU for complex jobs; consider API fallback (DALL-E) for high-quality requests |
| Telegram API rate limits | Medium | High | Implement per-chat request queuing; exponential backoff; batch non-urgent messages; cache repeated API calls |
| OpenAI API latency / costs | Medium | Medium | Use GPT-4o-mini (cheapest); implement response caching; set strict token limits; fallback to simpler local NLP for basic tasks |
| Single-VPS single point of failure | Medium | High | Automated daily backups to cloud (DB + configs); health-check auto-restart via Docker; set up uptime monitoring alerts |
| Music streaming legal risk | Low | Medium | Use yt-dlp for personal/group use only; add clear ToS disclaiming redistribution; respect platform terms of service |
| Storage growth (logs + media) | Medium | Low | Log rotation (7-day retention); periodic media cleanup; compress old exports; monitor disk via Prometheus alerts at 75% |
| Memory pressure under load | High | Medium | Redis eviction policies; connection pooling for PostgreSQL; async I/O throughout; graceful degradation of non-critical features under load |

---

## 11. Deployment & Launch Checklist

This checklist is executed sequentially at the end of Phase 7 (and can be reused for any subsequent major release). Each stage has a clear pass/fail criterion.

| Stage | Actions |
|---|---|
| Pre-Deploy | Final code review; run full test suite (pytest); lint & type-check; update migration scripts; tag release in Git |
| Environment | Provision .env on VPS; verify all API keys active; confirm PostgreSQL & Redis accessible; pull Docker images |
| Database | Run Alembic migrations; seed initial data (default settings, system user); verify schema integrity |
| Containers | docker compose up -d; verify all containers healthy; check inter-service connectivity |
| Smoke Test | Send test commands to @ZyraXRobot in a private group; verify moderation, notes, welcome, and a game command respond correctly |
| Monitoring | Confirm Prometheus scraping all endpoints; verify Grafana dashboards loading; set up PagerDuty / alert channel |
| DNS & Public | Verify bot is discoverable via @ZyraXRobot on Telegram; share bot link; announce launch |
| Post-Launch | Monitor error rates for 24h; watch RAM/CPU/disk trends; hotfix any critical bugs; schedule first weekly review |

---

## 12. Security Controls

Security is not a phase — it is a cross-cutting concern built into every layer from day one. The following controls are mandatory for production deployment.

| # | Security Control |
|---|---|
| 1 | All secrets (API keys, DB passwords, bot token) stored in .env — never hardcoded or committed to version control |
| 2 | 2FA enforcement for all bot owner / super-admin commands |
| 3 | IP whitelisting for owner-level commands (configurable per-environment) |
| 4 | Per-user rate limiting with Redis-backed sliding window |
| 5 | Bruteforce protection on admin dashboard (if enabled) |
| 6 | Full audit log trail: every admin action timestamped, logged, and exportable |
| 7 | GDPR compliance module: user data export (JSON) and full deletion on request |
| 8 | Encrypted database backups with verification checksums |
| 9 | Session management with automatic expiry and invalidation |
| 10 | Security alerts for suspicious activity (mass bans, unusual login patterns) |
| 11 | Regular dependency scanning (pip-audit) in CI/CD pipeline |
| 12 | Network policies: bot container has no inbound ports — only outbound to Telegram API and configured services |

---

## 13. Monitoring & Observability

Production health is monitored through three complementary systems, all running within the same Docker Compose stack to minimize operational overhead.

### Prometheus — Metrics

- Scrapes all services every 15 seconds: bot response latency, commands processed per minute, active users, error rates, Celery task queue depth.
- System metrics: CPU usage per core, RAM utilization, disk I/O, GPU utilization (via nvidia-smi exporter), network throughput.
- Alerts fire at: CPU > 85%, RAM > 80%, disk > 75%, error rate > 5% over 5 minutes, any service unhealthy.

### Grafana — Dashboards

- Pre-built dashboards: Bot Health (latency, errors, uptime), Group Activity (messages, users, commands), Economy (transactions, balance trends), System Resources.
- All dashboards are exported as JSON and version-controlled — recreatable from scratch in minutes.

### Structured Logging (loguru)

- Every request, command execution, error, and admin action is logged as structured JSON with a correlation ID.
- Logs are written to rotating files (7-day retention) and can be streamed to an external log aggregator if needed.
- The bot's `/logs` command (owner-only) provides a tail of recent errors directly in Telegram.

---

## 14. Conclusion

ZyraX is an ambitious but thoroughly planned project. The 20-week roadmap delivers value incrementally — Phase 1 alone produces a fully functional moderation bot. The technology stack is chosen for the specific constraints of the GT 730 VPS while remaining extensible as the project (and potentially the infrastructure) grows. Every feature tier, every risk, and every operational concern has been addressed in this plan.

The next step is to begin Phase 1: project scaffolding, Docker environment setup, and the first working moderation commands. Each phase ends with a working, testable bot — so progress is always demonstrable.

---

*— End of Project Plan —*
