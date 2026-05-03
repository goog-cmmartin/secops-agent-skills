#!/bin/bash
set -e

echo "===================================================="
echo " Installing Google SecOps Agent Skills for OpenCode "
echo "===================================================="

REPO_DIR=$(pwd)

echo "[1/4] Setting up Python virtual environment..."
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt --quiet
echo "      Virtual environment created at: $REPO_DIR/venv"

echo ""
echo "[2/4] Checking environment variables..."
if [ ! -f .env ]; then
    echo "      Creating .env file from template..."
    cp .env.example .env
    echo "      ⚠️ IMPORTANT: Please edit $REPO_DIR/.env with your GCP Project ID, Customer ID, and Region!"
else
    echo "      .env file already exists."
fi

echo ""
echo "[3/4] Installing SKILL files to ~/.config/opencode/skills..."
mkdir -p ~/.config/opencode/skills

# Copy the skills directories
cp -r skills/* ~/.config/opencode/skills/

echo ""
echo "[4/4] Configuring skills with absolute paths..."
# Replace the placeholder with the actual absolute path to the repository
find ~/.config/opencode/skills/secops-* -type f -name "SKILL.md" -exec sed -i "s|<PATH_TO_SECOPS_SKILLS>|$REPO_DIR|g" {} +

echo "===================================================="
echo " Installation Complete! "
echo " OpenCode will now automatically discover these skills."
echo " You can test it by asking OpenCode: 'What can you do with SecOps?'"
echo "===================================================="
