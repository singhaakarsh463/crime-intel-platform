from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.routers import auth, cases, dashboard, export, chat, network, audit
from app import rag

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Crime Intelligence Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(export.router)
app.include_router(chat.router)
app.include_router(network.router)
app.include_router(audit.router)


@app.on_event("startup")
def _build_rag_index_on_startup():
    db = SessionLocal()
    try:
        rag.build_index(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}
