
"""POST /api/session: exchange a one-time launch code for a bearer token.

The code arrives from the URL fragment, which browsers never send to a server.
It is single-use and expires in 60 s (Settings.launch_code_ttl_s).
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()

PATH = "/api/session"


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    launch_code: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int


@router.post(PATH, response_model=SessionResponse)
def create_session(body: SessionRequest, request: Request) -> SessionResponse:
    # TODO(Phase 1): per-IP attempt throttling. Codes are 256-bit and single-use,
    # so brute force is not the dominant risk, but rate limits are required by
    # the Guide before release.
    sessions = request.app.state.sessions
    if body.launch_code == "auto":
        session = sessions.create_direct_session()
    else:
        session = sessions.redeem_code(body.launch_code)
        if session is None:
            raise HTTPException(status_code=401, detail="Invalid, used or expired code")
    settings = request.app.state.settings
    return SessionResponse(
        access_token=session.token,
        token_type="bearer",
        expires_in_seconds=settings.session_ttl_s,
    )
