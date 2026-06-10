#!/bin/bash
set -e

echo "======================================"
echo " AIOps Desktop Agent Installer"
echo "======================================"

echo "1. Checking requirements..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install it first."
    exit 1
fi

echo "2. Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "3. Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo "4. Building standalone executable with PyInstaller..."
# We use --onedir because it is much faster to launch than --onefile on Linux
pyinstaller --noconfirm --onedir --windowed --name "AIOps-Agent" \
  --hidden-import PySide6.QtCore \
  --hidden-import PySide6.QtGui \
  --hidden-import PySide6.QtWidgets \
  --hidden-import requests \
  main.py

echo "5. Installing to ~/.local/bin..."
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications

# Clean previous installation if exists
rm -rf ~/.local/bin/AIOps-Agent-App
cp -r dist/AIOps-Agent ~/.local/bin/AIOps-Agent-App

# Create a symlink so it can be executed easily
ln -sf ~/.local/bin/AIOps-Agent-App/AIOps-Agent ~/.local/bin/AIOps-Agent

echo "6. Setting up Desktop Entry..."
cp AIOps.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/ || true

echo "======================================"
echo " Installation Complete!"
echo " You can now launch 'AIOps Desktop Agent' from your system application menu."
echo " Or run '~/.local/bin/AIOps-Agent' directly from terminal."
echo "======================================"
