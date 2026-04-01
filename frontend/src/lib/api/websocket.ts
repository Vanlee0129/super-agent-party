/**
 * WebSocket client with JSON-RPC protocol support and auto-reconnection
 */

import {
  JSONRPCRequest,
  JSONRPCResponse,
  WSMessage,
  isJSONRPCResponse,
  createRequest,
} from './json-rpc';

export interface WebSocketClientConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
  exponentialBackoff?: boolean;
  maxReconnectDelay?: number;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

type ConnectionHandler = () => void;
type MessageHandler = (data: WSMessage) => void;
type ErrorHandler = (error: Event) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketClientConfig>;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pendingRequests: Map<string | number, {
    resolve: (value: JSONRPCResponse) => void;
    reject: (reason: Error) => void;
  }> = new Map();
  private isIntentionallyClosed = false;
  private connectionStatus: ConnectionStatus = 'disconnected';
  private statusChangeHandlers: Array<(status: ConnectionStatus) => void> = [];

  private onConnectHandlers: ConnectionHandler[] = [];
  private onDisconnectHandlers: ConnectionHandler[] = [];
  private onMessageHandlers: MessageHandler[] = [];
  private onErrorHandlers: ErrorHandler[] = [];

  constructor(config: WebSocketClientConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      pingInterval: config.pingInterval ?? 30000,
      exponentialBackoff: config.exponentialBackoff ?? true,
      maxReconnectDelay: config.maxReconnectDelay ?? 30000,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isIntentionallyClosed = false;
      this.setConnectionStatus('connecting');

      try {
        this.ws = new WebSocket(this.config.url);
        this.ws.binaryType = 'arraybuffer';

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this.startPing();
          this.setConnectionStatus('connected');
          this.onConnectHandlers.forEach((handler) => handler());
          resolve();
        };

        this.ws.onclose = () => {
          this.stopPing();
          this.onDisconnectHandlers.forEach((handler) => handler());

          if (!this.isIntentionallyClosed) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          this.onErrorHandlers.forEach((handler) => handler(error));
          reject(error);
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.stopPing();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    // Reject all pending requests
    this.pendingRequests.forEach(({ reject }) => {
      reject(new Error('WebSocket disconnected'));
    });
    this.pendingRequests.clear();
  }

  /**
   * Send a raw message
   */
  send(data: string | ArrayBuffer): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  /**
   * Send a JSON-RPC request and wait for response
   */
  request(
    method: string,
    params?: Record<string, unknown> | unknown[]
  ): Promise<JSONRPCResponse> {
    const request = createRequest(method, params);

    return new Promise((resolve, reject) => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket is not connected'));
        return;
      }

      // Store the pending request
      this.pendingRequests.set(request.id, { resolve, reject });

      // Send the request
      try {
        this.ws.send(JSON.stringify(request));
      } catch (error) {
        this.pendingRequests.delete(request.id);
        reject(error);
      }

      // Set timeout for request (30 seconds)
      setTimeout(() => {
        if (this.pendingRequests.has(request.id)) {
          this.pendingRequests.delete(request.id);
          reject(new Error(`Request ${method} timed out`));
        }
      }, 30000);
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string | ArrayBuffer): void {
    // Handle binary data (ping/pong or other binary messages)
    if (data instanceof ArrayBuffer) {
      const text = new TextDecoder().decode(data);
      try {
        const parsed = JSON.parse(text);
        if (parsed.type === 'pong') {
          return; // Ignore pong messages
        }
        this.onMessageHandlers.forEach((handler) => handler(parsed));
      } catch {
        // Treat as raw binary data
        this.onMessageHandlers.forEach((handler) => handler(data));
      }
      return;
    }

    try {
      const parsed = JSON.parse(data);

      // Check if it's a JSON-RPC response to a pending request
      if (isJSONRPCResponse(parsed)) {
        const pending = this.pendingRequests.get(parsed.id);
        if (pending) {
          this.pendingRequests.delete(parsed.id);
          pending.resolve(parsed);
          return;
        }
      }

      // Broadcast to message handlers
      this.onMessageHandlers.forEach((handler) => handler(parsed));
    } catch {
      // Not JSON, broadcast as raw string
      this.onMessageHandlers.forEach((handler) => handler(data));
    }
  }

  /**
   * Schedule reconnection attempt with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.setConnectionStatus('disconnected');
      return;
    }

    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    this.setConnectionStatus('reconnecting');

    // Calculate delay with exponential backoff
    let delay = this.config.reconnectInterval;
    if (this.config.exponentialBackoff) {
      delay = Math.min(
        delay * Math.pow(2, this.reconnectAttempts - 1),
        this.config.maxReconnectDelay
      );
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(() => {
        // Connection failed, scheduleReconnect will be called again from onclose
      });
    }, delay);
  }

  /**
   * Start ping interval
   */
  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        try {
          // Send ping as JSON message
          this.ws.send(JSON.stringify({ type: 'ping' }));
        } catch {
          // Ignore ping errors
        }
      }
    }, this.config.pingInterval);
  }

  /**
   * Stop ping interval
   */
  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  /**
   * Register connect event handler
   */
  onConnect(handler: ConnectionHandler): void {
    this.onConnectHandlers.push(handler);
  }

  /**
   * Register disconnect event handler
   */
  onDisconnect(handler: ConnectionHandler): void {
    this.onDisconnectHandlers.push(handler);
  }

  /**
   * Register message event handler
   */
  onMessage(handler: MessageHandler): void {
    this.onMessageHandlers.push(handler);
  }

  /**
   * Register error event handler
   */
  onError(handler: ErrorHandler): void {
    this.onErrorHandlers.push(handler);
  }

  /**
   * Get current connection state
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection status
   */
  get status(): ConnectionStatus {
    return this.connectionStatus;
  }

  /**
   * Set connection status and notify listeners
   */
  private setConnectionStatus(status: ConnectionStatus): void {
    this.connectionStatus = status;
    this.statusChangeHandlers.forEach((handler) => handler(status));
  }

  /**
   * Register status change event handler
   */
  onStatusChange(handler: (status: ConnectionStatus) => void): void {
    this.statusChangeHandlers.push(handler);
  }

  /**
   * Get reconnection info
   */
  getReconnectInfo(): { attempts: number; nextDelay: number | null; maxAttempts: number } {
    let nextDelay: number | null = null;
    if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
      nextDelay = this.config.exponentialBackoff
        ? Math.min(
            this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts),
            this.config.maxReconnectDelay
          )
        : this.config.reconnectInterval;
    }
    return {
      attempts: this.reconnectAttempts,
      nextDelay,
      maxAttempts: this.config.maxReconnectAttempts,
    };
  }
}
