# Use Python 3.11 slim image
FROM python:3.11-slim

# Install Node.js for Lighthouse CLI
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Node.js package files and install (for caching)
COPY apps/worker/package*.json apps/worker/
RUN cd apps/worker && npm install && cd /app

# Copy rest of application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8787

# Start command
CMD ["python", "apps/worker/run.py"]
