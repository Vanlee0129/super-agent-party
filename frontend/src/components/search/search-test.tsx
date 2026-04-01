'use client';

import React, { useState } from 'react';
import { useSearchStore, SearchResult } from '@/lib/stores/search-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Search, ExternalLink, AlertCircle, Check } from 'lucide-react';

export function SearchTest() {
  const { config, testResults, testLoading, setTestResults, setTestLoading } = useSearchStore();
  const [query, setQuery] = useState('');
  const [selectedProvider, setSelectedProvider] = useState(config.defaultProvider);
  const [error, setError] = useState<string | null>(null);
  const [responseTime, setResponseTime] = useState<number | null>(null);

  const handleTestSearch = async () => {
    if (!query.trim()) return;

    setError(null);
    setTestLoading(true);
    setTestResults([]);
    setResponseTime(null);

    const startTime = Date.now();

    try {
      const response = await fetch('/api/search/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selectedProvider,
          query: query.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResponseTime(Date.now() - startTime);

      if (data.error) {
        throw new Error(data.error);
      }

      // Parse results based on provider response format
      let results: SearchResult[] = [];

      if (Array.isArray(data.results)) {
        results = data.results.map((item: Record<string, unknown>, index: number) => ({
          title: String(item.title || item.name || `Result ${index + 1}`),
          link: String(item.link || item.url || '#'),
          snippet: String(item.snippet || item.description || item.content || ''),
          source: item.source ? String(item.source) : selectedProvider,
        }));
      } else if (data.content) {
        // Single content result (for crawlers)
        results = [{
          title: data.title || query,
          link: data.url || '#',
          snippet: data.content,
          source: selectedProvider,
        }];
      }

      setTestResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setTestResults([]);
    } finally {
      setTestLoading(false);
    }
  };

  const enabledProviders = config.providers.filter((p) => p.enabled);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Test Search</CardTitle>
        <CardDescription>Test your search configuration</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-4">
          <div className="flex-1 space-y-2">
            <Label htmlFor="searchQuery">Search Query</Label>
            <Input
              id="searchQuery"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleTestSearch();
                }
              }}
            />
          </div>
          <div className="w-48 space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {enabledProviders.length > 0 ? (
                  enabledProviders.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      {provider.name}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="duckduckgo" disabled>
                    No providers enabled
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button onClick={handleTestSearch} disabled={testLoading || !query.trim()}>
              {testLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
            <div className="text-sm text-red-800">
              <p className="font-medium">Search Error</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
          </div>
        )}

        {responseTime !== null && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Check className="h-3 w-3 text-green-500" />
            <span>Response time: {responseTime}ms</span>
          </div>
        )}

        <Tabs defaultValue="results" className="w-full">
          <TabsList>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="raw">Raw Response</TabsTrigger>
          </TabsList>
          <TabsContent value="results" className="mt-4">
            {testResults.length > 0 ? (
              <div className="space-y-4">
                {testResults.map((result, index) => (
                  <Card key={index} className="p-4">
                    <h4 className="font-medium text-sm mb-1">{result.title}</h4>
                    <a
                      href={result.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline flex items-center gap-1 mb-2"
                    >
                      {result.link.substring(0, 60)}
                      {result.link.length > 60 && '...'}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                    <p className="text-sm text-muted-foreground">{result.snippet}</p>
                    {result.source && (
                      <p className="text-xs text-muted-foreground mt-2">
                        Source: {result.source}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No results yet. Run a search to see results here.</p>
              </div>
            )}
          </TabsContent>
          <TabsContent value="raw" className="mt-4">
            <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-xs">
              {testResults.length > 0
                ? JSON.stringify(testResults, null, 2)
                : 'No raw data available. Run a search first.'}
            </pre>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
