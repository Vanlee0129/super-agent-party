'use client';

import React from 'react';
import { Home, MessageCircle, Bot, BookOpen, Puzzle, Settings } from 'lucide-react';
import { useUIStore } from '@/lib/stores/ui-store';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const menuItems = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'chat', label: 'Chat', icon: MessageCircle },
  { id: 'bots', label: 'Bots', icon: Bot },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'extensions', label: 'Extensions', icon: Puzzle },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const { sidebarOpen, activeMenu, setActiveMenu } = useUIStore();

  if (!sidebarOpen) return null;

  return (
    <aside
      className={cn(
        'flex flex-col w-64 h-screen border-r bg-card transition-all duration-300 ease-in-out'
      )}
    >
      <div className="p-6">
        <h1 className="text-xl font-bold">Super Agent</h1>
      </div>
      <nav className="flex-1 px-3">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeMenu === item.id;
          return (
            <Button
              key={item.id}
              variant={isActive ? 'secondary' : 'ghost'}
              className={cn(
                'w-full justify-start gap-3 mb-1 transition-all duration-200',
                isActive && 'bg-secondary shadow-sm'
              )}
              onClick={() => setActiveMenu(item.id)}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Button>
          );
        })}
      </nav>
    </aside>
  );
}
