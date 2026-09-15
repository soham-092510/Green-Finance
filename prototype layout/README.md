# 🌱 Green-Finance | Eco-Monitor Phase 2 Prototype

A modern, clean **white-theme** frontend layout designed for **Phase 2 Presentation & Evaluation**, adhering to the IEEE 830 Software Requirements Specification (SRS).

---

## 🎯 Phase 2 Objectives Implemented

As specified in the project SRS:
1. **RF01 & RF02: Simulated Banking Layer & Swagger UI**
   - Authenticated user session with registered Bank ID (`HDFC9999`).
   - Transfer money with user control over transfer amounts (₹ INR) to other authenticated recipient Bank IDs (e.g. `MAH123`, `IDF892`, `SBIN456`, `AXIS777`).
   - Interactive Swagger UI simulator testing `POST /auth/login`, `POST /payment/transfer`, `GET /telemetry/realtime`, and `GET /metrics`.
2. **RF03, RF04 & RF05: PromQL & Carbon-per-Transaction Derivation**
   - Live PromQL console with pre-configured IEEE SRS queries:
     $$\text{Carbon-per-Transaction} = \frac{\text{Container Energy (Joules)} \times \text{Regional Factor}}{\text{Transaction Count}}$$
   - Real-time evaluation time series and JSON metric vector responses.
3. **RF06: Grafana Observability Dashboard**
   - 4-panel observability view:
     - Panel 1: Carbon-per-Transaction over time with live baseline.
     - Panel 2: Microservice energy rate (Watts) attributed per container (`payment-service` vs `auth-service`).
     - Panel 3: Request throughput (req/s) and latency distribution.
     - Panel 4: Energy Hotspot Ranking table with ESG ratings.
   - Time-range selector (5m, 15m, 1h, 24h) and auto-refresh controls.
4. **RF07: High Emission Alerting**
   - Automated threshold alerts when a transaction's carbon intensity exceeds safety limits.
5. **Double-Entry Financial & Carbon Ledger**
   - Atomic balancing ledger verifying $\text{Debits} = \text{Credits}$ for every transfer, tracking energy in Joules and carbon footprint in grams of $\text{CO}_2$.

---

## 🚀 How to Run Locally (Localhost Only Required)

You can launch this prototype with any local HTTP server:

### Option 1: Python Built-in Server (Recommended)
Navigate to this folder and run:
```bash
# From workspace root:
cd "prototype layout"
python -m http.server 8085
```
Open your browser at:
👉 **[http://localhost:8085](http://localhost:8085)**

### Option 2: Open Directly in Browser
You can also directly double-click or open `index.html` in Chrome, Edge, or Firefox.

---

## 👥 Project Team (SPIT TE Sem V)
- **Soham Haridas Gaikwad** (UID: 2024800030) — Backend, Monitoring Stack & DevOps
- **Atharva Pramod Hule** (UID: 2024800038) — Frontend Dashboard & System Documentation
- **Laukik Vidyadhar Deshpande** (UID: 2024800023) — Testing, Carbon-Factor Research & Report Generation
