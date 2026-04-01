'use client';

import React, { useState } from 'react';
import { useSearchStore, SearchProvider } from '@/lib/stores/search-store';
import { ProviderList } from '@/components/search/provider-list';
import { ProviderConfig } from '@/components/search/provider-config';
import { SearchTest } from '@/components/search/search-test';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Settings, FlaskConical, RotateCcw } from 'lucide-react';

export default function SearchConfigPage() {
  const { config, resetConfig, isLoading, setConfig } = useSearchStore();
  const [selectedProvider, setSelectedProvider] = useState<SearchProvider | null>(null);
  const [activeTab, setActiveTab] = useState('providers');

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all search configuration to defaults?')) {
      resetConfig();
      setSelectedProvider(null);
    }
  };

  const handleSaveAll = async () => {
    try {
      const response = await fetch('/api/search/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          providers: config.providers.map((p) => ({
            id: p.id,
            apiKey: p.apiKey,
            enabled: p.enabled,
            maxResults: p.maxResults,
            config: p.config,
          })),
          defaultProvider: config.defaultProvider,
        }),
      });

      if (response.ok) {
        alert('Configuration saved successfully!');
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      alert('Failed to save configuration to server. Local changes are preserved.');
    }
  };

  return (
    <div className="container max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Network Search Configuration</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Configure search providers and API keys
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button onClick={handleSaveAll} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Configuration'
            )}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="providers">
            <Settings className="mr-2 h-4 w-4" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="test">
            <FlaskConical className="mr-2 h-4 w-4" />
            Test Search
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <ProviderList
                onSelectProvider={setSelectedProvider}
                selectedProviderId={selectedProvider?.id}
              />
            </div>
            <div>
              {selectedProvider ? (
                <ProviderConfig
                  provider={selectedProvider}
                  onClose={() => setSelectedProvider(null)}
                />
              ) : (
                <Card className="h-full flex items-center justify-center">
                  <CardContent className="text-center py-12">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">
                      Select a provider to configure its settings
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="test" className="mt-6">
          <SearchTest />
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Provider Status</CardTitle>
          <CardDescription>Overview of configured providers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {config.providers.map((provider) => (
              <div
                key={provider.id}
                className="flex flex-col items-center p-3 border rounded-lg"
              >
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      provider.enabled ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  />
                  <span className="text-sm font-medium">{provider.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {provider.requiresApiKey
                    ? provider.apiKey
                      ? 'API Key Set'
                      : 'No API Key'
                    : 'No Key Required'}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
