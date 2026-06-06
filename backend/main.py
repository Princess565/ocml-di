# main.py
"""
OCML-DI Main Application
Owner: Efe Ikharo (Project Lead, ML/AI Systems)
"""

import json
import os

from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Relative imports within the backend package
from .dashboard import router as dashboard_router
from .ussd_router import router as ussd_router
from . import sync
from . import auth

# Define DATA_FOLDER relative to backend/
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")

# Single app instantiation with metadata
app = FastAPI(
    title="OCML-DI",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- Root & Health ---
@app.get("/api/sync")
def sync_endpoint():
    path = os.path.join(DATA_FOLDER, "demo_sync_rules.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
@app.get("/")
def read_root():
    return {"message": "Hello Efe, FastAPI is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Interaction Check ---
class InteractionRequest(BaseModel):
    drug: str
    conflict_with: str

@app.post("/check_interaction")
def check_interaction(req: InteractionRequest):
    # Replace with your risk engine logic
    return {
        "drug": req.drug,
        "conflict_with": req.conflict_with,
        "risk_level": "HIGH",
        "outcome": f"Reduced {req.drug} plasma levels when combined with {req.conflict_with}",
        "recommendation": "Increase dose or monitor viral load"
    }

# --- USSD Callback ---
class UssdPayload(BaseModel):
    sessionId: str
    msisdn: str
    text: str

@app.post("/ussd/callback")
def ussd_callback(payload: UssdPayload):
    # Parse text into drug/conflict
    parts = payload.text.split("|")
    drug = parts[0].strip() if len(parts) > 0 else ""
    conflict = parts[1].strip() if len(parts) > 1 else ""

    # Call risk engine here; demo returns static response
    response_text = (
        f"CON Risk Level: HIGH\n"
        f"Outcome: Reduced {drug} plasma levels\n"
        f"Recommendation: Increase dose or monitor viral load"
    )

    return {
        "sessionId": payload.sessionId,
        "response": response_text,
        "endSession": False
    }