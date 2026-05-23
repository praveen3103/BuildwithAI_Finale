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

def generate_stadium_svg(stadium_state):
    gates = stadium_state.get("gates", {})
    
    # Map gates to coordinates
    gate_coords = {
        "Gate 1": {"node": (200, 30), "align": "middle"},
        "Gate 2": {"node": (370, 150), "align": "end"},
        "Gate 3": {"node": (200, 270), "align": "middle"},
        "Gate 4": {"node": (30, 150), "align": "start"}
    }
    
    svg_elements = []
    
    # SVG Definition & Styles
    svg_elements.append("""
    <svg viewBox="0 0 400 300" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="background-color: #0b0f19; border-radius: 12px; border: 1px solid #1f2937; box-shadow: inset 0 0 20px rgba(0,0,0,0.6); margin-bottom: 20px;">
      <defs>
        <!-- Gradients -->
        <radialGradient id="fieldGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#14532d" stop-opacity="0.9"/>
          <stop offset="100%" stop-color="#0f2d1a" stop-opacity="0.9"/>
        </radialGradient>
        <radialGradient id="stadiumGlow" cx="50%" cy="50%" r="60%">
          <stop offset="70%" stop-color="#111827" stop-opacity="0"/>
          <stop offset="100%" stop-color="#030712" stop-opacity="0.8"/>
        </radialGradient>
        <!-- Glow filters -->
        <filter id="glow-red" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="glow-amber" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="glow-green" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      
      <style>
        @keyframes pulse {
          0% { r: 10px; opacity: 1; }
          50% { r: 16px; opacity: 0.5; }
          100% { r: 10px; opacity: 1; }
        }
        .pulse-effect {
          animation: pulse 1.8s infinite ease-in-out;
        }
        .gate-title {
          font-family: 'Inter', sans-serif;
          font-weight: 700;
          font-size: 10px;
          fill: #9ca3af;
        }
        .gate-value {
          font-family: 'Inter', sans-serif;
          font-weight: 700;
          font-size: 12px;
          fill: #f3f4f6;
        }
        .gate-percent {
          font-family: 'Inter', sans-serif;
          font-size: 9px;
        }
        .stadium-label {
          font-family: 'Outfit', 'Inter', sans-serif;
          font-weight: 800;
          font-size: 11px;
          fill: #4b5563;
          letter-spacing: 2px;
        }
      </style>
      
      <!-- Outer Stadium Structure -->
      <ellipse cx="200" cy="150" rx="175" ry="115" fill="none" stroke="#1f2937" stroke-width="6" />
      <ellipse cx="200" cy="150" rx="175" ry="115" fill="url(#stadiumGlow)" />
      
      <!-- Stand Seating Tiers (Visual Accent Lines) -->
      <ellipse cx="200" cy="150" rx="160" ry="102" fill="none" stroke="#111827" stroke-width="1.5" stroke-dasharray="8 6" />
      <ellipse cx="200" cy="150" rx="150" ry="92" fill="none" stroke="#1f2937" stroke-width="1" />
      
      <!-- Cricket Field (Outfield) -->
      <ellipse cx="200" cy="150" rx="130" ry="78" fill="url(#fieldGlow)" stroke="#22c55e" stroke-width="2" stroke-opacity="0.3" />
      
      <!-- Wickets & Pitch Boundary (Inner Ring) -->
      <ellipse cx="200" cy="150" rx="90" ry="50" fill="none" stroke="#22c55e" stroke-width="1" stroke-opacity="0.15" stroke-dasharray="4 4" />
      
      <!-- Cricket Pitch -->
      <rect x="193" y="132" width="14" height="36" rx="1" fill="#b45309" fill-opacity="0.75" stroke="#d97706" stroke-width="0.75" />
      <!-- Crease/Wicket markings -->
      <line x1="193" y1="136" x2="207" y2="136" stroke="#fef08a" stroke-width="0.75" opacity="0.6" />
      <line x1="193" y1="164" x2="207" y2="164" stroke="#fef08a" stroke-width="0.75" opacity="0.6" />
      
      <!-- Stadium Label -->
      <text x="200" y="105" text-anchor="middle" class="stadium-label">CRICKET ARENA</text>
    """)
    
    # Render Gates and labels dynamically
    for g_id, data in gates.items():
        cap = data["capacity"]
        cnt = data["crowd_count"]
        pct = cnt / cap
        status = data["status"]
        
        # Determine status colors and classes
        if status == "BOTTLENECK" or pct >= 0.95:
            color = "#ef4444"
            glow_filter = "url(#glow-red)"
            pulse_class = "pulse-effect"
            pct_color = "#f87171"
        elif pct >= 0.8:
            color = "#f59e0b"
            glow_filter = "url(#glow-amber)"
            pulse_class = ""
            pct_color = "#fbbf24"
        else:
            color = "#10b981"
            glow_filter = "url(#glow-green)"
            pulse_class = ""
            pct_color = "#34d399"
            
        coords = gate_coords.get(g_id)
        if not coords:
            continue
            
        nx, ny = coords["node"]
        align = coords["align"]
        
        # 1. Draw glowing pulser if bottlenecked
        if pulse_class:
            svg_elements.append(f"""
            <circle cx="{nx}" cy="{ny}" r="15" fill="{color}" fill-opacity="0.3" class="{pulse_class}" />
            """)
            
        # 2. Draw Main Gate Node Circle
        svg_elements.append(f"""
        <circle cx="{nx}" cy="{ny}" r="10" fill="{color}" stroke="#ffffff" stroke-width="1.5" filter="{glow_filter}" style="cursor: pointer;" />
        <text x="{nx}" y="{ny + 3}" text-anchor="middle" fill="#ffffff" font-family="'Inter', sans-serif" font-weight="900" font-size="8px" style="pointer-events: none;">{g_id[-1]}</text>
        """)
        
        # 3. Draw Info Panel (Text Block) near the gate node
        anchor = "middle" if align == "middle" else ("end" if align == "end" else "start")
        dx = 0 if align == "middle" else (14 if align == "start" else -14)
        dy = 22 if g_id == "Gate 1" else (-15 if g_id == "Gate 3" else 4)
        
        tx = nx + dx
        ty = ny + dy
        
        svg_elements.append(f"""
        <g>
          <!-- Small shadow behind labels -->
          <text x="{tx}" y="{ty}" text-anchor="{anchor}" class="gate-title" stroke="#0b0f19" stroke-width="3" paint-order="stroke">{g_id.upper()}</text>
          <text x="{tx}" y="{ty}" text-anchor="{anchor}" class="gate-title">{g_id.upper()}</text>
          
          <text x="{tx}" y="{ty + 12}" text-anchor="{anchor}" class="gate-value" stroke="#0b0f19" stroke-width="3" paint-order="stroke">{cnt:,} / {cap:,}</text>
          <text x="{tx}" y="{ty + 12}" text-anchor="{anchor}" class="gate-value">{cnt:,} <tspan class="gate-percent" fill="{pct_color}">({round(pct * 100, 1)}%)</tspan></text>
        </g>
        """)
        
    svg_elements.append("</svg>")
    return "\n".join(svg_elements)

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
    
    # Stadium Visual Map
    st.markdown("##### 🗺️ Dynamic Visual Stadium Map")
    st.markdown(generate_stadium_svg(stadium_state), unsafe_allow_html=True)
    
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
