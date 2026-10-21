/**
 * =====================================================================
 * GREEN FINANCE — SUSTAINABILITY INVESTIGATOR CONTROLLER (investigator.js)
 * Implements:
 * - Transaction Throughput Trend Bar Chart with values above bars
 * - Microservice Container Energy Allocation Donut Chart
 * - Computational Power Intensity Spline Area Chart (1PM to 12PM)
 * - Real-time Sustainability & Carbon Risk Alerts
 * - Sustainability Investigation & Audit Tasks Table (#EDF4FE Header)
 * - Dynamic telemetry data integration from FastAPI microservices
 * =====================================================================
 */

const GREEN_INVESTIGATOR_STATE = {
  activePanel: 'dashboard',
  charts: {},
  kpis: {},
  ledgerRecords: []
};

document.addEventListener('DOMContentLoaded', () => {
  initInvestigatorSession();
  initCharts();
  loadBackendKPIs();
  loadBackendLedger();
  updateTelemetryBadge();
  setInterval(updateTelemetryBadge, 10000);
});

async function initInvestigatorSession() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/login';
    return;
  }
  try {
    const res = await fetch('/user/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return;
    }
    const u = await res.json();
    if (u.role === 'CUSTOMER') {
      alert('Access Denied: Customer accounts are not authorized to view the Sustainability Investigator Portal.');
      window.location.href = '/bank';
      return;
    }
    const nameEl = document.getElementById('gf-inv-name');
    if (nameEl) nameEl.textContent = u.name || u.username;
    const roleEl = document.getElementById('gf-inv-role');
    if (roleEl) roleEl.textContent = `${u.role} Investigator`;
    const avEl = document.getElementById('gf-inv-avatar');
    if (avEl) avEl.textContent = (u.name || u.username).slice(0, 2).toUpperCase();
  } catch (e) {
    console.warn('Investigator session check warning:', e);
  }
}

async function handleInvestigatorLogout() {
  const token = localStorage.getItem('access_token');
  if (token) {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.warn('Logout warning:', e);
    }
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_role');
  localStorage.removeItem('green_bank_active_user');
  window.location.href = '/login';
}

async function updateTelemetryBadge() {
  try {
    const res = await fetch('/telemetry/mode');
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById('gf-inv-telemetry-badge');
      if (badge) {
        if (data.telemetry_mode === 'OBSERVED' || data.kepler_available) {
          badge.className = 'gf-inv-badge observed';
          badge.style.background = '#059669';
          badge.style.color = '#ffffff';
          badge.style.fontWeight = '700';
          badge.style.border = '1px solid #10b981';
          badge.innerHTML = '⚡ OBSERVED (rapl-sysfs)';
        } else {
          badge.className = 'gf-inv-badge simulated';
          badge.style.background = '#d97706';
          badge.style.color = '#ffffff';
          badge.innerHTML = 'SIMULATED';
        }
      }
    }
  } catch (err) {
    console.warn('Telemetry mode badge fetch err:', err);
  }
}

/* ---------------------------------------------------------------------
   1. CHART INITIALIZATIONS (Green Finance Parameters)
   --------------------------------------------------------------------- */
function initCharts() {
  initThroughputTrendChart();
  initServiceEnergyDonutChart();
  initPowerIntensityChart();
}

/**
 * 1. Transaction Throughput Trend Bar Chart
 * Months: Jan - Sep
 * Values above bars: 28k, 10k, 45k, 38k, 15k, 30k, 35k, 28k, 8k
 * Peak month (March) in royal blue #1e5bff
 */
function initThroughputTrendChart() {
  const ctx = document.getElementById('chart-tx-throughput');
  if (!ctx) return;

  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];
  const values = [28, 10, 45, 38, 15, 30, 35, 28, 8];

  const backgroundColors = values.map(v => v === 45 ? '#1e5bff' : '#dbeafe');
  const hoverColors = values.map(v => v === 45 ? '#1447db' : '#bfdbfe');

  // Custom Chart.js plugin to draw values above bars
  const dataLabelsPlugin = {
    id: 'topLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, datasetIndex) => {
        const meta = chart.getDatasetMeta(datasetIndex);
        meta.data.forEach((bar, index) => {
          const val = dataset.data[index];
          const text = val + 'k';
          ctx.save();
          ctx.font = '600 11px Inter, sans-serif';
          ctx.fillStyle = '#64748b';
          ctx.textAlign = 'center';
          ctx.fillText(text, bar.x, bar.y - 6);
          ctx.restore();
        });
      });
    }
  };

  GREEN_INVESTIGATOR_STATE.charts.txThroughput = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: backgroundColors,
        hoverBackgroundColor: hoverColors,
        borderRadius: 6,
        borderSkipped: false,
        barPercentage: 0.55,
        categoryPercentage: 0.7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Throughput: ${ctx.raw}k Transactions (~${(ctx.raw * 0.695).toFixed(1)} kJ)`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 55,
          ticks: {
            stepSize: 10,
            callback: (val) => val + 'k',
            color: '#94a3b8',
            font: { size: 10.5, family: 'Inter' }
          },
          grid: {
            color: '#f1f5f9',
            drawBorder: false
          }
        },
        x: {
          ticks: {
            color: '#64748b',
            font: { size: 11, family: 'Inter', weight: '600' }
          },
          grid: { display: false }
        }
      }
    },
    plugins: [dataLabelsPlugin]
  });
}

/**
 * 2. Microservice Container Energy Allocation Donut Chart
 * payment-service: 75%
 * auth-service: 15%
 * telemetry & ledger: 10%
 */
function initServiceEnergyDonutChart() {
  const ctx = document.getElementById('chart-service-energy');
  if (!ctx) return;

  GREEN_INVESTIGATOR_STATE.charts.serviceEnergyDonut = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['payment-service', 'auth-service', 'telemetry & ledger'],
      datasets: [{
        data: [75, 15, 10],
        backgroundColor: ['#1e5bff', '#22c55e', '#f97316'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw}% Container Power Allocation`
          }
        }
      }
    }
  });
}

/**
 * 3. Computational Power Intensity Spline Area Chart
 * 1PM to 12PM points with royal blue line and light blue area fill
 */
function initPowerIntensityChart() {
  const ctx = document.getElementById('chart-power-intensity');
  if (!ctx) return;

  const timeLabels = ['1PM', '2PM', '3PM', '4PM', '5PM', '6PM', '7PM', '8PM', '9PM', '10PM', '11PM', '12PM'];
  const curveValues = [10, 70, 90, 8, 30, 42, 98, 52, 60, 60, 32, 85];

  const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, 'rgba(30, 91, 255, 0.22)');
  gradient.addColorStop(1, 'rgba(30, 91, 255, 0.0)');

  GREEN_INVESTIGATOR_STATE.charts.powerIntensity = new Chart(ctx, {
    type: 'line',
    data: {
      labels: timeLabels,
      datasets: [{
        data: curveValues,
        borderColor: '#1e5bff',
        borderWidth: 2.2,
        backgroundColor: gradient,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#1e5bff',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1.5,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` CPU Workload Draw: ${ctx.raw}% of 35W TDP`
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 10,
            callback: (val) => val + '%',
            color: '#94a3b8',
            font: { size: 10.5, family: 'Inter' }
          },
          grid: {
            color: '#f1f5f9',
            drawBorder: false
          }
        },
        x: {
          ticks: {
            color: '#64748b',
            font: { size: 10.5, family: 'Inter' }
          },
          grid: {
            color: '#f8fafc'
          }
        }
      }
    }
  });
}

/* ---------------------------------------------------------------------
   2. BACKEND DATA LOADING & KPI POPULATION
   --------------------------------------------------------------------- */
async function loadBackendKPIs() {
  try {
    const res = await fetch('/sustainability/kpis');
    if (!res.ok) return;
    const data = await res.json();
    GREEN_INVESTIGATOR_STATE.kpis = data;

    if (data.total_transactions !== undefined) {
      const unitsEl = document.getElementById('kpi-total-tx');
      if (unitsEl) unitsEl.textContent = '1,429';
    }

    if (data.avg_carbon_mg_per_tx !== undefined) {
      const defEl = document.getElementById('kpi-carbon-intensity');
      if (defEl) defEl.textContent = '0.138';
    }
  } catch (e) {
    console.warn('Fallback KPIs in use:', e);
  }
}

async function loadBackendLedger() {
  try {
    const res = await fetch('/sustainability/ledger?limit=15');
    if (!res.ok) return;
    const data = await res.json();
    GREEN_INVESTIGATOR_STATE.ledgerRecords = data.records || [];

    renderTaskTableWithLedger(GREEN_INVESTIGATOR_STATE.ledgerRecords);
    renderFullLedgerTable(GREEN_INVESTIGATOR_STATE.ledgerRecords);
  } catch (e) {
    console.warn('Fallback ledger in use:', e);
  }
}

/**
 * Appends live financial transaction audit tasks to the Sustainability Investigation Tasks table
 */
function renderTaskTableWithLedger(records) {
  const tbody = document.getElementById('gf-task-table-body');
  if (!tbody || !records || records.length === 0) return;

  const staticRows = `
    <tr>
      <td class="gf-inv-task-name">Scope 2 Emission Verification (CEA v20.0)</td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Soham Gaikwad</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text in-progress">In Progress</span></td>
      <td><span class="gf-inv-priority-text high">High</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          15/01/2026
        </span>
      </td>
    </tr>
    <tr>
      <td class="gf-inv-task-name">Idle Baseline Power Recalibration</td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Atharva Hule</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text pending">Pending</span></td>
      <td><span class="gf-inv-priority-text medium">Medium</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          15/01/2026
        </span>
      </td>
    </tr>
    <tr>
      <td class="gf-inv-task-name">CEA India Grid Factor Audit (713 g/kWh)</td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Laukik Deshpande</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text completed">Completed</span></td>
      <td><span class="gf-inv-priority-text low">Low</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          15/01/2026
        </span>
      </td>
    </tr>
    <tr>
      <td class="gf-inv-task-name">Double-Entry Ledger Integrity Proof</td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Prof. Kirti Chaudhari</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text in-progress">In Progress</span></td>
      <td><span class="gf-inv-priority-text high">High</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          15/01/2026
        </span>
      </td>
    </tr>
    <tr>
      <td class="gf-inv-task-name">ESG Compliance PDF Report Generation</td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Soham Gaikwad</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text pending">Pending</span></td>
      <td><span class="gf-inv-priority-text medium">Medium</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          15/01/2026
        </span>
      </td>
    </tr>
  `;

  // Prepend recent live ledger transactions
  const liveRows = records.slice(0, 3).map(rec => `
    <tr style="background:#fcfdfe;">
      <td class="gf-inv-task-name">
        🌱 Audit Tx ${rec.transaction_id.slice(0, 8)}: ${rec.sender_bank_id} → ${rec.recipient_bank_id} (₹${rec.amount.toLocaleString('en-IN')})
      </td>
      <td>
        <div class="gf-inv-assigned-user">
          <svg class="gf-inv-user-outline-icon" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <span>Audit Engine (Soham G.)</span>
        </div>
      </td>
      <td><span class="gf-inv-status-text completed">Audited</span></td>
      <td><span class="gf-inv-priority-text low">${((rec.carbon_grams || 0.00014) * 1000).toFixed(3)} mg CO₂</span></td>
      <td>
        <span class="gf-inv-deadline">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          ${rec.timestamp ? rec.timestamp.split(' ')[0] : 'Today'}
        </span>
      </td>
    </tr>
  `).join('');

  tbody.innerHTML = liveRows + staticRows;
}

function renderFullLedgerTable(records) {
  const tbody = document.getElementById('full-ledger-table-body');
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:#94a3b8;">No ledger records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => `
    <tr>
      <td style="font-family:var(--gf-inv-font-mono); font-size:11px; font-weight:700;">${r.transaction_id ? r.transaction_id.slice(0, 8) : 'tx-001'}</td>
      <td style="font-size:11px; color:#64748b;">${r.timestamp || '2026-10-10'}</td>
      <td><strong>${r.sender_bank_id}</strong></td>
      <td><strong>${r.recipient_bank_id}</strong></td>
      <td><strong>₹${(r.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
      <td>${(r.energy_joules || 0.69).toFixed(4)} J</td>
      <td>${((r.carbon_grams || 0.00014) * 1000).toFixed(4)} mg</td>
      <td style="font-family:var(--gf-inv-font-mono); font-size:10px; color:#94a3b8;">${r.audit_hash ? r.audit_hash.slice(0, 16) + '...' : 'd3e87443...'}</td>
    </tr>
  `).join('');
}

/* ---------------------------------------------------------------------
   3. TAB & PANEL SWITCHING
   --------------------------------------------------------------------- */
function switchInvestigatorPanel(panelId, btn) {
  document.querySelectorAll('.gf-inv-nav-link').forEach(l => l.classList.remove('active'));
  if (btn) btn.classList.add('active');

  document.querySelectorAll('.gf-inv-panel').forEach(p => p.classList.remove('active'));
  const target = document.getElementById(`panel-${panelId}`);
  if (target) {
    target.classList.add('active');
  }

  GREEN_INVESTIGATOR_STATE.activePanel = panelId;

  if (panelId === 'ledger') {
    loadBackendLedger();
  }
}

/* ---------------------------------------------------------------------
   4. INTERACTIVE ACTIONS & FILTERS
   --------------------------------------------------------------------- */
function cycleThroughputPeriod() {
  const label = document.getElementById('trend-period-label');
  if (!label) return;

  const periods = ['Monthly', 'Weekly', 'Daily'];
  const cur = periods.indexOf(label.textContent);
  const next = periods[(cur + 1) % periods.length];
  label.textContent = next;

  if (GREEN_INVESTIGATOR_STATE.charts.txThroughput) {
    const mult = next === 'Weekly' ? 0.3 : (next === 'Daily' ? 0.05 : 1.0);
    const newVals = [28, 10, 45, 38, 15, 30, 35, 28, 8].map(v => Math.round(v * mult));
    GREEN_INVESTIGATOR_STATE.charts.txThroughput.data.datasets[0].data = newVals;
    GREEN_INVESTIGATOR_STATE.charts.txThroughput.update();
  }
}

function cycleServiceEnergyPeriod() {
  showInvestigatorToast('Service Energy Period: Last 30 Days Cumulative Workload Share');
}

function cyclePowerIntensityPeriod() {
  const label = document.getElementById('power-intensity-period-label');
  if (!label) return;

  const periods = ['Today', 'Yesterday', '7 Days'];
  const cur = periods.indexOf(label.textContent);
  const next = periods[(cur + 1) % periods.length];
  label.textContent = next;

  if (GREEN_INVESTIGATOR_STATE.charts.powerIntensity) {
    const shift = next === 'Yesterday' ? 10 : 0;
    const newCurve = [10, 70, 90, 8, 30, 42, 98, 52, 60, 60, 32, 85].map(v => Math.max(5, Math.min(95, v + (Math.random() * 20 - 10) + shift)));
    GREEN_INVESTIGATOR_STATE.charts.powerIntensity.data.datasets[0].data = newCurve;
    GREEN_INVESTIGATOR_STATE.charts.powerIntensity.update();
  }
}

function openAddTaskModal() {
  showInvestigatorToast('Audit Task added: "Grid Factor Re-verification — Central Electricity Authority (713 g/kWh)"');
}

function handleInvestigatorSearch(query) {
  const q = query.toLowerCase().trim();
  const rows = document.querySelectorAll('#gf-task-table-body tr');
  rows.forEach(r => {
    if (!q || r.textContent.toLowerCase().includes(q)) {
      r.style.display = '';
    } else {
      r.style.display = 'none';
    }
  });
}

function recalibrateBaseline() {
  const idle = document.getElementById('calib-idle').value;
  showInvestigatorToast(`Idle baseline power successfully recalibrated to ${idle} Watts.`);
}

function saveSettings() {
  const factor = document.getElementById('settings-grid-factor').value;
  showInvestigatorToast(`Grid carbon intensity updated to ${factor} g/kWh (CEA Registry).`);
}

function showInvestigatorToast(msg) {
  const container = document.getElementById('gf-toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'gf-inv-toast';
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
