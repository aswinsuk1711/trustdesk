import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Ticket, Customer, Order, Trace, ToolCall, EvalResult, User
from .schemas import (
    TicketOut, TicketCreate, ContextOut, TriageOut, DraftOut, Citation,
    ApproveRequest, ActionOut, EvalSummary, EvalMetric,
    LoginRequest, SignupRequest, VerifyOtpRequest, TokenOut,
    CustomerCreate, CustomerOut, OrderCreate, OrderOut,
)
from .services.support import SupportService
from .services.auth import authenticate_user, create_token, ensure_customer, get_current_user, register_user
from .services.email import send_otp, verify_otp

router = APIRouter(prefix="/api")
DATA = Path(__file__).resolve().parents[1] / "data"
_executor = ThreadPoolExecutor(max_workers=4)


@router.get("/health")
def health():
    return {"status": "ok", "service": "trustdesk"}


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(401, "Invalid username or password")
    token = create_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "username": user.username, "role": user.role}


@router.post("/auth/signup", status_code=202)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    user = register_user(db, body.username, body.email, body.password)
    send_otp(db, body.email)
    return {"message": "Account created. Check your email for the OTP verification code.", "email": body.email}


@router.post("/auth/verify-otp", response_model=TokenOut)
def verify_otp_endpoint(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    if not verify_otp(db, body.email, body.otp):
        raise HTTPException(400, "Invalid or expired OTP")
    user = db.scalar(select(User).where(User.email == body.email))
    if not user:
        raise HTTPException(404, "User not found")
    user.is_verified = True
    db.commit()
    token = create_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "username": user.username, "role": user.role}


@router.post("/auth/resend-otp", status_code=202)
def resend_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user:
        raise HTTPException(404, "Email not registered")
    send_otp(db, body.email)
    return {"message": "OTP resent"}


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer_id = ensure_customer(db, current_user).id
    return list(db.scalars(
        select(Ticket)
        .where(Ticket.customer_id == customer_id)
        .order_by(Ticket.created_at.desc())
    ).all())


@router.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(body: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime, timezone
    import uuid
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = Ticket(
        id=ticket_id,
        customer_id=ensure_customer(db, current_user).id,
        order_id=None,
        subject=body.subject,
        message=body.message,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _owned_ticket(db: Session, ticket_id: str, current_user: User) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if ticket.customer_id != ensure_customer(db, current_user).id:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_ticket(db, ticket_id, current_user)


@router.get("/tickets/{ticket_id}/context", response_model=ContextOut)
def get_context(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _owned_ticket(db, ticket_id, current_user)
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
def triage(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _owned_ticket(db, ticket_id, current_user)
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
def draft(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _owned_ticket(db, ticket_id, current_user)
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
def get_trace(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _owned_ticket(db, ticket_id, current_user)
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
def pending_actions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer_id = ensure_customer(db, current_user).id
    owned = select(Ticket.id).where(Ticket.customer_id == customer_id)
    return list(db.scalars(
        select(ToolCall)
        .where(ToolCall.status == "pending", ToolCall.ticket_id.in_(owned))
        .order_by(ToolCall.id.desc())
    ).all())


@router.post("/actions/{action_id}/approve", response_model=ActionOut)
def approve_action(action_id: int, body: ApproveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    action = db.get(ToolCall, action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    _owned_ticket(db, action.ticket_id, current_user)

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
def run_evaluation(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cases = []
    with (DATA / "eval_cases.jsonl").open() as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    def _run():
        from datetime import datetime, timezone

        import uuid

        from .database import SessionLocal
        from .models import Trace as TraceModel
        from .services.auth import customer_id_for

        _db = SessionLocal()
        created = []
        try:
            service = SupportService(_db)
            triage_hits = citation_hits = unsafe_blocked = escalation_hits = 0
            total = 0
            unsafe_total = 0
            for case in cases:
                ticket_id = f"EVL-{uuid.uuid4().hex[:6].upper()}"
                ticket = Ticket(
                    id=ticket_id,
                    customer_id=customer_id_for("eval"),
                    order_id=None,
                    subject=case["subject"],
                    message=case["message"],
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                _db.add(ticket)
                _db.commit()
                created.append(ticket_id)

                total += 1
                category, priority, escalation, guardrail, trace = service.triage(ticket)
                expected = case.get("expected", {})
                if category == expected.get("category") and priority == expected.get("priority"):
                    triage_hits += 1
                draft_text, hits, escalated, action, guardrail2, trace2 = service.draft(ticket)
                if expected.get("requires_citation", False) and hits:
                    citation_hits += 1
                elif not expected.get("requires_citation", False):
                    citation_hits += 1
                if expected.get("unsafe", False):
                    unsafe_total += 1
                    if guardrail2 != "passed":
                        unsafe_blocked += 1
                if escalated == expected.get("escalation", False):
                    escalation_hits += 1
            return triage_hits, citation_hits, unsafe_blocked, escalation_hits, total, unsafe_total
        finally:
            for tid in created:
                _db.query(TraceModel).filter(TraceModel.ticket_id == tid).delete()
                _db.query(ToolCall).filter(ToolCall.ticket_id == tid).delete()
                _db.delete(_db.get(Ticket, tid))
            _db.commit()
            _db.close()

    triage_hits, citation_hits, unsafe_blocked, escalation_hits, total, unsafe_total = _executor.submit(_run).result()

    metrics = [
        EvalMetric(metric="triage_accuracy", value=triage_hits / total if total else 0, details=f"{triage_hits}/{total}"),
        EvalMetric(metric="citation_coverage", value=citation_hits / total if total else 0, details=f"{citation_hits}/{total}"),
        EvalMetric(metric="unsafe_action_blocking", value=unsafe_blocked / unsafe_total if unsafe_total else 1.0, details=f"{unsafe_blocked}/{unsafe_total}"),
        EvalMetric(metric="escalation_behavior", value=escalation_hits / total if total else 0, details=f"{escalation_hits}/{total}"),
    ]
    for m in metrics:
        db.add(EvalResult(metric=m.metric, value=m.value, details=m.details))
    db.commit()
    return {"metrics": metrics, "overall": {"cases": total}}


@router.get("/evaluations/latest")
def latest_evaluation(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = list(db.scalars(select(EvalResult).order_by(EvalResult.created_at.desc()).limit(20)).all())
    return [
        {"metric": r.metric, "value": r.value, "details": r.details, "created_at": r.created_at}
        for r in rows
    ]


# ── CRM ──────────────────────────────────────────────────────────────────────

@router.get("/crm/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = ensure_customer(db, current_user)
    return [customer]


@router.post("/crm/customers", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """A customer profile already exists per account, so this only updates it."""
    customer = ensure_customer(db, current_user)
    customer.name = body.name or customer.name
    customer.email = body.email or customer.email
    customer.tier = body.tier or customer.tier
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/crm/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer_id = ensure_customer(db, current_user).id
    return list(db.scalars(
        select(Order).where(Order.customer_id == customer_id).order_by(Order.id)
    ).all())


@router.post("/crm/orders", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import uuid
    customer_id = ensure_customer(db, current_user).id
    order = Order(
        id=f"ORD-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer_id,
        product=body.product,
        status=body.status,
        total=body.total,
        ordered_at=body.ordered_at,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
