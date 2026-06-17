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
