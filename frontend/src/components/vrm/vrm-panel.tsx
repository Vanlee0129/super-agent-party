'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { VRMViewer } from './vrm-viewer';
import { VRMControls } from './vrm-controls';
import { useVRMStore } from '@/lib/stores/vrm-store';

export function VRMPanel() {
  const { error, isLoading } = useVRMStore();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* 3D Viewer */}
      <div className="lg:col-span-2 h-[500px] lg:h-[600px]">
        <Card className="h-full">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">VRM Viewer</CardTitle>
          </CardHeader>
          <CardContent className="p-0 h-[calc(100%-60px)]">
            <div className="relative w-full h-full">
              <VRMViewer />
              {isLoading && (
                <div className="absolute inset-0 bg-background/50 flex items-center justify-center">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm text-muted-foreground">Loading model...</span>
                  </div>
                </div>
              )}
              {error && (
                <div className="absolute bottom-4 left-4 right-4 bg-destructive/90 text-destructive-foreground p-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls Panel */}
      <div className="lg:col-span-1">
        <Card className="h-full">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">VRM Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <VRMControls />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
