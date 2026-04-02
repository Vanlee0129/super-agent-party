"""VRM Animation system for controlling avatar movements and expressions."""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AnimationType(Enum):
    """Available animation types."""
    IDLE = "idle"
    WAVE = "wave"
    NOD = "nod"
    SHAKE = "shake"
    POINT = "point"
    THUMBS_UP = "thumbs_up"
    CLAP = "clap"
    BOW = "bow"


@dataclass
class AnimationKeyframe:
    """Single keyframe in an animation."""
    time: float  # Seconds from animation start
    bone: str  # Target bone name
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    blendshapes: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnimationSequence:
    """A complete animation sequence."""
    name: str
    duration: float  # Total duration in seconds
    keyframes: List[AnimationKeyframe] = field(default_factory=list)
    loop: bool = False


@dataclass
class AnimationState:
    """Current state of an animation."""
    animation_id: str
    sequence_name: str
    start_time: float
    current_time: float = 0.0
    is_playing: bool = False
    is_paused: bool = False


class VRMAnimation:
    """VRM animation data and keyframes."""

    # Pre-defined animation sequences
    ANIMATION_PRESETS: Dict[str, "VRMAnimation"] = {}

    def __init__(self, name: str, duration: float, loop: bool = False):
        self.name = name
        self.duration = duration
        self.loop = loop
        self.keyframes: List[AnimationKeyframe] = []

    def add_keyframe(
        self,
        time: float,
        bone: str,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        blendshapes: Optional[Dict[str, float]] = None
    ) -> "VRMAnimation":
        """Add a keyframe to this animation."""
        self.keyframes.append(AnimationKeyframe(
            time=time,
            bone=bone,
            position=position,
            rotation=rotation,
            blendshapes=blendshapes or {}
        ))
        return self

    @classmethod
    def create_idle(cls) -> "VRMAnimation":
        """Create idle breathing/bobbing animation."""
        anim = cls(name="idle", duration=4.0, loop=True)
        # Subtle breathing
        anim.add_keyframe(0.0, "Joints", blendshapes={"neutral": 1.0})
        anim.add_keyframe(2.0, "Joints", blendshapes={"neutral": 0.8})
        anim.add_keyframe(4.0, "Joints", blendshapes={"neutral": 1.0})
        return anim

    @classmethod
    def create_wave(cls) -> "VRMAnimation":
        """Create wave gesture animation."""
        anim = cls(name="wave", duration=1.5, loop=False)
        # Right hand wave
        anim.add_keyframe(0.0, "RightHand", position=(0.3, 1.2, 0.2), rotation=(0, 0, 0, 1))
        anim.add_keyframe(0.3, "RightHand", position=(0.3, 1.3, 0.2), rotation=(0, 0.3, 0, 0.95))
        anim.add_keyframe(0.6, "RightHand", position=(0.3, 1.25, 0.2), rotation=(0, 0, 0, 1))
        anim.add_keyframe(0.9, "RightHand", position=(0.3, 1.3, 0.2), rotation=(0, -0.3, 0, 0.95))
        anim.add_keyframe(1.2, "RightHand", position=(0.3, 1.2, 0.2), rotation=(0, 0, 0, 1))
        return anim

    @classmethod
    def create_nod(cls) -> "VRMAnimation":
        """Create head nod animation."""
        anim = cls(name="nod", duration=1.0, loop=False)
        anim.add_keyframe(0.0, "Head", rotation=(0, 0, 0, 1))
        anim.add_keyframe(0.25, "Head", rotation=(0.1, 0, 0, 1))
        anim.add_keyframe(0.5, "Head", rotation=(-0.05, 0, 0, 1))
        anim.add_keyframe(0.75, "Head", rotation=(0.05, 0, 0, 1))
        anim.add_keyframe(1.0, "Head", rotation=(0, 0, 0, 1))
        return anim

    @classmethod
    def create_shake(cls) -> "VRMAnimation":
        """Create head shake animation."""
        anim = cls(name="shake", duration=1.0, loop=False)
        anim.add_keyframe(0.0, "Head", rotation=(0, 0, 0, 1))
        anim.add_keyframe(0.2, "Head", rotation=(0, 0.2, 0, 1))
        anim.add_keyframe(0.4, "Head", rotation=(0, -0.2, 0, 1))
        anim.add_keyframe(0.6, "Head", rotation=(0, 0.15, 0, 1))
        anim.add_keyframe(0.8, "Head", rotation=(0, -0.1, 0, 1))
        anim.add_keyframe(1.0, "Head", rotation=(0, 0, 0, 1))
        return anim


class AnimationController:
    """Controls VRM animations and maintains current pose state."""

    def __init__(self):
        self._animations: Dict[str, VRMAnimation] = {}
        self._current_pose: Dict[str, Dict[str, Any]] = {}
        self._active_animations: Dict[str, AnimationState] = {}
        self._blendshapes: Dict[str, float] = {}
        self._listeners: List[Callable] = []

        # Register default animations
        self._register_default_animations()

    def _register_default_animations(self) -> None:
        """Register preset animations."""
        presets = [
            VRMAnimation.create_idle(),
            VRMAnimation.create_wave(),
            VRMAnimation.create_nod(),
            VRMAnimation.create_shake(),
        ]
        for anim in presets:
            self._animations[anim.name] = anim

    def register_animation(self, animation: VRMAnimation) -> None:
        """Register a custom animation."""
        self._animations[animation.name] = animation
        logger.info(f"Registered animation: {animation.name}")

    def get_animation(self, name: str) -> Optional[VRMAnimation]:
        """Get an animation by name."""
        return self._animations.get(name)

    def list_animations(self) -> List[str]:
        """List all available animation names."""
        return list(self._animations.keys())

    def set_bone(self, bone_name: str, transform: Dict[str, Any]) -> None:
        """Set bone transform data."""
        if bone_name not in self._current_pose:
            self._current_pose[bone_name] = {}

        self._current_pose[bone_name].update({
            "position": transform.get("position", (0, 0, 0)),
            "rotation": transform.get("rotation", (0, 0, 0, 1)),
            "updated_at": time.time(),
        })

        self._notify_listeners()

    def set_blendshape(self, name: str, weight: float) -> None:
        """Set blend shape weight."""
        self._blendshapes[name] = max(0.0, min(1.0, weight))
        self._notify_listeners()

    def get_pose(self) -> Dict[str, Dict[str, Any]]:
        """Get current pose state."""
        return self._current_pose.copy()

    def get_blendshapes(self) -> Dict[str, float]:
        """Get current blend shape weights."""
        return self._blendshapes.copy()

    async def trigger_animation(
        self,
        animation_name: str,
        vrm_id: Optional[str] = None,
        on_complete: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Trigger an animation.

        Args:
            animation_name: Name of the animation to play
            vrm_id: Optional VRM identifier (for multi-avatar support)
            on_complete: Optional callback when animation completes

        Returns:
            Animation ID if started, None if animation not found
        """
        animation = self._animations.get(animation_name)
        if not animation:
            logger.warning(f"Animation not found: {animation_name}")
            return None

        animation_id = str(uuid.uuid4())
        state = AnimationState(
            animation_id=animation_id,
            sequence_name=animation_name,
            start_time=time.time(),
            is_playing=True,
        )
        self._active_animations[animation_id] = state

        # Run animation task
        asyncio.create_task(
            self._run_animation(animation_id, animation, on_complete)
        )

        logger.info(f"Started animation {animation_name} (ID: {animation_id})")
        return animation_id

    async def _run_animation(
        self,
        animation_id: str,
        animation: VRMAnimation,
        on_complete: Optional[Callable]
    ) -> None:
        """Run an animation sequence."""
        state = self._active_animations.get(animation_id)
        if not state:
            return

        start_time = time.time()

        try:
            while state.is_playing and not state.is_paused:
                elapsed = time.time() - start_time

                if elapsed >= animation.duration:
                    if animation.loop:
                        start_time = time.time()
                        elapsed = 0
                    else:
                        break

                # Interpolate keyframes and apply
                self._apply_animation_frame(animation, elapsed)

                await asyncio.sleep(1/30)  # ~30 FPS

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error running animation {animation.name}: {e}")
        finally:
            if animation_id in self._active_animations:
                del self._active_animations[animation_id]

            if on_complete:
                try:
                    on_complete()
                except Exception as e:
                    logger.error(f"Error in animation complete callback: {e}")

    def _apply_animation_frame(self, animation: VRMAnimation, time: float) -> None:
        """Apply animation frame at given time."""
        # Find surrounding keyframes for each bone
        bone_keyframes: Dict[str, List[AnimationKeyframe]] = {}
        for kf in animation.keyframes:
            if kf.bone not in bone_keyframes:
                bone_keyframes[kf.bone] = []
            bone_keyframes[kf.bone].append(kf)

        # Interpolate each bone
        for bone, keyframes in bone_keyframes.items():
            keyframes.sort(key=lambda k: k.time)

            # Find interpolation range
            before: Optional[AnimationKeyframe] = None
            after: Optional[AnimationKeyframe] = None

            for kf in keyframes:
                if kf.time <= time:
                    before = kf
                if kf.time >= time and after is None:
                    after = kf

            if before and after and before != after:
                # Linear interpolation
                t = (time - before.time) / (after.time - before.time)
                pos = self._lerp_position(before.position, after.position, t)
                rot = self._slerp_rotation(before.rotation, after.rotation, t)

                self._current_pose[bone] = {
                    "position": pos,
                    "rotation": rot,
                    "updated_at": time.time(),
                }

                # Merge blendshapes
                for name, weight in after.blendshapes.items():
                    self._blendshapes[name] = weight
            elif before:
                self._current_pose[bone] = {
                    "position": before.position,
                    "rotation": before.rotation,
                    "updated_at": time.time(),
                }

        self._notify_listeners()

    def _lerp_position(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        t: float
    ) -> tuple[float, float, float]:
        """Linear interpolation between two positions."""
        return (
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t,
        )

    def _slerp_rotation(
        self,
        a: tuple[float, float, float, float],
        b: tuple[float, float, float, float],
        t: float
    ) -> tuple[float, float, float, float]:
        """Spherical linear interpolation between two quaternions."""
        # Simple linear interpolation (not true Slerp but close enough for animations)
        return (
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t,
            a[3] + (b[3] - a[3]) * t,
        )

    def pause_animation(self, animation_id: str) -> None:
        """Pause a playing animation."""
        if animation_id in self._active_animations:
            self._active_animations[animation_id].is_paused = True

    def resume_animation(self, animation_id: str) -> None:
        """Resume a paused animation."""
        if animation_id in self._active_animations:
            self._active_animations[animation_id].is_paused = False

    def stop_animation(self, animation_id: str) -> None:
        """Stop a playing animation."""
        if animation_id in self._active_animations:
            self._active_animations[animation_id].is_playing = False

    def stop_all_animations(self) -> None:
        """Stop all playing animations."""
        for state in self._active_animations.values():
            state.is_playing = False

    def add_listener(self, listener: Callable) -> None:
        """Add a listener for pose changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable) -> None:
        """Remove a pose change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of pose change."""
        for listener in self._listeners:
            try:
                listener(self._current_pose.copy(), self._blendshapes.copy())
            except Exception as e:
                logger.error(f"Error notifying animation listener: {e}")
