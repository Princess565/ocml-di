/**
 * OCML-DI · API Service
 * ─────────────────────────────────────────────
 * All HTTP calls to the FastAPI backend.
 * Base URL: http://127.0.0.1:8000
 *
 * Usage:
 *   import api from './services/api.js';
 *   const patients = await api.getPatients();
 *
 * For production, replace BASE_URL with your
 * ngrok URL or deployed server address.
 */

const BASE_URL = 'http://127.0.0.1:8000';

// ── AUTH TOKEN (set on login) ──────────────────
let _token = localStorage.getItem('ocml_token') || null;
export function setToken(t) { _token = t; localStorage.setItem('ocml_token', t); }
export function clearToken()  { _token = null; localStorage.removeItem('ocml_token'); }
export function getToken()    { return _token; }

// ── INTERNAL FETCH WRAPPER ────────────────────
async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(`${BASE_URL}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    // Graceful offline fallback — return null so UI can handle
    console.warn(`[OCML-DI API] ${method} ${path} failed:`, e.message);
    return null;
  }
}

const api = {

  // ── AUTH ─────────────────────────────────────
  /**
   * Login with username + password (form data).
   * FastAPI backend expects multipart form, not JSON.
   */
  async login(username, password) {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    try {
      const res = await fetch(`${BASE_URL}/login`, { method: 'POST', body: form });
      if (!res.ok) throw new Error('Login failed');
      return await res.json(); // { access_token, token_type }
    } catch (e) {
      console.warn('[OCML-DI API] Login failed:', e.message);
      return null;
    }
  },

  // ── PATIENTS ─────────────────────────────────
  /** GET /clinician/patients — list all patients */
  async getPatients() {
    return request('GET', '/clinician/patients');
  },

  /** GET /clinician/patient/:id — single patient record */
  async getPatient(id) {
    return request('GET', `/clinician/patient/${id}`);
  },

  // ── DRUG CHECK ───────────────────────────────
  /**
   * POST /clinician/check-drug
   * Body: { patient_id, drug_name }
   * Returns risk result from the RiskEngine
   */
  async checkDrug(patientId, drugName) {
    return request('POST', '/clinician/check-drug', {
      patient_id: patientId,
      drug_name: drugName,
    });
  },

  // ── QR WALLET ────────────────────────────────
  /**
   * POST /clinician/patient/:id/qr
   * Returns QR code as base64 PNG
   */
  async generateQR(patientId) {
    return request('POST', `/clinician/patient/${patientId}/qr`);
  },

  /**
   * POST /clinician/patient/qr/decode
   * Body: FormData with 'file' key (image upload)
   */
  async decodeQR(imageFile) {
    const form = new FormData();
    form.append('file', imageFile);
    try {
      const res = await fetch(`${BASE_URL}/clinician/patient/qr/decode`, {
        method: 'POST',
        body: form,
        headers: _token ? { 'Authorization': `Bearer ${_token}` } : {},
      });
      if (!res.ok) throw new Error('QR decode failed');
      return await res.json();
    } catch (e) {
      console.warn('[OCML-DI API] QR decode failed:', e.message);
      return null;
    }
  },

  // ── REVIEWS ──────────────────────────────────
  /** GET /clinician/dashboard — pending reviews */
  async getPendingReviews() {
    return request('GET', '/clinician/dashboard');
  },

  /** POST /clinician/review/:id/approve */
  async approveReview(reviewId) {
    return request('POST', `/clinician/review/${reviewId}/approve`);
  },

  /** POST /clinician/review/:id/reject */
  async rejectReview(reviewId) {
    return request('POST', `/clinician/review/${reviewId}/reject`);
  },

  // ── USSD ─────────────────────────────────────
  /**
   * POST /ussd/ussd
   * Simulates USSD session (Africa's Talking format)
   * Body: { sessionId, serviceCode, phoneNumber, text }
   */
  async ussdSession(sessionId, phoneNumber, text) {
    const form = new FormData();
    form.append('sessionId', sessionId);
    form.append('serviceCode', '*384*52591#');
    form.append('phoneNumber', phoneNumber);
    form.append('text', text);
    try {
      const res = await fetch(`${BASE_URL}/ussd/ussd`, { method: 'POST', body: form });
      if (!res.ok) throw new Error('USSD request failed');
      return await res.text(); // USSD returns plain text (CON ... / END ...)
    } catch (e) {
      console.warn('[OCML-DI API] USSD failed:', e.message);
      return null;
    }
  },
};

export default api;
