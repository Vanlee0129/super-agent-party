'use client';

import React from 'react';
import Editor from '@monaco-editor/react';
import { useCodeStore } from '@/lib/stores/code-store';

const languageMap: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  r: 'r',
  java: 'java',
  bash: 'shell',
};

export function CodeEditor() {
  const { code, setCode, language } = useCodeStore();

  const handleEditorChange = (value: string | undefined) => {
    setCode(value || '');
  };

  return (
    <div className="h-full w-full border rounded-md overflow-hidden">
      <Editor
        height="100%"
        language={languageMap[language] || 'python'}
        value={code}
        onChange={handleEditorChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          wordWrap: 'on',
          padding: { top: 8 },
        }}
      />
    </div>
  );
}
