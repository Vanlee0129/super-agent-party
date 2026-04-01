'use client';

import React from 'react';
import { Settings as SettingsIcon } from 'lucide-react';
import { GeneralSettings } from '@/components/settings/general-settings';
import { ModelConfig } from '@/components/settings/model-config';
import { ProxyConfig } from '@/components/settings/proxy-config';
import { ApiEndpoints } from '@/components/settings/api-endpoints';

export default function SettingsPage() {
  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center gap-3">
        <SettingsIcon className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure your application preferences</p>
        </div>
      </div>

      <div className="space-y-6">
        <section>
          <GeneralSettings />
        </section>

        <section>
          <ModelConfig />
        </section>

        <section>
          <ProxyConfig />
        </section>

        <section>
          <ApiEndpoints />
        </section>
      </div>
    </div>
  );
}
