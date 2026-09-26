from datetime import datetime
from pydantic import BaseModel, Field


class TicketOut(BaseModel):
    id: str
    customer_id: str
    order_id: str | None
    subject: str
    message: str
    created_at: datetime
    category: str | None
    priority: str | None
    escalation: bool

    model_config = {"from_attributes": True}


class ContextOut(BaseModel):
    customer: dict
    order: dict | None


class TriageOut(BaseModel):
    category: str
    priority: str
    escalation: bool
    rationale: str
    trace_id: int | None = None


class Citation(BaseModel):
    id: str
    title: str
    excerpt: str


class DraftOut(BaseModel):
    draft: str
    citations: list[Citation]
    escalated: bool
    recommended_action: str | None = None
    guardrail: str
    trace_id: int | None = None


class ApproveRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=128)


class ActionOut(BaseModel):
    id: int
    ticket_id: str
    tool_name: str
    status: str
    result: str | None
    idempotency_key: str

    model_config = {"from_attributes": True}


class EvalMetric(BaseModel):
    metric: str
    value: float
    details: str


class EvalSummary(BaseModel):
    metrics: list[EvalMetric]
    overall: dict
