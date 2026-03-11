import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from perplexity import Perplexity
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import chat, health
from app.config import settings
from app.limiter import limiter
from app.services.perplexity import PerplexityService

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = Perplexity(api_key=settings.perplexity_api_key)
    app.state.perplexity_service = PerplexityService(client)

    if settings.auth_disabled:
        logger.warning("Auth is DISABLED — do not use in production")
        app.state.jwks = []
    else:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        app.state.jwks = jwks_client.get_jwk_set().keys
        logger.info("JWKS loaded from %s (%d keys)", jwks_url, len(app.state.jwks))

    yield


app = FastAPI(
    title="Playbook API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
