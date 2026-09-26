import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from .database import Base, engine, SessionLocal
from .models import Customer, Order, Ticket, KnowledgeDocument


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Customer.id).limit(1)):
            return

        for row in json.loads((DATA / "customers.json").read_text()):
            db.add(Customer(**row))

        for row in json.loads((DATA / "orders.json").read_text()):
            row["ordered_at"] = datetime.fromisoformat(row["ordered_at"])
            db.add(Order(**row))

        for row in json.loads((DATA / "tickets.json").read_text()):
            row["created_at"] = datetime.fromisoformat(row["created_at"])
            db.add(Ticket(**row))

        for row in json.loads((DATA / "knowledge_base.json").read_text()):
            db.add(KnowledgeDocument(**row))

        db.commit()
    finally:
        db.close()
