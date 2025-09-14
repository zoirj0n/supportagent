from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from ..models.order import Order
from ..models.refund_not_found import RefundNotFound
from ..models.unhandled_email import UnhandledEmail
from .responder import reply_refund_received, reply_ask_order_id, reply_invalid_order_id


async def handle_refund(
    session: AsyncSession, account, email_ctx, parsed_order_id: str | None
):
    if not parsed_order_id:
        await reply_ask_order_id(account, email_ctx)
        return

    order = (
        await session.execute(select(Order).where(Order.id == parsed_order_id))
    ).scalar_one_or_none()
    if order:
        await session.execute(
            update(Order)
            .where(Order.id == parsed_order_id)
            .values(status="refund_requested")
        )
        await session.commit()
        await reply_refund_received(account, email_ctx, parsed_order_id)
        return

    await reply_invalid_order_id(account, email_ctx, parsed_order_id)
    await session.execute(
        insert(RefundNotFound).values(
            gmail_account_id=email_ctx.get("gmail_account_id"),
            thread_id=email_ctx.get("thread_id"),
            email_msg_id=email_ctx.get("msg_id"),
            provided_text=parsed_order_id,
        )
    )
    await session.commit()
