'use client';

import React from 'react';
import { useSearchStore, SearchProvider } from '@/lib/stores/search-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { AlertCircle, Check, Key, Loader2 } from 'lucide-react';

interface ProviderListProps {
  onSelectProvider: (provider: SearchProvider) => void;
  selectedProviderId?: string;
}

export function ProviderList({ onSelectProvider, selectedProviderId }: ProviderListProps) {
  const { config, toggleProvider, setDefaultProvider } = useSearchStore();
  const { providers } = config;

  const getStatusIcon = (provider: SearchProvider) => {
    if (!provider.requiresApiKey) {
      return <Check className="h-4 w-4 text-green-500" />;
    }
    if (provider.apiKey) {
      return <Key className="h-4 w-4 text-blue-500" />;
    }
    return <AlertCircle className="h-4 w-4 text-yellow-500" />;
  };

  const getStatusText = (provider: SearchProvider) => {
    if (!provider.requiresApiKey) {
      return 'Free';
    }
    if (provider.apiKey) {
      return 'Configured';
    }
    return 'No API Key';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Search Providers</h2>
        <Badge variant="secondary">
          {providers.filter((p) => p.enabled).length} enabled
        </Badge>
      </div>

      <div className="grid gap-3">
        {providers.map((provider) => (
          <Card
            key={provider.id}
            className={cn(
              'cursor-pointer transition-all hover:shadow-md',
              selectedProviderId === provider.id && 'ring-2 ring-primary',
              provider.enabled && 'border-l-4 border-l-primary'
            )}
            onClick={() => onSelectProvider(provider)}
          >
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base">{provider.name}</CardTitle>
                  {getStatusIcon(provider)}
                </div>
                <Switch
                  checked={provider.enabled}
                  onCheckedChange={() => toggleProvider(provider.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              <CardDescription className="text-xs mt-1">
                {provider.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={provider.free ? 'default' : 'outline'}
                    className="text-xs"
                  >
                    {provider.free ? 'Free' : 'Paid'}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {getStatusText(provider)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {config.defaultProvider === provider.id ? (
                    <Badge variant="secondary" className="text-xs">Default</Badge>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDefaultProvider(provider.id);
                      }}
                    >
                      Set Default
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
