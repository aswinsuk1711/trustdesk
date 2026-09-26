import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ToolCall


class ToolService:
    SENSITIVE_TOOLS = {"start_refund_review", "create_replacement_order"}

    def start_refund_review(
        self, db: Session, ticket_id: str, idempotency_key: str, amount: float
    ) -> ToolCall:
        existing = db.scalar(select(ToolCall).where(ToolCall.idempotency_key == idempotency_key))
        if existing:
            return existing

        call = ToolCall(
            ticket_id=ticket_id,
            tool_name="start_refund_review",
            status="executed",
            idempotency_key=idempotency_key,
            result=json.dumps({
                "message": "Refund review created for human processing.",
                "ticket_id": ticket_id,
                "amount": amount,
            }),
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return call
