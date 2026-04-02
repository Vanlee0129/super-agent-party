"""
VMC (Virtual Motion Capture) Protocol

Used for VRM animation streaming with applications like VSeeFace, liv Avatar, etc.
VMC uses OSC-like message format over UDP/WebSocket.
"""

import asyncio
import logging
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class VMCMessageType(Enum):
    """VMC protocol message types."""
    ROOT = "/VMC/Ext/Root"
    BONE = "/VMC/Ext/Bone"
    BLENDSHAPE = "/VMC/Ext/BlendShape"
    CONTROLLER = "/VMC/Ext/Con"
    TIMELINE = "/VMC/Ext/Timeline"
    TRAIL = "/VMC/Ext/Trail"
    SET = "/VMC/Ext/Set"


@dataclass
class BoneData:
    """Bone rotation and position data."""
    name: str
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # quaternion


@dataclass
class BlendshapeData:
    """Blend shape (viseme) data."""
    name: str
    weight: float = 0.0


@dataclass
class VMCFrame:
    """VMC Protocol Frame containing all avatar animation data."""

    # Root position and rotation
    root_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    root_rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)

    # Bone data indexed by bone name
    bones: Dict[str, BoneData] = field(default_factory=dict)

    # Blend shapes indexed by name
    blendshapes: Dict[str, BlendshapeData] = field(default_factory=dict)

    # Metadata
    timestamp: float = 0.0
    frame_index: int = 0

    @classmethod
    def parse(cls, data: bytes) -> "VMCFrame":
        """Parse VMC frame from raw bytes."""
        # VMC protocol uses OSC-like format
        # Format: OSC address pattern + type tags + values
        frame = cls()

        try:
            # Simple OSC-style parsing
            # VMC messages start with address pattern as null-terminated string
            offset = 0

            # Read address pattern
            addr_end = data.find(b'\x00', offset)
            if addr_end == -1:
                return frame

            address = data[offset:addr_end].decode('utf-8', errors='ignore')
            offset = addr_end + 4 - (addr_end % 4)  # Align to 4 bytes

            # Read type tag string (starts with ',')
            if offset >= len(data):
                return frame

            if data[offset:offset+1] == b',':
                offset += 1
                type_tags = []
                while offset < len(data) and data[offset:offset+1] != b'\x00':
                    type_tags.append(chr(data[offset]))
                    offset += 1

                # Parse values based on type tags
                values = []
                for tag in type_tags:
                    if offset + 4 > len(data):
                        break

                    if tag in ('f', 'i'):
                        values.append(struct.unpack('>f', data[offset:offset+4])[0])
                        offset += 4
                    elif tag == 's':
                        # String: null-terminated
                        str_end = data.find(b'\x00', offset)
                        if str_end == -1:
                            break
                        str_val = data[offset:str_end].decode('utf-8', errors='ignore')
                        values.append(str_val)
                        offset = str_end + 4 - ((str_end - offset) % 4)
                    elif tag == 'r':
                        # RGB color
                        values.append(struct.unpack('>fff', data[offset:offset+12]))
                        offset += 12

            # Parse based on address type
            if address == VMCMessageType.ROOT.value:
                if len(values) >= 7:
                    frame.root_position = (values[0], values[1], values[2])
                    frame.root_rotation = (values[3], values[4], values[5], values[6])

            elif address == VMCMessageType.BONE.value:
                if len(values) >= 8:
                    bone_name = values[0]
                    frame.bones[bone_name] = BoneData(
                        name=bone_name,
                        position=(values[1], values[2], values[3]),
                        rotation=(values[4], values[5], values[6], values[7])
                    )

            elif address == VMCMessageType.BLENDSHAPE.value:
                if len(values) >= 2:
                    blendshape_name = values[0]
                    weight = values[1]
                    frame.blendshapes[blendshape_name] = BlendshapeData(
                        name=blendshape_name,
                        weight=weight
                    )

        except Exception as e:
            logger.error(f"Error parsing VMC frame: {e}")

        return frame

    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to dictionary for JSON serialization."""
        return {
            "root": {
                "position": list(self.root_position),
                "rotation": list(self.root_rotation),
            },
            "bones": {
                name: {
                    "position": list(bone.position),
                    "rotation": list(bone.rotation),
                }
                for name, bone in self.bones.items()
            },
            "blendshapes": {
                name: bs.weight
                for name, bs in self.blendshapes.items()
            },
            "timestamp": self.timestamp,
            "frame_index": self.frame_index,
        }


class VMCServer:
    """VMC Protocol Server - receives data from VSeeFace and other VMC clients."""

    DEFAULT_PORT = 39539

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.port_udp: Optional[asyncio.DatagramProtocol] = None
        self._running = False
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._frames: List[VMCFrame] = []
        self._ws_clients: List["WebSocket"] = []
        self._frame_index = 0

    async def start(self) -> None:
        """Start VMC UDP server."""
        if self._running:
            logger.warning("VMC server already running")
            return

        self._running = True
        loop = asyncio.get_event_loop()

        # Create UDP server
        self._transport, self.port_udp = await loop.create_datagram_endpoint(
            lambda: VMCProtocolHandler(self),
            local_addr=('0.0.0.0', self.port)
        )

        logger.info(f"VMC server started on UDP port {self.port}")

    async def stop(self) -> None:
        """Stop VMC server."""
        self._running = False
        if self._transport:
            self._transport.close()
            self._transport = None
        logger.info("VMC server stopped")

    def add_ws_client(self, ws: "WebSocket") -> None:
        """Add a WebSocket client to broadcast frames to."""
        if ws not in self._ws_clients:
            self._ws_clients.append(ws)

    def remove_ws_client(self, ws: "WebSocket") -> None:
        """Remove a WebSocket client."""
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    def broadcast_frame(self, frame: VMCFrame) -> None:
        """Broadcast frame to all connected WebSocket clients."""
        if not self._ws_clients:
            return

        frame_data = frame.to_dict()
        disconnected = []

        for ws in self._ws_clients:
            try:
                # Send as JSON message
                asyncio.create_task(ws.send_json({
                    "type": "vmc_frame",
                    "data": frame_data
                }))
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            self.remove_ws_client(ws)

    def process_frame(self, data: bytes) -> None:
        """Process incoming VMC frame data."""
        frame = VMCFrame.parse(data)
        frame.frame_index = self._frame_index
        self._frame_index += 1

        self._frames.append(frame)
        if len(self._frames) > 100:  # Keep last 100 frames
            self._frames.pop(0)

        self.broadcast_frame(frame)

    @property
    def latest_frame(self) -> Optional[VMCFrame]:
        """Get the most recent frame."""
        return self._frames[-1] if self._frames else None

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


class VMCProtocolHandler(asyncio.DatagramProtocol):
    """UDP protocol handler for VMC messages."""

    def __init__(self, server: VMCServer):
        self.server = server

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        """Handle incoming UDP datagram."""
        if not self.server._running:
            return

        try:
            self.server.process_frame(data)
        except Exception as e:
            logger.error(f"Error processing VMC datagram from {addr}: {e}")

    def error_received(self, exc: Exception) -> None:
        """Handle UDP errors."""
        logger.error(f"VMC UDP error: {exc}")


async def create_vmc_server(port: int = VMCServer.DEFAULT_PORT) -> VMCServer:
    """Create and start a VMC server."""
    server = VMCServer(port=port)
    await server.start()
    return server
