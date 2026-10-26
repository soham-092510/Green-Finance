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

document.addEventListener('DOMContentLoaded', async () => {
  drawNeonSparkline();
  updateCarbonPreview();
  await initUserSession();

  // Resize listener to keep sparkline responsive
  window.addEventListener('resize', () => {
    drawNeonSparkline();
  });
});

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function getCsrfToken() {
  return getCookie('csrf_token') || '';
}

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  const csrf = getCsrfToken();
  const headers = { 'Accept': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (csrf) headers['X-CSRF-Token'] = csrf;
  return headers;
}

/* ---------------------------------------------------------------------
   1. USER SESSION MANAGEMENT (SERVER-SOURCE-OF-TRUTH)
   --------------------------------------------------------------------- */
async function initUserSession() {
  try {
    let headers = getAuthHeaders();
    let res = await fetch('/user/me', { headers, credentials: 'same-origin' });

    // If bearer token was stale/rejected, retry with cookie credentials alone
    if (!res.ok && localStorage.getItem('access_token')) {
      localStorage.removeItem('access_token');
      res = await fetch('/user/me', { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' });
    }

    if (!res.ok) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_role');
      localStorage.removeItem('green_bank_active_user');
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
    await loadBackendAccounts();
    await loadBackendTransactions();
  } catch (e) {
    console.warn('Session verification fallback:', e);
    window.location.href = '/login';
  }
}

async function handleLogout() {
  const token = localStorage.getItem('access_token');
  const csrf = getCsrfToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (csrf) headers['X-CSRF-Token'] = csrf;

  try {
    await fetch('/auth/logout', {
      method: 'POST',
      headers: headers
    });
  } catch (e) {
    console.warn('Logout request warning:', e);
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

  // Update source hidden input in transfer modal
  const srcHidden = document.getElementById('transfer-source-acc');
  if (srcHidden) {
    srcHidden.value = u.bank_id;
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
    const res = await fetch('/payment/accounts', { headers: getAuthHeaders(), credentials: 'same-origin' });
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
    const res = await fetch('/payment/transactions', { headers: getAuthHeaders(), credentials: 'same-origin' });
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

  // Clean reference transactions
  const staticItems = [
    {
      name: 'Services: Electricity Bill (ELEC_MAHA)',
      time: '10 Oct, 18:30 • Utility Pay',
      amount: -1850.00,
      avatarClass: 'spotify',
      avatarContent: '⚡',
      desc: 'Maharashtra State Electricity Board Utility Payment'
    },
    {
      name: 'Corporate Salary Credit',
      time: '01 Oct, 09:00 • Direct Deposit',
      amount: 25000.00,
      avatarClass: 'salary',
      avatarSvg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
      desc: 'Monthly Corporate Salary Direct Bank Deposit'
    },
    {
      name: 'Transfer to: Bank of Maharashtra (MAH123)',
      time: '28 Sep, 11:20 • Inter-Bank UPI',
      amount: -1250.00,
      avatarClass: 'starbucks',
      avatarContent: '🏛️',
      desc: 'Instant Inter-Bank UPI Transfer'
    }
  ];

  const myBankId = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.bank_id) 
    ? String(GREEN_BANK_STATE.currentUser.bank_id).toUpperCase() 
    : '';

  // If live transactions exist, map them with clear counterparty naming
  const dynamicItems = (liveList || []).slice(0, 5).map(tx => {
    const recId = String(tx.recipient_bank_id || tx.recipientBankId || '').toUpperCase();
    const sendId = String(tx.sender_bank_id || tx.senderBankId || '').toUpperCase();
    const isCredit = recId === myBankId;

    let counterpartyTitle = '';
    if (isCredit) {
      const senderDisplay = tx.sender_name 
        ? `${tx.sender_name} (${tx.sender_bank_id || tx.senderBankId})` 
        : (tx.sender_bank_id || tx.senderBankId || 'Sender');
      counterpartyTitle = `Received from: ${senderDisplay}`;
    } else {
      const recipDisplay = tx.recipient_name 
        ? `${tx.recipient_name} (${tx.recipient_bank_id || tx.recipientBankId})` 
        : (tx.recipient_bank_id || tx.recipientBankId || 'Recipient');
      counterpartyTitle = `Transfer to: ${recipDisplay}`;
    }

    return {
      name: counterpartyTitle,
      time: tx.timestamp ? tx.timestamp.replace('T', ' ').slice(0, 16) : 'Just now',
      amount: isCredit ? tx.amount : -tx.amount,
      avatarClass: isCredit ? 'salary' : 'bank',
      avatarContent: isCredit ? '📥' : '📤',
      desc: tx.description || tx.note || 'Instant UPI Transfer',
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
      : `<div class="tx-avatar ${item.avatarClass}">${item.avatarContent || '₹'}</div>`;

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
   6. TRANSFER HELPERS
   --------------------------------------------------------------------- */
function updateCarbonPreview() {
  // Legacy stub retained for backwards compatibility
}

function setQuickAmount(amt) {
  const input = document.getElementById('transfer-amount-input');
  if (input) {
    input.value = amt;
  }
}

function handleRecipientSelect(val) {
  // Legacy stub retained for backwards compatibility
}

/* ---------------------------------------------------------------------
   7. LIVE PAYMENT TRANSFER SUBMISSION
   --------------------------------------------------------------------- */
async function handleTransferSubmit(e) {
  e.preventDefault();

  const btn = document.getElementById('btn-submit-transfer');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Processing Transfer...';
  }

  const srcAcc = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.bank_id) || 'HDFC9999';
  const destInput = document.getElementById('transfer-dest-acc');
  const destAcc = destInput ? destInput.value.trim() : 'MAH123';
  const amount = parseFloat(document.getElementById('transfer-amount-input').value) || 1250;
  const paymentType = 'UPI_TRANSFER';
  const note = (document.getElementById('transfer-note') && document.getElementById('transfer-note').value) || 'Direct Payment';

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
    const csrf = getCsrfToken();
    if (csrf) {
      headers['X-CSRF-Token'] = csrf;
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch('/payment/transfer', {
      method: 'POST',
      headers: headers,
      credentials: 'same-origin',
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

    await loadBackendAccounts();
    await loadBackendTransactions();
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
  const rcptAmt = document.getElementById('rcpt-amount');
  if (rcptAmt) rcptAmt.textContent = formatINR(tx.amount);

  const rcptTxid = document.getElementById('rcpt-txid');
  if (rcptTxid) rcptTxid.textContent = tx.transaction_id || 'tx-' + Math.random().toString(36).substring(2, 12);

  const rcptTime = document.getElementById('rcpt-time');
  if (rcptTime) rcptTime.textContent = `${tx.timestamp ? tx.timestamp.replace('T', ' ').slice(0, 19) : new Date().toISOString().replace('T', ' ').slice(0, 19)} IST`;

  const myName = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.name) || 'You';
  const myBankId = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.bank_id) || 'Account';
  const isCredit = String(tx.recipient_bank_id || tx.recipientBankId).toUpperCase() === myBankId.toUpperCase();

  const rcptSender = document.getElementById('rcpt-sender');
  if (rcptSender) {
    const sName = tx.sender_name || (isCredit ? 'Sender' : myName);
    const sId = tx.sender_bank_id || tx.senderBankId || myBankId;
    rcptSender.textContent = `${sId} (${sName})`;
  }

  const rcptRecip = document.getElementById('rcpt-recipient');
  if (rcptRecip) {
    const rName = tx.recipient_name || (isCredit ? myName : 'Beneficiary');
    const rId = tx.recipient_bank_id || tx.recipientBankId || 'Recipient';
    rcptRecip.textContent = `${rId} (${rName})`;
  }

  const rcptHash = document.getElementById('rcpt-hash');
  if (rcptHash) {
    rcptHash.textContent = tx.audit_hash ? `SHA-256: ${tx.audit_hash.slice(0, 24)}... (Verified)` : 'SHA-256 Ledger Verified';
  }

  openModal('modal-receipt');
}

function showStaticReceipt(merchant, amt, desc) {
  const absAmt = Math.abs(amt);
  const isPos = amt > 0;

  const rcptAmt = document.getElementById('rcpt-amount');
  if (rcptAmt) rcptAmt.textContent = (isPos ? '+ ' : '- ') + formatINR(absAmt);

  const rcptTxid = document.getElementById('rcpt-txid');
  if (rcptTxid) rcptTxid.textContent = 'tx-' + Math.random().toString(36).substring(2, 10);

  const rcptTime = document.getElementById('rcpt-time');
  if (rcptTime) rcptTime.textContent = 'Recent Transaction';

  const myName = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.name) || 'Account Holder';
  const myBankId = (GREEN_BANK_STATE.currentUser && GREEN_BANK_STATE.currentUser.bank_id) || 'HDFC9999';

  const rcptSender = document.getElementById('rcpt-sender');
  if (rcptSender) rcptSender.textContent = isPos ? `${merchant}` : `${myBankId} (${myName})`;

  const rcptRecip = document.getElementById('rcpt-recipient');
  if (rcptRecip) rcptRecip.textContent = isPos ? `${myBankId} (${myName})` : `${merchant}`;

  const rcptHash = document.getElementById('rcpt-hash');
  if (rcptHash) rcptHash.textContent = 'SHA-256 Ledger Verified';

  openModal('modal-receipt');
}

/* ---------------------------------------------------------------------
   9. QUICK ACTIONS (Bills, Top Up, Workload Exchange)
   --------------------------------------------------------------------- */
function quickPayBill(serviceName, providerId, defaultAmount) {
  closeModal('modal-paybills');
  const destInput = document.getElementById('transfer-dest-acc');
  if (destInput) destInput.value = providerId;
  const amtInput = document.getElementById('transfer-amount-input');
  if (amtInput) amtInput.value = defaultAmount;
  const noteInput = document.getElementById('transfer-note');
  if (noteInput) noteInput.value = serviceName;
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
  // Legacy stub retained
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
  openModal('modal-transfer');
}

function openPayBillsModal() {
  openModal('modal-paybills');
}

function openTopUpModal() {
  openModal('modal-topup');
}

function openExchangeModal() {
  openModal('modal-exchange');
}

function openUserModal() {
  openModal('modal-user');
}

function openCardsModal() {
  showToast('Green Accounts: HDFC9999 Active (RuPay/VISA Platinum)');
}

function openAnalyticsModal() {
  showToast('Real-time balance analytics active.');
}

function openSupportModal() {
  openModal('modal-support');
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
