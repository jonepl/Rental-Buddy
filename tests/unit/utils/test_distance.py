import pytest

from app.utils.distance import haversine_distance


def test_haversine_distance_same_point():
    """Test distance between same point is 0"""
    distance = haversine_distance(40.7128, -74.0060, 40.7128, -74.0060)
    assert distance == 0.0


def test_haversine_distance_known_cities():
    """Test distance between known cities"""
    # NYC to Philadelphia (approximately 95 miles)
    nyc_lat, nyc_lng = 40.7128, -74.0060
    philly_lat, philly_lng = 39.9526, -75.1652

    distance = haversine_distance(nyc_lat, nyc_lng, philly_lat, philly_lng)

    # Should be approximately 95 miles, allow some tolerance
    assert 79.5 <= distance <= 81.5


def test_haversine_distance_rounding():
    """Test that distance is rounded to 1 decimal place"""
    # Small distance that would have many decimal places
    distance = haversine_distance(40.7128, -74.0060, 40.7129, -74.0061)

    # Check that result has at most 1 decimal place
    assert len(str(distance).split(".")[-1]) <= 1
