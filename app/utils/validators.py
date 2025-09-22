import re
from typing import Optional


def is_valid_us_address(address: str) -> bool:
    """
    Basic validation for US street addresses
    Should contain street number, street name, city, state, and optionally zip
    """
    if not address or len(address.strip()) < 10:
        return False

    # Basic pattern: number + street + city + state (+ optional zip)
    # This is a simplified check - real validation would be more complex
    pattern = r"^\d+\s+.+,\s*.+,\s*[A-Z]{2}(\s+\d{5}(-\d{4})?)?$"
    return bool(re.match(pattern, address.strip(), re.IGNORECASE))


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate latitude and longitude are within valid ranges
    """
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)


def normalize_bathrooms(bathrooms: float) -> float:
    """
    Ensure bathrooms is in 0.5 increments and return normalized value
    """
    return round(bathrooms * 2) / 2
