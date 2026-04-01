'use client';

import React from 'react';
import { Extension } from '@/lib/stores/extensions-store';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Settings, Trash2, ExternalLink } from 'lucide-react';

interface ExtensionCardProps {
  extension: Extension;
  onToggle: (extId: string) => void;
  onConfigure: (extension: Extension) => void;
  onDelete: (extId: string) => void;
}

export function ExtensionCard({ extension, onToggle, onConfigure, onDelete }: ExtensionCardProps) {
  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${extension.name}"?`)) {
      onDelete(extension.id);
    }
  };

  return (
    <Card className="flex flex-col hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-lg">{extension.name}</CardTitle>
            <CardDescription className="line-clamp-2">{extension.description}</CardDescription>
          </div>
          <Badge variant="secondary" className="ml-2">
            v{extension.version}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="space-y-2 text-sm text-muted-foreground">
          <p><span className="font-medium">Author:</span> {extension.author}</p>
          {extension.category && (
            <p><span className="font-medium">Category:</span> {extension.category}</p>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex items-center justify-between pt-4 border-t">
        <div className="flex items-center space-x-2">
          <Switch
            checked={extension.enabled ?? true}
            onCheckedChange={() => onToggle(extension.id)}
            id={`toggle-${extension.id}`}
          />
          <label htmlFor={`toggle-${extension.id}`} className="text-sm cursor-pointer">
            {extension.enabled ?? true ? 'Enabled' : 'Disabled'}
          </label>
        </div>
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onConfigure(extension)}
            title="Configure"
          >
            <Settings className="h-4 w-4" />
          </Button>
          {extension.repository && (
            <Button
              variant="ghost"
              size="icon"
              asChild
              title="Repository"
            >
              <a href={extension.repository} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            title="Delete"
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
