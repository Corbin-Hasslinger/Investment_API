import os

from dotenv import load_dotenv

load_dotenv()
class Settings:
    def __init__(self) -> None:
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")

        if not self.finnhub_api_key:
            raise ValueError(
                "FINNHUB_API_KEY is missing from the environment."
            )