import json
from backend.state import get_stadium_data, add_broadcast, update_gate_state

def get_gate_status(gate_id: str) -> str:
    """Evaluates stadium gate crowd count and capacity thresholds.

    Args:
        gate_id: The ID of the gate to evaluate (e.g. "Gate 1", "Gate 2", "Gate 3", "Gate 4").
    
    Returns:
        A JSON string containing gate details, utilization percentage, and safety status.
    """
    state = get_stadium_data()
    gates = state["gates"]
    if gate_id not in gates:
        return json.dumps({"error": f"Gate {gate_id} not found. Available gates: {list(gates.keys())}"})
    
    gate = gates[gate_id]
    utilization = gate["crowd_count"] / gate["capacity"]
    
    status = "SAFE"
    if utilization >= 0.9:
        status = "CRITICAL_BOTTLENECK"
        # Auto-update status to BOTTLENECK in memory
        update_gate_state(gate_id, gate["crowd_count"], "BOTTLENECK")
    elif utilization >= 0.8:
        status = "WARNING_CONGESTION"
    
    result = {
        "gate_id": gate_id,
        "capacity": gate["capacity"],
        "crowd_count": gate["crowd_count"],
        "utilization_rate": round(utilization * 100, 2),
        "status": status,
        "raw_status": gate["status"]
    }
    return json.dumps(result)

def calculate_dynamic_routing(source_gate: str, bottleneck_score: float) -> str:
    """Evaluates and calculates alternative open pathways to redirect crowd flow from a bottleneck.

    Args:
        source_gate: The bottlenecked gate ID (e.g. "Gate 3").
        bottleneck_score: Numerical score indicating bottleneck severity (between 0.0 and 10.0).
        
    Returns:
        A JSON string recommendation details with redirect pathways and gate utilization rates.
    """
    state = get_stadium_data()
    gates = state["gates"]
    
    if source_gate not in gates:
        return json.dumps({"error": f"Source gate {source_gate} not found."})
        
    alternatives = []
    for g_id, data in gates.items():
        if g_id == source_gate:
            continue
        if data["status"] == "OPEN":
            utilization = data["crowd_count"] / data["capacity"]
            if utilization < 0.8:  # Recommend gates that aren't also congested
                alternatives.append({
                    "gate_id": g_id,
                    "utilization": round(utilization * 100, 2),
                    "available_headroom": data["capacity"] - data["crowd_count"]
                })
                
    # Sort alternatives by utilization (lowest first)
    alternatives.sort(key=lambda x: x["utilization"])
    
    if not alternatives:
        return json.dumps({
            "source_gate": source_gate,
            "status": "NO_SAFE_ALTERNATIVES",
            "message": "All alternative gates are currently bottlenecked or closed."
        })
        
    recommended_gate = alternatives[0]["gate_id"]
    result = {
        "source_gate": source_gate,
        "bottleneck_severity_score": bottleneck_score,
        "recommended_redirect_gate": recommended_gate,
        "alternative_pathways": alternatives,
        "message": f"Successfully calculated dynamic routing. Redirect crowd flow from {source_gate} to {recommended_gate}."
    }
    return json.dumps(result)

def trigger_emergency_broadcast(message: str, zone: str) -> str:
    """Automates and broadcasts emergency alerts to specific stadium zones or stadium-wide.

    Args:
        message: The warning/action alert message to broadcast.
        zone: Target zone or gate (e.g. "Gate 3", "South Stand", "STADIUM_WIDE").
        
    Returns:
        A JSON string confirming broadcast execution status.
    """
    add_broadcast(message, zone)
    result = {
        "status": "BROADCAST_SENT",
        "zone": zone,
        "broadcast_message": message,
        "details": f"Alert successfully transmitted to public display and audio channels in {zone}."
    }
    return json.dumps(result)
