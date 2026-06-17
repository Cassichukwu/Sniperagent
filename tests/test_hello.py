"""Smoke test."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rich.console import Console
from config import settings
from src.qwen_brain import QwenBrain
from src.solana_watcher import SolanaWatcher
from src.scorer import score_token

console = Console()
console.print("Smoke Test", style="bold cyan")
console.print("Python: " + str(sys.version_info.major) + "." + str(sys.version_info.minor))
console.print("Qwen key: " + ("YES" if settings.QWEN_API_KEY else "NO"))
brain = QwenBrain()
test_token = {"name": "Test", "symbol": "TEST", "liquidity_usd": 20000, "holder_count": 300, "age_minutes": 45}
r = brain.score(test_token)
console.print("Brain: " + str(r))
console.print("All systems go!", style="bold green")
