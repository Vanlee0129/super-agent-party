'use client';

import React, { useState } from 'react';
import { Plus, Pencil, Trash2, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ModelForm } from './model-form';
import { useSettingsStore } from '@/lib/stores/settings-store';
import type { ModelConfig } from '@/lib/stores/settings-store';

const providerColors: Record<string, string> = {
  OpenAI: 'bg-green-500/10 text-green-500 border-green-500/20',
  Anthropic: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  Ollama: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  MiniMax: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
};

export function ModelConfig() {
  const { settings, updateSettings } = useSettingsStore();
  const [isAdding, setIsAdding] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);

  const handleAddModel = (model: ModelConfig) => {
    updateSettings({
      models: [...settings.models, model],
    });
    setIsAdding(false);
  };

  const handleUpdateModel = (model: ModelConfig) => {
    updateSettings({
      models: settings.models.map((m) => (m.id === model.id ? model : m)),
    });
    setEditingModel(null);
  };

  const handleDeleteModel = (id: string) => {
    const newModels = settings.models.filter((m) => m.id !== id);
    updateSettings({
      models: newModels,
      activeModel: settings.activeModel === id ? (newModels[0]?.id || '') : settings.activeModel,
    });
  };

  const handleSetActive = (id: string) => {
    updateSettings({ activeModel: id });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Model Configuration</CardTitle>
            <CardDescription>Configure AI models for chat interactions</CardDescription>
          </div>
          {!isAdding && !editingModel && (
            <Button onClick={() => setIsAdding(true)} size="sm">
              <Plus className="h-4 w-4 mr-1" />
              Add Model
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isAdding && (
          <div className="mb-6 p-4 border rounded-lg bg-muted/50">
            <h4 className="font-medium mb-4">Add New Model</h4>
            <ModelForm
              onSubmit={handleAddModel}
              onCancel={() => setIsAdding(false)}
            />
          </div>
        )}

        {editingModel && (
          <div className="mb-6 p-4 border rounded-lg bg-muted/50">
            <h4 className="font-medium mb-4">Edit Model</h4>
            <ModelForm
              model={editingModel}
              onSubmit={handleUpdateModel}
              onCancel={() => setEditingModel(null)}
            />
          </div>
        )}

        {settings.models.length === 0 && !isAdding && (
          <div className="text-center py-8 text-muted-foreground">
            <p>No models configured yet.</p>
            <p className="text-sm">Click &quot;Add Model&quot; to get started.</p>
          </div>
        )}

        <div className="space-y-3">
          {settings.models.map((model) => (
            <div
              key={model.id}
              className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                settings.activeModel === model.id
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-muted/50'
              }`}
            >
              <div className="flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{model.name}</span>
                    <Badge
                      variant="outline"
                      className={providerColors[model.provider]}
                    >
                      {model.provider}
                    </Badge>
                    {settings.activeModel === model.id && (
                      <Badge variant="default" className="text-xs">
                        Active
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">
                    {model.modelName}
                  </p>
                  {model.baseUrl && (
                    <p className="text-xs text-muted-foreground truncate">
                      {model.baseUrl}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                {settings.activeModel !== model.id && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleSetActive(model.id)}
                    title="Set as active"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setEditingModel(model)}
                  title="Edit"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDeleteModel(model.id)}
                  title="Delete"
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
