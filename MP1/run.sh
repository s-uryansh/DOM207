#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install Python 3, then run ./run.sh again."
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "Preparing the project for the first run..."
    python3 -m venv .venv
fi

echo "Installing the required packages..."
MP1_PIP_CACHE="${TMPDIR:-/tmp}/mp1-pip-cache"
PIP_CACHE_DIR="$MP1_PIP_CACHE" .venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo "Running the Foodie India analysis..."
.venv/bin/python analysis.py

echo "Checking the results..."
.venv/bin/python verify.py

echo "Done. Open Foodie_India_MP1_Report.pdf to read the report."
