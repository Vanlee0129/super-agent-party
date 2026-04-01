import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ModelConfig {
  id: string;
  name: string;
  provider: 'OpenAI' | 'Anthropic' | 'Ollama' | 'MiniMax';
  apiKey?: string;
  baseUrl?: string;
  modelName: string;
  temperature?: number;
  maxTokens?: number;
}

export interface ProxyConfig {
  enabled: boolean;
  type: 'http' | 'socks';
  host: string;
  port: number;
}

export interface ApiEndpoints {
  backendHost: string;
  backendPort: number;
  websocketUrl: string;
}

export interface Settings {
  theme: 'light' | 'dark' | 'system';
  language: 'zh-CN' | 'en';
  activeModel: string;
  models: ModelConfig[];
  autoSave: boolean;
  proxy: ProxyConfig;
  apiEndpoints: ApiEndpoints;
}

export interface SettingsState {
  settings: Settings;
  updateSettings: (settings: Partial<Settings>) => void;
  resetSettings: () => void;
}

const defaultSettings: Settings = {
  theme: 'system',
  language: 'zh-CN',
  activeModel: '',
  models: [],
  autoSave: true,
  proxy: {
    enabled: false,
    type: 'http',
    host: '',
    port: 1080,
  },
  apiEndpoints: {
    backendHost: 'localhost',
    backendPort: 3456,
    websocketUrl: 'ws://localhost:3456',
  },
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'settings-storage',
    }
  )
);
