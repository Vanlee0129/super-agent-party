# Migration Guide

This guide helps users migrate from previous versions or architectures of Super Agent Party.

## From Vue/Electron to React/Tauri

### Frontend Changes

| Old (Vue/Electron) | New (React/Next.js) |
|--------------------|--------------------|
| Vue 3 Composition API | React 18 with Hooks |
| Pinia stores | Zustand stores |
| Electron IPC | WebSocket + JSON-RPC |
| Vue Router | Next.js App Router |
| vue-i18n | next-intl / react-i18next |

#### Component Migration Example

**Before (Vue):**

```vue
<template>
  <div>{{ message }}</div>
  <button @click="fetchData">Load</button>
</template>

<script setup>
import { ref } from 'vue'
import { useStore } from 'pinia'

const store = useStore()
const message = ref('Hello')

const fetchData = async () => {
  const data = await store.fetchData()
  message.value = data
}
</script>
```

**After (React):**

```tsx
import { useState } from 'react'
import { useStore } from '@/hooks/useStore'

export default function MyComponent() {
  const store = useStore()
  const [message, setMessage] = useState('Hello')

  const fetchData = async () => {
    const data = await store.fetchData()
    setMessage(data)
  }

  return (
    <div>{message}</div>
    <button onClick={fetchData}>Load</button>
  )
}
```

#### State Management Migration

**Before (Pinia):**

```typescript
// stores/chat.ts
export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    loading: false
  }),
  actions: {
    async sendMessage(msg) {
      this.loading = true
      // ...
      this.loading = false
    }
  }
})
```

**After (Zustand):**

```typescript
// hooks/useChatStore.ts
import { create } from 'zustand'

interface ChatState {
  messages: Message[]
  loading: boolean
  sendMessage: (msg: string) => Promise<void>
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  loading: false,
  sendMessage: async (msg) => {
    set({ loading: true })
    // ...
    set({ loading: false })
  }
}))
```

#### IPC Communication Migration

**Before (Electron IPC):**

```typescript
// Renderer process
const result = await window.electron.invoke('bot:start', { platform: 'discord' })

// Main process (main.js)
ipcMain.handle('bot:start', async (event, { platform }) => {
  return await botManager.start(platform)
})
```

**After (WebSocket + JSON-RPC):**

```typescript
// Client
const ws = new WebSocket('ws://localhost:3456/ws')
ws.send(JSON.stringify({
  method: 'chat.send',
  params: { message: 'Hello' },
  id: 1
}))

// Or use the API directly
const response = await fetch('/api/v1/bots/discord/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ config: {} })
})
```

---

## Backend Changes

### Monolithic server.py to Plugin Architecture

The backend has been refactored from a single `server.py` into a modular plugin architecture.

#### Old Structure

```
server.py (single file, 461KB)
- All routes defined inline
- Direct imports
- No plugin system
```

#### New Structure

```
py/
├── plugins/           # Plugin system
│   ├── base.py        # Plugin base class
│   ├── loader.py      # Dynamic plugin loader
│   ├── registry.py    # Plugin registry
│   └── hooks.py       # Lifecycle hooks
├── bots/              # Bot managers
├── chat/              # Chat API
├── knowledge/         # Knowledge base
├── search/            # Search API
├── code/              # Code execution
├── extensions/        # Extension management
├── live_router.py     # Live streaming
└── mcp/               # MCP protocol
```

#### API Changes

Routes are now organized by feature:

| Old (server.py) | New |
|-----------------|-----|
| Inline route definitions | Feature-based routers |
| Direct bot imports | `BotRegistry` singleton |
| Synchronous handlers | Async handlers throughout |
| Mixed configuration | Centralized `py/get_setting.py` |

---

## Bot Platform Changes

### Unified Bot API

All bot platforms now use a unified API interface.

#### Old Approach

Each platform had separate endpoints:
- `POST /qq/start`
- `POST /discord/start`
- `POST /feishu/start`

#### New Approach

Unified REST API:
- `POST /api/v1/bots/{platform}/start`
- `POST /api/v1/bots/{platform}/stop`
- `GET /api/v1/bots/{platform}/status`
- `GET /api/v1/bots/platforms`

---

## WebSocket Protocol Changes

### Message Format

**Before:**

```json
{"type": "message", "content": "Hello", "platform": "discord"}
```

**After (JSON-RPC 2.0):**

```json
{"method": "chat.send", "params": {"message": "Hello"}, "id": 1}
```

### Error Handling

**Before:**

```json
{"error": "Method not found", "code": 404}
```

**After (JSON-RPC 2.0):**

```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}
```

---

## Knowledge Base Changes

### Indexing

**Before:**
- Direct file processing
- Custom embedding

**After:**
- Document indexer with chunking
- Configurable embedding models
- FAISS vector storage
- BM25 hybrid search

### API Changes

| Old | New |
|-----|-----|
| Custom upload endpoint | `POST /api/v1/knowledge/documents` |
| Proprietary search | `POST /api/v1/knowledge/search` |
| Hardcoded settings | `GET/PUT /api/v1/knowledge/config` |

---

## Search Provider Changes

### Unified Search Aggregation

**Before:**
- Provider-specific endpoints
- Different response formats

**After:**
- `POST /api/v1/search/query` with provider selection
- Normalized response format
- Built-in reranking

---

## Breaking Changes

### 1. WebSocket Message Format

The WebSocket protocol now uses JSON-RPC 2.0. Update your client:

```javascript
// Old
ws.send(JSON.stringify({ type: 'chat', content: 'Hi' }))

// New
ws.send(JSON.stringify({ method: 'chat.send', params: { message: 'Hi' }, id: 1 }))
```

### 2. API Response Structure

API responses are now consistently structured:

```json
// Old (inconsistent)
{"status": "ok", "data": {...}}

// New (consistent)
{"success": true, "message": "Operation completed"}
```

### 3. Configuration Storage

Settings are now stored in `data/settings.json` with a structured format. See `py/get_setting.py` for the schema.

### 4. Extension Manifest

Extensions must include a `manifest.json` with the following structure:

```json
{
  "name": "extension-name",
  "version": "1.0.0",
  "description": "Extension description",
  "author": "Author",
  "category": "tools"
}
```

---

## Upgrade Checklist

When upgrading:

1. **Update dependencies**: `pip install -r requirements.txt` and `npm install`
2. **Backup settings**: Copy `data/settings.json` before starting the new version
3. **Review plugin manifest**: Ensure all extensions have valid `manifest.json`
4. **Update API clients**: Switch to JSON-RPC 2.0 for WebSocket communication
5. **Test bot connections**: Verify platform credentials are still valid
6. **Check knowledge base**: Consider re-indexing documents after migration

---

## Getting Help

If you encounter migration issues:

- GitHub Issues: https://github.com/Vanlee0129/super-agent-party/issues
- QQ Group: 931057213
- Discord: https://discord.gg/f2dsAKKr2V
