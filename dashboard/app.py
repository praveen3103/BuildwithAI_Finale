import os
import time
import requests
import streamlit as st
import pandas as pd

# Set page configuration for a premium stadium console look
st.set_page_config(
    page_title="Stadium Crowd Command & Emergency Orchestration Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark premium styling overrides using vanilla CSS
st.markdown("""
<style>
    .reportview-container {
        background: #0d1117;
    }
    .main {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #8b949e !important;
        font-weight: 600;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #238636, #d29922, #f85149);
    }
    .stAlert {
        border-radius: 8px;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .glow-header {
        background: linear-gradient(135deg, #58a6ff, #bc8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    .log-console {
        background-color: #010409;
        font-family: 'Courier New', monospace;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #21262d;
        max-height: 250px;
        overflow-y: auto;
    }
    .agent-thought {
        background-color: #1f1b2c;
        border-left: 4px solid #bc8cff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .agent-action-box {
        background-color: #0e1626;
        border-left: 4px solid #58a6ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# In Cloud Run: FastAPI owns $PORT and Streamlit is internal.
# BACKEND_URL must point to the FastAPI port which equals the Cloud Run service port.
_port = os.environ.get("PORT", "8080")
BACKEND_URL = os.environ.get("BACKEND_URL", f"http://localhost:{_port}")


# Header Section
st.markdown("<h1>Stadium Crowd Command & Emergency Orchestrator</h1>", unsafe_allow_html=True)
st.markdown("##### <span class='glow-header'>Autonomous Crowd Risk Mitigation & Multi-Agent Tactical Response Engine</span>", unsafe_allow_html=True)
st.write("---")

# Fetch state data from FastAPI
@st.fragment
def load_data():
    try:
        response = requests.get(f"{BACKEND_URL}/api/dashboard/data", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback default local data if backend connection fails
    return {
        "gates": {
            "Gate 1": {"capacity": 5000, "crowd_count": 1200, "status": "OPEN"},
            "Gate 2": {"capacity": 4000, "crowd_count": 800, "status": "OPEN"},
            "Gate 3": {"capacity": 5000, "crowd_count": 1500, "status": "OPEN"},
            "Gate 4": {"capacity": 3000, "crowd_count": 500, "status": "OPEN"},
        },
        "weather": {"condition": "CLEAR", "severity": "LOW"},
        "emergency": {"active": False, "threat_level": "LOW", "location": "N/A"},
        "broadcasts": [],
        "agent_actions": []
    }

stadium_state = load_data()

# Layout Columns
col_controls, col_monitors, col_logs = st.columns([1.2, 1.8, 2.0])

# ==========================================
# COLUMN 1: OPERATOR SIMULATION CONTROLS
# ==========================================
with col_controls:
    st.markdown("### 🎛️ Tactical Control Console")
    
    # Reset System Button
    if st.button("🔄 Reset Stadium State Database", use_container_width=True):
        try:
            res = requests.post(f"{BACKEND_URL}/api/telemetry/reset")
            st.success("Stadium database reset successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to reset: {e}")
            
    st.write("---")
    
    # Telemetry Ingest Simulator Card
    with st.container(border=True):
        st.markdown("##### 🏟️ Telemetry Ingest Simulator")
        
        # Ingestion target selector
        telemetry_source = st.radio(
            "Telemetry Event Source",
            ["Gate Ingestion (Bottleneck Trigger)", "Weather Advisory", "Active Emergency Trigger"]
        )
        
        if telemetry_source == "Gate Ingestion (Bottleneck Trigger)":
            gate_id = st.selectbox("Target Gate", list(stadium_state["gates"].keys()))
            crowd_count = st.slider("Simulated Crowd Flow Influx", 0, 6000, 4800)
            gate_status = st.selectbox("Set Ingestion Status", ["OPEN", "CLOSED", "BOTTLENECK"])
            
            if st.button("🚀 Push Gate Ingest Payload", use_container_width=True):
                payload = {
                    "gate": {
                        "gate_id": gate_id,
                        "crowd_count": crowd_count,
                        "status": gate_status
                    }
                }
                with st.spinner("Executing agent reasoning loop..."):
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/telemetry", json=payload)
                        st.success("Telemetry ingested!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
        elif telemetry_source == "Weather Advisory":
            condition = st.selectbox("Condition Mode", ["CLEAR", "HEAVY_RAIN", "LIGHTNING_STRIKE", "HIGH_WINDS"])
            severity = st.selectbox("Severity Classification", ["LOW", "MEDIUM", "HIGH"])
            
            if st.button("🚀 Push Weather Ingest Payload", use_container_width=True):
                payload = {
                    "weather": {
                        "condition": condition,
                        "severity": severity
                    }
                }
                with st.spinner("Evaluating weather impact..."):
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/telemetry", json=payload)
                        st.success("Weather advisory published!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
        elif telemetry_source == "Active Emergency Trigger":
            location = st.text_input("Threat Location Zone", "Gate 3 Concourse")
            threat_level = st.selectbox("Critical Level", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            
            if st.button("🚨 TRIGGER EMERGENCY ACTION", use_container_width=True, type="primary"):
                payload = {
                    "emergency": {
                        "location": location,
                        "threat_level": threat_level
                    }
                }
                with st.spinner("DEPLOYING AUTOMATED RESPONSE ENGINE..."):
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/telemetry", json=payload)
                        st.success("Emergency protocols deployed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# COLUMN 2: REAL-TIME GATE & STATUS MONITOR
# ==========================================
with col_monitors:
    st.markdown("### 📊 Live Gates & Weather Status")
    
    # Weather Overview Card
    weather = stadium_state.get("weather", {"condition": "CLEAR", "severity": "LOW"})
    weather_sev = weather.get("severity")
    weather_cond = weather.get("condition")
    
    w_color = "#238636"
    if weather_sev == "HIGH":
        w_color = "#f85149"
    elif weather_sev == "MEDIUM":
        w_color = "#d29922"
        
    st.markdown(f"""
    <div style='background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 20px;'>
        <h6 style='color: #8b949e; margin: 0;'>🏟️ METEOROLOGICAL OVERVIEW</h6>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 8px;'>
            <span style='font-size: 24px; font-weight: bold;'>{weather_cond}</span>
            <span style='background-color: {w_color}; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white;'>
                {weather_sev} SEVERITY
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Gate Capacity Dashboard
    st.markdown("##### 🚪 Gate Ingress Capacity Monitor")
    
    gates = stadium_state.get("gates", {})
    for g_id, data in gates.items():
        cap = data["capacity"]
        cnt = data["crowd_count"]
        pct = cnt / cap
        status = data["status"]
        
        status_color = "#238636"
        if status == "BOTTLENECK":
            status_color = "#f85149"
        elif pct >= 0.8:
            status_color = "#d29922"
            
        with st.container(border=True):
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                st.markdown(f"**{g_id}** (Limit: {cap:,})")
                st.progress(min(pct, 1.0))
            with col_g2:
                st.markdown(f"<div style='text-align: right;'><span style='font-size: 20px; font-weight: bold; color: {status_color};'>{cnt:,}</span> <span style='font-size: 12px; color: #8b949e;'>({round(pct * 100, 1)}%)</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: right;'><span style='background-color: {status_color}33; color: {status_color}; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;'>{status}</span></div>", unsafe_allow_html=True)

# ==========================================
# COLUMN 3: BROADCASTS & AGENT TRACKER
# ==========================================
with col_logs:
    tab_agent, tab_broadcasts = st.tabs(["🤖 Agent Automated Actions Tracker", "📢 Emergency Broadcast Console"])
    
    # TAB 1: Agent automated action trace log
    with tab_agent:
        st.markdown("##### 🔍 Real-Time Multi-Agent Execution Trace")
        
        # Display the active emergency indicator
        em_state = stadium_state.get("emergency", {})
        if em_state.get("active", False):
            st.error(f"🚨 **ACTIVE CRITICAL CONGESTION & EMERGENCY TRIGGERED** at location: **{em_state.get('location')}**")
            
        actions = stadium_state.get("agent_actions", [])
        if not actions:
            st.info("No active agent orchestration traces logged yet. Push simulated telemetry in Column 1 to deploy the routing agent.")
        else:
            for act in reversed(actions):
                # 1. Thought/Reasoning Render Block
                with st.container():
                    st.markdown(f"""
                    <div class='agent-thought'>
                        <div style='font-size: 11px; color: #bc8cff; font-weight: bold;'>🤔 AGENT ORCHESTRATION THOUGHT PROCESS ({act.get('timestamp')})</div>
                        <div style='margin-top: 5px; font-size: 14px;'>{act.get('reasoning')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 2. Execution Block
                with st.container():
                    st.markdown(f"""
                    <div class='agent-action-box'>
                        <div style='font-size: 11px; color: #58a6ff; font-weight: bold;'>🛠️ LOGGED TRIGGER STEP: {act.get('step')}</div>
                        <div style='font-size: 12px; margin-top: 5px; color: #8b949e;'>Tool Invoked: <code>{act.get('tool_called')}</code></div>
                        <div style='margin-top: 8px; border-top: 1px dashed #30363d; padding-top: 8px;'>
                            <strong>Orchestrated Operational Mitigation Plan:</strong>
                            <p style='font-size: 13px; color: #e6edf3; white-space: pre-wrap; margin-top: 4px;'>{act.get('outcome')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
    # TAB 2: Emergency Broadcasts Log
    with tab_broadcasts:
        st.markdown("##### 📢 Stadium PA System & Display Channel Broadcast Logs")
        
        broadcasts = stadium_state.get("broadcasts", [])
        if not broadcasts:
            st.info("Public display channel clean. No emergency alerts actively broadcasting.")
        else:
            for bc in reversed(broadcasts):
                st.warning(f"📢 **Zone: {bc.get('zone')}** [{bc.get('timestamp')}]\n\n{bc.get('message')}")
                st.write("---")
