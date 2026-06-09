/**
 * OCML-DI · Local Data Store
 * ─────────────────────────────────────────────
 * Offline-first patient data.
 * Used when the backend is unreachable.
 * In production this is seeded from the SQLite DB
 * via the sync layer.
 */

export const PATIENTS = {
  'PAT-0041': {
    id: 'PAT-0041', name: 'Amina Bello', initials: 'AB', color: '#e24b4a',
    age: 38, gender: 'Female', phone: '+234 802 xxx xxxx',
    facility: 'Kano General Clinic', lastVisit: 'Today, 09:14',
    conditions: ['Chronic kidney disease', 'Hypertension'],
    medications: ['Lisinopril 10mg', 'Furosemide 40mg'],
    allergies: ['Penicillin'],
    history: [
      { drug: 'Ibuprofen',      by: 'Dr E. Ikharo', date: 'Today',   status: 'blocked'  },
      { drug: 'Paracetamol 500mg', by: 'Dr A. Musa', date: 'Jun 01', status: 'approved' },
      { drug: 'Amlodipine 5mg',    by: 'Dr A. Musa', date: 'May 20', status: 'approved' },
    ],
  },
  'PAT-0039': {
    id: 'PAT-0039', name: 'Kofi Asante', initials: 'KA', color: '#ba7517',
    age: 31, gender: 'Male', phone: '+233 244 xxx xxx',
    facility: 'Accra Ridge Hospital', lastVisit: 'Today, 08:55',
    conditions: ['HIV positive', 'Malaria'],
    medications: ['Efavirenz 600mg', 'TDF/3TC'],
    allergies: ['Sulphonamides'],
    history: [
      { drug: 'Artemether-lumefantrine', by: 'Dr E. Ikharo', date: 'Today',   status: 'blocked'  },
      { drug: 'Cotrimoxazole',           by: 'Dr K. Mensah', date: 'May 28',  status: 'review'   },
    ],
  },
  'PAT-0037': {
    id: 'PAT-0037', name: 'Fatima Nkosi', initials: 'FN', color: '#185fa5',
    age: 26, gender: 'Female', phone: '+27 82 xxx xxxx',
    facility: 'Johannesburg CHC', lastVisit: 'Yesterday',
    conditions: ['Tuberculosis'],
    medications: ['Rifampicin 600mg', 'Isoniazid 300mg', 'Pyrazinamide 1500mg'],
    allergies: [],
    history: [
      { drug: 'Oral contraceptive pill', by: 'Dr F. Nkosi', date: 'Jun 02', status: 'review' },
    ],
  },
};

export const ALL_PATIENTS = [
  { id: 'PAT-0041', name: 'Amina Bello',   age: 38, conditions: 'CKD, Hypertension',      meds: 'Lisinopril, Furosemide',      visit: 'Today',      alertStatus: 'alert',   key: 'PAT-0041' },
  { id: 'PAT-0039', name: 'Kofi Asante',   age: 31, conditions: 'HIV, Malaria',            meds: 'Efavirenz, TDF/3TC',          visit: 'Today',      alertStatus: 'alert',   key: 'PAT-0039' },
  { id: 'PAT-0037', name: 'Fatima Nkosi',  age: 26, conditions: 'Tuberculosis',            meds: 'Rifampicin, INH, PZA',        visit: 'Yesterday',  alertStatus: 'pending', key: 'PAT-0037' },
  { id: 'PAT-0034', name: 'Emmanuel Osei', age: 67, conditions: 'Heart failure, HTN',      meds: 'Digoxin, Furosemide',         visit: 'Yesterday',  alertStatus: 'pending' },
  { id: 'PAT-0031', name: 'Adaeze Okafor', age: 44, conditions: 'Type 2 diabetes',         meds: 'Metformin 500mg',             visit: '2 days ago', alertStatus: 'safe'    },
  { id: 'PAT-0028', name: 'Chidi Eze',     age: 55, conditions: 'Epilepsy',                meds: 'Phenobarbitone 60mg',         visit: '3 days ago', alertStatus: 'safe'    },
  { id: 'PAT-0025', name: 'Blessing Dada', age: 22, conditions: 'Malaria, Pregnancy',      meds: 'None current',               visit: '4 days ago', alertStatus: 'pending' },
  { id: 'PAT-0022', name: 'Yusuf Ibrahim', age: 48, conditions: 'Hypertension',            meds: 'Amlodipine 10mg',            visit: '5 days ago', alertStatus: 'safe'    },
  { id: 'PAT-0019', name: 'Ngozi Chukwu',  age: 52, conditions: 'Cardiac arrhythmia',      meds: 'Amiodarone, Quinine',        visit: '5 days ago', alertStatus: 'alert'   },
  { id: 'PAT-0016', name: 'Sadia Diallo',  age: 29, conditions: 'G6PD deficiency, Malaria',meds: 'Primaquine',                 visit: '6 days ago', alertStatus: 'alert'   },
];

// ── CLIENT-SIDE DRUG RULES (offline fallback) ──
// Full rules are in /data/africa_priority_rules.json
// and /data/who_essential_medicines_rules.json
export const DRUG_RULES = {
  ibuprofen: {
    level: 'critical', score: '9/10',
    title: 'CRITICAL: NSAID contraindicated in kidney disease',
    body: 'Ibuprofen (NSAID) is contraindicated in chronic kidney disease. NSAIDs inhibit prostaglandin synthesis, reducing renal blood flow and GFR — risking acute kidney injury.',
    rec: 'Use paracetamol (acetaminophen) instead. Refer for a renal-safe analgesic plan. Do not dispense.',
    source: 'WHO EML + OCML-DI Africa Priority Rules (AFR-001)',
  },
  diclofenac: {
    level: 'critical', score: '9/10',
    title: 'CRITICAL: NSAID contraindicated in kidney disease',
    body: 'Diclofenac carries the same renal contraindication as ibuprofen. Dangerous for CKD patients.',
    rec: 'Use paracetamol. Avoid all NSAIDs in kidney disease.',
    source: 'WHO EML + OCML-DI Africa Priority Rules (AFR-001)',
  },
  'artemether-lumefantrine': {
    level: 'critical', score: '8/10',
    title: 'CRITICAL: ARV–antimalarial interaction detected',
    body: 'Efavirenz reduces artemether-lumefantrine plasma levels by up to 75% through CYP3A4 induction. Malaria treatment will fail at standard doses.',
    rec: 'Switch to artesunate-amodiaquine, or use double-dose AL per WHO co-infection guidelines. Refer to senior clinician immediately.',
    source: 'Liverpool HIV DDI Database + OCML-DI Africa Priority Rules (AFR-003)',
  },
  coartem: {
    level: 'critical', score: '8/10',
    title: 'CRITICAL: ARV–antimalarial interaction',
    body: 'Coartem (artemether-lumefantrine) levels are dramatically reduced by efavirenz.',
    rec: 'Use artesunate-amodiaquine as alternative. Consult HIV/malaria specialist.',
    source: 'Liverpool HIV DDI Database + OCML-DI Africa Priority Rules (AFR-003)',
  },
  rifampicin: {
    level: 'critical', score: '9/10',
    title: 'CRITICAL: Rifampicin renders oral contraceptives ineffective',
    body: 'Rifampicin reduces ethinylestradiol and progestogen levels by up to 80% via CYP3A4 induction. Oral contraceptives will fail during TB treatment.',
    rec: 'Switch to copper IUD or barrier methods for the full duration of rifampicin treatment + 4 weeks after. Counsel patient explicitly.',
    source: 'WHO Model Formulary + OCML-DI Rules (WHO-007)',
  },
  quinine: {
    level: 'high', score: '7/10',
    title: 'HIGH RISK: QT prolongation risk',
    body: 'Quinine prolongs the QT interval. Current medications should be reviewed for additive cardiac risk.',
    rec: 'ECG monitoring required. Prefer artemisinin-based therapy where possible.',
    source: 'WHO EML + OCML-DI Rules (WHO-001)',
  },
  paracetamol: {
    level: 'safe', score: '1/10',
    title: 'Safe — no interactions detected',
    body: 'Paracetamol is the recommended analgesic for this patient. No clinically significant interactions found with current medications or conditions.',
    rec: 'Safe to dispense. Dosing: 500–1000mg every 4–6 hours. Maximum 4g per day.',
    source: 'WHO Essential Medicines List 22nd Edition',
  },
  acetaminophen: {
    level: 'safe', score: '1/10',
    title: 'Safe — no interactions detected',
    body: 'Acetaminophen (paracetamol) is safe for this patient. No significant interactions found.',
    rec: 'Standard dosing. Monitor liver function with long-term use.',
    source: 'WHO Essential Medicines List 22nd Edition',
  },
};
