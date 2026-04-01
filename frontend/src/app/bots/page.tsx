'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  MessageCircle,
  Users,
  Hash,
  Bot as BotIcon,
  Plus,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { BotList } from '@/components/bots/bot-list';
import { PlatformConfigForm } from '@/components/bots/platform-config';
import { useBotsStore, type BotPlatform, type Bot, type BotConfig, PLATFORM_NAMES } from '@/lib/stores/bots-store';
import { useWebSocket } from '@/hooks/use-websocket';

// Platform icons
const PlatformTabIcon = ({ platform }: { platform: BotPlatform }) => {
  const icons: Record<BotPlatform, React.ReactNode> = {
    feishu: <MessageCircle className="h-4 w-4" />,
    qq: <MessageCircle className="h-4 w-4" />,
    discord: <Users className="h-4 w-4" />,
    slack: <Hash className="h-4 w-4" />,
    dingtalk: <MessageCircle className="h-4 w-4" />,
    telegram: <BotIcon className="h-4 w-4" />,
  };
  return <span className="flex items-center">{icons[platform]}</span>;
};

const platforms: BotPlatform[] = ['feishu', 'qq', 'discord', 'slack', 'dingtalk', 'telegram'];

export default function BotsPage() {
  const {
    activePlatform,
    filterStatus,
    bots,
    isLoading,
    error,
    setActivePlatform,
    setFilterStatus,
    addBot,
    updateBot,
    removeBot,
    setBotStatus,
    setLoading,
    setError,
    getFilteredBots,
  } = useBotsStore();

  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [configuringBot, setConfiguringBot] = useState<Bot | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { request, isConnected } = useWebSocket();

  const filteredBots = getFilteredBots();

  // Fetch bot status from backend
  const fetchBotStatus = useCallback(async (platform: BotPlatform) => {
    if (!isConnected) return;

    const endpoints: Record<BotPlatform, string> = {
      feishu: '/feishu_bot_status',
      qq: '/qq_bot_status',
      discord: '/discord_bot_status',
      slack: '/slack_bot_status',
      dingtalk: '/dingtalk_bot_status',
      telegram: '/telegram_bot_status',
    };

    try {
      const response = await request(endpoints[platform]);
      if (response.result) {
        // Update bot status based on response
        const result = response.result as { running?: boolean; status?: string };
        const platformBots = bots.filter((b) => b.platform === platform);
        platformBots.forEach((bot) => {
          const isRunning = result.running ?? result.status === 'running';
          setBotStatus(bot.id, isRunning ? 'running' : 'stopped');
        });
      }
    } catch (err) {
      console.error(`Failed to fetch ${platform} bot status:`, err);
    }
  }, [isConnected, request, bots, setBotStatus]);

  // Start bot
  const handleStartBot = async (bot: Bot) => {
    if (!isConnected) {
      setError('WebSocket not connected');
      return;
    }

    setBotStatus(bot.id, 'starting');
    setLoading(true);

    const endpoints: Record<BotPlatform, string> = {
      feishu: '/start_feishu_bot',
      qq: '/start_qq_bot',
      discord: '/start_discord_bot',
      slack: '/start_slack_bot',
      dingtalk: '/start_dingtalk_bot',
      telegram: '/start_telegram_bot',
    };

    try {
      const response = await request(endpoints[bot.platform], { config: bot.config });
      if (response.error) {
        setBotStatus(bot.id, 'error', String(response.error));
      } else {
        setBotStatus(bot.id, 'running');
      }
    } catch (err) {
      setBotStatus(bot.id, 'error', String(err));
    } finally {
      setLoading(false);
    }
  };

  // Stop bot
  const handleStopBot = async (bot: Bot) => {
    if (!isConnected) {
      setError('WebSocket not connected');
      return;
    }

    setBotStatus(bot.id, 'stopping');
    setLoading(true);

    const endpoints: Record<BotPlatform, string> = {
      feishu: '/stop_feishu_bot',
      qq: '/stop_qq_bot',
      discord: '/stop_discord_bot',
      slack: '/stop_slack_bot',
      dingtalk: '/stop_dingtalk_bot',
      telegram: '/stop_telegram_bot',
    };

    try {
      const response = await request(endpoints[bot.platform]);
      if (response.error) {
        setBotStatus(bot.id, 'error', String(response.error));
      } else {
        setBotStatus(bot.id, 'stopped');
      }
    } catch (err) {
      setBotStatus(bot.id, 'error', String(err));
    } finally {
      setLoading(false);
    }
  };

  // Configure bot
  const handleConfigureBot = (bot: Bot) => {
    setConfiguringBot(bot);
    setShowConfigDialog(true);
  };

  // Delete bot
  const handleDeleteBot = (bot: Bot) => {
    if (bot.status === 'running') {
      setError('Cannot delete a running bot. Stop it first.');
      return;
    }
    removeBot(bot.id);
  };

  // Add new bot
  const handleAddBot = () => {
    setConfiguringBot(null);
    setShowConfigDialog(true);
  };

  // Save bot configuration
  const handleSaveConfig = async (config: BotConfig) => {
    setIsSubmitting(true);

    try {
      if (configuringBot) {
        // Update existing bot
        updateBot(configuringBot.id, { config });
      } else {
        // Add new bot
        const botName = config.botName ||
          config.qqNumber ||
          config.appId?.slice(0, 8) ||
          `Bot ${Date.now()}`;

        addBot({
          platform: activePlatform,
          name: botName,
          status: 'stopped',
          config,
        });
      }

      setShowConfigDialog(false);
      setConfiguringBot(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bot Management</h1>
          <p className="text-muted-foreground">
            Configure and manage your platform bots
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-muted-foreground">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Platform Tabs */}
      <div className="border-b">
        <nav className="flex gap-4 -mb-px">
          {platforms.map((platform) => (
            <button
              key={platform}
              onClick={() => setActivePlatform(platform)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activePlatform === platform
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
              }`}
            >
              <PlatformTabIcon platform={platform} />
              {PLATFORM_NAMES[platform]}
            </button>
          ))}
        </nav>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
          {error}
          <button
            className="float-right font-medium"
            onClick={() => setError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Bot List */}
      <BotList
        bots={filteredBots}
        platform={activePlatform}
        filterStatus={filterStatus}
        onFilterChange={setFilterStatus}
        onStartBot={handleStartBot}
        onStopBot={handleStopBot}
        onConfigureBot={handleConfigureBot}
        onDeleteBot={handleDeleteBot}
        onAddBot={handleAddBot}
      />

      {/* Configuration Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {configuringBot ? 'Configure Bot' : `Add ${PLATFORM_NAMES[activePlatform]} Bot`}
            </DialogTitle>
            <DialogDescription>
              {configuringBot
                ? 'Update the bot configuration'
                : `Enter the configuration details for your ${PLATFORM_NAMES[activePlatform]} bot`}
            </DialogDescription>
          </DialogHeader>
          <PlatformConfigForm
            platform={activePlatform}
            initialConfig={configuringBot?.config}
            onSubmit={handleSaveConfig}
            onCancel={() => setShowConfigDialog(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
