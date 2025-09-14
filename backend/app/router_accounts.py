from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from .deps import db_dep
from .models.gmail_account import GmailAccount

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/")
async def list_accounts(session: AsyncSession = Depends(db_dep)):
    res = await session.execute(select(GmailAccount))
    accounts = res.scalars().all()
    return [
        {
            "id": a.id,
            "gmail_address": a.gmail_address,
            "is_active": a.is_active,
            "created_at": a.created_at,
            "connected_at": a.created_at,
            "token_expiry": a.token_expiry,
            "history_id": a.history_id,
            "disconnected_at": a.disconnected_at,
        }
        for a in accounts
    ]


@router.get("/{account_id}")
async def get_account(account_id: str, session: AsyncSession = Depends(db_dep)):
    acc = (
        await session.execute(select(GmailAccount).where(GmailAccount.id == account_id))
    ).scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "id": acc.id,
        "gmail_address": acc.gmail_address,
        "is_active": acc.is_active,
        "created_at": acc.created_at,
        "token_expiry": acc.token_expiry,
        "history_id": acc.history_id,
        "connected_at": acc.created_at,
        "disconnected_at": acc.disconnected_at,
        "scopes": acc.scopes or [],
    }


@router.delete("/{account_id}")
async def disconnect_account(account_id: str, session: AsyncSession = Depends(db_dep)):
    acc = (
        await session.execute(select(GmailAccount).where(GmailAccount.id == account_id))
    ).scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    await session.execute(
        update(GmailAccount)
        .where(GmailAccount.id == account_id)
        .values(is_active=False, disconnected_at=datetime.now(timezone.utc))
    )
    await session.commit()
    return {"ok": True}
