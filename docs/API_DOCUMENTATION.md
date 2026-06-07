# OCML-DI API Documentation
**Version:** 0.1.0 | **Date:** June 2026
**Owner:** Efe Ikharo — Project Lead, ML/AI Systems
**Base URL:** `http://127.0.0.1:8000` (local) | `https://darkish-margin-spearfish.ngrok-free.dev` (public)
**Interactive docs:** `{BASE_URL}/docs`

---

## Overview

OCML-DI exposes a RESTful JSON API for the clinician dashboard and Flutter mobile app, plus a plain-text USSD callback endpoint for Africa's Talking integration.

All protected endpoints require a Bearer JWT token obtained from `/login/token`.

---

## Authentication

### POST `/login/token`
Obtain a JWT access token.

**Request** — `application/x-www-form-urlencoded`
```
username=doctor1&password=pass123
```

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "doctor",
  "name": "Dr Efe Ikharo"
}
```

**Error** `401 Unauthorized`
```json
{ "detail": "Invalid username or password" }
```

**Usage in subsequent requests:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Demo credentials:**

| Username | Password | Role |
|---|---|---|
| doctor1 | pass123 | doctor |
| pharma1 | pharma123 | pharmacist |
| nurse1 | nurse123 | nurse |
| chw1 | chw123 | chw |

---

## System

### GET `/`
Health check and version info. No auth required.

**Response** `200 OK`
```json
{
  "message": "OCML-DI API is running",
  "version": "0.1.0",
  "status": "online"
}
```

### GET `/health`
Liveness probe.

**Response** `200 OK`
```json
{
  "status": "ok",
  "timestamp": "2026-06-07T11:18:46.577Z"
}
```

### GET `/api/sync`
Returns the full Africa Priority Rules JSON — used by the sync layer to distribute updated drug rules to offline clinics.

**Response** `200 OK` — full contents of `africa_priority_rules.json`

---

## Patients

### GET `/api/patients`
List all registered patients. Paginated.

**Auth:** Required
**Query params:**
- `skip` (int, default 0) — offset
- `limit` (int, default 50) — page size

**Response** `200 OK`
```json
[
  {
    "id": "a3f2c1d4-...",
    "full_name": "Amina Bello",
    "phone": "+234 802 xxx xxxx",
    "gender": "female",
    "conditions": ["Chronic kidney disease", "Hypertension"],
    "medications": ["Lisinopril 10mg", "Furosemide 40mg"],
    "allergies": ["Penicillin"],
    "created_at": "2026-06-04T09:14:00.000Z"
  }
]
```

---

### GET `/api/patients/{patient_id}`
Get a single patient record by ID. Writes an audit log entry on every access.

**Auth:** Required
**Path param:** `patient_id` (string UUID)

**Response** `200 OK` — single patient object (same schema as above)

**Error** `404 Not Found`
```json
{ "detail": "Patient not found" }
```

---

### POST `/api/patients`
Register a new patient.

**Auth:** Required
**Request** — `application/json`
```json
{
  "full_name": "Amina Bello",
  "phone": "+234 802 xxx xxxx",
  "gender": "female",
  "conditions": [
    { "name": "Chronic kidney disease", "severity": "moderate" }
  ],
  "current_medications": [
    { "name": "Lisinopril 10mg", "dose": "10mg once daily" }
  ],
  "allergies": [
    { "allergen": "Penicillin", "reaction": "rash" }
  ]
}
```

**Response** `201 Created` — created patient object

---

### PUT `/api/patients/{patient_id}`
Update an existing patient record.

**Auth:** Required
**Request** — same schema as POST
**Response** `200 OK` — updated patient object

---

## Drug Safety

### POST `/api/check`
Run a drug interaction check against the OCML-DI risk engine. This is the core AI endpoint.

Can operate in two modes:
- **Patient mode** — supply `patient_id` to load conditions and medications from DB
- **Inline mode** — supply `conditions`, `current_medications`, and `allergies` directly (used by USSD and Flutter)

**Auth:** Required
**Request** — `application/json`
```json
{
  "proposed_drug": "ibuprofen",
  "patient_id": "a3f2c1d4-...",
  "current_medications": [],
  "conditions": [],
  "allergies": [],
  "channel": "dashboard",
  "clinician_id": "doctor1"
}
```

**Response** `200 OK`
```json
{
  "check_id": "b7e3a2f1-...",
  "proposed_drug": "ibuprofen",
  "patient_id": "a3f2c1d4-...",
  "interactions_found": [
    {
      "rule_id": "AFR-001",
      "cluster": "NSAID_RENAL",
      "interaction_type": "drug_condition",
      "drug_a": "ibuprofen",
      "drug_b_or_condition": "chronic kidney disease",
      "risk_score": 9,
      "risk_level": "critical",
      "warning_message": "CRITICAL: NSAIDs are contraindicated in patients with kidney disease.",
      "recommendation": "Use paracetamol instead. Do not dispense.",
      "mechanism": "NSAIDs inhibit prostaglandin synthesis, reducing renal blood flow and GFR.",
      "alternatives": ["paracetamol"],
      "source": "africa_priority_rules"
    }
  ],
  "max_risk_score": 9,
  "max_risk_level": "critical",
  "requires_human_review": true,
  "offline_mode": true,
  "evaluation_ms": 3,
  "ussd_summary": "CRITICAL RISK\nDrug: ibuprofen\nRisk: CRITICAL (9/10)\n\nDO NOT DISPENSE.\nSenior clinician review required.",
  "timestamp": "2026-06-07T11:18:46.577Z"
}
```

**Risk levels:** `low` | `moderate` | `high` | `critical`

**Channel values:** `dashboard` | `ussd` | `qr_scan` | `api`

**Side effects:**
- Always writes an audit log entry
- If `requires_human_review = true`, creates a `ClinicalReview` record with status `pending`

---

## Clinical Reviews

### GET `/api/reviews`
List clinical reviews requiring human sign-off.

**Auth:** Required
**Query params:**
- `status_filter` (string, default `pending`) — filter by status. Use `all` for all reviews.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "check_id": "b7e3a2f1-...",
    "patient_id": "a3f2c1d4-...",
    "patient_name": "Amina Bello",
    "proposed_drug": "ibuprofen",
    "risk_score": 9,
    "risk_level": "critical",
    "warning_summary": "CRITICAL: NSAIDs contraindicated in kidney disease.",
    "status": "pending",
    "reviewed_by": null,
    "review_notes": null,
    "created_at": "2026-06-07T11:18:46.577Z",
    "reviewed_at": null
  }
]
```

**Status values:** `pending` | `approved` | `rejected`

---

### POST `/api/reviews/{review_id}/approve`
Approve a pending clinical review. Records the reviewing clinician and timestamp.

**Auth:** Required
**Path param:** `review_id` (int)
**Query param:** `notes` (string, optional) — clinical notes

**Response** `200 OK` — updated review object with `status: "approved"`

---

### POST `/api/reviews/{review_id}/reject`
Reject a pending clinical review.

**Auth:** Required
**Path param:** `review_id` (int)
**Query param:** `notes` (string, optional) — reason for rejection

**Response** `200 OK` — updated review object with `status: "rejected"`

---

## Audit Log

### GET `/api/audit`
Return audit log entries — most recent first. Every significant clinical action is logged here.

**Auth:** Required
**Query params:**
- `skip` (int, default 0)
- `limit` (int, default 100)

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "action": "drug_check_performed",
    "actor_id": "doctor1",
    "patient_name": "Amina Bello",
    "channel": "dashboard",
    "risk_score": 9,
    "details": {
      "drug": "ibuprofen",
      "risk_level": "critical",
      "channel": "dashboard",
      "patient_id": "a3f2c1d4-..."
    },
    "timestamp": "2026-06-07T11:18:46.577Z"
  }
]
```

**Logged actions:**

| Action | Trigger |
|---|---|
| `patient_created` | POST `/api/patients` |
| `patient_accessed` | GET `/api/patients/:id` |
| `drug_check_performed` | POST `/api/check` |
| `critical_alert_raised` | Drug check with `requires_human_review = true` |
| `review_completed` | Approve or reject review |
| `ussd_check_performed` | USSD drug check |
| `qr_wallet_generated` | QR code export |

---

## Clinician Dashboard

### GET `/clinician/dashboard`
Returns pending clinical reviews as an HTML dashboard page.

**Auth:** Required (session cookie)

### GET `/clinician/patient/{patient_id}`
Returns patient record as HTML.

### POST `/clinician/patient/{patient_id}/qr`
Generates and returns a QR code for the patient's medical wallet as base64 PNG embedded in HTML.

### POST `/clinician/patient/qr/decode`
Decodes a QR wallet image uploaded as a file and returns the patient record.

**Request** — `multipart/form-data`
- `file` — image file containing QR code

---

## USSD

### POST `/ussd/callback`
Africa's Talking USSD callback. Receives session data as form fields, returns plain text prefixed with `CON` (continue session) or `END` (terminate session).

**No auth required** — Africa's Talking calls this directly.

**Request** — `application/x-www-form-urlencoded`
```
sessionId=AT-session-123&phoneNumber=%2B2348000000000&text=
```

**USSD flow:**

| Input `text` | Response |
|---|---|
| `` (empty) | `CON` — welcome menu |
| `1` | `CON` — prompt for drug name |
| `1*ibuprofen` | `END` — CRITICAL risk alert |
| `1*paracetamol` | `END` — SAFE result |
| `2` | `END` — about OCML-DI |
| `0` | `END` — goodbye |

**Example response (critical):**
```
END CRITICAL RISK
Drug: ibuprofen
Risk: CRITICAL (9/10)

DO NOT DISPENSE.
Senior clinician review
required immediately.

[OCML-DI + WHO rules]
```

**Example response (safe):**
```
END SAFE
Drug: paracetamol
Risk: LOW (1/10)

No critical interactions
found. Safe to dispense.

[OCML-DI + WHO rules]
```

---

## Error Responses

| Code | Meaning |
|---|---|
| `400 Bad Request` | Malformed request body |
| `401 Unauthorized` | Missing or invalid JWT token |
| `403 Forbidden` | Valid token but insufficient role |
| `404 Not Found` | Resource does not exist |
| `422 Unprocessable Entity` | Request validation failed (Pydantic) |
| `500 Internal Server Error` | Unexpected server error |

**Validation error example:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "proposed_drug"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## Flutter Integration Guide

To integrate with the Flutter mobile app:

**1. Get a token:**
```dart
final response = await http.post(
  Uri.parse('$baseUrl/login/token'),
  body: {'username': 'chw1', 'password': 'chw123'},
);
final token = jsonDecode(response.body)['access_token'];
```

**2. Run a drug check:**
```dart
final response = await http.post(
  Uri.parse('$baseUrl/api/check'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'proposed_drug': 'ibuprofen',
    'conditions': ['chronic kidney disease'],
    'current_medications': ['lisinopril'],
    'channel': 'api',
  }),
);
final result = jsonDecode(response.body);
final riskLevel = result['max_risk_level']; // 'critical'
final requiresReview = result['requires_human_review']; // true
```

**3. Register a patient:**
```dart
final response = await http.post(
  Uri.parse('$baseUrl/api/patients'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'full_name': 'Amina Bello',
    'phone': '+234802xxxxxxx',
    'gender': 'female',
    'conditions': [{'name': 'Chronic kidney disease'}],
    'current_medications': [{'name': 'Lisinopril 10mg'}],
    'allergies': [{'allergen': 'Penicillin'}],
  }),
);
```

---

## Rate Limits

Currently no rate limiting is enforced on the API. Africa's Talking enforces its own limits on the USSD channel. Rate limiting via `slowapi` is planned for v2.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 0.1.0 | June 2026 | Initial release — full patient CRUD, drug check, USSD callback, JWT auth, audit log |

---

*OCML-DI API Documentation v0.1.0 — Efe Ikharo*