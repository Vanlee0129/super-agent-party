import React from 'react';
import { MessageCircle, Bot, Globe } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

const features = [
  {
    icon: MessageCircle,
    title: 'AI Chat',
    description: 'Intelligent conversation with multiple AI models. Supports context-aware discussions and customizable prompts.',
  },
  {
    icon: Bot,
    title: 'VRM',
    description: 'Virtual RM (Relationship Manager) powered by advanced AI. Creates lifelike virtual characters with personality.',
  },
  {
    icon: Globe,
    title: 'Multi-platform Bot',
    description: 'Deploy intelligent bots across multiple platforms. Unified management for Discord, Telegram, and more.',
  },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Welcome to Super Agent Party</h1>
        <p className="text-muted-foreground text-lg">
          Your all-in-one platform for AI-powered interactions
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card key={feature.title} className="transition-shadow hover:shadow-lg">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
