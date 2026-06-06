# OCML-DI — Full Demo Script
### Hackathon Submission | Healthcare Track | 5 Minutes Max
### Format: AI-Generated Video (Recommended: HeyGen / Synthesia / Runway)

---

## VIDEO PRODUCTION NOTES

- **Presenter:** AI avatar (professional, calm, Nigerian or pan-African appearance)
- **Voice:** Clear, measured — not rushed. Let pauses work.
- **Background:** Clean clinical environment OR abstract dark tech background with green/white accents
- **Screen recordings:** Record dashboard and USSD simulator separately, edit in post
- **Music:** Subtle ambient underscore — low tension opening, resolve to hopeful by closing
- **Captions:** Always on. Many judges will watch muted.
- **Aspect ratio:** 16:9, 1080p minimum
- **Total runtime:** 4:30 – 5:00

---

## SCENE 1 — THE PROBLEM (0:00 – 0:45)

**[Visual: Black screen. Silence for 2 seconds.]**

**[Text fades in, white on black:]**
> *"Every year, thousands of patients across Africa are harmed not by the wrong diagnosis — but because one doctor didn't know what another prescribed."*

**[Cut to: avatar presenter — serious tone]**

**Narration:**
> "Meet Amina. She is 38 years old. She lives in Kano, Nigeria. She has chronic kidney disease — a condition she was diagnosed with two years ago at a hospital 90 kilometres away.
>
> Today, she walks into a local clinic with a fever and joint pain. The nurse has no access to her records. The hospital doesn't share data with this clinic. Her paper prescription was lost six months ago.
>
> The nurse prescribes Ibuprofen. It is cheap, available, and effective — for most patients.
>
> Within 48 hours, Amina is in acute renal failure."

**[Visual: Simple animation — patient icon → clinic icon → red warning icon. No gore, no distress.]**

**[Text overlay:]**
> *"This is not a rare tragedy. Across sub-Saharan Africa — this is Tuesday."*

**[Pause — 1.5 seconds of silence]**

**Narration:**
> "Nigeria alone has over 200 million people. Sixty percent live in areas with unreliable internet. Healthcare systems don't talk to each other. And patients — especially the most vulnerable — carry the cost of that silence."

**[Visual: Stat cards appear one by one]**
- *1 in 3 Africans has no accessible medical record*
- *300,000+ health facilities operating without shared data infrastructure*
- *Preventable drug harm costs African health systems billions annually*

---

## SCENE 2 — INTRODUCING OCML-DI (0:45 – 1:30)

**[Cut to: avatar — tone shifts, confident]**

**Narration:**
> "What if Amina's safety didn't depend on the internet being available? What if it didn't depend on hospitals sharing data? What if the safety net travelled with her?
>
> This is OCML-DI."

**[Visual: Logo animation — clean, modern]**

**[Text overlay:]**
> **Offline-first Clinical Medical Ledger with Drug Intelligence**

**Narration:**
> "OCML-DI is a portable medical safety system built specifically for African infrastructure realities — not as an afterthought, but as the foundation.
>
> It operates through three layers working together:"

**[Visual: Animated three-layer diagram — each lights up as named]**

**Narration:**
> "**One** — A portable QR medical wallet. Encrypted. Patient-controlled. Works with no internet, no data connection, no shared hospital system.
>
> **Two** — An AI-powered clinician dashboard. It checks every prescription against the patient's conditions, current medications, and allergies in real time — using drug interaction intelligence built on WHO guidelines, Nigeria's Essential Medicines List, and the EMDEX.
>
> **Three** — A USSD access channel. So a community health worker with a basic feature phone — no smartphone, no internet — can run the exact same safety check."

**[Visual: Three icons — QR code, dashboard screenshot, basic phone — appear side by side]**

**[Text overlay:]**
> *"Designed around African infrastructure. Not despite it."*

---

## SCENE 3 — LIVE DEMO (1:30 – 3:30)

**[Cut to: screen recording of dashboard — avatar narrates over it]**

**Narration:**
> "Let's go back to Amina — but this time, OCML-DI is in the clinic.
>
> The nurse opens the OCML-DI clinician dashboard. She scans Amina's QR wallet."

**[Visual: QR scan animation → patient record loads]**

**Narration:**
> "Amina's full medical record loads instantly. No internet required. Conditions: chronic kidney disease. Current medications: lisinopril. Allergies: penicillin.
>
> The nurse enters the proposed prescription — Ibuprofen."

**[Visual: Drug name typed into prescription field → processing animation]**

**[PAUSE — 1.5 seconds — let the alert fire on screen]**

**[Visual: RED alert banner floods the screen]**
> ⚠️ **CRITICAL INTERACTION DETECTED**
> NSAIDs are contraindicated in patients with chronic kidney disease.
> This prescription requires senior clinician review before dispensing.

**Narration:**
> "The AI risk engine — running entirely offline — has detected a critical drug-condition interaction. NSAIDs reduce blood flow to the kidneys. In a patient with CKD, this can trigger acute renal failure.
>
> The system doesn't just warn. It enforces a governance layer — a senior clinician must review and approve before this drug can be dispensed. The action is timestamped and logged for full accountability."

**[Visual: Audit log appears — timestamp, nurse ID, flagged drug, pending review status]**

**Narration:**
> "The recommendation appears automatically: use paracetamol instead. Safe. Available. Effective for this patient.
>
> Amina goes home safe."

**[Visual: Green checkmark — patient icon leaves clinic safely]**

**[Cut to: USSD simulator screen]**

**Narration:**
> "Now — same safety intelligence. Completely different setting.
>
> A community health worker in a rural clinic. Basic phone. No internet. No smartphone."

**[Visual: Feature phone screen — USSD dial sequence]**

**Narration:**
> "She dials `*384*52591#`. Selects option one — drug safety check. Enters the drug name: Ibuprofen."

**[Visual: Text appears on USSD screen]**
> `HIGH RISK: Ibuprofen — dangerous for patients with kidney disease. Do not dispense. Recommend paracetamol.`

**Narration:**
> "Three seconds. No data connection. The same AI-powered drug intelligence — delivered over basic telecoms infrastructure that already reaches 95% of Nigeria."

**[Visual: Side-by-side — smartphone dashboard alert vs. feature phone USSD alert]**

**[Text overlay:]**
> *"Same intelligence. Same protection. Any device. Anywhere."*

---

## SCENE 4 — TECHNICAL DEPTH (3:30 – 4:15)

**[Cut to: avatar — slightly more technical tone, but still accessible]**

**Narration:**
> "OCML-DI is a real, working system — not a prototype. Let's talk about what's under the hood.
>
> The backend is built on FastAPI with a SQLite-first architecture — meaning it runs fully offline, and syncs to a central server whenever connectivity is available. No internet required for core functionality.
>
> The AI risk engine checks every prescription against a curated rule set derived from the WHO Model Formulary, Nigeria's Standard Treatment Guidelines, and the Liverpool HIV Drug Interaction Database — with priority rules for the drug combinations most dangerous in the West African clinical context: ARVs and antimalarials, TB drugs and anticoagulants, NSAIDs and renal disease."

**[Visual: Risk engine rule visualization — nodes connecting drug names to conditions to risk levels]**

**Narration:**
> "Patient records are encrypted and embedded in QR codes — patient-controlled, portable, and readable without any network connection.
>
> The entire stack can run on a $40 Raspberry Pi. Deployment cost per clinic — near zero."

**[Visual: Architecture diagram — clean, simple: QR → FastAPI backend → Risk Engine → Dashboard / USSD]**

**[Text overlay:]**
> *"Offline-first. AI-powered. Infrastructure-aware."*

---

## SCENE 5 — IMPACT & VISION (4:15 – 5:00)

**[Cut to: avatar — warm, visionary tone]**

**Narration:**
> "OCML-DI is not asking Africa to wait for better infrastructure. We built the safety net that works with what's already there.
>
> Our target users are the 300,000 health facilities across sub-Saharan Africa operating under exactly these constraints — clinics, pharmacies, community health workers. People who are trying to do the right thing, and just need the right tool.
>
> In the short term — we prevent Amina's story from happening again. In the long term — we become the portable health safety layer for a continent."

**[Visual: Africa map — health facility density overlay — dots light up progressively]**

**Narration:**
> "Because healthcare safety shouldn't depend on your postcode. It shouldn't depend on the hospital you were born near, or whether the internet is working today.
>
> It should travel with you."

**[Final visual: OCML-DI logo — clean, held for 4 seconds]**

**[Tagline fades in:]**
> **"Healthcare that works around African infrastructure — not around African patients."**

**[Fade to black — team credits appear:]**

| | |
|---|---|
| **Backend / AI Systems** | Efe Ikharo — Project Lead |
| **Frontend / Security** | [Junior] |
| **Design / Documentation** | Esiro |

*OCML-DI · Built for Africa · Built for now*

---

## SPEAKER / PRODUCTION NOTES

### Handling the Judging Criteria

| Criterion | Where it's addressed in the video |
|---|---|
| Problem Understanding | Scene 1 — Amina's story, named user, real clinical context |
| User & Context Fit | Scene 3 USSD section — "would they actually use this?" answered directly |
| Technical Execution | Scene 4 — FastAPI, SQLite, offline-first, real working system |
| AI Relevance | Scene 3 & 4 — risk engine is the core differentiator, shown working live |
| Uniqueness | Scene 2 — three-layer architecture, USSD+QR+AI combination is novel |
| Demo Quality | Scene 3 — screen recording of working product, real alert firing |

### Anticipated Investor / Judge Questions — Prepare These

**"How do you scale this?"**
> "SQLite syncs to a central server on connectivity. Adding a new clinic is installing one file. No per-clinic infrastructure cost."

**"What about data privacy?"**
> "Patient data is encrypted at rest. The QR wallet is patient-controlled — they physically carry it and choose who scans it."

**"Is this regulated?"**
> "Our rules align with Nigeria Standard Treatment Guidelines and WHO Model Formulary. We're a clinical decision support tool — we assist, we don't replace, the clinician."

**"Why won't a big EHR company just do this?"**
> "They have. For hospitals with reliable internet and IT departments. We built for the 300,000 facilities they've written off."

### Video Tools Recommended
- **Avatar:** HeyGen (best African avatar selection) or Synthesia
- **Screen recording:** OBS Studio or Loom
- **Editing:** CapCut (free, fast) or DaVinci Resolve
- **Diagrams/animations:** Canva or Figma
- **Music:** Pixabay royalty-free or EpidemicSound

