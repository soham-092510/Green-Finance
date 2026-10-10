/**
 * =====================================================================
 * MOVA BANKING APPLICATION CONTROLLER (bank.js)
 * Strict implementation matching Reference Image 1:
 * - Glowing green sparkline canvas
 * - Live INR (₹) balances and atomic transfers
 * - Real-time computational energy (Joules) & Scope 2 CO₂ estimation
 * - Cryptographic SHA-256 audit digest receipts
 * - Dynamic Recent Transactions and Spending Overview pillars
 * =====================================================================
 */

const MOVA_STATE = {
  currentUser: {
    username: 'olivia_rhye',
    name: 'Olivia Rhye',
    firstName: 'Olivia',
    bank_id: 'OLIV5678',
    card_mask: '•••• 5678',
    tier: 'Premium',
    avatar: 'O'
  },
  accounts: [],
  transactions: [],
  totalBalance: 24560.00,
  mainAccountBalance: 9560.00,
  spendingTotal: 1820.00,
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
function initUserSession() {
  const saved = localStorage.getItem('mova_active_user');
  if (saved) {
    try {
      MOVA_STATE.currentUser = JSON.parse(saved);
    } catch (e) {
      console.warn('Could not parse saved user', e);
    }
  }
  renderUserInterface();
}

function renderUserInterface() {
  const u = MOVA_STATE.currentUser;
  
  const greetName = document.getElementById('header-greet-name');
  if (greetName) greetName.textContent = `${u.firstName || u.name.split(' ')[0]}!`;

  const sbAvatar = document.getElementById('sidebar-avatar');
  if (sbAvatar) sbAvatar.textContent = u.avatar || u.name.charAt(0);

  const sbName = document.getElementById('sidebar-user-name');
  if (sbName) sbName.textContent = u.name;

  const sbTier = document.getElementById('sidebar-user-tier');
  if (sbTier) sbTier.textContent = u.tier || 'Client';

  const cardMask = document.getElementById('card-masked-num');
  if (cardMask) cardMask.textContent = u.card_mask || `•••• ${u.bank_id.slice(-4)}`;

  // Update source dropdown in transfer modal
  const srcSelect = document.getElementById('transfer-source-acc');
  if (srcSelect) {
    srcSelect.innerHTML = `
      <option value="${u.bank_id}" selected>Main Account • ${u.bank_id} (${formatINR(MOVA_STATE.mainAccountBalance)})</option>
      <option value="HDFC9999">Savings Account • HDFC9999 (₹26,289.38)</option>
      <option value="DEMO0001">Investor Reserve • DEMO0001 (₹45,000.00)</option>
    `;
  }
}

function switchUser(userId) {
  const users = {
    'olivia_rhye': {
      username: 'olivia_rhye',
      name: 'Olivia Rhye',
      firstName: 'Olivia',
      bank_id: 'OLIV5678',
      card_mask: '•••• 5678',
      tier: 'Premium',
      avatar: 'O',
      mainBal: 9560.00,
      totalBal: 24560.00
    },
    'soham_gaikwad': {
      username: 'soham_gaikwad',
      name: 'Soham Gaikwad',
      firstName: 'Soham',
      bank_id: 'HDFC9999',
      card_mask: '•••• 9999',
      tier: 'Admin',
      avatar: 'SG',
      mainBal: 26289.38,
      totalBal: 58240.00
    },
    'demo_user': {
      username: 'demo_user',
      name: 'Demo User',
      firstName: 'Demo',
      bank_id: 'DEMO0001',
      card_mask: '•••• 0001',
      tier: 'Investor',
      avatar: 'DU',
      mainBal: 45000.00,
      totalBal: 85000.00
    },
    'alice_smith': {
      username: 'alice_smith',
      name: 'Alice Smith',
      firstName: 'Alice',
      bank_id: 'ALICE101',
      card_mask: '•••• 1101',
      tier: 'Personal',
      avatar: 'AS',
      mainBal: 18200.00,
      totalBal: 32400.00
    },
    'bob_kumar': {
      username: 'bob_kumar',
      name: 'Bob Kumar',
      firstName: 'Bob',
      bank_id: 'BOB202',
      card_mask: '•••• 2202',
      tier: 'Personal',
      avatar: 'BK',
      mainBal: 12400.00,
      totalBal: 21900.00
    }
  };

  const selected = users[userId] || users['olivia_rhye'];
  MOVA_STATE.currentUser = selected;
  MOVA_STATE.mainAccountBalance = selected.mainBal;
  MOVA_STATE.totalBalance = selected.totalBal;

  localStorage.setItem('mova_active_user', JSON.stringify(selected));
  renderUserInterface();
  updateBalanceDisplays();
  closeModal('modal-user');
  showToast(`Switched account to ${selected.name}`);
}

function logoutUser() {
  localStorage.removeItem('mova_active_user');
  switchUser('olivia_rhye');
  showToast('Logged out to default profile');
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

  // Normalised points matching Reference Image 1's wave profile
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

  // Reset shadow for subsequent drawings
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
    MOVA_STATE.accounts = data;

    // Look up current user's balance
    const current = data.find(a => a.bank_id === MOVA_STATE.currentUser.bank_id);
    if (current) {
      MOVA_STATE.mainAccountBalance = current.balance;
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
    MOVA_STATE.transactions = data;
    renderRecentTransactions(data);
  } catch (e) {
    console.warn('Using standard static transactions:', e);
  }
}

function updateBalanceDisplays() {
  const totDisp = document.getElementById('total-balance-display');
  if (totDisp) totDisp.textContent = formatINR(MOVA_STATE.totalBalance);

  const mainDisp = document.getElementById('main-account-balance');
  if (mainDisp) mainDisp.textContent = formatINR(MOVA_STATE.mainAccountBalance);

  const spendDisp = document.getElementById('spending-total-val');
  if (spendDisp) spendDisp.textContent = formatINR(MOVA_STATE.spendingTotal);
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

  // Static 4 reference items from Reference Image 1
  const staticItems = [
    {
      name: 'Amazon',
      time: '7 Aug, 20:24',
      amount: -78.90,
      avatarClass: 'amazon',
      avatarContent: 'a',
      desc: 'Amazon Marketplace Online Shopping'
    },
    {
      name: 'Spotify',
      time: '13 Aug, 20:24',
      amount: -9.99,
      avatarClass: 'spotify',
      avatarSvg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 11.5c3-1 6-0.8 8.5.5M8.5 14.2c2.5-.8 5-.6 7 .4M9 17c2-.6 4-.5 5.5.3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
      desc: 'Spotify Premium Streaming Monthly Subscription'
    },
    {
      name: 'Salary',
      time: '7 Aug, 20:24',
      amount: 2450.00,
      avatarClass: 'salary',
      avatarSvg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
      desc: 'Enterprise Payroll Direct Salary Credit'
    },
    {
      name: 'Starbucks',
      time: '7 Aug, 20:24',
      amount: -4.50,
      avatarClass: 'starbucks',
      avatarSvg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/><path d="M12 6a6 6 0 0 0-6 6c0 3.3 2.7 6 6 6s6-2.7 6-6a6 6 0 0 0-6-6zm0 10a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" fill="#ffffff"/></svg>',
      desc: 'Starbucks Coffee POS Payment'
    }
  ];

  // If live transactions exist, prepend the most recent ones
  const dynamicItems = (liveList || []).slice(0, 3).map(tx => {
    const isCredit = tx.recipient_bank_id === MOVA_STATE.currentUser.bank_id;
    return {
      name: isCredit ? `From: ${tx.sender_bank_id}` : `To: ${tx.recipient_bank_id}`,
      time: tx.timestamp ? tx.timestamp.split('T')[1] || tx.timestamp : 'Just now',
      amount: isCredit ? tx.amount : -tx.amount,
      avatarClass: 'bank',
      avatarContent: '₹',
      desc: tx.description || 'UPI Transfer Payment',
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
      : `<div class="tx-avatar ${item.avatarClass}">${item.avatarContent || '🏛️'}</div>`;

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

  // Store active rendered items for receipt modals
  MOVA_STATE._renderedItems = allItems;
}

function handleTxItemClick(idx) {
  const item = MOVA_STATE._renderedItems ? MOVA_STATE._renderedItems[idx] : null;
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
  MOVA_STATE.spendingPeriodIndex = (MOVA_STATE.spendingPeriodIndex + 1) % MOVA_STATE.spendingPeriods.length;
  const label = MOVA_STATE.spendingPeriods[MOVA_STATE.spendingPeriodIndex];
  
  const labelEl = document.getElementById('spending-period-label');
  if (labelEl) labelEl.textContent = label;

  const multipliers = [1.0, 1.25, 12.4];
  const mult = multipliers[MOVA_STATE.spendingPeriodIndex];
  MOVA_STATE.spendingTotal = 1820.00 * mult;
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
  const note = document.getElementById('transfer-note').value || 'Mova Transfer';

  const payload = {
    source_account: srcAcc,
    destination_account: destAcc,
    amount: amount,
    currency: 'INR',
    transaction_type: paymentType,
    note: note
  };

  try {
    const res = await fetch('/payment/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Transfer failed');
    }

    const txData = await res.json();

    // Deduct from balance locally
    MOVA_STATE.mainAccountBalance = Math.max(0, MOVA_STATE.mainAccountBalance - amount);
    MOVA_STATE.totalBalance = Math.max(0, MOVA_STATE.totalBalance - amount);
    updateBalanceDisplays();

    closeModal('modal-transfer');
    showLiveReceipt(txData);
    showToast(`Transfer of ${formatINR(amount)} completed!`);

    // Reload backend ledger in background
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
  document.getElementById('rcpt-sender').textContent = `${tx.sender_bank_id || 'HDFC9999'} (${MOVA_STATE.currentUser.name})`;
  document.getElementById('rcpt-recipient').textContent = `${tx.recipient_bank_id || 'MAH123'} (Verified Creditor)`;
  
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
  document.getElementById('rcpt-time').textContent = '2026-08-13 20:24:00 IST';
  document.getElementById('rcpt-sender').textContent = isPos ? `${merchant} Direct Pay` : `${MOVA_STATE.currentUser.bank_id} (${MOVA_STATE.currentUser.name})`;
  document.getElementById('rcpt-recipient').textContent = isPos ? `${MOVA_STATE.currentUser.bank_id} (Main Account)` : `${merchant} (POS Creditor)`;
  document.getElementById('rcpt-energy').textContent = '0.4820 Joules (1.34e-7 kWh)';
  document.getElementById('rcpt-carbon').textContent = '0.0955 mg CO₂ (0.000095 g)';
  document.getElementById('rcpt-hash').textContent = 'e4b988f4c' + Math.random().toString(16).substring(2, 14) + 'a97f10b71946c109a';

  openModal('modal-receipt');
}

/* ---------------------------------------------------------------------
   9. QUICK ACTIONS (Bills, Top Up, Workload Exchange)
   --------------------------------------------------------------------- */
function quickPayBill(billName, amount) {
  closeModal('modal-paybills');
  document.getElementById('transfer-dest-acc').value = 'manual';
  document.getElementById('manual-recipient-group').classList.remove('hidden');
  document.getElementById('manual-recipient-id').value = billName.split(' ')[0].toUpperCase() + 'BILL';
  document.getElementById('transfer-amount-input').value = amount;
  document.getElementById('transfer-note').value = billName;
  updateCarbonPreview();
  openModal('modal-transfer');
}

function executeTopUp() {
  const amt = parseFloat(document.getElementById('topup-amount').value) || 5000;
  MOVA_STATE.mainAccountBalance += amt;
  MOVA_STATE.totalBalance += amt;
  updateBalanceDisplays();
  closeModal('modal-topup');
  showToast(`Successfully deposited ${formatINR(amt)} into your Main Account!`);
}

async function executeBatchSimulation(count) {
  const feedback = document.getElementById('exchange-feedback');
  if (feedback) feedback.textContent = `Dispatching ${count} concurrent transactions...`;

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
  showToast('Cards view: Visa Debit •••• 5678 active');
}

function openAnalyticsModal() {
  window.location.href = '/investigator';
}

function openSettingsModal() {
  showToast('Settings: High-contrast mode & UPI encryption enabled');
}

function openSupportModal() {
  showToast('Support: 24/7 Green Banking desk reachable at support@greenfinance.io');
}

function openAllTransactionsModal() {
  window.location.href = '/investigator';
}

function switchNav(route, btn) {
  document.querySelectorAll('.mova-nav-link').forEach(el => el.classList.remove('active'));
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
  showToast('No unread alerts. All carbon audit ledgers are in compliance.');
}

function showToast(msg) {
  const container = document.getElementById('mova-toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'mova-toast';
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
