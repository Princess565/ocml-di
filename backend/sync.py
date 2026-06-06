import requests
from .database import SessionLocal, PatientDB

CENTRAL_API = "https://central.ocml-di.org/api/sync"

def sync_patients():
    db = SessionLocal()
    patients = db.query(PatientDB).all()
    payload = [p.__dict__ for p in patients]

    try:
        r = requests.post(CENTRAL_API, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Sync successful")
        else:
            print("⚠️ Sync failed:", r.text)
    except Exception as e:
        print("⚠️ Offline, sync deferred:", e)
