from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models import RoleEnum, CaseStatus, Severity


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.viewer


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Case ----------
class CaseCreate(BaseModel):
    case_id: str
    title: str
    crime_type: str
    district: str
    station_name: str
    status: CaseStatus = CaseStatus.open
    severity: Severity = Severity.medium
    incident_date: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    summary: Optional[str] = None


class CaseOut(BaseModel):
    id: str
    case_id: str
    title: str
    crime_type: str
    district: str
    station_name: str
    status: CaseStatus
    severity: Severity
    incident_date: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[CaseOut]


# ---------- Person / Evidence (for case detail) ----------
class PersonOut(BaseModel):
    id: str
    name: str
    role_in_case: Optional[str]
    phone_number: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class EvidenceOut(BaseModel):
    id: str
    description: str
    evidence_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class CaseDetailOut(CaseOut):
    persons: List[PersonOut] = []
    evidence: List[EvidenceOut] = []


class MapCase(BaseModel):
    id: str
    case_id: str
    title: str
    crime_type: str
    district: str
    status: CaseStatus
    severity: Severity
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True


# ---------- Chat / RAG ----------
class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[str] = None  # JSON-encoded list of {case_id, case_code, snippet, score}
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str
    language: str = "en"  # "en" or "kn" (Kannada)


class ChatAnswer(BaseModel):
    session_id: str
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut


# ---------- Dashboard ----------
class CrimeTypeCount(BaseModel):
    crime_type: str
    count: int


class DistrictCount(BaseModel):
    district: str
    count: int


class DashboardStats(BaseModel):
    total_cases: int
    open_cases: int
    closed_cases: int
    under_review_cases: int
    crime_type_distribution: List[CrimeTypeCount]
    district_summary: List[DistrictCount]
    recent_alerts: List[CaseOut]
