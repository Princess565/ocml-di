# ── MVP Subset ────────────────────────────────────────────────
# These are minimal models for hackathon demo speed.
# Use them when OCML_MODE = "MVP"

class MVPPatient(BaseModel):
    full_name: str
    conditions: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []

class MVPDrugCheckRequest(BaseModel):
    proposed_drug: str
    patient: MVPPatient

class MVPDrugCheckResponse(BaseModel):
    proposed_drug: str
    interactions: list[str] = []
    risk_level: str = "low"

    def is_safe(self) -> bool:
        return len(self.interactions) == 0
"""
models.py
OCML-DI — Offline Clinical Memory Layer with Drug Interaction Intelligence

Owner:      Efe Ikharo (Project Lead, ML/AI Systems)
Purpose:    All Pydantic data models and schemas used across the system.
            Every other backend file imports from here.

Model hierarchy:
    Patient
        └── Medication (current medications)
        └── Condition (medical conditions)
        └── Allergy
        └── QRWallet (generated from patient record)

    DrugCheckRequest   → submitted by clinician/CHW
    DrugCheckResponse  ← returned by risk_engine
        └── InteractionResult (one per detected interaction)

    AuditLog           → written on every important action
    ClinicalReview     → created when governance requires human sign-off
    USSDSession        → tracks USSD access events

Usage:
    from backend.models import Patient, DrugCheckRequest, AuditLog
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW      = "low"
    MODERATE = "moderate"
    HIGH     = "high"
    CRITICAL = "critical"


class ReviewStatus(str, Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    OVERRIDDEN = "overridden"
    ESCALATED = "escalated"


class AuditAction(str, Enum):
    PATIENT_CREATED       = "patient_created"
    PATIENT_ACCESSED      = "patient_accessed"
    DRUG_CHECK_PERFORMED  = "drug_check_performed"
    CRITICAL_ALERT_RAISED = "critical_alert_raised"
    ALERT_OVERRIDDEN      = "alert_overridden"
    REVIEW_COMPLETED      = "review_completed"
    QR_WALLET_GENERATED   = "qr_wallet_generated"
    QR_WALLET_SCANNED     = "qr_wallet_scanned"
    USSD_CHECK_PERFORMED  = "ussd_check_performed"
    CHW_SYNC_EVENT        = "chw_sync_event"


class AccessChannel(str, Enum):
    DASHBOARD = "dashboard"
    USSD      = "ussd"
    QR_SCAN   = "qr_scan"
    API       = "api"


class Gender(str, Enum):
    MALE    = "male"
    FEMALE  = "female"
    OTHER   = "other"


# ── Sub-models ────────────────────────────────────────────────────────────────

class Medication(BaseModel):
    """A single medication in a patient's current medication list."""
    name:         str  = Field(..., min_length=1, max_length=200, description="Generic or brand drug name")
    dose:         Optional[str] = Field(None, description="e.g. '500mg twice daily'")
    prescribed_by: Optional[str] = Field(None, description="Prescribing clinician or facility")
    start_date:   Optional[datetime] = None

    model_config = {"str_strip_whitespace": True}


class Condition(BaseModel):
    """A single medical condition in a patient's history."""
    name:       str  = Field(..., min_length=1, max_length=200, description="Condition name e.g. 'Kidney Disease'")
    diagnosed:  Optional[datetime] = None
    severity:   Optional[str] = Field(None, description="mild / moderate / severe")
    notes:      Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class Allergy(BaseModel):
    """A known drug or substance allergy."""
    allergen:  str  = Field(..., min_length=1, max_length=200)
    reaction:  Optional[str] = Field(None, description="e.g. 'anaphylaxis', 'rash'")
    severity:  Optional[str] = Field(None, description="mild / moderate / severe / life-threatening")


class EmergencyContact(BaseModel):
    name:         str
    relationship: str
    phone:        str


# ── Core models ───────────────────────────────────────────────────────────────

class Patient(BaseModel):
    """
    Core patient record. Stored locally (SQLite) and encoded into QR wallet.
    Designed to be minimal — only clinically essential fields.
    """
    id:                  UUID     = Field(default_factory=uuid4)
    full_name:           str      = Field(..., min_length=2, max_length=200)
    date_of_birth:       Optional[datetime] = None
    gender:              Optional[Gender]   = None
    phone:               Optional[str]      = Field(None, description="Patient phone number")
    facility_id:         Optional[str]      = Field(None, description="Registering clinic/facility ID")
    chw_id:              Optional[str]      = Field(None, description="Community health worker who registered patient")

    conditions:          list[Condition]    = Field(default_factory=list)
    current_medications: list[Medication]   = Field(default_factory=list)
    allergies:           list[Allergy]      = Field(default_factory=list)
    emergency_contact:   Optional[EmergencyContact] = None

    created_at:          datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:          datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active:           bool     = True

    @field_validator("full_name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Patient name cannot be blank")
        return v.strip().title()

    def condition_names(self) -> list[str]:
        """Return flat list of condition names for risk engine input."""
        return [c.name for c in self.conditions]

    def medication_names(self) -> list[str]:
        """Return flat list of current medication names for risk engine input."""
        return [m.name for m in self.current_medications]

    def allergy_names(self) -> list[str]:
        return [a.allergen for a in self.allergies]

    model_config = {"str_strip_whitespace": True}


class PatientCreate(BaseModel):
    """Request body for POST /patients — excludes auto-generated fields."""
    full_name:           str
    date_of_birth:       Optional[datetime] = None
    gender:              Optional[Gender]   = None
    phone:               Optional[str]      = None
    facility_id:         Optional[str]      = None
    chw_id:              Optional[str]      = None
    conditions:          list[Condition]    = Field(default_factory=list)
    current_medications: list[Medication]   = Field(default_factory=list)
    allergies:           list[Allergy]      = Field(default_factory=list)
    emergency_contact:   Optional[EmergencyContact] = None


class PatientSummary(BaseModel):
    """Lightweight patient record for list views and QR wallet encoding."""
    id:           UUID
    full_name:    str
    conditions:   list[str]   # condition names only
    allergies:    list[str]   # allergen names only
    medications:  list[str]   # medication names only
    updated_at:   datetime


# ── Drug check ────────────────────────────────────────────────────────────────

class DrugCheckRequest(BaseModel):
    """
    Submitted by a clinician or CHW to check a proposed drug against a patient.
    Can reference a patient by ID (dashboard flow) or pass data inline (USSD flow).
    """
    proposed_drug:        str  = Field(..., min_length=1, description="Drug being considered for prescription")
    patient_id:           Optional[UUID] = Field(None, description="Look up patient from database")

    # Inline fields used when patient_id is not available (e.g. USSD)
    current_medications:  list[str] = Field(default_factory=list)
    conditions:           list[str] = Field(default_factory=list)
    allergies:            list[str] = Field(default_factory=list)

    channel:              AccessChannel = AccessChannel.DASHBOARD
    clinician_id:         Optional[str] = None
    chw_id:               Optional[str] = None
    facility_id:          Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class InteractionResult(BaseModel):
    """A single detected drug interaction — mirrors InteractionMatch from risk_engine."""
    rule_id:               str
    cluster:               str
    interaction_type:      str
    drug_a:                str
    drug_b_or_condition:   str
    risk_score:            int    = Field(..., ge=1, le=10)
    risk_level:            RiskLevel
    warning_message:       str
    recommendation:        str
    mechanism:             str
    alternatives:          list[str] = Field(default_factory=list)
    source:                str       = "africa_priority_rules"
    references:            list[str] = Field(default_factory=list)


class DrugCheckResponse(BaseModel):
    """
    Full response returned after a drug safety check.
    Powers the dashboard alert card, USSD response, and audit log entry.
    """
    check_id:             UUID     = Field(default_factory=uuid4)
    proposed_drug:        str
    patient_id:           Optional[UUID] = None
    interactions_found:   list[InteractionResult] = Field(default_factory=list)
    max_risk_score:       int      = Field(..., ge=0, le=10)
    max_risk_level:       RiskLevel
    requires_human_review: bool
    offline_mode:         bool
    evaluation_ms:        int
    timestamp:            datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ussd_summary:         Optional[str] = Field(None, description="160-char USSD-safe summary")

    def is_safe(self) -> bool:
        return len(self.interactions_found) == 0


# ── QR Wallet ─────────────────────────────────────────────────────────────────

class QRWallet(BaseModel):
    """
    Portable encrypted medical record encoded into a QR code.
    Contains the minimum data needed for a clinician to make a safe decision.
    """
    wallet_id:    UUID     = Field(default_factory=uuid4)
    patient_id:   UUID
    patient_name: str
    conditions:   list[str]
    medications:  list[str]
    allergies:    list[str]
    blood_group:  Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at:   Optional[datetime] = None
    generated_by: Optional[str] = None   # clinician or CHW ID
    scan_count:   int = 0

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


# ── Governance / Clinical Review ──────────────────────────────────────────────

class ClinicalReview(BaseModel):
    """
    Created automatically when a drug check returns a critical risk score.
    Requires sign-off from a senior clinician before the medication can proceed.
    Implements the human-in-the-loop governance pillar.
    """
    review_id:      UUID         = Field(default_factory=uuid4)
    check_id:       UUID         = Field(..., description="The DrugCheckResponse that triggered this review")
    patient_id:     Optional[UUID] = None
    patient_name:   Optional[str]  = None
    proposed_drug:  str
    risk_score:     int
    risk_level:     RiskLevel
    warning_summary: str
    status:         ReviewStatus = ReviewStatus.PENDING
    assigned_to:    Optional[str] = Field(None, description="Clinician ID assigned to review")
    reviewed_by:    Optional[str] = None
    review_notes:   Optional[str] = None
    override_reason: Optional[str] = Field(None, description="Required if status=OVERRIDDEN")
    created_at:     datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at:    Optional[datetime] = None

    def is_pending(self) -> bool:
        return self.status == ReviewStatus.PENDING


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(BaseModel):
    """
    Immutable record of every clinically significant action in the system.
    Every important event writes an AuditLog — cannot be deleted or edited.
    Powers the Audit Logs screen and regulatory compliance.
    """
    log_id:       UUID         = Field(default_factory=uuid4)
    action:       AuditAction
    actor_id:     Optional[str] = Field(None, description="Clinician, CHW, or system ID")
    patient_id:   Optional[UUID] = None
    patient_name: Optional[str]  = None
    channel:      AccessChannel  = AccessChannel.DASHBOARD
    facility_id:  Optional[str]  = None
    details:      dict           = Field(default_factory=dict, description="Action-specific metadata")
    risk_score:   Optional[int]  = None
    timestamp:    datetime       = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address:   Optional[str]  = None
    session_id:   Optional[str]  = None


# ── USSD ──────────────────────────────────────────────────────────────────────

class USSDSession(BaseModel):
    """Tracks a single USSD drug safety check session."""
    session_id:    str      = Field(..., description="Telco-assigned USSD session ID")
    msisdn:        str      = Field(..., description="Caller phone number")
    input:         str      = Field(..., description="Raw USSD input string")
    drug_queried:  Optional[str]  = None
    response_text: Optional[str]  = None
    risk_score:    Optional[int]  = None
    timestamp:     datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms:   Optional[int]  = None


# ── CHW Sync ──────────────────────────────────────────────────────────────────

class CHWSyncEvent(BaseModel):
    """
    Records a community health worker data sync event.
    CHWs work offline and sync when connectivity is available.
    """
    sync_id:          UUID     = Field(default_factory=uuid4)
    chw_id:           str
    facility_id:      Optional[str] = None
    patients_synced:  int      = 0
    checks_synced:    int      = 0
    alerts_synced:    int      = 0
    sync_status:      str      = "success"   # success / partial / failed
    error_message:    Optional[str] = None
    synced_at:        datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from uuid import uuid4

    print("Testing models.py...\n")

    # Build a patient matching the Amina Bello demo case
    patient = Patient(
        full_name    = "Amina Bello",
        gender       = Gender.FEMALE,
        phone        = "+234 801 234 5678",
        conditions   = [Condition(name="Kidney Disease", severity="moderate")],
        current_medications = [],
        allergies    = [],
    )
    print(f"Patient     : {patient.full_name}")
    print(f"Conditions  : {patient.condition_names()}")
    print(f"ID          : {patient.id}")

    # Build a drug check request
    check = DrugCheckRequest(
        proposed_drug = "ibuprofen",
        patient_id    = patient.id,
        conditions    = patient.condition_names(),
        channel       = AccessChannel.USSD,
    )
    print(f"\nDrug Check  : {check.proposed_drug}")
    print(f"Channel     : {check.channel}")

    # Build a mock critical response
    interaction = InteractionResult(
        rule_id              = "AFR-001",
        cluster              = "NSAID_RENAL",
        interaction_type     = "drug_condition",
        drug_a               = "ibuprofen",
        drug_b_or_condition  = "kidney disease",
        risk_score           = 9,
        risk_level           = RiskLevel.CRITICAL,
        warning_message      = "CRITICAL: NSAIDs contraindicated in kidney disease.",
        recommendation       = "Use paracetamol instead.",
        mechanism            = "NSAIDs reduce renal blood flow.",
        alternatives         = ["paracetamol"],
    )
    response = DrugCheckResponse(
        proposed_drug         = "ibuprofen",
        patient_id            = patient.id,
        interactions_found    = [interaction],
        max_risk_score        = 9,
        max_risk_level        = RiskLevel.CRITICAL,
        requires_human_review = True,
        offline_mode          = True,
        evaluation_ms         = 1,
        ussd_summary          = "CRITICAL: ibuprofen\nRisk: 9/10\nAvoid — kidney disease patient.",
    )
    print(f"\nDrug Check Response")
    print(f"Risk Score  : {response.max_risk_score}/10")
    print(f"Risk Level  : {response.max_risk_level.upper()}")
    print(f"Safe?       : {response.is_safe()}")
    print(f"Needs Review: {response.requires_human_review}")

    # Build audit log
    log = AuditLog(
        action       = AuditAction.CRITICAL_ALERT_RAISED,
        actor_id     = "chw_001",
        patient_id   = patient.id,
        patient_name = patient.full_name,
        channel      = AccessChannel.USSD,
        risk_score   = 9,
        details      = {"drug": "ibuprofen", "rule": "AFR-001"},
    )
    print(f"\nAudit Log   : {log.action}")
    print(f"Timestamp   : {log.timestamp}")

    print("\n All models OK.")