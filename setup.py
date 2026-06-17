"""
setup.py — One-shot installer for MemeSniper Agent.
Run: python setup.py
"""
import os, sys, subprocess
from pathlib import Path

ROOT = Path.cwd()


def banner(t):
    print()
    print("=" * 60)
    print("  " + t)
    print("=" * 60)


def info(m): print("  [INFO]  " + m)
def ok(m):   print("  [ OK ]  " + m)
def fail(m): print("  [FAIL]  " + m)
def ask(p, d=""):
    s = " [" + d + "]" if d else ""
    v = input("  " + p + s + ": ").strip()
    return v or d


def write(rel, lines):
    """Write a list of lines to a file, creating parent dirs."""
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok("  " + rel)
    # ---------------- file contents (each as a list of plain lines) ----------------

CONFIG = [
    '"""config.py - loads .env settings."""',
    'import os',
    'from pathlib import Path',
    'from dotenv import load_dotenv',
    '',
    'env_path = Path(__file__).parent / ".env"',
    'load_dotenv(env_path)',
    '',
    'class Settings:',
    '    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")',
    '    BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")',
    '    BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")',
    '    BITGET_API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE", "")',
    '    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")',
    '    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")',
    '    SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "10"))',
    '    MIN_LIQUIDITY_USD = int(os.getenv("MIN_LIQUIDITY_USD", "1000"))',
    '',
    '    def status(self):',
    '        return {',
    '            "qwen_key": bool(self.QWEN_API_KEY),',
    '            "bitget_key": bool(self.BITGET_API_KEY),',
    '            "bitget_secret": bool(self.BITGET_API_SECRET),',
    '            "bitget_passphrase": bool(self.BITGET_API_PASSPHRASE),',
    '        }',
    '',
    'settings = Settings()',
]

SRC_INIT = ['"""src package."""']

SOLANA_WATCHER = [
    '"""Watches Solana for new tokens. Mock data for now."""',
    'import time, random, logging',
    'from config import settings',
    '',
    'log = logging.getLogger("solana")',
    '',
    'class SolanaWatcher:',
    '    def __init__(self):',
    '        self.rpc_url = settings.SOLANA_RPC_URL',
    '        self._n = 0',
    '',
    '    def get_recent_tokens(self, limit=10):',
    '        random.seed(int(time.time()) // 10)',
    '        self._n += 1',
    '        names = ["Pepe", "Doge", "Shib", "Wif", "Bonk", "Popcat", "Myro", "Slerf", "Giga", "Turbo"]',
    '        suf = random.choice(["", "2", "Inu", "Coin", "X", "AI", "Sol"])',
    '        out = []',
    '        for i in range(limit):',
    '            out.append({',
    '                "mint": "MOCK" + str(random.randint(100000, 999999)),',
    '                "symbol": random.choice(names) + suf + str(random.randint(1,99)),',
    '                "name": "Mock Token " + str(self._n) + "-" + str(i),',
    '                "liquidity_usd": random.uniform(500, 50000),',
    '                "holder_count": random.randint(10, 500),',
    '                "age_minutes": random.randint(1, 240),',
    '            })',
    '        return out',
    '',
    'if __name__ == "__main__":',
    '    w = SolanaWatcher()',
    '    for t in w.get_recent_tokens(3):',
    '        print(t)',
]
QWEN_BRAIN = [
    '"""Qwen LLM brain. Falls back to mock if no key."""',
    'import json, re, logging',
    'from config import settings',
    '',
    'log = logging.getLogger("qwen")',
    '',
    'PROMPT = """Score this Solana token 0-100 and pick BUY/WATCH/SKIP.',
    'Token: {name} ({symbol})',
    'Liquidity USD: {liquidity_usd}',
    'Holders: {holder_count}',
    'Age (min): {age_minutes}',
    '',
    'Return ONLY JSON: {{"score": N, "verdict": "BUY|WATCH|SKIP", "reasoning": "..."}}"""',
    '',
    'class QwenBrain:',
    '    def __init__(self):',
    '        self.api_key = settings.QWEN_API_KEY',
    '        self._client = None',
    '',
    '    def _ensure(self):',
    '        if self._client is None:',
    '            import dashscope',
    '            from dashscope import Generation',
    '            dashscope.api_key = self.api_key',
    '            self._client = Generation',
    '        return self._client',
    '',
    '    def _mock(self, t):',
    '        liq = t.get("liquidity_usd", 0)',
    '        h = t.get("holder_count", 0)',
    '        a = t.get("age_minutes", 999)',
    '        s = max(0, min(100, int(liq/100 + h*0.3 - a*0.5)))',
    '        v = "BUY" if s >= 70 else "WATCH" if s >= 45 else "SKIP"',
    '        return {"score": s, "verdict": v, "reasoning": "Mock: $" + format(liq, ",.0f") + " liq, " + str(h) + " holders, " + str(a) + "m old."}',
    '',
    '    def score(self, t):',
    '        if not self.api_key:',
    '            return self._mock(t)',
    '        try:',
    '            c = self._ensure()',
    '            prompt = PROMPT.format(',
    '                name=t.get("name", "?"),',
    '                symbol=t.get("symbol", "?"),',
    '                liquidity_usd=t.get("liquidity_usd", 0),',
    '                holder_count=t.get("holder_count", 0),',
    '                age_minutes=t.get("age_minutes", 0),',
    '            )',
    '            r = c.call(model="qwen-turbo", prompt=prompt)',
    '            text = r.output.text if hasattr(r.output, "text") else str(r.output)',
    '            return self._parse(text)',
    '        except Exception as e:',
    '            log.error("Qwen failed: " + str(e))',
    '            return self._mock(t)',
    '',
    '    def _parse(self, text):',
    '        try:',
    '            return self._ok(json.loads(text))',
    '        except Exception: pass',
    '        m = re.search(r"\\{[^{}]*\\}", text)',
    '        if m:',
    '            try: return self._ok(json.loads(m.group()))',
    '            except Exception: pass',
    '        return self._mock({})',
    '',
    '    def _ok(self, d):',
    '        s = max(0, min(100, int(d.get("score", 0))))',
    '        v = str(d.get("verdict", "SKIP")).upper()',
    '        if v not in ("BUY", "WATCH", "SKIP"): v = "SKIP"',
    '        return {"score": s, "verdict": v, "reasoning": str(d.get("reasoning", ""))[:200]}',
    '',
    'if __name__ == "__main__":',
    '    print(QwenBrain().score({"name":"Pepe","symbol":"PEPE","liquidity_usd":15000,"holder_count":250,"age_minutes":30}))',
]
SCORER = [
    '"""Combines data + Qwen verdict."""',
    'from dataclasses import dataclass',
    'from datetime import datetime',
    '',
    '@dataclass',
    'class TokenVerdict:',
    '    mint: str',
    '    symbol: str',
    '    name: str',
    '    score: int',
    '    verdict: str',
    '    reasoning: str',
    '    liquidity_usd: float',
    '    holder_count: int',
    '    age_minutes: int',
    '    timestamp: str = ""',
    '',
    'def score_token(t, q):',
    '    return TokenVerdict(',
    '        mint=t.get("mint","unknown"),',
    '        symbol=t.get("symbol","???"),',
    '        name=t.get("name","Unknown"),',
    '        score=int(q.get("score",0)),',
    '        verdict=str(q.get("verdict","SKIP")),',
    '        reasoning=str(q.get("reasoning","")),',
    '        liquidity_usd=float(t.get("liquidity_usd",0)),',
    '        holder_count=int(t.get("holder_count",0)),',
    '        age_minutes=int(t.get("age_minutes",0)),',
    '        timestamp=datetime.utcnow().isoformat(),',
    '    )',
]

BITGET = [
    '"""Bitget client (optional)."""',
    'import requests',
    'from config import settings',
    '',
    'class BitgetClient:',
    '    BASE = "https://api.bitget.com"',
    '    def __init__(self):',
    '        self.session = requests.Session()',
    '    def ping(self):',
    '        try:',
    '            r = self.session.get(self.BASE + "/api/v2/public/time", timeout=5)',
    '            return r.json()',
    '        except Exception as e: return {"error": str(e)}',
    '    def ticker(self, symbol="BTCUSDT"):',
    '        try:',
    '            r = self.session.get(self.BASE + "/api/v2/mix/market/ticker",',
    '                params={"symbol": symbol, "productType": "USDT-FUTURES"}, timeout=5)',
    '            d = r.json()',
    '            return d["data"][0] if d.get("code") == "00000" else None',
    '        except Exception: return None',
]

AGENT = [
    '"""Main agent loop."""',
    'import time, logging',
    'from rich.console import Console',
    'from rich.panel import Panel',
    'from rich.live import Live',
    'from rich.table import Table',
    'from config import settings',
    'from src.qwen_brain import QwenBrain',
    'from src.solana_watcher import SolanaWatcher',
    'from src.scorer import score_token',
    '',
    'console = Console()',
    'logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format="%(asctime)s [%(levelname)s] %(message)s")',
    'log = logging.getLogger("agent")',
    '',
    'BANNER = """',
    '   =========================================================',
    '     M E M E   S N I P E R   A G E N T',
    '     AI-Powered Solana Memecoin Hunter',
    '     Bitget AI x Crypto Hackathon 2026',
    '   =========================================================',
    '"""',
    '',
    'def table(verdicts):',
    '    t = Table(title="Live Verdicts", show_header=True, header_style="bold magenta")',
    '    t.add_column("Symbol", style="cyan")',
    '    t.add_column("Score", justify="right")',
    '    t.add_column("Verdict", justify="center")',
    '    t.add_column("Liquidity", justify="right")',
    '    t.add_column("Reasoning", style="dim")',
    '    for v in verdicts[-10:]:',
    '        style = {"BUY":"bold green","WATCH":"bold yellow","SKIP":"dim red"}.get(v.verdict, "white")',
    '        t.add_row(v.symbol, str(v.score), "[" + style + "]" + v.verdict + "[/" + style + "]",',
    '                  "$" + format(v.liquidity_usd, ",.0f"), v.reasoning[:60])',
    '    return t',
    '',
    'def run(cycles=5):',
    '    console.print(BANNER, style="bold cyan")',
    '    if not settings.status()["qwen_key"]:',
    '        console.print(Panel("No Qwen key - running in MOCK mode.", border_style="yellow"))',
    '    brain = QwenBrain()',
    '    watcher = SolanaWatcher()',
    '    verdicts = []',
    '    with Live(table(verdicts), refresh_per_second=2, console=console) as live:',
    '        for tick in range(cycles):',
    '            log.info("Cycle " + str(tick+1) + "/" + str(cycles))',
    '            for tok in watcher.get_recent_tokens(5):',
    '                v = score_token(tok, brain.score(tok))',
    '                verdicts.append(v)',
    '                log.info("  " + v.symbol + " -> " + str(v.score) + " (" + v.verdict + ")")',
    '            live.update(table(verdicts))',
    '            time.sleep(2)',
    '    console.print(Panel("Done. " + str(len(verdicts)) + " verdicts.", border_style="green"))',
    '',
    'if __name__ == "__main__":',
    '    run()',
]
TEST = [
    '"""Smoke test."""',
    'import sys',
    'from pathlib import Path',
    'sys.path.insert(0, str(Path(__file__).parent.parent))',
    'from rich.console import Console',
    'from config import settings',
    'console = Console()',
    'console.print("\\nSmoke Test", style="bold cyan")',
    'console.print("Python: " + str(sys.version_info.major) + "." + str(sys.version_info.minor))',
    's = settings.status()',
    'n = sum(s.values())',
    'console.print("Keys: " + str(n) + "/4")',
    'try:',
    '    from src.qwen_brain import QwenBrain',
    '    from src.solana_watcher import SolanaWatcher',
    '    from src.scorer import score_token',
    '    r = QwenBrain().score({"name":"T","symbol":"T","liquidity_usd":10000,"holder_count":100,"age_minutes":30})',
    '    console.print("Brain OK: " + str(r["score"]) + " " + r["verdict"])',
    '    console.print("All systems go!", style="bold green")',
    'except Exception as e:',
    '    console.print("FAIL: " + str(e), style="red")',
    '    sys.exit(1)',
]

DASH = [
    '"""Streamlit dashboard. Run: streamlit run dashboard/app.py"""',
    'import streamlit as st',
    'import pandas as pd',
    'import plotly.express as px',
    '',
    'st.set_page_config(page_title="MemeSniper", page_icon="xF0x9Fx8ExAF", layout="wide")',
    'st.title("MemeSniper Agent")',
    'st.subheader("AI-Powered Solana Memecoin Hunter")',
    '',
    'df = pd.DataFrame({',
    '    "Symbol": ["PEPE2", "DOGEX", "BONKINU", "WIFAI", "TURBO99", "SLERF2"],',
    '    "Score": [85, 72, 45, 91, 38, 67],',
    '    "Verdict": ["BUY", "WATCH", "SKIP", "BUY", "SKIP", "WATCH"],',
    '    "Liquidity": [15000, 8000, 2000, 22000, 500, 12000],',
    '    "Holders": [180, 95, 30, 250, 12, 140],',
    '    "Age_min": [15, 45, 8, 25, 3, 60],',
    '})',
    '',
    'c1, c2, c3, c4 = st.columns(4)',
    'c1.metric("Scanned", "127", "+12/hr")',
    'c2.metric("BUY", "8", "+2/hr")',
    'c3.metric("Win Rate", "67%")',
    'c4.metric("Qwen", "342/10k")',
    '',
    'st.markdown("---")',
    'st.subheader("Recent Verdicts")',
    'st.dataframe(df, use_container_width=True)',
    '',
    'cl, cr = st.columns(2)',
    'with cl:',
    '    st.plotly_chart(px.histogram(df, x="Score", color="Verdict",',
    '        color_discrete_map={"BUY":"green","WATCH":"yellow","SKIP":"red"}),',
    '        use_container_width=True)',
    'with cr:',
    '    st.plotly_chart(px.scatter(df, x="Liquidity", y="Score", color="Verdict",',
    '        size="Holders", color_discrete_map={"BUY":"green","WATCH":"yellow","SKIP":"red"}),',
    '        use_container_width=True)',
    '',
    'st.caption("Bitget AI x Crypto Hackathon 2026")',
]

README = [
    '# MemeSniper Agent',
    '',
    'AI Trading Agent for the Bitget AI x Crypto Hackathon 2026.',
    '',
    '## Run',
    '```',
    'pip install -r requirements.txt',
    'python src/agent.py',
    'streamlit run dashboard/app.py',
    '```',
]

REQS = [
    'requests==2.32.3',
    'pandas==2.2.2',
    'numpy==1.26.4',
    'python-dotenv==1.0.1',
    'rich==13.7.1',
    'pydantic==2.8.2',
    'streamlit==1.38.0',
    'plotly==5.22.0',
    'dashscope==1.20.11',
    'solana==0.30.2',
    'solders==0.18.1',
    'httpx==0.27.0',
]

GITIGNORE = [
    '.env',
    '*.key',
    '__pycache__/',
    '*.py[cod]',
    'venv/',
    '.venv/',
    'data/',
    '*.log',
    '.vscode/',
    '.idea/',
]

ALL_FILES = {
    "config.py": CONFIG,
    "src/__init__.py": SRC_INIT,
    "src/solana_watcher.py": SOLANA_WATCHER,
    "src/qwen_brain.py": QWEN_BRAIN,
    "src/scorer.py": SCORER,
    "src/bitget_client.py": BITGET,
    "src/agent.py": AGENT,
    "tests/test_hello.py": TEST,
    "dashboard/app.py": DASH,
    "README.md": README,
    "requirements.txt": REQS,
    ".gitignore": GITIGNORE,
}
# ---------------- main flow ----------------

def install_deps():
    banner("STEP 1: Installing packages")
    pkgs = ["requests", "pandas", "streamlit", "python-dotenv", "rich", "pydantic",
            "dashscope", "solana", "solders", "plotly", "httpx"]
    info("Installing: " + ", ".join(pkgs))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *pkgs])
        ok("All packages installed")
        return True
    except subprocess.CalledProcessError as e:
        fail("pip failed: " + str(e))
        return False


def write_env(qwen):
    banner("STEP 2: Writing .env")
    content = ("QWEN_API_KEY=" + qwen + "\n"
               "BITGET_API_KEY=\n"
               "BITGET_API_SECRET=\n"
               "BITGET_API_PASSPHRASE=\n"
               "SOLANA_RPC_URL=https://api.mainnet-beta.solana.com\n"
               "LOG_LEVEL=INFO\n"
               "SCAN_INTERVAL_SECONDS=10\n"
               "MIN_LIQUIDITY_USD=1000\n")
    (ROOT / ".env").write_text(content, encoding="utf-8")
    ok("Created .env")


def write_all():
    banner("STEP 3: Creating project files")
    for rel, lines in ALL_FILES.items():
        write(rel, lines)


def smoke():
    banner("STEP 4: Smoke test")
    try:
        subprocess.check_call([sys.executable, str(ROOT / "tests" / "test_hello.py")])
        return True
    except subprocess.CalledProcessError as e:
        fail("Smoke failed: " + str(e))
        return False


def main():
    print()
    print("  M E M E   S N I P E R   A G E N T  -  SETUP")
    print()
    banner("STEP 0: API Keys")
    qwen = ask("Qwen API key (from Bitget email)", "")
    if not install_deps():
        return 1
    write_env(qwen)
    write_all()
    smoke()
    banner("DONE")
    print()
    print("  Next:")
    print("    python src/agent.py")
    print("    streamlit run dashboard/app.py")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())