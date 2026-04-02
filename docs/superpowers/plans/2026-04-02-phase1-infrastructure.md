# Phase 1: Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimum runnable version with Next.js frontend + Tauri desktop + FastAPI backend plugin architecture, with basic UI and working chat.

**Architecture:** Next.js App Router frontend with Zustand state management communicates via WebSocket JSON-RPC to FastAPI backend with plugin-based architecture. Tauri 2.x wraps the web frontend as a desktop app. Backend integrates Skills, MCP, and Model configuration systems.

**Tech Stack:** Next.js 14+, TypeScript, Tailwind CSS, shadcn/ui, Zustand, Tauri 2.x, FastAPI, Python 3.12, WebSockets, JSON-RPC

---

## File Structure

### Frontend (`src/` or `frontend/`)

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Home page
│   ├── (chat)/                 # Chat routes
│   │   ├── layout.tsx          # Chat layout
│   │   └── page.tsx            # Chat main page
│   ├── (settings)/              # Settings routes
│   │   └── page.tsx            # Settings page
│   └── api/                    # API routes (if needed)
├── components/
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── chat/                   # Chat-specific components
│   │   ├── chat-container.tsx
│   │   ├── message-list.tsx
│   │   ├── message-item.tsx
│   │   ├── chat-input.tsx
│   │   └── chat-header.tsx
│   ├── layout/                 # Layout components
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── main-layout.tsx
│   └── theme/                  # Theme components
│       └── theme-provider.tsx
├── lib/
│   ├── api/
│   │   ├── websocket.ts        # WebSocket JSON-RPC client
│   │   ├── json-rpc.ts        # JSON-RPC types and helpers
│   │   └── rest.ts            # REST client for file uploads
│   ├── stores/
│   │   ├── chat-store.ts      # Chat state
│   │   ├── settings-store.ts  # Settings state
│   │   └── ui-store.ts        # UI state
│   └── utils/
│       └── cn.ts              # tailwind merge utility
├── hooks/
│   ├── use-websocket.ts        # WebSocket hook
│   └── use-chat.ts            # Chat hook
├── types/
│   ├── api.ts                 # API types
│   ├── chat.ts                # Chat types
│   └── models.ts              # Model types
├── tailwind.config.ts
├── next.config.js
└── package.json
```

### Backend (`py/`)

```
py/
├── core/                       # Core modules (NEW)
│   ├── __init__.py
│   ├── config.py              # Centralized config (refactored from get_setting.py)
│   ├── database.py            # Database connections
│   ├── events.py              # Lifecycle events
│   └── exceptions.py          # Custom exceptions
├── plugins/                    # Plugin system (NEW -参考CoPaw)
│   ├── __init__.py
│   ├── base.py                # Plugin base class and interface
│   ├── loader.py              # Plugin discovery and loading
│   ├── registry.py            # Plugin registry
│   └── hooks.py               # Plugin lifecycle hooks
├── skills/                     # Skills system (refactored)
│   ├── __init__.py
│   ├── manager.py             # Skill manager
│   ├── scanner.py             # Skill discovery
│   ├── runner.py              # Skill execution
│   └── schemas.py             # Skill schemas
├── mcp/                        # MCP integration (refactored -参考CoPaw)
│   ├── __init__.py
│   ├── client.py              # MCP client
│   ├── transport/
│   │   ├── base.py           # Transport base
│   │   ├── stdio.py          # stdio transport
│   │   ├── sse.py            # SSE transport
│   │   ├── websocket.py       # WebSocket transport
│   │   └── streamable_http.py # HTTP stream transport
│   └── protocol.py            # MCP protocol
├── models/                     # Model configuration (refactored -参考CoPaw)
│   ├── __init__.py
│   ├── provider.py            # Provider base class
│   ├── registry.py            # Provider registry
│   ├── config.py              # Model configs
│   └── capabilities.py         # Model capabilities
├── bots/                       # Bot managers (existing, minimal changes)
│   └── ... (keep as-is for Phase 1)
├── tools/                      # Tools system (existing)
│   └── ... (keep as-is for Phase 1)
└── server.py                   # Main server (refactored)
```

---

## Phase 1 Tasks

### PART A: Project Scaffolding

---

### Task A1: Initialize Next.js Project with TypeScript

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`

- [ ] **Step 1: Create frontend directory and initialize package.json**

```bash
mkdir -p frontend && cd frontend && npm init -y
```

```json
{
  "name": "super-agent-party-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zustand": "^4.5.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "lucide-react": "^0.400.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.12.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
}

module.exports = nextConfig
```

- [ ] **Step 4: Create tailwind.config.ts**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 5: Create postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Create src/app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/next.config.js frontend/tailwind.config.ts frontend/postcss.config.js frontend/src/app/globals.css
git commit -m "feat(frontend): scaffold Next.js + TypeScript + Tailwind project"
```

---

### Task A2: Setup shadcn/ui Components

**Files:**
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/card.tsx`

- [ ] **Step 1: Create lib/utils.ts (tailwind-merge utility)**

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: Create button component**

```typescript
import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline:
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
```

- [ ] **Step 3: Create input component**

```typescript
import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

export { Input }
```

- [ ] **Step 4: Create card component**

```typescript
import * as React from 'react'
import { cn } from '@/lib/utils'

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      className
    )}
    {...props}
  />
))
Card.displayName = 'Card'

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-2xl font-semibold leading-none tracking-tight',
      className
    )}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/utils.ts frontend/src/components/ui/button.tsx frontend/src/components/ui/input.tsx frontend/src/components/ui/card.tsx
git commit -m "feat(frontend): add shadcn/ui base components (Button, Input, Card)"
```

---

### Task A3: Setup Zustand Stores

**Files:**
- Create: `frontend/src/lib/stores/chat-store.ts`
- Create: `frontend/src/lib/stores/settings-store.ts`
- Create: `frontend/src/lib/stores/ui-store.ts`

- [ ] **Step 1: Create chat store**

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  setMessages: (messages: Message[]) => void
  clearMessages: () => void
  setLoading: (isLoading: boolean) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      isLoading: false,
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: crypto.randomUUID(),
              timestamp: Date.now(),
            },
          ],
        })),
      setMessages: (messages) => set({ messages }),
      clearMessages: () => set({ messages: [] }),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'chat-storage',
    }
  )
)
```

- [ ] **Step 2: Create settings store**

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ModelConfig {
  id: string
  name: string
  provider: 'openai' | 'anthropic' | 'ollama' | 'minimax'
  apiKey?: string
  baseUrl?: string
  modelName: string
}

export interface Settings {
  theme: 'light' | 'dark' | 'system'
  language: string
  activeModel: string
  models: ModelConfig[]
}

interface SettingsState {
  settings: Settings
  updateSettings: (settings: Partial<Settings>) => void
  resetSettings: () => void
}

const defaultSettings: Settings = {
  theme: 'system',
  language: 'zh-CN',
  activeModel: 'gpt-4',
  models: [],
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'settings-storage',
    }
  )
)
```

- [ ] **Step 3: Create UI store**

```typescript
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  activeMenu: string
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setActiveMenu: (menu: string) => void
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  activeMenu: 'home',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveMenu: (menu) => set({ activeMenu: menu }),
}))
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/stores/chat-store.ts frontend/src/lib/stores/settings-store.ts frontend/src/lib/stores/ui-store.ts
git commit -m "feat(frontend): add Zustand stores (chat, settings, ui)"
```

---

### Task A4: Create WebSocket JSON-RPC Client

**Files:**
- Create: `frontend/src/lib/api/json-rpc.ts`
- Create: `frontend/src/lib/api/websocket.ts`

- [ ] **Step 1: Create JSON-RPC types and helpers**

```typescript
// JSON-RPC 2.0 types
export interface JSONRPCRequest {
  jsonrpc: '2.0'
  id: string
  method: string
  params?: Record<string, unknown>
}

export interface JSONRPCResponse {
  jsonrpc: '2.0'
  id: string
  result?: unknown
  error?: {
    code: number
    message: string
    data?: unknown
  }
}

export interface JSONRPCError {
  code: number
  message: string
  data?: unknown
}

export type WSMessage =
  | { type: 'jsonrpc'; data: JSONRPCRequest | JSONRPCResponse }
  | { type: 'binary'; data: ArrayBuffer }
  | { type: 'ping' }
  | { type: 'pong' }

// Error codes
export const JSONRPC_ERRORS = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
} as const

// Helper to create request
export function createRequest(
  method: string,
  params?: Record<string, unknown>
): JSONRPCRequest {
  return {
    jsonrpc: '2.0',
    id: crypto.randomUUID(),
    method,
    params,
  }
}

// Helper to check if message is response
export function isJSONRPCResponse(
  msg: JSONRPCRequest | JSONRPCResponse
): msg is JSONRPCResponse {
  return 'result' in msg || 'error' in msg
}
```

- [ ] **Step 2: Create WebSocket client with reconnection**

```typescript
import {
  JSONRPCRequest,
  JSONRPCResponse,
  createRequest,
  isJSONRPCResponse,
  WSMessage,
} from './json-rpc'

type MessageHandler = (response: JSONRPCResponse) => void
type ConnectionHandler = () => void

interface WebSocketClientConfig {
  url: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  pingInterval?: number
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectInterval: number
  private maxReconnectAttempts: number
  private pingInterval: number
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private pingTimer: ReturnType<typeof setInterval> | null = null
  private pendingRequests = new Map<string, MessageHandler>()
  private onConnectHandlers: ConnectionHandler[] = []
  private onDisconnectHandlers: ConnectionHandler[] = []

  constructor(config: WebSocketClientConfig) {
    this.url = config.url
    this.reconnectInterval = config.reconnectInterval ?? 3000
    this.maxReconnectAttempts = config.maxReconnectAttempts ?? 5
    this.pingInterval = config.pingInterval ?? 30000
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        this.ws.binaryType = 'arraybuffer'

        this.ws.onopen = () => {
          this.reconnectAttempts = 0
          this.startPing()
          this.onConnectHandlers.forEach((handler) => handler())
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onclose = () => {
          this.stopPing()
          this.onDisconnectHandlers.forEach((handler) => handler())
          this.scheduleReconnect()
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  private handleMessage(data: string | ArrayBuffer) {
    if (data instanceof ArrayBuffer) {
      // Binary message (e.g., audio)
      return
    }

    try {
      const message: WSMessage = JSON.parse(data)

      if (message.type === 'ping') {
        this.send({ type: 'pong' })
        return
      }

      if (message.type !== 'jsonrpc') return

      const response = message.data as JSONRPCResponse
      if (isJSONRPCResponse(response)) {
        const handler = this.pendingRequests.get(response.id)
        if (handler) {
          handler(response)
          this.pendingRequests.delete(response.id)
        }
      }
    } catch (error) {
      console.error('Failed to parse message:', error)
    }
  }

  private startPing() {
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping' })
    }, this.pingInterval)
  }

  private stopPing() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      console.log(
        `Reconnecting... attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      )
      this.connect().catch(console.error)
    }, this.reconnectInterval)
  }

  send(message: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  async request<T = unknown>(
    method: string,
    params?: Record<string, unknown>,
    timeout = 30000
  ): Promise<T> {
    const request = createRequest(method, params)

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(request.id)
        reject(new Error(`Request ${method} timed out`))
      }, timeout)

      this.pendingRequests.set(request.id, (response) => {
        clearTimeout(timeoutId)
        if (response.error) {
          reject(new Error(response.error.message))
        } else {
          resolve(response.result as T)
        }
      })

      this.send({ type: 'jsonrpc', data: request })
    })
  }

  onConnect(handler: ConnectionHandler) {
    this.onConnectHandlers.push(handler)
  }

  onDisconnect(handler: ConnectionHandler) {
    this.onDisconnectHandlers.push(handler)
  }

  disconnect() {
    this.stopPing()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
```

- [ ] **Step 3: Create WebSocket hook**

```typescript
import { useEffect, useState, useCallback, useRef } from 'react'
import { WebSocketClient } from '@/lib/api/websocket'
import { useUIStore } from '@/lib/stores/ui-store'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const clientRef = useRef<WebSocketClient | null>(null)
  const { setActiveMenu } = useUIStore()

  const connect = useCallback(async () => {
    try {
      const wsUrl =
        typeof window !== 'undefined'
          ? `ws://${window.location.hostname}:3456/ws`
          : 'ws://localhost:3456/ws'

      const client = new WebSocketClient({
        url: wsUrl,
        reconnectInterval: 3000,
        maxReconnectAttempts: 10,
      })

      client.onConnect(() => {
        setIsConnected(true)
        setError(null)
      })

      client.onDisconnect(() => {
        setIsConnected(false)
      })

      await client.connect()
      clientRef.current = client
    } catch (err) {
      setError(err as Error)
      setIsConnected(false)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect()
      clientRef.current = null
    }
  }, [])

  const sendMessage = useCallback(
    async (method: string, params?: Record<string, unknown>) => {
      if (!clientRef.current) {
        throw new Error('WebSocket not connected')
      }
      return clientRef.current.request(method, params)
    },
    []
  )

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage,
    client: clientRef.current,
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api/json-rpc.ts frontend/src/lib/api/websocket.ts frontend/src/hooks/use-websocket.ts
git commit -m "feat(frontend): add WebSocket JSON-RPC client with reconnection"
```

---

### Task A5: Create Basic Layout Components

**Files:**
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/header.tsx`
- Create: `frontend/src/components/layout/main-layout.tsx`

- [ ] **Step 1: Create sidebar component**

```typescript
'use client'

import { cn } from '@/lib/utils'
import { useUIStore } from '@/lib/stores/ui-store'
import { Button } from '@/components/ui/button'
import {
  Home,
  MessageSquare,
  Settings,
  Bot,
  BookOpen,
  Layers,
} from 'lucide-react'

const menuItems = [
  { id: 'home', label: '首页', icon: Home },
  { id: 'chat', label: '聊天', icon: MessageSquare },
  { id: 'bots', label: '机器人', icon: Bot },
  { id: 'knowledge', label: '知识库', icon: BookOpen },
  { id: 'extensions', label: '扩展', icon: Layers },
  { id: 'settings', label: '设置', icon: Settings },
]

export function Sidebar() {
  const { sidebarOpen, activeMenu, setActiveMenu } = useUIStore()

  return (
    <aside
      className={cn(
        'flex h-screen w-64 flex-col border-r bg-card transition-all duration-300',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="flex h-14 items-center border-b px-4">
        <h1 className="text-lg font-semibold">Super Agent</h1>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          return (
            <Button
              key={item.id}
              variant={activeMenu === item.id ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => setActiveMenu(item.id)}
            >
              <Icon className="mr-2 h-4 w-4" />
              {item.label}
            </Button>
          )
        })}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: Create header component**

```typescript
'use client'

import { useUIStore } from '@/lib/stores/ui-store'
import { Button } from '@/components/ui/button'
import { Menu, Moon, Sun } from 'lucide-react'
import { useSettingsStore } from '@/lib/stores/settings-store'

export function Header() {
  const { toggleSidebar } = useUIStore()
  const { settings, updateSettings } = useSettingsStore()

  const toggleTheme = () => {
    const themes = ['light', 'dark', 'system'] as const
    const currentIndex = themes.indexOf(settings.theme)
    const nextTheme = themes[(currentIndex + 1) % themes.length]
    updateSettings({ theme: nextTheme })
  }

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={toggleTheme}>
          {settings.theme === 'dark' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </Button>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Create main layout component**

```typescript
'use client'

import { Sidebar } from './sidebar'
import { Header } from './header'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto bg-background p-4">
          {children}
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Update root layout**

```typescript
import type { Metadata } from 'next'
import './globals.css'
import { MainLayout } from '@/components/layout/main-layout'

export const metadata: Metadata = {
  title: 'Super Agent Party',
  description: 'Multi-platform AI Agent Desktop Application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  )
}
```

- [ ] **Step 5: Create home page**

```typescript
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function HomePage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="mb-8 text-3xl font-bold">欢迎使用 Super Agent Party</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>AI 聊天</CardTitle>
            <CardDescription>与 AI 进行自然语言对话</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              支持多种 AI 模型，包括 GPT-4、Claude、Ollama 等。
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>VRM 虚拟形象</CardTitle>
            <CardDescription>实时驱动的 3D 虚拟形象</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              使用 VRM 模型，配合 TTS/ASR 实现实时对话。
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>多平台 Bot</CardTitle>
            <CardDescription>连接各大社交平台</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              支持飞书、QQ、Discord、Slack、钉钉、Telegram 等。
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/layout/sidebar.tsx frontend/src/components/layout/header.tsx frontend/src/components/layout/main-layout.tsx frontend/src/app/layout.tsx frontend/src/app/page.tsx
git commit -m "feat(frontend): add basic layout components (sidebar, header, main-layout)"
```

---

### Task A6: Integrate Tauri 2.x

**Files:**
- Create: `src-tauri/Cargo.toml`
- Create: `src-tauri/tauri.conf.json`
- Create: `src-tauri/src/main.rs`
- Create: `src-tauri/src/lib.rs`
- Modify: `frontend/package.json` (add tauri scripts)

- [ ] **Step 1: Create Tauri configuration**

```toml
[package]
name = "super-agent-party"
version = "0.1.0"
description = "Multi-platform AI Agent Desktop Application"
authors = ["you"]
edition = "2021"

[lib]
name = "super_agent_party_lib"
crate-type = ["lib", "cdylib", "staticlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["devtools"] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[profile.release]
panic = "abort"
codegen-units = 1
lto = true
opt-level = "s"
strip = true
```

- [ ] **Step 2: Create tauri.conf.json**

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Super Agent Party",
  "version": "0.1.0",
  "identifier": "com.superagent.party",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:3000",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../.next"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [
      {
        "title": "Super Agent Party",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "center": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

- [ ] **Step 3: Create Rust source files**

```rust
// src-tauri/src/lib.rs
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

```rust
// src-tauri/src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    super_agent_party_lib::run()
}
```

```rust
// src-tauri/build.rs
fn main() {
    tauri_build::build()
}
```

- [ ] **Step 4: Update frontend package.json with tauri scripts**

```json
{
  "scripts": {
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.0.0"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add src-tauri/Cargo.toml src-tauri/tauri.conf.json src-tauri/src/lib.rs src-tauri/src/main.rs src-tauri/build.rs
git commit -m "feat(tauri): add Tauri 2.x integration"
```

---

### PART B: Backend Plugin Architecture

---

### Task B1: Create Backend Plugin System (参考 CoPaw)

**Files:**
- Create: `py/core/__init__.py`
- Create: `py/core/config.py`
- Create: `py/core/exceptions.py`
- Create: `py/core/events.py`
- Create: `py/plugins/base.py`
- Create: `py/plugins/loader.py`
- Create: `py/plugins/registry.py`
- Create: `py/plugins/hooks.py`

- [ ] **Step 1: Create core config.py (centralized config)**

```python
"""Centralized configuration management."""
import os
from pathlib import Path
from typing import Optional
import json

class Config:
    """Central configuration class."""

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 3456
        self.user_data_dir = self._get_user_data_dir()
        self.database_path = self.user_data_dir / "data"
        self.skills_dir = self.user_data_dir / "skills"
        self.extensions_dir = self.user_data_dir / "extensions"
        self.agent_dir = self.user_data_dir / "agents"
        self.memory_cache_dir = self.user_data_dir / "memory"
        self.kb_dir = self.user_data_dir / "knowledge_base"
        self.default_vrm_dir = self.user_data_dir / "vrm"
        self.upload_files_dir = self.user_data_dir / "uploads"

        self._ensure_directories()

    def _get_user_data_dir(self) -> Path:
        """Get user data directory."""
        if os.environ.get("PORTABLE_MODE"):
            return Path("user_data")
        elif os.name == "nt":
            appdata = os.environ.get("APPDATA", "")
            return Path(appdata) / "SuperAgentParty"
        else:
            return Path.home() / ".super-agent-party"

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [
            self.user_data_dir,
            self.database_path,
            self.skills_dir,
            self.extensions_dir,
            self.agent_dir,
            self.memory_cache_dir,
            self.kb_dir,
            self.default_vrm_dir,
            self.upload_files_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default=None):
        """Get configuration value."""
        return getattr(self, key, default)

    def set(self, key: str, value):
        """Set configuration value."""
        setattr(self, key, value)

    def load_from_file(self, path: Path):
        """Load configuration from JSON file."""
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

    def save_to_file(self, path: Path):
        """Save configuration to JSON file."""
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


# Global config instance
config = Config()
```

- [ ] **Step 2: Create core exceptions.py**

```python
"""Custom exceptions for the application."""

class SuperAgentError(Exception):
    """Base exception for all application errors."""
    pass


class PluginError(SuperAgentError):
    """Exception raised for plugin-related errors."""
    pass


class SkillError(SuperAgentError):
    """Exception raised for skill-related errors."""
    pass


class MCPError(SuperAgentError):
    """Exception raised for MCP-related errors."""
    pass


class ModelError(SuperAgentError):
    """Exception raised for model-related errors."""
    pass


class ConfigurationError(SuperAgentError):
    """Exception raised for configuration errors."""
    pass


class APIError(SuperAgentError):
    """Exception raised for API errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
```

- [ ] **Step 3: Create core/events.py**

```python
"""Event system for application lifecycle."""
from typing import Callable, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Event:
    """Event object."""
    type: str
    data: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventEmitter:
    """Simple event emitter."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable):
        """Register an event handler."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)

    def off(self, event: str, handler: Callable):
        """Unregister an event handler."""
        if event in self._listeners:
            self._listeners[event].remove(handler)

    def emit(self, event: str, data: Dict = None):
        """Emit an event."""
        e = Event(type=event, data=data or {})
        if event in self._listeners:
            for handler in self._listeners[event]:
                handler(e)


# Global event emitter
events = EventEmitter()
```

- [ ] **Step 4: Create plugins/base.py (Plugin base class)**

```python
"""Base plugin interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PluginMetadata:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: list = field(default_factory=list)
    loaded_at: Optional[datetime] = None


class Plugin(ABC):
    """Base class for all plugins."""

    def __init__(self):
        self._metadata: Optional[PluginMetadata] = None
        self._enabled = False

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the plugin."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the plugin."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def enable(self):
        """Enable the plugin."""
        self._enabled = True

    def disable(self):
        """Disable the plugin."""
        self._enabled = False
```

- [ ] **Step 5: Create plugins/registry.py**

```python
"""Plugin registry for managing plugins."""
from typing import Dict, Optional, List, Type
from .base import Plugin, PluginMetadata
from ..core.exceptions import PluginError

class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._metadata_cache: Dict[str, PluginMetadata] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        metadata = plugin.metadata
        if metadata.id in self._plugins:
            raise PluginError(f"Plugin {metadata.id} already registered")
        self._plugins[metadata.id] = plugin
        self._metadata_cache[metadata.id] = metadata

    def unregister(self, plugin_id: str) -> None:
        """Unregister a plugin."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
        if plugin_id in self._metadata_cache:
            del self._metadata_cache[plugin_id]

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def list_all(self) -> List[PluginMetadata]:
        """List all registered plugins."""
        return list(self._metadata_cache.values())

    def list_enabled(self) -> List[PluginMetadata]:
        """List all enabled plugins."""
        return [
            m for m in self._metadata_cache.values()
            if self._plugins[m.id].enabled
        ]

    @property
    def plugins(self) -> Dict[str, Plugin]:
        """Get all plugins."""
        return self._plugins


# Global registry
registry = PluginRegistry()
```

- [ ] **Step 6: Create plugins/loader.py**

```python
"""Plugin loader for discovering and loading plugins."""
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Type
from .base import Plugin
from .registry import registry
from ..core.exceptions import PluginError

class PluginLoader:
    """Loads plugins from various sources."""

    def __init__(self, plugin_dirs: List[Path] = None):
        self.plugin_dirs = plugin_dirs or []

    def load_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all plugins from a directory."""
        loaded = []
        if not directory.exists():
            return loaded

        for path in directory.iterdir():
            if path.is_file() and path.suffix == ".py":
                try:
                    plugin = self._load_from_file(path)
                    if plugin:
                        registry.register(plugin)
                        loaded.append(plugin)
                except Exception as e:
                    print(f"Failed to load plugin from {path}: {e}")

        return loaded

    def _load_from_file(self, path: Path) -> Optional[Plugin]:
        """Load a plugin from a Python file."""
        module_name = f"plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find Plugin subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    return attr()

        return None

    def load_builtin_plugins(self) -> List[Plugin]:
        """Load built-in plugins."""
        loaded = []
        builtin_path = Path(__file__).parent.parent / "builtin_plugins"
        if builtin_path.exists():
            loaded.extend(self.load_from_directory(builtin_path))
        return loaded
```

- [ ] **Step 7: Create plugins/hooks.py**

```python
"""Plugin lifecycle hooks."""
from typing import Callable, List
from enum import Enum

class Hook(str, Enum):
    """Plugin lifecycle hooks."""
    BEFORE_STARTUP = "before_startup"
    AFTER_STARTUP = "after_startup"
    BEFORE_SHUTDOWN = "before_shutdown"
    AFTER_SHUTDOWN = "after_shutdown"
    ON_REQUEST = "on_request"
    ON_MESSAGE = "on_message"

class PluginHooks:
    """Manages plugin lifecycle hooks."""

    def __init__(self):
        self._handlers: dict[Hook, List[Callable]] = {
            hook: [] for hook in Hook
        }

    def register(self, hook: Hook, handler: Callable):
        """Register a hook handler."""
        self._handlers[hook].append(handler)

    def unregister(self, hook: Hook, handler: Callable):
        """Unregister a hook handler."""
        if handler in self._handlers[hook]:
            self._handlers[hook].remove(handler)

    async def emit(self, hook: Hook, **kwargs):
        """Emit a hook, calling all handlers."""
        for handler in self._handlers[hook]:
            await handler(**kwargs)


# Global hooks instance
hooks = PluginHooks()
```

- [ ] **Step 8: Commit**

```bash
git add py/core/__init__.py py/core/config.py py/core/exceptions.py py/core/events.py py/plugins/__init__.py py/plugins/base.py py/plugins/registry.py py/plugins/loader.py py/plugins/hooks.py
git commit -m "feat(backend): add plugin system foundation (base, registry, loader, hooks)"
```

---

### Task B2: Create Skills System (参考 CoPaw)

**Files:**
- Create: `py/skills/__init__.py`
- Create: `py/skills/schemas.py`
- Create: `py/skills/manager.py`
- Create: `py/skills/scanner.py`
- Create: `py/skills/runner.py`

- [ ] **Step 1: Create skills/schemas.py**

```python
"""Skill schemas and types."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class SkillMetadata:
    """Skill metadata."""
    id: str
    name: str
    description: str
    version: str
    author: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"

@dataclass
class SkillParameter:
    """Skill parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None

@dataclass
class SkillManifest:
    """Skill manifest definition."""
    metadata: SkillMetadata
    parameters: List[SkillParameter] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)  # script_name -> path
    references: List[str] = field(default_factory=list)

@dataclass
class SkillExecution:
    """Skill execution context."""
    skill_id: str
    parameters: Dict[str, Any]
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
```

- [ ] **Step 2: Create skills/manager.py**

```python
"""Skill manager for managing skill lifecycle."""
from typing import Dict, List, Optional
from pathlib import Path
from .schemas import SkillManifest, SkillExecution
from .scanner import SkillScanner
from ..core.exceptions import SkillError

class SkillManager:
    """Manages skills lifecycle."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.scanner = SkillScanner(skills_dir)
        self._skills: Dict[str, SkillManifest] = {}
        self._executions: Dict[str, SkillExecution] = {}

    async def load_all(self) -> List[SkillManifest]:
        """Scan and load all skills."""
        manifests = await self.scanner.scan_all()
        for manifest in manifests:
            self._skills[manifest.metadata.id] = manifest
        return manifests

    def get(self, skill_id: str) -> Optional[SkillManifest]:
        """Get a skill manifest by ID."""
        return self._skills.get(skill_id)

    def list_all(self) -> List[SkillManifest]:
        """List all loaded skills."""
        return list(self._skills.values())

    def list_by_category(self, category: str) -> List[SkillManifest]:
        """List skills by category."""
        return [
            s for s in self._skills.values()
            if s.metadata.category == category
        ]

    async def execute(
        self,
        skill_id: str,
        parameters: Dict[str, any]
    ) -> SkillExecution:
        """Execute a skill."""
        manifest = self.get(skill_id)
        if not manifest:
            raise SkillError(f"Skill {skill_id} not found")

        execution = SkillExecution(
            skill_id=skill_id,
            parameters=parameters
        )

        try:
            # Validate parameters
            for param in manifest.parameters:
                if param.required and param.name not in parameters:
                    raise SkillError(f"Missing required parameter: {param.name}")

            # Execute (placeholder - actual execution delegated to runner)
            execution.result = {"status": "success"}
            execution.completed_at = datetime.now()
        except Exception as e:
            execution.error = str(e)
            execution.completed_at = datetime.now()

        self._executions[skill_id] = execution
        return execution

    def get_execution(self, skill_id: str) -> Optional[SkillExecution]:
        """Get execution history for a skill."""
        return self._executions.get(skill_id)
```

- [ ] **Step 3: Create skills/scanner.py**

```python
"""Skill scanner for discovering skills."""
import yaml
from pathlib import Path
from typing import List, Optional
from .schemas import SkillManifest, SkillMetadata, SkillParameter

class SkillScanner:
    """Scans directories for skills."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    async def scan_all(self) -> List[SkillManifest]:
        """Scan all skill directories."""
        manifests = []
        if not self.skills_dir.exists():
            return manifests

        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                manifest = await self.scan_skill(skill_path)
                if manifest:
                    manifests.append(manifest)

        return manifests

    async def scan_skill(self, skill_path: Path) -> Optional[SkillManifest]:
        """Scan a single skill directory."""
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return None

        try:
            content = skill_md.read_text()
            return self._parse_skill_md(content, skill_path)
        except Exception as e:
            print(f"Failed to parse skill {skill_path}: {e}")
            return None

    def _parse_skill_md(self, content: str, skill_path: Path) -> SkillManifest:
        """Parse SKILL.md file."""
        # Split frontmatter and content
        parts = content.split("---")
        if len(parts) < 3:
            raise ValueError("Invalid SKILL.md format")

        frontmatter = yaml.safe_load(parts[1])

        metadata = SkillMetadata(
            id=frontmatter.get("id", skill_path.name),
            name=frontmatter.get("name", skill_path.name),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", ""),
            tags=frontmatter.get("tags", []),
            category=frontmatter.get("category", "general"),
        )

        parameters = [
            SkillParameter(
                name=p["name"],
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", False),
                default=p.get("default"),
            )
            for p in frontmatter.get("parameters", [])
        ]

        scripts = {}
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.iterdir():
                if script.is_file():
                    scripts[script.stem] = str(script)

        return SkillManifest(
            metadata=metadata,
            parameters=parameters,
            scripts=scripts,
            references=frontmatter.get("references", []),
        )
```

- [ ] **Step 4: Create skills/runner.py**

```python
"""Skill runner for executing skills."""
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .schemas import SkillManifest, SkillExecution
from ..core.exceptions import SkillError

class SkillRunner:
    """Executes skills."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    async def run(
        self,
        manifest: SkillManifest,
        parameters: Dict[str, Any],
        script_name: str = "run"
    ) -> Any:
        """Run a skill script."""
        script_path = manifest.scripts.get(script_name)
        if not script_path:
            raise SkillError(f"Script {script_name} not found in skill {manifest.metadata.id}")

        script_file = self.skills_dir / manifest.metadata.id / script_path
        if not script_file.exists():
            raise SkillError(f"Script file not found: {script_file}")

        # Determine how to run based on file extension
        result = await self._execute_script(script_file, parameters)
        return result

    async def _execute_script(
        self,
        script_path: Path,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a script file."""
        suffix = script_path.suffix.lower()

        if suffix == ".py":
            return await self._run_python(script_path, parameters)
        elif suffix in [".sh", ".bash"]:
            return await self._run_shell(script_path, parameters)
        elif suffix == ".js":
            return await self._run_node(script_path, parameters)
        else:
            raise SkillError(f"Unsupported script type: {suffix}")

    async def _run_python(self, script: Path, params: Dict) -> Dict:
        """Run Python script."""
        cmd = ["python3", str(script)]
        for key, value in params.items():
            cmd.extend([f"--{key}", str(value)])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
        }

    async def _run_shell(self, script: Path, params: Dict) -> Dict:
        """Run shell script."""
        cmd = [str(script)]
        for key, value in params.items():
            cmd.extend([f"--{key}", str(value)])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
        }

    async def _run_node(self, script: Path, params: Dict) -> Dict:
        """Run Node.js script."""
        cmd = ["node", str(script)]
        for key, value in params.items():
            cmd.extend([f"--{key}", str(value)])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
        }
```

- [ ] **Step 5: Commit**

```bash
git add py/skills/__init__.py py/skills/schemas.py py/skills/manager.py py/skills/scanner.py py/skills/runner.py
git commit -m "feat(backend): add Skills system (manager, scanner, runner) - CoPaw style"
```

---

### Task B3: Create MCP Integration (参考 CoPaw)

**Files:**
- Create: `py/mcp/__init__.py`
- Create: `py/mcp/protocol.py`
- Create: `py/mcp/transport/__init__.py`
- Create: `py/mcp/transport/base.py`
- Create: `py/mcp/transport/stdio.py`
- Create: `py/mcp/transport/websocket.py`
- Create: `py/mcp/client.py`

- [ ] **Step 1: Create mcp/protocol.py**

```python
"""MCP protocol definitions."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class MCPMethod(str, Enum):
    """MCP protocol methods."""
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

@dataclass
class MCPRequest:
    """MCP JSON-RPC request."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

@dataclass
class MCPResponse:
    """MCP JSON-RPC response."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

def create_request(method: str, params: Dict = None, req_id: str = None) -> MCPRequest:
    """Create an MCP request."""
    return MCPRequest(
        jsonrpc="2.0",
        id=req_id or str(id({})),
        method=method,
        params=params or {}
    )

def parse_response(data: str) -> MCPResponse:
    """Parse JSON-RPC response."""
    obj = json.loads(data)
    return MCPResponse(
        jsonrpc=obj.get("jsonrpc", "2.0"),
        id=obj.get("id"),
        result=obj.get("result"),
        error=obj.get("error")
    )
```

- [ ] **Step 2: Create mcp/transport/base.py**

```python
"""Base transport interface."""
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any

class Transport(ABC):
    """Base class for MCP transports."""

    def __init__(self):
        self._message_handler: Optional[Callable[[str], None]] = None
        self._error_handler: Optional[Callable[[Exception], None]] = None

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the transport."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the transport."""
        pass

    @abstractmethod
    async def send(self, message: str) -> None:
        """Send a message."""
        pass

    @abstractmethod
    async def receive(self) -> str:
        """Receive a message."""
        pass

    def on_message(self, handler: Callable[[str], None]):
        """Set message handler."""
        self._message_handler = handler

    def on_error(self, handler: Callable[[Exception], None]):
        """Set error handler."""
        self._error_handler = handler

    def handle_message(self, message: str):
        """Handle incoming message."""
        if self._message_handler:
            self._message_handler(message)

    def handle_error(self, error: Exception):
        """Handle error."""
        if self._error_handler:
            self._error_handler(error)
```

- [ ] **Step 3: Create mcp/transport/stdio.py**

```python
"""Stdio transport for MCP."""
import asyncio
import json
from typing import Optional
from .base import Transport

class StdioTransport(Transport):
    """Stdio transport using stdin/stdout."""

    def __init__(self):
        super().__init__()
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None

    async def connect(self) -> None:
        """Start the subprocess."""
        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader = self._process.stdout

    async def disconnect(self) -> None:
        """Stop the subprocess."""
        if self._process:
            self._process.terminate()
            await self._process.wait()

    async def send(self, message: str) -> None:
        """Send message to stdin."""
        if self._process and self._process.stdin:
            self._process.stdin.write(message.encode() + b"\n")
            await self._process.stdin.drain()

    async def receive(self) -> str:
        """Receive message from stdout."""
        if self._reader:
            line = await self._reader.readline()
            return line.decode().strip()
        return ""

    async def start_server(self, command: list, cwd: Optional[str] = None):
        """Start a server process with stdio transport."""
        self.command = command
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        self._reader = self._process.stdout

        # Start reading in background
        asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Background read loop."""
        while self._process and self._process.returncode is None:
            try:
                line = await asyncio.wait_for(self._reader.readline(), timeout=1.0)
                if line:
                    self.handle_message(line.decode().strip())
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.handle_error(e)
                break
```

- [ ] **Step 4: Create mcp/transport/websocket.py**

```python
"""WebSocket transport for MCP."""
import asyncio
import json
from typing import Optional
from websockets.client import connect, WebSocketClientProtocol
from .base import Transport

class WebSocketTransport(Transport):
    """WebSocket transport."""

    def __init__(self, url: str, headers: dict = None):
        super().__init__()
        self.url = url
        self.headers = headers or {}
        self._ws: Optional[WebSocketClientProtocol] = None

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        self._ws = await connect(self.url, extra_headers=self.headers)

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._ws:
            await self._ws.close()

    async def send(self, message: str) -> None:
        """Send message."""
        if self._ws:
            await self._ws.send(message)

    async def receive(self) -> str:
        """Receive message."""
        if self._ws:
            return await self._ws.recv()
        return ""

    async def start_client(self):
        """Start WebSocket client."""
        await self.connect()
        asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Background read loop."""
        try:
            async for message in self._ws:
                if isinstance(message, str):
                    self.handle_message(message)
                elif isinstance(message, bytes):
                    self.handle_message(message.decode())
        except Exception as e:
            self.handle_error(e)
```

- [ ] **Step 5: Create mcp/client.py**

```python
"""MCP client implementation."""
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from .protocol import MCPRequest, MCPResponse, MCPMethod
from .transport.base import Transport
from .transport.stdio import StdioTransport
from .transport.websocket import WebSocketTransport
from ..core.exceptions import MCPError

class MCPClient:
    """MCP client for connecting to MCP servers."""

    def __init__(self):
        self._transport: Optional[Transport] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._server_info: Optional[Dict] = None
        self._tools: List[Dict] = []
        self._resources: List[Dict] = []

    async def connect_stdio(self, command: List[str], cwd: Optional[str] = None):
        """Connect using stdio transport."""
        self._transport = StdioTransport()
        await self._transport.start_server(command, cwd)
        self._transport.on_message(self._handle_message)
        self._transport.on_error(self._handle_error)

        # Initialize
        await self.initialize()

    async def connect_websocket(self, url: str, headers: Dict = None):
        """Connect using WebSocket transport."""
        self._transport = WebSocketTransport(url, headers)
        await self._transport.start_client()
        self._transport.on_message(self._handle_message)
        self._transport.on_error(self._handle_error)

        # Initialize
        await self.initialize()

    async def initialize(self) -> Dict:
        """Send initialize request."""
        result = await self._send_request(
            MCPMethod.INITIALIZE,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                },
                "clientInfo": {
                    "name": "super-agent-party",
                    "version": "0.1.0",
                },
            }
        )
        self._server_info = result.get("serverInfo", {})
        return result

    async def list_tools(self) -> List[Dict]:
        """List available tools."""
        result = await self._send_request(MCPMethod.TOOLS_LIST)
        self._tools = result.get("tools", [])
        return self._tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool."""
        result = await self._send_request(
            MCPMethod.TOOLS_CALL,
            {
                "name": tool_name,
                "arguments": arguments,
            }
        )
        return result

    async def list_resources(self) -> List[Dict]:
        """List available resources."""
        result = await self._send_request(MCPMethod.RESOURCES_LIST)
        self._resources = result.get("resources", [])
        return self._resources

    async def read_resource(self, uri: str) -> Dict:
        """Read a resource."""
        return await self._send_request(
            MCPMethod.RESOURCES_READ,
            {"uri": uri}
        )

    async def _send_request(
        self,
        method: str,
        params: Dict = None
    ) -> Dict:
        """Send a request and wait for response."""
        req_id = str(uuid.uuid4())
        request = MCPRequest(
            jsonrpc="2.0",
            id=req_id,
            method=method,
            params=params or {}
        )

        future = asyncio.get_event_loop().create_future()
        self._pending_requests[req_id] = future

        # Send request
        import json
        self._transport.send(json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }))

        # Wait for response
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise MCPError(f"Request {method} timed out")

    def _handle_message(self, data: str):
        """Handle incoming message."""
        import json
        try:
            obj = json.loads(data)
            if "id" in obj and obj["id"] in self._pending_requests:
                future = self._pending_requests.pop(obj["id"])
                if "error" in obj:
                    future.set_exception(MCPError(obj["error"].get("message", "Unknown error")))
                else:
                    future.set_result(obj.get("result", {}))
        except Exception as e:
            print(f"Failed to handle message: {e}")

    def _handle_error(self, error: Exception):
        """Handle transport error."""
        print(f"MCP transport error: {error}")
        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(error)

    @property
    def tools(self) -> List[Dict]:
        """Get cached tools list."""
        return self._tools

    @property
    def resources(self) -> List[Dict]:
        """Get cached resources list."""
        return self._resources

    @property
    def server_info(self) -> Optional[Dict]:
        """Get server info."""
        return self._server_info
```

- [ ] **Step 6: Commit**

```bash
git add py/mcp/__init__.py py/mcp/protocol.py py/mcp/transport/__init__.py py/mcp/transport/base.py py/mcp/transport/stdio.py py/mcp/transport/websocket.py py/mcp/client.py
git commit -m "feat(backend): add MCP client with transport abstraction - CoPaw style"
```

---

### Task B4: Create Model Configuration System (参考 CoPaw)

**Files:**
- Create: `py/models/__init__.py`
- Create: `py/models/config.py`
- Create: `py/models/capabilities.py`
- Create: `py/models/provider.py`
- Create: `py/models/registry.py`
- Create: `py/models/openai.py`
- Create: `py/models/anthropic.py`
- Create: `py/models/ollama.py`

- [ ] **Step 1: Create models/capabilities.py**

```python
"""Model capability definitions."""
from dataclasses import dataclass
from typing import List
from enum import Flag, auto

class ModelCapability(Flag):
    """Model capabilities."""
    CHAT = auto()
    COMPLETION = auto()
    STREAMING = auto()
    VISION = auto()
    FUNCTION_CALLING = auto()
    JSON_MODE = auto()
    SYSTEM_PROMPT = auto()
    MULTI_MODAL = auto()
    TTS = auto()
    ASR = auto()
    EMBEDDING = auto()

@dataclass
class ModelInfo:
    """Model information."""
    id: str
    name: str
    provider: str
    capabilities: List[str]
    context_window: int
    max_output_tokens: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    pricing: dict = None  # {"input": 0.001, "output": 0.002}

# Predefined model info
MODELS = {
    "gpt-4": ModelInfo(
        id="gpt-4",
        name="GPT-4",
        provider="openai",
        capabilities=["chat", "streaming", "function_calling", "json_mode", "vision"],
        context_window=128000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_vision=True,
    ),
    "gpt-3.5-turbo": ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        capabilities=["chat", "streaming", "function_calling", "json_mode"],
        context_window=16385,
        max_output_tokens=4096,
        supports_streaming=True,
    ),
    "claude-3-opus": ModelInfo(
        id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        capabilities=["chat", "streaming", "vision", "multi_modal"],
        context_window=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_vision=True,
    ),
    "claude-3-sonnet": ModelInfo(
        id="claude-3-sonnet",
        name="Claude 3 Sonnet",
        provider="anthropic",
        capabilities=["chat", "streaming", "vision", "multi_modal"],
        context_window=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_vision=True,
    ),
}
```

- [ ] **Step 2: Create models/config.py**

```python
"""Model configuration."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ProviderConfig(BaseModel):
    """Provider configuration."""
    id: str
    name: str
    provider_type: str  # "openai", "anthropic", "ollama", "minimax"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = ""
    timeout: int = 60
    max_retries: int = 3

class ModelConfig(BaseModel):
    """Model configuration."""
    id: str
    provider_id: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChatMessage:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None

@dataclass
class ChatCompletionRequest:
    """Chat completion request."""
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    stop: list = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChatCompletionResponse:
    """Chat completion response."""
    id: str
    model: str
    choices: list
    usage: dict
    created: int
```

- [ ] **Step 3: Create models/provider.py**

```python
"""Base provider class."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional
from .config import ChatCompletionRequest, ChatCompletionResponse

class Provider(ABC):
    """Base class for model providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return provider type."""
        pass

    @abstractmethod
    async def chat_complete(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send chat completion request with streaming."""
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass
```

- [ ] **Step 4: Create models/registry.py**

```python
"""Provider registry."""
from typing import Dict, Type, Optional, List
from .provider import Provider
from ..core.exceptions import ModelError

class ProviderRegistry:
    """Registry for model providers."""

    def __init__(self):
        self._providers: Dict[str, Type[Provider]] = {}
        self._instances: Dict[str, Provider] = {}

    def register(self, provider_type: str, provider_class: Type[Provider]):
        """Register a provider class."""
        self._providers[provider_type] = provider_class

    def get(self, provider_type: str) -> Type[Provider]:
        """Get a provider class."""
        return self._providers.get(provider_type)

    def create(self, provider_type: str, config: Dict) -> Provider:
        """Create a provider instance."""
        provider_class = self.get(provider_type)
        if not provider_class:
            raise ModelError(f"Unknown provider type: {provider_type}")

        instance = provider_class(config)
        self._instances[provider_type] = instance
        return instance

    def get_instance(self, provider_type: str) -> Optional[Provider]:
        """Get existing provider instance."""
        return self._instances.get(provider_type)

    def list_providers(self) -> List[str]:
        """List registered provider types."""
        return list(self._providers.keys())


# Global registry
registry = ProviderRegistry()
```

- [ ] **Step 5: Create models/openai.py**

```python
"""OpenAI provider implementation."""
import os
import json
from typing import List, Dict, Any, AsyncIterator
import httpx
from .provider import Provider
from .config import ChatCompletionRequest, ChatCompletionResponse
from .capabilities import MODELS

class OpenAIProvider(Provider):
    """OpenAI provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.get("timeout", 60),
        )

    @property
    def provider_type(self) -> str:
        return "openai"

    async def chat_complete(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request."""
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        if request.stop:
            payload["stop"] = request.stop

        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatCompletionResponse(
            id=data["id"],
            model=data["model"],
            choices=data["choices"],
            usage=data.get("usage", {}),
            created=data.get("created", 0),
        )

    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send chat completion request with streaming."""
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        if request.stop:
            payload["stop"] = request.stop

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield json.loads(data)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        response = await self.client.get("/models")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 6: Create models/anthropic.py**

```python
"""Anthropic provider implementation."""
import os
import json
from typing import List, Dict, Any, AsyncIterator
import httpx
from .provider import Provider
from .config import ChatCompletionRequest, ChatCompletionResponse

class AnthropicProvider(Provider):
    """Anthropic provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=config.get("timeout", 60),
        )

    @property
    def provider_type(self) -> str:
        return "anthropic"

    async def chat_complete(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request."""
        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        for m in request.messages:
            if m.role == "system":
                system_message = m.content
            else:
                anthropic_messages.append({
                    "role": m.role,
                    "content": m.content,
                })

        payload = {
            "model": request.model,
            "messages": anthropic_messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if system_message:
            payload["system"] = system_message
        if request.stop:
            payload["stop_sequences"] = request.stop

        response = await self.client.post("/messages", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatCompletionResponse(
            id=f"anthropic-{data.get('id', '')}",
            model=data["model"],
            choices=[{
                "message": {"role": "assistant", "content": data["content"][0]["text"]},
                "finish_reason": data.get("stop_reason"),
            }],
            usage={
                "prompt_tokens": data["usage"]["input_tokens"],
                "completion_tokens": data["usage"]["output_tokens"],
            },
            created=0,
        )

    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send chat completion request with streaming."""
        system_message = ""
        anthropic_messages = []
        for m in request.messages:
            if m.role == "system":
                system_message = m.content
            else:
                anthropic_messages.append({
                    "role": m.role,
                    "content": m.content,
                })

        payload = {
            "model": request.model,
            "messages": anthropic_messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        if system_message:
            payload["system"] = system_message
        if request.stop:
            payload["stop_sequences"] = request.stop

        async with self.client.stream("POST", "/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield json.loads(data)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models (placeholder)."""
        # Anthropic doesn't have a list models endpoint
        return [
            {"id": "claude-3-opus", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku"},
        ]

    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        try:
            # Send a minimal request to check health
            response = await self.client.post(
                "/messages",
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                }
            )
            return response.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 7: Create models/ollama.py**

```python
"""Ollama provider implementation."""
from typing import List, Dict, Any, AsyncIterator
import httpx
from .provider import Provider
from .config import ChatCompletionRequest, ChatCompletionResponse

class OllamaProvider(Provider):
    """Ollama provider for local models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=config.get("timeout", 120),
        )

    @property
    def provider_type(self) -> str:
        return "ollama"

    async def chat_complete(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request."""
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "stream": False,
        }
        if request.temperature:
            payload["options"] = {"temperature": request.temperature}
        if request.stop:
            payload["options"] = payload.get("options", {})
            payload["options"]["stop"] = request.stop

        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatCompletionResponse(
            id=f"ollama-{data.get('model', request.model)}",
            model=data.get("model", request.model),
            choices=[{
                "message": {"role": "assistant", "content": data["message"]["content"]},
                "finish_reason": data.get("done_reason"),
            }],
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            created=0,
        )

    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send chat completion request with streaming."""
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "stream": True,
        }
        if request.temperature:
            payload["options"] = {"temperature": request.temperature}

        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    yield json.loads(line)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])

    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 8: Register providers in models/__init__.py**

```python
"""Models package."""
from .registry import registry
from .provider import Provider
from .config import ModelConfig, ProviderConfig, ChatMessage, ChatCompletionRequest
from .capabilities import ModelCapability, ModelInfo, MODELS

# Import providers to register them
from . import openai
from . import anthropic
from . import ollama

def setup_providers():
    """Setup default providers."""
    registry.register("openai", openai.OpenAIProvider)
    registry.register("anthropic", anthropic.AnthropicProvider)
    registry.register("ollama", ollama.OllamaProvider)

__all__ = [
    "registry",
    "Provider",
    "ModelConfig",
    "ProviderConfig",
    "ChatMessage",
    "ChatCompletionRequest",
    "ModelCapability",
    "ModelInfo",
    "MODELS",
    "setup_providers",
]
```

- [ ] **Step 9: Commit**

```bash
git add py/models/__init__.py py/models/config.py py/models/capabilities.py py/models/provider.py py/models/registry.py py/models/openai.py py/models/anthropic.py py/models/ollama.py
git commit -m "feat(backend): add model configuration system with provider abstraction - CoPaw style"
```

---

### Task B5: Refactor server.py with Plugin Architecture

**Files:**
- Modify: `py/server.py`

- [ ] **Step 1: Create new server.py structure**

```python
"""Main FastAPI server with plugin architecture."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware

from py.core.config import config
from py.core.events import events
from py.plugins.registry import registry
from py.plugins.loader import PluginLoader
from py.plugins.hooks import hooks, Hook
from py.skills import SkillManager
from py.mcp.client import MCPClient
from py.models import setup_providers, registry as model_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
skill_manager: SkillManager = None
mcp_clients: dict[str, MCPClient] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global skill_manager

    # Startup
    logger.info("Starting Super Agent Party server...")

    # Setup model providers
    setup_providers()

    # Load plugins
    plugin_loader = PluginLoader([config.extensions_dir])
    await plugin_loader.load_builtin_plugins()

    # Load skills
    skill_manager = SkillManager(config.skills_dir)
    await skill_manager.load_all()

    # Emit startup hook
    await hooks.emit(Hook.AFTER_STARTUP)

    logger.info("Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down server...")
    await hooks.emit(Hook.BEFORE_SHUTDOWN)

    # Stop plugins
    for plugin in registry.plugins.values():
        if plugin.enabled:
            await plugin.stop()
            await plugin.cleanup()

    logger.info("Server shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Super Agent Party",
    description="Multi-platform AI Agent Desktop Application",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Super Agent Party API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_ws_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_ws_message(websocket: WebSocket, data: dict):
    """Handle incoming WebSocket message."""
    msg_type = data.get("type")
    method = data.get("method")
    params = data.get("params", {})

    try:
        if method == "chat.complete":
            result = await handle_chat_complete(params)
        elif method == "chat.complete_stream":
            result = await handle_chat_complete_stream(websocket, params)
        elif method == "skills.list":
            result = await handle_skills_list()
        elif method == "skills.execute":
            result = await handle_skills_execute(params)
        elif method == "mcp.connect":
            result = await handle_mcp_connect(params)
        elif method == "mcp.tools":
            result = await handle_mcp_tools(params)
        elif method == "settings.get":
            result = await handle_settings_get()
        elif method == "settings.update":
            result = await handle_settings_update(params)
        else:
            result = {"error": f"Unknown method: {method}"}

        await manager.send_message({
            "type": "jsonrpc",
            "id": data.get("id"),
            "result": result,
        }, websocket)

    except Exception as e:
        await manager.send_message({
            "type": "jsonrpc",
            "id": data.get("id"),
            "error": {"message": str(e)},
        }, websocket)

# Chat handlers
async def handle_chat_complete(params: dict) -> dict:
    """Handle chat completion request."""
    model = params.get("model", "gpt-3.5-turbo")
    messages = params.get("messages", [])

    # Get provider from model name
    provider_type = "openai"  # Default
    if model.startswith("claude"):
        provider_type = "anthropic"
    elif model.startswith("ollama"):
        provider_type = "ollama"

    provider = model_registry.get_instance(provider_type)
    if not provider:
        provider = model_registry.create(provider_type, {})

    from py.models.config import ChatCompletionRequest, ChatMessage
    chat_messages = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]

    request = ChatCompletionRequest(
        model=model,
        messages=chat_messages,
        temperature=params.get("temperature", 0.7),
        max_tokens=params.get("max_tokens", 4096),
    )

    response = await provider.chat_complete(request)

    return {
        "id": response.id,
        "model": response.model,
        "choices": response.choices,
        "usage": response.usage,
    }

async def handle_chat_complete_stream(websocket: WebSocket, params: dict):
    """Handle streaming chat completion."""
    model = params.get("model", "gpt-3.5-turbo")
    messages = params.get("messages", [])

    provider_type = "openai"
    if model.startswith("claude"):
        provider_type = "anthropic"
    elif model.startswith("ollama"):
        provider_type = "ollama"

    provider = model_registry.get_instance(provider_type)
    if not provider:
        provider = model_registry.create(provider_type, {})

    from py.models.config import ChatCompletionRequest, ChatMessage
    chat_messages = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]

    request = ChatCompletionRequest(
        model=model,
        messages=chat_messages,
        temperature=params.get("temperature", 0.7),
        max_tokens=params.get("max_tokens", 4096),
    )

    async for chunk in provider.chat_complete_stream(request):
        await manager.send_message({
            "type": "stream",
            "data": chunk,
        }, websocket)

# Skills handlers
async def handle_skills_list() -> dict:
    """List all skills."""
    skills = skill_manager.list_all()
    return {
        "skills": [
            {
                "id": s.metadata.id,
                "name": s.metadata.name,
                "description": s.metadata.description,
                "category": s.metadata.category,
            }
            for s in skills
        ]
    }

async def handle_skills_execute(params: dict) -> dict:
    """Execute a skill."""
    skill_id = params.get("skill_id")
    parameters = params.get("parameters", {})

    execution = await skill_manager.execute(skill_id, parameters)
    return {
        "skill_id": execution.skill_id,
        "result": execution.result,
        "error": execution.error,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }

# MCP handlers
async def handle_mcp_connect(params: dict) -> dict:
    """Connect to an MCP server."""
    mcp_id = params.get("mcp_id")
    transport = params.get("transport", "stdio")
    config_ = params.get("config", {})

    client = MCPClient()
    if transport == "stdio":
        command = config_.get("command", [])
        cwd = config_.get("cwd")
        await client.connect_stdio(command, cwd)
    elif transport == "websocket":
        url = config_.get("url")
        headers = config_.get("headers", {})
        await client.connect_websocket(url, headers)

    mcp_clients[mcp_id] = client
    return {"status": "connected", "mcp_id": mcp_id}

async def handle_mcp_tools(params: dict) -> dict:
    """Get MCP tools."""
    mcp_id = params.get("mcp_id")
    client = mcp_clients.get(mcp_id)
    if not client:
        return {"error": f"MCP client {mcp_id} not found"}

    tools = await client.list_tools()
    return {"tools": tools}

# Settings handlers
async def handle_settings_get() -> dict:
    """Get current settings."""
    return {
        "host": config.host,
        "port": config.port,
    }

async def handle_settings_update(params: dict) -> dict:
    """Update settings."""
    for key, value in params.items():
        if hasattr(config, key):
            config.set(key, value)
    return {"status": "updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
```

- [ ] **Step 2: Commit**

```bash
git add py/server.py
git commit -m "feat(backend): refactor server.py with plugin architecture and lifespan management"
```

---

### PART C: Frontend Chat Feature

---

### Task C1: Create Chat Components

**Files:**
- Create: `frontend/src/components/chat/chat-container.tsx`
- Create: `frontend/src/components/chat/message-list.tsx`
- Create: `frontend/src/components/chat/message-item.tsx`
- Create: `frontend/src/components/chat/chat-input.tsx`
- Create: `frontend/src/components/chat/chat-header.tsx`

- [ ] **Step 1: Create message item component**

```typescript
import { Message } from '@/lib/stores/chat-store'
import { cn } from '@/lib/utils'
import { User, Bot } from 'lucide-react'

interface MessageItemProps {
  message: Message
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 p-4',
        isUser ? 'bg-muted/50' : 'bg-background'
      )}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="font-semibold">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-muted-foreground">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>

        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create message list component**

```typescript
'use client'

import { useRef, useEffect } from 'react'
import { useChatStore } from '@/lib/stores/chat-store'
import { MessageItem } from './message-item'

export function MessageList() {
  const { messages } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="text-lg">No messages yet</p>
          <p className="text-sm">Start a conversation by typing below</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 3: Create chat input component**

```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t">
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || !input.trim()} size="icon">
        <Send className="h-4 w-4" />
      </Button>
    </form>
  )
}
```

- [ ] **Step 4: Create chat header component**

```typescript
'use client'

import { useChatStore } from '@/lib/stores/chat-store'
import { useWebSocket } from '@/hooks/use-websocket'
import { Button } from '@/components/ui/button'
import { Trash2 } from 'lucide-react'

export function ChatHeader() {
  const { clearMessages } = useChatStore()
  const { isConnected } = useWebSocket()

  return (
    <div className="flex items-center justify-between border-b px-4 py-3">
      <div>
        <h2 className="font-semibold">Chat</h2>
        <p className="text-xs text-muted-foreground">
          {isConnected ? 'Connected' : 'Disconnected'}
        </p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        onClick={clearMessages}
        title="Clear chat"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}
```

- [ ] **Step 5: Create chat container component**

```typescript
'use client'

import { useChatStore } from '@/lib/stores/chat-store'
import { useWebSocket } from '@/hooks/use-websocket'
import { MessageList } from './message-list'
import { ChatInput } from './chat-input'
import { ChatHeader } from './chat-header'

export function ChatContainer() {
  const { addMessage, isLoading, setLoading } = useChatStore()
  const { sendMessage, isConnected } = useWebSocket()

  const handleSend = async (content: string) => {
    // Add user message
    addMessage({ role: 'user', content })

    if (!isConnected) {
      addMessage({
        role: 'assistant',
        content: 'Error: Not connected to server. Please refresh the page.',
      })
      return
    }

    setLoading(true)

    try {
      const messages = useChatStore.getState().messages
      const response = await sendMessage('chat.complete', {
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      })

      addMessage({
        role: 'assistant',
        content: response.choices?.[0]?.message?.content || 'No response',
      })
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-1 flex-col">
      <ChatHeader />
      <MessageList />
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}
```

- [ ] **Step 6: Create chat page**

```typescript
'use client'

import { ChatContainer } from '@/components/chat/chat-container'
import { Card } from '@/components/ui/card'

export default function ChatPage() {
  return (
    <div className="container mx-auto h-full py-4">
      <Card className="flex h-full flex-col overflow-hidden">
        <ChatContainer />
      </Card>
    </div>
  )
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/chat/chat-container.tsx frontend/src/components/chat/message-list.tsx frontend/src/components/chat/message-item.tsx frontend/src/components/chat/chat-input.tsx frontend/src/components/chat/chat-header.tsx frontend/src/app/chat/page.tsx
git commit -m "feat(frontend): add chat feature components (container, messages, input)"
```

---

### PART D: Verification & Integration

---

### Task D1: Verify End-to-End Communication

- [ ] **Step 1: Test backend starts correctly**

Run: `cd py && python server.py`
Expected: Server starts on port 3456, logs show plugin loading

- [ ] **Step 2: Test frontend builds**

Run: `cd frontend && npm run build`
Expected: Build completes without errors

- [ ] **Step 3: Test Tauri builds**

Run: `npm run tauri:build`
Expected: Tauri app builds successfully

- [ ] **Step 4: Test WebSocket connection**

Test manually: Open app, verify WebSocket connects to backend

- [ ] **Step 5: Commit**

```bash
git commit -m "test: verify end-to-end communication works"
```

---

## Summary

**Phase 1 creates:**

1. **Frontend scaffolding**: Next.js + TypeScript + Tailwind + shadcn/ui + Zustand
2. **Tauri 2.x integration**: Desktop wrapper for the web app
3. **Plugin system**: Base architecture for backend extensibility
4. **Skills system**: CoPaw-style skill management
5. **MCP integration**: CoPaw-style MCP client with transports
6. **Model configuration**: CoPaw-style provider abstraction
7. **Chat feature**: Basic chat UI communicating with backend

**After Phase 1:**
- Frontend can build and run in Tauri
- Backend can start and expose WebSocket API
- Chat messages flow from frontend to backend and back

**Next steps (Phase 2):**
- Complete migration of all features (VRM, Bots, Knowledge Base, etc.)
- Add remaining UI components
- Implement settings page
- Add TTS/ASR support

---

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
