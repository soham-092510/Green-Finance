/**
 * =====================================================================
 * GREEN FINANCE — SHARED UTILITIES
 * Common functions used by both Banking and Investigator apps
 * =====================================================================
 */

// API Base URL
const API_BASE = '';

// Global state management
const AppState = {
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  
  setAuth(token, refreshToken, user) {
    this.token = token;
    this.refreshToken = refreshToken;
    this.user = user;
    this.isAuthenticated = true;
    localStorage.setItem('gf_token', token);
    localStorage.setItem('gf_refresh_token', refreshToken);
    localStorage.setItem('gf_user', JSON.stringify(user));
  },
  
  clearAuth() {
    this.token = null;
    this.refreshToken = null;
    this.user = null;
    this.isAuthenticated = false;
    localStorage.removeItem('gf_token');
    localStorage.removeItem('gf_refresh_token');
    localStorage.removeItem('gf_user');
  },
  
  loadFromStorage() {
    const token = localStorage.getItem('gf_token');
    const refreshToken = localStorage.getItem('gf_refresh_token');
    const user = localStorage.getItem('gf_user');
    if (token && user) {
      this.token = token;
      this.refreshToken = refreshToken;
      this.user = JSON.parse(user);
      this.isAuthenticated = true;
      return true;
    }
    return false;
  },
  
  getAuthHeaders() {
    return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
  }
};

// API Request Helper
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...AppState.getAuthHeaders()
    }
  };
  
  const config = { ...defaultOptions, ...options };
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }
  
  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));
    
    if (response.status === 401 && AppState.refreshToken) {
      // Try to refresh token
      const refreshed = await refreshAuthToken();
      if (refreshed) {
        // Retry original request with new token
        config.headers = { ...config.headers, ...AppState.getAuthHeaders() };
        const retryResponse = await fetch(url, config);
        return await retryResponse.json();
      } else {
        AppState.clearAuth();
        window.location.href = '/bank/login';
        return null;
      }
    }
    
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

async function refreshAuthToken() {
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: AppState.refreshToken })
    });
    if (response.ok) {
      const data = await response.json();
      AppState.setAuth(data.access_token, data.refresh_token, AppState.user);
      return true;
    }
  } catch (e) {
    console.error('Token refresh failed:', e);
  }
  return false;
}

// Formatters
const Formatters = {
  currencyINR(amount, showSymbol = true) {
    const formatted = new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
    return showSymbol ? formatted : formatted.replace('₹', '').trim();
  },
  
  currencyCompact(amount) {
    if (amount >= 1e7) return `₹${(amount / 1e7).toFixed(1)} Cr`;
    if (amount >= 1e5) return `₹${(amount / 1e5).toFixed(1)} L`;
    if (amount >= 1e3) return `₹${(amount / 1e3).toFixed(1)} K`;
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  },
  
  number(value, decimals = 2) {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  },
  
  numberCompact(value) {
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toLocaleString('en-IN');
  },
  
  dateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    });
  },
  
  dateOnly(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  },
  
  timeOnly(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    });
  },
  
  relativeTime(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return this.dateOnly(dateStr);
  },
  
  energy(joules) {
    if (joules >= 1e6) return `${(joules / 1e6).toFixed(2)} MJ`;
    if (joules >= 1e3) return `${(joules / 1e3).toFixed(2)} kJ`;
    return `${joules.toFixed(4)} J`;
  },
  
  carbon(grams) {
    if (grams >= 1e3) return `${(grams / 1e3).toFixed(3)} kg CO₂`;
    if (grams >= 1) return `${grams.toFixed(3)} g CO₂`;
    return `${(grams * 1000).toFixed(2)} mg CO₂`;
  },
  
  carbonPerTx(grams) {
    return `${(grams * 1000).toFixed(3)} mg CO₂/tx`;
  },
  
  watts(watts) {
    if (watts >= 1e3) return `${(watts / 1e3).toFixed(2)} kW`;
    return `${watts.toFixed(2)} W`;
  },
  
  percentage(value, decimals = 1) {
    return `${value.toFixed(decimals)}%`;
  },
  
  truncate(str, length = 20) {
    if (!str) return '';
    return str.length > length ? str.slice(0, length) + '…' : str;
  }
};

// UI Helpers
const UI = {
  showNotification(title, message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = `alert-banner ${type} fade-in`;
    alert.innerHTML = `
      <div class="alert-icon">${this.getAlertIcon(type)}</div>
      <div class="alert-content">
        <strong>${this.escapeHtml(title)}</strong>
        <span>${this.escapeHtml(message)}</span>
      </div>
      <button class="alert-dismiss" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(alert);
    
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 300);
    }, duration);
  },
  
  getAlertIcon(type) {
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', danger: '❌' };
    return icons[type] || icons.info;
  },
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },
  
  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('hidden');
  },
  
  hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('hidden');
  },
  
  setLoading(element, loading) {
    if (!element) return;
    if (loading) {
      element.disabled = true;
      element.dataset.originalText = element.innerHTML;
      element.innerHTML = '<span class="spinner"></span> Loading...';
    } else {
      element.disabled = false;
      element.innerHTML = element.dataset.originalText || element.innerHTML;
    }
  },
  
  formatTelemetryMode(mode) {
    const modes = {
      'OBSERVED': { label: 'Observed', class: 'badge-success', icon: '📡' },
      'SIMULATED': { label: 'Simulated', class: 'badge-warning', icon: '🧪' },
      'CALCULATED': { label: 'Calculated', class: 'badge-info', icon: '🧮' }
    };
    const m = modes[mode] || modes['SIMULATED'];
    return `<span class="badge ${m.class}">${m.icon} ${m.label}</span>`;
  },
  
  createElement(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.firstElementChild;
  },
  
  renderTable(containerId, columns, data, rowRenderer) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!data || data.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📭</div>
          <div class="empty-state-title">No Data Available</div>
          <div class="empty-state-text">No records match your current filters.</div>
        </div>
      `;
      return;
    }
    
    let html = `
      <div class="table-responsive">
        <table class="table">
          <thead><tr>`;
    columns.forEach(col => {
      html += `<th${col.width ? ` style="width: ${col.width}"` : ''}>${col.header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    data.forEach(row => {
      html += '<tr>';
      if (rowRenderer) {
        html += rowRenderer(row);
      } else {
        columns.forEach(col => {
          const value = row[col.key];
          html += `<td${col.align ? ` style="text-align: ${col.align}"` : ''}>${this.escapeHtml(value ?? '')}</td>`;
        });
      }
      html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
  }
};

// Chart Helpers (using Chart.js)
const Charts = {
  instances: new Map(),
  
  create(ctx, config) {
    if (this.instances.has(ctx.canvas.id)) {
      this.instances.get(ctx.canvas.id).destroy();
    }
    const chart = new Chart(ctx, config);
    this.instances.set(ctx.canvas.id, chart);
    return chart;
  },
  
  destroy(canvasId) {
    const chart = this.instances.get(canvasId);
    if (chart) { chart.destroy(); this.instances.delete(canvasId); }
  },
  
  destroyAll() {
    this.instances.forEach(chart => chart.destroy());
    this.instances.clear();
  },
  
  getDefaultOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { usePointStyle: true, padding: 16, font: { size: 11, family: 'Inter' } }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleFont: { size: 12, family: 'Inter', weight: '600' },
          bodyFont: { size: 11, family: 'Inter' },
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          boxPadding: 6
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: '#94a3b8', font: { size: 10, family: 'Inter' } }
        },
        y: {
          grid: { color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: '#94a3b8', font: { size: 10, family: 'Inter' } }
        }
      },
      animation: { duration: 300, easing: 'easeOutQuart' }
    };
  },
  
  getColors() {
    return {
      primary: '#059669', primaryLight: 'rgba(5, 150, 105, 0.1)',
      blue: '#2563eb', blueLight: 'rgba(37, 99, 235, 0.1)',
      purple: '#7c3aed', purpleLight: 'rgba(124, 58, 237, 0.1)',
      amber: '#d97706', amberLight: 'rgba(217, 119, 6, 0.1)',
      rose: '#e11d48', roseLight: 'rgba(225, 29, 72, 0.1)',
      cyan: '#0891b2', cyanLight: 'rgba(8, 145, 178, 0.1)',
      gray: '#64748b', grayLight: 'rgba(100, 116, 139, 0.1)'
    };
  }
};

// WebSocket for real-time updates (optional)
class RealtimeClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
  }
  
  connect(url, handlers = {}) {
    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        handlers.onOpen?.();
      };
      this.ws.onmessage = (event) => {
        try { handlers.onMessage?.(JSON.parse(event.data)); }
        catch (e) { handlers.onMessage?.(event.data); }
      };
      this.ws.onclose = () => this.handleReconnect(url, handlers);
      this.ws.onerror = (err) => handlers.onError?.(err);
    } catch (e) { console.error('WebSocket connection failed:', e); }
  }
  
  handleReconnect(url, handlers) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(url, handlers), this.reconnectDelay * this.reconnectAttempts);
    }
  }
  
  send(data) { if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(data)); }
  disconnect() { if (this.ws) { this.ws.close(); this.ws = null; } }
}

// Export for module usage
window.AppState = AppState;
window.apiRequest = apiRequest;
window.Formatters = Formatters;
window.UI = UI;
window.Charts = Charts;
window.RealtimeClient = RealtimeClient;