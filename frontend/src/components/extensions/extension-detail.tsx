'use client';

import React from 'react';
import { Extension } from '@/lib/stores/extensions-store';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConfigForm } from './config-form';
import { ExternalLink, Github, User } from 'lucide-react';

interface ExtensionDetailProps {
  extension: Extension | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onToggle: (extId: string) => void;
}

export function ExtensionDetail({ extension, open, onOpenChange, onToggle }: ExtensionDetailProps) {
  if (!extension) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between pr-8">
            <div>
              <DialogTitle className="text-xl">{extension.name}</DialogTitle>
              <DialogDescription className="mt-2">{extension.description}</DialogDescription>
            </div>
            <Badge variant="secondary">v{extension.version}</Badge>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Author:</span>
              <span>{extension.author}</span>
            </div>
            {extension.category && (
              <Badge variant="outline">{extension.category}</Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={extension.enabled ?? true ? 'default' : 'secondary'}
              size="sm"
              onClick={() => onToggle(extension.id)}
            >
              {extension.enabled ?? true ? 'Enabled' : 'Disabled'}
            </Button>
            {extension.repository && (
              <Button variant="outline" size="sm" asChild>
                <a href={extension.repository} target="_blank" rel="noopener noreferrer">
                  <Github className="h-4 w-4 mr-1" />
                  Repository
                  <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            )}
          </div>
        </div>

        <Tabs defaultValue="config" className="w-full">
          <TabsList className="w-full">
            <TabsTrigger value="config" className="flex-1">Configuration</TabsTrigger>
            <TabsTrigger value="readme" className="flex-1">README</TabsTrigger>
            <TabsTrigger value="permissions" className="flex-1">Permissions</TabsTrigger>
          </TabsList>

          <TabsContent value="config" className="space-y-4">
            <ConfigForm extension={extension} />
          </TabsContent>

          <TabsContent value="readme">
            <div className="rounded-md border p-4 min-h-[200px]">
              {extension.systemPrompt ? (
                <pre className="whitespace-pre-wrap text-sm">{extension.systemPrompt}</pre>
              ) : (
                <p className="text-muted-foreground italic">No README available</p>
              )}
            </div>
          </TabsContent>

          <TabsContent value="permissions">
            <div className="rounded-md border p-4">
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-green-500"></span>
                  <span>Access to chat messages</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-green-500"></span>
                  <span>Store and retrieve configuration</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-yellow-500"></span>
                  <span>Network access (if repository is configured)</span>
                </li>
                {extension.enableVrmWindowSize && (
                  <li className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    <span>VRM window size customization</span>
                  </li>
                )}
              </ul>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
