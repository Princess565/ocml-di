# OCML-DI — Demo Script
### Hackathon Pitch & Investor Edition | 2–3 Minutes

---

## OPENING — The Problem (0:00 – 0:30)

**Narration:**
> "Every year, thousands of patients across Africa are harmed — not by the wrong diagnosis, not by lack of medicine — but because one doctor didn't know what another prescribed. A patient with kidney disease walks into a clinic in Kano. The nurse has no record of her condition. She's prescribed Ibuprofen. Within 48 hours, she's in acute renal failure.
>
> This isn't a rare tragedy. It's Tuesday.
>
> Africa has 200 million people living in areas with unreliable internet. Healthcare systems don't talk to each other. Paper records get lost. And patients pay with their lives."

**Visuals:**
- Black screen → single stat fades in: *"1 in 3 Africans has no accessible medical record"*
- Cut to: patient holding a worn paper prescription
- Overlay text appears: **Your Medical Record, Your Safety**

---

## SOLUTION OVERVIEW (0:30 – 1:00)

**Narration:**
> "OCML-DI — Offline-first Clinical Medical Ledger with Drug Intelligence — is a portable medical safety system built specifically for African infrastructure realities. Not as an afterthought. As the foundation.
>
> It works through three layers working in concert: a portable QR medical wallet the patient carries with them. A clinician dashboard that flags dangerous drug interactions in real time. And a USSD access channel — so a nurse in a rural clinic with a basic phone and no internet can run the same safety check as a doctor in a teaching hospital."

**Visuals:**
- Animated three-layer diagram: QR wallet → Dashboard → USSD phone
- Each layer lights up as named
- Tagline appears: *"Designed around African infrastructure — not despite it"*

---

## LIVE DEMO (1:00 – 2:00)

**Narration:**
> "Let's see it in action. Same patient. Same clinic. Same Tuesday — but this time, OCML-DI is there.
>
> The nurse scans the patient's QR wallet. Her full medical record loads instantly — no internet required, encrypted, tamper-proof. Conditions: chronic kidney disease. Current medications: lisinopril.
>
> The nurse enters the proposed prescription: Ibuprofen.
>
> Watch what happens."

**[PAUSE — let the demo breathe]**

> "OCML-DI's risk engine — trained on WHO guidelines, Nigeria's Essential Medicines List, and the EMDEX — flags a CRITICAL interaction. NSAIDs are contraindicated in kidney disease. A senior clinician must review and approve before this drug is dispensed. Every action is logged. Accountability is built in.
>
> Now — same safety check. Different setting. No smartphone. No internet."

**[Switch to USSD simulator]**

> "A community health worker dials `*384*52591#`. Enters the drug name: Ibuprofen. Three seconds later — HIGH RISK alert. Same intelligence. Same protection. Feature phone. Zero data."

**Visuals:**
- Dashboard: patient record loads → Ibuprofen entered → RED alert flashes → "Requires senior clinician review"
- Audit log appears showing timestamped action
- Cut to USSD simulator: dial sequence → drug entry → warning text appears on screen
- Side-by-side: smartphone dashboard vs. basic phone USSD — same result

---

## IMPACT & VISION (2:00 – 2:30)

**Narration:**
> "OCML-DI is not a pilot project hoping to scale. It is a resilient infrastructure play — built offline-first, USSD-capable, and clinically validated for the West African context from day one.
>
> The addressable market is every clinic, pharmacy, and community health worker across sub-Saharan Africa — an ecosystem of over 300,000 health facilities operating under the exact constraints we've built for.
>
> We're not asking Africa to wait for better internet. We built the safety net that works right now, with what's already there."

**Visuals:**
- Map of sub-Saharan Africa with health facility density overlay
- Stats fade in: *300,000+ health facilities | 1.2B people | 60% in low-connectivity zones*
- Final frame: OCML-DI logo + tagline

**Tagline overlay — hold for 5 seconds:**
> **"Healthcare that works around African infrastructure — not around African patients."**

---

## CLOSING SLIDE (Team Credits)

| Role | Name |
|------|------|
| Backend / ML Systems | Efe Ikharo — Project Lead |
| Frontend / Security | [Junior] |
| Design / Documentation | Esiro |

*OCML-DI — Built for Africa. Built for now.*

---

## SPEAKER NOTES

- **Pace:** Slow down at the demo moment — silence is powerful. Let judges watch the alert fire.
- **The USSD moment** is your differentiator. Emphasise it. Most teams will not have this.
- **If asked about scale:** "Our architecture is SQLite-first with a sync layer — it runs on a $40 Raspberry Pi. Deployment cost per clinic is near zero."
- **If asked about data privacy:** "All patient data is encrypted at rest. The QR wallet is patient-controlled — they decide who scans it."
- **If asked about regulation:** "We've aligned our drug interaction rules with the Nigeria Standard Treatment Guidelines and WHO Model Formulary. We're designed to assist clinical decision-making, not replace it."
