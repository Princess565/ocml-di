# database.py
"""
OCML-DI Database Layer
Owner: Efe Ikharo (Project Lead, ML/AI Systems)

Purpose:
    Local SQLite database for patients, audit logs, and governance reviews.
    Provides offline-first persistence with SQLAlchemy ORM.
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./ocml_di.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Patient Table ───────────────────────────────────────────────
class PatientDB(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    conditions = Column(JSON, default=[])
    medications = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Audit Log Table ─────────────────────────────────────────────
class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    actor_id = Column(String, nullable=True)
    patient_id = Column(String, nullable=True)
    patient_name = Column(String, nullable=True)
    channel = Column(String, default="dashboard")
    facility_id = Column(String, nullable=True)
    details = Column(JSON, default={})
    risk_score = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ── Clinical Review Table ───────────────────────────────────────
class ClinicalReviewDB(Base):
    __tablename__ = "clinical_reviews"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=True)
    patient_name = Column(String, nullable=True)
    proposed_drug = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    warning_summary = Column(String, nullable=False)
    status = Column(String, default="pending")
    assigned_to = Column(String, nullable=True)
    reviewed_by = Column(String, nullable=True)
    review_notes = Column(String, nullable=True)
    override_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)


# ── Init ───────────────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
