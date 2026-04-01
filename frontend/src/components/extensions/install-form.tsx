'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useExtensionsStore } from '@/lib/stores/extensions-store';
import { Github, Upload, Link2, Loader2 } from 'lucide-react';

interface InstallFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function InstallForm({ open, onOpenChange }: InstallFormProps) {
  const [installUrl, setInstallUrl] = useState('');
  const [backupUrl, setBackupUrl] = useState('');
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('url');
  const { installFromUrl, isLoading, error } = useExtensionsStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!installUrl.trim()) return;
    await installFromUrl(installUrl.trim(), backupUrl.trim());
    if (!error) {
      setInstallUrl('');
      setBackupUrl('');
      onOpenChange(false);
    }
  };

  const handleClose = () => {
    setInstallUrl('');
    setBackupUrl('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Install Extension</DialogTitle>
          <DialogDescription>
            Install a new extension from a GitHub/Gitee repository or upload a ZIP file.
          </DialogDescription>
        </DialogHeader>

        <div className="flex space-x-1 rounded-lg bg-muted p-1 mb-4">
          <button
            type="button"
            onClick={() => setActiveTab('url')}
            className={`flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === 'url' ? 'bg-background shadow' : 'hover:bg-background/50'
            }`}
          >
            <Link2 className="h-4 w-4" />
            From URL
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === 'upload' ? 'bg-background shadow' : 'hover:bg-background/50'
            }`}
          >
            <Upload className="h-4 w-4" />
            Upload ZIP
          </button>
        </div>

        {activeTab === 'url' && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="repo-url" className="text-sm font-medium">
                Repository URL
              </label>
              <div className="relative">
                <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="repo-url"
                  type="url"
                  placeholder="https://github.com/user/repo"
                  value={installUrl}
                  onChange={(e) => setInstallUrl(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Supports GitHub and Gitee repositories
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="backup-url" className="text-sm font-medium">
                Backup Repository URL (optional)
              </label>
              <div className="relative">
                <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="backup-url"
                  type="url"
                  placeholder="https://gitee.com/user/repo"
                  value={backupUrl}
                  onChange={(e) => setBackupUrl(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading || !installUrl.trim()}>
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Installing...
                  </>
                ) : (
                  'Install'
                )}
              </Button>
            </DialogFooter>
          </form>
        )}

        {activeTab === 'upload' && (
          <div className="space-y-4">
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground mb-4">
                Drag and drop a ZIP file here, or click to browse
              </p>
              <input type="file" accept=".zip" className="hidden" id="zip-upload" />
              <Button variant="outline" asChild>
                <label htmlFor="zip-upload" className="cursor-pointer">
                  Browse Files
                </label>
              </Button>
            </div>
            <p className="text-xs text-muted-foreground text-center">
              ZIP files should contain index.html, index.js, or package.json at the root level.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
