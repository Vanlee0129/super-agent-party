'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Environment, Center } from '@react-three/drei';
import * as THREE from 'three';
import { VRM, VRMLoaderPlugin } from '@pixiv/three-vrm';
import { useVRMStore, BlendshapeName, AnimationType } from '@/lib/stores/vrm-store';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GLTFLoaderType = any;

interface VRMModelProps {
  url: string;
  blendshapes: Record<BlendshapeName, number>;
  animation: AnimationType;
  onLoaded: () => void;
  onError: (error: string) => void;
}

function VRMModel({ url, blendshapes, animation, onLoaded, onError }: VRMModelProps) {
  const vrmRef = useRef<VRM | null>(null);
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);
  const { scene } = useThree();

  useEffect(() => {
    let mounted = true;

    const loadVRM = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch VRM model');
        const buffer = await response.arrayBuffer();

        // Dynamic import to avoid TypeScript module resolution issues
        // @ts-ignore - three/examples/jsm doesn't have type declarations
        const GLTFLoader = (await import('three/examples/jsm/loaders/GLTFLoader')).GLTFLoader;
        const gltfLoader = new GLTFLoader();
        gltfLoader.register((parser: any) => new VRMLoaderPlugin(parser));

        gltfLoader.parse(
          buffer,
          '',
          (gltf: { scene: THREE.Scene; userData: { vrm?: VRM } }) => {
            gltf.scene.traverse((obj: THREE.Object3D) => {
              obj.castShadow = true;
              obj.receiveShadow = true;
            });

            const vrm = gltf.userData.vrm;
            if (vrm) {
              vrmRef.current = vrm;
              scene.add(vrm.scene);

              // Setup mixer for animations
              mixerRef.current = new THREE.AnimationMixer(vrm.scene);
              onLoaded();
            }
          },
          (error: GLTFLoaderType) => {
            if (mounted) {
              onError(error instanceof Error ? error.message : 'Failed to load VRM');
            }
          }
        );
      } catch (err) {
        if (mounted) {
          onError(err instanceof Error ? err.message : 'Failed to load VRM');
        }
      }
    };

    loadVRM();

    return () => {
      mounted = false;
      if (vrmRef.current) {
        scene.remove(vrmRef.current.scene);
        vrmRef.current = null;
      }
      if (mixerRef.current) {
        mixerRef.current.stopAllAction();
        mixerRef.current = null;
      }
    };
  }, [url, scene, onLoaded, onError]);

  // Update blendshapes
  useEffect(() => {
    const vrm = vrmRef.current;
    if (!vrm) return;

    const expressionManager = vrm.expressionManager;
    if (!expressionManager) return;

    const blendshapeMap: Record<BlendshapeName, string> = {
      neutral: 'neutral',
      happy: 'happy',
      angry: 'angry',
      sad: 'sad',
      surprised: 'surprised',
      blink: 'blink',
      blinkLeft: 'blinkLeft',
      blinkRight: 'blinkRight',
      lookLeft: 'lookLeft',
      lookRight: 'lookRight',
      lookUp: 'lookUp',
      lookDown: 'lookDown',
      browDownLeft: 'browDownLeft',
      browDownRight: 'browDownRight',
      browUpLeft: 'browUpLeft',
      browUpRight: 'browUpRight',
      jawOpen: 'jawOpen',
      mouthSmile: 'smile',
      mouthFrown: 'mouthFrown',
    };

    (Object.keys(blendshapes) as BlendshapeName[]).forEach((name) => {
      const vrmName = blendshapeMap[name];
      if (vrmName) {
        expressionManager.setValue(vrmName, blendshapes[name]);
      }
    });
  }, [blendshapes]);

  // Handle idle animation
  useFrame((state, delta) => {
    if (!vrmRef.current) return;

    const vrm = vrmRef.current;

    // Apply idle animation (subtle breathing/bobbing)
    if (animation === 'idle') {
      const time = state.clock.getElapsedTime();
      vrm.scene.position.y = Math.sin(time * 0.5) * 0.01;
      vrm.scene.rotation.y = Math.sin(time * 0.3) * 0.02;
    }

    // Update mixer
    if (mixerRef.current) {
      mixerRef.current.update(delta);
    }

    // Update VRM
    vrm.update(delta);
  });

  return null;
}

interface IdleAnimationProps {
  animation: AnimationType;
}

function IdleAnimation({ animation }: IdleAnimationProps) {
  return null;
}

interface VRMViewerContentProps {
  modelUrl: string | null;
  blendshapes: Record<BlendshapeName, number>;
  animation: AnimationType;
  onLoaded: () => void;
  onError: (error: string) => void;
}

function VRMViewerContent({
  modelUrl,
  blendshapes,
  animation,
  onLoaded,
  onError,
}: VRMViewerContentProps) {
  if (!modelUrl) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="#888888" wireframe />
      </mesh>
    );
  }

  return (
    <>
      <VRMModel
        url={modelUrl}
        blendshapes={blendshapes}
        animation={animation}
        onLoaded={onLoaded}
        onError={onError}
      />
      <Center>
        <mesh position={[0, -0.5, 0]} receiveShadow>
          <planeGeometry args={[5, 5]} />
          <shadowMaterial opacity={0.2} />
        </mesh>
      </Center>
    </>
  );
}

export function VRMViewer() {
  const [isClient, setIsClient] = useState(false);
  const { currentModelUrl, blendshapes, currentAnimation, setLoading, setError } = useVRMStore();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleLoaded = useCallback(() => {
    setLoading(false);
  }, [setLoading]);

  const handleError = useCallback(
    (error: string) => {
      setLoading(false);
      setError(error);
    },
    [setLoading, setError]
  );

  if (!isClient) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-muted">
        <p className="text-muted-foreground">Loading 3D viewer...</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-gradient-to-b from-gray-900 to-gray-800 rounded-lg overflow-hidden">
      <Canvas
        camera={{ position: [0, 1.5, 3], fov: 45 }}
        shadows
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[5, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />
        <pointLight position={[-5, 5, -5]} intensity={0.5} />
        <spotLight
          position={[0, 10, 0]}
          angle={0.3}
          penumbra={1}
          intensity={0.5}
          castShadow
        />

        <VRMViewerContent
          modelUrl={currentModelUrl}
          blendshapes={blendshapes}
          animation={currentAnimation}
          onLoaded={handleLoaded}
          onError={handleError}
        />

        <Environment preset="studio" />
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={1}
          maxDistance={10}
          target={[0, 1, 0]}
        />
      </Canvas>

      {!currentModelUrl && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-white/50 text-lg">Select a VRM model to display</p>
        </div>
      )}
    </div>
  );
}
