'use client';

import React, { useState } from 'react';
import { Extension } from '@/lib/stores/extensions-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Save, Loader2 } from 'lucide-react';

interface ConfigFormProps {
  extension: Extension;
}

interface ExtensionConfig {
  systemPrompt?: string;
  transparent?: boolean;
  width?: number;
  height?: number;
  enableVrmWindowSize?: boolean;
}

export function ConfigForm({ extension }: ConfigFormProps) {
  const [config, setConfig] = useState<ExtensionConfig>({
    systemPrompt: extension.systemPrompt || '',
    transparent: extension.transparent || false,
    width: extension.width || 800,
    height: extension.height || 600,
    enableVrmWindowSize: extension.enableVrmWindowSize || false,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleChange = (key: keyof ExtensionConfig, value: string | number | boolean) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`/api/extensions/${extension.id}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="system-prompt">System Prompt</Label>
        <Textarea
          id="system-prompt"
          value={config.systemPrompt || ''}
          onChange={(e) => handleChange('systemPrompt', e.target.value)}
          placeholder="Enter system prompt for this extension..."
          rows={4}
        />
        <p className="text-xs text-muted-foreground">
          Customize how the AI behaves when this extension is active.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="width">Window Width</Label>
        <Input
          id="width"
          type="number"
          value={config.width || 800}
          onChange={(e) => handleChange('width', parseInt(e.target.value) || 800)}
          min={400}
          max={1920}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="height">Window Height</Label>
        <Input
          id="height"
          type="number"
          value={config.height || 600}
          onChange={(e) => handleChange('height', parseInt(e.target.value) || 600)}
          min={300}
          max={1080}
        />
      </div>

      <div className="flex items-center justify-between rounded-lg border p-3">
        <div className="space-y-0.5">
          <Label htmlFor="transparent" className="cursor-pointer">Transparent Background</Label>
          <p className="text-xs text-muted-foreground">
            Enable transparent window background
          </p>
        </div>
        <Switch
          id="transparent"
          checked={config.transparent || false}
          onCheckedChange={(checked) => handleChange('transparent', checked)}
        />
      </div>

      <div className="flex items-center justify-between rounded-lg border p-3">
        <div className="space-y-0.5">
          <Label htmlFor="vrm-size" className="cursor-pointer">VRM Window Size</Label>
          <p className="text-xs text-muted-foreground">
            Allow this extension to control VRM window size
          </p>
        </div>
        <Switch
          id="vrm-size"
          checked={config.enableVrmWindowSize || false}
          onCheckedChange={(checked) => handleChange('enableVrmWindowSize', checked)}
        />
      </div>

      <Button onClick={handleSave} disabled={isSaving} className="w-full">
        {isSaving ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Saving...
          </>
        ) : saved ? (
          <>
            <Save className="h-4 w-4" />
            Saved!
          </>
        ) : (
          <>
            <Save className="h-4 w-4" />
            Save Configuration
          </>
        )}
      </Button>
    </div>
  );
}
