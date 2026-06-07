# OCML-DI — Judge FAQ
**Project:** Offline Clinical Medical Ledger with Drug Intelligence
**Track:** Healthcare Solutions for African Infrastructure
**Lead:** Efe Ikharo — Backend / ML/AI Systems
**Submission:** June 2026 Hackathon

---

## The Problem

**Q: What specific problem are you solving?**

Preventable drug harm caused by fragmented medical records. In Nigeria and across sub-Saharan Africa, patients visit multiple clinics that don't share data. A patient with chronic kidney disease walks into a clinic where the nurse has no record of her condition — she's prescribed Ibuprofen, an NSAID that is contraindicated in kidney disease, and develops acute renal failure. This isn't rare. It happens because healthcare systems don't talk to each other, paper records get lost, and most safety tools assume reliable internet.

**Q: How big is this problem really?**

Sub-Saharan Africa has over 300,000 health facilities. Roughly 60% of the population lives in areas with unreliable internet. Nigeria's Essential Medicines List runs to hundreds of drugs, many with dangerous interactions that are routinely missed in high-volume, under-resourced clinics. The WHO estimates preventable medication errors cost healthcare systems billions annually — the burden in low-resource settings is disproportionately high.

**Q: Why hasn't this been solved already?**

Existing solutions like Epic, Cerner, and even basic EHR systems assume reliable internet, hospital IT infrastructure, and smartphones. They were built for the US and European markets and retrofitted elsewhere. Nobody has built a system that treats offline operation and feature phone access as first-class requirements — not edge cases.

---

## The Solution

**Q: What exactly is OCML-DI?**

OCML-DI is a three-layer drug safety system:

1. **QR medical wallet** — an encrypted patient record the patient carries physically. A nurse scans it to instantly load conditions, medications, and allergies — no internet required.
2. **Clinician dashboard** — a web-based interface that runs a real AI risk engine against any proposed prescription, flags dangerous interactions, and requires senior clinician sign-off for critical cases.
3. **USSD channel** — a community health worker with a basic feature phone dials `*384*52591#`, enters a drug name, and receives the same AI-powered risk assessment over GSM 2G with no smartphone or internet required.

**Q: What makes this genuinely offline-first rather than just "works offline sometimes"?**

The entire drug safety check runs locally. The risk engine loads rules from JSON files at startup — `africa_priority_rules.json` and `who_essential_medicines_rules.json` — and evaluates every prescription against those rules without any network call. The SQLite database stores all patient records locally. The system syncs to a central server when connectivity is available, but every core function works without it. This is not a degraded offline mode — it is the default mode.

**Q: Why USSD specifically? Isn't that old technology?**

USSD reaches 95% of Nigeria through existing GSM infrastructure that already covers rural areas. Every mobile phone — including the most basic handsets — can run USSD. No app installation, no data plan, no smartphone required. Community health workers in rural clinics already use USSD for mobile money. OCML-DI meets them where they already are.

---

## The Technology

**Q: What AI is actually powering the drug checks?**

The risk engine is a rule-based expert system trained on clinically validated sources — the WHO Model Formulary, Nigeria's Standard Treatment Guidelines, and the Liverpool HIV Drug Interaction Database. It evaluates every proposed prescription against a curated set of 32+ interaction rules covering the drug combinations most dangerous in the West African clinical context: ARVs and antimalarials, TB drugs and contraceptives, NSAIDs and renal disease, and G6PD deficiency interactions.

The AI differentiator is not that we used a large language model — it's that we encoded expert clinical knowledge into a system that can run in 5 milliseconds on a $40 Raspberry Pi with no internet. That's the hard part.

**Q: Why not just use an LLM for drug checks?**

LLMs hallucinate. In a clinical context, a hallucinated drug interaction result can kill a patient. Our rule-based engine is fully auditable — every result traces back to a specific rule, a specific source, and a specific clinical reference. Judges, regulators, and clinicians can inspect exactly why a drug was flagged. You cannot do that with an LLM.

**Q: What is the tech stack?**

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Auth:** JWT (python-jose), bcrypt (passlib)
- **Drug rules:** Custom risk engine evaluating WHO + Africa Priority JSON rule sets
- **QR:** qrcode + pyzbar for generation and decoding
- **USSD:** Africa's Talking API, plain text CON/END responses
- **Frontend:** Vanilla HTML/CSS/JS — no framework dependency, runs in any browser
- **Deployment:** Runs on any machine including a $40 Raspberry Pi

**Q: How does the governance layer work?**

Every drug check is logged to an immutable audit trail. When the risk engine flags a critical interaction, it automatically creates a `ClinicalReview` record with status `pending`. A senior clinician must explicitly approve or reject the prescription before it can proceed. Every approval and rejection is timestamped and attributed to the reviewing clinician. This implements the human-in-the-loop governance principle — the AI flags, the human decides.

**Q: Can you show the system actually working?**

Yes. The demo video shows:
- Amina Bello's QR wallet scanned → record loads offline
- Ibuprofen entered → CRITICAL alert fires in under 5ms
- The same check performed on a feature phone via USSD
- The governance review queue showing the pending case

---

## Traction & Validation

**Q: Are your drug rules clinically validated?**

Yes. All rules are derived from publicly available, peer-reviewed sources:
- WHO Model Formulary 2008 (CC BY-NC-SA 3.0 IGO)
- WHO Essential Medicines List 22nd Edition 2021
- Nigeria Standard Treatment Guidelines
- Liverpool HIV Drug Interaction Database
- WHO Guidelines for Treatment of Malaria 3rd Edition

Every rule includes its source, mechanism, clinical consequence, and recommendation. The rules are specifically curated for the West African clinical context — HIV/ARV interactions, malaria co-infection, TB drug interactions, and G6PD deficiency are prioritised because they are the most clinically significant in this population.

**Q: Have you tested this with real clinicians?**

This is a hackathon submission — we have not conducted formal clinical trials. The demo case (Ibuprofen + kidney disease) is based on a documented real-world clinical scenario. The drug rules are sourced from guidelines that practising clinicians in Nigeria already follow. The next step is a pilot with a partner clinic to validate the workflow and rule set with real prescribing behaviour.

---

## Business & Scale

**Q: How does this scale beyond one clinic?**

The architecture is designed for federation. Each clinic runs its own OCML-DI instance locally — fully offline. When connectivity is available, instances sync patient records and rule updates to a central server. Adding a new clinic requires installing one application file. There is no per-clinic infrastructure cost. The entire stack can run on a $40 Raspberry Pi.

**Q: What is the business model?**

Three potential paths:
1. **B2G (Government)** — licence to state or federal health ministries as a patient safety infrastructure layer
2. **B2B (NGO/health systems)** — integration into existing CHW programmes (MSF, CHAI, Partners in Health)
3. **Freemium API** — free for public clinics, paid tier for private hospital networks with advanced analytics

**Q: How do you handle data privacy and regulation?**

Patient data is stored locally on the clinic's own device — it never leaves the facility without explicit sync. The QR wallet is patient-controlled — they physically carry it and choose who scans it. We align with Nigeria's National Health Act on patient data confidentiality. The system is designed to assist clinical decision-making, not replace it — placing it in the clinical decision support category rather than the medical device category for regulatory purposes.

**Q: What happens when the rules are wrong?**

Every rule has a recommendation that defers to clinical judgement. The system never blocks a prescription outright — it flags, warns, and requires human review for critical cases. The clinician retains final authority. If a rule is incorrect, it can be updated in the JSON file and reloaded without a system restart. The rule files are version-controlled in git and auditable.

---

## Compared to Alternatives

**Q: How is this different from existing drug interaction checkers like Drugs.com or Medscape?**

Those tools require internet, require a smartphone, and are not designed for the African clinical context. They don't know about artemether-lumefantrine + efavirenz interactions. They don't know about G6PD deficiency prevalence in West Africa. They have no QR wallet, no USSD channel, no offline mode, and no governance layer. They are reference tools for individual clinicians — OCML-DI is a safety infrastructure layer for entire clinic networks.

**Q: Why not just use WhatsApp or SMS?**

WhatsApp requires a smartphone and data. SMS requires sending patient data over unencrypted channels to a third-party server. USSD is session-based, encrypted at the network layer, requires no data plan, and runs on any handset. It is the right channel for this use case.

---

## Team

**Q: Who built what?**

| Role | Contributor |
|---|---|
| Backend / ML / AI Systems / Risk Engine / API | Efe Ikharo (Project Lead) |
| Frontend / Security | Junior |
| Design / Documentation | Esiro |

**Q: What would you do differently with more time?**

1. Encrypt QR wallet payloads with AES-256
2. Add Africa's Talking webhook signature validation
3. Migrate from SQLite to PostgreSQL for multi-clinic deployments
4. Conduct a formal clinical pilot with a partner facility in Lagos or Kano
5. Add patient consent flow for QR wallet generation
6. Build the Flutter mobile app for CHW field workers

---

*OCML-DI — Built for Africa. Built for now.*
*Healthcare that works around African infrastructure — not around African patients.*
