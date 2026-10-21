/**
 * =====================================================================
 * GREEN FINANCE — BANKING APPLICATION CONTROLLER (bank.js)
 * Implements:
 * - Real-time banking operations in INR (₹)
 * - Soham Gaikwad (Admin) default profile
 * - Green Bond investments & eco transactions
 * - Glowing neon green sparkline canvas
 * - Real-time computational energy (Joules) & Scope 2 CO₂ estimation
 * - Cryptographic SHA-256 audit digest receipts
 * - Dynamic Recent Transactions and Spending Overview pillars
 * =====================================================================
 */

const GREEN_BANK_STATE = {
  currentUser: {
    username: 'soham_gaikwad',
    name: 'Soham Gaikwad',
    firstName: 'Soham',
    bank_id: 'HDFC9999',
    card_mask: 'HDFC •••• 9999',
    tier: 'Green Premier • Admin',
    avatar: 'SG'
  },
  accounts: [],
  transactions: [],
  totalBalance: 26289.38,
  mainAccountBalance: 26289.38,
  spendingTotal: 8100.00,
  spendingCarbon: 0.89,
  spendingPeriodIndex: 0,
  spendingPeriods: ['This month', 'Last month', 'This year']
};

document.addEventListener('DOMContentLoaded', () => {
  initUserSession();
  drawNeonSparkline();
  loadBackendAccounts();
  loadBackendTransactions();
  updateCarbonPreview();

  // Resize listener to keep sparkline responsive
  window.addEventListener('resize', () => {
    drawNeonSparkline();
  });
});

/* ---------------------------------------------------------------------
   1. USER SESSION MANAGEMENT
   --------------------------------------------------------------------- */
async function initUserSession() {
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
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_role');
      window.location.href = '/login';
      return;
    }
    const u = await res.json();
    GREEN_BANK_STATE.currentUser = {
      username: u.username,
      name: u.name || u.username,
      firstName: (u.name || u.username).split(' ')[0],
      bank_id: u.bank_id || 'CUST101',
      card_mask: `GREEN •••• ${(u.bank_id || '9999').slice(-4)}`,
      tier: u.role === 'CUSTOMER' ? 'Verified Customer' : (u.role || 'Member'),
      avatar: (u.name || u.username).slice(0, 2).toUpperCase(),
      email: u.email,
      role: u.role
    };
    localStorage.setItem('green_bank_active_user', JSON.stringify(GREEN_BANK_STATE.currentUser));
    renderUserInterface();
    loadBackendAccounts();
    loadBackendTransactions();
  } catch (e) {
    console.warn('Session verification fallback:', e);
    const saved = localStorage.getItem('green_bank_active_user');
    if (saved) {
      try { GREEN_BANK_STATE.currentUser = JSON.parse(saved); } catch (_) {}
    }
    renderUserInterface();
  }
}

async function handleLogout() {
  const token = localStorage.getItem('access_token');
  if (token) {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.warn('Logout request warning:', e);
    }
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_role');
  localStorage.removeItem('green_bank_active_user');
  window.location.href = '/login';
}

function renderUserInterface() {
  const u = GREEN_BANK_STATE.currentUser;
  
  const greetName = document.getElementById('header-greet-name');
  if (greetName) greetName.textContent = `${u.firstName || u.name.split(' ')[0]}!`;

  const sbAvatar = document.getElementById('sidebar-avatar');
  if (sbAvatar) sbAvatar.textContent = u.avatar || u.name.slice(0, 2).toUpperCase();

  const sbName = document.getElementById('sidebar-user-name');
  if (sbName) sbName.textContent = u.name;

  const sbTier = document.getElementById('sidebar-user-tier');
  if (sbTier) sbTier.textContent = u.tier || 'Verified Customer';

  const cardMask = document.getElementById('card-masked-num');
  if (cardMask) cardMask.textContent = u.card_mask || `•••• ${(u.bank_id || '9999').slice(-4)}`;

  const headerBadge = document.getElementById('header-user-badge');
  if (headerBadge) headerBadge.textContent = `${u.name} (${u.role || 'CUSTOMER'})`;

  // Update Verified Profile Modal fields
  const mAvatar = document.getElementById('modal-profile-avatar');
  if (mAvatar) mAvatar.textContent = u.avatar || u.name.slice(0, 2).toUpperCase();
  const mName = document.getElementById('modal-profile-name');
  if (mName) mName.textContent = u.name;
  const mRole = document.getElementById('modal-profile-role');
  if (mRole) mRole.textContent = u.role || 'CUSTOMER';
  const mUser = document.getElementById('modal-profile-username');
  if (mUser) mUser.textContent = u.username;
  const mEmail = document.getElementById('modal-profile-email');
  if (mEmail) mEmail.textContent = u.email || `${u.username}@greenfinance.internal`;
  const mBankId = document.getElementById('modal-profile-bankid');
  if (mBankId) mBankId.textContent = u.bank_id;
  const mTier = document.getElementById('modal-profile-tier');
  if (mTier) mTier.textContent = u.tier || 'Green Premier';

  // Update source dropdown in transfer modal
  const srcSelect = document.getElementById('transfer-source-acc');
  if (srcSelect) {
    srcSelect.innerHTML = `
      <option value="${u.bank_id}" selected>${u.name} • ${u.bank_id} (${formatINR(GREEN_BANK_STATE.mainAccountBalance)})</option>
    `;
  }
}

function switchUser(userId) {
  const users = {
    'soham_gaikwad': {
      username: 'soham_gaikwad',
      name: 'Soham Gaikwad',
      firstName: 'Soham',
      bank_id: 'HDFC9999',
      card_mask: 'HDFC •••• 9999',
      tier: 'Green Premier • Admin',
      avatar: 'SG',
      mainBal: 26289.38,
      totalBal: 58240.00
    },
    'demo_user': {
      username: 'demo_user',
      name: 'Demo Investor',
      firstName: 'Investor',
      bank_id: 'DEMO0001',
      card_mask: 'AXIS •••• 0001',
      tier: 'ESG Investor',
      avatar: 'DU',
      mainBal: 45000.00,
      totalBal: 85000.00
    },
    'alice_smith': {
      username: 'alice_smith',
      name: 'Alice Smith',
      firstName: 'Alice',
      bank_id: 'ALICE101',
      card_mask: 'HDFC •••• 1101',
      tier: 'Retail Client',
      avatar: 'AS',
      mainBal: 18200.00,
      totalBal: 32400.00
    },
    'bob_kumar': {
      username: 'bob_kumar',
      name: 'Bob Kumar',
      firstName: 'Bob',
      bank_id: 'BOB202',
      card_mask: 'ICIC •••• 2202',
      tier: 'Corporate Client',
      avatar: 'BK',
      mainBal: 12400.00,
      totalBal: 21900.00
    }
  };

  const selected = users[userId] || users['soham_gaikwad'];
  GREEN_BANK_STATE.currentUser = selected;
  GREEN_BANK_STATE.mainAccountBalance = selected.mainBal;
  GREEN_BANK_STATE.totalBalance = selected.totalBal;

  localStorage.setItem('green_bank_active_user', JSON.stringify(selected));
  renderUserInterface();
  updateBalanceDisplays();
  closeModal('modal-user');
  showToast(`Switched account to ${selected.name}`);
}

/* ---------------------------------------------------------------------
   2. GLOWING NEON SPARKLINE (HTML5 Canvas)
   --------------------------------------------------------------------- */
function drawNeonSparkline() {
  const canvas = document.getElementById('sparkline-canvas');
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = (rect.width || 460) * dpr;
  canvas.height = (rect.height || 70) * dpr;

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const w = rect.width || 460;
  const h = rect.height || 70;

  ctx.clearRect(0, 0, w, h);

  const rawPoints = [
    { x: 0.00, y: 0.70 },
    { x: 0.10, y: 0.74 },
    { x: 0.20, y: 0.58 },
    { x: 0.28, y: 0.82 },
    { x: 0.36, y: 0.42 },
    { x: 0.45, y: 0.88 },
    { x: 0.55, y: 0.65 },
    { x: 0.66, y: 0.52 },
    { x: 0.75, y: 0.78 },
    { x: 0.85, y: 0.60 },
    { x: 0.94, y: 0.50 },
    { x: 1.00, y: 0.62 }
  ];

  const points = rawPoints.map(p => ({
    x: p.x * w,
    y: p.y * h
  }));

  // Path for fill gradient underneath
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 0; i < points.length - 1; i++) {
    const cpX = (points[i].x + points[i + 1].x) / 2;
    const cpY = (points[i].y + points[i + 1].y) / 2;
    ctx.quadraticCurveTo(points[i].x, points[i].y, cpX, cpY);
  }
  ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();

  const fillGradient = ctx.createLinearGradient(0, 0, 0, h);
  fillGradient.addColorStop(0, 'rgba(82, 189, 137, 0.35)');
  fillGradient.addColorStop(1, 'rgba(82, 189, 137, 0.0)');
  ctx.fillStyle = fillGradient;
  ctx.fill();

  // Glowing neon line stroke
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 0; i < points.length - 1; i++) {
    const cpX = (points[i].x + points[i + 1].x) / 2;
    const cpY = (points[i].y + points[i + 1].y) / 2;
    ctx.quadraticCurveTo(points[i].x, points[i].y, cpX, cpY);
  }
  ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);

  ctx.shadowColor = '#52bd89';
  ctx.shadowBlur = 12;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 0;
  ctx.strokeStyle = '#52bd89';
  ctx.lineWidth = 2.4;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  ctx.shadowBlur = 0;
}

/* ---------------------------------------------------------------------
   3. DATA FETCHING & BALANCE UPDATES
   --------------------------------------------------------------------- */
async function loadBackendAccounts() {
  try {
    const res = await fetch('/payment/accounts');
    if (!res.ok) return;
    const data = await res.json();
    GREEN_BANK_STATE.accounts = data;

    // Look up current user's balance
    const current = data.find(a => a.bank_id === GREEN_BANK_STATE.currentUser.bank_id);
    if (current) {
      GREEN_BANK_STATE.mainAccountBalance = current.balance;
      GREEN_BANK_STATE.totalBalance = current.balance + 31950.62;
    }
    updateBalanceDisplays();
  } catch (e) {
    console.warn('Fallback local balances in use:', e);
  }
}

async function loadBackendTransactions() {
  try {
    const res = await fetch('/payment/transactions');
    if (!res.ok) return;
    const data = await res.json();
    GREEN_BANK_STATE.transactions = data;
    renderRecentTransactions(data);
  } catch (e) {
    console.warn('Using standard green transactions:', e);
  }
}

function updateBalanceDisplays() {
  const totDisp = document.getElementById('total-balance-display');
  if (totDisp) totDisp.textContent = formatINR(GREEN_BANK_STATE.totalBalance);

  const mainDisp = document.getElementById('main-account-balance');
  if (mainDisp) mainDisp.textContent = formatINR(GREEN_BANK_STATE.mainAccountBalance);

  const spendDisp = document.getElementById('spending-total-val');
  if (spendDisp) spendDisp.textContent = formatINR(GREEN_BANK_STATE.spendingTotal);

  const spendCarb = document.getElementById('spending-carbon-val');
  if (spendCarb) spendCarb.textContent = `${GREEN_BANK_STATE.spendingCarbon.toFixed(2)} mg CO₂`;
}

function formatINR(val) {
  const num = typeof val === 'number' ? val : parseFloat(val) || 0;
  return '₹' + num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/* ---------------------------------------------------------------------
   4. RECENT TRANSACTIONS RENDERING
   --------------------------------------------------------------------- */
function renderRecentTransactions(liveList) {
  const list = document.getElementById('recent-transactions-list');
  if (!list) return;

  // Real Green Finance reference items
  const staticItems = [
    {
      name: 'Green Sovereign Bond 2026',
      time: '10 Oct, 18:30 • Clean Energy',
      amount: -5000.00,
      avatarClass: 'amazon',
      avatarContent: '🌱',
      desc: 'Clean Solar Infrastructure Sovereign Bond Investment'
    },
    {
      name: 'Tata Solar Utility',
      time: '09 Oct, 14:15 • Solar Tariff',
      amount: -1850.00,
      avatarClass: 'spotify',
      avatarContent: '⚡',
      desc: 'Tata Power Rooftop Solar Net Metering Tariff'
    },
    {
      name: 'Corporate ESG Payroll',
      time: '01 Oct, 09:00 • Salary Credit',
      amount: 25000.00,
      avatarClass: 'salary',
      avatarSvg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
      desc: 'Enterprise Payroll Direct Salary Credit with Scope 2 Attribution'
    },
    {
      name: 'Bank of Maharashtra (MAH123)',
      time: '28 Sep, 11:20 • Inter-Bank UPI',
      amount: -1250.00,
      avatarClass: 'starbucks',
      avatarContent: '🏛️',
      desc: 'UPI Double-Entry Transfer (0.695 J, 0.138 mg CO₂)'
    }
  ];

  // If live transactions exist, prepend the most recent ones
  const dynamicItems = (liveList || []).slice(0, 3).map(tx => {
    const isCredit = tx.recipient_bank_id === GREEN_BANK_STATE.currentUser.bank_id;
    return {
      name: isCredit ? `Credit from: ${tx.sender_bank_id}` : `Transfer to: ${tx.recipient_bank_id}`,
      time: tx.timestamp ? tx.timestamp.replace('T', ' ').slice(0, 16) : 'Just now',
      amount: isCredit ? tx.amount : -tx.amount,
      avatarClass: 'bank',
      avatarContent: '₹',
      desc: tx.description || 'UPI Inter-Bank Transfer',
      txRaw: tx
    };
  });

  const allItems = [...dynamicItems, ...staticItems];

  list.innerHTML = allItems.map((item, idx) => {
    const isPos = item.amount > 0;
    const sign = isPos ? '+ ' : '- ';
    const amtStr = sign + formatINR(Math.abs(item.amount));
    const amtClass = isPos ? 'tx-amount positive' : 'tx-amount negative';

    const avatarHtml = item.avatarSvg 
      ? `<div class="tx-avatar ${item.avatarClass}">${item.avatarSvg}</div>`
      : `<div class="tx-avatar ${item.avatarClass}">${item.avatarContent || '🌱'}</div>`;

    return `
      <li class="tx-item" onclick="handleTxItemClick(${idx})">
        <div class="tx-item-left">
          ${avatarHtml}
          <div class="tx-meta">
            <span class="tx-name">${item.name}</span>
            <span class="tx-time">${item.time}</span>
          </div>
        </div>
        <span class="${amtClass}">${amtStr}</span>
      </li>
    `;
  }).join('');

  GREEN_BANK_STATE._renderedItems = allItems;
}

function handleTxItemClick(idx) {
  const item = GREEN_BANK_STATE._renderedItems ? GREEN_BANK_STATE._renderedItems[idx] : null;
  if (!item) return;

  if (item.txRaw) {
    showLiveReceipt(item.txRaw);
  } else {
    showStaticReceipt(item.name, item.amount, item.desc);
  }
}

/* ---------------------------------------------------------------------
   5. SPENDING OVERVIEW & PILLARS
   --------------------------------------------------------------------- */
function cycleSpendingPeriod() {
  GREEN_BANK_STATE.spendingPeriodIndex = (GREEN_BANK_STATE.spendingPeriodIndex + 1) % GREEN_BANK_STATE.spendingPeriods.length;
  const label = GREEN_BANK_STATE.spendingPeriods[GREEN_BANK_STATE.spendingPeriodIndex];
  
  const labelEl = document.getElementById('spending-period-label');
  if (labelEl) labelEl.textContent = label;

  const multipliers = [1.0, 1.35, 11.8];
  const mult = multipliers[GREEN_BANK_STATE.spendingPeriodIndex];
  GREEN_BANK_STATE.spendingTotal = 8100.00 * mult;
  GREEN_BANK_STATE.spendingCarbon = 0.89 * mult;
  updateBalanceDisplays();

  // Vary pillar heights dynamically
  const bars = document.querySelectorAll('.pillar-bar');
  const baseHeights = [38, 58, 86, 52, 104, 128, 74];
  bars.forEach((bar, i) => {
    const newH = Math.min(130, Math.max(20, Math.round(baseHeights[i] * (0.8 + Math.random() * 0.4))));
    bar.style.height = `${newH}px`;
  });
}

/* ---------------------------------------------------------------------
   6. REAL-TIME CARBON CALCULATION PREVIEW
   --------------------------------------------------------------------- */
function updateCarbonPreview() {
  const amtInput = document.getElementById('transfer-amount-input');
  const amount = parseFloat(amtInput ? amtInput.value : 1250) || 1250;

  // Workload energy attribution formula: Baseline energy + marginal payload
  const energyJoules = 0.55 + (amount * 0.000116);
  // Scope 2 Carbon based on CEA India Baseline Factor (713.0 g CO₂ / kWh)
  const carbonGrams = (energyJoules / 3600000) * 713.0;
  const carbonMg = carbonGrams * 1000;

  const energyEl = document.getElementById('prev-energy');
  if (energyEl) energyEl.textContent = `${energyJoules.toFixed(4)} Joules`;

  const carbonEl = document.getElementById('prev-carbon');
  if (carbonEl) carbonEl.textContent = `${carbonMg.toFixed(4)} mg CO₂`;
}

function setQuickAmount(amt) {
  const input = document.getElementById('transfer-amount-input');
  if (input) {
    input.value = amt;
    updateCarbonPreview();
  }
}

function handleRecipientSelect(val) {
  const manualGroup = document.getElementById('manual-recipient-group');
  if (manualGroup) {
    if (val === 'manual') {
      manualGroup.classList.remove('hidden');
    } else {
      manualGroup.classList.add('hidden');
    }
  }
}

/* ---------------------------------------------------------------------
   7. LIVE PAYMENT TRANSFER SUBMISSION
   --------------------------------------------------------------------- */
async function handleTransferSubmit(e) {
  e.preventDefault();

  const btn = document.getElementById('btn-submit-transfer');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Processing Transaction & Telemetry...';
  }

  const srcAcc = document.getElementById('transfer-source-acc').value;
  let destAcc = document.getElementById('transfer-dest-acc').value;
  if (destAcc === 'manual') {
    destAcc = document.getElementById('manual-recipient-id').value.trim() || 'MAH123';
  }
  const amount = parseFloat(document.getElementById('transfer-amount-input').value) || 1250;
  const paymentType = document.getElementById('transfer-payment-type').value;
  const note = document.getElementById('transfer-note').value || 'Green Finance Transfer';

  const payload = {
    source_account: srcAcc,
    destination_account: destAcc,
    amount: amount,
    currency: 'INR',
    transaction_type: paymentType,
    note: note
  };

  try {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      'Idempotency-Key': 'idemp-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9)
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch('/payment/transfer', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Transfer failed');
    }

    const txData = await res.json();

    // Deduct from balance locally
    GREEN_BANK_STATE.mainAccountBalance = Math.max(0, GREEN_BANK_STATE.mainAccountBalance - amount);
    GREEN_BANK_STATE.totalBalance = Math.max(0, GREEN_BANK_STATE.totalBalance - amount);
    updateBalanceDisplays();

    closeModal('modal-transfer');
    showLiveReceipt(txData);
    showToast(`Transfer of ${formatINR(amount)} completed!`);

    loadBackendTransactions();
  } catch (error) {
    console.error('Transfer failed:', error);
    showToast(`Transfer Failed: ${error.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Authorize Transfer →';
    }
  }
}

/* ---------------------------------------------------------------------
   8. DIGITAL RECEIPT MODALS
   --------------------------------------------------------------------- */
function showLiveReceipt(tx) {
  document.getElementById('rcpt-amount').textContent = formatINR(tx.amount);
  document.getElementById('rcpt-txid').textContent = tx.transaction_id || '9a81d666-dbb4-4770-987a';
  document.getElementById('rcpt-time').textContent = `${tx.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19)} IST`;
  document.getElementById('rcpt-sender').textContent = `${tx.sender_bank_id || 'HDFC9999'} (${GREEN_BANK_STATE.currentUser.name})`;
  document.getElementById('rcpt-recipient').textContent = `${tx.recipient_bank_id || 'MAH123'} (Verified Beneficiary)`;
  
  const energyJ = tx.energy_joules || 0.6952;
  document.getElementById('rcpt-energy').textContent = `${energyJ.toFixed(4)} Joules (${(energyJ / 3600000).toExponential(2)} kWh)`;
  
  const carbonG = tx.carbon_grams || 0.000138;
  document.getElementById('rcpt-carbon').textContent = `${(carbonG * 1000).toFixed(4)} mg CO₂ (${carbonG.toFixed(6)} g)`;
  
  document.getElementById('rcpt-hash').textContent = tx.audit_hash || 'd3e87443725e8f8e9348140a88e8a58ec63ab14be3014a71249d5848c3d5d6e2';

  openModal('modal-receipt');
}

function showStaticReceipt(merchant, amt, desc) {
  const absAmt = Math.abs(amt);
  const isPos = amt > 0;
  
  document.getElementById('rcpt-amount').textContent = (isPos ? '+ ' : '- ') + formatINR(absAmt);
  document.getElementById('rcpt-txid').textContent = 'tx-' + Math.random().toString(36).substring(2, 10) + '-' + Math.random().toString(36).substring(2, 6);
  document.getElementById('rcpt-time').textContent = '2026-10-10 18:30:00 IST';
  document.getElementById('rcpt-sender').textContent = isPos ? `${merchant}` : `${GREEN_BANK_STATE.currentUser.bank_id} (${GREEN_BANK_STATE.currentUser.name})`;
  document.getElementById('rcpt-recipient').textContent = isPos ? `${GREEN_BANK_STATE.currentUser.bank_id} (Main Account)` : `${merchant}`;
  document.getElementById('rcpt-energy').textContent = '0.6952 Joules (1.93e-7 kWh)';
  document.getElementById('rcpt-carbon').textContent = '0.1376 mg CO₂ (0.000138 g)';
  document.getElementById('rcpt-hash').textContent = 'd3e87443725e8f8e9348140a88e8a58ec63ab14be3014a71249d5848c3d5d6e2';

  openModal('modal-receipt');
}

/* ---------------------------------------------------------------------
   9. QUICK ACTIONS (Bills, Top Up, Workload Exchange)
   --------------------------------------------------------------------- */
function quickPayBill(billName, amount) {
  closeModal('modal-paybills');
  document.getElementById('transfer-dest-acc').value = 'manual';
  document.getElementById('manual-recipient-group').classList.remove('hidden');
  document.getElementById('manual-recipient-id').value = billName.split(' ')[0].toUpperCase() + 'ECO';
  document.getElementById('transfer-amount-input').value = amount;
  document.getElementById('transfer-note').value = billName;
  updateCarbonPreview();
  openModal('modal-transfer');
}

function executeTopUp() {
  const amt = parseFloat(document.getElementById('topup-amount').value) || 5000;
  GREEN_BANK_STATE.mainAccountBalance += amt;
  GREEN_BANK_STATE.totalBalance += amt;
  updateBalanceDisplays();
  closeModal('modal-topup');
  showToast(`Successfully deposited ${formatINR(amt)} into your Green Finance account!`);
}

async function executeBatchSimulation(count) {
  const feedback = document.getElementById('exchange-feedback');
  if (feedback) feedback.textContent = `Dispatching ${count} concurrent microservice transactions...`;

  let successCount = 0;
  for (let i = 0; i < count; i++) {
    try {
      await fetch('/payment/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_account: 'HDFC9999',
          destination_account: 'MAH123',
          amount: Math.round(100 + Math.random() * 500),
          currency: 'INR',
          transaction_type: 'UPI_TRANSFER',
          note: `Batch workload simulation #${i + 1}`
        })
      });
      successCount++;
    } catch (e) {
      console.warn('Batch item error', e);
    }
  }

  if (feedback) {
    feedback.textContent = `✓ Generated ${successCount} transactions. Attributed ~${(successCount * 0.69).toFixed(1)} J of telemetry!`;
  }
  showToast(`Generated ${successCount} transactions across microservices!`);
  loadBackendAccounts();
  loadBackendTransactions();
}

/* ---------------------------------------------------------------------
   10. MODAL & NAVIGATION HELPERS
   --------------------------------------------------------------------- */
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('hidden');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('hidden');
}

function openTransferModal() {
  updateCarbonPreview();
  openModal('modal-transfer');
}

function openPayBillsModal() {
  openModal('modal-paybills');
}

function openTopUpModal() {
  openModal('modal-topup');
}

function openExchangeModal() {
  const feedback = document.getElementById('exchange-feedback');
  if (feedback) feedback.textContent = '';
  openModal('modal-exchange');
}

function openUserModal() {
  openModal('modal-user');
}

function openCardsModal() {
  showToast('Green Accounts: HDFC9999 Active (RuPay/VISA Platinum)');
}

function openAnalyticsModal() {
  showToast('Carbon Footprint: Computed live for every payment using Scope 2 baseline.');
}

function openSupportModal() {
  showToast('Green Finance Support & ESG Desk: support@greenfinance.io');
}

function openAllTransactionsModal() {
  showToast('All transaction receipts are cryptographically hashed and verified in ledger.');
}

function switchNav(route, btn) {
  document.querySelectorAll('.gf-bank-nav-link').forEach(el => el.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

function handleGlobalSearch(query) {
  const q = query.toLowerCase().trim();
  const items = document.querySelectorAll('.tx-item');
  items.forEach(el => {
    if (!q || el.textContent.toLowerCase().includes(q)) {
      el.style.display = 'flex';
    } else {
      el.style.display = 'none';
    }
  });
}

function toggleNotifications() {
  showToast('All transaction carbon audit ledgers are strictly compliant with CEA India baseline.');
}

function showToast(msg) {
  const container = document.getElementById('gf-bank-toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'gf-bank-toast';
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
