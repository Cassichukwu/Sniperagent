"""dashboard/app.py - Streamlit dashboard with live data."""
import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="MemeSniper Agent", page_icon=":dart:", layout="wide")

PROJECT_ROOT = Path(__file__).parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "verdicts.json"


def load_verdicts():
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def run_agent_and_capture():
    try:
        result = subprocess.run(
            ["python", "-m", "src.agent"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error("Agent run failed: " + str(e))
        return []


verdicts = load_verdicts()

st.title("MemeSniper Agent")
st.subheader("AI-Powered Solana Memecoin Hunter")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.metric("Agent Status", "Ready" if verdicts else "Not Run")
with col_s2:
    from config import settings
    st.metric("Qwen API", "OK" if settings.QWEN_API_KEY else "Missing")
with col_s3:
    st.metric("Bitget", "OK" if settings.BITGET_API_KEY else "Demo")
with col_s4:
    if verdicts:
        st.metric("Last Run", verdicts[0].get("timestamp", "")[:19])
    else:
        st.metric("Last Run", "Never")

st.markdown("---")

if st.button("Run Agent Now", type="primary"):
    with st.spinner("Agent running... (1-2 min with Qwen)"):
        verdicts = run_agent_and_capture()
    if verdicts:
        st.success("Scanned " + str(len(verdicts)) + " tokens!")
        st.rerun()
    else:
        st.warning("No tokens captured.")

if verdicts:
    df = pd.DataFrame(verdicts)
    st.markdown("### Latest Verdicts")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tokens", len(verdicts))
    with c2:
        st.metric("BUY", sum(1 for v in verdicts if v.get("verdict") == "BUY"))
    with c3:
        st.metric("SKIP", sum(1 for v in verdicts if v.get("verdict") == "SKIP"))
    with c4:
        avg = sum(v.get("score", 0) for v in verdicts) / len(verdicts)
        st.metric("Avg Score", str(int(avg)))
    display = df[["symbol", "score", "verdict", "liquidity_usd", "reasoning"]].copy()
    display["liquidity_usd"] = display["liquidity_usd"].apply(lambda x: "$" + format(float(x), ",.0f"))
    display.columns = ["Symbol", "Score", "Verdict", "Liquidity", "Reasoning"]
    st.dataframe(display, use_container_width=True, height=400)
    st.markdown("---")
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(px.histogram(df, x="score", nbins=15, color="verdict",
            color_discrete_map={"BUY": "green", "WATCH": "yellow", "SKIP": "red"}),
            use_container_width=True)
    with cr:
        st.plotly_chart(px.scatter(df, x="liquidity_usd", y="score", color="verdict", size="score",
            color_discrete_map={"BUY": "green", "WATCH": "yellow", "SKIP": "red"}),
            use_container_width=True)
    st.markdown("### Top BUY Signals")
    buys = sorted([v for v in verdicts if v.get("verdict") == "BUY"], key=lambda x: x.get("score", 0), reverse=True)[:5]
    if buys:
        for b in buys:
            st.success("**" + str(b.get("symbol")) + "** - Score " + str(b.get("score")) + " - $" + format(b.get("liquidity_usd", 0), ",.0f") + " - " + str(b.get("reasoning", "")))
    else:
        st.info("No BUY signals this run.")
else:
    st.info("No data yet. Click Run Agent Now to start.")

st.caption("Bitget AI x Crypto Hackathon 2026 | Python + Qwen + Solana + Streamlit")