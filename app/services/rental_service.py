import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.models.schemas import CompProperty
from app.utils.distance import haversine_distance

logger = logging.getLogger(__name__)


class RentalService:
    def __init__(self):
        self.api_key = settings.rentcast_api_key
        self.base_url = settings.rentcast_url
        self.timeout = settings.request_timeout_seconds
        self.request_cap = settings.rentcast_request_cap

    async def get_rental_comps(
        self,
        latitude: float,
        longitude: float,
        bedrooms: int,
        bathrooms: float,
        radius_miles: float = 5.0,
        days_old: str = "*:270",
    ) -> List[CompProperty]:
        """
        Fetch rental listings from RentCast API and return filtered/sorted comps

        Returns:
            List of CompProperty objects, sorted by distance then price then sqft
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius_miles or settings.rentcast_radius_miles_default,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "daysOld": days_old or settings.rentcast_days_old_default,
            "limit": min(
                50, self.request_cap
            ),  # Use request cap but max 50 per API limits
        }

        headers = {"X-Api-Key": self.api_key, "accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(
                    f"Fetching rentals for {latitude}, {longitude} - {bedrooms}br/{bathrooms}ba"
                )
                response = await client.get(
                    self.base_url, params=params, headers=headers
                )
                response.raise_for_status()

                listings = response.json()
                # listings = data.get("listings", [])

                # Process and filter listings
                comps = []
                seen_addresses = set()

                for listing in listings:
                    comp = self._process_listing(
                        listing, latitude, longitude, bedrooms, bathrooms
                    )
                    if comp and comp.address.lower() not in seen_addresses:
                        comps.append(comp)
                        seen_addresses.add(comp.address.lower())

                # Sort by distance, then price (asc), then sqft (desc)
                comps.sort(
                    key=lambda x: (x.distance_miles, x.price, -(x.square_footage or 0))
                )

                # Return top 5
                return comps[: settings.max_results]

        except httpx.TimeoutException:
            logger.error("Timeout fetching rental data")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Rate limited by rental service")
                return []
            logger.error(f"HTTP error fetching rentals: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching rentals: {e}")
            return []

    def _process_listing(
        self,
        listing: Dict[Any, Any],
        subject_lat: float,
        subject_lng: float,
        target_bedrooms: int,
        target_bathrooms: float,
    ) -> Optional[CompProperty]:
        """
        Process a single listing from RentCast API into a CompProperty

        Returns None if listing should be filtered out
        """
        try:
            # Extract required fields
            price = listing.get("price")
            bedrooms = listing.get("bedrooms")
            bathrooms = listing.get("bathrooms")
            address = listing.get("formattedAddress") or listing.get("address")
            latitude = listing.get("latitude")
            longitude = listing.get("longitude")
            square_footage = listing.get("squareFootage")

            # Filter out listings with missing critical data
            if not all([price, address, latitude, longitude]):
                return None

            # Ensure exact bed/bath match
            if bedrooms < target_bedrooms or bathrooms < target_bathrooms:
                return None

            # Calculate distance
            distance = haversine_distance(subject_lat, subject_lng, latitude, longitude)

            return CompProperty(
                address=address,
                price=int(price),
                bedrooms=int(bedrooms),
                bathrooms=float(bathrooms),
                square_footage=int(square_footage) if square_footage else None,
                distance_miles=distance,
            )

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Error processing listing: {e}")
            return None

    async def get_mock_comps(
        self, latitude: float, longitude: float, bedrooms: int, bathrooms: float
    ) -> List[CompProperty]:
        """
        Return mock rental comps for testing when real API is unavailable
        """
        mock_listings = [
            {
                "address": f"123 Mock St, Test City, FL 33301",
                "price": 2400,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "square_footage": 1400,
                "distance_miles": 0.8,
            },
            {
                "address": f"456 Sample Ave, Test City, FL 33301",
                "price": 2300,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "square_footage": 1350,
                "distance_miles": 1.2,
            },
            {
                "address": f"789 Demo Blvd, Test City, FL 33301",
                "price": 2500,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "square_footage": 1500,
                "distance_miles": 1.5,
            },
        ]

        return [CompProperty(**listing) for listing in mock_listings]
