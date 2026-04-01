'use client';

import React from 'react';
import { Server } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { useSettingsStore } from '@/lib/stores/settings-store';

export function ApiEndpoints() {
  const { settings, updateSettings } = useSettingsStore();

  const handleEndpointsUpdate = (updates: Partial<typeof settings.apiEndpoints>) => {
    updateSettings({
      apiEndpoints: { ...settings.apiEndpoints, ...updates },
    });
  };

  const generateWebsocketUrl = () => {
    const { backendHost, backendPort } = settings.apiEndpoints;
    return `ws://${backendHost}:${backendPort}`;
  };

  const handleHostChange = (host: string) => {
    handleEndpointsUpdate({ backendHost: host });
    handleEndpointsUpdate({ websocketUrl: generateWebsocketUrl() });
  };

  const handlePortChange = (port: number) => {
    handleEndpointsUpdate({ backendPort: port });
    handleEndpointsUpdate({ websocketUrl: generateWebsocketUrl() });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          <CardTitle>API Endpoints</CardTitle>
        </div>
        <CardDescription>Configure backend server connection</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="backendHost">Backend Host</Label>
            <Input
              id="backendHost"
              placeholder="localhost"
              value={settings.apiEndpoints.backendHost}
              onChange={(e) => handleHostChange(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="backendPort">Backend Port</Label>
            <Input
              id="backendPort"
              type="number"
              placeholder="3456"
              value={settings.apiEndpoints.backendPort}
              onChange={(e) => handlePortChange(parseInt(e.target.value) || 0)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="websocketUrl">WebSocket URL</Label>
          <Input
            id="websocketUrl"
            placeholder="ws://localhost:3456"
            value={settings.apiEndpoints.websocketUrl}
            onChange={(e) => handleEndpointsUpdate({ websocketUrl: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            Used for real-time communication with the backend server
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
