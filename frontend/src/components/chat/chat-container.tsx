'use client';

import React from 'react';
import { useChatStore } from '@/lib/stores/chat-store';
import { useWebSocket } from '@/hooks/use-websocket';
import { ChatHeader } from './chat-header';
import { MessageList } from './message-list';
import { ChatInput } from './chat-input';
import { Loader2 } from 'lucide-react';

export function ChatContainer() {
  const { addMessage, setLoading, isLoading } = useChatStore();
  const { sendMessage, isConnected } = useWebSocket();

  const handleSend = (content: string) => {
    if (!isConnected) return;

    addMessage({ role: 'user', content });
    setLoading(true);

    // Send via WebSocket - the response will be handled by the WebSocket hook
    sendMessage(JSON.stringify({
      jsonrpc: '2.0',
      method: 'chat.message',
      params: { content },
    }));
  };

  return (
    <div className="flex flex-col h-full">
      <ChatHeader />
      <MessageList />
      {isLoading && (
        <div className="flex items-center justify-center p-4 gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Thinking...</span>
        </div>
      )}
      <ChatInput onSend={handleSend} disabled={!isConnected} />
    </div>
  );
}
