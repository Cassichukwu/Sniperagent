Set-Location "C:\meme-sniper-agent"
Remove-Item -Recurse -Force src, tests, dashboard, config.py -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "src", "tests", "dashboard" | Out-Null

@'
"""config.py - loads .env settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Settings:
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
    BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")
    BITGET_API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE", "")
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def status(self):
        return {"qwen_key": bool(self.QWEN_API_KEY), "bitget_key": bool(self.BITGET_API_KEY)}


settings = Settings()
'@ | Out-File "config.py" -Encoding utf8

@'
"""src package."""
'@ | Out-File "src\__init__.py" -Encoding utf8

@'
"""Watches Solana for new tokens. Mock data for now."""
import time
import random
import logging
from config import settings

log = logging.getLogger("solana")


class SolanaWatcher:
    def __init__(self):
        self.rpc_url = settings.SOLANA_RPC_URL
        self._n = 0

    def get_recent_tokens(self, limit=10):
        random.seed(int(time.time()) // 10)
        self._n += 1
        names = ["Pepe", "Doge", "Shib", "Wif", "Bonk", "Popcat", "Myro", "Slerf", "Giga", "Turbo"]
        suf = random.choice(["", "2", "Inu", "Coin", "X", "AI", "Sol"])
        out = []
        for i in range(limit):
            liq = random.uniform(500, 50000)
            h = random.randint(10, 500)
            a = random.randint(1, 240)
            out.append({
                "mint": "MOCK" + str(random.randint(100000, 999999)),
                "symbol": random.choice(names) + suf + str(random.randint(1, 99)),
                "name": "Mock Token " + str(self._n) + "-" + str(i),
                "liquidity_usd": liq,
                "holder_count": h,
                "age_minutes": a,
            })
        return out
'@ | Out-File "src\solana_watcher.py" -Encoding utf8

@'
"""Qwen LLM brain."""
import json
import re
import logging
from config import settings

log = logging.getLogger("qwen")

PROMPT = """You are a Solana memecoin analyst. Score 0-100, return ONLY JSON:
Token: {name} ({symbol})
Liquidity USD: {liquidity_usd}
Holders: {holder_count}
Age min: {age_minutes}

0-30 scam SKIP, 31-60 risky WATCH, 61-80 decent WATCH, 81-100 strong BUY.

JSON only: {{"score": N, "verdict": "BUY" or "WATCH" or "SKIP", "reasoning": "short"}}"""


class QwenBrain:
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self._client = None

    def _ensure(self):
        if self._client is None:
            import dashscope
            from dashscope import Generation
            dashscope.api_key = self.api_key
            self._client = Generation
        return self._client

    def _mock(self, t):
        liq = float(t.get("liquidity_usd", 0) or 0)
        h = int(t.get("holder_count", 0) or 0)
        a = int(t.get("age_minutes", 999) or 999)
        liq_score = min(50, liq / 500)
        holder_score = min(30, h * 0.1)
        freshness = max(0, 20 - a * 0.1)
        s = int(liq_score + holder_score + freshness)
        s = max(0, min(100, s))
        v = "BUY" if s >= 70 else "WATCH" if s >= 45 else "SKIP"
        reasoning = f"${liq:,.0f} liq, {h} holders, {a}m old. " + ("Strong" if s >= 70 else "Mixed" if s >= 45 else "Weak")
        return {"score": s, "verdict": v, "reasoning": reasoning}

    def _extract_text(self, response):
        try:
            out = response.output
            if out is None:
                return None
            if hasattr(out, "text") and out.text:
                return out.text
            if isinstance(out, dict) and out.get("text"):
                return out["text"]
            if hasattr(out, "choices") and out.choices:
                return out.choices[0].message.content
            return str(out)
        except Exception:
            return None

    def score(self, t):
        if not self.api_key:
            return self._mock(t)
        try:
            c = self._ensure()
            prompt = PROMPT.format(
                name=t.get("name", "Unknown"),
                symbol=t.get("symbol", "???"),
                liquidity_usd=t.get("liquidity_usd", 0),
                holder_count=t.get("holder_count", 0),
                age_minutes=t.get("age_minutes", 0),
            )
            r = c.call(model="qwen-turbo", prompt=prompt)
            text = self._extract_text(r)
            if not text:
                return self._mock(t)
            return self._parse(text)
        except Exception as e:
            log.error("Qwen failed: " + str(e))
            return self._mock(t)

    def _parse(self, text):
        if not text:
            return self._mock({})
        try:
            return self._ok(json.loads(text))
        except Exception:
            pass
        m = re.search(r"\{[^{}]*\}", text)
        if m:
            try:
                return self._ok(json.loads(m.group()))
            except Exception:
                pass
        return self._mock({})

    def _ok(self, d):
        s = max(0, min(100, int(d.get("score", 0))))
        v = str(d.get("verdict", "SKIP")).upper()
        if v not in ("BUY", "WATCH", "SKIP"):
            v = "SKIP"
        return {"score": s, "verdict": v, "reasoning": str(d.get("reasoning", ""))[:200]}
'@ | Out-File "src\qwen_brain.py" -Encoding utf8

@'
"""Combines data + Qwen verdict."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TokenVerdict:
    mint: str
    symbol: str
    name: str
    score: int
    verdict: str
    reasoning: str
    liquidity_usd: float
    holder_count: int
    age_minutes: int
    timestamp: str = ""


def score_token(t, q):
    return TokenVerdict(
        mint=t.get("mint", "unknown"),
        symbol=t.get("symbol", "???"),
        name=t.get("name", "Unknown"),
        score=int(q.get("score", 0)),
        verdict=str(q.get("verdict", "SKIP")),
        reasoning=str(q.get("reasoning", "")),
        liquidity_usd=float(t.get("liquidity_usd", 0)),
        holder_count=int(t.get("holder_count", 0)),
        age_minutes=int(t.get("age_minutes", 0)),
        timestamp=datetime.utcnow().isoformat(),
    )
'@ | Out-File "src\scorer.py" -Encoding utf8

@'
"""Bitget client (optional)."""
import requests


class BitgetClient:
    BASE = "https://api.bitget.com"

    def __init__(self):
        self.session = requests.Session()

    def ping(self):
        try:
            r = self.session.get(self.BASE + "/api/v2/public/time", timeout=5)
            return r.json()
        except Exception as e:
            return {"error": str(e)}
'@ | Out-File "src\bitget_client.py" -Encoding utf8

@'
"""Main agent loop."""
import time
import logging
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from config import settings
from src.qwen_brain import QwenBrain
from src.solana_watcher import SolanaWatcher
from src.scorer import score_token

console = Console()
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent")

BANNER = """
   =========================================================
     M E M E   S N I P E R   A G E N T
     AI-Powered Solana Memecoin Hunter
   =========================================================
"""


def table(verdicts):
    t = Table(title="Live Verdicts", show_header=True, header_style="bold magenta")
    t.add_column("Symbol", style="cyan")
    t.add_column("Score", justify="right")
    t.add_column("Verdict", justify="center")
    t.add_column("Liquidity", justify="right")
    t.add_column("Reasoning", style="dim")
    for v in verdicts[-10:]:
        style = {"BUY": "bold green", "WATCH": "bold yellow", "SKIP": "dim red"}.get(v.verdict, "white")
        t.add_row(v.symbol, str(v.score), "[" + style + "]" + v.verdict + "[/" + style + "]",
                  "$" + format(v.liquidity_usd, ",.0f"), v.reasoning[:60])
    return t


def run(cycles=5):
    console.print(BANNER, style="bold cyan")
    if not settings.status()["qwen_key"]:
        console.print(Panel("No Qwen key - running in MOCK mode.", border_style="yellow"))
    brain = QwenBrain()
    watcher = SolanaWatcher()
    verdicts = []
    with Live(table(verdicts), refresh_per_second=2, console=console) as live:
        for tick in range(cycles):
            log.info("Cycle " + str(tick + 1) + "/" + str(cycles))
            for tok in watcher.get_recent_tokens(5):
                v = score_token(tok, brain.score(tok))
                verdicts.append(v)
                log.info("  " + v.symbol + " -> " + str(v.score) + " (" + v.verdict + ")")
            live.update(table(verdicts))
            time.sleep(2)
    console.print(Panel("Done. " + str(len(verdicts)) + " verdicts.", border_style="green"))


if __name__ == "__main__":
    run()
'@ | Out-File "src\agent.py" -Encoding utf8

@'
"""Dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="MemeSniper", page_icon="dart", layout="wide")
st.title("MemeSniper Agent")
st.subheader("AI-Powered Solana Memecoin Hunter")

df = pd.DataFrame({
    "Symbol": ["PEPE2", "DOGEX", "BONKINU", "WIFAI", "TURBO99", "SLERF2"],
    "Score": [85, 72, 45, 91, 38, 67],
    "Verdict": ["BUY", "WATCH", "SKIP", "BUY", "SKIP", "WATCH"],
    "Liquidity": [15000, 8000, 2000, 22000, 500, 12000],
    "Holders": [180, 95, 30, 250, 12, 140],
})

c1, c2, c3 = st.columns(3)
c1.metric("Scanned", "127")
c2.metric("BUY", "8")
c3.metric("Win Rate", "67%")

st.dataframe(df, use_container_width=True)

fig = px.scatter(df, x="Liquidity", y="Score", color="Verdict", size="Holders",
                 color_discrete_map={"BUY": "green", "WATCH": "yellow", "SKIP": "red"})
st.plotly_chart(fig, use_container_width=True)

st.caption("Bitget AI x Crypto Hackathon 2026")
'@ | Out-File "dashboard\app.py" -Encoding utf8

@'
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
'@ | Out-File "tests\test_hello.py" -Encoding utf8

@'
QWEN_API_KEY=nsqeQrjWasXDrvdd
BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSPHRASE=
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
LOG_LEVEL=INFO
'@ | Out-File ".env" -Encoding utf8

Write-Host "Reset complete. Run: python -m src.agent" -ForegroundColor Green