# ZyraX Development Roadmap

**Visual documentation of system architecture and development workflow**

---

## System Architecture Overview

### High-Level Component Diagram

```mermaid
graph TB
    subgraph External
        TG[Telegram Servers]
        User[Users/Admins]
    end
    
    subgraph Bot Application
        PTB[PTB Bot API]
        Pyro[Pyrogram MTProto]
        
        subgraph Core
            App[Application Manager]
            Loader[Command Loader]
            Scheduler[APScheduler]
        end
        
        subgraph Middleware
            Perm[Permissions]
            Flood[Anti-Flood]
            Lang[Language]
            Log[Logger]
        end
        
        subgraph Handlers
            Admin[Admin Commands]
            Mod[Moderation]
            Protect[Protection]
            Content[Content Mgmt]
            Fed[Federations]
        end
    end
    
    subgraph Data Layer
        Mongo[(MongoDB)]
        Redis[(Redis Cache)]
    end
    
    User --> TG
    TG --> PTB
    TG --> Pyro
    PTB --> App
    Pyro --> App
    App --> Loader
    App --> Scheduler
    Loader --> Middleware
    Middleware --> Handlers
    Handlers --> Mongo
    Handlers --> Redis
    Scheduler --> Mongo
```

---

## Development Timeline

### 16-Week Implementation Schedule

```mermaid
gantt
    title ZyraX Development Timeline
    dateFormat YYYY-MM-DD
    section Phase 1: Foundation
    Project Setup           :p1, 2024-01-01, 3d
    Core Infrastructure     :p2, after p1, 5d
    Dynamic Loader          :p3, after p2, 4d
    Base Utilities          :p4, after p3, 2d
    
    section Phase 2: Admin & Moderation
    Admin Commands          :p5, after p4, 4d
    Moderation Suite        :p6, after p5, 5d
    Warning System          :p7, after p6, 3d
    Scheduler Integration   :p8, after p7, 2d
    
    section Phase 3: Protection
    Anti-Flood System       :p9, after p8, 3d
    Anti-Raid System        :p10, after p9, 3d
    Captcha System          :p11, after p10, 4d
    Approval System         :p12, after p11, 2d
    Locks Module            :p13, after p12, 2d
    
    section Phase 4: Content Management
    Filters System          :p14, after p13, 3d
    Notes System            :p15, after p14, 3d
    Blocklists              :p16, after p15, 3d
    Greetings               :p17, after p16, 2d
    Rules Module            :p18, after p17, 2d
    
    section Phase 5: Federations
    Federation Core         :p19, after p18, 4d
    Owner Commands          :p20, after p19, 3d
    Admin Commands          :p21, after p20, 2d
    User Commands           :p22, after p21, 2d
    Import/Export           :p23, after p22, 2d
    
    section Phase 6: Advanced Features
    Pins Module             :p24, after p23, 2d
    Log Channels            :p25, after p24, 3d
    Clean Modules           :p26, after p25, 2d
    Connections             :p27, after p26, 2d
    Disabling System        :p28, after p27, 2d
    Reports                 :p29, after p28, 2d
    
    section Phase 7: Engagement
    Leveling System         :p30, after p29, 4d
    Economy System          :p31, after p30, 3d
    Fun Commands            :p32, after p31, 2d
    Giveaways               :p33, after p32, 2d
    Tickets                 :p34, after p33, 2d
    Suggestions             :p35, after p34, 1d
    
    section Phase 8: Polish
    Utilities               :p36, after p35, 2d
    Stats Tracking          :p37, after p36, 2d
    Multi-Language          :p38, after p37, 3d
    Import/Export           :p39, after p38, 2d
    Testing                 :p40, after p39, 3d
    Documentation           :p41, after p40, 2d
    Deployment              :p42, after p41, 2d
```

---

## Request Processing Flow

### Command Handler Execution Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant B as Bot PTB
    participant M as Middleware
    participant H as Handler
    participant D as Database
    
    U->>T: /ban @user spam
    T->>B: Update received
    B->>M: Process update
    
    M->>M: Check chat type
    M->>M: Load language
    M->>M: Check permissions
    M->>M: Check if disabled
    M->>M: Check rate limit
    
    M->>H: Execute handler
    H->>D: Get user data
    D-->>H: User info
    H->>D: Get chat settings
    D-->>H: Settings
    H->>T: Ban user
    T-->>H: Success
    H->>D: Log action
    H->>U: ✅ User banned
```

---

## Module Dependencies

### Component Relationship Diagram

```mermaid
graph LR
    subgraph Core Layer
        Config[Config]
        Logger[Logger]
        Database[Database]
        Cache[Cache]
    end
    
    subgraph Application Layer
        App[Application]
        PTB[PTB Instance]
        Pyro[Pyrogram Client]
        Scheduler[Scheduler]
    end
    
    subgraph Utilities Layer
        UserRes[User Resolver]
        TimeParser[Time Parser]
        MsgParser[Message Parser]
        Validators[Validators]
    end
    
    subgraph Handler Layer
        Loader[Command Loader]
        Decorators[Decorators]
        Handlers[Command Handlers]
    end
    
    Config --> Database
    Config --> Cache
    Database --> App
    Cache --> App
    Logger --> App
    
    App --> PTB
    App --> Pyro
    App --> Scheduler
    
    Database --> UserRes
    Cache --> UserRes
    Pyro --> UserRes
    
    UserRes --> Handlers
    TimeParser --> Handlers
    MsgParser --> Handlers
    Validators --> Handlers
    
    Decorators --> Handlers
    Loader --> Handlers
    App --> Loader
```

---

## Permission Verification Flow

### Authorization Check Process

```mermaid
flowchart TD
    Start([Command Received]) --> GroupCheck{In Group?}
    GroupCheck -->|No| Private[Send Private Error]
    Private --> End([End])
    
    GroupCheck -->|Yes| UserAdmin{User is Admin?}
    UserAdmin -->|No| NoAdmin[Send No Admin Error]
    NoAdmin --> End
    
    UserAdmin -->|Yes| UserPerm{Has Required Permissions?}
    UserPerm -->|No| NoPerm[Send No Permission Error]
    NoPerm --> End
    
    UserPerm -->|Yes| BotAdmin{Bot is Admin?}
    BotAdmin -->|No| BotNoAdmin[Send Bot Not Admin Error]
    BotNoAdmin --> End
    
    BotAdmin -->|Yes| BotPerm{Bot Has Permissions?}
    BotPerm -->|No| BotNoPerm[Send Bot No Permission Error]
    BotNoPerm --> End
    
    BotPerm -->|Yes| Execute[Execute Command]
    Execute --> LogAction[Log Action to DB]
    LogAction --> Success[Send Success Message]
    Success --> End
```

---

## User Resolution Strategy

### Multi-Tier Lookup Process

```mermaid
flowchart TD
    Start([Resolve User Request]) --> Reply{Reply to Message?}
    Reply -->|Yes| GetReply[Extract User from Reply]
    GetReply --> Found([User Found])
    
    Reply -->|No| Mention{Text Mention?}
    Mention -->|Yes| GetMention[Extract User from Mention]
    GetMention --> Found
    
    Mention -->|No| Args{Has Arguments?}
    Args -->|No| Self[Use Command Sender]
    Self --> Found
    
    Args -->|Yes| IDCheck{Is User ID?}
    IDCheck -->|Yes| CheckCache1{In Cache?}
    CheckCache1 -->|Yes| Found
    CheckCache1 -->|No| CheckDB1{In Database?}
    CheckDB1 -->|Yes| CacheIt1[Cache User]
    CacheIt1 --> Found
    CheckDB1 -->|No| MTProto1{MTProto Available?}
    MTProto1 -->|Yes| FetchMT1[Fetch via MTProto]
    FetchMT1 --> SaveDB1[Save to DB]
    SaveDB1 --> Found
    MTProto1 -->|No| NotFound1([User Not Found])
    
    IDCheck -->|No| Username{Is Username?}
    Username -->|Yes| CheckCache2{In Cache?}
    CheckCache2 -->|Yes| Found
    CheckCache2 -->|No| CheckDB2{In Database?}
    CheckDB2 -->|Yes| CacheIt2[Cache User]
    CacheIt2 --> Found
    CheckDB2 -->|No| AdminList{Check Admin List?}
    AdminList -->|Yes| InAdmins{In Admin List?}
    InAdmins -->|Yes| CacheIt3[Cache User]
    CacheIt3 --> Found
    InAdmins -->|No| MTProto2{MTProto Available?}
    AdminList -->|No| MTProto2
    MTProto2 -->|Yes| ResolveMT[Resolve via MTProto]
    ResolveMT --> SaveDB2[Save to DB]
    SaveDB2 --> Found
    MTProto2 -->|No| NotFound2([User Not Found])
    
    Username -->|No| Invalid([Invalid Format])
```

---

## Anti-Flood Detection

### State Machine Implementation

```mermaid
stateDiagram-v2
    [*] --> Normal: User joins
    
    Normal --> Tracking: Message received
    Tracking --> Normal: Below threshold
    
    Tracking --> Warning: Above threshold
    Warning --> Normal: Time window expired
    Warning --> Flooding: Continues sending
    
    Flooding --> Action: Trigger action
    Action --> Muted: Mute action
    Action --> Banned: Ban action
    Action --> Kicked: Kick action
    
    Muted --> [*]: Time expired
    Banned --> [*]: Manual unban
    Kicked --> [*]: User kicked
```

---

## Captcha Verification Flow

### New Member Verification Process

```mermaid
sequenceDiagram
    participant U as New User
    participant T as Telegram
    participant B as Bot
    participant D as Database
    participant S as Scheduler
    
    U->>T: Joins group
    T->>B: New member event
    
    B->>D: Check captcha enabled
    D-->>B: Enabled
    
    B->>B: Generate captcha
    B->>U: Send captcha message
    B->>D: Store pending verification
    B->>B: Restrict user (mute)
    
    B->>S: Schedule timeout job
    
    alt User solves correctly
        U->>T: Click button/Answer
        T->>B: Callback/Message
        B->>D: Verify answer
        D-->>B: Correct
        B->>B: Unrestrict user
        B->>U: Welcome message
        B->>S: Cancel timeout job
    else Timeout expires
        S->>B: Timeout triggered
        B->>T: Kick/Ban user
        B->>D: Remove pending
    end
```

---

## Database Schema Relationships

### Entity Relationship Diagram

```mermaid
erDiagram
    CHATS ||--o{ USERS : contains
    CHATS ||--o{ FILTERS : has
    CHATS ||--o{ NOTES : has
    CHATS ||--o{ WARNINGS : tracks
    CHATS ||--o{ BLOCKLISTS : has
    FEDERATIONS ||--o{ CHATS : includes
    FEDERATIONS ||--o{ FED_BANS : has
    USERS ||--o{ WARNINGS : receives
    USERS ||--o{ FED_BANS : has
    
    CHATS {
        int id PK
        string title
        string language
        object antiflood
        object captcha
        object locks
        object greetings
    }
    
    USERS {
        int id PK
        string username
        string first_name
        object chat_data
    }
    
    FEDERATIONS {
        string id PK
        string name
        int owner_id FK
        array admin_ids
        array banned_users
    }
    
    FILTERS {
        objectid id PK
        int chat_id FK
        string trigger
        string response
    }
    
    NOTES {
        objectid id PK
        int chat_id FK
        string name
        string content
    }
    
    WARNINGS {
        objectid id PK
        int chat_id FK
        int user_id FK
        string reason
        datetime created_at
    }
```

---

## Deployment Architecture

### Production Environment Structure

```mermaid
graph TB
    subgraph Production Server
        subgraph Container or Process
            Bot[ZyraX Bot Process]
            Scheduler[Background Scheduler]
        end
        
        subgraph Services
            Mongo[(MongoDB)]
            Redis[(Redis Optional)]
            Logs[Log Files]
        end
    end
    
    subgraph External Services
        TG[Telegram API]
        Backup[Backup Storage]
    end
    
    subgraph Monitoring
        Health[Health Checks]
        Metrics[Metrics Collection]
        Alerts[Alert System]
    end
    
    Bot --> Mongo
    Bot --> Redis
    Bot --> Logs
    Scheduler --> Mongo
    Bot <--> TG
    
    Mongo --> Backup
    
    Health --> Bot
    Metrics --> Bot
    Alerts --> Health
```

---

## Development Workflow

### Feature Implementation Process

```mermaid
flowchart LR
    Start([Start Feature]) --> Design[Design Feature]
    Design --> Model[Create/Update Models]
    Model --> Handler[Write Handler]
    Handler --> Test[Write Tests]
    Test --> Manual[Manual Testing]
    Manual --> Review{Works?}
    Review -->|No| Debug[Debug Issues]
    Debug --> Handler
    Review -->|Yes| Commit[Commit Changes]
    Commit --> Next([Next Feature])
```

---

## Implementation Phases

### Phase Deliverables

#### Phase 1: Foundation (Weeks 1-2)
- Core infrastructure and dynamic loading
- Database connectivity and caching
- Basic utilities (user resolution, time parsing)
- Command registration system

#### Phase 2: Admin & Moderation (Weeks 3-4)
- Admin management (promote/demote)
- Moderation commands (ban/mute/kick)
- Warning system
- Message deletion (purge)

#### Phase 3: Protection Systems (Weeks 5-6)
- Anti-flood detection and enforcement
- Anti-raid protection
- Multi-mode captcha system
- User approval/whitelist
- Content locks (26+ types)

#### Phase 4: Content Management (Weeks 7-8)
- Custom filters with triggers
- Notes system with hashtags
- Welcome/goodbye messages
- Rules management
- Word blocklists

#### Phase 5: Federation System (Weeks 9-10)
- Cross-group ban synchronization
- Federation management
- Admin hierarchy
- Ban import/export

#### Phase 6: Advanced Features (Weeks 11-12)
- Pin management
- Log channels
- Report system
- Command disabling
- Chat connections

#### Phase 7: Engagement (Weeks 13-14)
- XP and leveling system
- Virtual economy
- Fun commands
- Giveaways
- Support tickets

#### Phase 8: Production (Weeks 15-16)
- Multi-language support
- Comprehensive testing
- Documentation completion
- Deployment configuration
- Performance optimization

---

## Architecture Principles

### Design Guidelines

**Modularity**
- Each feature module is self-contained
- Clear interfaces between components
- Minimal coupling between modules

**Async-First**
- Non-blocking I/O throughout
- Proper use of async/await
- Connection pooling for resources

**Performance**
- Multi-tier caching strategy
- Database query optimization
- Batch operations where applicable

**Reliability**
- Comprehensive error handling
- Graceful degradation
- Automatic retry mechanisms

**Observability**
- Structured logging
- Metrics collection
- Health monitoring

---

## Technical References

### External Documentation

- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Pyrogram Documentation](https://docs.pyrogram.org/)
- [Motor (MongoDB) Documentation](https://motor.readthedocs.io/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram MTProto API](https://core.telegram.org/api)

---

**Document Version:** 2.0  
**Last Updated:** October 2025  
**Status:** Production Implementation Complete