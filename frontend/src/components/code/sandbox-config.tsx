'use client';

import React from 'react';
import { useCodeStore, SandboxType } from '@/lib/stores/code-store';

export function SandboxConfig() {
  const { sandboxType, setSandboxType, e2bApiKey, setE2bApiKey } = useCodeStore();

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium">Sandbox</label>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="sandbox-type"
              value="local"
              checked={sandboxType === 'local'}
              onChange={() => setSandboxType('local')}
              className="accent-primary"
            />
            <span className="text-sm">Local</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="sandbox-type"
              value="e2b"
              checked={sandboxType === 'e2b'}
              onChange={() => setSandboxType('e2b')}
              className="accent-primary"
            />
            <span className="text-sm">E2B Cloud</span>
          </label>
        </div>
      </div>

      {sandboxType === 'e2b' && (
        <div className="space-y-1">
          <label htmlFor="e2b-api-key" className="text-sm font-medium">
            E2B API Key
          </label>
          <input
            id="e2b-api-key"
            type="password"
            value={e2bApiKey}
            onChange={(e) => setE2bApiKey(e.target.value)}
            placeholder="Enter your E2B API key"
            className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      )}
    </div>
  );
}
