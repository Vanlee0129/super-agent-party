'use client';

import React from 'react';
import {
  Play,
  Square,
  Settings,
  Trash2,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  MessageCircle,
  Users,
  Hash,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Bot, BotPlatform, BotStatus } from '@/lib/stores/bots-store';

// Platform icons as simple emoji representations (in production, use proper icons)
const PlatformIcon = ({ platform }: { platform: BotPlatform }) => {
  const icons: Record<BotPlatform, React.ReactNode> = {
    feishu: <MessageCircle className="h-5 w-5 text-blue-500" />,
    qq: <MessageCircle className="h-5 w-5 text-green-500" />,
    discord: <Users className="h-5 w-5 text-indigo-500" />,
    slack: <Hash className="h-5 w-5 text-pink-500" />,
    dingtalk: <MessageCircle className="h-5 w-5 text-orange-500" />,
    telegram: <MessageCircle className="h-5 w-5 text-blue-400" />,
  };
  return icons[platform] || <MessageCircle className="h-5 w-5" />;
};

const StatusIcon = ({ status }: { status: BotStatus }) => {
  const icons: Record<BotStatus, React.ReactNode> = {
    running: <CheckCircle className="h-4 w-4 text-green-500" />,
    stopped: <Square className="h-4 w-4 text-gray-400" />,
    starting: <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />,
    stopping: <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />,
    error: <XCircle className="h-4 w-4 text-red-500" />,
  };
  return icons[status] || null;
};

const StatusBadge = ({ status }: { status: BotStatus }) => {
  const variants: Record<BotStatus, string> = {
    running: 'bg-green-500/10 text-green-500 border-green-500/20',
    stopped: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    starting: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    stopping: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    error: 'bg-red-500/10 text-red-500 border-red-500/20',
  };

  return (
    <Badge variant="outline" className={variants[status]}>
      <StatusIcon status={status} />
      <span className="ml-1 capitalize">{status}</span>
    </Badge>
  );
};

interface BotCardProps {
  bot: Bot;
  onStart: (bot: Bot) => void;
  onStop: (bot: Bot) => void;
  onConfigure: (bot: Bot) => void;
  onDelete: (bot: Bot) => void;
}

export function BotCard({ bot, onStart, onStop, onConfigure, onDelete }: BotCardProps) {
  const isRunning = bot.status === 'running';
  const isTransitioning = bot.status === 'starting' || bot.status === 'stopping';

  return (
    <Card className="w-full transition-shadow hover:shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-muted">
              <PlatformIcon platform={bot.platform} />
            </div>
            <div>
              <CardTitle className="text-lg">{bot.name}</CardTitle>
              <CardDescription className="capitalize">{bot.platform}</CardDescription>
            </div>
          </div>
          <StatusBadge status={bot.status} />
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        {bot.error && (
          <div className="flex items-start gap-2 p-2 rounded-md bg-destructive/10 text-destructive text-sm mb-3">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span className="line-clamp-2">{bot.error}</span>
          </div>
        )}

        <div className="text-sm text-muted-foreground">
          <p>ID: {bot.id.slice(0, 8)}...</p>
          <p>Created: {new Date(bot.createdAt).toLocaleDateString()}</p>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2 pt-0">
        {isRunning ? (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onStop(bot)}
            disabled={isTransitioning}
          >
            <Square className="h-4 w-4 mr-1" />
            Stop
          </Button>
        ) : (
          <Button
            variant="default"
            size="sm"
            onClick={() => onStart(bot)}
            disabled={isTransitioning}
          >
            <Play className="h-4 w-4 mr-1" />
            Start
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => onConfigure(bot)}
          disabled={isRunning}
        >
          <Settings className="h-4 w-4 mr-1" />
          Configure
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(bot)}
          disabled={isRunning || isTransitioning}
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="h-4 w-4 mr-1" />
          Delete
        </Button>
      </CardFooter>
    </Card>
  );
}

export { PlatformIcon, StatusIcon, StatusBadge };
