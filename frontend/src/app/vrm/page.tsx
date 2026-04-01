'use client';

import { VRMPanel } from '@/components/vrm/vrm-panel';

export default function VRMPage() {
  return (
    <main className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">VRM 3D Avatar</h1>
        <p className="text-muted-foreground mt-2">
          View and customize 3D VRM avatars with expressions and animations
        </p>
      </div>
      <VRMPanel />
    </main>
  );
}
