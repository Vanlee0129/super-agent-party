"""REST API routes for OpenAI-compatible chat endpoints."""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from py.chat.history import ChatHistory
from py.chat.streamer import ChatStreamer
from py.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    get_registry,
    list_available_models,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


# ==================== Chat Completions ====================

@router.post("/chat/completions")
async def create_chat_completion(request: Dict[str, Any]) -> ChatCompletionResponse:
    """OpenAI-compatible chat completions endpoint.

    Supports both streaming and non-streaming responses.
    """
    # Extract parameters
    model = request.get("model", "gpt-4")
    messages = request.get("messages", [])
    stream = request.get("stream", False)
    provider = request.get("provider", "openai")

    # Convert messages to ChatMessage objects
    chat_messages = []
    for msg in messages:
        chat_messages.append(ChatMessage(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
        ))

    # Create request object
    chat_request = ChatCompletionRequest(
        model=model,
        messages=chat_messages,
        stream=stream,
    )

    # Get provider
    registry = get_registry()
    provider_config = registry.get_config(provider)
    if not provider_config:
        raise HTTPException(status_code=400, detail=f"Provider not configured: {provider}")

    provider_instance = registry.get_instance(provider)
    if not provider_instance:
        provider_instance = registry.create(provider_config)

    if stream:
        # Return streaming response
        return StreamingResponse(
            _stream_response(chat_request, provider_instance, model),
            media_type="text/event-stream",
        )
    else:
        # Non-streaming response
        response = await provider_instance.chat_complete(chat_request)
        return response


async def _stream_response(request: ChatCompletionRequest, provider_instance, model: str):
    """Generator for streaming SSE responses."""
    import json

    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    first_chunk = True

    try:
        async for chunk in provider_instance.chat_complete_stream(request):
            if first_chunk:
                # Send role in first chunk
                content = chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                yield f"data: {json.dumps({
                    'id': chunk_id,
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': model,
                    'choices': [{
                        'index': chunk.index if hasattr(chunk, 'index') else 0,
                        'delta': {'role': 'assistant', 'content': content},
                        'finish_reason': None,
                    }]
                })}\n\n"
                first_chunk = False
            else:
                content = chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                yield f"data: {json.dumps({
                    'id': chunk_id,
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': model,
                    'choices': [{
                        'index': chunk.index if hasattr(chunk, 'index') else 0,
                        'delta': {'content': content},
                        'finish_reason': chunk.finish_reason if hasattr(chunk, 'finish_reason') else None,
                    }]
                })}\n\n"

        # Send final chunk
        yield f"data: {json.dumps({
            'id': chunk_id,
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': model,
            'choices': [{
                'index': 0,
                'delta': {},
                'finish_reason': 'stop',
            }]
        })}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.exception(f"Error in stream response: {e}")
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'internal_error'}})}\n\n"


# ==================== Models ====================

@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """List available models."""
    models = list_available_models()
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 0,
                "owned_by": info.provider,
                "permission": [],
            }
            for model_id, info in models.items()
        ],
    }


# ==================== Streaming Chat ====================

@router.post("/chat/stream")
async def stream_chat(request: Dict[str, Any]) -> StreamingResponse:
    """Streaming chat endpoint with conversation history support.

    Returns Server-Sent Events (SSE) stream.
    """
    message = request.get("message", "")
    model = request.get("model", "gpt-4")
    conversation_id = request.get("conversation_id")
    provider = request.get("provider", "openai")
    history_limit = request.get("history_limit", 50)

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    # Get conversation history
    history_messages = []
    if conversation_id:
        history_messages = ChatHistory.get_messages(conversation_id, limit=history_limit)

    # Add current message to history
    msg_id = str(uuid.uuid4())
    timestamp = time.time()

    if conversation_id:
        ChatHistory.add_message(conversation_id, {
            "id": msg_id,
            "role": "user",
            "content": message,
            "timestamp": timestamp,
        })

    # Create streamer
    streamer = ChatStreamer()

    return StreamingResponse(
        _chat_stream_response(streamer, message, model, provider, conversation_id, history_messages),
        media_type="text/event-stream",
    )


async def _chat_stream_response(
    streamer: ChatStreamer,
    message: str,
    model: str,
    provider: str,
    conversation_id: Optional[str],
    history_messages: List[Dict[str, Any]],
):
    """Generator for chat SSE responses."""
    import json

    stream_id = str(uuid.uuid4())
    first_chunk = True
    full_content = ""
    assistant_id = str(uuid.uuid4())
    assistant_timestamp = time.time()

    try:
        async for chunk in streamer.stream_chat(
            message,
            model=model,
            provider=provider,
            conversation_history=history_messages,
        ):
            if chunk.get("type") == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': chunk.get('content')})}\n\n"
                continue

            if chunk.get("type") == "chunk":
                delta = chunk.get("delta", "")
                full_content += delta

                yield f"data: {json.dumps({
                    'type': 'chunk',
                    'stream_id': stream_id,
                    'id': assistant_id if not first_chunk else None,
                    'content': delta,
                    'done': False,
                })}\n\n"
                first_chunk = False

        # Add assistant message to history
        if conversation_id:
            ChatHistory.add_message(conversation_id, {
                "id": assistant_id,
                "role": "assistant",
                "content": full_content,
                "timestamp": assistant_timestamp,
            })

        # Send done signal
        yield f"data: {json.dumps({
            'type': 'done',
            'stream_id': stream_id,
            'id': assistant_id,
            'content': full_content,
            'conversation_id': conversation_id,
        })}\n\n"

    except Exception as e:
        logger.exception(f"Error in chat stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


# ==================== Conversation History ====================

@router.get("/chat/history/{conversation_id}")
async def get_history(conversation_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get conversation history."""
    messages = ChatHistory.get_messages(conversation_id, limit=limit)
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "count": len(messages),
    }


@router.delete("/chat/history/{conversation_id}")
async def clear_history(conversation_id: str) -> Dict[str, Any]:
    """Clear conversation history."""
    ChatHistory.clear_conversation(conversation_id)
    return {
        "conversation_id": conversation_id,
        "cleared": True,
    }


@router.get("/chat/stats")
async def get_stats() -> Dict[str, Any]:
    """Get chat statistics."""
    return ChatHistory.get_stats()
