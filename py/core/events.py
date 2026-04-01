"""Event emission system for Super Agent Party."""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from py.core.exceptions import SuperAgentError


class EventEmitter:
    """Event emitter for pub/sub messaging."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[..., None]]] = {}

    def on(self, event_type: str, handler: Callable[..., None]) -> None:
        """Register an event handler.

        Args:
            event_type: The type of event to listen for.
            handler: The callback function to invoke when the event is emitted.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)

    def off(self, event_type: str, handler: Callable[..., None]) -> None:
        """Unregister an event handler.

        Args:
            event_type: The type of event.
            handler: The callback function to remove.
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(handler)
            except ValueError:
                pass

    def emit(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event, invoking all registered handlers.

        Args:
            event_type: The type of event to emit.
            *args: Positional arguments to pass to handlers.
            **kwargs: Keyword arguments to pass to handlers.
        """
        if event_type in self._listeners:
            for handler in self._listeners[event_type]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    raise SuperAgentError(f"Event handler error: {e}") from e


@dataclass
class Event:
    """Event data structure."""

    type: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)


# Global events instance
events = EventEmitter()
