# Architecture

## System Overview

Super Agent Party is a multi-platform AI agent system with a modular architecture consisting of:

- **Frontend**: Next.js web application with real-time WebSocket communication
- **Backend**: FastAPI Python server with plugin-based architecture
- **Desktop**: Tauri 2.x wrapper for native desktop experience
- **Protocols**: MCP for tool integration, WebSocket/JSON-RPC for real-time communication

## Frontend (Next.js 14+)

Located in `frontend/src/`:

```
frontend/src/
├── app/                 # Next.js App Router pages
├── components/          # React components
├── contexts/           # React context providers
├── hooks/              # Custom React hooks
└── lib/                # Utilities and helpers
```

### Key Frontend Technologies

- **State Management**: Zustand stores for global state
- **UI Components**: shadcn/ui component library
- **Real-time Communication**: WebSocket + JSON-RPC protocol
- **Styling**: Tailwind CSS with custom design tokens

## Backend (FastAPI + Python 3.12)

Located in `py/`:

### Plugin System

```
py/plugins/
├── base.py       # Plugin base class (Plugin, PluginMetadata)
├── loader.py     # Dynamic plugin loader
├── registry.py   # Plugin registry for lifecycle management
└── hooks.py      # Extension hooks (lifecycle events)
```

The plugin system follows a lifecycle model:
1. `initialize(config)` - Load and configure plugin
2. `start()` - Start plugin operations
3. `stop()` - Graceful shutdown
4. `cleanup()` - Resource cleanup

### Core Modules

| Module | Path | Description |
|--------|------|-------------|
| Chat | `py/chat/` | WebSocket handler, streaming, history management |
| Bots | `py/bots/` | Multi-platform bot registry and managers |
| VRM | `py/vrm/` | VRM avatar and VMC protocol support |
| Knowledge | `py/knowledge/` | Document indexing, embedding, FAISS retrieval |
| Search | `py/search/` | Multi-provider web search aggregation |
| Code | `py/code/` | Sandboxed code execution |
| Extensions | `py/extensions/` | Extension management system |
| Live | `py/live_router.py` | Bilibili, YouTube, Twitch streaming |
| MCP | `py/mcp/` | Model Context Protocol client/server |

### Bot Platforms

Supported instant messaging platforms:

| Platform | Manager File |
|----------|-------------|
| Feishu | `py/feishu_bot_manager.py` |
| QQ | `py/qq_bot_manager.py` |
| Discord | `py/discord_bot_manager.py` |
| Slack | `py/slack_bot_manager.py` |
| DingTalk | `py/dingtalk_bot_manager.py` |
| Telegram | `py/telegram_bot_manager.py` |

### Data Models

```
py/models/
├── capabilities.py    # Model capability definitions
├── provider.py        # LLM provider configurations
├── registry.py        # Model/provider registry
├── config.py         # Application configuration
├── openai.py         # OpenAI-compatible models
├── anthropic.py     # Anthropic models
└── ollama.py        # Ollama local models
```

### API Routers

| Router | Prefix | Description |
|--------|--------|-------------|
| Bot API | `/api/v1/bots` | Bot lifecycle management |
| Chat API | `/api/v1/chat` | Chat completions (OpenAI-compatible) |
| Knowledge API | `/api/v1/knowledge` | Document management and retrieval |
| Search API | `/api/v1/search` | Web search aggregation |
| Code API | `/api/v1/code` | Code execution |
| Extensions API | `/api/v1/extensions` | Extension management |
| Live API | `/api/live` | Live streaming control |

## Desktop (Tauri 2.x)

Located in `src-tauri/`:

```
src-tauri/
├── src/              # Rust source code
├── Cargo.toml        # Rust dependencies
└── tauri.conf.json   # Tauri configuration
```

### Tauri Capabilities

- Window management
- System tray integration
- Native file dialogs
- IPC bridge between frontend and Rust backend
- Plugin support via Tauri plugins

## Communication Protocols

### WebSocket + JSON-RPC

Real-time communication between frontend and backend uses JSON-RPC 2.0 over WebSocket:

```json
// Client -> Server
{"method": "chat.send", "params": {"message": "Hi"}, "id": 1}

// Server -> Client
{"jsonrpc": "2.0", "id": 1, "result": {...}}
```

Supported methods:
- `chat.send` - Non-streaming message
- `chat.stream` - Streaming response
- `chat.history` - Get conversation history
- `chat.clear` - Clear conversation

### MCP (Model Context Protocol)

Exposed at `/mcp` endpoint for external AI tool integration:

```json
{
  "mcpServers": {
    "super-agent-party": {
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

## Data Flow

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Frontend  │ ←───────────────→ │   Backend   │
│  (Next.js)  │    JSON-RPC       │  (FastAPI)  │
└─────────────┘                   └─────────────┘
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           │                              │                              │
           ▼                              ▼                              ▼
    ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
    │    Bots     │              │  Knowledge   │              │   Search    │
    │  Managers   │              │    Base      │              │  Providers  │
    └─────────────┘              └─────────────┘              └─────────────┘
           │                              │                              │
           ▼                              ▼                              ▼
    ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
    │  Platform   │              │   FAISS     │              │   External  │
    │   APIs      │              │   Index     │              │    APIs     │
    └─────────────┘              └─────────────┘              └─────────────┘
```

## Extension System

Extensions are self-contained packages located in `extensions/` with the following manifest format:

```json
{
  "name": "extension-name",
  "version": "1.0.0",
  "description": "Extension description",
  "author": "Author Name",
  "systemPrompt": "Optional system prompt override",
  "repository": "https://github.com/author/extension",
  "category": "tools|integration|entertainment",
  "transparent": false,
  "width": 800,
  "height": 600
}
```

Extension API available at `GET /api/v1/extensions`.
