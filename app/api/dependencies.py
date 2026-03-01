from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWK

from app.services.perplexity import PerplexityService

_bearer = HTTPBearer()


def _find_signing_key(token: str, jwks: list[PyJWK]) -> PyJWK:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for key in jwks:
        if key.key_id == kid:
            return key
    raise jwt.InvalidTokenError(f"No matching key found for kid={kid}")


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    token = credentials.credentials
    try:
        jwks: list[PyJWK] = request.app.state.jwks
        signing_key = _find_signing_key(token, jwks)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
        )
        return payload["sub"]
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from exc


CurrentUser = Annotated[str, Depends(get_current_user)]


def get_perplexity_service(request: Request) -> PerplexityService:
    return request.app.state.perplexity_service


PerplexityDep = Annotated[PerplexityService, Depends(get_perplexity_service)]
