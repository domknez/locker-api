from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from parcel_locker.domain.exceptions import (
    ConflictError,
    DomainError,
    GeocodingError,
    NotFoundError,
    UnauthorizedError,
)


def _error(
    code: str,
    message: str,
    status_code: int,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UnauthorizedError)
    async def _unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return _error(
            "unauthorized",
            str(exc),
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return _error("not_found", str(exc), status.HTTP_404_NOT_FOUND)

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return _error("conflict", str(exc), status.HTTP_409_CONFLICT)

    @app.exception_handler(GeocodingError)
    async def _geocoding(_: Request, exc: GeocodingError) -> JSONResponse:
        return _error("geocoding_failed", str(exc), status.HTTP_502_BAD_GATEWAY)

    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return _error("domain_error", str(exc), status.HTTP_400_BAD_REQUEST)
