import logging
from collections.abc import Iterable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import settings

logger = logging.getLogger(__name__)

LOCAL_HOSTS = ("127.0.0.1", "localhost")
LOCAL_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def normalize_origin(value: str) -> str:
    return value.strip().rstrip("/")


def allowed_origins() -> set[str]:
    origins = {normalize_origin(settings.frontend_origin), *LOCAL_ORIGINS}
    return {origin for origin in origins if origin}


def is_allowed_mutation(
    origin: str | None,
    sec_fetch_site: str | None,
    allowed: Iterable[str],
) -> bool:
    if origin is not None:
        return normalize_origin(origin) in set(allowed)
    # Las peticiones del servidor (SSR) y de herramientas locales no llevan
    # Origin. Solo rechazamos las que el navegador marca explícitamente como
    # cross-site y que, por tanto, no deberían poder cambiar datos.
    return sec_fetch_site != "cross-site"


def install_security(app: FastAPI) -> None:
    origins = allowed_origins()

    @app.middleware("http")
    async def reject_cross_site_mutations(request: Request, call_next):
        if request.method in MUTATING_METHODS and not is_allowed_mutation(
            request.headers.get("origin"),
            request.headers.get("sec-fetch-site"),
            origins,
        ):
            logger.warning(
                "Petición %s rechazada por origen no permitido: %s",
                request.method,
                request.headers.get("origin"),
            )
            return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
        return await call_next(request)

    # El orden importa: CORS queda en la capa exterior para que las respuestas
    # permitidas incluyan sus cabeceras, y TrustedHost corta el DNS rebinding
    # antes de llegar a los routers.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(LOCAL_HOSTS))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=600,
    )
