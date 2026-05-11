import hmac
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from parcel_locker.core.config import Settings, get_settings
from parcel_locker.domain.exceptions import UnauthorizedError

_bearer_scheme = HTTPBearer(auto_error=False, description="Static API token")


def require_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Reject requests without a valid bearer token.

    Static token comparison; sufficient per task spec ("minimal effort").
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")

    if not hmac.compare_digest(credentials.credentials, settings.api_bearer_token):
        raise UnauthorizedError("Invalid bearer token")


BearerAuth = Depends(require_bearer_token)
