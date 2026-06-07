# OCML-DI Threat Model
**Owner:** Efe Ikharo — Project Lead, ML/AI Systems
**Version:** 1.0.0 | **Date:** June 2026
**Methodology:** STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)

---

## System Overview

OCML-DI is an offline-first clinical drug safety system operating across three channels:
- **Clinician dashboard** — FastAPI backend + HTML frontend
- **QR medical wallet** — patient-controlled encrypted record
- **USSD channel** — feature phone access via Africa's Talking

The system handles sensitive medical data including patient conditions, medications, allergies, and drug interaction results. The threat model reflects the African clinical infrastructure context — low-connectivity environments, shared devices, and varying levels of digital literacy.

---

## Assets to Protect

| Asset | Sensitivity | Why It Matters |
|---|---|---|
| Patient medical records | Critical | Contains conditions, medications, allergies — misuse causes patient harm |
| Drug interaction results | Critical | Wrong result could lead to dangerous prescription |
| Clinician credentials | High | Compromised account enables fraudulent prescriptions |
| QR wallet payload | High | Contains encoded patient data — interception risks privacy |
| Audit logs | High | Tampering destroys accountability trail |
| Africa Priority Rules JSON | Medium | Manipulation could cause false safety signals |
| USSD session data | Medium | Phone numbers + drug queries reveal health information |

---

## Trust Boundaries

```
[Africa's Talking] ──HTTPS──► [ngrok/public URL] ──► [FastAPI /ussd/callback]
[Clinician browser] ──HTTPS──► [FastAPI /api/*] ──► [SQLite DB]
[Flutter app] ──HTTPS──► [FastAPI /login/token] ──► [JWT]
[QR scanner] ──local──► [dashboard decode endpoint]
```

---

## STRIDE Analysis

### S — Spoofing

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| Attacker impersonates clinician | `/login/token` | High | JWT with bcrypt password hashing. Tokens expire in 8 hours. |
| USSD caller spoofs phone number | `/ussd/callback` | Medium | Africa's Talking signs requests — validate `AT-Signature` header in production |
| Fake QR wallet presented | QR decode endpoint | Medium | QR payload should be signed with HMAC in production |

### T — Tampering

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| Drug rules JSON modified | `africa_priority_rules.json` | Critical | File hash verification on startup. Read-only in production. |
| Patient record altered in DB | SQLite | High | Audit log records every write. DB file permissions restricted. |
| USSD response intercepted and modified | Africa's Talking → backend | Low | HTTPS enforced end-to-end via ngrok/TLS |

### R — Repudiation

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| Clinician denies approving a review | Dashboard | High | `AuditLogDB` records actor_id, timestamp, and action on every review |
| USSD drug check denied | USSD | Medium | Every USSD check logged with msisdn, session ID, drug, and timestamp |
| Patient record creation disputed | API | Medium | `patient_created` audit entry written on every POST /api/patients |

### I — Information Disclosure

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| Patient data exposed in API response | `/api/patients` | Critical | JWT auth required on all patient endpoints. CORS restricted in production. |
| QR code photographed/intercepted | QR wallet | High | QR payload should be encrypted with AES-256 in production (currently JSON) |
| USSD session sniffed on GSM | USSD channel | Medium | USSD is inherently plaintext on GSM — minimise PII in responses |
| Error messages expose stack traces | All endpoints | Low | FastAPI exception handlers return generic errors in production |

### D — Denial of Service

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| USSD endpoint flooded | `/ussd/callback` | Medium | Rate limiting via Africa's Talking platform. Add FastAPI rate limiter in production. |
| SQLite locked by concurrent writes | Database | Medium | SQLAlchemy connection pooling. Migrate to PostgreSQL for production scale. |
| Risk engine CPU exhaustion | `/api/check` | Low | Rule evaluation is O(n) with n=rules. Current 32 rules evaluates in <5ms. |

### E — Elevation of Privilege

| Threat | Component | Risk | Mitigation |
|---|---|---|---|
| CHW accesses doctor-only endpoints | All `/api/*` | High | Role checked in `get_current_user()`. AUTHORIZED_ROLES enforced per endpoint. |
| Expired token reused | JWT | Medium | Token expiry enforced by `jose` library. 8-hour window balances security/usability for clinical settings. |
| USSD caller accesses patient DB | `/ussd/callback` | Low | USSD endpoint does not query patient DB — runs drug check with no patient context |

---

## Risk Register

| ID | Threat | Likelihood | Impact | Overall | Status |
|---|---|---|---|---|---|
| T-001 | Drug rules file tampered | Low | Critical | High | Mitigated — hash check on startup |
| T-002 | Clinician credential compromise | Medium | Critical | Critical | Mitigated — bcrypt + JWT |
| T-003 | QR wallet data intercepted | Medium | High | High | Partial — encrypt payload in v2 |
| T-004 | Patient API accessed without auth | Low | Critical | High | Mitigated — JWT required |
| T-005 | Audit log tampered | Low | High | Medium | Mitigated — append-only DB table |
| T-006 | USSD endpoint flooded | Medium | Medium | Medium | Partial — AT rate limits apply |
| T-007 | Privilege escalation via JWT | Low | High | Medium | Mitigated — role checked per request |

---

## Out of Scope (v1.0 Hackathon)

- Physical device theft (clinic hardware)
- Insider threat (malicious clinician)
- SIM swap attacks on USSD phone numbers
- Africa's Talking platform compromise
- Full PKI infrastructure for QR signing

These are documented for v2.0 production hardening.

---

## Residual Risks Accepted for Hackathon Demo

1. **QR payload is plain JSON** — acceptable for demo; AES-256 encryption planned for v2
2. **SQLite instead of PostgreSQL** — acceptable for offline-first single-clinic deployment
3. **SECRET_KEY hardcoded** — must move to environment variable before production
4. **No rate limiting** — acceptable for demo; `slowapi` integration planned for v2
