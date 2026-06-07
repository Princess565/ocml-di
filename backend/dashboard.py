from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from .database import SessionLocal, PatientDB, ClinicalReviewDB, AuditLogDB
from .auth import get_current_user
from datetime import datetime
import qrcode
import base64
from io import BytesIO
from fastapi import APIRouter, Depends, Request, UploadFile, File
import json


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ── QR decode route ───────────────────────────────────────────
@router.post("/patient/qr/decode", response_class=HTMLResponse)
async def decode_qr(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    # Read uploaded QR image
    contents = await file.read()

    # Decode QR (using qrcode + pillow)
    from PIL import Image
    import cv2
    import numpy as np
    import pyzbar.pyzbar as pyzbar

    # Convert bytes to numpy array
    npimg = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # Decode QR
    decoded_objects = pyzbar.decode(img)
    if not decoded_objects:
        return HTMLResponse("<h1>No QR code detected</h1>", status_code=400)

    data = decoded_objects[0].data.decode("utf-8")
    payload = json.loads(data)

    # Lookup patient by ID
    db = SessionLocal()
    patient = db.query(PatientDB).filter(PatientDB.id == payload["id"]).first()
    if not patient:
        return HTMLResponse("<h1>Patient not found in this facility</h1>", status_code=404)

    return templates.TemplateResponse("patient.html", {"request": request, "patient": patient})

# ── Dashboard view ─────────────────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user)):
    db = SessionLocal()
    reviews = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.status == "pending").all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "reviews": reviews})

# ── Patient record view ────────────────────────────────────────
@router.get("/patient/{patient_id}", response_class=HTMLResponse)
def patient_view(patient_id: str, request: Request, user=Depends(get_current_user)):
    db = SessionLocal()
    patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
    if not patient:
        return HTMLResponse("<h1>Patient not found</h1>", status_code=404)
    return templates.TemplateResponse("patient.html", {"request": request, "patient": patient})

# ── QR code export ─────────────────────────────────────────────
@router.post("/patient/{patient_id}/qr", response_class=HTMLResponse)
def patient_qr(patient_id: str, request: Request, user=Depends(get_current_user)):
    db = SessionLocal()
    patient = db.query(PatientDB).filter(PatientDB.id == patient_id).first()
    if not patient:
        return HTMLResponse("<h1>Patient not found</h1>", status_code=404)

    # Generate QR code with patient ID + name (can encrypt later)
    qr = qrcode.QRCode(box_size=10, border=4)
    import json
    qr.add_data(json.dumps({"id": patient.id, "name": patient.full_name}))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, kind="PNG")
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()

    return templates.TemplateResponse(
        "patient.html",
        {"request": request, "patient": patient, "qr_code": qr_code_b64}
    )

# ── Approve flagged case ───────────────────────────────────────
@router.post("/review/{review_id}/approve")
def approve_review(review_id: int, user=Depends(get_current_user)):
    db = SessionLocal()
    review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
    if review:
        review.status = "approved"
        review.reviewed_by = user["id"]
        review.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url="/clinician/dashboard", status_code=303)

# ── Reject flagged case ────────────────────────────────────────
@router.post("/review/{review_id}/reject")
def reject_review(review_id: int, user=Depends(get_current_user)):
    db = SessionLocal()
    review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
    if review:
        review.status = "rejected"
        review.reviewed_by = user["id"]
        review.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url="/clinician/dashboard", status_code=303)
