# Natural Disaster Data Models

This document defines the standard data models that all language implementations must use.

## Core Types

### DisasterType (Enum)
```
HURRICANE = "hurricane"
TORNADO = "tornado"
WILDFIRE = "wildfire"
```

### Location
Represents a query location (from CLI or CSV).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Location name/identifier |
| `latitude` | float | Yes | Decimal degrees (-90 to 90) |
| `longitude` | float | Yes | Decimal degrees (-180 to 180) |

---

## Disaster Results

### DisasterResult (Base)
All disaster types inherit from this base structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `disaster_type` | DisasterType | Yes | Type of disaster |
| `name` | string | Yes | Name/identifier of disaster |
| `distance_miles` | float | Yes | Distance from query location |
| `latitude` | float | Yes | Disaster center latitude |
| `longitude` | float | Yes | Disaster center longitude |
| `severity` | string | Yes | Human-readable severity |
| `details` | object | No | Type-specific additional data |
| `last_updated` | datetime | No | When data was fetched |

### HurricaneResult
Extends DisasterResult with hurricane-specific fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | HurricaneCategory | No | Saffir-Simpson category |
| `max_wind_mph` | float | No | Maximum sustained wind |
| `movement_direction` | string | No | Direction of movement (N, NE, etc.) |
| `movement_speed_mph` | float | No | Forward speed |
| `advisory_number` | string | No | NHC advisory number |
| `basin` | string | No | Ocean basin (AL, EP, etc.) |
| `inside_cone` | boolean | No | Is location inside forecast cone |

### TornadoResult
Extends DisasterResult with tornado-specific fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ef_scale` | TornadoScale | No | Enhanced Fujita scale rating |
| `max_wind_mph` | float | No | Estimated maximum wind |
| `path_length_miles` | float | No | Tornado path length |
| `path_width_yards` | float | No | Tornado path width |
| `fatalities` | integer | No | Number of fatalities |
| `injuries` | integer | No | Number of injuries |
| `storm_date` | datetime | No | Date/time of tornado |

### WildfireResult
Extends DisasterResult with wildfire-specific fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `size_category` | WildfireSize | No | Size classification |
| `acres` | float | No | Fire size in acres |
| `containment_percent` | float | No | Percent contained (0-100) |
| `inside_perimeter` | boolean | No | Is location inside fire perimeter |

---

## Severity Enums

### HurricaneCategory
Based on Saffir-Simpson Hurricane Wind Scale.

| Value | Wind Speed (mph) | Description |
|-------|------------------|-------------|
| `TD` | < 39 | Tropical Depression |
| `TS` | 39-73 | Tropical Storm |
| `1` | 74-95 | Category 1 (Minimal) |
| `2` | 96-110 | Category 2 (Moderate) |
| `3` | 111-129 | Category 3 (Extensive) |
| `4` | 130-156 | Category 4 (Extreme) |
| `5` | 157+ | Category 5 (Catastrophic) |

### TornadoScale
Enhanced Fujita Scale.

| Value | Wind Speed (mph) | Description |
|-------|------------------|-------------|
| `EF0` | 65-85 | Light damage |
| `EF1` | 86-110 | Moderate damage |
| `EF2` | 111-135 | Significant damage |
| `EF3` | 136-165 | Severe damage |
| `EF4` | 166-200 | Devastating damage |
| `EF5` | 200+ | Incredible damage |

### WildfireSize
Based on incident size classifications.

| Value | Acres | Description |
|-------|-------|-------------|
| `small` | < 100 | Small fire |
| `medium` | 100-1,000 | Medium fire |
| `large` | 1,000-10,000 | Large fire |
| `major` | 10,000-100,000 | Major fire |
| `mega` | 100,000+ | Megafire |

---

## Aggregated Results

### LocationResults
Results for a single location query.

| Field | Type | Description |
|-------|------|-------------|
| `location` | Location | The queried location |
| `hurricanes` | HurricaneResult[] | List of nearby hurricanes |
| `tornadoes` | TornadoResult[] | List of nearby tornadoes |
| `wildfires` | WildfireResult[] | List of nearby wildfires |
| `query_time` | datetime | When the query was executed |

**Computed Properties:**
- `total_disasters`: Sum of all disaster counts

---

## JSON Output Schema

All implementations must produce JSON output matching this schema:

```json
{
  "query_time": "2025-01-08T12:00:00Z",
  "location": {
    "name": "Houston TX",
    "latitude": 29.7604,
    "longitude": -95.3698
  },
  "radius_miles": 100,
  "results": {
    "hurricanes": [
      {
        "disaster_type": "hurricane",
        "name": "Hurricane Milton",
        "distance_miles": 45.23,
        "latitude": 28.5,
        "longitude": -94.2,
        "severity": "Category 2",
        "category": "2",
        "max_wind_mph": 100,
        "movement_direction": "NW",
        "movement_speed_mph": 12,
        "advisory_number": "15",
        "basin": "AL",
        "inside_cone": false,
        "details": {},
        "last_updated": "2025-01-08T12:00:00Z"
      }
    ],
    "tornadoes": [],
    "wildfires": []
  },
  "summary": {
    "total_disasters": 1,
    "hurricanes_count": 1,
    "tornadoes_count": 0,
    "wildfires_count": 0
  }
}
```

---

## CSV Input Format

All implementations must accept CSV files with this format:

**Required Columns:**
- `name` (or `location`) - Location identifier
- `latitude` - Decimal degrees
- `longitude` - Decimal degrees

**Example:**
```csv
name,latitude,longitude
Houston TX,29.7604,-95.3698
Miami FL,25.7617,-80.1918
```

**Parsing Rules:**
1. First row is header (required)
2. Accept either `name` or `location` for the name column
3. Latitude/longitude must be valid decimal degrees
4. Skip rows with invalid coordinates (log warning)
5. UTF-8 encoding expected

