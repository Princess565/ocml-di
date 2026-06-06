# ussd_router.py
"""
OCML-DI USSD Router
Owner: Efe Ikharo (Project Lead, ML/AI Systems)

Purpose:
    Handle USSD sessions via telco aggregator (e.g. Africa's Talking).
    Integrates with RiskEngine to provide offline-first drug safety checks.
"""

from fastapi import APIRouter, Form
from .risk_engine import RiskEngine

router = APIRouter()
engine = RiskEngine()

@router.post("/ussd")
async def ussd_handler(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form("")
):
    """
    USSD flow:
    - "CON" → continue session
    - "END" → terminate session
    """

    if text == "":
        # First dial-in
        response = "CON Welcome to OCML-DI\n1. Check drug safety\n2. Exit"

    elif text == "1":
        response = "CON Enter drug name:"

    elif text.startswith("1*"):
        # Extract drug name from input
        drug = text.split("*")[1]
        result = engine.evaluate(proposed_drug=drug, current_medications=[], conditions=[])

        if result.requires_human_review:
            response = f"END {drug} → CRITICAL risk. Human review required."
        else:
            response = f"END {drug} → {result.max_risk_level.upper()} risk. Safe to proceed."

    else:
        response = "END Goodbye"

    return response
