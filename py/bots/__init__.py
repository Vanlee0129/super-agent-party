"""Bot management package.

Provides unified REST API endpoints for managing bots across multiple platforms:
- Feishu
- QQ
- Discord
- Slack
- DingTalk
- Telegram

Usage:
    from py.bots.api import router
    app.include_router(router)

    # Initialize managers at startup
    from py.bots.registry import initialize_managers
    initialize_managers()
"""

from py.bots.api import router
from py.bots.registry import (
    BotRegistry,
    BotManagerAdapter,
    get_bot_manager,
    get_supported_platforms,
    initialize_managers,
)

__all__ = [
    "router",
    "BotRegistry",
    "BotManagerAdapter",
    "get_bot_manager",
    "get_supported_platforms",
    "initialize_managers",
]
