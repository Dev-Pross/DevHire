#!/bin/bash

# 1. DESTROY the corrupted environment first
rm -rf myenv

# 2. Create the environment FORCING copies instead of symlinks (The NTFS Fix)
python3 -m venv --copies myenv

# 3. Activate the virtual environment
source myenv/bin/activate

# 4. Upgrade pip inside the isolated environment
pip install --upgrade pip

# 5. Install your Python dependencies
pip install -r requirements.txt
pip install aiohttp

# 6. Install Playwright binaries
playwright install chromium