/**
 * =====================================================================
 * GREEN-FINANCE / ECO-MONITOR — PROTOTYPE LAYOUT JAVASCRIPT (PHASE 2)
 * Handles state management, simulated bank transactions, PromQL query
 * evaluation, Grafana chart panels, and double-entry ledger bookkeeping.
 * =====================================================================
 */

// --- Global Application State ---
const state = {
  activeView: 'overview',
  user: {
    username: 'soham_gaikwad',
    name: 'Soham Gaikwad',
    bankId: 'HDFC9999',
    role: 'ADMIN'
  },
  config: {
    emissionFactor: 0.38, // kg CO2 / kWh
    carbonThreshold: 12.0, // g CO2 / tx threshold for RF07 alert
    scrapeInterval: 15, // seconds
    alertAction: 'banner'
  },
  metrics: {
    txCount: 1429,
    activePowerWatts: 118.6,
    carbonPerTx: 8.42,
    cumulativeCarbonKg: 12.03,
    avgLatencyMs: 42
  },
  // Initial historical data points for charts (10 points)
  timeLabels: ['10:00', '10:02', '10:04', '10:06', '10:08', '10:10', '10:12', '10:14', '10:16', '10:18'],
  carbonSeries: [7.8, 8.1, 7.9, 8.5, 9.2, 8.8, 8.4, 8.9, 8.2, 8.42],
  energyPaymentSeries: [75, 78, 76, 82, 86, 84, 80, 83, 79, 81.2],
  energyAuthSeries: [32, 34, 33, 36, 38, 37, 35, 36, 35, 37.4],
  throughputSeries: [22, 25, 24, 28, 34, 30, 26, 29, 27, 28.5],
  
  // Ledger Transactions List
  transactions: [
    {
      id: 'TX-99824-A1B2',
      timestamp: '2026-09-15 10:18:42',
      senderBankId: 'HDFC9999',
      recipientBankId: 'MAH123',
      protocol: 'IMPS',
      amount: 12500,
      joules: 24.15,
      carbonGrams: 2.548,
      note: 'Client vendor settlement',
      status: 'COMPLETED',
      isAlert: false
    },
    {
      id: 'TX-99823-C3D4',
      timestamp: '2026-09-15 10:17:15',
      senderBankId: 'HDFC9999',
      recipientBankId: 'IDF892',
      protocol: 'UPI',
      amount: 4200,
      joules: 19.80,
      carbonGrams: 2.089,
      note: 'SaaS cloud server billing',
      status: 'COMPLETED',
      isAlert: false
    },
    {
      id: 'TX-99822-E5F6',
      timestamp: '2026-09-15 10:14:02',
      senderBankId: 'HDFC9999',
      recipientBankId: 'SBIN456',
      protocol: 'RTGS',
      amount: 75000,
      joules: 38.60,
      carbonGrams: 4.072,
      note: 'Institutional treasury transfer',
      status: 'COMPLETED',
      isAlert: false
    },
    {
      id: 'TX-99821-G7H8',
      timestamp: '2026-09-15 10:11:30',
      senderBankId: 'HDFC9999',
      recipientBankId: 'AXIS777',
      protocol: 'NEFT',
      amount: 150000,
      joules: 52.40,
      carbonGrams: 14.85, // High spike to demonstrate RF07
      note: 'Batch supplier payroll run',
      status: 'COMPLETED',
      isAlert: true
    },
    {
      id: 'TX-99820-J9K0',
      timestamp: '2026-09-15 10:09:12',
      senderBankId: 'HDFC9999',
      recipientBankId: 'MAH123',
      protocol: 'IMPS',
      amount: 9800,
      joules: 21.30,
      carbonGrams: 2.247,
      note: 'Quarterly office maintenance',
      status: 'COMPLETED',
      isAlert: false
    }
  ],

  // PromQL Presets
  promqlPresets: {
    carbon_per_tx: {
      query: `(sum(rate(kepler_container_joules_total[1m])) * 0.38) / sum(rate(http_requests_total[1m]))`,
      explain: `Computes carbon intensity by taking total container energy consumption in Watts (rate of Joules), multiplying by the regional emission coefficient (0.38 kg/kWh), and dividing by the transaction rate.`,
      metricName: 'carbon_per_transaction',
      unit: 'grams_CO2_per_tx',
      seriesData: [7.8, 8.1, 7.9, 8.5, 9.2, 8.8, 8.4, 8.9, 8.2, 8.42]
    },
    kepler_joules: {
      query: `sum(rate(kepler_container_joules_total{container_name!=""}[1m])) by (container_name)`,
      explain: `Extracts per-container energy consumption rate in Joules/sec (Watts) using Kepler's eBPF kernel telemetry.`,
      metricName: 'kepler_container_joules_total',
      unit: 'Watts',
      seriesData: [107, 112, 109, 118, 124, 121, 115, 119, 114, 118.6]
    },
    http_requests: {
      query: `sum(rate(http_requests_total{handler=~"/payment.*"}[1m]))`,
      explain: `Calculates incoming transaction throughput (requests per second) processed by the FastAPI payment-service.`,
      metricName: 'http_requests_total',
      unit: 'req/sec',
      seriesData: [22, 25, 24, 28, 34, 30, 26, 29, 27, 28.5]
    },
    latency_p99: {
      query: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000`,
      explain: `Evaluates 99th percentile HTTP response latency in milliseconds to verify the RNF05 SLA requirement (< 2000ms).`,
      metricName: 'p99_latency_ms',
      unit: 'milliseconds',
      seriesData: [41, 44, 42, 48, 55, 49, 43, 46, 44, 46.2]
    },
    payment_joules_increase: {
      query: `sum(increase(kepler_container_joules_total{container_name="payment-service"}[5m]))`,
      explain: `Calculates total energy delta (in Joules) consumed specifically by the payment-service during the last 5 minutes.`,
      metricName: 'kepler_payment_delta_joules',
      unit: 'Joules',
      seriesData: [1200, 1340, 1290, 1510, 1720, 1610, 1450, 1580, 1490, 1520]
    }
  }
};

// Chart instances dictionary
const charts = {};

// --- Initialization on Window Load ---
window.addEventListener('DOMContentLoaded', () => {
  initCharts();
  renderTransactionStream();
  renderFullLedger();
  loadPromQLPreset();
  startLiveMetricsTicker();
});

// --- View Switching ---
function switchView(viewName, clickedBtn) {
  state.activeView = viewName;

  // Toggle active class on navigation links
  document.querySelectorAll('.nav-link').forEach(btn => btn.classList.remove('active'));
  if (clickedBtn) {
    clickedBtn.classList.add('active');
  } else {
    // Find matching button
    document.querySelectorAll('.nav-link').forEach(btn => {
      if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(viewName)) {
        btn.classList.add('active');
      }
    });
  }

  // Toggle active class on view panels
  document.querySelectorAll('.view-panel').forEach(panel => panel.classList.remove('active'));
  const targetPanel = document.getElementById(`view-${viewName}`);
  if (targetPanel) {
    targetPanel.classList.add('active');
  }

  // Trigger chart resize when switching to avoid canvas zero-width glitch
  setTimeout(() => {
    Object.values(charts).forEach(chart => {
      if (chart) chart.resize();
    });
  }, 50);
}

// --- Chart Initialization ---
function initCharts() {
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { font: { family: 'Inter', size: 11, weight: '500' }, color: '#475569' }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { family: 'Inter', size: 12, weight: '600' },
        bodyFont: { family: 'JetBrains Mono', size: 12 },
        padding: 10,
        cornerRadius: 6
      }
    },
    scales: {
      x: {
        grid: { color: '#f1f5f9' },
        ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
      },
      y: {
        grid: { color: '#f1f5f9' },
        ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
      }
    }
  };

  // 1. Overview Carbon-per-Tx Chart
  const ctxOverviewCarbon = document.getElementById('overviewCarbonChart')?.getContext('2d');
  if (ctxOverviewCarbon) {
    charts.overviewCarbon = new Chart(ctxOverviewCarbon, {
      type: 'line',
      data: {
        labels: [...state.timeLabels],
        datasets: [
          {
            label: 'Carbon Intensity (g CO₂/tx)',
            data: [...state.carbonSeries],
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.08)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 3,
            pointBackgroundColor: '#059669'
          },
          {
            label: 'RF07 Safety Threshold (12 g CO₂)',
            data: Array(state.timeLabels.length).fill(state.config.carbonThreshold),
            borderColor: '#f59e0b',
            borderDash: [5, 5],
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        ...commonOptions,
        scales: {
          ...commonOptions.scales,
          y: { ...commonOptions.scales.y, min: 0, max: 18 }
        }
      }
    });
  }

  // 2. Overview Energy Breakdown Chart
  const ctxOverviewEnergy = document.getElementById('overviewEnergyChart')?.getContext('2d');
  if (ctxOverviewEnergy) {
    charts.overviewEnergy = new Chart(ctxOverviewEnergy, {
      type: 'bar',
      data: {
        labels: [...state.timeLabels],
        datasets: [
          {
            label: 'payment-service (Watts)',
            data: [...state.energyPaymentSeries],
            backgroundColor: '#2563eb',
            borderRadius: 4
          },
          {
            label: 'auth-service (Watts)',
            data: [...state.energyAuthSeries],
            backgroundColor: '#10b981',
            borderRadius: 4
          }
        ]
      },
      options: {
        ...commonOptions,
        scales: {
          x: { ...commonOptions.scales.x, stacked: true },
          y: { ...commonOptions.scales.y, stacked: true }
        }
      }
    });
  }

  // 3. Grafana Panel 1: Carbon-per-Tx Over Time
  const ctxGrafanaCarbon = document.getElementById('grafanaCarbonPanel')?.getContext('2d');
  if (ctxGrafanaCarbon) {
    charts.grafanaCarbon = new Chart(ctxGrafanaCarbon, {
      type: 'line',
      data: {
        labels: [...state.timeLabels],
        datasets: [{
          label: 'g CO₂ / transaction',
          data: [...state.carbonSeries],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3
        }]
      },
      options: commonOptions
    });
  }

  // 4. Grafana Panel 2: Energy Allocation (Multi-line)
  const ctxGrafanaEnergy = document.getElementById('grafanaEnergyPanel')?.getContext('2d');
  if (ctxGrafanaEnergy) {
    charts.grafanaEnergy = new Chart(ctxGrafanaEnergy, {
      type: 'line',
      data: {
        labels: [...state.timeLabels],
        datasets: [
          {
            label: 'payment-service',
            data: [...state.energyPaymentSeries],
            borderColor: '#2563eb',
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 2
          },
          {
            label: 'auth-service',
            data: [...state.energyAuthSeries],
            borderColor: '#7c3aed',
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 2
          }
        ]
      },
      options: commonOptions
    });
  }

  // 5. Grafana Panel 3: Throughput
  const ctxGrafanaThroughput = document.getElementById('grafanaThroughputPanel')?.getContext('2d');
  if (ctxGrafanaThroughput) {
    charts.grafanaThroughput = new Chart(ctxGrafanaThroughput, {
      type: 'line',
      data: {
        labels: [...state.timeLabels],
        datasets: [{
          label: 'Requests / sec (FastAPI)',
          data: [...state.throughputSeries],
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3
        }]
      },
      options: commonOptions
    });
  }

  // 6. PromQL Result Chart
  const ctxPromQL = document.getElementById('promqlResultChart')?.getContext('2d');
  if (ctxPromQL) {
    charts.promqlResult = new Chart(ctxPromQL, {
      type: 'line',
      data: {
        labels: [...state.timeLabels],
        datasets: [{
          label: 'Evaluated PromQL Series',
          data: [...state.carbonSeries],
          borderColor: '#0f172a',
          backgroundColor: 'rgba(15, 23, 42, 0.05)',
          fill: true,
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#0f172a'
        }]
      },
      options: commonOptions
    });
  }
}

// --- Live Simulation & Ticker ---
function startLiveMetricsTicker() {
  setInterval(() => {
    // Add minor baseline fluctuation (±0.1)
    const delta = (Math.random() - 0.5) * 0.2;
    state.metrics.carbonPerTx = Math.max(5.0, Number((state.metrics.carbonPerTx + delta).toFixed(2)));
    state.metrics.activePowerWatts = Number((118.0 + (Math.random() - 0.5) * 4).toFixed(1));
    
    // Update live DOM values
    const kpiCarbon = document.getElementById('kpi-carbon-tx');
    if (kpiCarbon) kpiCarbon.textContent = state.metrics.carbonPerTx;
    
    const kpiEnergy = document.getElementById('kpi-energy-joules');
    if (kpiEnergy) kpiEnergy.textContent = state.metrics.activePowerWatts;

    const grafanaCarbon = document.getElementById('grafana-stat-carbon');
    if (grafanaCarbon) grafanaCarbon.innerHTML = `${state.metrics.carbonPerTx} <span class="unit">g CO₂/tx</span>`;

    const grafanaPower = document.getElementById('grafana-stat-power');
    if (grafanaPower) grafanaPower.innerHTML = `${state.metrics.activePowerWatts} <span class="unit">Watts</span>`;

    const lastTime = document.getElementById('last-update-time');
    if (lastTime) lastTime.textContent = new Date().toLocaleTimeString();
  }, 4000);
}

// --- Bank Money Transfer Engine ---
function processSimulatedTransfer({ senderBankId, recipientBankId, amount, protocol, note }) {
  // 1. Calculate realistic energy consumption for the transfer
  // Base energy for FastAPI request + DB row locking + serialization: ~15 to 45 Joules
  const baseJoules = 18 + Math.min(amount / 5000, 25) + (Math.random() * 8);
  const joules = Number(baseJoules.toFixed(2));

  // 2. Derive carbon footprint using SRS formula:
  // (Joules / 3,600,000) * (emissionFactor * 1000) = grams CO2
  // Factor: 0.38 kg/kWh = 380 g/kWh.
  // 1 kWh = 3,600,000 Joules.
  const kwh = joules / 3600000;
  const carbonGrams = Number((kwh * state.config.emissionFactor * 1000).toFixed(4));

  // Check if threshold exceeded (RF07)
  const isAlert = carbonGrams > (state.config.carbonThreshold / 3) || carbonGrams > 10;

  // 3. Generate transaction record
  const txRef = 'TX-' + Math.floor(10000 + Math.random() * 90000) + '-' + Math.random().toString(36).substring(2, 6).toUpperCase();
  const newTx = {
    id: txRef,
    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
    senderBankId,
    recipientBankId,
    protocol: protocol || 'IMPS',
    amount: Number(amount),
    joules,
    carbonGrams,
    note: note || 'Simulated transaction',
    status: 'COMPLETED',
    isAlert
  };

  // 4. Update state
  state.transactions.unshift(newTx);
  state.metrics.txCount += 1;
  state.metrics.cumulativeCarbonKg = Number((state.metrics.cumulativeCarbonKg + (carbonGrams / 1000)).toFixed(3));
  
  // Recalculate PromQL derived carbon intensity
  const newCarbonIntensity = Number(((joules * 0.38) / 1.0).toFixed(2));
  state.metrics.carbonPerTx = newCarbonIntensity;

  // 5. Update KPI Cards in DOM
  updateKPIDisplay();

  // 6. Push to Chart Series
  pushNewDataPoint(newCarbonIntensity, joules);

  // 7. Re-render tables
  renderTransactionStream();
  renderFullLedger();

  // 8. Handle RF07 Alert if threshold breached
  if (isAlert) {
    triggerAlertBanner(`Transaction ${txRef} consumed ${joules} J (${carbonGrams} g CO₂), exceeding standard baseline!`);
  }

  return newTx;
}

// Push fresh data point to all charts
function pushNewDataPoint(carbonValue, energyValue) {
  const newTimeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // Update datasets
  state.timeLabels.shift();
  state.timeLabels.push(newTimeLabel);

  state.carbonSeries.shift();
  state.carbonSeries.push(carbonValue);

  state.energyPaymentSeries.shift();
  state.energyPaymentSeries.push(Number((energyValue * 0.7).toFixed(1)));

  state.energyAuthSeries.shift();
  state.energyAuthSeries.push(Number((energyValue * 0.3).toFixed(1)));

  state.throughputSeries.shift();
  state.throughputSeries.push(Number((25 + Math.random() * 10).toFixed(1)));

  // Update chart instances
  Object.values(charts).forEach(chart => {
    if (chart && chart.data && chart.data.labels) {
      chart.data.labels = [...state.timeLabels];
      chart.update('none'); // fast update without animation jerk
    }
  });

  if (charts.overviewCarbon) {
    charts.overviewCarbon.data.datasets[0].data = [...state.carbonSeries];
    charts.overviewCarbon.update();
  }

  if (charts.overviewEnergy) {
    charts.overviewEnergy.data.datasets[0].data = [...state.energyPaymentSeries];
    charts.overviewEnergy.data.datasets[1].data = [...state.energyAuthSeries];
    charts.overviewEnergy.update();
  }

  if (charts.grafanaCarbon) {
    charts.grafanaCarbon.data.datasets[0].data = [...state.carbonSeries];
    charts.grafanaCarbon.update();
  }

  if (charts.grafanaEnergy) {
    charts.grafanaEnergy.data.datasets[0].data = [...state.energyPaymentSeries];
    charts.grafanaEnergy.data.datasets[1].data = [...state.energyAuthSeries];
    charts.grafanaEnergy.update();
  }

  if (charts.grafanaThroughput) {
    charts.grafanaThroughput.data.datasets[0].data = [...state.throughputSeries];
    charts.grafanaThroughput.update();
  }
}

// Update KPI UI
function updateKPIDisplay() {
  const txEl = document.getElementById('kpi-tx-count');
  if (txEl) txEl.textContent = state.metrics.txCount.toLocaleString();

  const totalCarbonEl = document.getElementById('kpi-total-carbon');
  if (totalCarbonEl) totalCarbonEl.textContent = state.metrics.cumulativeCarbonKg;

  const carbonTxEl = document.getElementById('kpi-carbon-tx');
  if (carbonTxEl) carbonTxEl.textContent = state.metrics.carbonPerTx;

  const lastTime = document.getElementById('last-update-time');
  if (lastTime) lastTime.textContent = new Date().toLocaleTimeString();
}

// --- Render Table Streams ---
function renderTransactionStream() {
  const tbody = document.getElementById('quick-stream-tbody');
  if (!tbody) return;

  const recent = state.transactions.slice(0, 5);
  tbody.innerHTML = recent.map(tx => `
    <tr>
      <td><code>${tx.id}</code></td>
      <td><strong>${tx.recipientBankId}</strong></td>
      <td>₹${tx.amount.toLocaleString()}</td>
      <td>${tx.joules} J</td>
      <td><strong>${tx.carbonGrams} g</strong></td>
      <td><span class="badge-status ${tx.isAlert ? 'alert' : 'success'}">${tx.isAlert ? 'SPIKE' : 'OK'}</span></td>
    </tr>
  `).join('');
}

function renderFullLedger() {
  const tbody = document.getElementById('ledger-full-tbody');
  if (!tbody) return;

  tbody.innerHTML = state.transactions.map(tx => `
    <tr>
      <td style="font-size: 11px; color: #64748b;">${tx.timestamp}</td>
      <td><code>${tx.id}</code></td>
      <td><span class="badge-status success">${tx.senderBankId}</span></td>
      <td><span class="badge-status success">${tx.recipientBankId}</span></td>
      <td><span class="promql-badge">${tx.protocol}</span></td>
      <td><strong>₹${tx.amount.toLocaleString()}</strong></td>
      <td>${tx.joules} J</td>
      <td style="font-weight: 600; color: ${tx.isAlert ? '#e11d48' : '#059669'};">
        ${tx.carbonGrams} g CO₂
      </td>
      <td>
        <span class="balance-proof">DR: ${tx.senderBankId} (-₹${tx.amount}) = CR: ${tx.recipientBankId} (+₹${tx.amount})</span>
      </td>
    </tr>
  `).join('');
}

// --- Form Handlers ---
function handleQuickTransfer(e) {
  e.preventDefault();
  const recipientBankId = document.getElementById('quick-recipient').value;
  const amount = document.getElementById('quick-amount').value;
  const protocol = document.getElementById('quick-protocol').value;
  const note = document.getElementById('quick-note').value;

  const btn = document.getElementById('btn-submit-transfer');
  btn.textContent = 'Processing & Attributing Kepler Telemetry...';
  btn.disabled = true;

  setTimeout(() => {
    processSimulatedTransfer({
      senderBankId: 'HDFC9999',
      recipientBankId,
      amount,
      protocol,
      note
    });

    btn.textContent = 'Execute Simulated Transaction & Measure Carbon';
    btn.disabled = false;
  }, 400);
}

function triggerRandomTransaction() {
  const recipients = ['MAH123', 'IDF892', 'SBIN456', 'AXIS777'];
  const randRecipient = recipients[Math.floor(Math.random() * recipients.length)];
  const randAmount = Math.floor(Math.random() * 40 + 1) * 500;

  processSimulatedTransfer({
    senderBankId: 'HDFC9999',
    recipientBankId: randRecipient,
    amount: randAmount,
    protocol: 'IMPS',
    note: 'Quick randomized evaluation transfer'
  });
}

// Modal Handlers
function openQuickTransferModal() {
  document.getElementById('quick-transfer-modal')?.classList.remove('hidden');
}

function closeQuickTransferModal() {
  document.getElementById('quick-transfer-modal')?.classList.add('hidden');
}

function handleModalTransfer(e) {
  e.preventDefault();
  const recipientBankId = document.getElementById('modal-recipient').value;
  const amount = document.getElementById('modal-amount').value;
  const note = document.getElementById('modal-note').value;

  processSimulatedTransfer({
    senderBankId: 'HDFC9999',
    recipientBankId,
    amount,
    protocol: 'RTGS',
    note
  });

  closeQuickTransferModal();
}

// --- Swagger UI Interactive Simulator ---
function toggleEndpoint(bodyId) {
  const body = document.getElementById(bodyId);
  if (!body) return;
  body.classList.toggle('hidden');
}

function executeSwaggerTransfer() {
  const senderBankId = document.getElementById('swag-sender').value;
  const recipientBankId = document.getElementById('swag-recipient').value;
  const amount = document.getElementById('swag-amount').value;
  const note = document.getElementById('swag-desc').value;

  const resultTx = processSimulatedTransfer({
    senderBankId,
    recipientBankId,
    amount,
    protocol: 'IMPS',
    note
  });

  // Display raw Swagger response JSON matching SRS
  const jsonPreview = document.getElementById('swag-response-json');
  if (jsonPreview) {
    jsonPreview.textContent = JSON.stringify({
      status: "COMPLETED",
      transaction_id: resultTx.id,
      timestamp: resultTx.timestamp,
      sender_bank_id: senderBankId,
      recipient_bank_id: recipientBankId,
      amount_transferred: Number(amount),
      currency: "INR",
      telemetry: {
        container: "payment-service",
        joules_consumed: resultTx.joules,
        carbon_emissions_grams: resultTx.carbonGrams,
        promql_metric: "carbon_per_transaction",
        grid_emission_factor: state.config.emissionFactor
      },
      ledger: {
        debit_account: `${senderBankId}_cash_wallet (-${amount})`,
        credit_account: `${recipientBankId}_cash_wallet (+${amount})`,
        accounting_balance_check: "OK (Debits = Credits)"
      }
    }, null, 2);
  }
}

function tryLoginEndpoint() {
  const res = document.getElementById('res-login');
  if (res) {
    res.innerHTML = `<strong>Response [200 OK]:</strong><pre><code>${JSON.stringify({
      access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJiYW5rX2lkIjoiSERGQzk5OTkifQ.demoToken",
      token_type: "bearer",
      bank_id: "HDFC9999",
      username: "soham_gaikwad",
      authenticated_at: new Date().toISOString()
    }, null, 2)}</code></pre>`;
  }
}

function tryTelemetryEndpoint() {
  const res = document.getElementById('res-telemetry');
  if (res) {
    res.innerHTML = `<strong>Response [200 OK]:</strong><pre><code>${JSON.stringify({
      platform_power_watts: 145.8,
      container_power_watts: state.metrics.activePowerWatts,
      container_breakdown_watts: [
        { name: "payment-service", watts: Number((state.metrics.activePowerWatts * 0.68).toFixed(1)) },
        { name: "auth-service", watts: Number((state.metrics.activePowerWatts * 0.32).toFixed(1)) }
      ],
      carbon_emission_rate_kg_per_hour: Number((state.metrics.activePowerWatts * 0.001 * state.config.emissionFactor).toFixed(5)),
      timestamp: new Date().toISOString()
    }, null, 2)}</code></pre>`;
  }
}

// --- PromQL Console Functions ---
function loadPromQLPreset() {
  const select = document.getElementById('promql-presets');
  if (!select) return;
  const key = select.value;
  const preset = state.promqlPresets[key];
  if (!preset) return;

  const queryInput = document.getElementById('promql-query-input');
  if (queryInput) queryInput.value = preset.query;

  const explain = document.getElementById('promql-explanation');
  if (explain) explain.textContent = preset.explain;

  executePromQLQuery();
}

function executePromQLQuery() {
  const select = document.getElementById('promql-presets');
  const key = select ? select.value : 'carbon_per_tx';
  const preset = state.promqlPresets[key] || state.promqlPresets['carbon_per_tx'];

  const now = Date.now() / 1000;
  const sampleValue = preset.seriesData[preset.seriesData.length - 1];

  // Update PromQL JSON output
  const jsonBox = document.getElementById('promql-json-output');
  if (jsonBox) {
    jsonBox.textContent = JSON.stringify({
      status: "success",
      data: {
        resultType: "vector",
        result: [
          {
            metric: {
              __name__: preset.metricName,
              service: "payment-service",
              job: "green-finance-telemetry",
              unit: preset.unit
            },
            value: [now, sampleValue.toString()]
          }
        ]
      }
    }, null, 2);
  }

  // Update PromQL Result Chart
  if (charts.promqlResult) {
    charts.promqlResult.data.datasets[0].label = `${preset.metricName} (${preset.unit})`;
    charts.promqlResult.data.datasets[0].data = [...preset.seriesData];
    charts.promqlResult.update();
  }

  const titleEl = document.getElementById('promql-chart-title');
  if (titleEl) titleEl.textContent = `PromQL Evaluation: ${preset.metricName}`;
}

// --- Grafana Controls ---
function updateGrafanaTimeRange() {
  const range = document.getElementById('grafana-timerange').value;
  // Trigger chart re-render with animation
  Object.values(charts).forEach(c => { if (c) c.update(); });
}

function toggleGrafanaRefresh() {
  // Configured in interval
}

function manualGrafanaRefresh() {
  triggerRandomTransaction();
}

// --- Alert Handling (RF07) ---
function triggerAlertBanner(message) {
  const banner = document.getElementById('high-emission-alert');
  const msgEl = document.getElementById('alert-message');
  if (banner && msgEl) {
    msgEl.textContent = message;
    banner.classList.remove('hidden');
  }
}

function dismissAlert() {
  document.getElementById('high-emission-alert')?.classList.add('hidden');
}

// --- Settings Actions ---
function saveESGConfig() {
  const factor = parseFloat(document.getElementById('cfg-emission-factor').value);
  const interval = parseInt(document.getElementById('cfg-scrape-interval').value);
  if (!isNaN(factor)) state.config.emissionFactor = factor;
  if (!isNaN(interval)) state.config.scrapeInterval = interval;
  alert(`Settings saved! Grid emission factor set to ${state.config.emissionFactor} kg CO₂/kWh.`);
}

function saveAlertRules() {
  const threshold = parseFloat(document.getElementById('cfg-carbon-threshold').value);
  if (!isNaN(threshold)) {
    state.config.carbonThreshold = threshold;
    if (charts.overviewCarbon) {
      charts.overviewCarbon.data.datasets[1].data = Array(state.timeLabels.length).fill(threshold);
      charts.overviewCarbon.update();
    }
  }
  alert(`RF07 Alert threshold set to ${state.config.carbonThreshold} g CO₂/transaction.`);
}

// --- CSV Export ---
function exportLedgerCSV() {
  let csv = 'Timestamp,Tx_ID,Sender_Bank_ID,Recipient_Bank_ID,Protocol,Amount_INR,Energy_Joules,Carbon_Grams_CO2,Status\n';
  state.transactions.forEach(t => {
    csv += `"${t.timestamp}","${t.id}","${t.senderBankId}","${t.recipientBankId}","${t.protocol}",${t.amount},${t.joules},${t.carbonGrams},"${t.status}"\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Green_Finance_Ledger_${new Date().toISOString().substring(0,10)}.csv`;
  a.click();
}
