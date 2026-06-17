"""config.py - loads .env settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Try several locations for .env to be safe
for candidate in [Path(__file__).parent / ".env", Path.cwd() / ".env"]:
    if candidate.exists():
        load_dotenv(candidate, override=True)
        break


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
