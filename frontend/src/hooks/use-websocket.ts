/**
 * React hook for WebSocket connection with JSON-RPC support
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketClient, ConnectionStatus } from '../lib/api/websocket';
import { JSONRPCResponse, WSMessage } from '../lib/api/json-rpc';
import { useUIStore } from '../lib/stores/ui-store';

interface UseWebSocketReturn {
  isConnected: boolean;
  status: ConnectionStatus;
  error: Event | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (data: string | ArrayBuffer) => void;
  request: (method: string, params?: Record<string, unknown> | unknown[]) => Promise<JSONRPCResponse>;
  client: WebSocketClient | null;
  onMessage: (handler: (data: WSMessage) => void) => () => void;
  reconnectInfo: { attempts: number; nextDelay: number | null; maxAttempts: number };
}

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<Event | null>(null);
  const [reconnectInfo, setReconnectInfo] = useState({ attempts: 0, nextDelay: null as number | null, maxAttempts: 10 });
  const clientRef = useRef<WebSocketClient | null>(null);
  const messageHandlersRef = useRef<Set<(data: WSMessage) => void>>(new Set());
  const setConnectionStatus = useUIStore((state) => state.setConnectionStatus);

  // Initialize WebSocket client
  useEffect(() => {
    const hostname = window.location.hostname;
    const wsUrl = `ws://${hostname}:3456`;

    const client = new WebSocketClient({
      url: wsUrl,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      pingInterval: 30000,
    });

    clientRef.current = client;

    client.onConnect(() => {
      setIsConnected(true);
      setError(null);
      setConnectionStatus('connected');
    });

    client.onDisconnect(() => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
    });

    // Listen for status changes
    client.onStatusChange((newStatus) => {
      setStatus(newStatus);
      setReconnectInfo(client.getReconnectInfo());
    });

    client.onError((err) => {
      setError(err);
    });

    client.onMessage((data) => {
      messageHandlersRef.current.forEach((handler) => handler(data));
    });

    return () => {
      client.disconnect();
      clientRef.current = null;
      setConnectionStatus('disconnected');
    };
  }, [setConnectionStatus]);

  const connect = useCallback(async () => {
    if (clientRef.current) {
      try {
        await clientRef.current.connect();
      } catch (err) {
        setError(err as Event);
        throw err;
      }
    }
  }, []);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
    }
  }, []);

  const sendMessage = useCallback((data: string | ArrayBuffer) => {
    if (clientRef.current) {
      clientRef.current.send(data);
    }
  }, []);

  const request = useCallback(
    async (method: string, params?: Record<string, unknown> | unknown[]): Promise<JSONRPCResponse> => {
      if (!clientRef.current) {
        throw new Error('WebSocket client not initialized');
      }
      return clientRef.current.request(method, params);
    },
    []
  );

  const onMessage = useCallback((handler: (data: WSMessage) => void) => {
    messageHandlersRef.current.add(handler);
    return () => {
      messageHandlersRef.current.delete(handler);
    };
  }, []);

  return {
    isConnected,
    status,
    error,
    connect,
    disconnect,
    sendMessage,
    request,
    client: clientRef.current,
    onMessage,
    reconnectInfo,
  };
}
