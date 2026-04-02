//! Tauri IPC Bridge - Frontend API for Tauri commands

import { invoke } from '@tauri-apps/api/core';
import { listen, UnlistenFn } from '@tauri-apps/api/event';

// Types
export interface BackendStatus {
  running: boolean;
  port: number | null;
  pid: number | null;
}

export interface StartBackendResult {
  success: boolean;
  port: number;
  pid: number;
  message: string;
}

export interface BackendLog {
  message: string;
  level?: 'info' | 'warn' | 'error';
}

// Tauri API wrapper
export const tauriAPI = {
  // Backend management
  startBackend: (): Promise<StartBackendResult> => invoke('start_backend'),

  stopBackend: (): Promise<void> => invoke('stop_backend'),

  getBackendStatus: (): Promise<BackendStatus> => invoke('get_backend_status'),

  // Window management
  createVrmWindow: (): Promise<void> => invoke('create_vrm_window'),

  createScreenshotOverlay: (): Promise<void> => invoke('create_screenshot_overlay'),

  closeWindow: (label: string): Promise<void> => invoke('close_window', { label }),

  toggleFullscreen: (label: string): Promise<boolean> =>
    invoke('toggle_fullscreen', { label }),

  // Event listeners
  onBackendLog: (callback: (log: BackendLog) => void): Promise<UnlistenFn> => {
    return listen<{ message: string; level?: string }>('backend-log', (event) => {
      callback({
        message: event.payload.message,
        level: event.payload.level as BackendLog['level'],
      });
    });
  },

  onBackendStarted: (callback: () => void): Promise<UnlistenFn> => {
    return listen('backend-started', () => {
      callback();
    });
  },

  onBackendStopped: (callback: () => void): Promise<UnlistenFn> => {
    return listen('backend-stopped', () => {
      callback();
    });
  },
};

// Platform detection
export const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI__' in window;
};

// Get the current platform
export const getPlatform = (): 'macos' | 'windows' | 'linux' | 'unknown' => {
  if (!isTauri()) return 'unknown';

  // @ts-expect-error Tauri platform detection
  const platform = window.__TAURI__?.window?.currentWindow?.label;
  if (navigator.userAgent.includes('Mac')) return 'macos';
  if (navigator.userAgent.includes('Windows')) return 'windows';
  if (navigator.userAgent.includes('Linux')) return 'linux';
  return 'unknown';
};

export default tauriAPI;
