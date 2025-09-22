# Rental Buddy API

A FastAPI-based service that provides rental property comparables ("comps") for real estate investment analysis.

## Overview

Rental Buddy helps property investors and homebuyers evaluate rental potential by finding the 5 closest rental properties that match specific bedroom/bathroom criteria. The API integrates with OpenCage for geocoding and RentCast for rental data.

## Features

- 🏠 Find rental comps by address or coordinates
- 📍 Exact bedroom/bathroom matching
- 📏 Distance-based sorting with Haversine calculation
- ⚡ In-memory caching for performance
- 🔒 Structured error handling with proper HTTP codes
- 📊 OpenAPI/Swagger documentation
- 🐳 Docker support

## Quick Start

### Prerequisites

- Python 3.11+
- OpenCage API key ([get one here](https://opencagedata.com/dashboard#geocoding))
- RentCast API key ([get one here](https://app.rentcast.io/app/api))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rental-buddy
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv       # On Windows usepy -3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the application:
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Usage

### Get Rental Comps

**POST** `/api/v1/comps`

#### Request Body

```json
{
  "address": "123 Main St, Fort Lauderdale, FL 33301",
  "bedrooms": 3,
  "bathrooms": 2.0,
  "radius_miles": 5.0,
  "days_old": "*:270"
}
```

Or use coordinates directly:

```json
{
  "latitude": 26.0052,
  "longitude": -80.2128,
  "bedrooms": 3,
  "bathrooms": 2.0
}
```

#### Response

```json
{
  "input": {
    "resolved_address": "123 Main St, Fort Lauderdale, FL 33301",
    "latitude": 26.0052,
    "longitude": -80.2128,
    "bedrooms": 3,
    "bathrooms": 2.0,
    "radius_miles": 5.0,
    "days_old": "*:270"
  },
  "comps": [
    {
      "address": "456 Oak Ave, Fort Lauderdale, FL 33301",
      "price": 2400,
      "bedrooms": 3,
      "bathrooms": 2.0,
      "square_footage": 1400,
      "distance_miles": 0.8
    }
  ]
}
```

### Other Endpoints

- **GET** `/api/v1/health` - Health check
- **GET** `/api/v1/cache/stats` - Cache statistics
- **GET** `/docs` - Interactive API documentation

## Configuration

Environment variables (see `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENCAGE_API_KEY` | ✅ | - | OpenCage geocoding API key |
| `RENTCAST_API_KEY` | ✅ | - | RentCast rental data API key |
| `RENTCAST_RADIUS_MILES_DEFAULT` | ☐ | 5 | Default search radius |
| `RENTCAST_DAYS_OLD_DEFAULT` | ☐ | *:270 | Default listing age filter |
| `REQUEST_TIMEOUT_SECONDS` | ☐ | 12 | HTTP request timeout |
| `MAX_RESULTS` | ☐ | 5 | Maximum comps returned |
| `CACHE_TTL_SECONDS` | ☐ | 600 | Cache time-to-live |
| `LOG_LEVEL` | ☐ | INFO | Logging level |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/utils/test_distance.py
```

### Code Formatting

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/
```

### Docker

```bash
# Build image
docker build -t rental-buddy .

# Run container
docker run -p 8000:8000 --env-file .env rental-buddy
```

## Project Structure

```
rental-buddy/
├── app/
│   ├── api/
│   │   └── endpoints.py          # API route definitions
│   ├── core/
│   │   └── config.py            # Configuration settings
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── services/
│   │   ├── geocoding_service.py # OpenCage integration
│   │   ├── rental_service.py    # RentCast integration
│   │   └── cache_service.py     # Caching layer
│   ├── utils/
│   │   ├── distance.py          # Haversine calculations
│   │   └── validators.py        # Input validation
│   └── main.py                  # FastAPI application
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Error Handling

The API returns structured error responses:

```json
{
  "code": "400_INVALID_INPUT",
  "message": "Provide either a full US street address or latitude & longitude"
}
```

Error codes:
- `400_INVALID_INPUT` - Invalid request parameters
- `404_NO_RESULTS` - No matching properties found
- `422_VALIDATION_ERROR` - Schema validation failed
- `429_RATE_LIMITED` - Rate limit exceeded
- `502_PROVIDER_UNAVAILABLE` - External API unavailable

## Performance

- **Response Time**: < 2 seconds typical
- **Concurrency**: Supports 100+ concurrent requests
- **Caching**: 10-minute TTL for identical queries
- **Rate Limiting**: Respects provider API limits

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please create a GitHub issue or contact the development team.
