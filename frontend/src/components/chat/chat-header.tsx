'use client';

import React from 'react';
import { Trash2, Wifi, WifiOff } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chat-store';
import { useWebSocket } from '@/hooks/use-websocket';
import { Button } from '@/components/ui/button';

export function ChatHeader() {
  const clearMessages = useChatStore((state) => state.clearMessages);
  const { isConnected } = useWebSocket();

  return (
    <div className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold">Chat</h2>
        <div className="flex items-center gap-1.5">
          {isConnected ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-xs text-green-500">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-destructive" />
              <span className="text-xs text-destructive">Disconnected</span>
            </>
          )}
        </div>
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
  );
}
