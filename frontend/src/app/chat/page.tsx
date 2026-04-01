'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ChatContainer } from '@/components/chat/chat-container';

export default function ChatPage() {
  return (
    <div className="container max-w-2xl mx-auto p-4">
      <Card className="h-[calc(100vh-8rem)]">
        <CardContent className="p-0 h-full">
          <ChatContainer />
        </CardContent>
      </Card>
    </div>
  );
}
