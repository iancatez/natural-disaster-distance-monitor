"""
Hurricane/Cyclone data fetching and distance calculation module.

This module provides functions to:
- Fetch active hurricane data from NOAA/NHC ArcGIS services
- Calculate distances from a location to hurricane forecast cones
- Determine if a location is inside a hurricane forecast cone
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .models import HurricaneResult, HurricaneCategory
from .utils import (
    haversine,
    haversine_vectorized,
    is_point_in_polygon_vectorized,
    create_retry_session,
    EARTH_RADIUS_MILES
)

# Configure module logger
logger = logging.getLogger(__name__)

# API Configuration
HURRICANE_BASE_URL = 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/ArcGIS/rest/services/Active_Hurricanes_v1/FeatureServer'
CONE_LAYER = 4      # Forecast cones (polygons)
DETAILS_LAYER = 0   # Detailed forecast points


def fetch_active_hurricanes(max_retries: int = 5) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Fetch all active hurricane data from NOAA/NHC.
    
    Retrieves both forecast cone polygons and detailed forecast points
    from the ArcGIS services.
    
    Args:
        max_retries: Maximum number of retry attempts for API calls
        
    Returns:
        Tuple of (cone_df, detailed_df) DataFrames, or (None, None) on failure
        
    Example:
        >>> cone_df, detailed_df = fetch_active_hurricanes()
        >>> if cone_df is not None:
        ...     print(f"Found {len(cone_df)} forecast cones")
    """
    logger.info("Fetching active hurricane data from NOAA/NHC...")
    
    cone_url = f'{HURRICANE_BASE_URL}/{CONE_LAYER}/query'
    detailed_url = f'{HURRICANE_BASE_URL}/{DETAILS_LAYER}/query'
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json',
        'resultRecordCount': 2000
    }
    
    def fetch_layer(url: str) -> Optional[List[dict]]:
        """Fetch all features from a single layer with pagination."""
        all_features = []
        offset = 0
        session = create_retry_session(retries=max_retries)
        
        while True:
            params['resultOffset'] = offset
            logger.debug(f"Fetching from {url} with offset: {offset}")
            
            try:
                response = session.get(url, params=params, timeout=30)
                data = response.json()
                
                if 'error' in data:
                    error = data['error']
                    logger.error(f"API error: {error}")
                    
                    # Handle rate limiting
                    if error.get('code') == 429:
                        details = error.get('details', ['wait 60 seconds'])
                        try:
                            retry_after = int(details[0].split()[-2])
                        except (IndexError, ValueError):
                            retry_after = 60
                        logger.info(f"Rate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue
                    return None
                
                if 'features' not in data:
                    logger.warning("No features in response")
                    return [] if offset == 0 else all_features
                
                features = data['features']
                logger.debug(f"Fetched {len(features)} features")
                all_features.extend(features)
                
                if len(features) < params['resultRecordCount']:
                    break
                    
                offset += len(features)
                
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                return None
        
        return all_features
    
    # Fetch both layers
    cone_features = fetch_layer(cone_url)
    detailed_features = fetch_layer(detailed_url)
    
    if cone_features is None:
        logger.error("Failed to fetch cone data")
        return None, None
    
    if detailed_features is None:
        logger.error("Failed to fetch detailed forecast data")
        return None, None
    
    if not cone_features and not detailed_features:
        logger.info("No active hurricanes found")
        return pd.DataFrame(), pd.DataFrame()
    
    # Convert to DataFrames
    if cone_features:
        cone_df = pd.DataFrame([
            {**feature['attributes'], 'geometry': json.dumps(feature.get('geometry', {}))}
            for feature in cone_features
        ])
        
        # Process date columns
        if 'ADVDATE' in cone_df.columns:
            cone_df['ADVDATE'] = pd.to_datetime(cone_df['ADVDATE'], unit='ms', errors='coerce')
        if 'FCSTPRD' in cone_df.columns:
            cone_df['FCSTPRD'] = pd.to_numeric(cone_df['FCSTPRD'], errors='coerce')
    else:
        cone_df = pd.DataFrame()
    
    if detailed_features:
        detailed_df = pd.DataFrame([feature['attributes'] for feature in detailed_features])
    else:
        detailed_df = pd.DataFrame()
    
    logger.info(f"Fetched {len(cone_df)} cone records and {len(detailed_df)} detailed records")
    return cone_df, detailed_df


def get_hurricanes_near_location(
    lat: float,
    lon: float,
    radius_miles: float = 100.0
) -> List[HurricaneResult]:
    """
    Get all hurricanes within a specified radius of a location.
    
    Fetches active hurricane data and calculates distances to the query location.
    For hurricanes with forecast cones, checks if the location is inside the cone.
    
    Args:
        lat: Latitude of the query location (decimal degrees)
        lon: Longitude of the query location (decimal degrees)
        radius_miles: Maximum distance in miles to include (default: 100)
        
    Returns:
        List of HurricaneResult objects sorted by distance (closest first)
        
    Example:
        >>> hurricanes = get_hurricanes_near_location(29.7604, -95.3698)
        >>> for h in hurricanes:
        ...     print(f"{h.name}: {h.distance_miles:.1f} miles")
    """
    results = []
    
    cone_df, detailed_df = fetch_active_hurricanes()
    
    if cone_df is None or cone_df.empty:
        logger.info("No active hurricanes to process")
        return results
    
    # Get the latest position data for each storm from detailed_df
    storm_positions = {}
    if detailed_df is not None and not detailed_df.empty:
        # Group by storm and get current position (TAU=0 or lowest TAU)
        for _, row in detailed_df.iterrows():
            storm_key = (row.get('STORMNAME'), row.get('STORMNUM'))
            tau = row.get('TAU', 999)
            
            if storm_key not in storm_positions or tau < storm_positions[storm_key].get('TAU', 999):
                storm_positions[storm_key] = row.to_dict()
    
    # Process each forecast cone
    processed_storms = set()
    
    for _, cone in cone_df.iterrows():
        storm_name = cone.get('STORMNAME', 'Unknown')
        storm_num = cone.get('STORMNUM')
        storm_key = (storm_name, storm_num)
        
        # Skip if we've already processed this storm (multiple cones per storm)
        # We want the most recent advisory
        if storm_key in processed_storms:
            continue
        
        try:
            # Calculate distance to cone
            distance, inside_cone = _calculate_distance_to_cone(lat, lon, cone)
            
            # Check if within radius
            if distance > radius_miles and not inside_cone:
                continue
            
            processed_storms.add(storm_key)
            
            # Get storm details from detailed positions
            position_data = storm_positions.get(storm_key, {})
            
            # Determine category
            max_wind = position_data.get('MAXWIND') or cone.get('MAX_WIND')
            ssnum = position_data.get('SSNUM')
            
            if ssnum is not None:
                category = HurricaneCategory.from_ssnum(int(ssnum))
            elif max_wind:
                category = HurricaneCategory.from_wind_speed(float(max_wind))
            else:
                category = None
            
            # Get storm center coordinates
            storm_lat = position_data.get('LAT') or cone.get('LAT')
            storm_lon = position_data.get('LON') or cone.get('LON')
            
            # Build severity string
            storm_type = cone.get('STORMTYPE', position_data.get('STORMTYPE', 'Storm'))
            if category:
                severity = f"{storm_type} - {category.description}"
            else:
                severity = storm_type
            
            result = HurricaneResult(
                disaster_type=None,  # Set by __post_init__
                name=storm_name,
                distance_miles=0.0 if inside_cone else distance,
                latitude=float(storm_lat) if storm_lat else 0.0,
                longitude=float(storm_lon) if storm_lon else 0.0,
                severity=severity,
                category=category,
                max_wind_mph=float(max_wind) if max_wind else None,
                gust_mph=float(position_data.get('GUST')) if position_data.get('GUST') else None,
                movement_direction=_format_direction(position_data.get('TCDIR')),
                movement_speed_mph=float(position_data.get('TCSPD')) if position_data.get('TCSPD') else None,
                advisory_number=str(cone.get('ADVISNUM', '')),
                basin=cone.get('BASIN'),
                storm_type=storm_type,
                inside_cone=inside_cone,
                last_updated=cone.get('ADVDATE'),
                details={
                    'forecast_period_hours': cone.get('FCSTPRD'),
                    'storm_number': storm_num,
                    'mslp_mb': position_data.get('MSLP'),
                }
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing hurricane {storm_name}: {str(e)}")
            continue
    
    # Sort by distance
    results.sort(key=lambda x: x.distance_miles)
    
    logger.info(f"Found {len(results)} hurricanes within {radius_miles} miles")
    return results


def _calculate_distance_to_cone(
    user_lat: float,
    user_lon: float,
    cone: pd.Series
) -> Tuple[float, bool]:
    """
    Calculate distance from a point to a hurricane forecast cone.
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        cone: DataFrame row containing cone geometry
        
    Returns:
        Tuple of (distance_miles, is_inside_cone)
    """
    try:
        geometry_str = cone.get('geometry', '{}')
        geometry = json.loads(geometry_str) if isinstance(geometry_str, str) else geometry_str
        
        if not geometry or 'rings' not in geometry:
            # No polygon geometry, use point distance if available
            cone_lat = cone.get('LAT')
            cone_lon = cone.get('LON')
            if cone_lat and cone_lon:
                distance = haversine(user_lon, user_lat, float(cone_lon), float(cone_lat))
                return distance, False
            return float('inf'), False
        
        # Get the outer ring of the polygon
        polygon = np.array(geometry['rings'][0])
        
        # Check if point is inside the cone
        inside = is_point_in_polygon_vectorized(
            np.array([user_lon]),
            np.array([user_lat]),
            polygon
        )
        
        if inside[0]:
            return 0.0, True
        
        # Calculate minimum distance to polygon boundary
        distances = haversine_vectorized(
            user_lon,
            user_lat,
            polygon[:, 0],
            polygon[:, 1]
        )
        
        min_distance = float(np.min(distances))
        return min_distance, False
        
    except Exception as e:
        logger.error(f"Error calculating cone distance: {str(e)}")
        return float('inf'), False


def _format_direction(degrees: Optional[float]) -> Optional[str]:
    """
    Convert degrees to cardinal direction.
    
    Args:
        degrees: Direction in degrees (0-360)
        
    Returns:
        Cardinal direction string (N, NE, E, etc.) or None
    """
    if degrees is None:
        return None
    
    try:
        degrees = float(degrees)
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    except (ValueError, TypeError):
        return None

