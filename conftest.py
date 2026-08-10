"""
conftest.py
────────────
Permet à pytest de trouver le package `src` depuis n'importe où,
en ajoutant la racine du projet au PYTHONPATH avant la collecte des tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))