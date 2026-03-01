from typing import Annotated

from fastapi import Depends, Request

from app.services.perplexity import PerplexityService


def get_perplexity_service(request: Request) -> PerplexityService:
    return request.app.state.perplexity_service


PerplexityDep = Annotated[PerplexityService, Depends(get_perplexity_service)]
