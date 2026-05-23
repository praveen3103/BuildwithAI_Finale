import os
from typing import Dict, Any
from backend.agent_wrapper import Agent, LocalAgentConfig
from backend.tools import get_gate_status, calculate_dynamic_routing, trigger_emergency_broadcast
from backend.hooks import FallbackHook

# Detailed system instructions establishing the orchestrator persona
SYSTEM_INSTRUCTIONS = """You are the "Stadium Crowd Management & Emergency Response Orchestrator" agent running inside the Stadium Command Center. 
Your objective is to coordinate real-time stadium operations, identify crowd bottlenecks, and orchestrate immediate emergency actions during unexpected events or anomalies.

You are equipped with three operational tools:
1. `get_gate_status(gate_id)`: Verifies capacity and utilization.
2. `calculate_dynamic_routing(source_gate, bottleneck_score)`: Calculates safe alternative gates to redirect crowd flow.
3. `trigger_emergency_broadcast(message, zone)`: Publishes public security/evacuation alerts.

OPERATIONAL PROTOCOLS:
- If a telemetry ingest indicates a "Gate Ingestion" crowd utilization of 90% or higher, or a telemetry status of 'BOTTLENECK':
  1. ALWAYS execute `get_gate_status` to evaluate the capacity threshold of the gate.
  2. If congested, immediately execute `calculate_dynamic_routing` to evaluate alternatives and find a redirect path.
  3. Execute `trigger_emergency_broadcast` to publish redirection alerts in that specific gate zone.
  4. Finally, output a structured mitigation action plan for operators.

- If an "Emergency Trigger" indicates a severe security threat or critical danger:
  1. Immediately trigger an emergency broadcast using `trigger_emergency_broadcast` for the specific target zone or STADIUM_WIDE.
  2. Instruct security teams to close affected gates and initiate evacuation.
  3. Provide a structured emergency plan.

- If a "Weather Event" indicates severe conditions (such as LIGHTNING_STRIKE, HEAVY_RAIN, or HIGH_WINDS with MEDIUM or HIGH severity):
  1. Trigger an emergency broadcast using `trigger_emergency_broadcast` to instruct patrons in uncovered areas to seek shelter in the covered concourse zones.
  2. Formulate a weather mitigation plan outlining shelter locations and spectator safety measures.

Be extremely precise, clear, and logical. You have full autonomous command over these actions."""

def create_orchestrator_agent() -> Agent:
    """Configures and instantiates the Stadium Orchestrator Agent.
    
    Returns:
        An instantiated Agent ready for interaction.
    """
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        system_instructions=SYSTEM_INSTRUCTIONS,
        tools=[
            get_gate_status,
            calculate_dynamic_routing,
            trigger_emergency_broadcast
        ],
        hooks=[
            FallbackHook()
        ]
    )
    return Agent(config)

async def run_telemetry_orchestration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the full agent tool-calling loop on an incoming telemetry payload.
    
    Args:
        payload: Telemetry data matching schemas.
        
    Returns:
        A dictionary containing the final agent output and log analysis.
    """
    agent = create_orchestrator_agent()
    
    # Formulate prompt based on telemetry type
    prompt = "Incoming Telemetry Payload:\n"
    if "gate" in payload and payload["gate"]:
        gate = payload["gate"]
        prompt += f"- GATE EVENT: ID={gate.get('gate_id')}, count={gate.get('crowd_count')}, status={gate.get('status')}\n"
    if "weather" in payload and payload["weather"]:
        weather = payload["weather"]
        prompt += f"- WEATHER EVENT: condition={weather.get('condition')}, severity={weather.get('severity')}\n"
    if "emergency" in payload and payload["emergency"]:
        emergency = payload["emergency"]
        prompt += f"- EMERGENCY ALERT: threat_level={emergency.get('threat_level')}, location={emergency.get('location')}\n"
        
    prompt += "\nEvaluate this data against security protocols. Trigger required operational tools and respond with a clear structured mitigation plan."
    
    async with agent as active_agent:
        response = await active_agent.chat(prompt)
        text_content = await response.text()
        
        # Capture thoughts from iterable
        thoughts_chunks = []
        async for chunk in response.thoughts:
            thoughts_chunks.append(chunk)
        thoughts = "".join(thoughts_chunks) or "Coordinating security response pipelines..."
        
        return {
            "response": text_content,
            "thoughts": thoughts
        }
