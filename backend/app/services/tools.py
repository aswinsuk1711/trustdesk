import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ToolCall


class ToolService:
    SENSITIVE_TOOLS = {"start_refund_review", "create_replacement_order", "create_coupon"}

    def _get_or_create(self, db: Session, ticket_id: str, tool_name: str, idempotency_key: str, result: dict) -> ToolCall:
        existing = db.scalar(select(ToolCall).where(ToolCall.idempotency_key == idempotency_key))
        if existing:
            return existing
        call = ToolCall(
            ticket_id=ticket_id,
            tool_name=tool_name,
            status="pending",
            idempotency_key=idempotency_key,
            result=json.dumps(result),
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    def start_refund_review(self, db: Session, ticket_id: str, idempotency_key: str, amount: float) -> ToolCall:
        return self._get_or_create(db, ticket_id, "start_refund_review", idempotency_key, {
            "message": "Refund review created for human processing.",
            "ticket_id": ticket_id, "amount": amount,
        })

    def create_replacement_order(self, db: Session, ticket_id: str, idempotency_key: str, product: str) -> ToolCall:
        return self._get_or_create(db, ticket_id, "create_replacement_order", idempotency_key, {
            "message": "Replacement order queued for human approval.",
            "ticket_id": ticket_id, "product": product,
        })

    def create_coupon(self, db: Session, ticket_id: str, idempotency_key: str, discount_pct: int) -> ToolCall:
        return self._get_or_create(db, ticket_id, "create_coupon", idempotency_key, {
            "message": "Coupon creation queued for human approval.",
            "ticket_id": ticket_id, "discount_pct": discount_pct,
        })
