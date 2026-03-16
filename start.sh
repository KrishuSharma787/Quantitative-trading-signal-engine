#!/bin/bash
echo "============================================"
echo "  Quantitative Trading Signal Engine"
echo "============================================"
echo ""

echo "[1/3] Checking Python..."
python3 --version || { echo "ERROR: Python not found. Install from python.org"; exit 1; }

echo ""
echo "[2/3] Installing dependencies..."
pip3 install -r requirements.txt --quiet || { echo "ERROR: pip install failed."; exit 1; }

echo ""
echo "[3/3] Seeding database with live data..."
python3 run.py --once || { echo "ERROR: Pipeline failed. Check .env and internet."; exit 1; }

echo ""
echo "============================================"
echo "  Launching Streamlit app..."
echo "  Open your browser to: http://localhost:8501"
echo "============================================"
echo ""
streamlit run app.py
