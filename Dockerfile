FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create report directory
RUN mkdir -p /tmp/downloads /app/reports

# Set Python path
ENV PYTHONPATH=/app

# Expose ports for MCP servers (SSE transport)
EXPOSE 8001 8002 8003

# Default command: run all 3 MCP servers + agent
CMD ["python", "-m", "client.main"]
