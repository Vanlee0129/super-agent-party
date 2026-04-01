"""Stdio transport for MCP - subprocess-based communication."""

import asyncio
import json
import logging
import shutil
from typing import Optional, List, Dict, Any
import os

from py.mcp.transport.base import Transport

logger = logging.getLogger(__name__)


class StdioTransport(Transport):
    """Transport that communicates with an MCP server over stdio.

    This transport spawns a subprocess and communicates with it
    through stdin/stdout using JSON-RPC 2.0 messages.
    """

    def __init__(self) -> None:
        """Initialize stdio transport."""
        super().__init__()
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._cwd: Optional[str] = None
        self._read_buffer: asyncio.Queue = asyncio.Queue()

    async def start_server(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """Start an MCP server subprocess.

        Args:
            command: The command to run (e.g., 'npx', 'uv', 'python')
            args: Command arguments
            env: Environment variables
            cwd: Working directory

        Raises:
            FileNotFoundError: If command is not found
            Exception: If subprocess fails to start
        """
        if args is None:
            args = []

        # Find the actual command path
        cmd_path = shutil.which(command)
        if not cmd_path:
            raise FileNotFoundError(f"Command not found: {command}")

        # Prepare environment
        if env is not None:
            full_env = {**os.environ, **env}
        else:
            full_env = os.environ.copy()

        # Prepare working directory
        if cwd is None:
            cwd = self._cwd or os.getcwd()

        logger.info("Starting MCP server: %s %s (cwd=%s)", cmd_path, args, cwd)

        try:
            self._process = await asyncio.create_subprocess_exec(
                cmd_path,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env,
                cwd=cwd,
            )
            self._connected = True
            self._cwd = cwd

            # Start background reader
            self._reader_task = asyncio.create_task(self._read_loop())

            logger.info("MCP server started with PID: %s", self._process.pid)

        except Exception as e:
            logger.error("Failed to start MCP server: %s", e)
            self._connected = False
            raise

    async def connect(self) -> None:
        """Connect to server (alias for start_server compatibility)."""
        if not self._connected:
            raise RuntimeError("Server not started. Call start_server() first.")

    async def disconnect(self) -> None:
        """Stop the MCP server subprocess."""
        self._connected = False

        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Terminate process
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate gracefully, killing...")
                self._process.kill()
            except Exception as e:
                logger.error("Error terminating process: %s", e)

        self._process = None
        logger.info("MCP server stopped")

    async def send(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server.

        Args:
            message: The JSON-RPC message dictionary

        Raises:
            RuntimeError: If not connected
            Exception: If write fails
        """
        if not self._process or not self._connected:
            raise RuntimeError("Not connected to MCP server")

        try:
            data = json.dumps(message) + "\n"
            self._process.stdin.write(data.encode("utf-8"))
            await self._process.stdin.drain()
            logger.debug("Sent message: %s", message)
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            self.handle_error(e)
            raise

    async def receive(self) -> Dict[str, Any]:
        """Receive a JSON-RPC message from the server.

        Args:
            message: The JSON-RPC message dictionary

        Returns:
            Received message dictionary

        Raises:
            asyncio.CancelledError: If connection is closed
        """
        try:
            message = await self._read_buffer.get()
            logger.debug("Received message: %s", message)
            return message
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Failed to receive message: %s", e)
            self.handle_error(e)
            raise

    async def _read_loop(self) -> None:
        """Background loop that reads from subprocess stdout."""
        if not self._process or not self._process.stdout:
            return

        try:
            while self._connected:
                try:
                    line = await asyncio.wait_for(
                        self._process.stdout.readline(),
                        timeout=30.0,
                    )
                except asyncio.TimeoutError:
                    # Check if process is still alive
                    if self._process.returncode is not None:
                        break
                    continue

                if not line:
                    # EOF - process closed
                    logger.info("MCP server closed stdout")
                    break

                try:
                    text = line.decode("utf-8").strip()
                    if text:
                        message = json.loads(text)
                        self._read_buffer.put_nowait(message)
                        self.handle_message(message)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON from server: %s: %s", e, text)
                except Exception as e:
                    logger.exception("Error processing message: %s", e)

        except asyncio.CancelledError:
            logger.debug("Read loop cancelled")
        except Exception as e:
            logger.exception("Read loop error: %s", e)
            self.handle_error(e)
        finally:
            self._connected = False

    @property
    def pid(self) -> Optional[int]:
        """Get the subprocess PID if running."""
        if self._process:
            return self._process.pid
        return None
