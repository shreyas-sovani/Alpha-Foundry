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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Lighthouse SDK globally
RUN npm install -g @lighthouse-web3/sdk

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8787

# Start command
CMD ["python", "apps/worker/run.py"]
