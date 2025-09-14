# backend/app/services/poller.py
from __future__ import annotations
import base64
import asyncio
from datetime import timezone
from email.utils import parsedate_to_datetime, parseaddr

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert  # << use PG upsert

from ..models.gmail_account import GmailAccount
from ..models.email_log import EmailLog
from ..models.unhandled_email import UnhandledEmail
from ..models.order import Order
from ..models.refund_not_found import RefundNotFound

from .gmail_client import build_service, list_unread, get_message, modify_labels
from .classifier import classify_email, extract_order_id
from .importance import score_importance
from . import rag
from .responder import (
    reply_text,
    reply_ask_order_id,
    reply_refund_received,
    reply_invalid_order_id,
    reply_escalated,
)


def _extract(headers: list[dict], key: str) -> str | None:
    for h in headers:
        if h.get("name") == key:
            return h.get("value")
    return None


def _b64url_decode(s: str) -> bytes:
    # Gmail uses base64url and may omit padding; add it if needed
    if not s:
        return b""
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _parse_body(payload) -> str:
    body_data = None

    # try flat text/plain first
    if payload.get("parts"):
        for p in payload["parts"]:
            if p.get("mimeType") == "text/plain" and p.get("body", {}).get("data"):
                body_data = p["body"]["data"]
                break

        # fallback: sometimes the text/plain is nested under multipart/alternative
        if not body_data:
            for p in payload["parts"]:
                if p.get("parts"):
                    for sub in p["parts"]:
                        if sub.get("mimeType") == "text/plain" and sub.get(
                            "body", {}
                        ).get("data"):
                            body_data = sub["body"]["data"]
                            break
                    if body_data:
                        break
    else:
        body_data = payload.get("body", {}).get("data")

    if body_data:
        try:
            return _b64url_decode(body_data).decode(errors="ignore")
        except Exception:
            return ""
    return ""


async def poll_once(session: AsyncSession):
    accounts = (
        (
            await session.execute(
                select(GmailAccount).where(GmailAccount.is_active == True)
            )
        )
        .scalars()
        .all()
    )

    for account in accounts:
        service = build_service(account)
        messages = list_unread(service, max_results=20)

        for m in messages:
            full = get_message(service, m["id"])
            payload = full.get("payload", {}) or {}
            headers = payload.get("headers", []) or []

            subject = _extract(headers, "Subject") or ""
            from_email_raw = _extract(headers, "From") or ""
            reply_to_raw = _extract(headers, "Reply-To") or from_email_raw
            to_email = _extract(headers, "To") or ""
            thread_id = full.get("threadId")
            body = _parse_body(payload)
            snippet = full.get("snippet", "")

            recipient = parseaddr(reply_to_raw)[1] or parseaddr(from_email_raw)[1] or ""

            message_id = _extract(headers, "Message-ID") or _extract(
                headers, "Message-Id"
            )
            references = _extract(headers, "References")

            # Build tz-aware datetime for TIMESTAMPTZ
            received_at = None
            date_hdr = _extract(headers, "Date")
            if date_hdr:
                try:
                    dt = parsedate_to_datetime(date_hdr)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    received_at = dt
                except Exception:
                    received_at = None

            category = classify_email(subject, body)
            parsed_order_id = extract_order_id(f"{subject} {body}")

            # --- Log the email (idempotent) ---
            # Avoid unique-constraint errors if we reprocess the same Gmail message.
            await session.execute(
                pg_insert(EmailLog)
                .values(
                    gmail_account_id=account.id,
                    gmail_msg_id=m["id"],
                    thread_id=thread_id,
                    from_email=from_email_raw,
                    to_email=to_email,
                    subject=subject,
                    snippet=snippet,
                    received_at=received_at,
                    category=category,
                    order_id=parsed_order_id,
                )
                .on_conflict_do_nothing(index_elements=["gmail_msg_id"])
            )
            await session.commit()

            email_ctx = {
                "thread_id": thread_id,
                "recipient": recipient,
                "from_email": from_email_raw,
                "subject": subject,
                "body": body,
                "msg_id": m["id"],
                "gmail_account_id": account.id,
                "message_id": message_id,
                "references": references,
                "account_from": account.gmail_address,
            }

            mark_read = True  # if a send fails, keep unread to retry next poll

            try:
                if category == "refund":
                    if parsed_order_id:
                        # ID present → check if it exists
                        order = (
                            await session.execute(
                                select(Order).where(Order.id == parsed_order_id)
                            )
                        ).scalar_one_or_none()

                        if order:
                            # Found → mark refund requested + confirm
                            await session.execute(
                                update(Order)
                                .where(Order.id == parsed_order_id)
                                .values(status="refund_requested")
                            )
                            await session.commit()
                            await reply_refund_received(
                                account, email_ctx, parsed_order_id
                            )
                            await session.execute(
                                update(EmailLog)
                                .where(EmailLog.gmail_msg_id == m["id"])
                                .values(is_handled=True)
                            )
                            await session.commit()

                        else:
                            # Not found → reply invalid, but only log on subsequent repeats
                            await reply_invalid_order_id(
                                account, email_ctx, parsed_order_id
                            )
                            await session.execute(
                                update(EmailLog)
                                .where(EmailLog.gmail_msg_id == m["id"])
                                .values(is_handled=True)
                            )
                            await session.commit()

                            # How many times THIS SAME ID appeared in THIS THREAD so far (incl. current)
                            occurrences = (
                                (
                                    await session.execute(
                                        select(EmailLog.id).where(
                                            EmailLog.thread_id == thread_id,
                                            EmailLog.category == "refund",
                                            EmailLog.order_id == parsed_order_id,
                                        )
                                    )
                                )
                                .scalars()
                                .all()
                            )

                            # If this invalid ID shows up again (2nd time or more), log it (de-duped)
                            if len(occurrences) >= 2:
                                exists_log = (
                                    await session.execute(
                                        select(RefundNotFound.id).where(
                                            RefundNotFound.thread_id == thread_id,
                                            RefundNotFound.provided_text
                                            == parsed_order_id,
                                        )
                                    )
                                ).scalar_one_or_none()
                                if not exists_log:
                                    await session.execute(
                                        pg_insert(RefundNotFound)
                                        .values(
                                            gmail_account_id=account.id,
                                            thread_id=thread_id,
                                            email_msg_id=m["id"],
                                            provided_text=parsed_order_id,
                                        )
                                        .on_conflict_do_nothing()
                                    )
                                    await session.commit()

                    else:
                        prior_ids = (
                            (
                                await session.execute(
                                    select(EmailLog.order_id).where(
                                        EmailLog.thread_id == thread_id,
                                        EmailLog.category == "refund",
                                        EmailLog.order_id.is_not(None),
                                    )
                                )
                            )
                            .scalars()
                            .all()
                        )

                        had_prior_invalid = False
                        for oid in {
                            oid for oid in prior_ids if oid
                        }:  # unique, non-null
                            exists = (
                                await session.execute(
                                    select(Order.id).where(Order.id == oid)
                                )
                            ).scalar_one_or_none()
                            if not exists:
                                had_prior_invalid = True
                                break

                        if had_prior_invalid:
                            snippet_text = (body or subject or "")[
                                :200
                            ] or "<no-id-reply>"
                            exists_log = (
                                await session.execute(
                                    select(RefundNotFound.id).where(
                                        RefundNotFound.thread_id == thread_id,
                                        RefundNotFound.provided_text == snippet_text,
                                    )
                                )
                            ).scalar_one_or_none()
                            if not exists_log:
                                await session.execute(
                                    pg_insert(RefundNotFound)
                                    .values(
                                        gmail_account_id=account.id,
                                        thread_id=thread_id,
                                        email_msg_id=m["id"],
                                        provided_text=snippet_text,
                                    )
                                    .on_conflict_do_nothing()
                                )
                                await session.commit()

                        # (Re)ask for the Order ID when none is present
                        await reply_ask_order_id(account, email_ctx)
                        await session.execute(
                            update(EmailLog)
                            .where(EmailLog.gmail_msg_id == m["id"])
                            .values(is_handled=True)
                        )
                        await session.commit()

                elif category == "question":
                    # Keep RAG behavior with escalation if we can't answer
                    handled = await rag.answer_or_escalate(session, account, email_ctx)
                    if handled:
                        await session.execute(
                            update(EmailLog)
                            .where(EmailLog.gmail_msg_id == m["id"])
                            .values(is_handled=True)
                        )
                        await session.commit()
                    else:
                        await session.execute(
                            pg_insert(UnhandledEmail)
                            .values(
                                gmail_account_id=account.id,
                                email_msg_id=m["id"],
                                thread_id=thread_id,
                                reason="RAG_no_answer",
                                importance="high",
                            )
                            .on_conflict_do_nothing()
                        )
                        await session.commit()

                else:
                    # Other / Nonsense with importance scoring
                    imp = score_importance(body)
                    await session.execute(
                        pg_insert(UnhandledEmail)
                        .values(
                            gmail_account_id=account.id,
                            email_msg_id=m["id"],
                            thread_id=thread_id,
                            reason="nonsense_or_other",
                            importance=imp,
                        )
                        .on_conflict_do_nothing()
                    )
                    await session.commit()
                await asyncio.sleep(0.15)

            except Exception as e:
                print(
                    f"[poll_once] send failed for msg {m['id']} in thread {thread_id}: {type(e).__name__}: {e}"
                )
                mark_read = False
            if mark_read:
                modify_labels(service, m["id"], remove_unread=True)
