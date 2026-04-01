import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface SearchProvider {
  id: string;
  name: string;
  description: string;
  requiresApiKey: boolean;
  free: boolean;
  maxResults?: number;
  apiKey?: string;
  enabled: boolean;
  config?: Record<string, unknown>;
}

export interface SearchConfig {
  providers: SearchProvider[];
  defaultProvider: string;
  rateLimit?: number;
}

export interface SearchResult {
  title: string;
  link: string;
  snippet: string;
  source?: string;
}

export interface SearchState {
  config: SearchConfig;
  isLoading: boolean;
  testResults: SearchResult[];
  testLoading: boolean;
  error: string | null;

  // Actions
  setConfig: (config: Partial<SearchConfig>) => void;
  updateProvider: (providerId: string, updates: Partial<SearchProvider>) => void;
  toggleProvider: (providerId: string) => void;
  setDefaultProvider: (providerId: string) => void;
  setTestResults: (results: SearchResult[]) => void;
  setTestLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetConfig: () => void;
}

const defaultProviders: SearchProvider[] = [
  {
    id: 'duckduckgo',
    name: 'DuckDuckGo',
    description: 'Free, no API key required. Good for general web search.',
    requiresApiKey: false,
    free: true,
    maxResults: 10,
    enabled: true,
  },
  {
    id: 'tavily',
    name: 'Tavily',
    description: 'High-quality search API with AI summarization. Requires API key.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'bing',
    name: 'Bing',
    description: 'Microsoft Bing search API. Requires API key.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'google',
    name: 'Google',
    description: 'Google Custom Search API. Requires API key and CSE ID.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'brave',
    name: 'Brave',
    description: 'Brave Search API. Requires API key.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'exa',
    name: 'Exa',
    description: 'AI-powered search API. Requires API key.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'searxng',
    name: 'SearXNG',
    description: 'Open-source meta-search engine. Can use self-hosted instance.',
    requiresApiKey: false,
    free: true,
    maxResults: 10,
    enabled: false,
    config: { url: 'http://127.0.0.1:8080' },
  },
  {
    id: 'jina',
    name: 'Jina',
    description: 'Web crawler and reader API. Requires API key for full features.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
  {
    id: 'crawl4ai',
    name: 'Crawl4AI',
    description: 'AI-friendly web crawler. Requires self-hosted server.',
    requiresApiKey: false,
    free: true,
    maxResults: 10,
    enabled: false,
    config: { baseUrl: 'http://localhost:11235' },
  },
  {
    id: 'firecrawl',
    name: 'Firecrawl',
    description: 'Website scraping and search API. Requires API key.',
    requiresApiKey: true,
    free: false,
    maxResults: 10,
    enabled: false,
  },
];

const defaultConfig: SearchConfig = {
  providers: defaultProviders,
  defaultProvider: 'duckduckgo',
  rateLimit: 60,
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      config: defaultConfig,
      isLoading: false,
      testResults: [],
      testLoading: false,
      error: null,

      setConfig: (newConfig) =>
        set((state) => ({
          config: { ...state.config, ...newConfig },
        })),

      updateProvider: (providerId, updates) =>
        set((state) => ({
          config: {
            ...state.config,
            providers: state.config.providers.map((p) =>
              p.id === providerId ? { ...p, ...updates } : p
            ),
          },
        })),

      toggleProvider: (providerId) =>
        set((state) => ({
          config: {
            ...state.config,
            providers: state.config.providers.map((p) =>
              p.id === providerId ? { ...p, enabled: !p.enabled } : p
            ),
          },
        })),

      setDefaultProvider: (providerId) =>
        set((state) => ({
          config: { ...state.config, defaultProvider: providerId },
        })),

      setTestResults: (results) => set({ testResults: results }),

      setTestLoading: (loading) => set({ testLoading: loading }),

      setError: (error) => set({ error }),

      resetConfig: () => set({ config: defaultConfig }),
    }),
    {
      name: 'search-config-storage',
    }
  )
);
