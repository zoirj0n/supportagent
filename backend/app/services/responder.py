import base64
import email
from email.utils import formatdate
from typing import Optional

from .gmail_client import send_reply, build_service


def _build_raw(
    to_email: str,
    subject: str,
    body_text: str,
    *,
    account_from: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> str:
    """
    Create a simple text/plain message that threads correctly:
      - From: (account's Gmail)
      - To:   parsed recipient
      - Subject: "Re: {subject}"
      - In-Reply-To / References: preserve thread
    """
    msg = email.message.EmailMessage()
    if account_from:
        msg["From"] = account_from
    msg["To"] = to_email
    msg["Subject"] = (
        f"Re: {subject}" if not subject.lower().startswith("re:") else subject
    )
    msg["Date"] = formatdate(localtime=True)

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        refs = references
        if in_reply_to and in_reply_to not in refs:
            refs = (refs + " " + in_reply_to).strip()
        msg["References"] = refs
    elif in_reply_to:
        msg["References"] = in_reply_to

    msg.set_content(body_text or "")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


async def reply_text(
    account,
    thread_id: str,
    to_email: str,
    subject: str,
    body: str,
    *,
    account_from: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
):
    """
    Send a threaded reply to the original sender. Raises on error so caller can decide to retry / keep unread.
    """
    service = build_service(account)
    raw = _build_raw(
        to_email,
        subject,
        body,
        account_from=account_from,
        in_reply_to=in_reply_to,
        references=references,
    )
    return send_reply(service, thread_id, raw)


async def reply_refund_received(account, email_ctx, order_id: str):
    body = f"Your refund request for {order_id} is received. We will process it within 3 business days."
    return await reply_text(
        account,
        email_ctx["thread_id"],
        email_ctx["recipient"],
        email_ctx["subject"],
        body,
        account_from=email_ctx.get("account_from"),
        in_reply_to=email_ctx.get("message_id"),
        references=email_ctx.get("references"),
    )


async def reply_ask_order_id(account, email_ctx):
    body = (
        "Please provide your Order ID (e.g., ORD-34567) so we can process your refund."
    )
    return await reply_text(
        account,
        email_ctx["thread_id"],
        email_ctx["recipient"],
        email_ctx["subject"],
        body,
        account_from=email_ctx.get("account_from"),
        in_reply_to=email_ctx.get("message_id"),
        references=email_ctx.get("references"),
    )


async def reply_invalid_order_id(account, email_ctx, order_id: str):
    body = (
        f"The Order ID '{order_id}' could not be found. Please double-check and resend."
    )
    return await reply_text(
        account,
        email_ctx["thread_id"],
        email_ctx["recipient"],
        email_ctx["subject"],
        body,
        account_from=email_ctx.get("account_from"),
        in_reply_to=email_ctx.get("message_id"),
        references=email_ctx.get("references"),
    )


async def reply_escalated(account, email_ctx):
    body = "Thanks for your question. We're escalating this to a specialist and will get back shortly."
    return await reply_text(
        account,
        email_ctx["thread_id"],
        email_ctx["recipient"],
        email_ctx["subject"],
        body,
        account_from=email_ctx.get("account_from"),
        in_reply_to=email_ctx.get("message_id"),
        references=email_ctx.get("references"),
    )
