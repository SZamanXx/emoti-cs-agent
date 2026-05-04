"""Login endpoint that trades demo credentials for a JWT bearer token.

For the demo, a single operator account is provisioned via env (`OPERATOR_USERNAME` /
`OPERATOR_PASSWORD`). Production would back this with the existing identity provider
(Auth0, Keycloak, Google Workspace, whatever Emoti uses internally).
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.security.jwt import JWT_DEFAULT_TTL_HOURS, issue_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str


def _expected_creds() -> tuple[str, str]:
    return (
        os.environ.get("OPERATOR_USERNAME", "operator"),
        os.environ.get("OPERATOR_PASSWORD", "operator-demo-pwd"),
    )


@router.post("/login", response_model=LoginOut)
async def login(payload: LoginIn) -> LoginOut:
    expected_user, expected_pwd = _expected_creds()
    if payload.username != expected_user or payload.password != expected_pwd:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = issue_token(subject=payload.username, role="operator")
    return LoginOut(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_DEFAULT_TTL_HOURS * 3600,
        role="operator",
    )
