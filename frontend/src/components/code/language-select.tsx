'use client';

import React from 'react';
import { useCodeStore, Language } from '@/lib/stores/code-store';

const languages: { value: Language; label: string }[] = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'r', label: 'R' },
  { value: 'java', label: 'Java' },
  { value: 'bash', label: 'Bash' },
];

export function LanguageSelect() {
  const { language, setLanguage } = useCodeStore();

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="language-select" className="text-sm font-medium">
        Language
      </label>
      <select
        id="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value as Language)}
        className="h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {languages.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  );
}
