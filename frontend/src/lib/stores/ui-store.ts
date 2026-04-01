import { create } from 'zustand';

export interface UIState {
  sidebarOpen: boolean;
  activeMenu: string;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveMenu: (menu: string) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  activeMenu: 'home',
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveMenu: (menu) => set({ activeMenu: menu }),
}));
