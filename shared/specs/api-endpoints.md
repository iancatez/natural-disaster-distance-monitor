# Natural Disaster API Endpoints

This document defines the external API endpoints used by all language implementations.

## Hurricane / Cyclone Data

**Provider:** NOAA/NHC via ArcGIS Services

### Forecast Cones (Polygons)
- **URL:** `https://services9.arcgis.com/RHVPKKiFTONKtxq3/ArcGIS/rest/services/Active_Hurricanes_v1/FeatureServer/4/query`
- **Method:** GET
- **Format:** ArcGIS JSON

### Detailed Forecast Points
- **URL:** `https://services9.arcgis.com/RHVPKKiFTONKtxq3/ArcGIS/rest/services/Active_Hurricanes_v1/FeatureServer/0/query`
- **Method:** GET
- **Format:** ArcGIS JSON

### Standard Query Parameters
```
where=1=1
outFields=*
returnGeometry=true
f=json
resultRecordCount=2000
resultOffset=0
```

### Key Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `STORMNAME` | string | Name of the storm |
| `STORMTYPE` | string | Type (Hurricane, Tropical Storm, etc.) |
| `ADVISNUM` | string | Advisory number |
| `ADVDATE` | timestamp | Advisory date (ms since epoch) |
| `BASIN` | string | Ocean basin (AL=Atlantic, EP=East Pacific) |
| `MAXWIND` | number | Maximum sustained wind (mph) |
| `GUST` | number | Maximum gust (mph) |
| `SSNUM` | number | Saffir-Simpson category (0-5) |
| `LAT` | number | Latitude |
| `LON` | number | Longitude |
| `geometry.rings` | array | Polygon coordinates for cone |

---

## Tornado Data

**Provider:** NOAA Damage Assessment Toolkit

### Tornado Reports
- **URL:** `https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/1/query`
- **Method:** GET
- **Format:** ArcGIS JSON

### Standard Query Parameters
```
where=efnum > 0 AND stormdate >= DATE '2025-01-01'
outFields=*
returnGeometry=true
f=json
resultRecordCount=1000
resultOffset=0
```

### Key Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `objectid` | number | Unique identifier |
| `stormdate` | timestamp | Date of tornado (ms since epoch) |
| `startlat` | number | Starting latitude |
| `startlon` | number | Starting longitude |
| `endlat` | number | Ending latitude |
| `endlon` | number | Ending longitude |
| `efscale` | string | EF scale rating (EF0-EF5) |
| `efnum` | number | EF number (0-5) |
| `length` | number | Path length (miles) |
| `width` | number | Path width (yards) |
| `maxwind` | number | Estimated max wind (mph) |
| `fatalities` | number | Number of fatalities |
| `injuries` | number | Number of injuries |

---

## Wildfire Data

**Provider:** WFIGS (Wildland Fire Interagency Geospatial Services)

### Fire Perimeters (Year-to-Date)
- **URL:** `https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/WFIGS_Interagency_Perimeters_YearToDate/FeatureServer/0/query`
- **Method:** GET
- **Format:** ArcGIS JSON

### Standard Query Parameters
```
where=1=1
outFields=*
returnGeometry=true
f=json
resultRecordCount=2000
resultOffset=0
```

### Key Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `poly_IRWINID` | string | Unique fire identifier |
| `poly_IncidentName` | string | Name of the fire |
| `attr_IncidentSize` | number | Fire size in acres |
| `attr_PercentContained` | number | Containment percentage |
| `attr_ModifiedOnDateTime_dt` | timestamp | Last modified (ms since epoch) |
| `poly_DateCurrent` | timestamp | Current as of date |
| `attr_ContainmentDateTime` | timestamp | Containment date (if contained) |
| `attr_FireBehaviorGeneral` | string | Fire behavior description |
| `geometry.rings` | array | Polygon coordinates for perimeter |

---

## ArcGIS Pagination

All ArcGIS endpoints use offset-based pagination:

```
resultOffset=0        # Start position
resultRecordCount=2000  # Max records per request
```

**Pagination Logic:**
```
offset = 0
while True:
    response = fetch(url, offset=offset, count=2000)
    features = response['features']
    process(features)
    
    if len(features) < 2000:
        break  # End of data
    
    offset += len(features)
```

---

## Rate Limiting

All APIs should be accessed with retry logic:

- **Max Retries:** 3-5 attempts
- **Backoff:** Exponential (0.3s base)
- **Status Codes to Retry:** 429, 500, 502, 503, 504

**Example Backoff Sequence:**
- Attempt 1: Immediate
- Attempt 2: Wait 0.3s
- Attempt 3: Wait 0.9s
- Attempt 4: Wait 2.7s
- Attempt 5: Wait 8.1s

---

## Error Handling

### Expected Error Responses
```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "details": ["Please retry after 60 seconds"]
  }
}
```

### Implementation Requirements
1. Check for `error` key in response before processing
2. Log full error details for debugging
3. Return empty results (not crash) on API failure
4. Distinguish between "no data available" and "error fetching"

