'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { useCodeStore } from '@/lib/stores/code-store';
import { OutputPanel } from '@/components/code/output-panel';
import { LanguageSelect } from '@/components/code/language-select';
import { SandboxConfig } from '@/components/code/sandbox-config';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { SkeletonCode } from '@/components/ui/skeleton';

const CodeEditor = dynamic(
  () => import('@/components/code/code-editor').then((mod) => mod.CodeEditor),
  {
    loading: () => <SkeletonCode />,
    ssr: false,
  }
);

export default function CodePage() {
  const {
    code,
    language,
    sandboxType,
    e2bApiKey,
    isExecuting,
    setIsExecuting,
    setOutput,
  } = useCodeStore();

  const handleRunCode = async () => {
    setIsExecuting(true);
    setOutput(null);

    const startTime = performance.now();

    try {
      const response = await fetch('/api/code/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          language,
          sandboxType,
          e2bApiKey: sandboxType === 'e2b' ? e2bApiKey : undefined,
        }),
      });

      const data = await response.json();
      const executionTime = performance.now() - startTime;

      setOutput({
        stdout: data.stdout || '',
        stderr: data.stderr || '',
        executionTime,
        error: data.error || null,
      });
    } catch (error) {
      const executionTime = performance.now() - startTime;
      setOutput({
        stdout: '',
        stderr: '',
        executionTime,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="container mx-auto p-4 h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Code Execution</h1>
        <div className="flex items-center gap-4">
          <LanguageSelect />
          <Button onClick={handleRunCode} disabled={isExecuting}>
            {isExecuting ? 'Running...' : 'Run Code'}
          </Button>
        </div>
      </div>

      <div className="mb-4">
        <SandboxConfig />
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        <Card className="flex flex-col min-h-[400px]">
          <CardContent className="flex-1 p-2">
            <CodeEditor />
          </CardContent>
        </Card>
        <OutputPanel />
      </div>
    </div>
  );
}
