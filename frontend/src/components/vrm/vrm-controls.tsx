'use client';

import { useVRMStore, AVAILABLE_MODELS, BlendshapeName, AnimationType } from '@/lib/stores/vrm-store';

interface BlendshapeControlProps {
  name: BlendshapeName;
  label: string;
  value: number;
  onChange: (value: number) => void;
}

function BlendshapeControl({ name, label, value, onChange }: BlendshapeControlProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-foreground">{label}</span>
        <span className="text-muted-foreground">{Math.round(value * 100)}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
      />
    </div>
  );
}

interface ModelSelectorProps {
  selectedUrl: string | null;
  selectedName: string;
  onSelect: (url: string | null, name: string) => void;
}

function ModelSelector({ selectedUrl, selectedName, onSelect }: ModelSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">VRM Model</label>
      <div className="grid grid-cols-2 gap-2">
        {AVAILABLE_MODELS.map((model) => (
          <button
            key={model.name}
            onClick={() => onSelect(model.url, model.name)}
            className={`p-2 rounded-lg border text-sm transition-colors ${
              selectedUrl === model.url
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border bg-card hover:bg-muted'
            }`}
          >
            {model.name}
          </button>
        ))}
      </div>
      {selectedUrl && (
        <p className="text-xs text-muted-foreground truncate">
          Current: {selectedName}
        </p>
      )}
    </div>
  );
}

interface AnimationSelectorProps {
  selected: AnimationType;
  onSelect: (animation: AnimationType) => void;
}

function AnimationSelector({ selected, onSelect }: AnimationSelectorProps) {
  const animations: { type: AnimationType; label: string }[] = [
    { type: 'idle', label: 'Idle' },
    { type: 'wave', label: 'Wave' },
    { type: 'nod', label: 'Nod' },
    { type: 'shake', label: 'Shake' },
  ];

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">Animation</label>
      <div className="flex flex-wrap gap-2">
        {animations.map((anim) => (
          <button
            key={anim.type}
            onClick={() => onSelect(anim.type)}
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              selected === anim.type
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80 text-muted-foreground'
            }`}
          >
            {anim.label}
          </button>
        ))}
      </div>
    </div>
  );
}

interface BlendshapeControlsProps {
  blendshapes: Record<BlendshapeName, number>;
  onChange: (name: BlendshapeName, value: number) => void;
  onReset: () => void;
}

function BlendshapeControls({ blendshapes, onChange, onReset }: BlendshapeControlsProps) {
  const controlGroups = [
    {
      label: 'Expressions',
      items: [
        { name: 'neutral' as BlendshapeName, label: 'Neutral' },
        { name: 'happy' as BlendshapeName, label: 'Happy' },
        { name: 'angry' as BlendshapeName, label: 'Angry' },
        { name: 'sad' as BlendshapeName, label: 'Sad' },
        { name: 'surprised' as BlendshapeName, label: 'Surprised' },
        { name: 'mouthSmile' as BlendshapeName, label: 'Smile' },
        { name: 'mouthFrown' as BlendshapeName, label: 'Frown' },
      ],
    },
    {
      label: 'Eyes',
      items: [
        { name: 'blink' as BlendshapeName, label: 'Blink' },
        { name: 'blinkLeft' as BlendshapeName, label: 'Blink Left' },
        { name: 'blinkRight' as BlendshapeName, label: 'Blink Right' },
        { name: 'lookLeft' as BlendshapeName, label: 'Look Left' },
        { name: 'lookRight' as BlendshapeName, label: 'Look Right' },
        { name: 'lookUp' as BlendshapeName, label: 'Look Up' },
        { name: 'lookDown' as BlendshapeName, label: 'Look Down' },
      ],
    },
    {
      label: 'Brows',
      items: [
        { name: 'browDownLeft' as BlendshapeName, label: 'Brow Down Left' },
        { name: 'browDownRight' as BlendshapeName, label: 'Brow Down Right' },
        { name: 'browUpLeft' as BlendshapeName, label: 'Brow Up Left' },
        { name: 'browUpRight' as BlendshapeName, label: 'Brow Up Right' },
      ],
    },
    {
      label: 'Mouth',
      items: [
        { name: 'jawOpen' as BlendshapeName, label: 'Jaw Open' },
      ],
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">Blendshapes</label>
        <button
          onClick={onReset}
          className="text-xs text-primary hover:underline"
        >
          Reset All
        </button>
      </div>

      {controlGroups.map((group) => (
        <div key={group.label} className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {group.label}
          </h4>
          <div className="grid gap-2">
            {group.items.map((item) => (
              <BlendshapeControl
                key={item.name}
                name={item.name}
                label={item.label}
                value={blendshapes[item.name]}
                onChange={(value) => onChange(item.name, value)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function VRMControls() {
  const {
    currentModelUrl,
    currentModelName,
    blendshapes,
    currentAnimation,
    setModel,
    setBlendshape,
    resetBlendshapes,
    setAnimation,
  } = useVRMStore();

  return (
    <div className="space-y-6">
      <ModelSelector
        selectedUrl={currentModelUrl}
        selectedName={currentModelName}
        onSelect={setModel}
      />

      <AnimationSelector
        selected={currentAnimation}
        onSelect={setAnimation}
      />

      <BlendshapeControls
        blendshapes={blendshapes}
        onChange={setBlendshape}
        onReset={resetBlendshapes}
      />
    </div>
  );
}
