import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import PerplexityDep
from app.models.chat import ChatRequest, StreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(request: ChatRequest, service: PerplexityDep) -> EventSourceResponse:
    async def event_generator():
        try:
            async for content in service.stream_chat(
                messages=request.messages,
                search=request.search,
            ):
                event = StreamEvent(type="content_delta", content=content)
                yield json.dumps(event.model_dump(exclude_none=True))

            done = StreamEvent(type="done")
            yield json.dumps(done.model_dump(exclude_none=True))

        except Exception:
            logger.exception("Streaming error")
            error = StreamEvent(type="error", content="An internal error occurred.")
            yield json.dumps(error.model_dump(exclude_none=True))

    return EventSourceResponse(event_generator())
