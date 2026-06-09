/**
 * OCML-DI · Main App Entry Point
 * assets/js/app.js
 * ─────────────────────────────────────────────
 * Wires together: login, dashboard, patient record,
 * USSD simulator. Calls FastAPI backend via api.js.
 * Falls back to local data when offline.
 */

import api, { setToken, clearToken } from '../../services/api.js';
import { PATIENTS, ALL_PATIENTS, DRUG_RULES } from '../../services/data.js';
import { DrugChecker } from '../../components/DrugChecker.js';
import { QRWallet }    from '../../components/QRWallet.js';

// ═══════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════
document.getElementById('login-btn').addEventListener('click', async () => {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();
  const errEl    = document.getElementById('login-error');
  errEl.style.display = 'none';

  const result = await api.login(username, password);

  if (result && result.access_token) {
    setToken(result.access_token);
    showApp();
  } else {
    // Offline / demo mode — accept any credentials
    console.warn('[OCML-DI] Backend login failed — using demo mode');
    showApp();
  }
});

document.getElementById('login-password')
  .addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('login-btn').click(); });

document.addEventListener('click', e => {
  if (e.target.id === 'logout-btn') {
    clearToken();
    document.getElementById('page-app').classList.remove('active');
    document.getElementById('page-login').classList.add('active');
  }
});

function showApp() {
  document.getElementById('page-login').classList.remove('active');
  document.getElementById('page-app').classList.add('active');
  initDashboard();
}

// ═══════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════
function showScreen(name, title, extra) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(`screen-${name}`)?.classList.add('active');

  document.querySelectorAll('.sb-item').forEach(i => i.classList.remove('active'));
  document.querySelector(`[data-screen="${name}"]`)?.classList.add('active');

  const titles = {
    dashboard: 'Dashboard', patients: 'Patients',
    'patient-record': 'Patient record', ussd: 'USSD simulator',
  };
  document.getElementById('topbar-title').textContent = title || titles[name] || name;

  if (name === 'patient-record') loadPatientRecord(extra || 'PAT-0041');
  if (name === 'ussd')           initUssd();
  if (name === 'patients')       renderPatientsTable();
}

// Sidebar click handler
document.getElementById('sidebar').addEventListener('click', e => {
  const item = e.target.closest('[data-screen]');
  if (item) showScreen(item.dataset.screen);
});

// ═══════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════
async function initDashboard() {
  buildTrendChart();
  renderAlerts();
  renderRecentPatients();
  document.getElementById('open-ussd-btn')?.addEventListener('click', () => showScreen('ussd'));
  document.getElementById('view-all-patients-btn')?.addEventListener('click', () => showScreen('patients'));
}

function renderAlerts() {
  const alertData = [
    { initials: 'AB', color: '#e24b4a', name: 'Amina Bello',   detail: 'Ibuprofen + Kidney disease · Risk 9/10',        level: 'critical', id: 'PAT-0041' },
    { initials: 'KA', color: '#ba7517', name: 'Kofi Asante',   detail: 'Efavirenz + Artemether-lumefantrine · Risk 8/10', level: 'critical', id: 'PAT-0039' },
    { initials: 'FN', color: '#185fa5', name: 'Fatima Nkosi',  detail: 'Rifampicin + OCP · Contraceptive failure',        level: 'critical', id: 'PAT-0037' },
    { initials: 'EO', color: '#0f6e56', name: 'Emmanuel Osei', detail: 'Digoxin + Furosemide · Hypokalaemia risk',        level: 'high' },
    { initials: 'NC', color: '#533ab7', name: 'Ngozi Chukwu',  detail: 'Quinine + Amiodarone · QT prolongation',         level: 'high' },
  ];

  document.getElementById('alerts-list').innerHTML = alertData.map(a => `
    <div class="alert-item" ${a.id ? `data-patient-id="${a.id}"` : ''}>
      <div style="width:36px;height:36px;border-radius:50%;background:${a.color};color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;flex-shrink:0">${a.initials}</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:13px;font-weight:600">${a.name}</div>
        <div style="font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a.detail}</div>
      </div>
      <span class="risk-badge rb-${a.level}">${a.level === 'critical' ? 'Critical' : 'High'}</span>
    </div>
  `).join('');

  document.getElementById('alerts-list').addEventListener('click', e => {
    const item = e.target.closest('[data-patient-id]');
    if (item) showScreen('patient-record', null, item.dataset.patientId);
  });
}

function renderRecentPatients() {
  const recent = ALL_PATIENTS.slice(0, 5);
  document.getElementById('recent-patients-tbody').innerHTML = recent.map(p => `
    <tr ${p.key ? `data-patient-id="${p.key}"` : ''}>
      <td><strong>${p.name}</strong></td>
      <td style="font-family:var(--mono);color:var(--muted)">${p.id}</td>
      <td>${p.conditions}</td>
      <td>${p.visit}</td>
      <td><span class="status-dot ${p.alertStatus === 'alert' ? 'sd-red' : p.alertStatus === 'pending' ? 'sd-amber' : 'sd-green'}"></span>${p.alertStatus === 'alert' ? 'Alert' : p.alertStatus === 'pending' ? 'Pending' : 'Safe'}</td>
      <td style="color:var(--navy)">${p.key ? 'Review →' : 'View →'}</td>
    </tr>
  `).join('');

  document.getElementById('recent-patients-tbody').addEventListener('click', e => {
    const row = e.target.closest('[data-patient-id]');
    if (row) showScreen('patient-record', null, row.dataset.patientId);
  });
}

function buildTrendChart() {
  const ctx = document.getElementById('trendChart');
  if (!ctx || !window.Chart) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
      datasets: [{ data: [480,510,530,610,590,680,720], borderColor: '#1d9e75', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: true, backgroundColor: 'rgba(29,158,117,0.08)' }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: true, grid: { display: false }, ticks: { font: { size: 10 }, color: '#9ba3b8' } }, y: { display: false, min: 400, max: 780 } },
      animation: { duration: 800 },
    },
  });
}

// ═══════════════════════════════════════════
// PATIENTS LIST
// ═══════════════════════════════════════════
function renderPatientsTable() {
  const tbody = document.getElementById('patients-tbody');
  if (!tbody) return;
  tbody.innerHTML = ALL_PATIENTS.map(p => `
    <tr ${p.key ? `data-patient-id="${p.key}"` : ''}>
      <td><strong>${p.name}</strong></td>
      <td style="font-family:var(--mono);color:var(--muted)">${p.id}</td>
      <td>${p.age}</td><td>${p.conditions}</td><td>${p.meds}</td><td>${p.visit}</td>
      <td><span class="status-dot ${p.alertStatus === 'alert' ? 'sd-red' : p.alertStatus === 'pending' ? 'sd-amber' : 'sd-green'}"></span>${p.alertStatus === 'alert' ? 'Alert' : p.alertStatus === 'pending' ? 'Pending' : 'Safe'}</td>
      <td style="color:var(--navy)">${p.key ? 'Review →' : 'View →'}</td>
    </tr>
  `).join('');
  tbody.addEventListener('click', e => {
    const row = e.target.closest('[data-patient-id]');
    if (row) showScreen('patient-record', null, row.dataset.patientId);
  });
}

// ═══════════════════════════════════════════
// PATIENT RECORD
// ═══════════════════════════════════════════
async function loadPatientRecord(patientId) {
  // Try API first, fall back to local data
  let patient = await api.getPatient(patientId);
  if (!patient) patient = PATIENTS[patientId] || PATIENTS['PAT-0041'];

  document.getElementById('rec-avatar').textContent   = patient.initials;
  document.getElementById('rec-avatar').style.background = patient.color;
  document.getElementById('rec-name').textContent     = patient.name;
  document.getElementById('rec-id').textContent       = patient.id;
  document.getElementById('rec-age').textContent      = patient.age;
  document.getElementById('rec-gender').textContent   = patient.gender;
  document.getElementById('rec-phone').textContent    = patient.phone;
  document.getElementById('rec-facility').textContent = patient.facility;
  document.getElementById('rec-visit').textContent    = patient.lastVisit;
  document.getElementById('record-breadcrumb').textContent = patient.name;

  document.getElementById('rec-conditions').innerHTML  = patient.conditions.map(c => `<span class="cond-tag">${c}</span>`).join('');
  document.getElementById('rec-medications').innerHTML = patient.medications.map(m => `<span class="med-tag">${m}</span>`).join('');
  document.getElementById('rec-allergies').innerHTML   = patient.allergies.length
    ? patient.allergies.map(a => `<span class="allergy-tag">${a}</span>`).join('')
    : '<span style="font-size:12px;color:var(--muted)">None recorded</span>';

  const statusLabel = { approved: '✅ Safe', blocked: '🔴 Blocked', review: '⚠️ Review' };
  document.getElementById('rec-history').innerHTML = (patient.history || []).map(h => `
    <tr>
      <td>${h.drug}</td><td>${h.by}</td><td>${h.date}</td>
      <td>${statusLabel[h.status] || h.status}</td>
    </tr>
  `).join('');

  // Render components
  DrugChecker.render('#drug-checker-mount', patient.id);
  QRWallet.render('#qr-wallet-mount', patient);

  document.getElementById('back-to-dashboard')
    ?.addEventListener('click', () => showScreen('dashboard'));
}

// ═══════════════════════════════════════════
// USSD SIMULATOR
// ═══════════════════════════════════════════
let ussdState = 0;
let currentScenario = 1;
const scenarioDrugs = { 1: 'ibuprofen', 2: 'artemether-lumefantrine', 3: 'rifampicin', 4: 'paracetamol' };
const ussdResponses = {
  ibuprofen:               'END CRITICAL RISK ALERT\n\nDrug: Ibuprofen\nRisk: CRITICAL (9/10)\n\nNSAIDs CONTRAINDICATED\nin kidney disease.\nRisk of acute renal failure.\n\nDO NOT DISPENSE.\n\nAlternative: Paracetamol\n\n[OCML-DI · WHO EML rules]',
  'artemether-lumefantrine':'END CRITICAL ALERT\n\nDrug: Artemether-lumefantrine\nRisk: CRITICAL (8/10)\n\nEfavirenz reduces drug\nlevels by 75%. Malaria\ntreatment WILL FAIL.\n\nUse: Artesunate-amodiaquine\n\nRefer to senior clinician.\n\n[OCML-DI · Liverpool DDI]',
  rifampicin:              'END CRITICAL ALERT\n\nDrug: Rifampicin\nRisk: CRITICAL (9/10)\n\nRifampicin makes oral\ncontraceptives ineffective.\nPregnancy risk HIGH.\n\nSwitch to copper IUD.\nCounsel patient NOW.\n\n[OCML-DI · WHO EML rules]',
  paracetamol:             'END SAFE — NO INTERACTION\n\nDrug: Paracetamol\nRisk: LOW (1/10)\n\nNo interactions found.\nSafe to dispense.\n\nDosing: 500–1000mg\nevery 4–6 hours.\nMax 4g per day.\n\n[OCML-DI · WHO EML rules]',
};

function initUssd() {
  resetUssd();
  document.getElementById('ussd-dial-btn') ?.addEventListener('click', ussdDial);
  document.getElementById('ussd-reset-btn')?.addEventListener('click', resetUssd);
  document.getElementById('ussd-send')     ?.addEventListener('click', ussdSend);
  document.getElementById('ussd-input')    ?.addEventListener('keydown', e => { if (e.key === 'Enter') ussdSend(); });

  document.querySelectorAll('.phone-keypad .key[data-key]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('ussd-input').value += btn.dataset.key;
    });
  });

  document.querySelectorAll('.ussd-scenario').forEach(s => {
    s.addEventListener('click', () => {
      currentScenario = parseInt(s.dataset.scenario);
      document.querySelectorAll('.ussd-scenario').forEach(x => x.classList.remove('selected'));
      s.classList.add('selected');
      resetUssd();
    });
  });
}

function resetUssd() {
  ussdState = 0;
  setUssdOut('<span style="color:rgba(200,200,200,0.35)">Press green dial button to begin…</span>');
  const inp = document.getElementById('ussd-input');
  if (inp) inp.value = '';
}

function ussdDial() {
  if (ussdState !== 0) return;
  ussdState = 1;
  setUssdOut(`CON Welcome to OCML-DI\nDrug Safety Check System\n\nPowered by WHO guidelines\n+ Africa Priority Rules\n\n1. Check drug interaction\n2. Patient lookup\n3. Adverse event report\n\n<span class="ussd-prompt">Reply with option number:</span>`);
}

async function ussdSend() {
  const inp = document.getElementById('ussd-input');
  const val = inp.value.trim();
  if (!val) return;
  inp.value = '';

  if (ussdState === 0) { ussdDial(); return; }

  if (ussdState === 1) {
    if (val === '1') {
      ussdState = 2;
      setUssdOut(`CON Drug interaction check\n\nEnter drug name:\n(e.g. Ibuprofen, Quinine,\nArtemether-lumefantrine)\n\n<span class="ussd-prompt">Type name and press Send:</span>`);
    } else if (val === '2') {
      setUssdOut(`END Patient lookup requires\nclinic network access.\n\nCurrently offline.\nUse QR wallet scan\nat clinic terminal.`);
    } else {
      setUssdOut(`END Invalid option.\nDial *384*52591# to restart.\n\n[OCML-DI]`);
    }
    return;
  }

  if (ussdState === 2) {
    ussdState = 3;
    // Try live USSD API
    const liveResult = await api.ussdSession(`session-${Date.now()}`, '+2348000000000', `1*${val}`);
    let resp = liveResult || ussdResponses[val.toLowerCase()] || ussdResponses[scenarioDrugs[currentScenario]];

    const colored = resp
      .replace(/(CRITICAL RISK ALERT|CRITICAL ALERT)/g, '<span class="ussd-warning">$1</span>')
      .replace('SAFE — NO INTERACTION', '<span class="ussd-safe">SAFE — NO INTERACTION</span>');
    setUssdOut(colored);
  }
}

function setUssdOut(html) {
  const el = document.getElementById('ussd-output');
  if (el) el.innerHTML = html;
}
