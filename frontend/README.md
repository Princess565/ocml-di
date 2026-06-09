# OCML-DI Frontend

**Offline-first clinician portal for the OCML-DI drug safety system.**

---

## Folder Structure

```
frontend/
├── index.html                  ← Entry point — open this in a browser
│
├── assets/
│   ├── css/
│   │   ├── main.css            ← Design tokens, global styles, components
│   │   └── shell.css           ← Sidebar + topbar layout
│   └── js/
│       └── app.js              ← Main app logic (router, dashboard, USSD, etc.)
│
├── components/
│   ├── Shell.js                ← Sidebar/topbar renderer (ES module)
│   ├── DrugChecker.js          ← Drug interaction check form + result display
│   └── QRWallet.js             ← QR code generator + download
│
├── pages/
│   ├── login.html              ← Login page fragment
│   ├── dashboard.html          ← Dashboard screen fragment
│   ├── patients.html           ← Patients list screen fragment
│   ├── patient-record.html     ← Patient record + QR + drug check
│   └── ussd.html               ← USSD simulator screen
│
└── services/
    ├── api.js                  ← All HTTP calls to the FastAPI backend
    └── data.js                 ← Offline patient data + drug rules (fallback)
```

---

## How to Run

### Option 1 — Open directly (demo mode, no backend needed)
Just open `index.html` in any browser. All data is offline. No server required.

### Option 2 — Connect to your FastAPI backend

1. Start the backend:
```bash
cd C:\Users\USER\ocml-di
& "C:\Users\USER\ocml-di\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload
```

2. Open `index.html` in your browser. The frontend calls `http://127.0.0.1:8000` by default.

3. If using ngrok, update `BASE_URL` in `services/api.js`:
```js
const BASE_URL = 'https://your-ngrok-url.ngrok-free.app';
```

---

## Backend API Endpoints Used

| Frontend action | Backend route | Method |
|---|---|---|
| Login | `/login` | POST (form data) |
| List patients | `/clinician/patients` | GET |
| Get patient | `/clinician/patient/:id` | GET |
| Drug check | `/clinician/check-drug` | POST |
| Generate QR | `/clinician/patient/:id/qr` | POST |
| Decode QR | `/clinician/patient/qr/decode` | POST |
| Pending reviews | `/clinician/dashboard` | GET |
| Approve review | `/clinician/review/:id/approve` | POST |
| Reject review | `/clinician/review/:id/reject` | POST |
| USSD session | `/ussd/ussd` | POST (form data) |

---

## Offline Fallback

All pages work without a backend. When the API is unreachable:
- Patient data loads from `services/data.js`
- Drug rules are checked against the local `DRUG_RULES` dictionary
- QR codes are generated client-side using `qrcodejs`
- USSD responses use pre-built scenario scripts

This is intentional — OCML-DI is **offline-first by design**.

---

## Adding the Frontend to Your Backend (Jinja2)

To serve the frontend from FastAPI using Jinja2 templates, add to `backend/main.py`:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount("/static", StaticFiles(directory="../frontend"), name="static")
templates = Jinja2Templates(directory="../frontend")

@app.get("/", response_class=HTMLResponse)
def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

Then install static files support:
```bash
pip install aiofiles
```

---

## CORS

The backend already has CORS configured in `main.py`:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
This allows the frontend to call the API from any origin, including a browser opened directly from disk (`file://`).

---

## Demo Flow (for video recording)

1. Open `index.html` → login screen appears
2. Click **Sign in** (credentials pre-filled)
3. Dashboard loads with 38 critical alerts
4. Click **Amina Bello** → patient record opens
5. Type `Ibuprofen` in drug check → **CRITICAL alert fires**
6. Navigate to **USSD simulator**
7. Press green dial button → select scenario → type drug → alert appears
8. Show side-by-side: dashboard alert = USSD alert = same AI intelligence

---

*OCML-DI · Built for Africa · Built for now*
