import os
import sys
import logging
import asyncio
import httpx
import websockets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from backend.schemas import TelemetryPayload, GateTelemetry, WeatherTelemetry, EmergencyTelemetry
from backend.state import (
    get_stadium_data, 
    update_gate_state, 
    update_weather_state, 
    update_emergency_state, 
    log_agent_action,
    STADIUM_STATE
)
from backend.agent import run_telemetry_orchestration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stadium_backend")

# Internal Streamlit port (background process)
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))
STREAMLIT_BASE = f"http://127.0.0.1:{STREAMLIT_PORT}"


app = FastAPI(
    title="Stadium Crowd Management & Emergency Response Orchestrator API",
    version="1.0.0",
    description="Production-grade FastAPI server for stadium command center automation."
)

@app.get("/api/health")
async def root():
    return {
        "status": "ONLINE",
        "service": "Stadium Crowd Management & Emergency Response Orchestrator Backend",
        "project": "Vertex AI & Antigravity SDK Integration"
    }

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Exposes the full in-memory stadium operational database to the Streamlit UI."""
    return get_stadium_data()

@app.post("/api/telemetry")
async def ingest_telemetry(payload: TelemetryPayload):
    """Ingests multi-source simulated telemetry, validates data, and runs agent orchestration."""
    logger.info(f"Ingested telemetry payload: {payload}")
    
    # 1. Parse and update in-memory state based on ingested sources
    if payload.gate:
        # Update our central gate state
        update_gate_state(
            gate_id=payload.gate.gate_id,
            crowd_count=payload.gate.crowd_count,
            status=payload.gate.status
        )
        logger.info(f"Updated gate state for {payload.gate.gate_id}")
        
    if payload.weather:
        update_weather_state(
            condition=payload.weather.condition,
            severity=payload.weather.severity
        )
        logger.info(f"Updated weather state: {payload.weather.condition}")
        
    if payload.emergency:
        is_active = payload.emergency.threat_level.upper() in {"HIGH", "CRITICAL"}
        update_emergency_state(
            active=is_active,
            threat_level=payload.emergency.threat_level,
            location=payload.emergency.location
        )
        logger.info(f"Updated emergency threat state at {payload.emergency.location}")

    # 2. Trigger the autonomous agent coordination response
    try:
        raw_payload = payload.model_dump()
        result = await run_telemetry_orchestration(raw_payload)
        
        # Log the agent action details centrally for dashboard visual tracking
        log_agent_action(
            step="Telemetry Ingestion Action",
            reasoning=result.get("thoughts", "Coordinating stadium systems response..."),
            tool_called="Agent Reasoning Loop",
            outcome=result.get("response", "No mitigation plan issued.")
        )
        
        return {
            "status": "PROCESSED",
            "message": "Telemetry received and agent pipeline completed.",
            "agent_response": result.get("response"),
            "agent_thoughts": result.get("thoughts")
        }
    except Exception as e:
        logger.error(f"Failed during agent response orchestration: {e}")
        
        # Deploy hardcoded stadium safety fallback rules if AI is offline
        reasoning = f"AI orchestrator offline ({str(e)}). Deploying automated stadium safety fallback rule engine."
        outcome = ""
        
        from backend.tools import get_gate_status, calculate_dynamic_routing, trigger_emergency_broadcast
        import json
        
        if payload.gate and (payload.gate.status == "BOTTLENECK" or payload.gate.crowd_count >= 4000):
            # Run tools directly to preserve safety
            get_gate_status(payload.gate.gate_id)
            routing = calculate_dynamic_routing(payload.gate.gate_id, 9.0)
            r_data = json.loads(routing)
            alt_gate = r_data.get("recommended_redirect_gate", "Gate 1")
            
            msg = f"ATTENTION CONGESTION: Crowd bottleneck at {payload.gate.gate_id}. Please redirect to open pathways at {alt_gate}."
            trigger_emergency_broadcast(msg, payload.gate.gate_id)
            
            outcome = (
                f"FALLBACK ROUTING ACTIVE:\n"
                f"- Gate status confirmed bottlenecked.\n"
                f"- Calculated alternative open pathway: Redirect crowd flow to {alt_gate}.\n"
                f"- Public announcement broadcasted to target zone {payload.gate.gate_id}."
            )
            
        elif payload.emergency and payload.emergency.threat_level.upper() in {"HIGH", "CRITICAL"}:
            msg = f"EMERGENCY EVACUATION: Active threat at {payload.emergency.location}. Initiate emergency evacuation!"
            trigger_emergency_broadcast(msg, "STADIUM_WIDE")
            outcome = f"FALLBACK EMERGENCY SYSTEM ACTIVE:\n- Triggered STADIUM_WIDE emergency alert for active threat at {payload.emergency.location}."
            
        elif payload.weather and payload.weather.severity.upper() in {"MEDIUM", "HIGH"}:
            msg = f"WEATHER ALERT: Severe {payload.weather.condition} detected. Patrons in open zones please move to covered stadium concourses."
            trigger_emergency_broadcast(msg, "STADIUM_WIDE")
            outcome = f"FALLBACK WEATHER SAFETY PROTOCOL ACTIVE:\n- Triggered STADIUM_WIDE safety announcement for severe weather condition: {payload.weather.condition}."
            
        log_agent_action(
            step="Safety System Fallback Protocol Deployed",
            reasoning=reasoning,
            tool_called="Hardcoded Safety Engine",
            outcome=outcome or f"Telemetry ingested. AI agent connection error: {str(e)}"
        )
        
        return {
            "status": "PARTIAL_SUCCESS",
            "message": "Telemetry saved locally and safety fallback rules successfully deployed.",
            "error": str(e),
            "fallback_outcome": outcome
        }

@app.post("/api/telemetry/reset")
async def reset_telemetry():
    """Resets the stadium dashboard to safe, default values for operational demos."""
    STADIUM_STATE["gates"] = {
        "Gate 1": {"capacity": 5000, "crowd_count": 1200, "status": "OPEN"},
        "Gate 2": {"capacity": 4000, "crowd_count": 800, "status": "OPEN"},
        "Gate 3": {"capacity": 5000, "crowd_count": 1500, "status": "OPEN"},
        "Gate 4": {"capacity": 3000, "crowd_count": 500, "status": "OPEN"},
    }
    STADIUM_STATE["weather"] = {
        "condition": "CLEAR",
        "severity": "LOW"
    }
    STADIUM_STATE["emergency"] = {
        "active": False,
        "threat_level": "LOW",
        "location": "N/A",
        "timestamp": None
    }
    STADIUM_STATE["broadcasts"] = []
    STADIUM_STATE["agent_actions"] = []
    logger.info("Stadium center database reset successfully.")
    return {"status": "RESET", "message": "Stadium center database successfully restored to default open states."}

# ─── Streamlit Reverse Proxy ───────────────────────────────────────────────
# Forwards all non-/api requests to the internal Streamlit process (port 8501)
# so Cloud Run only needs to expose a single port.

@app.websocket("/_stcore/stream")
@app.websocket("/stream")
async def websocket_proxy(websocket: WebSocket):
    """Proxies WebSocket connections to the internal Streamlit process."""
    query_string = str(websocket.query_params)
    target_url = f"ws://127.0.0.1:{STREAMLIT_PORT}/_stcore/stream"
    if query_string:
        target_url += f"?{query_string}"
    
    logger.info(f"Proxying WebSocket to Streamlit: {target_url}")
    
    # Parse subprotocols from client
    client_subprotocol = websocket.headers.get("sec-websocket-protocol")
    subprotocols = []
    if client_subprotocol:
        subprotocols = [s.strip() for s in client_subprotocol.split(",")]

    # Forward other headers
    headers = {}
    for k, v in websocket.headers.items():
        if k.lower() in {"user-agent", "cookie", "x-forwarded-for", "x-forwarded-proto"}:
            headers[k] = v

    try:
        async with websockets.connect(target_url, additional_headers=headers, subprotocols=subprotocols) as target_ws:
            logger.info(f"Connected to Streamlit. Negotiated subprotocol: {target_ws.subprotocol}")
            
            # Accept the client's WebSocket connection using the negotiated subprotocol
            await websocket.accept(subprotocol=target_ws.subprotocol)
            logger.info("Successfully accepted client WebSocket connection")
            
            async def forward_client_to_target():
                try:
                    while True:
                        data = await websocket.receive()
                        logger.info(f"WebSocket incoming from client: type={data.get('type')}, has_text={data.get('text') is not None}, has_bytes={data.get('bytes') is not None}")
                        if data["type"] == "websocket.receive":
                            if data.get("text") is not None:
                                await target_ws.send(data["text"])
                            elif data.get("bytes") is not None:
                                await target_ws.send(data["bytes"])
                        elif data["type"] == "websocket.disconnect":
                            logger.info(f"WebSocket client disconnected with code: {data.get('code')}")
                            break
                except Exception as e:
                    logger.warning(f"Websocket client exception: {e}")

            async def forward_target_to_client():
                try:
                    while True:
                        message = await target_ws.recv()
                        is_str = isinstance(message, str)
                        logger.info(f"WebSocket outgoing from Streamlit: is_str={is_str}, length={len(message)}")
                        if is_str:
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception as e:
                    logger.warning(f"Websocket target (Streamlit) exception: {e}")

            # run concurrently and wait for any to finish/disconnect
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(forward_client_to_target()),
                    asyncio.create_task(forward_target_to_client())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
    except Exception as e:
        logger.error(f"WebSocket proxy exception: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_root_to_streamlit(request: Request):
    """Forwards root base URL requests directly to Streamlit."""
    return await streamlit_proxy(request, "")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def streamlit_proxy(request: Request, path: str):
    """Transparent reverse proxy: forwards browser traffic to internal Streamlit."""
    target_url = f"{STREAMLIT_BASE}/{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            proxy_response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=await request.body()
            )
            
            # Exclude hop-by-hop headers and headers that httpx changes (like content-length/encoding after decompression)
            excluded_headers = {"content-length", "content-encoding", "transfer-encoding", "connection", "keep-alive"}
            headers = {k: v for k, v in proxy_response.headers.items() if k.lower() not in excluded_headers}

            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=headers,
                media_type=proxy_response.headers.get("content-type")
            )
    except httpx.ConnectError:
        logger.warning(f"Streamlit not yet ready at {STREAMLIT_BASE}/{path}, returning 503")
        return Response(
            content=b"<html><body><h2>Starting dashboard... please wait 10 seconds and refresh.</h2></body></html>",
            status_code=503,
            media_type="text/html"
        )
