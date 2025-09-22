import hashlib
import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        # Create TTL cache with max 100 entries and configurable TTL
        self.cache = TTLCache(maxsize=100, ttl=settings.cache_ttl_seconds)

    def _generate_cache_key(
        self,
        latitude: float,
        longitude: float,
        bedrooms: int,
        bathrooms: float,
        radius_miles: float,
        days_old: str,
    ) -> str:
        """
        Generate a cache key based on search parameters
        """
        key_data = {
            "lat": round(latitude, 6),  # Round to ~0.1m precision
            "lng": round(longitude, 6),
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "radius": radius_miles,
            "days_old": days_old,
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(
        self,
        latitude: float,
        longitude: float,
        bedrooms: int,
        bathrooms: float,
        radius_miles: float,
        days_old: str,
    ) -> Optional[Any]:
        """
        Get cached result for the given search parameters
        """
        cache_key = self._generate_cache_key(
            latitude, longitude, bedrooms, bathrooms, radius_miles, days_old
        )

        result = self.cache.get(cache_key)
        if result:
            logger.info(f"Cache hit for key: {cache_key}")
        else:
            logger.info(f"Cache miss for key: {cache_key}")

        return result

    def set(
        self,
        latitude: float,
        longitude: float,
        bedrooms: int,
        bathrooms: float,
        radius_miles: float,
        days_old: str,
        value: Any,
    ) -> None:
        """
        Cache the result for the given search parameters
        """
        cache_key = self._generate_cache_key(
            latitude, longitude, bedrooms, bathrooms, radius_miles, days_old
        )

        self.cache[cache_key] = value
        logger.info(f"Cached result for key: {cache_key}")

    def clear(self) -> None:
        """
        Clear all cached entries
        """
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """
        Get cache statistics
        """
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hits": getattr(self.cache, "hits", 0),
            "misses": getattr(self.cache, "misses", 0),
        }
