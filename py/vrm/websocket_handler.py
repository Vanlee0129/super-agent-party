"""VRM WebSocket handler for real-time avatar communication."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from py.vrm.vmc_protocol import VMCFrame, VMCServer
from py.vrm.animation import AnimationController

logger = logging.getLogger(__name__)


class VRMConnectionManager:
    """Manages WebSocket connections for VRM clients."""

    def __init__(self) -> None:
        self._connections: Dict[str, Dict[str, Any]] = {}

    async def connect(self, client_id: str, websocket: WebSocket, vrm_id: Optional[str] = None) -> None:
        """Accept and register a VRM WebSocket connection."""
        await websocket.accept()
        self._connections[client_id] = {
            "websocket": websocket,
            "vrm_id": vrm_id,
            "subscriptions": set(),
        }
        logger.info(f"VRM client connected: {client_id}, vrm_id: {vrm_id}")

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(f"VRM client disconnected: {client_id}")

    async def send(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific VRM client."""
        if client_id in self._connections:
            websocket = self._connections[client_id]["websocket"]
            await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any], vrm_id: Optional[str] = None) -> None:
        """Broadcast a message to all connected VRM clients, optionally filtered by vrm_id."""
        for conn_id, conn_data in self._connections.items():
            if vrm_id is None or conn_data.get("vrm_id") == vrm_id:
                await conn_data["websocket"].send_json(message)

    def subscribe(self, client_id: str, channel: str) -> None:
        """Subscribe client to a channel."""
        if client_id in self._connections:
            self._connections[client_id]["subscriptions"].add(channel)

    def unsubscribe(self, client_id: str, channel: str) -> None:
        """Unsubscribe client from a channel."""
        if client_id in self._connections:
            self._connections[client_id]["subscriptions"].discard(channel)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)


# Global connection manager
vrm_connection_manager = VRMConnectionManager()


class VRMWebSocket:
    """Handle VRM avatar WebSocket communication."""

    def __init__(self, vmc_server: Optional[VMCServer] = None, animation_controller: Optional[AnimationController] = None):
        self.vmc_server = vmc_server
        self.animation_controller = animation_controller or AnimationController()
        self._client_id: Optional[str] = None
        self._running = False

    async def handle_connection(self, websocket: WebSocket, vrm_id: Optional[str] = None) -> None:
        """Handle a VRM WebSocket connection."""
        self._client_id = str(id(websocket))
        self._running = True

        await vrm_connection_manager.connect(self._client_id, websocket, vrm_id)

        # Register with VMC server if available
        if self.vmc_server:
            self.vmc_server.add_ws_client(websocket)

        try:
            while self._running:
                data = await websocket.receive_json()
                await self._handle_message(data)
        except WebSocketDisconnect:
            logger.info(f"VRM client {self._client_id} disconnected")
        except Exception as e:
            logger.error(f"VRM WebSocket error for client {self._client_id}: {e}")
        finally:
            await self._cleanup()

    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        msg_type = data.get("type")
        payload = data.get("data", {})

        if msg_type == "vrm_frame":
            await self._handle_vrm_frame(payload)
        elif msg_type == "blendshape_update":
            await self._handle_blendshape_update(payload)
        elif msg_type == "bone_update":
            await self._handle_bone_update(payload)
        elif msg_type == "animation_trigger":
            await self._handle_animation_trigger(payload)
        elif msg_type == "tts_request":
            await self._handle_tts_request(payload)
        elif msg_type == "vmc_data":
            await self._handle_vmc_data(payload)
        elif msg_type == "subscribe":
            self._handle_subscribe(payload)
        elif msg_type == "ping":
            await vrm_connection_manager.send(self._client_id, {"type": "pong"})
        else:
            logger.warning(f"Unknown VRM message type: {msg_type}")

    async def _handle_vrm_frame(self, payload: Dict[str, Any]) -> None:
        """Handle incoming VRM animation frame."""
        # Process bone data
        bones = payload.get("bones", {})
        for bone_name, bone_data in bones.items():
            self.animation_controller.set_bone(bone_name, bone_data)

        # Process blend shapes
        blendshapes = payload.get("blendshapes", {})
        for name, weight in blendshapes.items():
            self.animation_controller.set_blendshape(name, weight)

        # Broadcast to other clients if needed
        await vrm_connection_manager.broadcast({
            "type": "vrm_frame",
            "data": payload,
        }, vrm_id=payload.get("vrm_id"))

    async def _handle_blendshape_update(self, payload: Dict[str, Any]) -> None:
        """Handle blend shape weight update."""
        blendshapes = payload.get("blendshapes", {})
        for name, weight in blendshapes.items():
            self.animation_controller.set_blendshape(name, weight)

        # Acknowledge
        await vrm_connection_manager.send(self._client_id, {
            "type": "blendshape_ack",
            "data": {"updated": list(blendshapes.keys())}
        })

    async def _handle_bone_update(self, payload: Dict[str, Any]) -> None:
        """Handle bone rotation/position update."""
        bone_name = payload.get("bone")
        transform = payload.get("transform", {})

        if bone_name:
            self.animation_controller.set_bone(bone_name, transform)

        await vrm_connection_manager.send(self._client_id, {
            "type": "bone_ack",
            "data": {"bone": bone_name}
        })

    async def _handle_animation_trigger(self, payload: Dict[str, Any]) -> None:
        """Handle animation trigger request."""
        animation_type = payload.get("animation")
        vrm_id = payload.get("vrm_id")

        await self.animation_controller.trigger_animation(animation_type, vrm_id)

        await vrm_connection_manager.send(self._client_id, {
            "type": "animation_started",
            "data": {"animation": animation_type}
        })

    async def _handle_tts_request(self, payload: Dict[str, Any]) -> None:
        """Handle TTS synthesis request for VRM animation."""
        text = payload.get("text")
        vrm_id = payload.get("vrm_id")
        voice_id = payload.get("voice_id")

        # This would integrate with TTS service
        # For now, send acknowledgment
        await vrm_connection_manager.send(self._client_id, {
            "type": "tts_started",
            "data": {"text": text, "vrm_id": vrm_id}
        })

    async def _handle_vmc_data(self, payload: Dict[str, Any]) -> None:
        """Handle VMC protocol data (forwarded from VMC server)."""
        # Parse VMC frame
        frame = VMCFrame.parse(payload.get("raw", b""))

        # Update animation controller with VMC data
        for bone_name, bone_data in frame.bones.items():
            self.animation_controller.set_bone(bone_name, {
                "position": bone_data.position,
                "rotation": bone_data.rotation,
            })

        for name, bs_data in frame.blendshapes.items():
            self.animation_controller.set_blendshape(name, bs_data.weight)

    def _handle_subscribe(self, payload: Dict[str, Any]) -> None:
        """Handle subscription to channels."""
        channel = payload.get("channel")
        if channel and self._client_id:
            vrm_connection_manager.subscribe(self._client_id, channel)

    async def send_frame(self, frame_data: Dict[str, Any]) -> None:
        """Send VRM animation frame to client."""
        if self._client_id:
            await vrm_connection_manager.send(self._client_id, {
                "type": "vrm_frame",
                "data": frame_data
            })

    async def receive_frame(self, frame_data: Dict[str, Any]) -> None:
        """Receive bone data from client (VMC protocol)."""
        await self._handle_vrm_frame(frame_data)

    async def _cleanup(self) -> None:
        """Clean up on disconnect."""
        if self.vmc_server and self._client_id:
            # Find and remove from VMC server
            pass  # VMC server handles its own client list

        vrm_connection_manager.disconnect(self._client_id)
        self._running = False

    async def stop(self) -> None:
        """Stop the WebSocket handler."""
        self._running = False


async def create_vrm_websocket_handler(
    vmc_server: Optional[VMCServer] = None,
    animation_controller: Optional[AnimationController] = None
) -> VRMWebSocket:
    """Create a VRM WebSocket handler."""
    return VRMWebSocket(vmc_server=vmc_server, animation_controller=animation_controller)
