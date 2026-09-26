from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    tier: Mapped[str] = mapped_column(String, default="standard")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    product: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    total: Mapped[float] = mapped_column(Float)
    ordered_at: Mapped[datetime] = mapped_column(DateTime)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[str | None] = mapped_column(String, nullable=True)
    escalation: Mapped[bool] = mapped_column(Boolean, default=False)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    unsafe: Mapped[bool] = mapped_column(Boolean, default=False)


class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String, index=True)
    tool_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)


class Trace(Base):
    __tablename__ = "traces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String, index=True)
    run_type: Mapped[str] = mapped_column(String)
    retrieved_doc_ids: Mapped[str] = mapped_column(Text, default="")
    tool_actions: Mapped[str] = mapped_column(Text, default="")
    guardrail_result: Mapped[str] = mapped_column(String, default="not_run")
    final_status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvalResult(Base):
    __tablename__ = "eval_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
