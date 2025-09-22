import pytest

from app.utils.validators import (is_valid_us_address, normalize_bathrooms,
                                  validate_coordinates)


def test_is_valid_us_address():
    """Test US address validation"""
    # Valid addresses
    assert is_valid_us_address("123 Main St, Fort Lauderdale, FL 33301")
    assert is_valid_us_address("456 Oak Avenue, Miami, FL")
    assert is_valid_us_address("789 Pine Street, Orlando, FL 32801-1234")

    # Invalid addresses
    assert not is_valid_us_address("")
    assert not is_valid_us_address("Miami, FL")  # No street address
    assert not is_valid_us_address("123")  # Too short
    assert not is_valid_us_address("Main Street")  # No number


def test_validate_coordinates():
    """Test coordinate validation"""
    # Valid coordinates
    assert validate_coordinates(40.7128, -74.0060)  # NYC
    assert validate_coordinates(0, 0)  # Equator/Prime Meridian
    assert validate_coordinates(90, 180)  # Max values
    assert validate_coordinates(-90, -180)  # Min values

    # Invalid coordinates
    assert not validate_coordinates(91, 0)  # Latitude too high
    assert not validate_coordinates(-91, 0)  # Latitude too low
    assert not validate_coordinates(0, 181)  # Longitude too high
    assert not validate_coordinates(0, -181)  # Longitude too low


def test_normalize_bathrooms():
    """Test bathroom normalization to 0.5 increments"""
    assert normalize_bathrooms(1.0) == 1.0
    assert normalize_bathrooms(1.5) == 1.5
    assert normalize_bathrooms(2.0) == 2.0
    assert normalize_bathrooms(2.3) == 2.5  # Rounds to nearest 0.5
    assert normalize_bathrooms(2.7) == 2.5  # Rounds to nearest 0.5
