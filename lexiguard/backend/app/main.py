
"""FastAPI application factory (Guide 2, 11.2, 11.3, 13.2).

Implemented here:
  * loopback-only bind (enforced by the runner, not this module)
  * exact Host validation on every request
  * bearer-token auth on every /api/* route except /api/session
  * Origin validation on state-changing requests
  * CSP and no-store headers
  * one-time launch-code session bootstrap
Implemented routes: session, health, documents (upload/list/delete/pages/image),
ask, review, overview and evidence. Model calls go only to local Ollama.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import (
    ask,
    cuad,
    documents,
    evidence,
    health,
    india_law,
    models,
    overview,
    review,
    session,
)
from app.config import Settings, get_settings
from app.security.headers import no_store_headers, security_headers
from app.security.hosts import is_allowed_host
from app.security.origin import is_allowed_origin
from app.security.tokens import LaunchSessionStore

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


def _with_security_headers(payload: JSONResponse) -> JSONResponse:
    for name, value in security_headers().items():
        payload.headers.setdefault(name, value)
    return payload


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="GBDoc",
        version=__version__,
        docs_url=None,      # no interactive docs: smaller surface, no CDN assets
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.sessions = LaunchSessionStore(
        code_ttl_s=settings.launch_code_ttl_s,
        session_ttl_s=settings.session_ttl_s,
    )
    app.state.launch_code = app.state.sessions.issue_code()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    try:
        from app.model.factory import build_provider

        app.state.provider = build_provider(settings)
    except Exception:  # noqa: BLE001 - a broken provider must not stop the app booting
        app.state.provider = None

    @app.middleware("http")
    async def guard(request: Request, call_next):  # type: ignore[no-untyped-def]
        if not is_allowed_host(request.headers.get("host"), settings):
            return _with_security_headers(
                JSONResponse({"detail": "Host not allowed"}, status_code=403)
            )

        path = request.url.path
        if (
            path.startswith("/api/")
            and path != session.PATH
            and not app.state.sessions.validate(_bearer_token(request))
        ):
            response = JSONResponse(
                {"detail": "Unauthorised"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            return _with_security_headers(response)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not is_allowed_origin(
            request.headers.get("origin"), settings
        ):
            return _with_security_headers(
                JSONResponse({"detail": "Origin not allowed"}, status_code=403)
            )

        response = await call_next(request)
        for name, value in security_headers().items():
            response.headers.setdefault(name, value)
        if path.startswith("/api/"):
            for name, value in no_store_headers().items():
                response.headers[name] = value
        return response

    app.include_router(session.router)
    app.include_router(health.router)
    app.include_router(models.router)
    app.include_router(documents.router)
    app.include_router(ask.router)
    app.include_router(review.router)
    app.include_router(overview.router)
    app.include_router(evidence.router)
    app.include_router(cuad.router)
    app.include_router(india_law.router)

    if (FRONTEND_DIST / "index.html").exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(FRONTEND_DIST / "assets")),
            name="assets",
        )

        if (FRONTEND_DIST / "favicon.svg").exists():

            @app.api_route("/favicon.svg", methods=["GET", "HEAD"], include_in_schema=False)
            def favicon() -> FileResponse:
                return FileResponse(FRONTEND_DIST / "favicon.svg")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(FRONTEND_DIST / "index.html")

    else:

        @app.get("/", include_in_schema=False)
        def index_placeholder() -> JSONResponse:
            payload = JSONResponse(
                {
                    "application": "GBDoc",
                    "frontend_built": False,
                    "message": "Run `npm install && npm run build` to build the UI.",
                }
            )
            for name, value in security_headers().items():
                payload.headers.setdefault(name, value)
            return payload

    return app


app = create_app()
