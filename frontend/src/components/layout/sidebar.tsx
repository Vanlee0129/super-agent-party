'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, MessageCircle, Bot, BookOpen, Puzzle, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const navItems = [
  { id: 'home', label: 'Home', icon: Home, href: '/' },
  { id: 'chat', label: 'Chat', icon: MessageCircle, href: '/chat' },
  { id: 'bots', label: 'Bots', icon: Bot, href: '/bots' },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen, href: '/knowledge' },
  { id: 'extensions', label: 'Extensions', icon: Puzzle, href: '/extensions' },
  { id: 'settings', label: 'Settings', icon: Settings, href: '/settings' },
];

export function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Desktop sidebar - hidden on mobile, flex on md and up */}
      <aside
        className={cn(
          'hidden md:flex flex-col w-64 h-screen border-r bg-card transition-all duration-300 ease-in-out'
        )}
      >
        <div className="p-6">
          <h1 className="text-xl font-bold">Super Agent</h1>
        </div>
        <nav className="flex-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link key={item.id} href={item.href}>
                <Button
                  variant={active ? 'secondary' : 'ghost'}
                  className={cn(
                    'w-full justify-start gap-3 mb-1 transition-all duration-200',
                    active && 'bg-secondary shadow-sm'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Button>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Mobile bottom navigation - visible on mobile, hidden on md and up */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t z-50 safe-area-pb">
        <div className="flex justify-around p-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link key={item.id} href={item.href}>
                <button
                  className={cn(
                    'flex flex-col items-center justify-center min-h-[44px] min-w-[44px] p-2 rounded-lg transition-colors',
                    active ? 'text-primary' : 'text-muted-foreground'
                  )}
                  aria-label={item.label}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs mt-1">{item.label}</span>
                </button>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
