# OCML-DI Penetration Test Plan
**Owner:** Efe Ikharo — Project Lead, ML/AI Systems
**Version:** 1.0.0 | **Date:** June 2026
**Scope:** OCML-DI backend API, USSD callback, QR wallet endpoint

---

## Scope & Objectives

This plan documents the penetration testing approach for OCML-DI. The objective is to verify that patient data, drug interaction results, and clinical audit trails cannot be accessed, modified, or disrupted by an unauthenticated or unauthorised actor.

**In scope:**
- FastAPI backend API (`http://127.0.0.1:8000`)
- USSD callback endpoint (`/ussd/callback`)
- Authentication endpoints (`/login`, `/login/token`)
- Patient CRUD API (`/api/patients`)
- Drug check endpoint (`/api/check`)
- QR decode endpoint (`/clinician/patient/qr/decode`)

**Out of scope:**
- Africa's Talking platform infrastructure
- ngrok tunnel infrastructure
- Physical clinic device security
- SQLite file system access (requires physical device access)

---

## Test Cases

### 1. Authentication Bypass

**Objective:** Verify no endpoint returns patient data without a valid JWT.

**Test 1.1 — Unauthenticated patient list access**
```bash
curl http://127.0.0.1:8000/api/patients
```
**Expected:** `401 Unauthorized`
**Pass criteria:** No patient data returned

**Test 1.2 — Invalid token**
```bash
curl http://127.0.0.1:8000/api/patients \
  -H "Authorization: Bearer invalidtoken123"
```
**Expected:** `401 Unauthorized`

**Test 1.3 — Expired token**
Manually set `ACCESS_TOKEN_EXPIRE_MINUTES = 0` in `auth.py`, generate a token, reset the value, then use the token.
**Expected:** `401 Unauthorized`

**Test 1.4 — No token on drug check**
```bash
curl -X POST http://127.0.0.1:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"proposed_drug": "ibuprofen", "conditions": ["kidney disease"]}'
```
**Expected:** `401 Unauthorized`

---

### 2. Authorisation & Role Escalation

**Objective:** Verify CHW cannot access doctor-only actions.

**Test 2.1 — CHW token used on review approval**
```bash
# Get CHW token
curl -X POST http://127.0.0.1:8000/login/token \
  -d "username=chw1&password=chw123"

# Use CHW token to approve review
curl -X POST http://127.0.0.1:8000/api/reviews/1/approve \
  -H "Authorization: Bearer CHW_TOKEN"
```
**Expected:** Either `403 Forbidden` or action succeeds — document actual behaviour for v2 role-scoping

---

### 3. Input Validation & Injection

**Objective:** Verify no SQL injection or input manipulation is possible.

**Test 3.1 — SQL injection in patient ID**
```bash
curl http://127.0.0.1:8000/api/patients/1%27%20OR%20%271%27%3D%271 \
  -H "Authorization: Bearer VALID_TOKEN"
```
**Expected:** `404 Not Found` — SQLAlchemy ORM prevents injection

**Test 3.2 — Oversized drug name**
```bash
curl -X POST http://127.0.0.1:8000/api/check \
  -H "Authorization: Bearer VALID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposed_drug": "'"$(python -c "print('A'*10000)")"'", "conditions": []}'
```
**Expected:** `422 Unprocessable Entity` or graceful handling — no server crash

**Test 3.3 — Malformed JSON body**
```bash
curl -X POST http://127.0.0.1:8000/api/check \
  -H "Authorization: Bearer VALID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{bad json}'
```
**Expected:** `422 Unprocessable Entity`

---

### 4. USSD Endpoint Security

**Objective:** Verify USSD endpoint handles malicious input gracefully.

**Test 4.1 — Missing required field**
```bash
curl -X POST http://127.0.0.1:8000/ussd/callback \
  -d "sessionId=test123&text="
```
**Expected:** `422 Unprocessable Entity` (phoneNumber missing)

**Test 4.2 — Script injection in drug name**
```bash
curl -X POST http://127.0.0.1:8000/ussd/callback \
  -d "sessionId=test&phoneNumber=%2B234800&text=1*<script>alert(1)</script>"
```
**Expected:** Plain text response — no script execution (USSD is plaintext, not HTML)

**Test 4.3 — Extremely long drug name**
```bash
curl -X POST http://127.0.0.1:8000/ussd/callback \
  -d "sessionId=test&phoneNumber=%2B234800&text=1*AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
```
**Expected:** `END` response with no server crash

**Test 4.4 — USSD flood simulation**
Run 50 rapid requests and verify the server remains responsive:
```bash
for i in {1..50}; do
  curl -s -X POST http://127.0.0.1:8000/ussd/callback \
    -d "sessionId=flood$i&phoneNumber=%2B234800&text=" &
done
wait
```
**Expected:** All requests return valid CON/END responses

---

### 5. Data Exposure

**Objective:** Verify sensitive data is not leaked in responses or error messages.

**Test 5.1 — Error response content**
Send an invalid request and inspect the error body — verify no stack traces, file paths, or internal details are exposed.

**Test 5.2 — Patient list does not expose passwords**
```bash
curl http://127.0.0.1:8000/api/patients \
  -H "Authorization: Bearer VALID_TOKEN"
```
**Expected:** Response contains no password fields

**Test 5.3 — Login failure message**
```bash
curl -X POST http://127.0.0.1:8000/login/token \
  -d "username=doctor1&password=wrongpassword"
```
**Expected:** `401` with generic message — no hint about which field was wrong

---

### 6. Drug Rules Integrity

**Objective:** Verify the risk engine cannot be manipulated through the API.

**Test 6.1 — No endpoint exposes rule modification**
Verify there is no `PUT /api/rules` or `POST /api/rules` endpoint in `/docs`.
**Expected:** No rule modification endpoints exist

**Test 6.2 — Rules file read-only**
Verify `africa_priority_rules.json` cannot be overwritten through the API.
**Expected:** No file upload endpoint reaches the data directory

---

## Results Template

| Test ID | Description | Result | Notes |
|---|---|---|---|
| 1.1 | Unauthenticated patient list | Pass / Fail | |
| 1.2 | Invalid token | Pass / Fail | |
| 1.3 | Expired token | Pass / Fail | |
| 1.4 | No token on drug check | Pass / Fail | |
| 2.1 | CHW role escalation | Pass / Fail | |
| 3.1 | SQL injection in patient ID | Pass / Fail | |
| 3.2 | Oversized drug name | Pass / Fail | |
| 3.3 | Malformed JSON | Pass / Fail | |
| 4.1 | USSD missing field | Pass / Fail | |
| 4.2 | Script injection in USSD | Pass / Fail | |
| 4.3 | Long drug name in USSD | Pass / Fail | |
| 4.4 | USSD flood | Pass / Fail | |
| 5.1 | Error message content | Pass / Fail | |
| 5.2 | No passwords in patient list | Pass / Fail | |
| 5.3 | Login failure message | Pass / Fail | |
| 6.1 | No rule modification endpoint | Pass / Fail | |
| 6.2 | Rules file read-only | Pass / Fail | |

---

## Tools

- `curl` — HTTP request testing
- FastAPI `/docs` — endpoint enumeration
- ngrok inspector (`http://127.0.0.1:4040`) — request/response inspection
- Browser DevTools — response header inspection

---

## Remediation Priority

| Severity | Finding | Action |
|---|---|---|
| Critical | SECRET_KEY hardcoded in auth.py | Move to environment variable before production |
| High | QR payload unencrypted | Add AES-256 encryption in v2 |
| High | CORS allows all origins | Restrict to known frontend origins in production |
| Medium | No rate limiting on API | Add `slowapi` rate limiter in v2 |
| Medium | AT-Signature not validated | Add Africa's Talking webhook signature validation in v2 |
| Low | Error messages verbose | Add custom exception handlers in production |

---

*OCML-DI Penetration Test Plan v1.0 — Efe Ikharo*
