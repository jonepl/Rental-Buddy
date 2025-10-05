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
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        radius_miles: float = 5.0,
        days_old: Optional[str] = None,
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
            "daysOld": days_old or settings.rentcast_days_old_default,
            "limit": min(50, self.request_cap),
        }
        # Only include bed/bath filters if provided
        if bedrooms is not None:
            params["bedrooms"] = bedrooms
        if bathrooms is not None:
            params["bathrooms"] = bathrooms
        if days_old is not None:
            params["daysOld"] = days_old

        headers = {"X-Api-Key": self.api_key, "accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(
                    f"Fetching rentals for {latitude}, {longitude}"
                    + (f" - {bedrooms}br" if bedrooms is not None else "")
                    + (f"/{bathrooms}ba" if bathrooms is not None else "")
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

                # Return up to configured max results
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
        target_bedrooms: Optional[int],
        target_bathrooms: Optional[float],
    ) -> Optional[CompProperty]:
        """
        Process a single listing from RentCast API into a CompProperty

        Returns None if listing should be filtered out
        """
        try:
            # Extract required fields
            address = listing.get("formattedAddress") or listing.get("address")
            city = listing.get("city")
            state = listing.get("state")
            zip_code = listing.get("zipCode")
            county = listing.get("county")
            latitude = listing.get("latitude")
            longitude = listing.get("longitude")
            price = listing.get("price")
            bedrooms = listing.get("bedrooms")
            bathrooms = listing.get("bathrooms")
            square_footage = listing.get("squareFootage")

            # Filter out listings with missing critical data
            if not all([price, address, latitude, longitude]):
                return None

            # Ensure bed/bath minimums if provided. Guard against missing values in provider data.
            if target_bedrooms is not None and (
                bedrooms is None or bedrooms < target_bedrooms
            ):
                return None
            if target_bathrooms is not None and (
                bathrooms is None or bathrooms < target_bathrooms
            ):
                return None

            # Calculate distance
            distance = haversine_distance(subject_lat, subject_lng, latitude, longitude)

            return CompProperty(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                county=county,
                latitude=latitude,
                longitude=longitude,
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
        self, latitude: float, longitude: float, bedrooms: Optional[int], bathrooms: Optional[float]
    ) -> List[CompProperty]:
        """
        Return mock rental comps for testing when real API is unavailable
        """
        mock_listings = [
            {
                "address": f"123 Mock St, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2400,
                "bedrooms": bedrooms if bedrooms is not None else 2,
                "bathrooms": bathrooms if bathrooms is not None else 1.5,
                "square_footage": 1400,
                "distance_miles": 0.8,
            },
            {
                "address": f"456 Sample Ave, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2300,
                "bedrooms": bedrooms if bedrooms is not None else 3,
                "bathrooms": bathrooms if bathrooms is not None else 2.0,
                "square_footage": 1350,
                "distance_miles": 1.2,
            },
            {
                "address": f"789 Demo Blvd, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2500,
                "bedrooms": bedrooms if bedrooms is not None else 1,
                "bathrooms": bathrooms if bathrooms is not None else 1.0,
                "square_footage": 1500,
                "distance_miles": 1.5,
            },
        ]

        return [CompProperty(**listing) for listing in mock_listings]
