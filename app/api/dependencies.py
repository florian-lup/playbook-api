import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWKClientError

from app.config import settings
from app.services.perplexity import PerplexityService

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=not settings.auth_disabled)


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> str:
    if settings.auth_disabled:
        logger.debug("Auth disabled — using dev-user")
        return "dev-user"

    if credentials is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    token = credentials.credentials
    try:
        jwks_client: PyJWKClient = request.app.state.jwks_client
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not isinstance(kid, str):
            raise jwt.InvalidTokenError("Missing key id")
        signing_key = jwks_client.get_signing_key(kid)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
        user_id = payload["sub"]
        if not isinstance(user_id, str) or not user_id:
            raise jwt.InvalidTokenError("Missing subject")
        return user_id
    except PyJWKClientConnectionError as exc:
        logger.warning("Failed to refresh Supabase JWKS: %s", exc)
        raise HTTPException(
            status_code=503, detail="Authentication unavailable"
        ) from exc
    except (jwt.InvalidTokenError, PyJWKClientError) as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from exc


CurrentUser = Annotated[str, Depends(get_current_user)]


def get_perplexity_service(request: Request) -> PerplexityService:
    return request.app.state.perplexity_service


PerplexityDep = Annotated[PerplexityService, Depends(get_perplexity_service)]
