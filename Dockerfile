# Use Python 3.11 slim image
FROM python:3.11-slim

# Install Node.js and essential tools
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Lighthouse SDK and dependencies globally
RUN npm install -g @lighthouse-web3/sdk @lighthouse-web3/kavach ethers

# Copy application code
COPY . .

# Set NODE_PATH so node can find globally installed modules
ENV NODE_PATH=/usr/local/lib/node_modules
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8787

# Start command
CMD ["python", "apps/worker/run.py"]
