#!/bin/bash
PROJECT_DIR="/home/classics2323/crypto-monitor"
PYTHON_BIN="/usr/bin/python3"
cd $PROJECT_DIR
echo "=== Pipeline démarré : $(date) ==="

echo "Step 0 — Check position ouverte..."
$PYTHON_BIN src/check_position.py

echo "Step 1 — Collecte des données..."
$PYTHON_BIN src/collector.py

echo "Step 2 — Analyse forensic..."
$PYTHON_BIN src/report_builder.py

echo "Step 3 — Envoi à l'agent OpenClaw..."
$PYTHON_BIN src/request_analysis.py

echo "Step 3b — Enter new position..."
$PYTHON_BIN src/enter_new_position.py

echo "Step 4 — Export mémoire JSON..."
$PYTHON_BIN src/export_memory_json.py

echo "Step 5 — Push sur GitHub Pages..."
$PYTHON_BIN src/push_to_github.py
$PYTHON_BIN src/push_memory_github.py

echo "=== Pipeline terminé : $(date) ==="
