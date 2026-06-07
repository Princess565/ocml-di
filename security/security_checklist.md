# OCML-DI Security Checklist
**Owner:** Efe Ikharo — Project Lead, ML/AI Systems
**Version:** 1.0.0 | **Date:** June 2026

Status key: ✅ Done | ⚠️ Partial | 🔲 Planned for v2

---

## Authentication & Authorisation

| # | Control | Status | Notes |
|---|---|---|---|
| 1 | Passwords hashed with bcrypt | ✅ | `passlib[bcrypt]` — cost factor 12 |
| 2 | JWT tokens for API authentication | ✅ | `python-jose[cryptography]` — HS256 |
| 3 | Token expiry enforced | ✅ | 8-hour expiry — balances security and clinical usability |
| 4 | Role-based access control | ✅ | Roles: doctor, pharmacist, nurse, chw — checked per request |
| 5 | No plaintext passwords stored | ✅ | All passwords bcrypt hashed at startup |
| 6 | OAuth2 token endpoint | ✅ | `/login/token` — standard Bearer token flow |
| 7 | Secret key in environment variable | ⚠️ | Currently hardcoded — must move to `.env` before production |
| 8 | Refresh token support | 🔲 | Planned for v2 |
| 9 | Multi-factor authentication | 🔲 | Out of scope for v1 |

---

## API Security

| # | Control | Status | Notes |
|---|---|---|---|
| 10 | All patient endpoints require JWT | ✅ | `Depends(auth.get_current_user)` on every route |
| 11 | CORS configured | ✅ | `allow_origins=["*"]` for demo — restrict to known origins in production |
| 12 | HTTPS enforced | ✅ | ngrok provides TLS termination — use proper cert in production |
| 13 | Input validation on all endpoints | ✅ | Pydantic models validate all request bodies |
| 14 | SQL injection prevention | ✅ | SQLAlchemy ORM — parameterised queries throughout |
| 15 | Error messages don't expose internals | ⚠️ | FastAPI returns validation details — configure custom exception handlers in production |
| 16 | Rate limiting | ⚠️ | Africa's Talking limits USSD — add `slowapi` to FastAPI for v2 |
| 17 | Request size limits | 🔲 | Add `max_upload_size` middleware in production |
| 18 | API versioning | ⚠️ | Routes use `/api/` prefix — formal versioning (`/api/v1/`) planned for v2 |

---

## Data Protection

| # | Control | Status | Notes |
|---|---|---|---|
| 19 | Patient data access logged | ✅ | Every `GET /api/patients/:id` writes audit log entry |
| 20 | Drug checks logged | ✅ | Every `/api/check` call writes audit log with actor, drug, risk level |
| 21 | Clinical reviews audited | ✅ | Approve/reject recorded with reviewer ID and timestamp |
| 22 | Audit log is append-only | ✅ | No DELETE endpoint on audit log table |
| 23 | QR wallet payload | ⚠️ | Currently plain JSON — AES-256 encryption planned for v2 |
| 24 | Database file permissions | ⚠️ | SQLite file should be `chmod 600` on Linux production |
| 25 | Sensitive data in USSD responses | ✅ | USSD responses contain drug + risk only — no patient PII |
| 26 | Data minimisation in QR wallet | ✅ | QR contains only clinically necessary fields |
| 27 | Patient data encrypted at rest | 🔲 | SQLite encryption (SQLCipher) planned for v2 |

---

## Drug Rules Integrity

| # | Control | Status | Notes |
|---|---|---|---|
| 28 | Rules file loaded and validated on startup | ✅ | RiskEngine validates JSON on init — logs rule count |
| 29 | Rules file hash verification | ⚠️ | Manual verification — automated SHA-256 check planned for v2 |
| 30 | Rules sourced from authoritative references | ✅ | WHO EML, Nigeria STG, Liverpool HIV DDI Database |
| 31 | Rule changes tracked in version control | ✅ | `africa_priority_rules.json` and `who_essential_medicines_rules.json` in git |

---

## Infrastructure

| # | Control | Status | Notes |
|---|---|---|---|
| 32 | No secrets in version control | ⚠️ | SECRET_KEY in `auth.py` — move to environment variable before production |
| 33 | `.gitignore` excludes database file | ✅ | `ocml_di.db` excluded |
| 34 | `.gitignore` excludes `.env` | ✅ | `.env` excluded |
| 35 | Dependency pinning | ⚠️ | `requirements.txt` present — pin exact versions for production |
| 36 | Virtual environment isolation | ✅ | `.venv` — all dependencies isolated |
| 37 | HTTPS in production | ⚠️ | ngrok for demo — proper TLS cert required for production deployment |

---

## USSD-Specific

| # | Control | Status | Notes |
|---|---|---|---|
| 38 | USSD endpoint accepts only form data | ✅ | Fixed from JSON BaseModel to `Form(...)` |
| 39 | USSD responses are plain text | ✅ | `PlainTextResponse` — Africa's Talking compliant |
| 40 | USSD responses start with CON/END | ✅ | All branches return correctly prefixed responses |
| 41 | USSD drug checks logged | ✅ | Audit entry written per USSD check with msisdn and session ID |
| 42 | No patient PII in USSD responses | ✅ | Responses contain drug name + risk level only |
| 43 | Africa's Talking signature validation | 🔲 | Validate `AT-Signature` header in production |

---

## Pre-Submission Checklist

- [x] Backend starts without errors
- [x] All API endpoints return correct responses
- [x] USSD callback returns CON/END plain text
- [x] JWT authentication working
- [x] Audit log writing on every clinical action
- [x] Drug rules loading from JSON files
- [x] QR code generation working
- [x] Africa's Talking USSD test successful
- [ ] Move SECRET_KEY to environment variable
- [ ] Restrict CORS origins for production
- [ ] Add AT-Signature validation

---

*OCML-DI Security Checklist v1.0 — Efe Ikharo*
