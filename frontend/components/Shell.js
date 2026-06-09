/**
 * OCML-DI · Shell Component
 * ─────────────────────────────────────────────
 * Renders sidebar + topbar HTML.
 * Call Shell.render() once on app init.
 * Call Shell.setScreen(name) to switch screens.
 */

export const Shell = {
  render() {
    document.getElementById('sidebar').innerHTML = `
      <div class="sb-brand">
        <div class="sb-brand-icon"><i class="ti ti-heartbeat" aria-hidden="true"></i></div>
        <div class="sb-brand-name">OCML-DI</div>
      </div>
      <div class="sb-section">Clinical</div>
      <div class="sb-item active" data-screen="dashboard">
        <i class="ti ti-layout-dashboard" aria-hidden="true"></i>Dashboard
      </div>
      <div class="sb-item" data-screen="patients">
        <i class="ti ti-users" aria-hidden="true"></i>Patients
      </div>
      <div class="sb-item" data-screen="patient-record">
        <i class="ti ti-file-medical" aria-hidden="true"></i>Patient record
      </div>
      <div class="sb-section">Tools</div>
      <div class="sb-item" data-screen="ussd">
        <i class="ti ti-device-mobile" aria-hidden="true"></i>USSD simulator
      </div>
      <div class="sb-item">
        <i class="ti ti-qrcode" aria-hidden="true"></i>QR wallets
      </div>
      <div class="sb-item">
        <i class="ti ti-shield-check" aria-hidden="true"></i>Audit log
      </div>
      <div class="sb-offline">
        <div class="sb-offline-dot">Offline mode active</div>
      </div>
    `;

    document.getElementById('topbar').innerHTML = `
      <div>
        <div class="topbar-title" id="topbar-title">Dashboard</div>
        <div class="topbar-sub" id="topbar-sub">Kano General Clinic</div>
      </div>
      <div class="topbar-right">
        <i class="ti ti-bell topbar-icon" aria-label="Notifications"></i>
        <div class="topbar-avatar" id="user-avatar" title="Clinician">EI</div>
        <i class="ti ti-logout topbar-icon" aria-label="Sign out" id="logout-btn"></i>
      </div>
    `;

    // Sidebar navigation
    document.getElementById('sidebar').addEventListener('click', e => {
      const item = e.target.closest('[data-screen]');
      if (item) this.setScreen(item.dataset.screen);
    });
  },

  setScreen(name, title) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(`screen-${name}`);
    if (screen) screen.classList.add('active');

    document.querySelectorAll('.sb-item').forEach(i => i.classList.remove('active'));
    const sbItem = document.querySelector(`[data-screen="${name}"]`);
    if (sbItem) sbItem.classList.add('active');

    const titles = {
      dashboard: 'Dashboard',
      patients: 'Patients',
      'patient-record': 'Patient record',
      ussd: 'USSD simulator',
    };
    document.getElementById('topbar-title').textContent = title || titles[name] || name;
  },

  setUser(name, initials) {
    const el = document.getElementById('user-avatar');
    if (el) { el.textContent = initials; el.title = name; }
  },
};
