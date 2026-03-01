import json
import logging

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import CurrentUser, PerplexityDep
from app.config import settings
from app.limiter import limiter
from app.models.chat import ChatRequest, StreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat")
@limiter.limit(settings.rate_limit)
async def chat(
    request: Request,
    body: ChatRequest,
    service: PerplexityDep,
    user_id: CurrentUser,
) -> EventSourceResponse:
    request.state.user_id = user_id
    logger.info("Chat request from user=%s, search=%s", user_id, body.search.value)

    async def event_generator():
        try:
            async for content in service.stream_chat(
                messages=body.messages,
                search=body.search,
            ):
                event = StreamEvent(type="content_delta", content=content)
                yield json.dumps(event.model_dump(exclude_none=True))

            done = StreamEvent(type="done")
            yield json.dumps(done.model_dump(exclude_none=True))

        except Exception:
            logger.exception("Streaming error for user=%s", user_id)
            error = StreamEvent(type="error", content="An internal error occurred.")
            yield json.dumps(error.model_dump(exclude_none=True))

    return EventSourceResponse(event_generator())
