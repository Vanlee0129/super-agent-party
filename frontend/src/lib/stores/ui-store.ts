import { create } from 'zustand';
import { ConnectionStatus } from '@/lib/api/websocket';

export interface UIState {
  sidebarOpen: boolean;
  activeMenu: string;
  connectionStatus: ConnectionStatus;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveMenu: (menu: string) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  activeMenu: 'home',
  connectionStatus: 'disconnected',
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveMenu: (menu) => set({ activeMenu: menu }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
