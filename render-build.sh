#!/usr/bin/env bash
# render-build.sh - Custom build script for Render

# Fail on error
set -o errexit
set -o pipefail
set -o nounset

# Display Python version
echo "Using Python version:"
python --version

# Upgrade pip, setuptools, and wheel
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Build completed successfully!"
