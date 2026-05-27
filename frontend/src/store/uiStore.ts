import { create } from 'zustand';

type UiState = {
  workspaceId: string;
  setWorkspaceId: (value: string) => void;
};

export const useUiStore = create<UiState>((set) => ({
  workspaceId: '1',
  setWorkspaceId: (value) => set({ workspaceId: value }),
}));
