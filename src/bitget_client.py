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
