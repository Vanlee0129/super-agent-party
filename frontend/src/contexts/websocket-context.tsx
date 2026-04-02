'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { ConnectionStatus } from '@/lib/api/websocket';

interface WebSocketContextValue {
  status: ConnectionStatus;
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextValue>({
  status: 'disconnected',
  isConnected: false,
});

interface WebSocketProviderProps {
  children: ReactNode;
  status: ConnectionStatus;
}

export function WebSocketProvider({ children, status }: WebSocketProviderProps) {
  const value: WebSocketContextValue = {
    status,
    isConnected: status === 'connected',
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketStatus() {
  return useContext(WebSocketContext);
}
