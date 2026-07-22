import json
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, rag, llm

router = APIRouter(prefix="/api/chat", tags=["chat"])

CASE_CODE_RE = re.compile(r"\bCR-\d{4}-\d{4}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\- ]{6,}\d")


def _deep_search(db: Session, query: str, top_k: int = 8):
    """
    Merge three retrieval strategies for a richer, investigator-grade search:
    1. TF-IDF similarity over all case text (broad recall)
    2. Exact case-ID mentions in the query (direct lookup)
    3. Phone-number mentions in the query (direct person/case lookup)

    Each hit is tagged with a match_type so the UI can show *why* it was
    retrieved (explainable AI, not a black box).
    """
    seen_chunk_ids = set()
    combined = []

    # 1. Direct case-ID mentions
    for code in CASE_CODE_RE.findall(query):
        case = db.query(models.Case).filter(models.Case.case_id.ilike(code)).first()
        if case:
            for chunk in rag.get_case_chunks(case.id):
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    combined.append((chunk, 1.0, "direct_case_id"))

    # 2. Phone-number mentions -> find matching persons, pull in their cases
    for phone_match in PHONE_RE.findall(query):
        digits = re.sub(r"\D", "", phone_match)
        if len(digits) < 7:
            continue
        persons = db.query(models.Person).filter(models.Person.phone_number.ilike(f"%{digits[-8:]}%")).all()
        for person in persons:
            for chunk in rag.get_case_chunks(person.case_id):
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    combined.append((chunk, 0.95, "phone_match"))

    # 3. Broad TF-IDF similarity search
    for chunk, score in rag.retrieve(query, top_k=top_k):
        if chunk.chunk_id not in seen_chunk_ids:
            seen_chunk_ids.add(chunk.chunk_id)
            combined.append((chunk, score, "similarity"))

    combined.sort(key=lambda x: x[1], reverse=True)
    return combined[:top_k]


@router.post("/reindex")
def reindex(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "analyst")),
):
    """Rebuild the RAG search index from current case data."""
    count = rag.build_index(db)
    return {"indexed_chunks": count}


@router.post("/sessions", response_model=schemas.ChatSessionOut)
def create_session(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    session = models.ChatSession(user_id=current_user.id, title="New conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[schemas.ChatSessionOut])
def list_sessions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.created_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}/messages", response_model=list[schemas.ChatMessageOut])
def get_messages(
    session_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    session = _get_owned_session(db, session_id, current_user)
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )


@router.post("/sessions/{session_id}/messages", response_model=schemas.ChatAnswer)
def send_message(
    session_id: str,
    payload: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = _get_owned_session(db, session_id, current_user)

    user_msg = models.ChatMessage(session_id=session.id, role="user", content=payload.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Auto-title the session from the first question
    if session.title == "New conversation":
        session.title = payload.content[:60]
        db.commit()

    # Build/lazily use the RAG index
    if not rag._chunks:
        rag.build_index(db)
    hits = _deep_search(db, payload.content, top_k=8)

    sources = [
        {
            "case_id": chunk.case_id,
            "case_code": chunk.case_code,
            "section": chunk.section,
            "snippet": chunk.text[:400],
            "score": round(score, 3),
            "match_type": match_type,
        }
        for chunk, score, match_type in hits
    ]

    if not hits:
        answer_text = (
            "I couldn't find any case data matching that question. Try rephrasing, "
            "or ask about a specific case ID, district, or crime type."
        )
    else:
        try:
            answer_text = llm.generate_answer(
                payload.content, [s["snippet"] for s in sources], language=payload.language
            )
        except llm.LLMNotConfigured as e:
            top_lines = "\n".join(f"- {s['case_code']}: {s['snippet']}" for s in sources)
            answer_text = (
                f"(AI generation unavailable: {e})\n\nHere are the most relevant cases I found:\n{top_lines}"
            )

    assistant_msg = models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        sources=json.dumps(sources),
    )
    db.add(assistant_msg)

    log = models.AuditLog(user_id=current_user.id, action="chat_query", detail=payload.content[:200])
    db.add(log)
    db.commit()
    db.refresh(assistant_msg)

    return schemas.ChatAnswer(session_id=session.id, user_message=user_msg, assistant_message=assistant_msg)


def _get_owned_session(db: Session, session_id: str, user: models.User) -> models.ChatSession:
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session
