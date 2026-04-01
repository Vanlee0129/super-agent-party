'use client';

import React from 'react';
import { Bot as BotIcon, Plus, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BotCard } from './bot-card';
import type { Bot, BotStatus, BotPlatform } from '@/lib/stores/bots-store';

interface BotListProps {
  bots: Bot[];
  platform: BotPlatform;
  filterStatus: BotStatus | 'all';
  onFilterChange: (status: BotStatus | 'all') => void;
  onStartBot: (bot: Bot) => void;
  onStopBot: (bot: Bot) => void;
  onConfigureBot: (bot: Bot) => void;
  onDeleteBot: (bot: Bot) => void;
  onAddBot: () => void;
}

export function BotList({
  bots,
  platform,
  filterStatus,
  onFilterChange,
  onStartBot,
  onStopBot,
  onConfigureBot,
  onDeleteBot,
  onAddBot,
}: BotListProps) {
  const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-semibold">{platformName} Bots</h2>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select
              value={filterStatus}
              onValueChange={(value) => onFilterChange(value as BotStatus | 'all')}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="stopped">Stopped</SelectItem>
                <SelectItem value="starting">Starting</SelectItem>
                <SelectItem value="stopping">Stopping</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button onClick={onAddBot}>
          <Plus className="h-4 w-4 mr-2" />
          Add {platformName} Bot
        </Button>
      </div>

      {bots.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center border rounded-lg bg-muted/50">
          <BotIcon className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No {platformName} bots</h3>
          <p className="text-muted-foreground mb-4 max-w-sm">
            You haven&apos;t configured any {platformName} bots yet. Add your first bot to get started.
          </p>
          <Button onClick={onAddBot}>
            <Plus className="h-4 w-4 mr-2" />
            Add {platformName} Bot
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {bots.map((bot) => (
            <BotCard
              key={bot.id}
              bot={bot}
              onStart={onStartBot}
              onStop={onStopBot}
              onConfigure={onConfigureBot}
              onDelete={onDeleteBot}
            />
          ))}
        </div>
      )}
    </div>
  );
}
