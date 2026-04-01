'use client';

import React from 'react';
import { useCodeStore } from '@/lib/stores/code-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function OutputPanel() {
  const { output, isExecuting, clearOutput } = useCodeStore();

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Output</CardTitle>
          {output && (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {output.executionTime.toFixed(2)}ms
              </Badge>
              {output.error && (
                <Badge variant="destructive" className="text-xs">
                  Error
                </Badge>
              )}
              <button
                onClick={clearOutput}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        {isExecuting ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
            <span className="text-sm">Executing...</span>
          </div>
        ) : output ? (
          <div className="space-y-3">
            {output.stdout && (
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">stdout</div>
                <pre className="text-sm bg-muted/50 p-2 rounded whitespace-pre-wrap break-words">
                  {output.stdout}
                </pre>
              </div>
            )}
            {output.stderr && (
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">stderr</div>
                <pre className="text-sm bg-destructive/10 text-destructive p-2 rounded whitespace-pre-wrap break-words">
                  {output.stderr}
                </pre>
              </div>
            )}
            {output.error && (
              <div>
                <div className="text-xs font-medium text-destructive mb-1">Error</div>
                <pre className="text-sm bg-destructive/10 text-destructive p-2 rounded whitespace-pre-wrap break-words">
                  {output.error}
                </pre>
              </div>
            )}
            {!output.stdout && !output.stderr && !output.error && (
              <div className="text-sm text-muted-foreground">No output</div>
            )}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">
            Run code to see output here
          </div>
        )}
      </CardContent>
    </Card>
  );
}
