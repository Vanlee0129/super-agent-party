# Super Agent Party 重构设计方案

**版本**: v1.0
**日期**: 2026-04-02
**项目**: super-agent-party 重构
**参考项目**: CoPaw (Skills/MCP/模型配置)

---

## 1. 项目概述

### 1.1 目标

将 super-agent-party 从 Vue 3 + Electron 技术栈重构为 React + Next.js + Tauri 技术栈，实现插件化架构，保持现有功能和样式不变。

### 1.2 关键约束

- **功能不变**: 所有现有功能（聊天、VRM、Bot 管理等）必须保持
- **样式重新设计**: 采用现代极简风格（Linear/Vercel 风格）
- **多端支持**: 桌面（Tauri）、移动（独立）、Linux 智能硬件
- **后端同步重构**: FastAPI + 插件化架构

---

## 2. 技术选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Next.js (App Router) | 多平台输出能力，SSR/SSG |
| 桌面框架 | Tauri 2.x | 替代 Electron，更小包体积 |
| 移动端 | React Native 或 Flutter | 独立实现 |
| 状态管理 | Zustand | 轻量、TypeScript 友好 |
| UI 组件 | shadcn/ui + Tailwind | 现代极简、完全可定制 |
| 后端框架 | FastAPI + 插件化 | 保持 Python，模块化重构 |
| 通信协议 | WebSocket + JSON-RPC | 统一多端实时通信 |
| 文件传输 | REST API | 大文件场景更合适 |
| 参考 | CoPaw | Skills + MCP + 模型配置 |

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Tauri Desktop                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Next.js Frontend                     │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │  Chat   │ │ Settings│ │   VRM   │ │   Bot   │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  │                      │                             │  │
│  │               ┌──────┴──────┐                      │  │
│  │               │   Zustand   │                      │  │
│  │               └──────┬──────┘                      │  │
│  │               ┌──────┴──────┐                      │  │
│  │               │  WebSocket  │                      │  │
│  │               │  JSON-RPC   │                      │  │
│  │               └──────┬──────┘                      │  │
│  └──────────────────────┼──────────────────────────────┘  │
│                         │                                  │
│  ┌──────────────────────┼──────────────────────────────┐  │
│  │              Python Backend                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │ Skills  │ │   MCP   │ │  Models │ │   Bot   │  │  │
│  │  │ System  │ │ Client  │ │ Config  │ │Manager  │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 前端架构 (Next.js)

```
src/
├── app/                      # Next.js App Router
│   ├── (chat)/              # 聊天相关页面
│   ├── (settings)/          # 设置页面
│   ├── (vrn)/              # VRM 页面
│   └── api/                # API 路由
├── components/              # React 组件
│   ├── ui/                 # shadcn/ui 组件
│   ├── chat/               # 聊天组件
│   ├── settings/           # 设置组件
│   └── vrm/                # VRM 组件
├── lib/                     # 工具库
│   ├── api/                # API 客户端
│   │   ├── websocket.ts    # WebSocket 客户端
│   │   └── rest.ts        # REST 客户端
│   ├── stores/             # Zustand stores
│   └── utils/              # 工具函数
├── hooks/                   # React hooks
└── types/                   # TypeScript 类型定义
```

### 3.3 后端架构 (FastAPI 插件化)

```
py/
├── core/                    # 核心模块
│   ├── config.py           # 配置管理
│   ├── database.py        # 数据库连接
│   └── events.py          # 生命周期事件
├── plugins/                # 插件系统 (新)
│   ├── base.py            # 插件基类
│   ├── loader.py          # 插件加载器
│   └── registry.py        # 插件注册表
├── skills/                 # Skills 系统 (参考 CoPaw)
│   ├── manager.py         # 技能管理器
│   ├── scanner.py         # 技能扫描器
│   └── runner.py          # 技能执行器
├── mcp/                    # MCP 集成 (参考 CoPaw)
│   ├── client.py          # MCP 客户端
│   ├── server.py          # MCP 服务器
│   └── transport/         # 传输层 (stdio/SSE/WS)
├── models/                 # 模型配置 (参考 CoPaw)
│   ├── provider.py        # Provider 基类
│   ├── openai.py          # OpenAI Provider
│   ├── anthropic.py       # Anthropic Provider
│   ├── ollama.py          # Ollama Provider
│   └── registry.py        # 模型注册表
├── bots/                   # Bot 管理器 (保持)
│   ├── base.py           # Bot 基类
│   ├── feishu.py         # 飞书
│   ├── qq.py             # QQ
│   ├── discord.py        # Discord
│   └── ...
└── server.py              # 主服务器 (重构)
```

### 3.4 通信协议设计

**WebSocket + JSON-RPC 统一协议:**

```typescript
// 请求格式
interface JSONRPCRequest {
  jsonrpc: "2.0";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

// 响应格式
interface JSONRPCResponse {
  jsonrpc: "2.0";
  id: string;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

// WebSocket 消息类型
type WSMessage =
  | { type: "jsonrpc"; data: JSONRPCRequest | JSONRPCResponse }
  | { type: "binary"; data: ArrayBuffer }
  | { type: "ping" }
  | { type: "pong" };
```

**REST API (仅文件传输):**

```
POST /api/v1/files/upload    # 文件上传
GET  /api/v1/files/{id}     # 文件下载
DELETE /api/v1/files/{id}    # 文件删除
```

---

## 4. 三阶段实施计划

### Phase 1: 基础设施搭建 (4-6 周)

**目标**: 搭建最小可运行版本

**前端任务:**
- [ ] 初始化 Next.js + TypeScript 项目
- [ ] 配置 Tailwind CSS + shadcn/ui
- [ ] 配置 Zustand 状态管理
- [ ] 搭建基础 UI 组件库
- [ ] 实现 WebSocket + JSON-RPC 客户端
- [ ] 集成 Tauri 2.x
- [ ] 基础页面框架 (布局、导航、主题)

**后端任务:**
- [ ] 设计插件系统架构
- [ ] 重构 get_setting.py 为配置中心
- [ ] 实现 Skills 管理系统 (参考 CoPaw)
- [ ] 实现 MCP 客户端 (参考 CoPaw)
- [ ] 实现模型配置系统 (参考 CoPaw)
- [ ] 重构 server.py 为插件化架构
- [ ] 迁移现有 API 端点

**输出**: 基础 UI + 聊天功能可运行

### Phase 2: 模块迁移 (8-12 周)

**目标**: 迁移所有功能模块

**优先级顺序:**
1. 聊天功能 (最高频)
2. 设置/配置页面
3. VRM 模块
4. Bot 管理模块 (飞书/QQ/Discord/Slack/钉钉/Telegram)
5. 知识库模块
6. 扩展系统
7. 代码执行模块
8. 网络搜索模块

### Phase 3: 清理与优化 (2-4 周)

**目标**: 优化和发布准备

- [ ] 性能优化 (首屏加载、运行时性能)
- [ ] 移动端适配 (可选)
- [ ] 文档完善
- [ ] 发布准备

---

## 5. 参考 CoPaw 实现细节

### 5.1 Skills 系统

参考 `CoPaw/src/copaw/skills/` 结构:

```python
# 技能目录结构
skills/
├── skill-name/
│   ├── SKILL.md           # YAML frontmatter + Markdown
│   ├── scripts/           # 可执行脚本
│   ├── references/         # 参考文档
│   └── assets/            # 静态资源

# 技能管理器核心功能
- skill_scanner.py: 扫描和发现技能
- skill_runner.py: 执行技能
- skill_manager.py: 生命周期管理
```

### 5.2 MCP 集成

参考 `CoPaw/src/copaw/providers/mcp/` 结构:

```python
# MCP 传输类型
- stdio: 标准输入输出
- SSE: Server-Sent Events
- websocket: WebSocket
- streamablehttp: HTTP 流

# MCP 客户端核心功能
- ConnectionManager: 连接管理
- RequestHandler: 请求处理
- Transport: 传输层抽象
```

### 5.3 模型配置

参考 `CoPaw/src/copaw/providers/` 结构:

```python
# Provider 架构
providers/
├── base.py              # Provider 基类
├── openai.py            # OpenAI 实现
├── anthropic.py         # Anthropic 实现
├── ollama.py            # Ollama 实现
└── registry.py          # Provider 注册表

# 模型配置
models.py:
- ModelConfig: 模型配置
- ModelCapability: 模型能力
- ProviderRegistry: 提供者注册表
```

---

## 6. 关键设计决策

### 6.1 为什么不继续用 Electron

- Electron 包体积大 (~150MB+)
- Tauri 使用系统 WebView，包体积小 (~10MB)
- Tauri 2.x 已成熟，支持移动平台

### 6.2 为什么选择 WebSocket + JSON-RPC

- 多平台统一协议，易于实现
- 支持实时双向通信 (聊天、VRM、TTS/ASR)
- JSON-RPC 简洁，与 REST 可混合使用
- 移动端可方便实现重连和离线队列

### 6.3 为什么保持 FastAPI

- Python AI 生态丰富
- FastAPI 性能优秀
- 保持现有业务逻辑，仅重构架构

---

## 7. 风险和注意事项

### 7.1 风险

| 风险 | 缓解措施 |
|------|----------|
| VRM 性能 | WebGL/Three.js 优化，考虑 WebGPU |
| 多端同步 | 统一协议，各端独立实现 |
| 插件化复杂度 | 参考 CoPaw 成熟实现 |
| 迁移周期长 | 分阶段交付，每阶段可运行 |

### 7.2 不在本次重构范围

- 移动端具体实现 (Phase 3 可选)
- Linux 智能硬件具体实现
- 现有数据库结构变更

---

## 8. 成功标准

1. **功能完整性**: 所有现有功能在重构后正常工作
2. **性能提升**: 首屏加载时间减少 50%+
3. **包体积**: Tauri 打包体积 < 20MB
4. **代码质量**: 类型覆盖率 > 90%
5. **可维护性**: 插件化架构，模块可独立测试

---

**下一步**: 创建详细的 Phase 1 实现计划
