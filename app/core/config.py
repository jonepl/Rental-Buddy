from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    opencage_api_key: str
    rentcast_api_key: str

    # API Endpoints
    rentcast_url: str = "https://api.rentcast.io/v1/listings/rental/long-term"
    opencage_url: str = "https://api.opencagedata.com/geocode/v1/json"

    # Configuration
    rentcast_radius_miles_default: float = 5.0
    rentcast_days_old_default: str = "*:270"
    rentcast_request_cap: int = 100
    request_timeout_seconds: int = 12
    max_results: int = 5
    rate_limit_rps: int = 20
    cache_ttl_seconds: int = 600
    log_level: str = "INFO"
    environment: str = "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
