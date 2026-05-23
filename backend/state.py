import time
from typing import Dict, List, Any

# In-memory database for stadium state
STADIUM_STATE = {
    "gates": {
        "Gate 1": {"capacity": 5000, "crowd_count": 1200, "status": "OPEN"},
        "Gate 2": {"capacity": 4000, "crowd_count": 800, "status": "OPEN"},
        "Gate 3": {"capacity": 5000, "crowd_count": 1500, "status": "OPEN"},
        "Gate 4": {"capacity": 3000, "crowd_count": 500, "status": "OPEN"},
    },
    "weather": {
        "condition": "CLEAR",
        "severity": "LOW"
    },
    "emergency": {
        "active": False,
        "threat_level": "LOW",
        "location": "N/A",
        "timestamp": None
    },
    "broadcasts": [],
    "agent_actions": [],  # Store the choices, reasoning chains, and executed tools of the running model
}

def get_stadium_data() -> Dict[str, Any]:
    return STADIUM_STATE

def update_gate_state(gate_id: str, crowd_count: int, status: str):
    if gate_id not in STADIUM_STATE["gates"]:
        # Initialize a default capacity if new gate
        STADIUM_STATE["gates"][gate_id] = {"capacity": 5000, "crowd_count": crowd_count, "status": status}
    else:
        STADIUM_STATE["gates"][gate_id]["crowd_count"] = crowd_count
        STADIUM_STATE["gates"][gate_id]["status"] = status

def update_weather_state(condition: str, severity: str):
    STADIUM_STATE["weather"]["condition"] = condition
    STADIUM_STATE["weather"]["severity"] = severity

def update_emergency_state(active: bool, threat_level: str, location: str):
    STADIUM_STATE["emergency"] = {
        "active": active,
        "threat_level": threat_level,
        "location": location,
        "timestamp": time.time()
    }

def add_broadcast(message: str, zone: str):
    STADIUM_STATE["broadcasts"].append({
        "message": message,
        "zone": zone,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

def log_agent_action(step: str, reasoning: str, tool_called: str, outcome: str):
    STADIUM_STATE["agent_actions"].append({
        "step": step,
        "reasoning": reasoning,
        "tool_called": tool_called,
        "outcome": outcome,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
