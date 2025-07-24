import json
from pathlib import Path
from loguru import logger

class CookieManager:
    def __init__(self, cookies_path="data_dump/cookies.json"):
        self.cookies_path = Path(cookies_path)
        self.cookies = {}

    def load(self):
        if self.cookies_path.exists():
            self.cookies = json.loads(self.cookies_path.read_text(encoding="utf-8"))
            logger.info(f"Loaded {len(self.cookies)} cookies: {list(self.cookies.keys())}")
            return True
        logger.error("No cookies found!")
        return False

    def all(self):
        if not self.cookies:
            self.load()
        return self.cookies.copy()