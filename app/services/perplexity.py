import logging
from collections.abc import AsyncGenerator
from typing import Any

from perplexity import Perplexity

from app.config import SYSTEM_PROMPT
from app.models.chat import ChatMessage, SearchMode

logger = logging.getLogger(__name__)

SEARCH_MODE_CONFIG: dict[SearchMode, dict[str, Any]] = {
    SearchMode.FAST: {
        "model": "sonar",
        "web_search_options": {"search_context_size": "low"},
    },
    SearchMode.PRO: {
        "model": "sonar-pro",
        "web_search_options": {"search_context_size": "high", "search_type": "auto"},
    },
}


class PerplexityService:
    def __init__(self, client: Perplexity) -> None:
        self._client = client

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        search: SearchMode = SearchMode.FAST,
    ) -> AsyncGenerator[str, None]:
        sanitized = [m for m in messages if m.role != "system"]

        api_messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": m.role, "content": m.content} for m in sanitized],
        ]

        config = SEARCH_MODE_CONFIG[search]

        logger.info(
            "Perplexity request — model=%s, search=%s, messages=%d",
            config["model"],
            search.value,
            len(api_messages),
        )

        stream = self._client.chat.completions.create(
            messages=api_messages,
            stream=True,
            **config,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
