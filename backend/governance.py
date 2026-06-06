# governance.py
"""
OCML-DI Governance Layer
Owner: Efe Ikharo (Project Lead, ML/AI Systems)

Purpose:
    Implements AI governance and human-in-the-loop review.
    Critical alerts trigger mandatory clinical review and audit logging.
"""

from datetime import datetime
from database import SessionLocal, AuditLogDB, ClinicalReviewDB


class GovernanceLayer:
    def __init__(self):
        self.db = SessionLocal()

    def record_audit(self, action: str, actor_id: str, patient_name: str, risk_score: int, details: dict):
        log_entry = AuditLogDB(
            action=action,
            actor_id=actor_id,
            patient_name=patient_name,
            risk_score=risk_score,
            details=details,
            timestamp=datetime.utcnow(),
        )
        self.db.add(log_entry)
        self.db.commit()
        return log_entry

    def create_review(self, check_id: str, patient_name: str, proposed_drug: str, risk_score: int, risk_level: str, warning_summary: str):
        review = ClinicalReviewDB(
            check_id=check_id,
            patient_name=patient_name,
            proposed_drug=proposed_drug,
            risk_score=risk_score,
            risk_level=risk_level,
            warning_summary=warning_summary,
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.add(review)
        self.db.commit()
        return review

    def complete_review(self, review_id: int, reviewed_by: str, notes: str, status: str = "approved"):
        review = self.db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
        if review:
            review.status = status
            review.reviewed_by = reviewed_by
            review.review_notes = notes
            review.reviewed_at = datetime.utcnow()
            self.db.commit()
        return review
