#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> IDShield AI: Starting Render build process..."

# 1. Build Frontend SPA
echo "==> Building frontend distribution..."
cd frontend
npm install --include=dev
npm run build
cd ..

# 2. Install Backend Dependencies
echo "==> Installing backend Python dependencies..."
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

echo "==> IDShield AI build completed successfully!"
