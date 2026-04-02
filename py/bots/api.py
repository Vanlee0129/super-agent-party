"""FastAPI routes for bot management across all platforms."""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from py.bots.registry import BotRegistry, get_bot_manager, get_supported_platforms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots", tags=["bots"])


class BotStatus(BaseModel):
    """Bot status response model."""
    platform: str
    status: str  # "running", "stopped", "error"
    uptime: float
    message_count: int
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BotConfig(BaseModel):
    """Bot configuration request model."""
    platform: str
    config: Dict[str, Any]


class BotStats(BaseModel):
    """Bot statistics response model."""
    platform: str
    uptime: float
    message_count: int
    error_count: int
    running: bool


# Supported platforms
SUPPORTED_PLATFORMS = ["feishu", "qq", "discord", "slack", "dingtalk", "telegram"]


def validate_platform(platform: str) -> None:
    """Validate that a platform is supported."""
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=404,
            detail=f"Platform '{platform}' not supported. Supported platforms: {SUPPORTED_PLATFORMS}"
        )


async def _get_manager(platform: str):
    """Get and validate bot manager, raising HTTPException if not found."""
    validate_platform(platform)
    manager = get_bot_manager(platform)
    if not manager:
        raise HTTPException(
            status_code=404,
            detail=f"Bot manager for '{platform}' not initialized. Call /api/v1/bots/init first."
        )
    return manager


@router.post("/{platform}/start")
async def start_bot(platform: str, config: Optional[BotConfig] = None):
    """Start a bot for the specified platform."""
    manager = await _get_manager(platform)
    try:
        await manager.start(config.config if config else None)
        return {"status": "started", "platform": platform}
    except Exception as e:
        logger.error(f"Failed to start {platform} bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{platform}/stop")
async def stop_bot(platform: str):
    """Stop a bot for the specified platform."""
    manager = await _get_manager(platform)
    try:
        await manager.stop()
        return {"status": "stopped", "platform": platform}
    except Exception as e:
        logger.error(f"Failed to stop {platform} bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/status", response_model=BotStatus)
async def get_status(platform: str):
    """Get the status of a bot."""
    manager = await _get_manager(platform)
    try:
        return BotStatus(**await manager.get_status())
    except Exception as e:
        logger.error(f"Failed to get status for {platform} bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{platform}/reload")
async def reload_bot(platform: str, config: Optional[BotConfig] = None):
    """Reload a bot with new configuration."""
    manager = await _get_manager(platform)
    try:
        await manager.reload(config.config if config else None)
        return {"status": "reloaded", "platform": platform}
    except Exception as e:
        logger.error(f"Failed to reload {platform} bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/stats", response_model=BotStats)
async def get_stats(platform: str):
    """Get statistics for a bot."""
    manager = await _get_manager(platform)
    try:
        return BotStats(**await manager.get_stats())
    except Exception as e:
        logger.error(f"Failed to get stats for {platform} bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def list_platforms():
    """List all supported bot platforms."""
    return {
        "platforms": SUPPORTED_PLATFORMS,
        "registered": BotRegistry.list_platforms(),
    }


@router.post("/init")
async def init_bots():
    """Initialize all bot managers."""
    from py.bots.registry import initialize_managers
    try:
        initialize_managers()
        return {"status": "initialized", "platforms": BotRegistry.list_platforms()}
    except Exception as e:
        logger.error(f"Failed to initialize bot managers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-all")
async def start_all_bots():
    """Start all registered bots."""
    try:
        await BotRegistry.start_all()
        return {"status": "started", "platforms": {p: "started" for p in BotRegistry.list_platforms()}}
    except Exception as e:
        logger.error(f"Failed to start all bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all")
async def stop_all_bots():
    """Stop all registered bots."""
    try:
        await BotRegistry.stop_all()
        return {"status": "stopped", "platforms": {p: "stopped" for p in BotRegistry.list_platforms()}}
    except Exception as e:
        logger.error(f"Failed to stop all bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status-all")
async def get_all_status():
    """Get status of all registered bots."""
    try:
        return {"platforms": BotRegistry.get_all_status()}
    except Exception as e:
        logger.error(f"Failed to get all bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
