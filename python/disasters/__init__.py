"""
Natural Disaster Distance Monitor - Python Implementation

A CLI tool to find hurricanes, tornadoes, and wildfires near any location.

This package provides:
- Real-time hurricane tracking from NOAA/NHC
- Recent tornado reports from NOAA DAT
- Active wildfire perimeters from WFIGS

Usage:
    from disasters import get_nearby_disasters, DisasterType
    
    # Query all disaster types within 100 miles
    results = get_nearby_disasters(29.7604, -95.3698)
    
    # Query specific types only
    results = get_nearby_disasters(
        29.7604, -95.3698,
        disaster_types=[DisasterType.HURRICANE, DisasterType.WILDFIRE]
    )
    
    # Print results
    for h in results.hurricanes:
        print(f"Hurricane: {h.name} - {h.distance_miles:.1f} miles")
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import (
    DisasterType,
    DisasterResult,
    HurricaneResult,
    TornadoResult,
    WildfireResult,
    Location,
    LocationResults,
    HurricaneCategory,
    TornadoScale,
    WildfireSize,
)
from .hurricanes import get_hurricanes_near_location, fetch_active_hurricanes
from .tornadoes import get_tornadoes_near_location, fetch_recent_tornadoes
from .wildfires import get_wildfires_near_location, fetch_active_wildfires
from .utils import (
    validate_coordinates,
    load_locations_from_csv,
    configure_logging,
    haversine,
    haversine_vectorized,
)

# Configure module logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    # Main functions
    'get_nearby_disasters',
    'query_locations_from_csv',
    # Types and models
    'DisasterType',
    'DisasterResult',
    'HurricaneResult',
    'TornadoResult',
    'WildfireResult',
    'Location',
    'LocationResults',
    # Severity enums
    'HurricaneCategory',
    'TornadoScale',
    'WildfireSize',
    # Individual fetchers
    'get_hurricanes_near_location',
    'get_tornadoes_near_location',
    'get_wildfires_near_location',
    'fetch_active_hurricanes',
    'fetch_recent_tornadoes',
    'fetch_active_wildfires',
    # Utilities
    'validate_coordinates',
    'load_locations_from_csv',
    'configure_logging',
    'haversine',
]

__version__ = '0.1.0'


def get_nearby_disasters(
    latitude: float,
    longitude: float,
    radius_miles: float = 100.0,
    disaster_types: Optional[List[DisasterType]] = None,
    name: str = "Query Location"
) -> LocationResults:
    """
    Query all disaster types near a single location.
    
    This is the main entry point for disaster queries. It fetches data from
    all requested disaster type APIs and returns results within the specified
    radius.
    
    Args:
        latitude: Query point latitude (-90 to 90)
        longitude: Query point longitude (-180 to 180)
        radius_miles: Search radius in miles (default: 100)
        disaster_types: List of DisasterType to query, or None for all
        name: Name for the query location (default: "Query Location")
        
    Returns:
        LocationResults object containing all found disasters
        
    Raises:
        ValueError: If coordinates are invalid
        
    Example:
        >>> # Find all disasters within 100 miles of Houston
        >>> results = get_nearby_disasters(29.7604, -95.3698)
        >>> print(f"Found {results.total_disasters} disasters")
        >>> 
        >>> # Find only hurricanes within 50 miles
        >>> results = get_nearby_disasters(
        ...     29.7604, -95.3698,
        ...     radius_miles=50,
        ...     disaster_types=[DisasterType.HURRICANE]
        ... )
    """
    # Validate coordinates
    if not validate_coordinates(latitude, longitude):
        raise ValueError(f"Invalid coordinates: lat={latitude}, lon={longitude}")
    
    # Default to all disaster types
    if disaster_types is None:
        disaster_types = list(DisasterType)
    
    # Create location object
    location = Location(name=name, latitude=latitude, longitude=longitude)
    
    # Initialize results
    results = LocationResults(
        location=location,
        radius_miles=radius_miles,
        query_time=datetime.now()
    )
    
    # Query each disaster type
    if DisasterType.HURRICANE in disaster_types:
        logger.info("Querying hurricanes...")
        try:
            results.hurricanes = get_hurricanes_near_location(
                latitude, longitude, radius_miles
            )
        except Exception as e:
            logger.error(f"Error fetching hurricanes: {e}")
            results.hurricanes = []
    
    if DisasterType.TORNADO in disaster_types:
        logger.info("Querying tornadoes...")
        try:
            results.tornadoes = get_tornadoes_near_location(
                latitude, longitude, radius_miles
            )
        except Exception as e:
            logger.error(f"Error fetching tornadoes: {e}")
            results.tornadoes = []
    
    if DisasterType.WILDFIRE in disaster_types:
        logger.info("Querying wildfires...")
        try:
            results.wildfires = get_wildfires_near_location(
                latitude, longitude, radius_miles
            )
        except Exception as e:
            logger.error(f"Error fetching wildfires: {e}")
            results.wildfires = []
    
    logger.info(
        f"Query complete: {len(results.hurricanes)} hurricanes, "
        f"{len(results.tornadoes)} tornadoes, "
        f"{len(results.wildfires)} wildfires"
    )
    
    return results


def query_locations_from_csv(
    csv_path: str,
    radius_miles: float = 100.0,
    disaster_types: Optional[List[DisasterType]] = None
) -> List[LocationResults]:
    """
    Query disasters for multiple locations from a CSV file.
    
    Reads locations from a CSV file and queries disasters for each one.
    CSV must have columns: name (or location), latitude, longitude
    
    Args:
        csv_path: Path to CSV file with locations
        radius_miles: Search radius in miles (default: 100)
        disaster_types: List of DisasterType to query, or None for all
        
    Returns:
        List of LocationResults, one per CSV row
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is missing required columns
        
    Example:
        >>> results = query_locations_from_csv('locations.csv', radius_miles=50)
        >>> for r in results:
        ...     print(f"{r.location.name}: {r.total_disasters} disasters found")
    """
    # Load locations from CSV
    locations = load_locations_from_csv(csv_path)
    
    if not locations:
        logger.warning("No valid locations found in CSV")
        return []
    
    logger.info(f"Querying {len(locations)} locations from {csv_path}")
    
    all_results = []
    
    for i, loc_data in enumerate(locations, 1):
        logger.info(f"Processing location {i}/{len(locations)}: {loc_data['name']}")
        
        try:
            results = get_nearby_disasters(
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude'],
                radius_miles=radius_miles,
                disaster_types=disaster_types,
                name=loc_data['name']
            )
            all_results.append(results)
            
        except Exception as e:
            logger.error(f"Error processing {loc_data['name']}: {e}")
            # Create empty results for failed location
            location = Location(
                name=loc_data['name'],
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude']
            )
            all_results.append(LocationResults(
                location=location,
                radius_miles=radius_miles,
                query_time=datetime.now()
            ))
    
    return all_results

