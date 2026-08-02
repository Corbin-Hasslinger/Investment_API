import os


class Settings:
    finnhub_api_key: str = os.getenv("FINNHUB_API_KEY", "")