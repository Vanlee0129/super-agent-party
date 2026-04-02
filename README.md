# Super Agent Party

A multi-platform AI agent desktop companion with VRM avatar support, real-time chat, instant messaging bots, live streaming integration, and a plugin-based extension system.

## Features

- **Multi-Platform Bots**: Feishu, QQ, Discord, Slack, DingTalk, Telegram
- **VRM Avatar**: Virtual agents with VMC protocol support
- **Chat**: WebSocket-based real-time chat with streaming
- **Knowledge Base**: Hybrid search with BM25 + FAISS
- **Web Search**: 10+ search providers (DuckDuckGo, Tavily, Bing, Google, Brave, Exa, SearXNG, Jina, Crawl4AI, Firecrawl)
- **Code Execution**: E2B cloud sandbox + local execution
- **Live Streaming**: Bilibili, YouTube, Twitch
- **Extensions**: Plugin-based extension system with sandboxed execution

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| Desktop | Tauri 2.x (Rust backend) |
| Backend | FastAPI, Python 3.12 |
| AI | OpenAI, Anthropic, Ollama |
| Protocol | MCP (Model Context Protocol), WebSocket, JSON-RPC |

## Quick Start

### Development

```bash
# Clone the repository
git clone https://github.com/Vanlee0129/super-agent-party.git
cd super-agent-party

# Install frontend dependencies
cd frontend && npm install && npm run dev

# In another terminal, start the backend
pip install -r requirements.txt
uvicorn server:app --reload --port 3456

# For desktop development
npm run tauri:dev
```

### Production Build

```bash
npm run tauri:build
```

### Docker

```bash
# Simple Docker deployment
docker pull ailm32442/super-agent-party:latest
docker run -d -p 3456:3456 -v ./super-agent-data:/app/data ailm32442/super-agent-party:latest

# With docker-compose (includes login gateway)
git clone https://github.com/Vanlee0129/super-agent-party.git
cd super-agent-party
docker-compose up -d
```

Access at http://localhost:3456/ (default credentials: root/pass)

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design details.

## API Reference

See [API.md](docs/API.md) for complete API documentation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

AGPL-3.0 - See [LICENSE](LICENSE) for details.

---

For more details, documentation, and community support, visit:
- Official Site: https://www.agentparty.top/
- Chinese Documentation: https://gcnij7egmcww.feishu.cn/wiki/DPRKwdetCiYBhPkPpXWcugujnRc
- English Guide: https://temporal-lantern-7e8.notion.site/super-agent-party-211b2b2cb6f180c899d1c27a98c4965d
