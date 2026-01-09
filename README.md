# Natural Disaster Distance Monitor

A multi-language CLI tool to find hurricanes, tornadoes, and wildfires near any location.

## Overview

This project provides real-time natural disaster proximity monitoring by querying public APIs from NOAA and other government agencies. It's designed to be implemented in multiple programming languages with identical functionality.

## Features

- 🌀 **Hurricane Tracking** - Active hurricanes from NOAA/NHC
- 🌪️ **Tornado Reports** - Recent tornado damage assessments
- 🔥 **Wildfire Perimeters** - Active fire boundaries from WFIGS
- 📍 **Distance Calculation** - Haversine formula for accurate distances
- 📄 **Batch Processing** - Query multiple locations via CSV file
- 🔄 **Multi-Language** - Same functionality in Python, Rust, and more

## Project Structure

```
natural-disaster-distance-monitor/
├── README.md                    # This file
├── IMPLEMENTATION_PLAN.md       # Detailed implementation spec
│
├── shared/                      # Shared across all languages
│   ├── data/
│   │   └── test_locations.csv   # Sample test data
│   └── specs/
│       ├── api-endpoints.md     # External API documentation
│       └── data-models.md       # Standard data model definitions
│
├── python/                      # Python implementation
│   ├── README.md                # Python-specific instructions
│   ├── requirements.txt
│   ├── main.py                  # CLI entry point
│   └── disasters/               # Core library
│
└── rust/                        # Rust implementation (planned)
    ├── README.md
    ├── Cargo.toml
    └── src/
```

## Language Implementations

| Language | Status | Directory | Notes |
|----------|--------|-----------|-------|
| Python | 🚧 In Progress | [`python/`](python/) | Primary implementation |
| Rust | 📋 Planned | [`rust/`](rust/) | High-performance version |

## Quick Start

### Python

```bash
cd python
pip install -r requirements.txt

# Single location query
python main.py --lat 29.7604 --lon -95.3698 --name "Houston TX"

# Batch query from CSV
python main.py --csv ../shared/data/test_locations.csv

# JSON output
python main.py --lat 29.7604 --lon -95.3698 --json
```

### Rust (Coming Soon)

```bash
cd rust
cargo build --release

# Single location query
./target/release/disaster-monitor --lat 29.7604 --lon -95.3698
```

## CLI Interface

All language implementations support the same command-line interface:

```
Usage: <program> [OPTIONS]

Options:
  --lat FLOAT          Latitude in decimal degrees
  --lon FLOAT          Longitude in decimal degrees
  --name STRING        Location name (optional)
  --csv FILE           CSV file with locations
  --radius FLOAT       Search radius in miles (default: 100)
  --type TYPE          Disaster type filter (hurricanes, tornadoes, wildfires)
  --json               Output as JSON
  --output FILE        Write JSON to file
  --help               Show help message
```

## Data Sources

| Disaster | Provider | Update Frequency |
|----------|----------|------------------|
| Hurricanes | NOAA/NHC | Every 6 hours |
| Tornadoes | NOAA DAT | As reported |
| Wildfires | WFIGS | Daily |

## Example Output

```
=== Natural Disaster Monitor ===
Location: Houston TX (29.7604, -95.3698)
Radius: 100 miles

HURRICANES (1 found)
  • Hurricane Milton - 45.2 miles SW
    Category 2, Max Wind: 100 mph
    Moving NW at 12 mph

TORNADOES (0 found)
  No recent tornadoes within 100 miles.

WILDFIRES (0 found)
  No active wildfires within 100 miles.
```

## Contributing

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed implementation specifications.

When adding a new language implementation:
1. Create a new directory (e.g., `go/`, `typescript/`)
2. Follow the data models in `shared/specs/data-models.md`
3. Use the API endpoints in `shared/specs/api-endpoints.md`
4. Ensure CLI matches the standard interface
5. Test against `shared/data/test_locations.csv`

## License

MIT License - See LICENSE file for details.

