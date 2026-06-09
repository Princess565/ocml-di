/**
 * OCML-DI · QRWallet Component
 * ─────────────────────────────────────────────
 * Generates and displays a patient QR wallet.
 * Uses qrcodejs (loaded via CDN in index.html).
 *
 * Usage:
 *   QRWallet.render('#qr-mount', patient);
 */

export const QRWallet = {
  render(mountSelector, patient) {
    const el = document.querySelector(mountSelector);
    if (!el) return;

    el.innerHTML = `
      <div class="qr-section" style="background:var(--navy-dark);border-radius:var(--radius);padding:20px;display:flex;flex-direction:column;align-items:center;gap:12px;margin-top:14px">
        <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.45)">
          <i class="ti ti-qrcode" style="font-size:13px;margin-right:5px"></i>QR medical wallet
        </div>
        <div id="qr-box" style="background:#fff;border-radius:var(--radius-sm);padding:10px"></div>
        <div style="font-family:var(--mono);font-size:12px;color:rgba(255,255,255,0.5);text-align:center">
          ${patient.id} · Scan to load record
        </div>
        <button
          id="qr-download-btn"
          style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:var(--radius-sm);padding:8px 14px;font-size:12px;color:rgba(255,255,255,0.7);cursor:pointer;font-family:var(--font);width:100%"
        >
          <i class="ti ti-download" style="font-size:13px;vertical-align:-2px;margin-right:4px"></i>
          Download QR wallet
        </button>
      </div>
    `;

    // Build QR payload — encrypted in production, plain JSON here
    const payload = JSON.stringify({
      id:          patient.id,
      name:        patient.name,
      conditions:  patient.conditions,
      medications: patient.medications,
      allergies:   patient.allergies,
      facility:    patient.facility,
      issued:      new Date().toISOString(),
    });

    const qrBox = document.getElementById('qr-box');
    try {
      // QRCode is loaded globally from CDN
      new QRCode(qrBox, {
        text:         payload,
        width:        120,
        height:       120,
        colorDark:    '#0e2f7e',
        colorLight:   '#ffffff',
        correctLevel: QRCode.CorrectLevel.H,
      });
    } catch (e) {
      qrBox.innerHTML = `<div style="width:120px;height:120px;display:flex;align-items:center;justify-content:center;font-size:11px;color:#666;text-align:center">QR library not loaded</div>`;
    }

    // Download handler
    document.getElementById('qr-download-btn').addEventListener('click', () => {
      const canvas = qrBox.querySelector('canvas');
      if (!canvas) return;
      const link = document.createElement('a');
      link.download = `${patient.id}-qr-wallet.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    });
  },
};
