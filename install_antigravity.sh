#!/bin/bash
set -e

echo "===================================================="
echo " Installing Google SecOps Agent Skills for Antigravity"
echo "===================================================="

REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "[1/4] Setting up Python virtual environment..."
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt --quiet
echo "      Virtual environment created at: $REPO_DIR/venv"

echo ""
echo "[2/4] Checking environment variables..."
if [ ! -f .env ]; then
    echo "      Creating .env file from template..."
    cp .env.example .env
    echo "      IMPORTANT: Please edit $REPO_DIR/.env with your GCP Project ID, Customer ID, Region, and optional Bindplane API keys!"
else
    echo "      .env file already exists."
fi

echo ""
echo "[3/4] Installing SKILL files to ~/.gemini/config/skills..."
mkdir -p ~/.gemini/config/skills

# Clean up retired/defunct skills from ~/.gemini/config/skills if previously installed
rm -rf ~/.gemini/config/skills/secops-cases \
       ~/.gemini/config/skills/secops-detection-eng \
       ~/.gemini/config/skills/secops-ingestion \
       ~/.gemini/config/skills/secops-router \
       ~/.gemini/config/skills/secops-threat-inv

# Copy the active skills directories
cp -r skills/* ~/.gemini/config/skills/

echo ""
echo "[4/4] Configuring skills with absolute paths..."
# Replace the placeholder with the actual absolute path to the repository
if [[ "$OSTYPE" == "darwin"* ]]; then
    find -L ~/.gemini/config/skills/secops-* ~/.gemini/config/skills/case-grouping -type f -name "*.md" -exec sed -i '' "s|<PATH_TO_SECOPS_SKILLS>|$REPO_DIR|g" {} +
else
    find -L ~/.gemini/config/skills/secops-* ~/.gemini/config/skills/case-grouping -type f -name "*.md" -exec sed -i "s|<PATH_TO_SECOPS_SKILLS>|$REPO_DIR|g" {} +
fi

echo "===================================================="
echo " Installation Complete! "
echo " Antigravity will now automatically discover these skills."
echo " Skills installed to: ~/.gemini/config/skills"
echo "===================================================="
