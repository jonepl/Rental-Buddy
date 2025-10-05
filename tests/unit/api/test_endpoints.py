from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import CompProperty, ErrorCode

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "service": "rental-buddy"}


def test_get_cache_stats():
    with patch(
        "app.api.endpoints.cache_service.get_stats",
        return_value={"hits": 1, "misses": 2, "size": 3},
    ):
        resp = client.get("/api/v1/cache/stats")

        assert resp.status_code == 200
        assert resp.json() == {"hits": 1, "misses": 2, "size": 3}


class TestCompsEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.p_resolve = patch(
            "app.api.endpoints._resolve_location", new_callable=AsyncMock
        )
        self.p_cache = patch("app.api.endpoints.cache_service")
        self.p_rental = patch("app.api.endpoints.rental_service")

        self.m_resolve = self.p_resolve.start()
        self.m_cache = self.p_cache.start()
        self.m_rental = self.p_rental.start()

        # defaults
        self.m_resolve.return_value = (30.2672, -97.7431, "123 Main St, Austin, TX")
        self.m_cache.get.return_value = None
        comp = CompProperty(
            address="456 Oak Ave, Austin, TX 78702",
            city="Austin",
            state="TX",
            zip_code="78702",
            county="Travis",
            longitude=-97.720118,
            latitude=30.263412,
            price=2450,
            bedrooms=2,
            bathrooms=2.0,
            square_footage=1025,
            distance_miles=1.4,
        )
        self.m_rental.get_rental_comps = AsyncMock(return_value=([comp]))
        self.m_rental.get_mock_comps = AsyncMock(return_value=[comp])

        yield
        patch.stopall()

    def test_success_returns_comps_with_address(self):
        req = {
            "address": "123 Main St, Austin, TX",
            "radius_miles": 5.0,
        }

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 200
        data = resp.json()
        assert "input" in data and "comps" in data
        assert len(data["comps"]) == 1
        assert data["comps"][0]["address"].startswith("456 Oak Ave")

    def test_success_returns_comps_with_lat_lng(self):
        req = {
            "latitude": 30.2672,
            "longitude": -97.7431,
            "radius_miles": 5.0,
        }

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 200
        data = resp.json()
        assert "input" in data and "comps" in data
        assert len(data["comps"]) == 1
        assert data["comps"][0]["latitude"] == 30.263412
        assert data["comps"][0]["longitude"] == -97.720118

    def test_cache_hit_returns_cached_payload(self):
        cached = {
            "input": {
                "resolved_address": "123 Main St, Austin, TX",
                "bedrooms": None,
                "bathrooms": None,
                "days_old": None,
                "latitude": 30.2672,
                "longitude": -97.7431,
                "radius_miles": 5.0,
            },
            "comps": [
                {
                    "address": "789 Pine St, Austin, TX 78703",
                    "city": "Austin",
                    "state": "TX",
                    "zip_code": "78703",
                    "county": "Travis",
                    "longitude": -97.750000,
                    "latitude": 30.270000,
                    "price": 2300,
                    "bedrooms": 2,
                    "bathrooms": 1.5,
                    "square_footage": 900,
                    "distance_miles": 1.0,
                }
            ],
        }
        self.m_cache.get.return_value = cached
        req = {"address": "123 Main St", "latitude": 30.2672, "longitude": -97.7431, "radius_miles": 5.0}

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 200
        assert resp.json() == cached

    def test_invalid_location_returns_400(self):
        self.m_resolve.return_value = (None, None, "Invalid coordinates provided")
        req = {"address": "bad", "bedrooms": 2, "bathrooms": 1.5, "radius_miles": 5.0}

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 400
        body: dict = resp.json()
        assert body["detail"]["code"] == ErrorCode.INVALID_INPUT

    def test_rental_error_falls_back_to_mock(self):
        self.m_rental.get_rental_comps = AsyncMock(return_value=([]))
        req = {"address": "123 Main St", "bedrooms": 2, "bathrooms": 1.5, "radius_miles": 5.0}

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 200
        assert len(resp.json()["comps"]) == 1

    def test_no_results_anywhere_returns_404(self):
        self.m_rental.get_rental_comps = AsyncMock(return_value=([]))
        self.m_rental.get_mock_comps = AsyncMock(return_value=[])
        req = {"address": "123 Main St", "bedrooms": 2, "bathrooms": 1.5, "radius_miles": 5.0}

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["code"] == ErrorCode.NO_RESULTS

    def test_validation_error_422_for_bad_bathrooms(self):
        req = {"address": "123 Main St", "bedrooms": 2, "bathrooms": 1.25, "radius_miles": 5.0}

        resp = client.post("/api/v1/comps", json=req)

        assert resp.status_code == 422
