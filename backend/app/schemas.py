from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: str = Field(min_length=5, max_length=120)


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


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


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)
    customer_id: str | None = None
    order_id: str | None = None


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


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=120)
    tier: str = Field(default="standard", pattern="^(standard|gold|platinum)$")


class CustomerOut(BaseModel):
    id: str
    name: str
    email: str
    tier: str
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_id: str
    product: str = Field(min_length=1, max_length=200)
    status: str = Field(default="delivered", pattern="^(pending|shipped|delivered|completed|cancelled)$")
    total: float = Field(gt=0)
    ordered_at: datetime


class OrderOut(BaseModel):
    id: str
    customer_id: str
    product: str
    status: str
    total: float
    ordered_at: datetime
    model_config = {"from_attributes": True}
