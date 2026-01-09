# Natural Disaster Distance Monitor - Python Implementation

Python implementation of the Natural Disaster Distance Monitor CLI tool.

## Requirements

- Python 3.10 or higher
- No database dependencies
- No AWS dependencies

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Usage

### Single Location Query

```bash
# Find all disasters within 100 miles of Houston, TX
python main.py --lat 29.7604 --lon -95.3698

# With a custom name
python main.py --lat 29.7604 --lon -95.3698 --name "Houston TX"

# Custom radius (50 miles)
python main.py --lat 29.7604 --lon -95.3698 --radius 50

# Filter to specific disaster types
python main.py --lat 29.7604 --lon -95.3698 --type hurricanes --type wildfires
```

### Batch Query from CSV

```bash
# Query multiple locations
python main.py --csv ../shared/data/test_locations.csv

# With custom radius
python main.py --csv ../shared/data/test_locations.csv --radius 50
```

### Output Options

```bash
# JSON to stdout
python main.py --lat 29.7604 --lon -95.3698 --json

# JSON to file
python main.py --lat 29.7604 --lon -95.3698 --output results.json

# Quiet mode (suppress progress messages)
python main.py --csv ../shared/data/test_locations.csv --quiet
```

## Project Structure

```
python/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── main.py               # CLI entry point
└── disasters/            # Core library
    ├── __init__.py       # Public API exports
    ├── models.py         # Data classes
    ├── utils.py          # Shared utilities
    ├── hurricanes.py     # Hurricane API client
    ├── tornadoes.py      # Tornado API client
    └── wildfires.py      # Wildfire API client
```

## Library Usage

You can also use the library directly in Python code:

```python
from disasters import get_nearby_disasters, DisasterType

# Query all disaster types
results = get_nearby_disasters(
    latitude=29.7604,
    longitude=-95.3698,
    radius_miles=100
)

print(f"Found {results.total_disasters} disasters")

for hurricane in results.hurricanes:
    print(f"  {hurricane.name}: {hurricane.distance_miles:.1f} miles")

# Query specific types only
results = get_nearby_disasters(
    latitude=29.7604,
    longitude=-95.3698,
    disaster_types=[DisasterType.HURRICANE, DisasterType.WILDFIRE]
)

# Batch query from CSV
from disasters import query_locations_from_csv

all_results = query_locations_from_csv(
    csv_path='../shared/data/test_locations.csv',
    radius_miles=100
)

for location_result in all_results:
    print(f"{location_result.location.name}: {location_result.total_disasters} disasters")
```

## Dependencies

This implementation uses only:

- `pandas` - Data manipulation
- `numpy` - Vectorized calculations
- `requests` - HTTP client

**Explicitly NOT used:**
- ❌ `boto3` (no AWS)
- ❌ `pyodbc` (no MSSQL)
- ❌ `sqlalchemy` (no database ORM)

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=disasters
```

### Code Style

This project follows PEP 8 style guidelines:

```bash
# Format code
black disasters/ main.py

# Check types
mypy disasters/ main.py
```

