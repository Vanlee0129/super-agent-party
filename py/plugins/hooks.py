"""Plugin hooks system for lifecycle and event callbacks."""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from py.core.exceptions import SuperAgentError


class Hook(Enum):
    """Enumeration of available plugin hooks."""

    BEFORE_STARTUP = "before_startup"
    AFTER_STARTUP = "after_startup"
    BEFORE_SHUTDOWN = "before_shutdown"
    AFTER_SHUTDOWN = "after_shutdown"
    ON_REQUEST = "on_request"
    ON_MESSAGE = "on_message"


class PluginHooks:
    """Manages plugin hook registrations and emissions."""

    def __init__(self) -> None:
        self._handlers: Dict[Hook, List[Callable[..., Any]]] = {
            hook: [] for hook in Hook
        }

    def register(self, hook: Hook, handler: Callable[..., Any]) -> None:
        """Register a handler for a specific hook.

        Args:
            hook: The hook type to register for.
            handler: The callback function to invoke when the hook is emitted.
        """
        if hook not in self._handlers:
            self._handlers[hook] = []
        self._handlers[hook].append(handler)

    def unregister(self, hook: Hook, handler: Callable[..., Any]) -> None:
        """Unregister a handler from a specific hook.

        Args:
            hook: The hook type to unregister from.
            handler: The callback function to remove.
        """
        if hook in self._handlers:
            try:
                self._handlers[hook].remove(handler)
            except ValueError:
                pass

    def emit(self, hook: Hook, *args: Any, **kwargs: Any) -> List[Any]:
        """Emit a hook, invoking all registered handlers.

        Args:
            hook: The hook type to emit.
            *args: Positional arguments to pass to handlers.
            **kwargs: Keyword arguments to pass to handlers.

        Returns:
            A list of results from all handlers.
        """
        results: List[Any] = []
        if hook in self._handlers:
            for handler in self._handlers[hook]:
                try:
                    result = handler(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    raise SuperAgentError(
                        f"Hook handler error for {hook.value}: {e}"
                    ) from e
        return results

    def clear(self, hook: Optional[Hook] = None) -> None:
        """Clear all handlers for a specific hook, or all hooks if none specified.

        Args:
            hook: Optional hook to clear. If None, clears all hooks.
        """
        if hook is not None:
            self._handlers[hook] = []
        else:
            self._handlers = {hook: [] for hook in Hook}


# Global hooks instance
hooks = PluginHooks()
