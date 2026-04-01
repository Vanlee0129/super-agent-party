'use client';

import React from 'react';
import { Globe } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useSettingsStore } from '@/lib/stores/settings-store';

export function ProxyConfig() {
  const { settings, updateSettings } = useSettingsStore();

  const handleProxyUpdate = (updates: Partial<typeof settings.proxy>) => {
    updateSettings({
      proxy: { ...settings.proxy, ...updates },
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5" />
          <CardTitle>Proxy Settings</CardTitle>
        </div>
        <CardDescription>Configure network proxy for API requests</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Enable Proxy</Label>
            <p className="text-sm text-muted-foreground">
              Route API requests through a proxy server
            </p>
          </div>
          <Switch
            checked={settings.proxy.enabled}
            onCheckedChange={(checked) => handleProxyUpdate({ enabled: checked })}
          />
        </div>

        {settings.proxy.enabled && (
          <>
            <div className="space-y-2">
              <Label htmlFor="proxyType">Proxy Type</Label>
              <Select
                value={settings.proxy.type}
                onValueChange={(value) => handleProxyUpdate({ type: value as 'http' | 'socks' })}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select proxy type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="http">HTTP Proxy</SelectItem>
                  <SelectItem value="socks">SOCKS Proxy</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 space-y-2">
                <Label htmlFor="proxyHost">Host</Label>
                <Input
                  id="proxyHost"
                  placeholder="127.0.0.1"
                  value={settings.proxy.host}
                  onChange={(e) => handleProxyUpdate({ host: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="proxyPort">Port</Label>
                <Input
                  id="proxyPort"
                  type="number"
                  placeholder="1080"
                  value={settings.proxy.port}
                  onChange={(e) => handleProxyUpdate({ port: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
