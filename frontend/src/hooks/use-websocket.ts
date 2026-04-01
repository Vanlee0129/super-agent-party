/**
 * React hook for WebSocket connection with JSON-RPC support
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketClient } from '../lib/api/websocket';
import { JSONRPCResponse, WSMessage } from '../lib/api/json-rpc';
import { useUIStore } from '../lib/stores/ui-store';

interface UseWebSocketReturn {
  isConnected: boolean;
  error: Event | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (data: string | ArrayBuffer) => void;
  request: (method: string, params?: Record<string, unknown> | unknown[]) => Promise<JSONRPCResponse>;
  client: WebSocketClient | null;
  onMessage: (handler: (data: WSMessage) => void) => () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const clientRef = useRef<WebSocketClient | null>(null);
  const messageHandlersRef = useRef<Set<(data: WSMessage) => void>>(new Set());
  const setConnectionState = useUIStore((state) => state.setActiveMenu);

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
      setConnectionState('connected');
    });

    client.onDisconnect(() => {
      setIsConnected(false);
      setConnectionState('disconnected');
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
    };
  }, [setConnectionState]);

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
    error,
    connect,
    disconnect,
    sendMessage,
    request,
    client: clientRef.current,
    onMessage,
  };
}
