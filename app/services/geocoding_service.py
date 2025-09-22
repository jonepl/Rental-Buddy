import logging
from typing import Optional, Tuple

import httpx

from app.core.config import settings
from app.models.schemas import ErrorCode

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.api_key = settings.opencage_api_key
        self.base_url = settings.opencage_url
        self.timeout = settings.request_timeout_seconds

    async def geocode_address(
        self, address: str
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Geocode an address using OpenCage API

        Returns:
            Tuple of (latitude, longitude, formatted_address) or (None, None, error_message)
        """
        if not address or not address.strip():
            return None, None, "Address cannot be empty"

        params = {
            "q": address.strip(),
            "key": self.api_key,
            "countrycode": "us",
            "limit": 1,
            "no_annotations": 1,
            "min_confidence": 9,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Geocoding address: {address}")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if not data.get("results"):
                    return None, None, "Address not found or invalid"

                result = data["results"][0]
                geometry = result.get("geometry", {})

                latitude = geometry.get("lat")
                longitude = geometry.get("lng")
                formatted_address = result.get("formatted")

                if latitude is None or longitude is None:
                    return None, None, "Could not extract coordinates from address"

                logger.info(f"Geocoded to: {latitude}, {longitude}")
                return float(latitude), float(longitude), formatted_address

        except httpx.TimeoutException:
            logger.error(f"Timeout geocoding address: {address}")
            return None, None, "Geocoding service timeout"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Rate limited by geocoding service")
                return None, None, "Rate limited by geocoding service"
            logger.error(f"HTTP error geocoding address: {e}")
            return None, None, f"Geocoding service error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Unexpected error geocoding address: {e}")
            return None, None, "Geocoding service unavailable"
