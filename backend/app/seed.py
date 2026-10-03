import json
from pathlib import Path

from sqlalchemy import select

from .database import Base, engine, SessionLocal
from .models import KnowledgeDocument


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.scalar(select(KnowledgeDocument.id).limit(1)):
            return
        for row in json.loads((DATA / "knowledge_base.json").read_text()):
            db.add(KnowledgeDocument(**row))
        db.commit()
    finally:
        db.close()