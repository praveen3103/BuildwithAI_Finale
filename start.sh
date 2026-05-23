#!/bin/bash

# Cloud Run injects PORT — FastAPI claims it, Streamlit on a fixed internal port
PORT=${PORT:-8080}
STREAMLIT_PORT=8501

# Start Streamlit on internal port 8501
echo "Starting Streamlit dashboard on internal port $STREAMLIT_PORT..."
export BACKEND_URL="http://localhost:${PORT}"
./venv/bin/python -m streamlit run dashboard/app.py \
    --server.port $STREAMLIT_PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.enableWebsocketCompression false &

sleep 2
echo "Streamlit started on port $STREAMLIT_PORT."

# Start FastAPI on Cloud Run's required PORT (the health-checked port)
echo "Starting FastAPI backend on port $PORT (Cloud Run port)..."
./venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
