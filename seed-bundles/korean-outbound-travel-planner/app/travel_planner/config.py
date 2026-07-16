from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")
load_dotenv(APP_DIR.parent / ".env")


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    db_path: str = os.getenv("APP_DB_PATH", str(APP_DIR / "data" / "travel_planner.db"))
    price_stale_minutes: int = int(os.getenv("PRICE_STALE_MINUTES", "15"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    amadeus_client_id: str = os.getenv("AMADEUS_CLIENT_ID", "")
    amadeus_client_secret: str = os.getenv("AMADEUS_CLIENT_SECRET", "")
    amadeus_base_url: str = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    booking_api_key: str = os.getenv("BOOKING_API_KEY", "")
    booking_affiliate_id: str = os.getenv("BOOKING_AFFILIATE_ID", "")
    booking_base_url: str = os.getenv("BOOKING_BASE_URL", "https://demandapi-sandbox.booking.com/3.2")
    skyscanner_api_key: str = os.getenv("SKYSCANNER_API_KEY", "")
    skyscanner_base_url: str = os.getenv("SKYSCANNER_BASE_URL", "https://partners.api.skyscanner.net")

    @property
    def amadeus_enabled(self) -> bool:
        return bool(self.amadeus_client_id and self.amadeus_client_secret)

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_maps_api_key)

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def booking_enabled(self) -> bool:
        return bool(self.booking_api_key and self.booking_affiliate_id)

    @property
    def skyscanner_enabled(self) -> bool:
        return bool(self.skyscanner_api_key)



settings = Settings()
