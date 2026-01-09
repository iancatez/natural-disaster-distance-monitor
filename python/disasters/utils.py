"""
Shared utility functions for the Natural Disaster Distance Monitor.

This module provides common functions used across all disaster type modules:
- Distance calculations (haversine formula)
- Polygon containment checks (ray-casting algorithm)
- HTTP session management with retry logic
- Coordinate validation
- CSV file loading
"""

import csv
import math
import logging
from pathlib import Path
from typing import List, Tuple, Union, Optional

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
EARTH_RADIUS_MILES = 3956
DEFAULT_DISTANCE_MILES = 100.0


# =============================================================================
# Distance Calculations
# =============================================================================

def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great-circle distance between two points using the haversine formula.
    
    Args:
        lon1: Longitude of first point (decimal degrees)
        lat1: Latitude of first point (decimal degrees)
        lon2: Longitude of second point (decimal degrees)
        lat2: Latitude of second point (decimal degrees)
        
    Returns:
        Distance between the two points in miles
        
    Example:
        >>> distance = haversine(-95.3698, 29.7604, -80.1918, 25.7617)
        >>> print(f"Houston to Miami: {distance:.1f} miles")
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_MILES * c


def haversine_vectorized(
    lon1: Union[float, np.ndarray],
    lat1: Union[float, np.ndarray],
    lon2: Union[float, np.ndarray],
    lat2: Union[float, np.ndarray]
) -> np.ndarray:
    """
    Vectorized haversine formula for calculating distances between coordinate arrays.
    
    Efficiently calculates distances between arrays of coordinates using NumPy
    broadcasting. Useful for calculating distances from one point to many, or
    between two arrays of points.
    
    Args:
        lon1: Longitude(s) of first point(s) (decimal degrees)
        lat1: Latitude(s) of first point(s) (decimal degrees)
        lon2: Longitude(s) of second point(s) (decimal degrees)
        lat2: Latitude(s) of second point(s) (decimal degrees)
        
    Returns:
        Array of distances in miles
        
    Example:
        >>> user_lon, user_lat = -95.3698, 29.7604
        >>> storm_lons = np.array([-94.0, -93.0, -92.0])
        >>> storm_lats = np.array([28.0, 27.0, 26.0])
        >>> distances = haversine_vectorized(user_lon, user_lat, storm_lons, storm_lats)
    """
    try:
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        return EARTH_RADIUS_MILES * c
    except Exception as e:
        logger.error(f"Error in haversine_vectorized: {str(e)}")
        raise


# =============================================================================
# Polygon Operations
# =============================================================================

def is_point_in_polygon_vectorized(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    polygon: Union[List[Tuple[float, float]], np.ndarray]
) -> np.ndarray:
    """
    Check if points are inside a polygon using ray-casting algorithm.
    
    Uses a vectorized implementation with bounding box pre-filtering for
    performance. Handles edge cases including points on vertices and edges.
    
    Args:
        x: X coordinate(s) / longitude(s) to check
        y: Y coordinate(s) / latitude(s) to check
        polygon: List of (x, y) tuples or numpy array defining polygon vertices
        
    Returns:
        Boolean array indicating which points are inside or on the polygon edge
        
    Example:
        >>> polygon = [(-100, 25), (-100, 35), (-90, 35), (-90, 25)]
        >>> lons = np.array([-95, -85, -95])
        >>> lats = np.array([30, 30, 40])
        >>> inside = is_point_in_polygon_vectorized(lons, lats, polygon)
        >>> # Returns: array([True, False, False])
    """
    try:
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        polygon = np.asarray(polygon, dtype=float)
        n = len(polygon)
        inside_or_on_edge = np.zeros(len(x), dtype=bool)
        
        if len(x) == 0:
            return inside_or_on_edge
        
        # Bounding box check for early filtering
        min_x, min_y = np.min(polygon, axis=0)
        max_x, max_y = np.max(polygon, axis=0)
        bbox_check = (x >= min_x) & (x <= max_x) & (y >= min_y) & (y <= max_y)
        
        # Only process points within the bounding box
        x_in_bbox = x[bbox_check]
        y_in_bbox = y[bbox_check]
        
        if len(x_in_bbox) == 0:
            return inside_or_on_edge
        
        inside_or_on_edge_bbox = np.zeros(len(x_in_bbox), dtype=bool)
        
        for i in range(n):
            j = (i + 1) % n
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            # Check if point is on vertex
            on_vertex = (np.abs(x_in_bbox - xi) < 1e-9) & (np.abs(y_in_bbox - yi) < 1e-9)
            inside_or_on_edge_bbox |= on_vertex

            # Check if point is on edge
            edge_x = xj - xi
            edge_y = yj - yi
            edge_length_sq = edge_x ** 2 + edge_y ** 2
            
            if edge_length_sq > 0:
                t = ((x_in_bbox - xi) * edge_x + (y_in_bbox - yi) * edge_y) / edge_length_sq
                px = xi + t * edge_x
                py = yi + t * edge_y
                distance_sq = (x_in_bbox - px) ** 2 + (y_in_bbox - py) ** 2
                tolerance = 1e-12
                edge_check = (distance_sq < tolerance) & (t >= 0) & (t <= 1)
                inside_or_on_edge_bbox |= edge_check
            
            # Ray-casting algorithm for points not on the edge
            mask = ~inside_or_on_edge_bbox & (yi != yj)
            yj_gt_yi = yj > yi
            intersect = mask & (
                ((yi <= y_in_bbox) & (y_in_bbox < yj) & yj_gt_yi) |
                ((yj <= y_in_bbox) & (y_in_bbox < yi) & ~yj_gt_yi)
            )
            with np.errstate(divide='ignore', invalid='ignore'):
                slope = edge_x / edge_y
                intersect &= x_in_bbox < xi + (y_in_bbox - yi) * slope
            inside_or_on_edge_bbox[mask] ^= intersect[mask]
        
        # Assign results back to the original boolean array
        inside_or_on_edge[bbox_check] = inside_or_on_edge_bbox
        
        return inside_or_on_edge
    except Exception as e:
        logger.error(f"Error in is_point_in_polygon_vectorized: {str(e)}")
        raise


def is_point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    """
    Check if a single point is inside a polygon.
    
    Convenience wrapper around is_point_in_polygon_vectorized for single points.
    
    Args:
        x: X coordinate / longitude
        y: Y coordinate / latitude
        polygon: List of (x, y) tuples defining polygon vertices
        
    Returns:
        True if point is inside or on the polygon edge
    """
    result = is_point_in_polygon_vectorized(x, y, polygon)
    return bool(result[0])


# =============================================================================
# HTTP Session Management
# =============================================================================

class CustomRetry(Retry):
    """
    Custom retry class with logging for API debugging.
    
    Extends urllib3's Retry to log retry attempts and API errors,
    which is helpful for debugging rate limiting and API issues.
    """
    
    def increment(
        self,
        method: Optional[str] = None,
        url: Optional[str] = None,
        response: Optional[requests.Response] = None,
        error: Optional[Exception] = None,
        _pool: Optional[object] = None,
        _stacktrace: Optional[object] = None
    ) -> Retry:
        if response:
            logger.warning(f"Retry attempt for {url}. Status code: {response.status_code}")
            try:
                data = response.json()
                if 'error' in data:
                    logger.error(f"API error: {data['error']}")
            except Exception:
                logger.debug(f"Response body: {response.text[:500]}")
        return super().increment(method, url, response, error, _pool, _stacktrace)


def create_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: Tuple[int, ...] = (429, 500, 502, 503, 504)
) -> requests.Session:
    """
    Create an HTTP session with automatic retry logic.
    
    Creates a requests Session configured with exponential backoff retry
    for transient failures and rate limiting.
    
    Args:
        retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (0.3 = 0.3s, 0.9s, 2.7s...)
        status_forcelist: HTTP status codes that trigger a retry
        
    Returns:
        Configured requests.Session object
        
    Example:
        >>> session = create_retry_session(retries=5)
        >>> response = session.get('https://api.example.com/data')
    """
    session = requests.Session()
    retry = CustomRetry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'POST']),
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# =============================================================================
# Coordinate Validation
# =============================================================================

def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude values.
    
    Args:
        lat: Latitude value to validate
        lon: Longitude value to validate
        
    Returns:
        True if coordinates are valid, False otherwise
        
    Example:
        >>> validate_coordinates(29.7604, -95.3698)  # Houston
        True
        >>> validate_coordinates(91.0, -95.3698)  # Invalid latitude
        False
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def validate_and_normalize_coordinates(
    lat: float,
    lon: float
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Validate and normalize coordinate values.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        Tuple of (normalized_lat, normalized_lon, error_message)
        If valid, error_message is None. If invalid, coordinates are None.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError) as e:
        return None, None, f"Invalid coordinate format: {e}"
    
    if not (-90 <= lat <= 90):
        return None, None, f"Latitude {lat} out of range [-90, 90]"
    
    if not (-180 <= lon <= 180):
        return None, None, f"Longitude {lon} out of range [-180, 180]"
    
    return lat, lon, None


# =============================================================================
# CSV Loading
# =============================================================================

def load_locations_from_csv(filepath: str) -> List[dict]:
    """
    Load location data from a CSV file.
    
    CSV must have columns: name (or location), latitude, longitude
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of dictionaries with 'name', 'latitude', 'longitude' keys
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
        
    Example:
        >>> locations = load_locations_from_csv('data/test_locations.csv')
        >>> for loc in locations:
        ...     print(f"{loc['name']}: ({loc['latitude']}, {loc['longitude']})")
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    locations = []
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check for required columns
        fieldnames = reader.fieldnames or []
        has_name = 'name' in fieldnames or 'location' in fieldnames
        has_lat = 'latitude' in fieldnames
        has_lon = 'longitude' in fieldnames
        
        if not (has_name and has_lat and has_lon):
            missing = []
            if not has_name:
                missing.append('name (or location)')
            if not has_lat:
                missing.append('latitude')
            if not has_lon:
                missing.append('longitude')
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                name = row.get('name') or row.get('location', f'Location {row_num}')
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                
                if validate_coordinates(lat, lon):
                    locations.append({
                        'name': name.strip(),
                        'latitude': lat,
                        'longitude': lon
                    })
                else:
                    logger.warning(f"Row {row_num}: Invalid coordinates ({lat}, {lon}) - skipping")
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Row {row_num}: Error parsing row - {e}")
                continue
    
    logger.info(f"Loaded {len(locations)} locations from {filepath}")
    return locations


# =============================================================================
# Logging Configuration
# =============================================================================

def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the disasters package.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

