'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ModelConfig } from '@/lib/stores/settings-store';

const modelFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  provider: z.enum(['OpenAI', 'Anthropic', 'Ollama', 'MiniMax']),
  apiKey: z.string().optional(),
  baseUrl: z.string().optional(),
  modelName: z.string().min(1, 'Model name is required'),
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().min(1).max(100000).optional(),
});

type ModelFormData = z.infer<typeof modelFormSchema>;

interface ModelFormProps {
  model?: ModelConfig;
  onSubmit: (data: ModelConfig) => void;
  onCancel: () => void;
}

export function ModelForm({ model, onSubmit, onCancel }: ModelFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ModelFormData>({
    resolver: zodResolver(modelFormSchema),
    defaultValues: {
      name: model?.name || '',
      provider: model?.provider || 'OpenAI',
      apiKey: model?.apiKey || '',
      baseUrl: model?.baseUrl || '',
      modelName: model?.modelName || '',
      temperature: model?.temperature ?? 0.7,
      maxTokens: model?.maxTokens ?? 4096,
    },
  });

  const provider = watch('provider');

  const handleFormSubmit = (data: ModelFormData) => {
    const modelData: ModelConfig = {
      id: model?.id || crypto.randomUUID(),
      ...data,
    };
    onSubmit(modelData);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            placeholder="My Model"
            {...register('name')}
          />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="provider">Provider</Label>
          <Select
            defaultValue={model?.provider || 'OpenAI'}
            onValueChange={(value) => setValue('provider', value as 'OpenAI' | 'Anthropic' | 'Ollama' | 'MiniMax')}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="OpenAI">OpenAI</SelectItem>
              <SelectItem value="Anthropic">Anthropic</SelectItem>
              <SelectItem value="Ollama">Ollama</SelectItem>
              <SelectItem value="MiniMax">MiniMax</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="modelName">Model Name</Label>
        <Input
          id="modelName"
          placeholder="gpt-4, claude-3-opus, etc."
          {...register('modelName')}
        />
        {errors.modelName && (
          <p className="text-xs text-destructive">{errors.modelName.message}</p>
        )}
      </div>

      {provider !== 'Ollama' && (
        <div className="space-y-2">
          <Label htmlFor="apiKey">API Key</Label>
          <Input
            id="apiKey"
            type="password"
            placeholder="sk-..."
            {...register('apiKey')}
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="baseUrl">Base URL (Optional)</Label>
        <Input
          id="baseUrl"
          placeholder="https://api.openai.com/v1"
          {...register('baseUrl')}
        />
        {provider === 'Ollama' && (
          <p className="text-xs text-muted-foreground">
            Default: http://localhost:11434
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="temperature">Temperature</Label>
          <Input
            id="temperature"
            type="number"
            step="0.1"
            min="0"
            max="2"
            {...register('temperature', { valueAsNumber: true })}
          />
          {errors.temperature && (
            <p className="text-xs text-destructive">{errors.temperature.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="maxTokens">Max Tokens</Label>
          <Input
            id="maxTokens"
            type="number"
            min="1"
            max="100000"
            {...register('maxTokens', { valueAsNumber: true })}
          />
          {errors.maxTokens && (
            <p className="text-xs text-destructive">{errors.maxTokens.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {model ? 'Update' : 'Add'} Model
        </Button>
      </div>
    </form>
  );
}
