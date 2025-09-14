from __future__ import annotations
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .deps import db_dep
from .models.gmail_account import GmailAccount
from .models.order import Order
from .models.email_log import EmailLog
from .models.refund_not_found import RefundNotFound
from .models.unhandled_email import UnhandledEmail
from .models.rag import RAGDocument
from .models.rag_chunk import RAGChunk
from .schemas import (
    GmailAccountOut,
    OrderOut,
    EmailLogOut,
    RefundNotFoundOut,
    UnhandledEmailOut,
    RAGDocumentOut,
    RAGChunkOut,
    Page,
    PageMeta,
)

router = APIRouter(prefix="/admin", tags=["Admin / Data"])


def _meta(total: int, limit: int, offset: int) -> PageMeta:
    return PageMeta(total=total, limit=limit, offset=offset)


# ---------- Accounts ----------
@router.get("/accounts", response_model=Page, summary="List Gmail accounts")
async def admin_list_accounts(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
):
    q = select(GmailAccount)
    if is_active is not None:
        q = q.where(GmailAccount.is_active == is_active)
    total = await session.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        (
            await session.execute(
                q.order_by(desc(GmailAccount.created_at)).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )

    items = [
        GmailAccountOut(
            id=a.id,
            gmail_address=a.gmail_address,
            is_active=a.is_active,
            connected_at=a.created_at,
            disconnected_at=a.disconnected_at,
            token_expiry=a.token_expiry,
            history_id=a.history_id,
            google_user_id=a.google_user_id,
            scopes=a.scopes,
        ).dict()
        for a in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


# ---------- Orders ----------
@router.get("/orders", response_model=Page, summary="List orders")
async def admin_list_orders(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    email: Optional[str] = Query(None, alias="user_email"),
    q: Optional[str] = Query(None, description="Search in id or user_email"),
):
    conds = []
    base = select(Order)
    if status:
        conds.append(Order.status == status)
    if email:
        conds.append(Order.user_email == email)
    if q:
        ilike = f"%{q}%"
        conds.append(and_((Order.id.ilike(ilike)) | (Order.user_email.ilike(ilike))))

    if conds:
        base = base.where(and_(*conds))

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(desc(Order.created_at)).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        OrderOut(
            id=o.id, user_email=o.user_email, status=o.status, created_at=o.created_at
        ).dict()
        for o in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


# ---------- Email logs ----------
@router.get("/email-logs", response_model=Page, summary="List email logs")
async def admin_list_email_logs(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    order_id: Optional[str] = Query(None),
    handled: Optional[bool] = Query(None, description="Filter by is_handled"),
    since: Optional[datetime] = Query(None, description="ISO timestamp lower bound"),
    until: Optional[datetime] = Query(None, description="ISO timestamp upper bound"),
    q: Optional[str] = Query(None, description="Search in subject/snippet"),
):
    base = select(EmailLog)
    conds = []
    if category:
        conds.append(EmailLog.category == category)
    if thread_id:
        conds.append(EmailLog.thread_id == thread_id)
    if order_id:
        conds.append(EmailLog.order_id == order_id)
    if handled is not None:
        conds.append(EmailLog.is_handled == handled)
    if since:
        conds.append(EmailLog.received_at >= since)
    if until:
        conds.append(EmailLog.received_at <= until)
    if q:
        ilike = f"%{q}%"
        conds.append((EmailLog.subject.ilike(ilike)) | (EmailLog.snippet.ilike(ilike)))
    if conds:
        base = base.where(and_(*conds))

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(desc(EmailLog.received_at), desc(EmailLog.id))
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        EmailLogOut(
            id=e.id,
            gmail_account_id=e.gmail_account_id,
            gmail_msg_id=e.gmail_msg_id,
            thread_id=e.thread_id,
            from_email=e.from_email,
            to_email=e.to_email,
            subject=e.subject,
            snippet=e.snippet,
            received_at=e.received_at,
            category=e.category,
            order_id=e.order_id,
            is_handled=e.is_handled,
            created_at=e.created_at,
        ).dict()
        for e in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


# ---------- Refund Not Found ----------
@router.get(
    "/refund-not-found", response_model=Page, summary="List refund requests not found"
)
async def admin_list_refund_nf(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    thread_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search in provided_text"),
):
    base = select(RefundNotFound)
    if thread_id:
        base = base.where(RefundNotFound.thread_id == thread_id)
    if q:
        base = base.where(RefundNotFound.provided_text.ilike(f"%{q}%"))

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(desc(RefundNotFound.id)).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        RefundNotFoundOut(
            id=r.id,
            gmail_account_id=r.gmail_account_id,
            thread_id=r.thread_id,
            email_msg_id=r.email_msg_id,
            provided_text=r.provided_text,
            created_at=r.created_at,
        ).dict()
        for r in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


# ---------- Unhandled ----------
@router.get("/unhandled-emails", response_model=Page, summary="List unhandled emails")
async def admin_list_unhandled(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    reason: Optional[str] = Query(None),
    importance: Optional[str] = Query(None),
):
    base = select(UnhandledEmail)
    if reason:
        base = base.where(UnhandledEmail.reason == reason)
    if importance:
        base = base.where(UnhandledEmail.importance == importance)

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(desc(UnhandledEmail.id)).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        UnhandledEmailOut(
            id=u.id,
            gmail_account_id=u.gmail_account_id,
            email_msg_id=u.email_msg_id,
            thread_id=u.thread_id,
            reason=u.reason,
            importance=u.importance,
            created_at=u.created_at,
        ).dict()
        for u in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


# ---------- RAG ----------
@router.get("/rag/documents", response_model=Page, summary="List RAG documents")
async def admin_list_rag_docs(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search in title/content"),
):
    base = select(RAGDocument)
    if tag:
        base = base.where(func.array_position(RAGDocument.tags, tag) != None)
    if q:
        ilike = f"%{q}%"
        base = base.where(
            (RAGDocument.title.ilike(ilike)) | (RAGDocument.content.ilike(ilike))
        )

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(desc(RAGDocument.id)).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        RAGDocumentOut(
            id=d.id,
            title=d.title,
            content=d.content,
            tags=d.tags,
            created_at=d.created_at,
        ).dict()
        for d in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}


@router.get("/rag/chunks", response_model=Page, summary="List RAG chunks")
async def admin_list_rag_chunks(
    session: AsyncSession = Depends(db_dep),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    doc_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search in content"),
):
    base = select(RAGChunk)
    if doc_id:
        base = base.where(RAGChunk.doc_id == doc_id)
    if tag:
        base = base.where(func.array_position(RAGChunk.tags, tag) != None)
    if q:
        base = base.where(RAGChunk.content.ilike(f"%{q}%"))

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        (
            await session.execute(
                base.order_by(RAGChunk.doc_id, RAGChunk.chunk_index)
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        RAGChunkOut(
            id=c.id,
            doc_id=c.doc_id,
            content=c.content,
            tags=c.tags,
            chunk_index=c.chunk_index,
            created_at=c.created_at,
        ).dict()
        for c in rows
    ]
    return {"items": items, "meta": _meta(total, limit, offset).dict()}
