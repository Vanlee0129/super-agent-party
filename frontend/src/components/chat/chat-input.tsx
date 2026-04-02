'use client';

import React, { useState, useRef, FormEvent } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useKeyboardHeight } from '@/hooks/use-keyboard-height';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const keyboardHeight = useKeyboardHeight();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;

    onSend(trimmed);
    setValue('');
    inputRef.current?.focus();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 p-4 border-t safe-area-pb"
      style={{ paddingBottom: keyboardHeight > 0 ? `calc(1rem + ${keyboardHeight}px)` : '1rem' }}
    >
      <Input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
        className="flex-1 min-h-[44px]"
        autoComplete="off"
      />
      <Button
        type="submit"
        size="icon"
        disabled={disabled || !value.trim()}
        className="min-h-[44px] min-w-[44px]"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}
