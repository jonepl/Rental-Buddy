from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.services.geocoding_service import GeocodingService


class TestGeocodingService:
    """Test the GeocodingService class"""

    @pytest.fixture
    def geocoding_service(self):
        return GeocodingService()

    @pytest.fixture
    def mock_success_response(self):
        return {
            "results": [
                {
                    "geometry": {"lat": 30.2672, "lng": -97.7431},
                    "formatted": "123 Main St, Austin, TX 78701, USA",
                }
            ]
        }

    @pytest.fixture
    def mock_no_results_response(self):
        return {"results": []}

    @pytest.mark.asyncio
    async def test_geocode_address_success(
        self, geocoding_service: GeocodingService, mock_success_response
    ):
        """Test successful geocoding of an address"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_success_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            test_address = "123 Main St, Austin, TX"
            lat, lng, formatted_address = await geocoding_service.geocode_address(
                test_address
            )

            # Verify the correct URL and params were used
            mock_client.get.assert_awaited_once()
            args, kwargs = mock_client.get.await_args
            assert args[0] == settings.opencage_url
            assert kwargs["params"]["q"] == test_address

            # Verify the response was parsed correctly
            assert lat == 30.2672
            assert lng == -97.7431
            assert formatted_address == "123 Main St, Austin, TX 78701, USA"

    @pytest.mark.asyncio
    async def test_geocode_address_no_results(
        self, geocoding_service: GeocodingService, mock_no_results_response
    ):
        """Test geocoding when no results are found"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_no_results_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            lat, lng, error = await geocoding_service.geocode_address(
                "Nonexistent Address, ZZ"
            )

            assert lat is None
            assert lng is None
            assert "not found" in error.lower()

    @pytest.mark.asyncio
    async def test_geocode_address_empty_address(
        self, geocoding_service: GeocodingService
    ):
        """Test geocoding with an empty address"""
        lat, lng, error = await geocoding_service.geocode_address("")

        assert lat is None
        assert lng is None
        assert "Address cannot be empty" in error

    @pytest.mark.asyncio
    async def test_geocode_address_invalid_response(
        self, geocoding_service: GeocodingService
    ):
        """Test handling of invalid API response"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "invalid": "response"
            }  # Missing expected fields
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            lat, lng, error = await geocoding_service.geocode_address("123 Main St")

            assert lat is None
            assert lng is None
            assert "could not extract" in error.lower() or "invalid" in error.lower()

    @pytest.mark.asyncio
    async def test_geocode_address_http_error(
        self, geocoding_service: GeocodingService
    ):
        """Test handling of HTTP errors"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            # Simulate a 404 response causing raise_for_status to raise HTTPStatusError
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
            )
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            lat, lng, error = await geocoding_service.geocode_address("123 Main St")

            assert lat is None
            assert lng is None
            assert (
                "not found" in error.lower()
                or "geocoding service error: 404" in error.lower()
            )

    @pytest.mark.asyncio
    async def test_geocode_address_timeout(self, geocoding_service: GeocodingService):
        """Test handling of timeout errors"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            lat, lng, error = await geocoding_service.geocode_address("123 Main St")

            assert lat is None
            assert lng is None
            assert "timeout" in error.lower() or "timed out" in error.lower()
