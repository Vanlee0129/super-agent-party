'use client';

import React from 'react';
import Link from 'next/link';
import { Menu, Sun, Moon, Monitor, Home, MessageCircle, Bot, BookOpen, Puzzle, Settings, X } from 'lucide-react';
import { useUIStore } from '@/lib/stores/ui-store';
import { useSettingsStore } from '@/lib/stores/settings-store';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ConnectionStatusIndicator } from '@/components/ui/connection-status';
import { cn } from '@/lib/utils';

const menuItems = [
  { id: 'home', label: 'Home', icon: Home, href: '/' },
  { id: 'chat', label: 'Chat', icon: MessageCircle, href: '/chat' },
  { id: 'bots', label: 'Bots', icon: Bot, href: '/bots' },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen, href: '/knowledge' },
  { id: 'extensions', label: 'Extensions', icon: Puzzle, href: '/extensions' },
  { id: 'settings', label: 'Settings', icon: Settings, href: '/settings' },
];

export function Header() {
  const { toggleSidebar, connectionStatus } = useUIStore();
  const { settings, updateSettings } = useSettingsStore();

  const cycleTheme = () => {
    const themes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(settings.theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    updateSettings({ theme: themes[nextIndex] });
  };

  const ThemeIcon = () => {
    switch (settings.theme) {
      case 'light':
        return <Sun className="h-5 w-5" />;
      case 'dark':
        return <Moon className="h-5 w-5" />;
      case 'system':
        return <Monitor className="h-5 w-5" />;
      default:
        return <Sun className="h-5 w-5" />;
    }
  };

  return (
    <header className="flex items-center justify-between h-16 px-4 border-b bg-card">
      {/* Mobile menu - visible on mobile, hidden on md and up */}
      <div className="md:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="min-h-[44px] min-w-[44px]">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[280px]">
            <SheetHeader className="pb-4 border-b">
              <SheetTitle className="text-left">Super Agent Party</SheetTitle>
            </SheetHeader>
            <nav className="flex flex-col gap-1 mt-4">
              {menuItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.id} href={item.href}>
                    <Button variant="ghost" className="w-full justify-start gap-3 min-h-[44px]">
                      <Icon className="h-5 w-5" />
                      <span>{item.label}</span>
                    </Button>
                  </Link>
                );
              })}
            </nav>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop toggle - visible on md and up */}
      <div className="hidden md:block">
        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="min-h-[44px] min-w-[44px]">
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Center content - visible on mobile */}
      <div className="md:hidden flex-1 flex justify-center">
        <ConnectionStatusIndicator status={connectionStatus} />
      </div>

      {/* Desktop status - visible on md and up */}
      <div className="hidden md:flex items-center gap-4">
        <ConnectionStatusIndicator status={connectionStatus} />
      </div>

      <Button variant="ghost" size="icon" onClick={cycleTheme} className="min-h-[44px] min-w-[44px]">
        <ThemeIcon />
      </Button>
    </header>
  );
}
