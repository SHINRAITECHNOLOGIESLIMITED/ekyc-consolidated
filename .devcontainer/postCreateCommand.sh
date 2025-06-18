#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements-dev.txt

echo "Installing Node.js dependencies for portal..."
if [ -d "portal" ]; then
  cd portal && npm install
fi

echo "Setup complete!"