'use client';

import React, { useState, useEffect } from 'react';
import { useSearchStore, SearchProvider } from '@/lib/stores/search-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { AlertCircle, Check, Loader2, Save, X } from 'lucide-react';

interface ProviderConfigProps {
  provider: SearchProvider;
  onClose: () => void;
}

export function ProviderConfig({ provider, onClose }: ProviderConfigProps) {
  const { updateProvider } = useSearchStore();
  const [apiKey, setApiKey] = useState(provider.apiKey || '');
  const [maxResults, setMaxResults] = useState(provider.maxResults || 10);
  const [configUrl, setConfigUrl] = useState(
    (provider.config as { url?: string })?.url || ''
  );
  const [configBaseUrl, setConfigBaseUrl] = useState(
    (provider.config as { baseUrl?: string })?.baseUrl || ''
  );
  const [isSaving, setIsSaving] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updates: Partial<SearchProvider> = {
        apiKey: apiKey || undefined,
        maxResults,
      };

      if (provider.id === 'searxng' && configUrl) {
        updates.config = { url: configUrl };
      } else if (provider.id === 'crawl4ai' && configBaseUrl) {
        updates.config = { baseUrl: configBaseUrl };
      }

      updateProvider(provider.id, updates);

      // Call backend API to save configuration
      try {
        await fetch('/api/search/config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            providerId: provider.id,
            apiKey: apiKey || null,
            maxResults,
            config: updates.config,
          }),
        });
      } catch (e) {
        // Silently fail - config is saved locally anyway
      }

      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{provider.name} Configuration</CardTitle>
            <CardDescription>Configure API key and settings</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {provider.requiresApiKey ? (
          <div className="space-y-2">
            <Label htmlFor="apiKey">API Key</Label>
            <div className="relative">
              <Input
                id="apiKey"
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="pr-10"
              />
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <X className="h-4 w-4" /> : <Check className="h-4 w-4" />}
              </Button>
            </div>
            {provider.id === 'google' && (
              <p className="text-xs text-muted-foreground">
                Also requires CSE ID in settings
              </p>
            )}
            {provider.id === 'firecrawl' && (
              <p className="text-xs text-muted-foreground">
                Also supports self-hosted instance URL
              </p>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
            <Check className="h-4 w-4 text-green-500" />
            <span className="text-sm">No API key required for {provider.name}</span>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="maxResults">Max Results</Label>
          <Input
            id="maxResults"
            type="number"
            min={1}
            max={100}
            value={maxResults}
            onChange={(e) => setMaxResults(parseInt(e.target.value) || 10)}
          />
          <p className="text-xs text-muted-foreground">
            Number of search results to return (1-100)
          </p>
        </div>

        {provider.id === 'searxng' && (
          <div className="space-y-2">
            <Label htmlFor="searxngUrl">SearXNG URL</Label>
            <Input
              id="searxngUrl"
              type="url"
              value={configUrl}
              onChange={(e) => setConfigUrl(e.target.value)}
              placeholder="http://127.0.0.1:8080"
            />
            <p className="text-xs text-muted-foreground">
              URL of your self-hosted SearXNG instance
            </p>
          </div>
        )}

        {provider.id === 'crawl4ai' && (
          <div className="space-y-2">
            <Label htmlFor="crawl4aiUrl">Crawl4AI Server URL</Label>
            <Input
              id="crawl4aiUrl"
              type="url"
              value={configBaseUrl}
              onChange={(e) => setConfigBaseUrl(e.target.value)}
              placeholder="http://localhost:11235"
            />
            <p className="text-xs text-muted-foreground">
              URL of your self-hosted Crawl4AI server
            </p>
          </div>
        )}

        {provider.id === 'firecrawl' && (
          <div className="space-y-2">
            <Label htmlFor="firecrawlUrl">Firecrawl URL (Optional)</Label>
            <Input
              id="firecrawlUrl"
              type="url"
              value={(provider.config as { firecrawlUrl?: string })?.firecrawlUrl || ''}
              onChange={(e) =>
                updateProvider(provider.id, {
                  config: { ...provider.config, firecrawlUrl: e.target.value },
                })
              }
              placeholder="https://api.firecrawl.dev/v2"
            />
            <p className="text-xs text-muted-foreground">
              Leave empty to use official Firecrawl API
            </p>
          </div>
        )}

        {!provider.requiresApiKey && !provider.apiKey && (
          <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium">No API Key Configured</p>
              <p className="text-xs mt-1">
                This provider works without an API key, but some features may be limited.
              </p>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
