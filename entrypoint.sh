#!/bin/bash
set -e

# Navigate to the app directory
cd /app

# Execute the Python application
exec /usr/local/bin/python apps/worker/run.py
