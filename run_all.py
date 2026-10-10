"""
Green Finance - Unified Enterprise Ecosystem Launcher
Launches:
- Unified Green Finance Ecosystem on http://localhost:8000
  * Gateway Hub:                      http://localhost:8000/
  * Banking Application:              http://localhost:8000/bank
  * Sustainability Investigator:      http://localhost:8000/investigator
  * Interactive API Docs:             http://localhost:8000/docs
  * Prometheus Metrics:               http://localhost:8000/metrics
- Also mirrors on port 8001 for compatibility with old links
"""

import os
import sys
import time
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Support running from inside Green-Finance or parent folder
GF1_DIR = ROOT_DIR if os.path.exists(os.path.join(ROOT_DIR, "backend")) else os.path.join(ROOT_DIR, "Green-Finance")

gf_python = os.path.join(GF1_DIR, "venv", "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(GF1_DIR, "venv", "bin", "python")
if not os.path.exists(gf_python):
    gf_python = sys.executable

print("=" * 75)
print("  🌱 GREEN FINANCE - UNIFIED ECOSYSTEM LAUNCHER")
print("=" * 75)
print("  Gateway Hub & Overview:             http://localhost:8000/")
print("  🏛️ Banking Application (INR):        http://localhost:8000/bank")
print("  🌱 Sustainability Investigator:     http://localhost:8000/investigator")
print("  📑 Interactive API Docs (OpenAPI):  http://localhost:8000/docs")
print("  📈 Prometheus Metrics:              http://localhost:8000/metrics")
print("  Compatibility Bank Port (:8001):   http://localhost:8001/bank")
print("=" * 75)

# Launch Primary Platform on Port 8000
p1 = subprocess.Popen(
    [gf_python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
    cwd=GF1_DIR
)
time.sleep(2)

# Launch Compatibility Platform on Port 8001
p2 = subprocess.Popen(
    [gf_python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"],
    cwd=GF1_DIR
)

print("\nAll services are running. Press Ctrl+C to terminate both servers.\n")

try:
    p1.wait()
    p2.wait()
except KeyboardInterrupt:
    print("\nShutting down servers...")
    p1.terminate()
    p2.terminate()
    p1.wait()
    p2.wait()
