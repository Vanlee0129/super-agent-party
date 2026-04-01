'use client';

import React from 'react';
import { Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react';
import { ConnectionStatus } from '@/lib/api/websocket';
import { cn } from '@/lib/utils';

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
  reconnectInfo?: { attempts: number; nextDelay: number | null; maxAttempts: number };
  showDetails?: boolean;
}

const statusConfig: Record<ConnectionStatus, {
  icon: typeof Wifi;
  label: string;
  color: string;
  bgColor: string;
  animate?: boolean;
}> = {
  connected: {
    icon: Wifi,
    label: 'Connected',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
  connecting: {
    icon: Loader2,
    label: 'Connecting',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    animate: true,
  },
  reconnecting: {
    icon: Loader2,
    label: 'Reconnecting',
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    animate: true,
  },
  disconnected: {
    icon: WifiOff,
    label: 'Disconnected',
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
  },
};

export function ConnectionStatusIndicator({
  status,
  reconnectInfo,
  showDetails = false,
}: ConnectionStatusIndicatorProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2">
      <div className={cn('flex items-center gap-1.5 px-2 py-1 rounded-full', config.bgColor)}>
        <Icon className={cn('h-4 w-4', config.color, config.animate && 'animate-spin')} />
        <span className={cn('text-xs font-medium', config.color)}>{config.label}</span>
      </div>
      {showDetails && status === 'reconnecting' && reconnectInfo && (
        <span className="text-xs text-muted-foreground">
          Attempt {reconnectInfo.attempts}/{reconnectInfo.maxAttempts}
          {reconnectInfo.nextDelay && ` (${Math.round(reconnectInfo.nextDelay / 1000)}s)`}
        </span>
      )}
      {showDetails && status === 'disconnected' && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <AlertCircle className="h-3 w-3" />
          <span>Max attempts reached</span>
        </div>
      )}
    </div>
  );
}
