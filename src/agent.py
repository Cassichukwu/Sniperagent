"""DEBUG agent - tests save first, then runs loop."""
import json
import time
import logging
from pathlib import Path
from rich.console import Console
from config import settings
from src.qwen_brain import QwenBrain
from src.solana_watcher import SolanaWatcher
from src.scorer import score_token

PROJECT_ROOT = Path(__file__).parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "verdicts.json"

console = Console()
logging.basicConfig(level=10, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent")

console.print("DEBUG: __file__ =", __file__)
console.print("DEBUG: PROJECT_ROOT =", PROJECT_ROOT)
console.print("DEBUG: LOG_FILE =", LOG_FILE)

# Test save immediately
try:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    test_data = [{"test": "save_works", "timestamp": "now"}]
    with open(LOG_FILE, "w") as f:
        json.dump(test_data, f, indent=2)
    console.print("DEBUG: SAVE WORKS! File at", LOG_FILE, "exists:", LOG_FILE.exists())
except Exception as e:
    console.print("DEBUG: SAVE FAILED:", e)

# Now run the agent
console.print("DEBUG: Starting agent loop...")

brain = QwenBrain()
watcher = SolanaWatcher()
verdicts = []

for i in range(3):
    console.print("DEBUG: Iteration", i)
    for tok in watcher.get_recent_tokens(3):
        try:
            v = score_token(tok, brain.score(tok))
            verdicts.append(v)
            console.print("  Scored", v.symbol, "->", v.score, v.verdict)
        except Exception as e:
            console.print("  ERROR scoring", tok.get("symbol"), ":", e)

console.print("DEBUG: Loop done. Verdicts count:", len(verdicts))

# Try to save real verdicts
try:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = [v.to_dict() for v in verdicts]
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    console.print("DEBUG: REAL SAVE WORKS! File exists:", LOG_FILE.exists())
    console.print("DEBUG: File size:", LOG_FILE.stat().st_size if LOG_FILE.exists() else 0)
except Exception as e:
    console.print("DEBUG: REAL SAVE FAILED:", e)

console.print("DEBUG: Done!")