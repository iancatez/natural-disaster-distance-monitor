"""
Tornado data fetching and distance calculation module.

This module provides functions to:
- Fetch recent tornado reports from NOAA Damage Assessment Toolkit
- Calculate distances from a location to tornado start points
- Filter by EF scale and date range
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from .models import TornadoResult, TornadoScale
from .utils import haversine, create_retry_session

# Configure module logger
logger = logging.getLogger(__name__)

# API Configuration
TORNADO_API_URL = "https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/1/query"


def fetch_recent_tornadoes(
    days_ago: int = 14,
    min_ef_scale: int = 0,
    max_retries: int = 3
) -> List[dict]:
    """
    Fetch recent tornado reports from NOAA.
    
    Queries the NOAA Damage Assessment Toolkit for tornado reports
    within the specified date range and minimum EF scale.
    
    Args:
        days_ago: Number of days in the past to search (default: 14)
        min_ef_scale: Minimum EF scale to include (0-5, default: 0)
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of tornado feature dictionaries from the API
        
    Example:
        >>> tornadoes = fetch_recent_tornadoes(days_ago=30, min_ef_scale=2)
        >>> print(f"Found {len(tornadoes)} EF2+ tornadoes in the last 30 days")
    """
    logger.info(f"Fetching tornado data for the last {days_ago} days (EF{min_ef_scale}+)...")
    
    start_date = datetime.now() - timedelta(days=days_ago)
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    # Build query
    where_clause = f"stormdate >= DATE '{start_date_str}'"
    if min_ef_scale > 0:
        where_clause += f" AND efnum >= {min_ef_scale}"
    
    params = {
        'where': where_clause,
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json',
        'resultOffset': 0,
        'resultRecordCount': 1000
    }
    
    all_features = []
    session = create_retry_session(retries=max_retries)
    
    while True:
        logger.debug(f"Fetching tornadoes with offset: {params['resultOffset']}")
        
        try:
            response = session.get(TORNADO_API_URL, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"API error: Status {response.status_code}")
                break
            
            data = response.json()
            
            if 'error' in data:
                logger.error(f"API error: {data['error']}")
                break
            
            if 'features' not in data:
                logger.warning("No features in response")
                break
            
            features = data['features']
            all_features.extend(features)
            logger.debug(f"Fetched {len(features)} features")
            
            if len(features) < params['resultRecordCount']:
                break
                
            params['resultOffset'] += params['resultRecordCount']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            break
    
    logger.info(f"Total tornadoes fetched: {len(all_features)}")
    return all_features


def get_tornadoes_near_location(
    lat: float,
    lon: float,
    radius_miles: float = 100.0,
    days_ago: int = 14,
    min_ef_scale: int = 0
) -> List[TornadoResult]:
    """
    Get all tornadoes within a specified radius of a location.
    
    Fetches recent tornado data and calculates distances to the query location.
    Distance is measured from the tornado's starting point.
    
    Args:
        lat: Latitude of the query location (decimal degrees)
        lon: Longitude of the query location (decimal degrees)
        radius_miles: Maximum distance in miles to include (default: 100)
        days_ago: Number of days in the past to search (default: 14)
        min_ef_scale: Minimum EF scale to include (0-5, default: 0)
        
    Returns:
        List of TornadoResult objects sorted by distance (closest first)
        
    Example:
        >>> tornadoes = get_tornadoes_near_location(35.4676, -97.5164)  # OKC
        >>> for t in tornadoes:
        ...     print(f"{t.ef_scale}: {t.distance_miles:.1f} miles on {t.storm_date}")
    """
    results = []
    
    tornado_features = fetch_recent_tornadoes(
        days_ago=days_ago,
        min_ef_scale=min_ef_scale
    )
    
    if not tornado_features:
        logger.info("No tornado data available")
        return results
    
    for feature in tornado_features:
        try:
            attrs = feature.get('attributes', {})
            
            # Get tornado start position
            start_lat = attrs.get('startlat')
            start_lon = attrs.get('startlon')
            
            if start_lat is None or start_lon is None:
                continue
            
            # Calculate distance
            distance = haversine(lon, lat, float(start_lon), float(start_lat))
            
            if distance > radius_miles:
                continue
            
            # Parse EF scale
            efnum = attrs.get('efnum')
            ef_scale = TornadoScale.from_efnum(int(efnum)) if efnum is not None else None
            
            # Parse storm date
            storm_date = None
            if attrs.get('stormdate'):
                try:
                    storm_date = datetime.fromtimestamp(attrs['stormdate'] / 1000)
                except (ValueError, TypeError, OSError):
                    pass
            
            # Build severity string
            ef_str = f"EF{efnum}" if efnum is not None else "Unknown"
            severity = ef_scale.description if ef_scale else ef_str
            
            # Create result
            result = TornadoResult(
                disaster_type=None,  # Set by __post_init__
                name=f"Tornado {ef_str}",
                distance_miles=distance,
                latitude=float(start_lat),
                longitude=float(start_lon),
                severity=severity,
                ef_scale=ef_scale,
                max_wind_mph=float(attrs.get('maxwind')) if attrs.get('maxwind') and attrs.get('maxwind') > 0 else None,
                path_length_miles=float(attrs.get('length')) if attrs.get('length') and attrs.get('length') > 0 else None,
                path_width_yards=float(attrs.get('width')) if attrs.get('width') and attrs.get('width') > 0 else None,
                fatalities=int(attrs.get('fatalities', 0)) if attrs.get('fatalities') else None,
                injuries=int(attrs.get('injuries', 0)) if attrs.get('injuries') else None,
                storm_date=storm_date,
                last_updated=datetime.now(),
                details={
                    'objectid': attrs.get('objectid'),
                    'event_id': attrs.get('event_id'),
                    'end_lat': attrs.get('endlat'),
                    'end_lon': attrs.get('endlon'),
                    'ef_scale_text': attrs.get('efscale'),
                    'comments': attrs.get('comments'),
                }
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing tornado: {str(e)}")
            continue
    
    # Sort by distance
    results.sort(key=lambda x: x.distance_miles)
    
    logger.info(f"Found {len(results)} tornadoes within {radius_miles} miles")
    return results

