import time
import threading
import requests
import uvicorn
import sys
from backend.main import app

def run_server():
    """Runs the FastAPI server in a separate background thread."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

def main():
    print("================================================================")
    print(" 🧪 Starting Automated Synthetic Integration Test Suite          ")
    print("================================================================")
    
    # 1. Start backend server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("⏳ Waiting for FastAPI server to start...")
    time.sleep(3) # Let server start
    
    BASE_URL = "http://127.0.0.1:8000"
    
    try:
        # Check online status
        res = requests.get(f"{BASE_URL}/")
        assert res.status_code == 200, "Backend is offline!"
        print("✅ FastAPI server successfully online.")
        
        # Reset any existing states
        requests.post(f"{BASE_URL}/api/telemetry/reset")
        print("✅ Stadium database successfully reset.")
        
        # 2. Simulate "Gate 3 Bottleneck" Telemetry Crisis Influx
        print("\n🚨 Simulating 'Gate 3 Bottleneck' Crisis Payload (utilization = 96%)...")
        telemetry_payload = {
            "gate": {
                "gate_id": "Gate 3",
                "crowd_count": 4800, # Gate 3 capacity limit is 5000 (96% utilization)
                "status": "BOTTLENECK"
            }
        }
        
        # Send telemetry ingest post request
        ingest_res = requests.post(f"{BASE_URL}/api/telemetry", json=telemetry_payload)
        assert ingest_res.status_code == 200, f"Telemetry ingestion failed: {ingest_res.text}"
        data = ingest_res.json()
        print("✅ Ingest call returned HTTP 200 successfully.")
        print(f"👉 Backend message: {data.get('message')}")
        
        # 3. Retrieve and Assert Stadium Operational State Updates
        print("\n🔍 Fetching latest Stadium database to verify state changes...")
        db_res = requests.get(f"{BASE_URL}/api/dashboard/data")
        assert db_res.status_code == 200
        stadium_db = db_res.json()
        
        # Assert Gate 3 is correctly updated to BOTTLENECK
        gate_3 = stadium_db["gates"].get("Gate 3")
        assert gate_3 is not None, "Gate 3 not found in stadium state!"
        assert gate_3["crowd_count"] == 4800, "Crowd count not updated!"
        assert gate_3["status"] == "BOTTLENECK", "Gate status was not marked as BOTTLENECK!"
        print("✅ ASSERTION SUCCESSFUL: Gate 3 status is correctly set to BOTTLENECK in-memory.")
        
        # Assert that the broadcast alert was published
        broadcasts = stadium_db["broadcasts"]
        assert len(broadcasts) > 0, "No emergency broadcasts were generated!"
        print("✅ ASSERTION SUCCESSFUL: Emergency broadcasts were published to public channels:")
        for bc in broadcasts:
            print(f"   📣 [{bc.get('zone')}]: {bc.get('message')}")
            
        # Assert that agent trace logs are captured
        actions = stadium_db["agent_actions"]
        assert len(actions) > 0, "No agent actions were logged!"
        print("✅ ASSERTION SUCCESSFUL: Routing Agent response logs captured in action tracker:")
        for act in actions:
            print(f"   🤖 [Agent Action]: {act.get('step')}")
            print(f"   💬 Reasoning trace: {act.get('reasoning')[:120]}...")
            print(f"   🚀 Orchestrated Mitigation Plan: {act.get('outcome')[:180]}...")
            
        print("\n================================================================")
        print(" 🎉 ALL AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY!         ")
        print("================================================================")
        sys.exit(0)
        
    except AssertionError as ae:
        print(f"\n❌ ASSERTION FAILED: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR DURING TEST EXECUTION: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
