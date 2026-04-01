'use client';

import React, { useEffect } from 'react';
import { useExtensionsStore } from '@/lib/stores/extensions-store';
import { ExtensionCard } from '@/components/extensions/extension-card';
import { ExtensionDetail } from '@/components/extensions/extension-detail';
import { InstallForm } from '@/components/extensions/install-form';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, RefreshCw, PackageOpen } from 'lucide-react';

export default function ExtensionsPage() {
  const {
    extensions,
    selectedExtension,
    isDetailOpen,
    isInstallDialogOpen,
    isLoading,
    error,
    fetchExtensions,
    openDetail,
    closeDetail,
    openInstallDialog,
    closeInstallDialog,
    deleteExtension,
    toggleExtension,
  } = useExtensionsStore();

  useEffect(() => {
    fetchExtensions();
  }, [fetchExtensions]);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Extensions</h1>
          <p className="text-muted-foreground mt-1">
            Manage your installed extensions and discover new ones
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={fetchExtensions} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button onClick={openInstallDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Install Extension
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-4 text-destructive">
            {error}
          </CardContent>
        </Card>
      )}

      {extensions.length === 0 && !isLoading ? (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center justify-center text-center">
            <PackageOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No extensions installed</h3>
            <p className="text-muted-foreground mb-4">
              Get started by installing your first extension
            </p>
            <Button onClick={openInstallDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Install Extension
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {extensions.map((extension) => (
            <ExtensionCard
              key={extension.id}
              extension={extension}
              onToggle={toggleExtension}
              onConfigure={openDetail}
              onDelete={deleteExtension}
            />
          ))}
        </div>
      )}

      <ExtensionDetail
        extension={selectedExtension}
        open={isDetailOpen}
        onOpenChange={(open) => {
          if (!open) closeDetail();
        }}
        onToggle={toggleExtension}
      />

      <InstallForm
        open={isInstallDialogOpen}
        onOpenChange={(open) => {
          if (!open) closeInstallDialog();
        }}
      />
    </div>
  );
}
