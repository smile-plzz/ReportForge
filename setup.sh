#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "✅ Environment ready. Run: python src/report.py --csv ./tests/sample_comments.csv --tz Asia/Dhaka --out ./out"
