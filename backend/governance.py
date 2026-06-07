# governance.py
"""
OCML-DI Governance Layer
Owner: Efe Ikharo (Project Lead, ML/AI Systems)

Implements human-in-the-loop review and audit logging.
Fixed: relative imports, DB session management.
"""

from datetime import datetime
from .database import SessionLocal, AuditLogDB, ClinicalReviewDB


class GovernanceLayer:
    def record_audit(self, action: str, actor_id: str, patient_name: str, risk_score: int, details: dict):
        """Write an immutable audit log entry."""
        db = SessionLocal()
        try:
            log_entry = AuditLogDB(
                action       = action,
                actor_id     = actor_id,
                patient_name = patient_name,
                risk_score   = risk_score,
                details      = details,
                channel      = details.get("channel", "api"),
                timestamp    = datetime.utcnow(),
            )
            db.add(log_entry)
            db.commit()
            return log_entry
        except Exception as e:
            db.rollback()
            print(f"⚠️ Audit log failed: {e}")
        finally:
            db.close()

    def create_review(self, check_id: str, patient_name: str, proposed_drug: str,
                      risk_score: int, risk_level: str, warning_summary: str):
        """Create a pending clinical review for critical drug checks."""
        db = SessionLocal()
        try:
            review = ClinicalReviewDB(
                check_id        = check_id,
                patient_name    = patient_name,
                proposed_drug   = proposed_drug,
                risk_score      = risk_score,
                risk_level      = risk_level,
                warning_summary = warning_summary,
                status          = "pending",
                created_at      = datetime.utcnow(),
            )
            db.add(review)
            db.commit()
            db.refresh(review)
            return review
        except Exception as e:
            db.rollback()
            print(f"⚠️ Review creation failed: {e}")
        finally:
            db.close()

    def complete_review(self, review_id: int, reviewed_by: str, notes: str, status: str = "approved"):
        """Mark a review as approved, rejected, or overridden."""
        db = SessionLocal()
        try:
            review = db.query(ClinicalReviewDB).filter(ClinicalReviewDB.id == review_id).first()
            if review:
                review.status      = status
                review.reviewed_by = reviewed_by
                review.review_notes= notes
                review.reviewed_at = datetime.utcnow()
                db.commit()
            return review
        except Exception as e:
            db.rollback()
            print(f"⚠️ Review completion failed: {e}")
        finally:
            db.close()
