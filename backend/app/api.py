import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Ticket, Customer, Order, Trace, ToolCall, EvalResult
from .schemas import (
    TicketOut, ContextOut, TriageOut, DraftOut, Citation,
    ApproveRequest, ActionOut, EvalSummary, EvalMetric
)
from .services.support import SupportService
from .services.guardrails import inspect_untrusted

router = APIRouter(prefix="/api")
DATA = Path(__file__).resolve().parents[1] / "data"


@router.get("/health")
def health():
    return {"status": "ok", "service": "trustdesk"}


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return list(db.scalars(select(Ticket).order_by(Ticket.created_at.desc())).all())


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.get("/tickets/{ticket_id}/context", response_model=ContextOut)
def get_context(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    customer = db.get(Customer, ticket.customer_id)
    order = db.get(Order, ticket.order_id) if ticket.order_id else None
    return {
        "customer": {
            "id": customer.id, "name": customer.name, "email": customer.email, "tier": customer.tier
        } if customer else {},
        "order": {
            "id": order.id, "product": order.product, "status": order.status,
            "total": order.total, "ordered_at": order.ordered_at
        } if order else None,
    }


@router.post("/tickets/{ticket_id}/triage", response_model=TriageOut)
def triage(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    category, priority, escalation, guardrail, trace = SupportService(db).triage(ticket)
    return {
        "category": category,
        "priority": priority,
        "escalation": escalation,
        "rationale": (
            f"Category={category}, priority={priority}. "
            f"Guardrail={guardrail}. Escalation is required when the request is unsafe, "
            f"security-sensitive, or urgent."
        ),
        "trace_id": trace.id,
    }


@router.post("/tickets/{ticket_id}/draft", response_model=DraftOut)
def draft(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    draft_text, hits, escalated, action, guardrail, trace = SupportService(db).draft(ticket)
    return {
        "draft": draft_text,
        "citations": [
            {"id": h.id, "title": h.title, "excerpt": h.content[:260]}
            for h in hits
        ],
        "escalated": escalated,
        "recommended_action": action,
        "guardrail": guardrail,
        "trace_id": trace.id,
    }


@router.get("/tickets/{ticket_id}/trace")
def get_trace(ticket_id: str, db: Session = Depends(get_db)):
    traces = list(db.scalars(
        select(Trace).where(Trace.ticket_id == ticket_id).order_by(Trace.created_at.desc())
    ).all())
    return [
        {
            "id": t.id,
            "run_type": t.run_type,
            "retrieved_doc_ids": json.loads(t.retrieved_doc_ids or "[]"),
            "tool_actions": json.loads(t.tool_actions or "[]"),
            "guardrail_result": t.guardrail_result,
            "final_status": t.final_status,
            "created_at": t.created_at,
        }
        for t in traces
    ]


@router.get("/actions/pending", response_model=list[ActionOut])
def pending_actions(db: Session = Depends(get_db)):
    return list(db.scalars(
        select(ToolCall).where(ToolCall.status == "pending").order_by(ToolCall.id.desc())
    ).all())


@router.post("/actions/{action_id}/approve", response_model=ActionOut)
def approve_action(action_id: int, body: ApproveRequest, db: Session = Depends(get_db)):
    action = db.get(ToolCall, action_id)
    if not action:
        raise HTTPException(404, "Action not found")

    existing = db.scalar(select(ToolCall).where(ToolCall.idempotency_key == body.idempotency_key))
    if existing and existing.id != action.id:
        return existing

    if action.status == "executed":
        return action

    action.status = "executed"
    action.result = json.dumps({
        "message": "Sensitive action approved and executed.",
        "tool": action.tool_name,
        "ticket_id": action.ticket_id,
    })
    action.idempotency_key = body.idempotency_key
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


@router.post("/evaluations/run", response_model=EvalSummary)
def run_evaluation(db: Session = Depends(get_db)):
    cases = []
    with (DATA / "eval_cases.jsonl").open() as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    service = SupportService(db)
    triage_hits = citation_hits = unsafe_blocked = escalation_hits = 0
    total = len(cases)

    for case in cases:
        ticket = db.get(Ticket, case["ticket_id"])
        if not ticket:
            continue
        category, priority, escalation, guardrail, trace = service.triage(ticket)
        expected = case.get("expected", {})

        if category == expected.get("category") and priority == expected.get("priority"):
            triage_hits += 1

        draft_text, hits, escalated, action, guardrail2, trace2 = service.draft(ticket)
        if expected.get("requires_citation", False) and hits:
            citation_hits += 1
        elif not expected.get("requires_citation", False):
            citation_hits += 1

        if expected.get("unsafe", False) and guardrail2 != "passed":
            unsafe_blocked += 1

        if escalated == expected.get("escalation", False):
            escalation_hits += 1

    metrics = [
        EvalMetric(metric="triage_accuracy", value=triage_hits / total if total else 0, details=f"{triage_hits}/{total}"),
        EvalMetric(metric="citation_coverage", value=citation_hits / total if total else 0, details=f"{citation_hits}/{total}"),
        EvalMetric(metric="unsafe_action_blocking", value=unsafe_blocked / total if total else 0, details=f"{unsafe_blocked}/{total}"),
        EvalMetric(metric="escalation_behavior", value=escalation_hits / total if total else 0, details=f"{escalation_hits}/{total}"),
    ]

    for m in metrics:
        db.add(EvalResult(metric=m.metric, value=m.value, details=m.details))
    db.commit()

    return {"metrics": metrics, "overall": {"cases": total}}


@router.get("/evaluations/latest")
def latest_evaluation(db: Session = Depends(get_db)):
    rows = list(db.scalars(select(EvalResult).order_by(EvalResult.created_at.desc()).limit(20)).all())
    return [
        {"metric": r.metric, "value": r.value, "details": r.details, "created_at": r.created_at}
        for r in rows
    ]
