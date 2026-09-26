from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .seed import seed
from .api import router

app = FastAPI(
    title="TrustDesk API",
    version="1.0.0",
    description="AI Support Operations Agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    seed()


app.include_router(router)
