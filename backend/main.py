# main.py
"""
OCML-DI Main Application
Owner: Efe Ikharo (Project Lead, ML/AI Systems)

All routers registered, real risk engine wired to every endpoint,
JWT auth, Flutter-facing JSON API, USSD callback fixed.
"""

import json
import os
import time
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .dashboard  import router as dashboard_router
from .ussd_router import router as ussd_router
from .database   import SessionLocal, PatientDB, ClinicalReviewDB, AuditLogDB, init_db
from .risk_engine import RiskEngine
from .governance  import GovernanceLayer
from .models      import (
    PatientCreate, DrugCheckRequest, DrugCheckResponse,
    InteractionResult, RiskLevel, AccessChannel, AuditAction
)
from . import auth

# ── INIT ──────────────────────────────────────
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")

app = FastAPI(
    title="OCML-DI",
    version="0.1.0",
    description="Offline Clinical Medical Ledger with Drug Intelligence — built for African healthcare infrastructure",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(dashboard_router, prefix="/clinician", tags=["Clinician Dashboard"])
app.include_router(ussd_router,      prefix="/ussd",      tags=["USSD"])

# Risk engine + governance — single instances shared across all routes
engine     = RiskEngine()
governance = GovernanceLayer()

# ── STARTUP ───────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("🚀 OCML-DI system starting up...")
    init_db()
    from . import sync
    try:
        sync.sync_patients()
    except Exception as e:
        print("⚠️ Sync deferred:", e)


# ══════════════════════════════════════════════
# HEALTH & ROOT
# ══════════════════════════════════════════════

@app.get("/", tags=["System"])
def read_root():
    return {"message": "OCML-DI API is running", "version": "0.1.0", "status": "online"}

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/sync", tags=["System"])
def sync_endpoint():
    path = os.path.join(DATA_FOLDER, "africa_priority_rules.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"rules": [], "message": "Rules file not found"}


# ══════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════

@app.get("/login", response_class=HTMLResponse, tags=["Auth"])
def login_page(request: Request):
    return auth.login_page(request)

@app.post("/login", tags=["Auth"])
def login_action(username: str = Form(...), password: str = Form(...)):
    return auth.login_action(username, password)

@app.post("/login/token", tags=["Auth"])
def login_token(username: str = Form(...), password: str = Form(...)):
    """
    JWT token endpoint for Flutter app and USSD simulator.
    Returns: { access_token, token_type, role, name }
    """
    return auth.login_token(username, password)


# ══════════════════════════════════════════════
# PATIENT API  (Flutter + Frontend)
# ══════════════════════════════════════════════

@app.get("/api/patients", tags=["Patients"])
def list_patients(
    skip: int = 0,
    limit: int = 50,
    user=Depends(auth.get_current_user)
):
    """List all patients — paginated."""
    db = SessionLocal()
    patients = db.query(PatientDB).offset(skip).limit(limit).all()
    return [_patient_to_dict(p) for p in patients]


@app.get("/api/patients/{patient_id}", tags=["Patients"])
def get_patient(patient_id: str, user=Depends(auth.get_current_user)):
    """Get a single patient record by ID."""
    db = SessionLocal()
    patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    governance.record_audit(
        action="patient_accessed", actor_id=user["id"],
        patient_name=patient.full_name, risk_score=0,
        details={"patient_id": patient_id, "channel": "api"}
    )
    return _patient_to_dict(patient)


@app.post("/api/patients", tags=["Patients"], status_code=201)
def create_patient(data: PatientCreate, user=Depends(auth.get_current_user)):
    """Register a new patient."""
    db = SessionLocal()
    patient = PatientDB(
        id=str(uuid.uuid4()),
        full_name=data.full_name,
        phone=data.phone,
        gender=data.gender.value if data.gender else None,
        conditions=[c.name for c in data.conditions],
        medications=[m.name for m in data.current_medications],
        allergies=[a.allergen for a in data.allergies],
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    governance.record_audit(
        action="patient_created", actor_id=user["id"],
        patient_name=patient.full_name, risk_score=0,
        details={"patient_id": patient.id}
    )
    return _patient_to_dict(patient)


@app.put("/api/patients/{patient_id}", tags=["Patients"])
def update_patient(patient_id: str, data: PatientCreate, user=Depends(auth.get_current_user)):
    """Update an existing patient record."""
    db = SessionLocal()
    patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.full_name  = data.full_name
    patient.phone      = data.phone
    patient.gender     = data.gender.value if data.gender else patient.gender
    patient.conditions = [c.name for c in data.conditions]
    patient.medications= [m.name for m in data.current_medications]
    patient.allergies  = [a.allergen for a in data.allergies]
    db.commit()
    return _patient_to_dict(patient)


# ══════════════════════════════════════════════
# DRUG CHECK API  — real risk engine
# ══════════════════════════════════════════════

@app.post("/api/check", tags=["Drug Safety"])
def check_drug(req: DrugCheckRequest, user=Depends(auth.get_current_user)):
    """
    Main drug interaction check endpoint.
    Accepts patient_id (looks up from DB) or inline conditions/medications.
    Calls the real RiskEngine — not hardcoded demo data.
    """
    db = SessionLocal()
    conditions   = list(req.conditions)
    medications  = list(req.current_medications)
    allergies    = list(req.allergies)
    patient_name = "Unknown"
    patient_id_str = str(req.patient_id) if req.patient_id else None

    # If patient_id supplied, load from DB and merge
    if req.patient_id:
        patient = db.query(PatientDB).filter(PatientDB.id == str(req.patient_id)).first()
        if patient:
            conditions  = list(set(conditions  + (patient.conditions  or [])))
            medications = list(set(medications + (patient.medications or [])))
            allergies   = list(set(allergies   + (patient.allergies   or [])))
            patient_name = patient.full_name

    # Run real risk engine
    t0     = time.time()
    result = engine.evaluate(
        proposed_drug=req.proposed_drug,
        current_medications=medications,
        conditions=conditions,
    )
    eval_ms = int((time.time() - t0) * 1000)

    # Build interactions list
    interactions = []
    for match in (result.matches if hasattr(result, "matches") else []):
        interactions.append(InteractionResult(
            rule_id             = match.rule_id,
            cluster             = match.cluster,
            interaction_type    = match.interaction_type,
            drug_a              = match.drug_a,
            drug_b_or_condition = match.drug_b_or_condition,
            risk_score          = match.risk_score,
            risk_level          = RiskLevel(match.risk_level),
            warning_message     = match.warning_message,
            recommendation      = match.recommendation,
            mechanism           = match.mechanism,
            alternatives        = match.alternatives or [],
        ))

    response = DrugCheckResponse(
        proposed_drug         = req.proposed_drug,
        patient_id            = req.patient_id,
        interactions_found    = interactions,
        max_risk_score        = result.max_risk_score,
        max_risk_level        = RiskLevel(result.max_risk_level),
        requires_human_review = result.requires_human_review,
        offline_mode          = True,
        evaluation_ms         = eval_ms,
        ussd_summary          = _build_ussd_summary(req.proposed_drug, result),
    )

    # Governance — log audit + create review if critical
    governance.record_audit(
        action       = "drug_check_performed",
        actor_id     = user["id"],
        patient_name = patient_name,
        risk_score   = result.max_risk_score,
        details      = {
            "drug": req.proposed_drug,
            "risk_level": result.max_risk_level,
            "channel": req.channel.value,
            "patient_id": patient_id_str,
        }
    )
    if result.requires_human_review:
        governance.create_review(
            check_id       = str(response.check_id),
            patient_name   = patient_name,
            proposed_drug  = req.proposed_drug,
            risk_score     = result.max_risk_score,
            risk_level     = result.max_risk_level,
            warning_summary= _build_warning_summary(result),
        )

    return response


# Legacy endpoint — kept for backwards compatibility with old frontend
@app.post("/check_interaction", tags=["Drug Safety (Legacy)"])
def check_interaction_legacy(req: DrugCheckRequest, user=Depends(auth.get_current_user)):
    """Deprecated — use /api/check instead."""
    return check_drug(req, user)


# ══════════════════════════════════════════════
# REVIEWS API
# ══════════════════════════════════════════════

@app.get("/api/reviews", tags=["Reviews"])
def list_reviews(
    status_filter: str = "pending",
    user=Depends(auth.get_current_user)
):
    """List clinical reviews — default pending only."""
    db = SessionLocal()
    q = db.query(ClinicalReviewDB)
    if status_filter != "all":
        q = q.filter(ClinicalReviewDB.status == status_filter)
    return [_review_to_dict(r) for r in q.all()]


@app.post("/api/reviews/{review_id}/approve", tags=["Reviews"])
def approve_review(review_id: int, notes: str = "", user=Depends(auth.get_current_user)):
    """Approve a pending clinical review."""
    db = SessionLocal()
    review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.status      = "approved"
    review.reviewed_by = user["id"]
    review.review_notes= notes
    review.reviewed_at = datetime.utcnow()
    db.commit()
    return _review_to_dict(review)


@app.post("/api/reviews/{review_id}/reject", tags=["Reviews"])
def reject_review(review_id: int, notes: str = "", user=Depends(auth.get_current_user)):
    """Reject a pending clinical review."""
    db = SessionLocal()
    review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.status      = "rejected"
    review.reviewed_by = user["id"]
    review.review_notes= notes
    review.reviewed_at = datetime.utcnow()
    db.commit()
    return _review_to_dict(review)


# ══════════════════════════════════════════════
# AUDIT LOG API
# ══════════════════════════════════════════════

@app.get("/api/audit", tags=["Audit"])
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    user=Depends(auth.get_current_user)
):
    """Return audit log entries — most recent first."""
    db = SessionLocal()
    logs = db.query(AuditLogDB).order_by(AuditLogDB.timestamp.desc()).offset(skip).limit(limit).all()
    return [_audit_to_dict(l) for l in logs]


# ══════════════════════════════════════════════
# USSD CALLBACK  (Africa's Talking)
# ══════════════════════════════════════════════

@app.post("/ussd/callback", tags=["USSD"])
async def ussd_callback(
    sessionId: str = Form(...),
    msisdn:    str = Form(...),
    text:      str = Form(""),
):
    """
    Africa's Talking USSD callback.
    Receives form data, returns plain text starting with CON or END.
    """
    parts = text.split("*")

    if text == "":
        response = (
            "CON Welcome to OCML-DI\n"
            "Drug Safety Check\n\n"
            "1. Check drug interaction\n"
            "2. About OCML-DI\n"
            "0. Exit"
        )

    elif text == "1":
        response = "CON Enter drug name:\n(e.g. Ibuprofen)"

    elif text.startswith("1*") and len(parts) >= 2:
        drug = parts[1].strip()
        if not drug:
            response = "END Please enter a valid drug name."
        else:
            try:
                result = engine.evaluate(
                    proposed_drug=drug,
                    current_medications=[],
                    conditions=[],
                )
                summary = _build_ussd_summary(drug, result)
                response = f"END {summary}"

                # Log USSD check
                governance.record_audit(
                    action       = "ussd_check_performed",
                    actor_id     = msisdn,
                    patient_name = "USSD caller",
                    risk_score   = result.max_risk_score,
                    details      = {"drug": drug, "msisdn": msisdn, "session": sessionId, "channel": "ussd"}
                )
            except Exception as e:
                response = f"END Error processing check for {drug}. Please try again."

    elif text == "2":
        response = (
            "END OCML-DI\n"
            "Offline Clinical Medical\n"
            "Ledger with Drug Intelligence\n\n"
            "Built for African healthcare.\n"
            "ocml-di.org"
        )

    elif text == "0":
        response = "END Thank you. Stay safe."

    else:
        response = "END Invalid option.\nDial *384*52591# to restart."

    return PlainTextResponse(content=response)


# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════

def _patient_to_dict(p: PatientDB) -> dict:
    return {
        "id":          p.id,
        "full_name":   p.full_name,
        "phone":       p.phone,
        "gender":      p.gender,
        "conditions":  p.conditions  or [],
        "medications": p.medications or [],
        "allergies":   p.allergies   or [],
        "created_at":  p.created_at.isoformat() if p.created_at else None,
    }

def _review_to_dict(r: ClinicalReviewDB) -> dict:
    return {
        "id":              r.id,
        "check_id":        r.check_id,
        "patient_id":      r.patient_id,
        "patient_name":    r.patient_name,
        "proposed_drug":   r.proposed_drug,
        "risk_score":      r.risk_score,
        "risk_level":      r.risk_level,
        "warning_summary": r.warning_summary,
        "status":          r.status,
        "reviewed_by":     r.reviewed_by,
        "review_notes":    r.review_notes,
        "created_at":      r.created_at.isoformat() if r.created_at else None,
        "reviewed_at":     r.reviewed_at.isoformat() if r.reviewed_at else None,
    }

def _audit_to_dict(l: AuditLogDB) -> dict:
    return {
        "id":           l.id,
        "action":       l.action,
        "actor_id":     l.actor_id,
        "patient_name": l.patient_name,
        "channel":      l.channel,
        "risk_score":   l.risk_score,
        "details":      l.details,
        "timestamp":    l.timestamp.isoformat() if l.timestamp else None,
    }

def _build_ussd_summary(drug: str, result) -> str:
    """Build a USSD-safe plain text summary (max 182 chars)."""
    level = result.max_risk_level.upper() if result.max_risk_level else "UNKNOWN"
    score = result.max_risk_score

    if result.requires_human_review:
        return (
            f"CRITICAL RISK\n"
            f"Drug: {drug}\n"
            f"Risk: {level} ({score}/10)\n\n"
            f"DO NOT DISPENSE.\n"
            f"Senior clinician review\n"
            f"required immediately.\n\n"
            f"[OCML-DI + WHO rules]"
        )
    elif score >= 5:
        return (
            f"HIGH RISK\n"
            f"Drug: {drug}\n"
            f"Risk: {level} ({score}/10)\n\n"
            f"Caution advised.\n"
            f"Review before dispensing.\n\n"
            f"[OCML-DI + WHO rules]"
        )
    else:
        return (
            f"SAFE\n"
            f"Drug: {drug}\n"
            f"Risk: {level} ({score}/10)\n\n"
            f"No critical interactions\n"
            f"found. Safe to dispense.\n\n"
            f"[OCML-DI + WHO rules]"
        )

def _build_warning_summary(result) -> str:
    if hasattr(result, "matches") and result.matches:
        return result.matches[0].warning_message
    return f"Risk score {result.max_risk_score}/10 — {result.max_risk_level} risk detected"
