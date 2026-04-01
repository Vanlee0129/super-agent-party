import { create } from 'zustand';

export interface Extension {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  systemPrompt: string;
  repository: string;
  backupRepository: string;
  category: string;
  transparent: boolean;
  width: number;
  height: number;
  enableVrmWindowSize: boolean;
  enabled?: boolean;
}

export interface TaskStatus {
  status: 'installing' | 'success' | 'error' | 'unknown';
  detail: string;
  progress: number;
  timestamp: number;
}

interface ExtensionsState {
  extensions: Extension[];
  selectedExtension: Extension | null;
  isDetailOpen: boolean;
  isInstallDialogOpen: boolean;
  isLoading: boolean;
  error: string | null;
  installTaskStatus: Record<string, TaskStatus>;

  fetchExtensions: () => Promise<void>;
  selectExtension: (extension: Extension | null) => void;
  openDetail: (extension: Extension) => void;
  closeDetail: () => void;
  openInstallDialog: () => void;
  closeInstallDialog: () => void;
  installFromUrl: (url: string, backupUrl?: string) => Promise<void>;
  deleteExtension: (extId: string) => Promise<void>;
  toggleExtension: (extId: string) => void;
  updateConfig: (extId: string, config: Record<string, unknown>) => Promise<void>;
  pollTaskStatus: (extId: string) => Promise<void>;
}

const API_BASE = '/api/extensions';

export const useExtensionsStore = create<ExtensionsState>((set, get) => ({
  extensions: [],
  selectedExtension: null,
  isDetailOpen: false,
  isInstallDialogOpen: false,
  isLoading: false,
  error: null,
  installTaskStatus: {},

  fetchExtensions: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/list`);
      if (!res.ok) throw new Error('Failed to fetch extensions');
      const data = await res.json();
      set({ extensions: data.extensions || [], isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  selectExtension: (extension) => set({ selectedExtension: extension }),

  openDetail: (extension) => set({ selectedExtension: extension, isDetailOpen: true }),

  closeDetail: () => set({ isDetailOpen: false, selectedExtension: null }),

  openInstallDialog: () => set({ isInstallDialogOpen: true }),

  closeInstallDialog: () => set({ isInstallDialogOpen: false }),

  installFromUrl: async (url: string, backupUrl?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/install-from-github`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, backupUrl: backupUrl || '' }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to install extension');
      }
      const data = await res.json();
      set({ installTaskStatus: { ...get().installTaskStatus, [data.ext_id]: { status: 'installing', detail: 'Starting...', progress: 0, timestamp: Date.now() } } });
      // Start polling
      get().pollTaskStatus(data.ext_id);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  deleteExtension: async (extId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/${extId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete extension');
      set((state) => ({
        extensions: state.extensions.filter((e) => e.id !== extId),
        isLoading: false,
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  toggleExtension: (extId: string) => {
    set((state) => ({
      extensions: state.extensions.map((e) =>
        e.id === extId ? { ...e, enabled: !e.enabled } : e
      ),
    }));
  },

  updateConfig: async (extId: string, config: Record<string, unknown>) => {
    try {
      const res = await fetch(`${API_BASE}/${extId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!res.ok) throw new Error('Failed to update config');
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  pollTaskStatus: async (extId: string) => {
    try {
      const res = await fetch(`${API_BASE}/task-status/${extId}`);
      if (!res.ok) return;
      const data: TaskStatus = await res.json();
      set((state) => ({
        installTaskStatus: { ...state.installTaskStatus, [extId]: data },
      }));
      if (data.status === 'installing') {
        setTimeout(() => get().pollTaskStatus(extId), 2000);
      } else if (data.status === 'success') {
        get().fetchExtensions();
        set({ isLoading: false });
      }
    } catch {
      // Silently fail on polling errors
    }
  },
}));
