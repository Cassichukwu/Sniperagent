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
