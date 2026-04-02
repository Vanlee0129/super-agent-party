"""DingTalk Bot Platform Plugin.

Refactored from dingtalk_bot_manager.py
"""

import asyncio
import json
import logging
import random
import threading
from typing import Dict, Any, List, Optional

import aiohttp
import dingtalk_stream
from dingtalk_stream import AckMessage, ChatbotMessage
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from py.bots.platforms.base import BotPlatformPlugin
from py.plugins.base import PluginMetadata

logger = logging.getLogger(__name__)


class DingtalkBotConfig(BaseModel):
    """DingTalk bot configuration."""
    DingtalkAgent: str
    memoryLimit: int
    appKey: str
    appSecret: str
    separators: List[str]
    reasoningVisible: bool
    quickRestart: bool
    enableTTS: bool
    wakeWord: str
    behaviorSettings: Optional[Dict[str, Any]] = None
    behaviorTargetChatIds: List[str] = Field(default_factory=list)


class DingtalkBotPlugin(BotPlatformPlugin):
    """DingTalk bot platform implementation."""

    platform_name = "dingtalk"

    def __init__(self) -> None:
        super().__init__()
        self.bot_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._startup_error: Optional[str] = None
        self.client = None
        self.bot_logic: Optional["DingtalkClientLogic"] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="bot.platform.dingtalk",
            name="DingTalk Bot Platform",
            version="1.0.0",
            description="DingTalk bot platform plugin for enterprise messaging",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the DingTalk bot with configuration."""
        self._config = DingtalkBotConfig(**config)
        self.bot_logic = None
        logger.info(f"DingTalk bot initialized: {self._config.appKey}")

    async def _start(self) -> None:
        """Start the DingTalk bot."""
        if self._is_running:
            return

        self._startup_error = None

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(self._config,),
            daemon=True,
            name="DingtalkBotThread"
        )
        self.bot_thread.start()

        self._is_running = True
        logger.info("DingTalk bot started")

    async def _stop(self) -> None:
        """Stop the DingTalk bot."""
        if self.client:
            try:
                self.client.stop()
            except:
                pass
        self._is_running = False
        logger.info("DingTalk bot stopped")

    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        await self._stop()
        self._config = DingtalkBotConfig(**config)
        if self.bot_logic:
            self.bot_logic.config = self._config

    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "is_running": self._is_running,
            "has_error": self._startup_error is not None,
            "error_message": self._startup_error,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "platform": "dingtalk",
            "is_running": self._is_running,
            "uptime": 0,
            "message_count": 0,
        }

    def _run_bot_thread(self, config: DingtalkBotConfig) -> None:
        """Run bot in a separate thread."""

        async def main_loop():
            try:
                self.bot_logic = DingtalkClientLogic(config)

                from py.get_setting import load_settings
                settings = await load_settings()
                behavior_data = settings.get("behaviorSettings", {})
                target_ids = config.behaviorTargetChatIds or []

                if behavior_data:
                    logger.info(f"[Dingtalk] Syncing behavior config... targets: {len(target_ids)}")
                    from py.behavior_engine import global_behavior_engine
                    global_behavior_engine.update_config(behavior_data, {"dingtalk": target_ids})

                credential = dingtalk_stream.Credential(config.appKey, config.appSecret)
                self.client = dingtalk_stream.DingTalkStreamClient(credential)

                handler = DingtalkInternalHandler(self.bot_logic)
                self.client.register_callback_handler(ChatbotMessage.TOPIC, handler)

                logger.info("[Dingtalk] Starting behavior engine + DingTalk connection...")

                from py.behavior_engine import global_behavior_engine
                await asyncio.gather(
                    global_behavior_engine.start(),
                    self.client.start()
                )

            except Exception as e:
                self._startup_error = str(e)
                logger.error(f"[Dingtalk] Async loop exception: {e}")
            finally:
                self._is_running = False
                from py.behavior_engine import global_behavior_engine
                global_behavior_engine.stop()

        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(main_loop())
        except Exception as e:
            logger.error(f"[Dingtalk] Thread exit: {e}")

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a chat."""
        # Implementation in DingtalkClientLogic
        return False


class DingtalkInternalHandler(dingtalk_stream.ChatbotHandler):
    """Internal handler for DingTalk messages."""

    def __init__(self, bot_logic):
        super().__init__()
        self.bot_logic = bot_logic

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        try:
            incoming_message = ChatbotMessage.from_dict(callback.data)
            await self.bot_logic.on_message(callback.data, incoming_message, self)
        except Exception as e:
            logger.error(f"Message processing exception: {e}")
        return AckMessage.STATUS_OK, 'OK'


class DingtalkClientLogic:
    """Client logic for handling DingTalk messages."""

    def __init__(self, config: DingtalkBotConfig):
        self.config = config
        self.memory_list: Dict[str, List[dict]] = {}
        self.port = None
        self.separators = config.separators if config.separators else ['。', '\n', '？', '！']

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.register_handler("dingtalk", self.execute_behavior_event)

        try:
            from py.get_setting import get_port
            self.port = get_port()
        except Exception:
            self.port = 8000

    async def _get_image_base64(self, url: str) -> Optional[str]:
        """Download DingTalk image and convert to Base64."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.read()
                        import base64
                        return base64.b64encode(data).decode('utf-8')
        except Exception as e:
            logger.error(f"Image processing exception: {e}")
        return None

    async def on_message(self, raw_data: dict, incoming_message: ChatbotMessage, handler: DingtalkInternalHandler):
        """Handle incoming message."""
        cid = incoming_message.conversation_id
        msg_type = incoming_message.message_type

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.report_activity("dingtalk", cid)

        user_text_parts = []
        user_content_items = []
        has_image = False

        # Process text message
        if msg_type == "text":
            if hasattr(incoming_message, 'text') and incoming_message.text:
                user_text_parts.append(incoming_message.text.content.strip())

        # Process image message
        elif msg_type == "picture":
            download_code = incoming_message.image_content.download_code
            if download_code:
                img_url = handler.get_image_download_url(download_code)
                if img_url:
                    base64_str = await self._get_image_base64(img_url)
                    if base64_str:
                        has_image = True
                        user_content_items.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}
                        })
            if hasattr(incoming_message, 'text') and incoming_message.text:
                user_text_parts.append(incoming_message.text.content.strip())

        # Process rich text message
        elif msg_type == "richText":
            if hasattr(incoming_message, 'rich_text_content') and incoming_message.rich_text_content:
                rich_list = incoming_message.rich_text_content.rich_text_list
                if rich_list:
                    for item in rich_list:
                        if 'text' in item and item['text']:
                            user_text_parts.append(item['text'])
                        if 'downloadCode' in item and item['downloadCode']:
                            download_code = item['downloadCode']
                            img_url = handler.get_image_download_url(download_code)
                            if img_url:
                                base64_str = await self._get_image_base64(img_url)
                                if base64_str:
                                    has_image = True
                                    user_content_items.append({
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}
                                    })

        user_text = "\n".join(user_text_parts).strip()

        if not user_text and not has_image:
            return

        # Handle /id command
        if "/id" in user_text.lower():
            if cid.startswith("cid"):
                msg = f"【群聊】\n群会话 ID:\n`{cid}`"
            else:
                staff_id = getattr(incoming_message, 'sender_staff_id', None)
                if not staff_id:
                    staff_id = raw_data.get("senderStaffId")
                final_id = staff_id if staff_id else incoming_message.sender_id
                msg = f"【单聊】\n用户 ID:\n`{final_id}`"

            handler.reply_markdown("ID Assistant", msg, incoming_message)
            return

        if self.config.quickRestart and user_text and ("/重启" in user_text or "/restart" in user_text):
            self.memory_list[cid] = []
            handler.reply_text("对话记录已重置。", incoming_message)
            return

        if self.config.wakeWord and self.config.wakeWord not in user_text and not has_image:
            return

        if cid not in self.memory_list:
            self.memory_list[cid] = []

        current_content = []
        if user_text:
            current_content.append({"type": "text", "text": user_text})
        if has_image:
            current_content.extend(user_content_items)
            if not user_text:
                current_content.insert(0, {"type": "text", "text": "请分析这张图片"})

        self.memory_list[cid].append({"role": "user", "content": current_content})

        # Call AI
        ai_client = AsyncOpenAI(api_key="none", base_url=f"http://127.0.0.1:{self.port}/v1")
        state = {"text_buffer": "", "full_response": ""}

        try:
            stream = await ai_client.chat.completions.create(
                model=self.config.DingtalkAgent,
                messages=self.memory_list[cid],
                stream=True
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                reasoning = ""
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    if self.config.reasoningVisible:
                        reasoning = delta.reasoning_content

                content = delta.content or ""
                combined_chunk = reasoning + content

                if not combined_chunk:
                    continue

                state["text_buffer"] += combined_chunk
                state["full_response"] += content

                if any(sep in state["text_buffer"] for sep in self.separators):
                    if state["text_buffer"].strip():
                        handler.reply_markdown("AI Assistant", state["text_buffer"], incoming_message)
                    state["text_buffer"] = ""

            if state["text_buffer"].strip():
                handler.reply_markdown("AI Assistant", state["text_buffer"], incoming_message)

            self.memory_list[cid].append({"role": "assistant", "content": state["full_response"]})
            if self.config.memoryLimit > 0:
                while len(self.memory_list[cid]) > self.config.memoryLimit * 2:
                    self.memory_list[cid].pop(0)

        except Exception as e:
            logger.error(f"DingTalk AI generation exception: {e}")
            handler.reply_text(f"处理消息时出错: {str(e)}", incoming_message)

    async def _get_access_token(self) -> Optional[str]:
        """Get DingTalk API access token."""
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        payload = {
            "appKey": self.config.appKey,
            "appSecret": self.config.appSecret
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("accessToken")
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
        return None

    async def execute_behavior_event(self, chat_id: str, behavior_item: Any) -> None:
        """Execute behavior event triggered by behavior engine."""
        target_id = str(chat_id).strip()
        if not target_id:
            return

        logger.info(f"[Dingtalk] Behavior trigger! Target: {target_id}")

        def resolve_prompt(behavior):
            action = behavior.action
            if action.type == "prompt":
                return action.prompt
            elif action.type == "random":
                events = action.random.events
                if not events:
                    return None
                return random.choice(events) if action.random.type == "random" else events[action.random.orderIndex % len(events)]

        prompt_content = resolve_prompt(behavior_item)
        if not prompt_content:
            return

        try:
            ai_client = AsyncOpenAI(api_key="none", base_url=f"http://127.0.0.1:{self.port}/v1")
            response = await ai_client.chat.completions.create(
                model=self.config.DingtalkAgent,
                messages=[{"role": "user", "content": "[system]: " + prompt_content}],
                stream=False
            )
            reply_content = response.choices[0].message.content
            if not reply_content:
                return

            token = await self._get_access_token()
            if not token:
                return

            headers = {
                "x-acs-dingtalk-access-token": token,
                "Content-Type": "application/json"
            }

            if target_id.startswith("cid"):
                url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"
                payload = {
                    "msgKey": "sampleMarkdown",
                    "msgParam": json.dumps({
                        "title": "AI Assistant",
                        "text": reply_content
                    }),
                    "openConversationId": target_id,
                    "robotCode": self.config.appKey
                }
            else:
                url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
                payload = {
                    "robotCode": self.config.appKey,
                    "userIds": [target_id],
                    "msgKey": "sampleMarkdown",
                    "msgParam": json.dumps({
                        "title": "AI Assistant",
                        "text": reply_content
                    })
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    result = await resp.json()
                    if resp.status == 200 and result.get("processQueryKey"):
                        logger.info(f"[Dingtalk] Push success! Target: {target_id}")
                        if target_id not in self.memory_list:
                            self.memory_list[target_id] = []
                        self.memory_list[target_id].append({"role": "assistant", "content": reply_content})
                    else:
                        logger.error(f"[Dingtalk] Push failed: {result}")

        except Exception as e:
            logger.error(f"[Dingtalk] Execution exception: {e}")
