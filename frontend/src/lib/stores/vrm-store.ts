import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type BlendshapeName =
  | 'neutral'
  | 'happy'
  | 'angry'
  | 'sad'
  | 'surprised'
  | 'blink'
  | 'blinkLeft'
  | 'blinkRight'
  | 'lookLeft'
  | 'lookRight'
  | 'lookUp'
  | 'lookDown'
  | 'browDownLeft'
  | 'browDownRight'
  | 'browUpLeft'
  | 'browUpRight'
  | 'jawOpen'
  | 'mouthSmile'
  | 'mouthFrown';

export type AnimationType = 'idle' | 'wave' | 'nod' | 'shake';

export interface VRMState {
  currentModelUrl: string | null;
  currentModelName: string;
  blendshapes: Record<BlendshapeName, number>;
  currentAnimation: AnimationType;
  isLoading: boolean;
  error: string | null;
  setModel: (url: string | null, name: string) => void;
  setBlendshape: (name: BlendshapeName, value: number) => void;
  setAllBlendshapes: (blendshapes: Record<BlendshapeName, number>) => void;
  resetBlendshapes: () => void;
  setAnimation: (animation: AnimationType) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const defaultBlendshapes: Record<BlendshapeName, number> = {
  neutral: 1,
  happy: 0,
  angry: 0,
  sad: 0,
  surprised: 0,
  blink: 0,
  blinkLeft: 0,
  blinkRight: 0,
  lookLeft: 0,
  lookRight: 0,
  lookUp: 0,
  lookDown: 0,
  browDownLeft: 0,
  browDownRight: 0,
  browUpLeft: 0,
  browUpRight: 0,
  jawOpen: 0,
  mouthSmile: 0,
  mouthFrown: 0,
};

export const useVRMStore = create<VRMState>()(
  persist(
    (set) => ({
      currentModelUrl: null,
      currentModelName: '',
      blendshapes: { ...defaultBlendshapes },
      currentAnimation: 'idle',
      isLoading: false,
      error: null,

      setModel: (url, name) =>
        set({
          currentModelUrl: url,
          currentModelName: name,
          error: null,
        }),

      setBlendshape: (name, value) =>
        set((state) => ({
          blendshapes: {
            ...state.blendshapes,
            [name]: Math.max(0, Math.min(1, value)),
          },
        })),

      setAllBlendshapes: (blendshapes) =>
        set({ blendshapes }),

      resetBlendshapes: () =>
        set({ blendshapes: { ...defaultBlendshapes } }),

      setAnimation: (animation) =>
        set({ currentAnimation: animation }),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setError: (error) =>
        set({ error }),
    }),
    {
      name: 'vrm-storage',
      partialize: (state) => ({
        currentModelUrl: state.currentModelUrl,
        currentModelName: state.currentModelName,
        currentAnimation: state.currentAnimation,
      }),
    }
  )
);

// Available VRM models for demo
export const AVAILABLE_MODELS = [
  {
    name: 'Alicia Solid',
    url: 'https://pixi.chat/drei/alicia.vrm',
    thumbnail: 'https://pixi.chat/drei/alicia.png',
  },
  {
    name: 'VRM 1.0 Demo',
    url: 'https://pixi.chat/drei/VRM1_Constraint_Twist_Sample.vrm',
    thumbnail: null,
  },
] as const;
