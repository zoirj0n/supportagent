import secrets
import warnings
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from ..config import settings
from ..deps import db_dep
from ..models.gmail_account import GmailAccount

router = APIRouter(prefix="/auth/google", tags=["auth"])

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


def _make_flow() -> Flow:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.OAUTH_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.OAUTH_REDIRECT_URI
    return flow


@router.get("/start")
def start_oauth():
    flow = _make_flow()

    state = secrets.token_urlsafe(16)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    print("OAuth redirect_uri ->", flow.redirect_uri)
    return RedirectResponse(auth_url)


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: Optional[str] = None,
    session: AsyncSession = Depends(db_dep),
):
    try:
        flow = _make_flow()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            flow.fetch_token(code=code)
        creds: Credentials = flow.credentials
        oauth2 = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        me = oauth2.userinfo().get().execute()
        gmail_address = me.get("email")
        granted_scopes = list(getattr(creds, "scopes", []) or [])
        google_user_id = me.get("id")

        if not gmail_address:
            raise HTTPException(
                status_code=400, detail="Could not read Google account email."
            )
        user_id = UUID("00000000-0000-0000-0000-000000000001")

        exp = getattr(creds, "expiry", None)

        if exp is None:
            token_expiry_dt = datetime.now(timezone.utc)
        else:
            token_expiry_dt = exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)

        # Keep existing refresh_token if Google didn't return one on reconnection
        existing = (
            await session.execute(
                select(GmailAccount).where(
                    (GmailAccount.gmail_address == gmail_address)
                    & (GmailAccount.user_id == user_id)
                )
            )
        ).scalar_one_or_none()

        refresh_token = creds.refresh_token or (
            existing.refresh_token if existing else ""
        )

        if existing:
            await session.execute(
                update(GmailAccount)
                .where(GmailAccount.id == existing.id)
                .values(
                    access_token=creds.token,
                    refresh_token=refresh_token,
                    token_expiry=token_expiry_dt,
                    is_active=True,
                    scopes=granted_scopes,
                    google_user_id=google_user_id,
                    disconnected_at=None,
                )
            )
        else:
            await session.execute(
                insert(GmailAccount).values(
                    id=secrets.token_hex(16),
                    user_id=user_id,
                    gmail_address=gmail_address,
                    access_token=creds.token,
                    refresh_token=refresh_token,
                    token_expiry=token_expiry_dt,
                    is_active=True,
                    scopes=granted_scopes,
                    google_user_id=google_user_id,
                )
            )

        await session.commit()
        frontend = settings.FRONTEND_URL.rstrip("/")

        return RedirectResponse(f"{frontend}", status_code=303)

    except Exception as e:
        print("OAuth callback failed:", repr(e))
        raise HTTPException(status_code=500, detail="OAuth callback failed")
