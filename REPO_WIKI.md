# Super Agent Party - Repository Wiki

## 项目概述

**Super Agent Party** 是一个多平台 AI Agent 桌面应用，支持 VRM 虚拟形象、任务自动化、多角色群聊、即时通讯机器人、直播监听、代码执行、知识库检索等功能。

- **版本**: v0.4.0-beta.1
- **许可**: AGPL-3.0
- **Python**: 3.12
- **仓库**: [heshengtao/super-agent-party](https://github.com/heshengtao/super-agent-party)

---

## 技术架构

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI |
| 前端 | Vue 3 (CDN), Element Plus, Electron |
| AI 集成 | OpenAI API, Claude API, Ollama, LangChain |
| 协议 | MCP (Model Context Protocol), A2A, WebSocket |
| 向量数据库 | FAISS |
| 代码执行 | E2B Cloud Sandbox |

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron (main.js)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  窗口管理     │ │  后端进程    │ │  IPC Handler (30+) │  │
│  │  - 主窗口    │ │  - Python   │ │  - 文件/下载       │  │
│  │  - VRM窗口  │ │  - 端口发现  │ │  - VMC/OSC        │  │
│  │  - 截图浮层 │ │             │ │  - 窗口控制        │  │
│  └──────────────┘ └──────────────┘ └────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ contextBridge
┌─────────────────────────┴───────────────────────────────────┐
│                  preload.js (桥接层)                          │
│  electronAPI | vmcAPI | downloadAPI                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                  index.html (Vue 应用)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  vue_data.js  │  renderer.js  │  vue_methods.js   │   │
│  │   状态定义     │   Vue组件     │   业务逻辑(565K)  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────┴───────────────────────────────────┐
│                  Python Backend (server.py)                  │
│  - FastAPI 服务器 (端口 3456)                               │
│  - 60+ 工具函数                                            │
│  - WebSocket 流式响应                                       │
│  - 6 大平台 Bot 集成                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
super-agent-party/
├── server.py              # 主后端 (10,019 行)
├── main.js               # Electron 主进程
├── start.js              # 启动脚本
├── py/                   # Python 模块 (50+ 文件)
│   ├── get_setting.py    # 中央配置枢纽
│   ├── task_center.py    # 任务编排中心
│   ├── sub_agent.py      # 子代理执行器
│   ├── behavior_engine.py # 行为自动化引擎
│   ├── skills.py         # 技能管理系统
│   ├── extensions.py     # 扩展管理系统
│   ├── know_base.py      # 知识库检索 (BM25+FAISS)
│   ├── mcp_clients.py    # MCP 客户端
│   ├── llm_tool.py       # LLM 工具
│   ├── web_search.py     # 网络搜索 (10+ 提供商)
│   ├── load_files.py     # 文件内容提取
│   ├── code_interpreter.py # 代码执行 (E2B)
│   ├── computer_use_tool.py # 桌面自动化
│   ├── cdp_tool.py       # Chrome DevTools Protocol
│   ├── *._bot_manager.py # 机器人管理器
│   └── ...
├── vrm/                  # VRM 资源
│   ├── animations/       # VRM 动画
│   ├── scene/           # 3D 场景
│   └── *.vrm            # VRM 模型
├── config/               # 配置文件
│   ├── settings_template.json
│   └── locales.json
├── static/               # 前端资源
│   ├── index.html       # 主页面 (777KB)
│   ├── chat.html
│   ├── js/              # JavaScript 模块
│   │   ├── preload.js   # Electron 预加载
│   │   ├── renderer.js # Vue 应用
│   │   ├── vue_data.js # 响应式状态
│   │   ├── vue_methods.js # 业务逻辑 (565KB)
│   │   ├── vrm.js      # VRM 控制
│   │   └── locales.js  # 国际化
│   └── css/
├── skills/               # Agent 技能
│   ├── skill-creator/   # 技能创建器
│   ├── officeCLI/       # Office CLI 工具
│   └── find-skills/     # 技能发现
└── doc/                  # 文档和图片
```

---

## 核心模块深度解析

### 1. server.py (10,019 行) - 主服务器

#### 1.1 架构分层

| 阶段 | 行数范围 | 职责 |
|------|----------|------|
| 第一阶段 | L1-183 | 端口初始化、命令行解析 |
| 第二阶段 | L185-323 | 环境预处理、macOS 修复 |
| 第三阶段 | L324-500 | 核心库导入 |
| 第四阶段 | L500-541 | 配置加载 |
| 第五阶段 | L556-741 | Lifespan 生命周期管理 |
| 第六阶段 | L759-782 | FastAPI 应用构建、CORS |
| 第七阶段 | L790-1300 | 工具系统 (60+ 工具) |
| 第八阶段 | L5472-10019 | API 路由实现 |

#### 1.2 核心 API 路由

**Chat/对话 API**
| 路径 | 方法 | 功能 |
|------|------|------|
| `/v1/chat/completions` | POST | OpenAI 兼容 Chat API |
| `/simple_chat` | POST | 简单对话接口 |
| `/v1/models` | GET | 获取可用模型列表 |

**任务管理 API**
| 路径 | 方法 | 功能 |
|------|------|------|
| `/v1/tasks/list` | GET | 列出任务 |
| `/v1/tasks/create` | POST | 创建任务 |
| `/v1/tasks/cancel/{task_id}` | POST | 取消任务 |
| `/v1/tasks/{task_id}` | DELETE | 删除任务 |

**文件管理 API**
| 路径 | 方法 | 功能 |
|------|------|------|
| `/load_file` | POST | 上传文件 |
| `/delete_file` | DELETE | 删除文件 |
| `/upload_vrm_model` | POST | 上传 VRM 模型 |
| `/upload_gauss_scene` | POST | 上传 Gauss 场景 |

**TTS/ASR API**
| 路径 | 方法 | 功能 |
|------|------|------|
| `/ws/asr` | WebSocket | FunASR 实时语音识别 |
| `/ws/tts` | WebSocket | TTS 语音传输 |
| `/ws/vrm` | WebSocket | VRM 实时通信 |
| `/tts` | POST | 文本转语音 |

**MCP API**
| 路径 | 方法 | 功能 |
|------|------|------|
| `/create_mcp` | POST | 创建 MCP 服务 |
| `/mcp_status/{mcp_id}` | GET | 获取 MCP 状态 |
| `/remove_mcp` | DELETE | 删除 MCP 服务 |
| `/start_HA` | POST | 启动 Home Assistant MCP |
| `/start_ChromeMCP` | POST | 启动 Chrome MCP |
| `/start_sql` | POST | 启动 SQL MCP |

**机器人管理 API** (每个平台 4 个接口)
- `POST /start_{platform}_bot` - 启动
- `POST /stop_{platform}_bot` - 停止
- `GET /{platform}_bot_status` - 状态
- `POST /reload_{platform}_bot` - 重载

**WebSocket 端点**
| 路径 | 功能 |
|------|------|
| `/ws` | 主 WebSocket 通信 |
| `/ws/tts` | TTS 语音传输 |
| `/ws/vrm` | VRM 实时通信 |
| `/ws/asr` | ASR 语音识别 |

#### 1.3 工具系统 (60+ 工具)

| 类别 | 工具数量 | 代表工具 |
|------|----------|----------|
| 网络搜索 | 12+ | DDGsearch_async, Tavily_search_async, Bing_search_async |
| 知识库 | 1 | query_knowledge_base |
| 图像生成 | 3 | pollinations_image, openai_image |
| 代码执行 | 2 | e2b_code_async, local_run_code_async |
| 浏览器控制 | 10+ | list_pages, navigate_page, take_snapshot |
| 文件操作 | 16+ | Docker 文件操作、本地文件操作 |
| 鼠标键盘 | 8 | mouse_move_async, keyboard_type_async |
| 任务管理 | 4 | create_subtask, query_task_progress |
| MCP 工具 | 动态 | 通过 mcp_client_list 调用 |

#### 1.4 权限拦截 (Human-in-the-loop)

**敏感工具列表**:
```python
SENSITIVE_TOOLS = [
    "docker_sandbox_async", "edit_file_tool", "edit_file_patch_tool",
    "todo_write_tool", "shell_tool_local", "edit_file_tool_local",
    "manage_processes_tool", "docker_manage_ports_tool", "local_net_tool",
]
```

**权限模式**:
| 模式 | 行为 |
|------|------|
| `yolo` / `cowork` | 全部放行 |
| `auto-approve` | 文件编辑/任务管理放行，危险命令拦截 |
| `default` | 全部拦截 |
| 项目配置 | 白名单覆盖 |

---

### 2. py/ 模块详解

#### 2.1 get_setting.py - 中央配置枢纽

**核心常量**:
```python
HOST, PORT              # 服务地址
USER_DATA_DIR          # 用户数据目录
DATABASE_PATH          # 向量数据库路径
SKILLS_DIR             # 技能目录
EXT_DIR                # 扩展目录
AGENT_DIR              # Agent 配置目录
MEMORY_CACHE_DIR       # 记忆缓存目录
KB_DIR                 # 知识库目录
DEFAULT_VRM_DIR        # 默认 VRM 模型目录
UPLOAD_FILES_DIR       # 上传文件存储
```

**核心函数**:
- `load_settings()` - 异步加载 JSON 配置
- `save_settings(settings)` - 保存配置到 JSON
- `configure_host_port(host, port)` - 配置服务地址
- `get_host()`, `get_port()` - 获取服务地址

---

#### 2.2 task_center.py - 任务编排中心

**数据结构**:
```python
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SubTask(BaseModel):
    task_id: str
    parent_task_id: Optional[str]  # 父子任务关系
    title: str
    description: str
    status: TaskStatus
    progress: int  # 0-100
    result: Optional[str]
    context: Dict[str, Any]  # 任务上下文
    agent_type: str  # 使用的智能体类型
```

**TaskCenter 核心方法**:
- `create_task(title, description, parent_task_id, agent_type, context)` - 创建任务
- `get_task(task_id)` - 获取任务状态
- `update_task_progress(task_id, progress, status)` - 更新进度
- `cancel_task(task_id)` - 取消任务
- `finish_task(task_id, result)` - 完成任务

---

#### 2.3 sub_agent.py - 子代理执行器

**核心类**: `SubAgentExecutor`

```python
class SubAgentExecutor:
    async def execute_subtask(
        task_id: str,
        consensus_content: Optional[str] = None,
        max_iterations: int = 30
    ) -> Dict[str, Any]:
        # 执行子任务的主循环
        # 1. 调用 LLM 流式响应
        # 2. 检查任务状态 (可能其他进程已完成)
        # 3. 支持中断和进度更新
```

**特性**:
- 与 TaskCenter 集成进行状态管理
- LLM 流式响应处理
- 最大迭代次数保护（默认30轮）
- 数据库状态驱动的终止逻辑

---

#### 2.4 behavior_engine.py - 行为自动化引擎

**触发器类型** (TriggerType):
- `time` - 定时触发
- `noInput` - 无输入触发
- `cycle` - 周期触发

**动作类型** (ActionType):
- `prompt` - 直接 Prompt
- `random` - 随机事件
- `topic` - 话题切换

**核心类**: `BehaviorEngine`
```python
class BehaviorEngine:
    def register_handler(platform, handler)
    def update_config(settings, target_map)
    def report_activity(platform, target_id)
    def start(), stop()  # 生命周期管理
```

---

#### 2.5 know_base.py - 知识库检索

**核心类**: `HybridSearch`

**检索流程**:
1. BM25 关键词检索
2. FAISS 向量相似度检索
3. Jina/Vllm Reranking 重排
4. 融合结果返回

**文本分块**: `RecursiveCharacterTextSplitter`

**API**:
```python
hybrid_search = HybridSearch(...)
results = await hybrid_search.search(query, top_k=5)
await hybrid_search.add_documents(texts, metadatas)
```

---

#### 2.6 mcp_clients.py - MCP 客户端

**传输类型支持**:
| 类型 | 说明 |
|------|------|
| `stdio` | 标准输入输出 |
| `SSE` | Server-Sent Events |
| `websocket` | WebSocket |
| `streamablehttp` | HTTP 流 |

**核心类**: `ConnectionManager`
```python
class ConnectionManager:
    async def connect(transport, transport_mode, ...)
    async def reconnect()
    async def send_request(method, params)
    # 心跳机制和自动重连
```

---

#### 2.7 web_search.py - 网络搜索 (10+ 提供商)

**支持的搜索提供商**:
- DuckDuckGo
- Tavily
- Bing
- Google
- Brave
- Exa
- Searxng
- Jina Crawler
- Crawl4ai
- Firecrawl

**特性**:
- Robots.txt 合规性检查
- SSRF 保护（禁止访问内网 IP）
- 多源聚合搜索

---

#### 2.8 code_interpreter.py - 代码执行

**执行环境**:
- **E2B 云端沙箱**: `e2b-code-interpreter`
- **本地沙箱**: `node_runner`

**支持语言**:
Python, JavaScript, TypeScript, R, Java, Go, Rust, C, C++, Ruby, PHP, Kotlin, Scala, Julia

---

#### 2.9 live_router.py - 直播路由

**支持平台**:
| 平台 | 库 | 协议 |
|------|-----|------|
| Bilibili | blivedm | WebSocket |
| YouTube | YouTubeDMClient | YouTube Data API v3 |
| Twitch | SimpleTwitchChat | IRC over SSL |

**核心类**: `ConnectionManager`
```python
class ConnectionManager:
    async def connect_bilibili(room_id)
    async def connect_youtube(video_id)
    async def connect_twitch(channel)
    async def broadcast(event_type, data)  # 广播事件
```

---

### 3. Bot Managers 机器人管理器系列

#### 3.1 feishu_bot_manager.py (1,398 行) - 飞书机器人

**核心类**: `FeishuBotManager`
**协议**: lark-oapi
**功能**:
- 卡片消息支持
- 多媒体处理
- 行为引擎集成
- 企业应用支持

#### 3.2 qq_bot_manager.py (879 行) - QQ 机器人

**核心类**: `QQBotManager`, `MyClient`
**协议**: botpy
**功能**:
- 个人消息 (C2C) 处理
- 群组消息 (Group) 处理
- 图片格式转换和发送
- 内存限制管理

#### 3.3 discord_bot_manager.py (581 行) - Discord 机器人

**核心类**: `DiscordBotManager`
**协议**: discord.py
**功能**:
- Slash commands 支持
- 消息流式响应
- 行为引擎集成
- TTS/语音合成

#### 3.4 slack_bot_manager.py (433 行) - Slack 机器人

**核心类**: `SlackBotManager`
**协议**: slack-sdk
**功能**:
- Slack Events API
- Socket Mode 支持
- 消息流式响应

#### 3.5 dingtalk_bot_manager.py (481 行) - 钉钉机器人

**核心类**: `DingtalkBotManager`
**协议**: dingtalk-stream
**功能**:
- 企业内应用支持
- 消息加解密
- 持久化存储

#### 3.6 telegram_bot_manager.py + telegram_client.py (243+573 行)

**核心类**: `TelegramBotManager`, `TelegramClient`
**协议**: Bot API (HTTP Polling)
**功能**:
- 消息处理: 文字、图片、语音
- LLM 流式响应
- Omni 音频支持 (Opus)
- TTS 语音合成
- 行为引擎回调

---

### 4. 前端架构 (Electron + Vue)

#### 4.1 main.js - Electron 主进程

**核心职责**:
- 窗口管理 (主窗口、VRM 窗口、截图浮层)
- 后端进程管理 (启动 Python server.py)
- IPC 通信 (30+ 通道)

**后端启动机制**:
```javascript
async function startBackend() {
  // 开发模式: python3 -u server.py --host 127.0.0.1 --port 3456
  // 生产模式: server 可执行文件
  // 通过日志 "REAL_PORT_FOUND:(\d+)" 捕获实际端口
}
```

**WebSecurity 配置**:
```javascript
webPreferences: {
  contextIsolation: true,   // 启用上下文隔离
  nodeIntegration: false,
  sandbox: false,
  webSecurity: false,       // 允许加载外部资源
  webviewTag: true,         // 支持 <webview> 标签
  preload: 'static/js/preload.js'
}
```

---

#### 4.2 preload.js - IPC 桥接层

**暴露的 API**:

```javascript
// electron 对象 - 基础信息
contextBridge.exposeInMainWorld('electron', {
  isMac, isWindows,
  server: { host: '127.0.0.1', port: 3456 }
});

// electronAPI 对象 - 主进程调用
contextBridge.exposeInMainWorld('electronAPI', {
  windowAction, onWindowState, toggleWindowSize, setAlwaysOnTop,
  openFileDialog, readFile, pathJoin,
  captureDesktop, showScreenshotOverlay, cropDesktop,
  startVRMWindow, stopVRMWindow, setVMCConfig,
  downloadFile, showContextMenu,
  checkForUpdates, downloadUpdate, quitAndInstall,
  registerGlobalShortcut, openDirectoryDialog, execCommand
});

// vmcAPI 对象 - VMC 协议
contextBridge.exposeInMainWorld('vmcAPI', {
  onVMCBone, sendVMCFrame, sendVMCBlend
});

// downloadAPI 对象 - 下载管理
contextBridge.exposeInMainWorld('downloadAPI', {
  onDownloadStarted, onDownloadUpdated, onDownloadDone, controlDownload
});
```

---

#### 4.3 Vue 应用架构

**入口**: `renderer.js:660`
```javascript
const app = Vue.createApp({
  data() { return vue_data },    // 来自 vue_data.js
  methods: { ...vue_methods },   // 来自 vue_methods.js
  mixins: [A2UIRendererComponent]
});
app.mount('#app');
```

**vue_data 结构** (78.6KB):
```javascript
let vue_data = {
  isMac: false, isWindows: false, isElectron: true,
  activeMenu: 'home',      // 当前菜单
  messages: [],            // 聊天消息
  settings: {},            // 用户设置
  asrSettings: {},         // ASR 配置
  ttsSettings: {},         // TTS 配置
  visionControlSettings: {}, // 视觉控制
  browserTabs: [],         // 浏览器标签页
  downloads: [],           // 下载列表
  // ... 2000+ 行
};
```

---

#### 4.4 前端与后端通信

**A. HTTP REST API (fetch)**
```javascript
GET /llm_models
POST /load_file (multipart/form-data)
POST /update_storage
```

**B. WebSocket 实时通信 (主要方式)**
```javascript
initWebSocket() {
  const ws_url = `ws://${HOST}:${PORT}/ws`;
  this.ws = new WebSocket(ws_url);
  
  this.ws.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
      case 'message':     // 聊天消息
      case 'ui':          // A2UI 组件
      case 'tool_call':   // 工具调用
      case 'tool_result': // 工具结果
    }
  };
}
```

**WebSocket 消息类型**:
| Type | 方向 | 功能 |
|------|------|------|
| `ping/pong` | 双向 | 心跳检测 |
| `save_settings` | 双向 | 保存设置 |
| `set_user_input` | 双向 | 设置用户输入 |
| `start_read/stop_read` | 双向 | TTS 朗读控制 |
| `trigger_send_message` | 双向 | 发送消息 |
| `messages_update` | 服务器→客户端 | 消息更新 |
| `start_tts/stop_tts` | 服务器→客户端 | TTS 控制 |

---

#### 4.5 A2UI 渲染器

后端返回的 JSON UI 配置，渲染为 Vue 组件:
```javascript
const A2UIRendererComponent = {
  types: ['Input', 'Select', 'Text', 'Button', 'Card', 
          'Slider', 'Switch', 'Radio', 'Checkbox', 
          'DatePicker', 'Rate', 'Group', 'List', 'Divider']
};
```

---

### 5. Skills 系统

#### 5.1 Skill 结构
```
skill-name/
├── SKILL.md (required)     # YAML frontmatter + Markdown
├── scripts/               # 可执行脚本
├── references/            # 参考文档
└── assets/               # 静态资源
```

#### 5.2 核心原则
1. **Concise is Key** - 只添加 Claude 没有的上下文
2. **Appropriate Degrees of Freedom**:
   - High: 文本指令（多路径）
   - Medium: 伪代码/参数化脚本
   - Low: 特定脚本（关键路径）

#### 5.3 内置 Skills
| Skill | 用途 |
|-------|------|
| `skill-creator` | 创建新技能的指南 |
| `officeCLI` | Office 文档处理 CLI 工具 |
| `find-skills` | 技能发现与搜索 |

---

### 6. Extension 系统

#### 6.1 Extension 数据模型
```python
class Extension:
    id: str
    name: str
    description: str
    version: str
    author: str
    systemPrompt: str  # 扩展的系统提示词
    repository: str    # Git 仓库
    category: str
    transparent: bool  # 是否透明窗口
    width, height: int  # 窗口尺寸
    enableVrmWindowSize: bool
```

#### 6.2 安装方式
- Git 仓库安装 (GitHub/Gitee)
- ZIP 上传安装
- Node.js 扩展支持 (通过 node_runner)

---

## 模块依赖关系图

```
get_setting.py (中央配置)
       │
       ├───> task_center.py ──────> sub_agent.py
       ├───> behavior_engine.py
       ├───> know_base.py
       ├───> mcp_clients.py
       ├───> utility_tools.py
       ├───> llm_tool.py
       ├───> live_router.py ─────> ytdm.py (YouTube)
       │                        ─────> twitch_service.py (Twitch)
       │                        ─────> blivedm (Bilibili)
       │
       ├───> Bot Managers
       │        │
       │        ├──> discord_bot_manager.py
       │        ├──> slack_bot_manager.py
       │        ├──> dingtalk_bot_manager.py
       │        ├──> feishu_bot_manager.py
       │        ├──> telegram_bot_manager.py ──> telegram_client.py
       │        └──> qq_bot_manager.py
       │
       ├───> code_interpreter.py
       ├───> computer_use_tool.py
       ├───> cdp_tool.py
       ├───> extensions.py
       ├───> skills.py
       ├───> web_search.py
       ├───> pollinations.py
       ├───> affection_system.py
       ├───> ebd_model_manager.py / minilm_router.py
       └───> sherpa_asr.py / sherpa_model_manager.py
```

---

## 业务逻辑亮点

1. **多平台统一消息处理**: 所有 bot managers 共享相似架构（流式响应、记忆管理、TTS）
2. **行为自动化引擎**: 支持定时、无输入、周期三种触发器，实现主动式 AI 交互
3. **混合检索**: BM25 + FAISS + Reranking 提供高质量知识库检索
4. **MCP 协议支持**: 统一客户端实现 stdio/SSE/websocket/streamablehttp 多种传输
5. **代码执行**: 支持云端 (E2B) 和本地沙箱，多语言支持
6. **实时直播监听**: 多平台统一的事件广播系统
7. **权限安全**: SOCKS 代理防御、路径遍历保护、敏感工具拦截

---

## 大型模块排名

| 排名 | 模块 | 行数 | 职责 |
|------|------|------|------|
| 1 | `cli_tool.py` | 2,327 | CLI 核心工具，Claude Agent SDK 集成 |
| 2 | `feishu_bot_manager.py` | 1,398 | 飞书机器人完整实现 |
| 3 | `web_search.py` | 1,046 | 网页搜索集成 (10+ 提供商) |
| 4 | `qq_bot_manager.py` | 879 | QQ 机器人 |
| 5 | `load_files.py` | 753 | 文件加载处理 |
| 6 | `extensions.py` | 709 | 扩展系统 |
| 7 | `skills.py` | 696 | 技能管理 |
| 8 | `utility_tools.py` | 572 | 通用工具 |
| 9 | `live_router.py` | 546 | 直播路由 |
| 10 | `cdp_tool.py` | 535 | Chrome DevTools Protocol |

---

## 快速开始

### Windows 便携版
```bash
# 下载 super-agent-party-win-v0.3.9.7z
双击 一键启动(start).bat
```

### macOS 源码版
```bash
# 1. 移除网络下载隔离
sudo xattr -rd com.apple.quarantine <文件夹>

# 2. 授予脚本执行权限
chmod +x 一键更新(update).sh 一键启动(start).sh

# 3. 运行
./一键启动(start).sh
```

### 开发者模式
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn server:app --host 127.0.0.1 --port 3456
```

---

## 修订历史

| 版本 | 日期 | 描述 |
|------|------|------|
| v0.4.0-beta.1 | 当前 | 最新开发版 |
| v0.3.9 | 之前 | 稳定版 |
