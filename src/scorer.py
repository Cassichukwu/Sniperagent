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

    def to_dict(self):
        return {
            "mint": self.mint,
            "symbol": self.symbol,
            "name": self.name,
            "score": self.score,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "liquidity_usd": self.liquidity_usd,
            "holder_count": self.holder_count,
            "age_minutes": self.age_minutes,
            "timestamp": self.timestamp,
        }


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