FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create required dirs
RUN mkdir -p logs exports

# Expose API port
EXPOSE 5000

# Default: run the demo (change to api_server.py for production REST API)
CMD ["python", "demo.py"]
