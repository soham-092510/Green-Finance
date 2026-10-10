# =====================================================================
# GREEN-FINANCE — TELEMETRY_SERVICE.PY (PROMETHEUS & KEPLER TELEMETRY)
# =====================================================================
# Purpose: Connects to Prometheus, queries Kepler energy metrics via PromQL,
#          translates electricity consumption into carbon footprint estimates.
#          Maintains explicit telemetry source labeling: OBSERVED | SIMULATED | CALCULATED
# =====================================================================

import urllib.request
import urllib.parse
import json
import random
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.middleware.logger import logger
from backend.services import carbon_service, accuracy_service


TELEMETRY_MODE = "SIMULATED"  # OBSERVED | SIMULATED | CALCULATED
KEPLER_AVAILABLE = False  # Set to True when Kepler RAPL counters are accessible


def query_prometheus(query: str) -> Optional[Dict]:
    """Query Prometheus and return parsed JSON response."""
    try:
        encoded_query = urllib.parse.urlencode({"query": query})
        url = f"{settings.prometheus_url}/api/v1/query?{encoded_query}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as err:
        logger.error(f"Failed to query Prometheus: {str(err)} (Query: {query})")
    return None


def extract_single_value(response: Optional[Dict]) -> float:
    """Extract single numeric value from Prometheus response."""
    if response and response.get("status") == "success":
        results = response.get("data", {}).get("result", [])
        if results:
            val_str = results[0].get("value", [0, "0"])[1]
            return float(val_str)
    return 0.0


def extract_labeled_values(response: Optional[Dict], label_key: str) -> List[Dict]:
    """Extract labeled values from Prometheus response."""
    output = []
    if response and response.get("status") == "success":
        results = response.get("data", {}).get("result", [])
        for r in results:
            metric = r.get("metric", {})
            name = metric.get(label_key, "unknown")
            val_str = r.get("value", [0, "0"])[1]
            output.append({"name": name, "value": float(val_str)})
    return output


def check_kepler_availability() -> bool:
    """Check if Kepler metrics are available (non-zero)."""
    global KEPLER_AVAILABLE
    try:
        resp = query_prometheus("sum(rate(kepler_container_joules_total[1m]))")
        val = extract_single_value(resp)
        KEPLER_AVAILABLE = val > 0.0
        return KEPLER_AVAILABLE
    except Exception:
        KEPLER_AVAILABLE = False
        return False


def get_telemetry_mode() -> str:
    """Return current telemetry mode with availability context."""
    if KEPLER_AVAILABLE:
        return "OBSERVED"
    return "SIMULATED"


def get_realtime_metrics() -> Dict:
    """Get real-time energy metrics with explicit telemetry labeling."""
    global KEPLER_AVAILABLE
    
    # Try to get real Kepler metrics
    platform_power_resp = query_prometheus("sum(rate(kepler_node_platform_joules_total[1m]))")
    platform_power = extract_single_value(platform_power_resp)
    
    container_power_resp = query_prometheus("sum(rate(kepler_container_joules_total[1m]))")
    container_power = extract_single_value(container_power_resp)
    
    container_breakdown_resp = query_prometheus(
        'sum(rate(kepler_container_joules_total{container_name!=""}[1m])) by (container_name)'
    )
    container_breakdown = extract_labeled_values(container_breakdown_resp, "container_name")
    
    # Determine telemetry mode
    telemetry_mode = get_telemetry_mode()
    
    # Fallback to simulated if Kepler unavailable
    if platform_power <= 0.0 or container_power <= 0.0:
        telemetry_mode = "SIMULATED"
        raw_host = random.uniform(70.0, 75.0)
        raw_containers = random.uniform(48.0, 52.0)
        raw_idle = random.uniform(18.2, 19.1)
        telemetry_ema = accuracy_service.update_realtime_power_telemetry(raw_host, raw_containers, raw_idle)
        
        platform_power = telemetry_ema["host_power_watts_ema"]
        container_power = telemetry_ema["container_power_watts_ema"]
        idle_power = telemetry_ema["idle_power_watts_ema"]
        residual_power = telemetry_ema["residual_watts"]
        fidelity_pct = telemetry_ema["fidelity_percent"]
        
        container_breakdown = [
            {"name": "payment-service", "value": round(container_power * 0.68, 2)},
            {"name": "auth-service", "value": round(container_power * 0.22, 2)},
            {"name": "ledger-service", "value": round(container_power * 0.10, 2)}
        ]
    else:
        idle_power = 18.7
        residual_power = max(0.0, platform_power - (container_power + idle_power))
        fidelity_pct = round((1.0 - (residual_power / platform_power)) * 100.0, 1) if platform_power > 0 else 95.0
    
    carbon_rate_hour = container_power * 0.001 * 0.38
    
    return {
        "platform_power_watts": round(platform_power, 2),
        "container_power_watts": round(container_power, 2),
        "idle_power_watts": round(idle_power, 2),
        "residual_power_watts": round(residual_power, 2),
        "attribution_fidelity_percent": round(fidelity_pct, 1),
        "container_breakdown_watts": [
            {"name": c["name"], "watts": round(c.get("value", c.get("watts", 0.0)), 2)} for c in container_breakdown
        ],
        "carbon_emission_rate_kg_per_hour": round(carbon_rate_hour, 5),
        "status": "HEALTHY",
        "telemetry_mode": telemetry_mode,
        "kepler_available": KEPLER_AVAILABLE,
        "measurement_note": "Physical RAPL counters unavailable in Docker Desktop/WSL2. Using high-fidelity simulated telemetry." if telemetry_mode == "SIMULATED" else "Kepler eBPF RAPL counters active."
    }


def get_historical_metrics(range_str: str = "1h") -> Dict:
    """Get historical energy metrics with telemetry labeling."""
    telemetry_mode = get_telemetry_mode()
    
    energy_resp = query_prometheus(f"sum(increase(kepler_container_joules_total[{range_str}]))")
    energy_joules = extract_single_value(energy_resp)
    energy_kwh = energy_joules / 3600000.0
    carbon_emissions = energy_kwh * 0.38
    
    breakdown_resp = query_prometheus(
        f'sum(increase(kepler_container_joules_total{{container_name!=""}}[{range_str}])) by (container_name)'
    )
    breakdown_joules = extract_labeled_values(breakdown_resp, "container_name")
    
    container_stats = []
    for c in breakdown_joules:
        c_kwh = c["value"] / 3600000.0
        container_stats.append({
            "container_name": c["name"],
            "energy_kwh": round(c_kwh, 4),
            "carbon_kg": round(c_kwh * 0.38, 4)
        })
    
    return {
        "range": range_str,
        "total_energy_kwh": round(energy_kwh, 4),
        "total_carbon_kg": round(carbon_emissions, 4),
        "containers": container_stats,
        "telemetry_mode": telemetry_mode,
        "kepler_available": KEPLER_AVAILABLE
    }


def calculate_transaction_carbon(energy_joules: float, factor_gco2_per_kwh: float = 713.0) -> Dict:
    """Calculate carbon from energy with explicit labeling."""
    energy_kwh = energy_joules / 3600000.0
    carbon_grams = energy_kwh * factor_gco2_per_kwh
    carbon_mg = carbon_grams * 1000.0
    
    return {
        "energy_joules": round(energy_joules, 4),
        "energy_kwh": round(energy_kwh, 9),
        "carbon_grams": round(carbon_grams, 6),
        "carbon_mg": round(carbon_mg, 3),
        "factor_used_gco2_per_kwh": factor_gco2_per_kwh,
        "calculation_type": "CALCULATED",
        "formula": "CO2_g = (Energy_J / 3,600,000) * Factor_gCO2_per_kWh",
        "telemetry_mode": get_telemetry_mode()
    }


def log_telemetry_emissions(db: Session, user_id: str, range_str: str = "1h") -> Optional[Dict]:
    """Log emissions with telemetry mode tracking."""
    stats = get_historical_metrics(range_str=range_str)
    kwh = stats["total_energy_kwh"]
    carbon_kg = stats["total_carbon_kg"]
    telemetry_mode = stats["telemetry_mode"]
    
    if kwh <= 0:
        logger.warning(f"Telemetry query returned 0 kWh ({telemetry_mode}); skipping emission auto-logging.")
        return None
    
    description = f"Auto-logged server footprint ({range_str} telemetry, {telemetry_mode}): {round(kwh, 3)} kWh energy"
    
    record = carbon_service.log_emission(
        db=db,
        user_id=user_id,
        activity_type="energy",
        metric_value=kwh,
        description=description
    )
    
    return {
        "carbon_record_id": record.id,
        "energy_kwh": round(kwh, 4),
        "carbon_logged_kg": round(carbon_kg, 4),
        "description": description,
        "telemetry_mode": telemetry_mode
    }