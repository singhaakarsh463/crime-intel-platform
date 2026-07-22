import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    investigator = "investigator"
    analyst = "analyst"
    admin = "admin"
    viewer = "viewer"


class CaseStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    under_review = "under_review"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat_sessions = relationship("ChatSession", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, unique=True, index=True, nullable=False)  # human-readable e.g. CR-2026-0001
    title = Column(String, nullable=False)
    crime_type = Column(String, index=True, nullable=False)
    district = Column(String, index=True, nullable=False)
    station_name = Column(String, nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.open, index=True)
    severity = Column(Enum(Severity), default=Severity.medium, index=True)
    incident_date = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    persons = relationship("Person", back_populates="case")
    evidence = relationship("Evidence", back_populates="case")


class Person(Base):
    __tablename__ = "persons"

    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    name = Column(String, nullable=False)
    role_in_case = Column(String, nullable=True)  # suspect / witness / victim
    phone_number = Column(String, nullable=True, index=True)
    identifier_hash = Column(String, nullable=True)  # for linking across cases without storing raw PII
    notes = Column(Text, nullable=True)

    case = relationship("Case", back_populates="persons")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    description = Column(String, nullable=False)
    evidence_hash = Column(String, nullable=False)  # integrity hash
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="evidence")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON-encoded citation list
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
