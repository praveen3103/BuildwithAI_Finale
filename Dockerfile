FROM python:3.11-slim

WORKDIR /app

# Install basic system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project requirements and build virtual environment
COPY requirements.txt .
RUN python -m venv venv
RUN ./venv/bin/pip install --no-cache-dir --upgrade pip
RUN ./venv/bin/pip install --no-cache-dir -r requirements.txt
RUN ./venv/bin/pip install --no-cache-dir pandas

# Install the real google-antigravity package
# Since this container runs Linux x86_64, the compatible wheel is fetched automatically from PyPI.
RUN ./venv/bin/pip install --no-cache-dir google-antigravity || true

# Copy application source files
COPY backend/ backend/
COPY dashboard/ dashboard/
COPY start.sh .
RUN chmod +x start.sh

# Expose standard Cloud Run port
EXPOSE 8080

# Execute unified startup process
CMD ["./start.sh"]
