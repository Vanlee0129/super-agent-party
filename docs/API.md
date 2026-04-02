# API Reference

Base URL: `http://localhost:3456`

## Table of Contents

- [Chat API](#chat-api)
- [Bots API](#bots-api)
- [Knowledge Base API](#knowledge-base-api)
- [Search API](#search-api)
- [Code Execution API](#code-execution-api)
- [Extensions API](#extensions-api)
- [Live Streaming API](#live-streaming-api)
- [WebSocket Protocol](#websocket-protocol)

---

## Chat API

OpenAI-compatible chat completions API.

### POST /api/v1/chat/completions

Create a chat completion (OpenAI-compatible).

**Request:**

```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1709300000,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }]
}
```

### Streaming Response

Set `stream: true` for Server-Sent Events:

```json
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

**Response (SSE):**

```
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: {"choices":[{"delta":{"content":"!"}}]}
data: [DONE]
```

---

## Bots API

Manage multi-platform instant messaging bots.

### POST /api/v1/bots/init

Initialize all bot managers.

**Response:**

```json
{
  "status": "initialized",
  "platforms": ["feishu", "qq", "discord", "slack", "dingtalk", "telegram"]
}
```

### GET /api/v1/bots/platforms

List supported bot platforms.

**Response:**

```json
{
  "platforms": ["feishu", "qq", "discord", "slack", "dingtalk", "telegram"],
  "registered": ["feishu", "discord"]
}
```

### POST /api/v1/bots/{platform}/start

Start a bot for the specified platform.

**Path Parameters:**
- `platform`: One of `feishu`, `qq`, `discord`, `slack`, `dingtalk`, `telegram`

**Request Body (optional):**

```json
{
  "platform": "discord",
  "config": {
    "token": "your-bot-token",
    "guild_id": "123456"
  }
}
```

**Response:**

```json
{
  "status": "started",
  "platform": "discord"
}
```

### POST /api/v1/bots/{platform}/stop

Stop a running bot.

**Response:**

```json
{
  "status": "stopped",
  "platform": "discord"
}
```

### GET /api/v1/bots/{platform}/status

Get bot status.

**Response:**

```json
{
  "platform": "discord",
  "status": "running",
  "uptime": 3600.5,
  "message_count": 150,
  "error": null
}
```

### GET /api/v1/bots/{platform}/stats

Get bot statistics.

**Response:**

```json
{
  "platform": "discord",
  "uptime": 3600.5,
  "message_count": 150,
  "error_count": 2,
  "running": true
}
```

### POST /api/v1/bots/{platform}/reload

Reload bot with new configuration.

### POST /api/v1/bots/start-all

Start all registered bots.

### POST /api/v1/bots/stop-all

Stop all running bots.

### GET /api/v1/bots/status-all

Get status of all bots.

---

## Knowledge Base API

Document management and semantic search.

### POST /api/v1/knowledge/documents

Upload and index a document.

**Request:** `multipart/form-data`
- `file`: The file to upload
- `title` (optional): Document title override

**Supported file types:** txt, md, json, pdf, docx, epub, csv, png, jpg, jpeg, gif

**Response:**

```json
{
  "id": "doc-uuid",
  "title": "Document Title",
  "content": "First 1000 characters...",
  "metadata": {
    "file_name": "document.pdf",
    "file_path": "uploaded://document.pdf"
  },
  "chunk_count": 42,
  "created_at": 1709300000.0
}
```

### GET /api/v1/knowledge/documents

List all indexed documents.

**Response:**

```json
[{
  "id": "doc-uuid",
  "title": "Document Title",
  "metadata": {"file_name": "document.pdf"},
  "chunk_count": 42,
  "created_at": 1709300000.0
}]
```

### DELETE /api/v1/knowledge/documents/{doc_id}

Delete a document from the index.

**Response:**

```json
{
  "success": true,
  "message": "Document doc-uuid deleted"
}
```

### POST /api/v1/knowledge/search

Search the knowledge base.

**Query Parameters:**
- `query`: Search query string (required)
- `top_k`: Number of results (default: 5, range: 1-20)
- `rerank`: Apply reranking (default: true)

**Response:**

```json
[{
  "document_id": "doc-uuid",
  "chunk_id": "chunk-uuid",
  "content": "Matching content...",
  "score": 0.95,
  "metadata": {"file_name": "document.pdf"}
}]
```

### GET /api/v1/knowledge/config

Get current knowledge base configuration.

**Response:**

```json
{
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "top_k": 5,
  "weight": 0.5
}
```

### POST /api/v1/knowledge/config

Update knowledge base configuration.

**Request:**

```json
{
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "top_k": 5,
  "weight": 0.5
}
```

---

## Search API

Multi-provider web search aggregation.

### GET /api/v1/search/providers

List available search providers.

**Response:**

```json
[{
  "name": "duckduckgo",
  "enabled": true,
  "api_key_required": false
}, {
  "name": "tavily",
  "enabled": false,
  "api_key_required": true
}]
```

### POST /api/v1/search/query

Execute a web search.

**Request:**

```json
{
  "query": "What is the weather today?",
  "providers": ["duckduckgo", "tavily"],
  "top_k": 10,
  "rerank": false
}
```

**Response:**

```json
[{
  "title": "Weather Report",
  "url": "https://example.com/weather",
  "snippet": "Today's weather is sunny...",
  "provider": "duckduckgo",
  "score": 1.0
}]
```

### POST /api/v1/search/providers/{provider}/test

Test a search provider connection.

**Response:**

```json
{
  "provider": "tavily",
  "success": true,
  "result_count": 3,
  "results": [...]
}
```

### GET /api/v1/search/providers/{provider}/config

Get provider configuration.

### PUT /api/v1/search/providers/{provider}/config

Update provider configuration.

### POST /api/v1/search/crawl

Crawl a specific URL.

**Request:**

```json
{
  "url": "https://example.com/page",
  "provider": "jina"
}
```

---

## Code Execution API

Sandboxed code execution.

### POST /api/v1/code/execute

Execute code in a sandbox.

**Request:**

```json
{
  "language": "python",
  "code": "print('Hello, World!')",
  "timeout": 30
}
```

**Response:**

```json
{
  "success": true,
  "output": "Hello, World!\n",
  "error": null,
  "execution_time": 0.05
}
```

### Supported Languages

- `python` - Python 3.x
- `javascript` - Node.js
- `bash` - Shell commands

---

## Extensions API

Extension management.

### GET /api/v1/extensions

List all installed extensions.

**Response:**

```json
[{
  "id": "example-extension",
  "name": "Example Extension",
  "description": "An example plugin",
  "version": "1.0.0",
  "author": "Author Name",
  "status": "enabled",
  "category": "tools"
}]
```

### POST /api/v1/extensions/{ext_id}/enable

Enable an extension.

### POST /api/v1/extensions/{ext_id}/disable

Disable an extension.

### DELETE /api/v1/extensions/{ext_id}

Delete an extension.

### GET /api/v1/extensions/categories

List extension categories.

---

## Live Streaming API

Live streaming bot control.

### POST /api/live/start

Start live streaming listeners.

**Request:**

```json
{
  "config": {
    "bilibili_enabled": true,
    "bilibili_type": "web",
    "bilibili_room_id": "123456",
    "youtube_enabled": false,
    "twitch_enabled": false
  }
}
```

### POST /api/live/stop

Stop all streaming listeners.

### WebSocket /ws/live/danmu

Connect to receive live danmaku (comments) in real-time.

**Server Message:**

```json
{
  "type": "danmaku",
  "platform": "bilibili",
  "data": {
    "user": "username",
    "message": "Hello!",
    "timestamp": 1709300000
  }
}
```

---

## WebSocket Protocol

Connect to `/ws` for real-time JSON-RPC communication.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:3456/ws');
```

### Send Message

```json
{"method": "chat.send", "params": {"message": "Hello"}, "id": 1}
```

### Response

```json
{"jsonrpc": "2.0", "id": 1, "result": {...}}
```

### Error Response

```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}
```

### Supported Methods

| Method | Description |
|--------|-------------|
| `chat.send` | Send message, get response |
| `chat.stream` | Start streaming response |
| `chat.history` | Get conversation history |
| `chat.clear` | Clear conversation |

### Streaming

For `chat.stream`, after sending the request:

```json
{"method": "chat.stream", "params": {"message": "Hello"}, "id": 2}
```

Receive chunks:

```json
{"type": "chunk", "stream_id": "xxx", "content": "Hello", "done": false}
{"type": "chunk", "stream_id": "xxx", "content": "!", "done": true}
```

---

## MCP Protocol

Access via `/mcp` endpoint for external AI tool integration.

### JSON-RPC 2.0

All MCP requests use JSON-RPC 2.0 format over HTTP:

**Tools List:**

```json
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "search", "description": "Web search", "inputSchema": {...}},
      {"name": "knowledge", "description": "Knowledge base query", "inputSchema": {...}}
    ]
  }
}
```

### Claude Desktop Integration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "super-agent-party": {
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```
