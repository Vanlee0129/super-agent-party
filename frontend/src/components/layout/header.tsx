'use client';

import React from 'react';
import { Menu, Sun, Moon, Monitor } from 'lucide-react';
import { useUIStore } from '@/lib/stores/ui-store';
import { useSettingsStore } from '@/lib/stores/settings-store';
import { Button } from '@/components/ui/button';

export function Header() {
  const { toggleSidebar } = useUIStore();
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
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        <Menu className="h-5 w-5" />
      </Button>
      <Button variant="ghost" size="icon" onClick={cycleTheme}>
        <ThemeIcon />
      </Button>
    </header>
  );
}
