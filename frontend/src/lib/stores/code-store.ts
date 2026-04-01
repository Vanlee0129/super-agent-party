import { create } from 'zustand';

export type Language = 'python' | 'javascript' | 'typescript' | 'r' | 'java' | 'bash';
export type SandboxType = 'e2b' | 'local';

export interface ExecutionOutput {
  stdout: string;
  stderr: string;
  executionTime: number;
  error: string | null;
}

export interface CodeState {
  code: string;
  language: Language;
  sandboxType: SandboxType;
  e2bApiKey: string;
  isExecuting: boolean;
  output: ExecutionOutput | null;
  setCode: (code: string) => void;
  setLanguage: (language: Language) => void;
  setSandboxType: (sandboxType: SandboxType) => void;
  setE2bApiKey: (apiKey: string) => void;
  setIsExecuting: (isExecuting: boolean) => void;
  setOutput: (output: ExecutionOutput | null) => void;
  clearOutput: () => void;
  reset: () => void;
}

const initialState = {
  code: 'print("Hello, World!")',
  language: 'python' as Language,
  sandboxType: 'local' as SandboxType,
  e2bApiKey: '',
  isExecuting: false,
  output: null,
};

export const useCodeStore = create<CodeState>()((set) => ({
  ...initialState,
  setCode: (code) => set({ code }),
  setLanguage: (language) => set({ language }),
  setSandboxType: (sandboxType) => set({ sandboxType }),
  setE2bApiKey: (e2bApiKey) => set({ e2bApiKey }),
  setIsExecuting: (isExecuting) => set({ isExecuting }),
  setOutput: (output) => set({ output }),
  clearOutput: () => set({ output: null }),
  reset: () => set(initialState),
}));
