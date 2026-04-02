"""VRM REST API endpoints."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from py.vrm.models import VRMModel, VRMModelManager, get_vrm_model_manager
from py.vrm.animation import AnimationController
from py.vrm.tts_integration import VRMTTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vrm", tags=["vrm"])

# Global instances - lazily initialized
_model_manager: Optional[VRMModelManager] = None
_animation_controller: Optional[AnimationController] = None
_vrm_tts: Optional[VRMTTS] = None


def get_model_manager() -> VRMModelManager:
    global _model_manager
    if _model_manager is None:
        _model_manager = get_vrm_model_manager()
    return _model_manager


def get_animation_controller() -> AnimationController:
    global _animation_controller
    if _animation_controller is None:
        _animation_controller = AnimationController()
    return _animation_controller


def get_vrm_tts() -> VRMTTS:
    global _vrm_tts
    if _vrm_tts is None:
        _vrm_tts = VRMTTS()
    return _vrm_tts


@router.post("/upload")
async def upload_vrm_model(
    file: UploadFile = File(...),
    metadata: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a new VRM model.

    Args:
        file: VRM model file (.vrm, .glb, .gltf)
        metadata: Optional JSON metadata string

    Returns:
        Upload result with model ID
    """
    manager = get_model_manager()

    # Parse metadata if provided
    meta = {}
    if metadata:
        import json
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = file.filename.lower().split('.')[-1]
    if ext not in ('vrm', 'glb', 'gltf'):
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .vrm, .glb, or .gltf")

    result = await manager.upload_model(file.file, file.filename, meta)

    if result.success:
        return {
            "success": True,
            "model_id": result.model_id,
            "file_path": result.file_path,
        }
    else:
        raise HTTPException(status_code=500, detail=result.error or "Upload failed")


@router.get("/models")
async def list_vrm_models() -> List[Dict[str, Any]]:
    """
    List all available VRM models.

    Returns:
        List of VRM model metadata
    """
    manager = get_model_manager()
    models = await manager.list_models()

    return [
        {
            "id": m.id,
            "name": m.name,
            "format": m.format.value,
            "thumbnail_url": m.thumbnail_url,
            "metadata": m.metadata,
            "created_at": m.created_at,
            "file_size": m.file_size,
            "url": m.url,
        }
        for m in models
    ]


@router.get("/models/{model_id}")
async def get_vrm_model(model_id: str) -> Dict[str, Any]:
    """
    Get VRM model details.

    Args:
        model_id: Model identifier

    Returns:
        Model metadata
    """
    manager = get_model_manager()
    model = await manager.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "id": model.id,
        "name": model.name,
        "format": model.format.value,
        "thumbnail_url": model.thumbnail_url,
        "metadata": model.metadata,
        "created_at": model.created_at,
        "file_size": model.file_size,
        "url": model.url,
        "exists": model.exists,
    }


@router.get("/models/{model_id}/file")
async def download_vrm_model(model_id: str) -> Response:
    """
    Download VRM model file.

    Args:
        model_id: Model identifier

    Returns:
        VRM model file bytes
    """
    manager = get_model_manager()
    model = await manager.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    data = await manager.get_model_file(model_id)
    if not data:
        raise HTTPException(status_code=404, detail="Model file not found")

    ext = model.file_path.split('.')[-1].lower()
    media_type = {
        "vrm": "model/gltf-binary",
        "glb": "model/gltf-binary",
        "gltf": "model/gltf+json",
    }.get(ext, "application/octet-stream")

    return Response(content=data, media_type=media_type)


@router.delete("/models/{model_id}")
async def delete_vrm_model(model_id: str) -> Dict[str, Any]:
    """
    Delete a VRM model.

    Args:
        model_id: Model identifier

    Returns:
        Deletion result
    """
    manager = get_model_manager()
    success = await manager.delete_model(model_id)

    if success:
        return {"success": True, "deleted": model_id}
    else:
        raise HTTPException(status_code=404, detail="Model not found")


@router.post("/animations")
async def trigger_animation(
    animation: str,
    vrm_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger an animation on a VRM avatar.

    Args:
        animation: Animation name (idle, wave, nod, shake)
        vrm_id: Optional VRM model ID

    Returns:
        Animation trigger result
    """
    controller = get_animation_controller()

    animation_id = await controller.trigger_animation(animation, vrm_id)

    if animation_id:
        return {
            "success": True,
            "animation_id": animation_id,
            "animation": animation,
            "vrm_id": vrm_id,
        }
    else:
        raise HTTPException(status_code=400, detail=f"Animation not found: {animation}")


@router.get("/animations")
async def list_animations() -> List[str]:
    """
    List available animations.

    Returns:
        List of animation names
    """
    controller = get_animation_controller()
    return controller.list_animations()


@router.get("/animations/{animation_id}/status")
async def get_animation_status(animation_id: str) -> Dict[str, Any]:
    """
    Get animation status.

    Args:
        animation_id: Animation identifier

    Returns:
        Animation state
    """
    controller = get_animation_controller()
    state = controller._active_animations.get(animation_id)

    if not state:
        raise HTTPException(status_code=404, detail="Animation not found")

    return {
        "animation_id": state.animation_id,
        "sequence_name": state.sequence_name,
        "is_playing": state.is_playing,
        "is_paused": state.is_paused,
        "current_time": state.current_time,
    }


@router.post("/tts")
async def synthesize_tts(
    text: str,
    vrm_id: Optional[str] = None,
    voice_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesize TTS and trigger lip-sync animation.

    Args:
        text: Text to synthesize
        vrm_id: VRM model ID
        voice_id: Optional voice ID

    Returns:
        TTS synthesis result with viseme timeline
    """
    tts = get_vrm_tts()
    result = await tts.synthesize_and_animate(text, vrm_id or "default", voice_id)
    return result


@router.get("/{vrm_id}/status")
async def get_vrm_status(vrm_id: str) -> Dict[str, Any]:
    """
    Get VRM avatar status.

    Args:
        vrm_id: VRM model identifier

    Returns:
        Current VRM state
    """
    controller = get_animation_controller()

    return {
        "vrm_id": vrm_id,
        "pose": controller.get_pose(),
        "blendshapes": controller.get_blendshapes(),
        "active_animations": len(controller._active_animations),
        "available_animations": controller.list_animations(),
    }
