import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.core.constants import HttpStatus
from app.models.schemas import (CompsRequest, CompsResponse, ErrorCode,
                                ErrorResponse, InputSummary)
from app.services.cache_service import CacheService
from app.services.geocoding_service import GeocodingService
from app.services.rental_service import RentalService
from app.utils.validators import is_valid_us_address, validate_coordinates

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
geocoding_service = GeocodingService()
rental_service = RentalService()
cache_service = CacheService()


@router.post("/comps", response_model=CompsResponse)
async def get_rental_comps(request: CompsRequest):
    """
    Get rental comparables for a given property

    Returns rental properties that match the bedroom/bathroom criteria,
    sorted by distance from the subject property.
    """
    try:
        # Resolve the address to coordinates
        latitude, longitude, resolved_address = await _resolve_location(request)

        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    code=ErrorCode.INVALID_INPUT,
                    message=resolved_address or "Could not resolve location",
                ).model_dump(),
            )

        # Check cache first
        cached_result = cache_service.get(
            latitude,
            longitude,
            request.bedrooms,
            request.bathrooms,
            request.radius_miles,
            request.days_old,
        )

        if cached_result:
            logger.info("Returning cached result")
            return cached_result

        # Fetch rental comps
        comps = await rental_service.get_rental_comps(
            latitude=latitude,
            longitude=longitude,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            radius_miles=request.radius_miles,
            days_old=request.days_old,
        )

        # If no results from real API or error occurred, try mock data
        if not comps:
            logger.warning("No rental comps found, using mock data")
            comps = await rental_service.get_mock_comps(
                latitude, longitude, request.bedrooms, request.bathrooms
            )

            if not comps:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        code=ErrorCode.NO_RESULTS,
                        message="No rental comps found, even with mock data",
                    ).model_dump(),
                )

        # Build response
        response = CompsResponse(
            input=InputSummary(
                resolved_address=resolved_address,
                latitude=latitude,
                longitude=longitude,
                bedrooms=request.bedrooms,
                bathrooms=request.bathrooms,
                radius_miles=request.radius_miles,
                days_old=request.days_old,
            ),
            comps=comps,
        )

        # Cache the result
        cache_service.set(
            latitude,
            longitude,
            request.bedrooms,
            request.bathrooms,
            request.radius_miles,
            request.days_old,
            response,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_rental_comps: {e}")
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code=ErrorCode.PROVIDER_UNAVAILABLE, message="Internal server error"
            ).model_dump(),
        )


async def _resolve_location(
    request: CompsRequest,
) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Resolve location from either coordinates or address

    Returns: (latitude, longitude, resolved_address)
    """
    # If coordinates provided, use them directly
    if request.latitude is not None and request.longitude is not None:
        if not validate_coordinates(request.latitude, request.longitude):
            return None, None, "Invalid coordinates provided"

        # Use provided address or generate a placeholder
        resolved_address = (
            request.address or f"Location at {request.latitude}, {request.longitude}"
        )
        return request.latitude, request.longitude, resolved_address

    # Otherwise, geocode the address
    if not request.address:
        return None, None, "Must provide either address or latitude & longitude"

    if not is_valid_us_address(request.address):
        return None, None, "Invalid US address format"

    latitude, longitude, error_or_address = await geocoding_service.geocode_address(
        request.address
    )

    if latitude is None:
        return None, None, error_or_address

    return latitude, longitude, error_or_address


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rental-buddy"}


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics (for debugging)"""
    return cache_service.get_stats()
