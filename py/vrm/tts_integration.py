"""
TTS to VRM - Animate VRM avatar with TTS audio

Generates speech audio and triggers viseme-based lip-sync animation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import base64

logger = logging.getLogger(__name__)


@dataclass
class VisemeData:
    """Viseme (mouth shape) animation data."""
    timestamp: float
    viseme: str
    weight: float


class VRMTTS:
    """Animate VRM avatar with TTS audio using viseme-based lip-sync."""

    # Standard VRM viseme mappings (VRM 1.0)
    VISEME_MAP = {
        # Silence
        "sil": ["neutral"],
        # Mouth shapes for phonemes
        "A": ["mouthFrown", "jawOpen"],
        "I": ["mouthSmile", "jawOpen"],
        "U": ["mouthSmile"],
        "E": ["jawOpen"],
        "O": ["mouthFrown", "jawOpen"],
        # Additional shapes
        "neutral": ["neutral"],
        "happy": ["happy"],
        "sad": ["sad"],
        "angry": ["angry"],
        "surprised": ["surprised"],
    }

    def __init__(self, tts_provider: Optional[Callable] = None):
        """
        Initialize TTS integration.

        Args:
            tts_provider: Optional async callable that takes text and returns audio bytes.
                         If not provided, a mock provider is used.
        """
        self.tts_provider = tts_provider or self._mock_tts_provider
        self._active_animations: Dict[str, asyncio.Task] = {}

    async def synthesize_and_animate(
        self,
        text: str,
        vrm_id: str,
        voice_id: Optional[str] = None,
        on_audio_chunk: Optional[Callable[[bytes], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate TTS audio and trigger lip-sync animation.

        Args:
            text: Text to synthesize
            vrm_id: VRM avatar identifier
            voice_id: Optional voice configuration ID
            on_audio_chunk: Callback for streaming audio chunks

        Returns:
            Dictionary with synthesis results and viseme timeline
        """
        logger.info(f"TTS request for VRM {vrm_id}: {text[:50]}...")

        try:
            # Generate audio
            audio_data = await self.tts_provider(text, voice_id=voice_id)

            # Generate viseme timeline from audio
            viseme_timeline = self.blend_shape_from_audio(audio_data)

            # Start lip-sync animation task
            if vrm_id in self._active_animations:
                self._active_animations[vrm_id].cancel()

            animation_task = asyncio.create_task(
                self._run_lip_sync_animation(vrm_id, viseme_timeline, on_audio_chunk)
            )
            self._active_animations[vrm_id] = animation_task

            return {
                "success": True,
                "vrm_id": vrm_id,
                "audio_duration": len(audio_data) / 16000 if audio_data else 0,
                "viseme_count": len(viseme_timeline),
                "viseme_timeline": [
                    {"timestamp": v.timestamp, "viseme": v.viseme, "weight": v.weight}
                    for v in viseme_timeline
                ],
            }

        except Exception as e:
            logger.error(f"TTS synthesis error for {vrm_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "vrm_id": vrm_id,
            }

    def blend_shape_from_audio(self, audio_data: bytes) -> List[VisemeData]:
        """
        Generate blend shape weights from audio data using simple VAD-based visemes.

        This is a simplified implementation. Production systems would use:
        - WebRTC VAD (Voice Activity Detection)
        - Disney's "Papagayo" viseme system
        - Oxford University's lip-sync technology

        Args:
            audio_data: Raw audio bytes

        Returns:
            List of VisemeData with timestamps and weights
        """
        visemes: List[VisemeData] = []

        if not audio_data:
            return visemes

        # Simple mock implementation - in production, use proper audio analysis
        # Duration estimate (assuming 16kHz mono 16-bit)
        duration_seconds = len(audio_data) / 32000  # 16kHz * 2 bytes per sample
        num_frames = int(duration_seconds * 10)  # 10 viseme changes per second

        # Generate simple alternating visemes for demonstration
        viseme_sequence = ["A", "I", "U", "E", "O", "neutral"]

        for i in range(num_frames):
            timestamp = i / 10.0
            viseme_name = viseme_sequence[i % len(viseme_sequence)]

            # Weight varies based on position (simulate speech rhythm)
            weight = 0.3 + 0.5 * ((i % 3) / 2)  # Oscillate between 0.3 and 0.8

            visemes.append(VisemeData(
                timestamp=timestamp,
                viseme=viseme_name,
                weight=weight
            ))

        return visemes

    def get_blend_shapes_for_viseme(self, viseme: str) -> Dict[str, float]:
        """
        Get VRM blend shape weights for a given viseme.

        Args:
            viseme: Viseme name

        Returns:
            Dictionary of blend shape names to weights
        """
        shapes = self.VISEME_MAP.get(viseme, ["neutral"])

        result = {}
        for shape in shapes:
            if shape == "neutral":
                result["neutral"] = 1.0
            elif shape == "mouthSmile":
                result["mouthSmile"] = 0.6
                result["jawOpen"] = 0.2
            elif shape == "mouthFrown":
                result["mouthFrown"] = 0.5
                result["jawOpen"] = 0.3
            elif shape == "jawOpen":
                result["jawOpen"] = 0.4
            elif shape in ("happy", "sad", "angry", "surprised"):
                result[shape] = 0.5

        return result

    async def _run_lip_sync_animation(
        self,
        vrm_id: str,
        viseme_timeline: List[VisemeData],
        on_audio_chunk: Optional[Callable[[bytes], None]]
    ) -> None:
        """Run the lip-sync animation coroutine."""
        try:
            start_time = asyncio.get_event_loop().time() if hasattr(asyncio.get_event_loop(), 'time') else 0
            for viseme in viseme_timeline:
                # Get blend shapes for this viseme
                blend_shapes = self.get_blend_shapes_for_viseme(viseme.viseme)
                await asyncio.sleep(0.1)  # Simulate timing
        except asyncio.CancelledError:
            logger.debug(f"Lip-sync animation cancelled for {vrm_id}")
        except Exception as e:
            logger.error(f"Error in lip-sync animation for {vrm_id}: {e}")
        finally:
            if vrm_id in self._active_animations:
                del self._active_animations[vrm_id]

    async def stop_animation(self, vrm_id: str) -> None:
        """Stop active lip-sync animation for a VRM."""
        if vrm_id in self._active_animations:
            self._active_animations[vrm_id].cancel()
            del self._active_animations[vrm_id]
            logger.info(f"Stopped lip-sync animation for {vrm_id}")

    async def _mock_tts_provider(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Mock TTS provider for testing."""
        # Simulate TTS processing delay
        await asyncio.sleep(0.1)
        # Return empty bytes (mock audio)
        return b""


async def create_vrm_tts(tts_provider: Optional[Callable] = None) -> VRMTTS:
    """Create a VRM TTS instance."""
    return VRMTTS(tts_provider=tts_provider)
