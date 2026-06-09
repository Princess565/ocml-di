# main.py
"""
OCML-DI Main Application
Owner: Efe Ikharo (Project Lead, ML/AI Systems)
"""

import json
import os
import time
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse

from backend.dashboard   import router as dashboard_router
from backend.ussd_router import router as ussd_router
from backend.database    import SessionLocal, PatientDB, ClinicalReviewDB, AuditLogDB, init_db
from backend.risk_engine import RiskEngine
from backend.governance  import GovernanceLayer
from backend.models      import (
    PatientCreate, DrugCheckRequest, DrugCheckResponse,
    InteractionResult, RiskLevel, AccessChannel, AuditAction
)
from . import auth

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

app.include_router(dashboard_router, prefix="/clinician", tags=["Clinician Dashboard"])
app.include_router(ussd_router,      prefix="/ussd",      tags=["USSD"])

engine     = RiskEngine()
governance = GovernanceLayer()


@app.on_event("startup")
async def startup_event():
    print("🚀 OCML-DI system starting up...")
    init_db()
    from . import sync
    try:
        sync.sync_patients()
    except Exception as e:
        print("⚠️ Sync deferred:", e)


# ── SYSTEM ────────────────────────────────────

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


# ── AUTH ──────────────────────────────────────

@app.get("/login", response_class=HTMLResponse, tags=["Auth"])
def login_page(request: Request):
    return auth.login_page(request)

@app.post("/login", tags=["Auth"])
def login_action(username: str = Form(...), password: str = Form(...)):
    return auth.login_action(username, password)

@app.post("/login/token", tags=["Auth"])
def login_token(username: str = Form(...), password: str = Form(...)):
    return auth.login_token(username, password)


# ── PATIENTS ──────────────────────────────────

@app.get("/api/patients", tags=["Patients"])
def list_patients(skip: int = 0, limit: int = 50, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        patients = db.query(PatientDB).offset(skip).limit(limit).all()
        return [_patient_to_dict(p) for p in patients]
    finally:
        db.close()

@app.get("/api/patients/{patient_id}", tags=["Patients"])
def get_patient(patient_id: str, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        governance.record_audit(
            action="patient_accessed", actor_id=user["id"],
            patient_name=patient.full_name, risk_score=0,
            details={"patient_id": patient_id, "channel": "api"}
        )
        return _patient_to_dict(patient)
    finally:
        db.close()

@app.post("/api/patients", tags=["Patients"], status_code=201)
def create_patient(data: PatientCreate, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
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
    finally:
        db.close()

@app.put("/api/patients/{patient_id}", tags=["Patients"])
def update_patient(patient_id: str, data: PatientCreate, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient.full_name   = data.full_name
        patient.phone       = data.phone
        patient.gender      = data.gender.value if data.gender else patient.gender
        patient.conditions  = [c.name for c in data.conditions]
        patient.medications = [m.name for m in data.current_medications]
        patient.allergies   = [a.allergen for a in data.allergies]
        db.commit()
        return _patient_to_dict(patient)
    finally:
        db.close()


# ── DRUG CHECK ────────────────────────────────

@app.post("/api/check", tags=["Drug Safety"])
def check_drug(req: DrugCheckRequest, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        conditions    = list(req.conditions)
        medications   = list(req.current_medications)
        allergies     = list(req.allergies)
        patient_name  = "Unknown"
        patient_id_str = str(req.patient_id) if req.patient_id else None

        if req.patient_id:
            patient = db.query(PatientDB).filter(PatientDB.id == str(req.patient_id)).first()
            if patient:
                conditions   = list(set(conditions  + (patient.conditions  or [])))
                medications  = list(set(medications + (patient.medications or [])))
                allergies    = list(set(allergies   + (patient.allergies   or [])))
                patient_name = patient.full_name

        t0     = time.time()
        result = engine.evaluate(
            proposed_drug=req.proposed_drug,
            current_medications=medications,
            conditions=conditions,
        )
        eval_ms = int((time.time() - t0) * 1000)

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
            proposed_drug          = req.proposed_drug,
            patient_id             = req.patient_id,
            interactions_found     = interactions,
            max_risk_score         = result.max_risk_score,
            max_risk_level         = RiskLevel(result.max_risk_level),
            requires_human_review  = result.requires_human_review,
            offline_mode           = True,
            evaluation_ms          = eval_ms,
            ussd_summary           = _build_ussd_summary(req.proposed_drug, result),
        )

        governance.record_audit(
            action       = "drug_check_performed",
            actor_id     = user["id"],
            patient_name = patient_name,
            risk_score   = result.max_risk_score,
            details      = {
                "drug":       req.proposed_drug,
                "risk_level": result.max_risk_level,
                "channel":    req.channel.value,
                "patient_id": patient_id_str,
            }
        )
        if result.requires_human_review:
            governance.create_review(
                check_id        = str(response.check_id),
                patient_name    = patient_name,
                proposed_drug   = req.proposed_drug,
                risk_score      = result.max_risk_score,
                risk_level      = result.max_risk_level,
                warning_summary = _build_warning_summary(result),
            )

        return response
    finally:
        db.close()

@app.post("/check_interaction", tags=["Drug Safety (Legacy)"])
def check_interaction_legacy(req: DrugCheckRequest, user=Depends(auth.get_current_user)):
    return check_drug(req, user)


# ── REVIEWS ───────────────────────────────────

@app.get("/api/reviews", tags=["Reviews"])
def list_reviews(status_filter: str = "pending", user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        q = db.query(ClinicalReviewDB)
        if status_filter != "all":
            q = q.filter(ClinicalReviewDB.status == status_filter)
        return [_review_to_dict(r) for r in q.all()]
    finally:
        db.close()

@app.post("/api/reviews/{review_id}/approve", tags=["Reviews"])
def approve_review(review_id: int, notes: str = "", user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        review.status       = "approved"
        review.reviewed_by  = user["id"]
        review.review_notes = notes
        review.reviewed_at  = datetime.utcnow()
        db.commit()
        return _review_to_dict(review)
    finally:
        db.close()

@app.post("/api/reviews/{review_id}/reject", tags=["Reviews"])
def reject_review(review_id: int, notes: str = "", user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        review.status       = "rejected"
        review.reviewed_by  = user["id"]
        review.review_notes = notes
        review.reviewed_at  = datetime.utcnow()
        db.commit()
        return _review_to_dict(review)
    finally:
        db.close()


# ── AUDIT ─────────────────────────────────────

@app.get("/api/audit", tags=["Audit"])
def get_audit_log(skip: int = 0, limit: int = 100, user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        logs = db.query(AuditLogDB).order_by(AuditLogDB.timestamp.desc()).offset(skip).limit(limit).all()
        return [_audit_to_dict(l) for l in logs]
    finally:
        db.close()


# ── USSD CALLBACK (Africa's Talking) ──────────

@app.post("/ussd/callback", tags=["USSD"])
async def ussd_callback(
    sessionId:   str = Form(...),
    phoneNumber: str = Form(...),
    text:        str = Form(""),
):
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
        response = "CON Enter drug name and condition:\nFormat: drug,condition\n(e.g. Ibuprofen,kidney disease)"

    elif text.startswith("1*") and len(parts) >= 2:
        entry = parts[1].strip()

        if not entry:
            response = "END Please enter a valid drug name."
        else:
            if "," in entry:
                drug, condition = entry.split(",", 1)
                drug = drug.strip()
                condition = condition.strip()
                conditions = [condition]
            else:
                drug = entry.strip()
                conditions = []

            try:
                result = engine.evaluate(
                    proposed_drug=drug,
                    current_medications=[],
                    conditions=conditions,
                )

                summary = _build_ussd_summary(drug, result)
                response = f"END {summary}"

                governance.record_audit(
                    action="ussd_check_performed",
                    actor_id=phoneNumber,
                    patient_name="USSD caller",
                    risk_score=result.max_risk_score,
                    details={
                        "drug": drug,
                        "msisdn": phoneNumber,
                        "session": sessionId,
                        "channel": "ussd",
                    }
                )

            except Exception:
                response = (
                    f"END Error processing check for {drug}. "
                    f"Please try again."
                )

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
        response = (
            "END Invalid option.\n"
            "Dial *384*52591# to restart."
        )

    return PlainTextResponse(content=response)


# ── HELPERS ───────────────────────────────────

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
    level = result.max_risk_level.upper() if result.max_risk_level else "UNKNOWN"
    score = result.max_risk_score
    if result.requires_human_review:
        return (
            f"CRITICAL RISK\nDrug: {drug}\nRisk: {level} ({score}/10)\n\n"
            f"DO NOT DISPENSE.\nSenior clinician review\nrequired immediately.\n\n"
            f"[OCML-DI + WHO rules]"
        )
    elif score >= 5:
        return (
            f"HIGH RISK\nDrug: {drug}\nRisk: {level} ({score}/10)\n\n"
            f"Caution advised.\nReview before dispensing.\n\n"
            f"[OCML-DI + WHO rules]"
        )
    else:
        return (
            f"SAFE\nDrug: {drug}\nRisk: {level} ({score}/10)\n\n"
            f"No critical interactions found.\nSafe to dispense.\n\n"
            f"[OCML-DI + WHO rules]"
        )

def _build_warning_summary(result) -> str:
    if hasattr(result, "matches") and result.matches:
        return result.matches[0].warning_message
    return f"Risk score {result.max_risk_score}/10 — {result.max_risk_level} risk detected"
