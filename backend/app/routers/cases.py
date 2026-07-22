from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas, auth, rag

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=schemas.CaseListResponse)
def list_cases(
    q: Optional[str] = Query(None, description="Free text search across case id, title, station"),
    district: Optional[str] = None,
    crime_type: Optional[str] = None,
    status: Optional[models.CaseStatus] = None,
    severity: Optional[models.Severity] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Case)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.Case.case_id.ilike(like),
                models.Case.title.ilike(like),
                models.Case.station_name.ilike(like),
            )
        )
    if district:
        query = query.filter(models.Case.district == district)
    if crime_type:
        query = query.filter(models.Case.crime_type == crime_type)
    if status:
        query = query.filter(models.Case.status == status)
    if severity:
        query = query.filter(models.Case.severity == severity)
    if date_from:
        query = query.filter(models.Case.incident_date >= date_from)
    if date_to:
        query = query.filter(models.Case.incident_date <= date_to)

    total = query.count()
    results = (
        query.order_by(models.Case.incident_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return schemas.CaseListResponse(total=total, page=page, page_size=page_size, results=results)


@router.get("/map", response_model=list[schemas.MapCase])
def map_cases(
    district: Optional[str] = None,
    crime_type: Optional[str] = None,
    status: Optional[models.CaseStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Case).filter(
        models.Case.latitude.isnot(None), models.Case.longitude.isnot(None)
    )
    if district:
        query = query.filter(models.Case.district == district)
    if crime_type:
        query = query.filter(models.Case.crime_type == crime_type)
    if status:
        query = query.filter(models.Case.status == status)
    return query.all()


@router.get("/{case_id}", response_model=schemas.CaseDetailOut)
def get_case(case_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/{case_id}/similar")
def similar_cases(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not rag._chunks:
        rag.build_index(db)

    hits = rag.similar_to_case(case_id, top_k=4)
    results = []
    for chunk, score in hits:
        similar = db.query(models.Case).filter(models.Case.id == chunk.case_id).first()
        if similar:
            results.append({
                "id": similar.id,
                "case_id": similar.case_id,
                "title": similar.title,
                "district": similar.district,
                "crime_type": similar.crime_type,
                "severity": similar.severity.value,
                "status": similar.status.value,
                "similarity": round(score, 3),
            })
    return results


@router.post("", response_model=schemas.CaseOut)
def create_case(
    payload: schemas.CaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("investigator", "admin")),
):
    existing = db.query(models.Case).filter(models.Case.case_id == payload.case_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="A case with this case_id already exists")

    case = models.Case(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)

    log = models.AuditLog(user_id=current_user.id, action="create_case", detail=f"Created case {case.case_id}")
    db.add(log)
    db.commit()

    rag.build_index(db)

    return case
