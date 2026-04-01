'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import type { BotPlatform, BotConfig } from '@/lib/stores/bots-store';

// Feishu schema
const feishuSchema = z.object({
  appId: z.string().min(1, 'App ID is required'),
  feishuAppSecret: z.string().min(1, 'App Secret is required'),
  botName: z.string().min(1, 'Bot Name is required'),
});

// QQ schema
const qqSchema = z.object({
  qqNumber: z.string().min(1, 'QQ Number is required'),
  token: z.string().min(1, 'Token is required'),
});

// Discord schema
const discordSchema = z.object({
  discordBotToken: z.string().min(1, 'Bot Token is required'),
  guildId: z.string().min(1, 'Guild ID is required'),
});

// Slack schema
const slackSchema = z.object({
  slackBotToken: z.string().min(1, 'Bot Token is required'),
  workspace: z.string().min(1, 'Workspace is required'),
});

// Dingtalk schema
const dingtalkSchema = z.object({
  appKey: z.string().min(1, 'App Key is required'),
  dingtalkAppSecret: z.string().min(1, 'App Secret is required'),
});

// Telegram schema
const telegramSchema = z.object({
  telegramBotToken: z.string().min(1, 'Bot Token is required'),
});

const schemas: Record<BotPlatform, z.ZodSchema> = {
  feishu: feishuSchema,
  qq: qqSchema,
  discord: discordSchema,
  slack: slackSchema,
  dingtalk: dingtalkSchema,
  telegram: telegramSchema,
};

const platformTitles: Record<BotPlatform, { title: string; description: string }> = {
  feishu: {
    title: 'Feishu Bot Configuration',
    description: 'Configure your Feishu (Lark) bot with App ID and App Secret',
  },
  qq: {
    title: 'QQ Bot Configuration',
    description: 'Configure your QQ bot with QQ number and token',
  },
  discord: {
    title: 'Discord Bot Configuration',
    description: 'Configure your Discord bot with bot token and guild ID',
  },
  slack: {
    title: 'Slack Bot Configuration',
    description: 'Configure your Slack bot with bot token and workspace',
  },
  dingtalk: {
    title: 'Dingtalk Bot Configuration',
    description: 'Configure your Dingtalk bot with app key and secret',
  },
  telegram: {
    title: 'Telegram Bot Configuration',
    description: 'Configure your Telegram bot with bot token',
  },
};

interface PlatformConfigFormProps {
  platform: BotPlatform;
  initialConfig?: Partial<BotConfig>;
  onSubmit: (config: BotConfig) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function PlatformConfigForm({
  platform,
  initialConfig = {},
  onSubmit,
  onCancel,
  isLoading = false,
}: PlatformConfigFormProps) {
  const schema = schemas[platform];
  const { title, description } = platformTitles[platform];

  const { register, handleSubmit, formState: { errors } } = useForm<BotConfig>({
    resolver: zodResolver(schema),
    defaultValues: initialConfig,
  });

  const handleFormSubmit = (data: BotConfig) => {
    onSubmit(data);
  };

  const renderPlatformFields = () => {
    switch (platform) {
      case 'feishu':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="appId">App ID</Label>
              <Input id="appId" placeholder="cli_xxxxx" {...register('appId')} />
              {errors.appId && <p className="text-sm text-destructive">{errors.appId.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="feishuAppSecret">App Secret</Label>
              <Input id="feishuAppSecret" type="password" placeholder="Enter app secret" {...register('feishuAppSecret')} />
              {errors.feishuAppSecret && <p className="text-sm text-destructive">{errors.feishuAppSecret.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="botName">Bot Name</Label>
              <Input id="botName" placeholder="My Feishu Bot" {...register('botName')} />
              {errors.botName && <p className="text-sm text-destructive">{errors.botName.message}</p>}
            </div>
          </>
        );

      case 'qq':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="qqNumber">QQ Number</Label>
              <Input id="qqNumber" placeholder="123456789" {...register('qqNumber')} />
              {errors.qqNumber && <p className="text-sm text-destructive">{errors.qqNumber.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="token">Token</Label>
              <Input id="token" type="password" placeholder="Enter QQ token" {...register('token')} />
              {errors.token && <p className="text-sm text-destructive">{errors.token.message}</p>}
            </div>
          </>
        );

      case 'discord':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="discordBotToken">Bot Token</Label>
              <Input id="discordBotToken" type="password" placeholder="Enter bot token" {...register('discordBotToken')} />
              {errors.discordBotToken && <p className="text-sm text-destructive">{errors.discordBotToken.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="guildId">Guild ID</Label>
              <Input id="guildId" placeholder="123456789012345678" {...register('guildId')} />
              {errors.guildId && <p className="text-sm text-destructive">{errors.guildId.message}</p>}
            </div>
          </>
        );

      case 'slack':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="slackBotToken">Bot Token</Label>
              <Input id="slackBotToken" type="password" placeholder="xoxb-..." {...register('slackBotToken')} />
              {errors.slackBotToken && <p className="text-sm text-destructive">{errors.slackBotToken.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="workspace">Workspace</Label>
              <Input id="workspace" placeholder="workspace-name" {...register('workspace')} />
              {errors.workspace && <p className="text-sm text-destructive">{errors.workspace.message}</p>}
            </div>
          </>
        );

      case 'dingtalk':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="appKey">App Key</Label>
              <Input id="appKey" placeholder="dingxxxxx" {...register('appKey')} />
              {errors.appKey && <p className="text-sm text-destructive">{errors.appKey.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="dingtalkAppSecret">App Secret</Label>
              <Input id="dingtalkAppSecret" type="password" placeholder="Enter app secret" {...register('dingtalkAppSecret')} />
              {errors.dingtalkAppSecret && <p className="text-sm text-destructive">{errors.dingtalkAppSecret.message}</p>}
            </div>
          </>
        );

      case 'telegram':
        return (
          <div className="space-y-2">
            <Label htmlFor="telegramBotToken">Bot Token</Label>
            <Input id="telegramBotToken" type="password" placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ" {...register('telegramBotToken')} />
            {errors.telegramBotToken && <p className="text-sm text-destructive">{errors.telegramBotToken.message}</p>}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <CardContent className="space-y-4">
          {renderPlatformFields()}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save Configuration'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}

export { feishuSchema, qqSchema, discordSchema, slackSchema, dingtalkSchema, telegramSchema };
