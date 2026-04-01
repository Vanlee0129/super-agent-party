import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type BotPlatform = 'feishu' | 'qq' | 'discord' | 'slack' | 'dingtalk' | 'telegram';

export type BotStatus = 'running' | 'stopped' | 'starting' | 'stopping' | 'error';

export interface BotConfig {
  // Feishu
  appId?: string;
  feishuAppSecret?: string;
  botName?: string;
  // QQ
  qqNumber?: string;
  token?: string;
  // Discord
  discordBotToken?: string;
  guildId?: string;
  // Slack
  slackBotToken?: string;
  workspace?: string;
  // Dingtalk
  appKey?: string;
  dingtalkAppSecret?: string;
  // Telegram
  telegramBotToken?: string;
}

export interface Bot {
  id: string;
  platform: BotPlatform;
  name: string;
  status: BotStatus;
  config: BotConfig;
  createdAt: number;
  updatedAt: number;
  error?: string;
}

export interface BotsState {
  bots: Bot[];
  activePlatform: BotPlatform;
  filterStatus: BotStatus | 'all';
  isLoading: boolean;
  error: string | null;

  // Actions
  setActivePlatform: (platform: BotPlatform) => void;
  setFilterStatus: (status: BotStatus | 'all') => void;
  addBot: (bot: Omit<Bot, 'id' | 'createdAt' | 'updatedAt'>) => Bot;
  updateBot: (id: string, updates: Partial<Bot>) => void;
  removeBot: (id: string) => void;
  setBotStatus: (id: string, status: BotStatus, error?: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  getBotsByPlatform: (platform: BotPlatform) => Bot[];
  getFilteredBots: () => Bot[];
}

// Platform display names
export const PLATFORM_NAMES: Record<BotPlatform, string> = {
  feishu: 'Feishu',
  qq: 'QQ',
  discord: 'Discord',
  slack: 'Slack',
  dingtalk: 'Dingtalk',
  telegram: 'Telegram',
};

// Platform icons (lucide-react icon names)
export const PLATFORM_ICONS: Record<BotPlatform, string> = {
  feishu: 'MessageCircle',
  qq: 'MessageCircle',
  discord: 'MessageCircle',
  slack: 'MessageCircle',
  dingtalk: 'MessageCircle',
  telegram: 'MessageCircle',
};

// API endpoints for each platform
export const PLATFORM_ENDPOINTS: Record<BotPlatform, { start: string; stop: string; status: string }> = {
  feishu: {
    start: '/start_feishu_bot',
    stop: '/stop_feishu_bot',
    status: '/feishu_bot_status',
  },
  qq: {
    start: '/start_qq_bot',
    stop: '/stop_qq_bot',
    status: '/qq_bot_status',
  },
  discord: {
    start: '/start_discord_bot',
    stop: '/stop_discord_bot',
    status: '/discord_bot_status',
  },
  slack: {
    start: '/start_slack_bot',
    stop: '/stop_slack_bot',
    status: '/slack_bot_status',
  },
  dingtalk: {
    start: '/start_dingtalk_bot',
    stop: '/stop_dingtalk_bot',
    status: '/dingtalk_bot_status',
  },
  telegram: {
    start: '/start_telegram_bot',
    stop: '/stop_telegram_bot',
    status: '/telegram_bot_status',
  },
};

// Default config for each platform
export const DEFAULT_CONFIGS: Record<BotPlatform, BotConfig> = {
  feishu: {
    appId: '',
    feishuAppSecret: '',
    botName: '',
  },
  qq: {
    qqNumber: '',
    token: '',
  },
  discord: {
    discordBotToken: '',
    guildId: '',
  },
  slack: {
    slackBotToken: '',
    workspace: '',
  },
  dingtalk: {
    appKey: '',
    dingtalkAppSecret: '',
  },
  telegram: {
    telegramBotToken: '',
  },
};

export const useBotsStore = create<BotsState>()(
  persist(
    (set, get) => ({
      bots: [],
      activePlatform: 'feishu',
      filterStatus: 'all',
      isLoading: false,
      error: null,

      setActivePlatform: (platform) => set({ activePlatform: platform }),

      setFilterStatus: (status) => set({ filterStatus: status }),

      addBot: (botData) => {
        const now = Date.now();
        const newBot: Bot = {
          ...botData,
          id: crypto.randomUUID(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({
          bots: [...state.bots, newBot],
        }));
        return newBot;
      },

      updateBot: (id, updates) => {
        set((state) => ({
          bots: state.bots.map((bot) =>
            bot.id === id
              ? { ...bot, ...updates, updatedAt: Date.now() }
              : bot
          ),
        }));
      },

      removeBot: (id) => {
        set((state) => ({
          bots: state.bots.filter((bot) => bot.id !== id),
        }));
      },

      setBotStatus: (id, status, error) => {
        set((state) => ({
          bots: state.bots.map((bot) =>
            bot.id === id
              ? { ...bot, status, error, updatedAt: Date.now() }
              : bot
          ),
        }));
      },

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      getBotsByPlatform: (platform) => {
        return get().bots.filter((bot) => bot.platform === platform);
      },

      getFilteredBots: () => {
        const state = get();
        let filtered = state.bots.filter((bot) => bot.platform === state.activePlatform);
        if (state.filterStatus !== 'all') {
          filtered = filtered.filter((bot) => bot.status === state.filterStatus);
        }
        return filtered;
      },
    }),
    {
      name: 'bots-storage',
    }
  )
);
