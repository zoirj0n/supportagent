from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Page(BaseModel):
    items: list
    meta: PageMeta


class GmailAccountOut(BaseModel):
    id: str
    gmail_address: str
    is_active: bool
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    token_expiry: Optional[datetime] = None
    history_id: Optional[str] = None
    google_user_id: Optional[str] = None
    scopes: Optional[List[str]] = None


class OrderOut(BaseModel):
    id: str
    user_email: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class EmailLogOut(BaseModel):
    id: int
    gmail_account_id: str
    gmail_msg_id: str
    thread_id: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    subject: Optional[str] = None
    snippet: Optional[str] = None
    received_at: Optional[datetime] = None
    category: Optional[str] = None
    order_id: Optional[str] = None
    is_handled: bool
    created_at: Optional[datetime] = None


class RefundNotFoundOut(BaseModel):
    id: int
    gmail_account_id: str
    thread_id: Optional[str] = None
    email_msg_id: Optional[str] = None
    provided_text: Optional[str] = None
    created_at: Optional[datetime] = None


class UnhandledEmailOut(BaseModel):
    id: int
    gmail_account_id: str
    email_msg_id: Optional[str] = None
    thread_id: Optional[str] = None
    reason: Optional[str] = None
    importance: Optional[str] = None
    created_at: Optional[datetime] = None


class RAGDocumentOut(BaseModel):
    id: int
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class RAGChunkOut(BaseModel):
    id: int
    doc_id: int
    content: str
    tags: Optional[List[str]] = None
    chunk_index: Optional[int] = None
    created_at: Optional[datetime] = None
