"""
Wildfire data fetching and distance calculation module.

This module provides functions to:
- Fetch active wildfire perimeters from WFIGS ArcGIS services
- Calculate distances from a location to fire perimeters
- Determine if a location is inside a fire perimeter
"""

import math
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .models import WildfireResult, WildfireSize
from .utils import (
    haversine_vectorized,
    is_point_in_polygon_vectorized,
    create_retry_session
)

# Configure module logger
logger = logging.getLogger(__name__)

# API Configuration
WILDFIRE_API_URL = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/WFIGS_Interagency_Perimeters_YearToDate/FeatureServer/0/query'


def fetch_active_wildfires(
    days_recent: int = 7,
    max_retries: int = 5
) -> pd.DataFrame:
    """
    Fetch active wildfire perimeters from WFIGS.
    
    Retrieves wildfire perimeter polygons from the WFIGS ArcGIS service
    and filters to recently active fires.
    
    Args:
        days_recent: Only include fires modified within this many days (default: 7)
        max_retries: Maximum number of retry attempts for API calls
        
    Returns:
        DataFrame with wildfire perimeter data and geometry
        
    Example:
        >>> fires_df = fetch_active_wildfires(days_recent=14)
        >>> print(f"Found {len(fires_df)} active fires")
    """
    logger.info(f"Fetching active wildfire perimeters (last {days_recent} days)...")
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json',
        'resultRecordCount': 2000
    }
    
    all_features = []
    offset = 0
    session = create_retry_session(retries=max_retries)
    
    while True:
        params['resultOffset'] = offset
        logger.debug(f"Fetching wildfires with offset: {offset}")
        
        try:
            response = session.get(WILDFIRE_API_URL, params=params, timeout=30)
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
                return pd.DataFrame()
            
            if 'features' not in data:
                logger.warning("No features in response")
                break
            
            features = data['features']
            logger.debug(f"Fetched {len(features)} features")
            all_features.extend(features)
            
            if len(features) < params['resultRecordCount']:
                break
                
            offset += len(features)
            
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return pd.DataFrame()
    
    if not all_features:
        logger.info("No wildfire data found")
        return pd.DataFrame()
    
    logger.info(f"Total features fetched: {len(all_features)}")
    
    # Convert to DataFrame
    df = pd.DataFrame([feature['attributes'] for feature in all_features])
    
    # Extract geometry (polygon rings)
    df['geometry_rings'] = [
        feature.get('geometry', {}).get('rings', [])
        for feature in all_features
    ]
    
    # Process date columns
    date_columns = ['attr_ModifiedOnDateTime_dt', 'poly_DateCurrent', 'attr_ContainmentDateTime']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit='ms', errors='coerce')
    
    # Filter to recent fires
    cutoff_date = datetime.now() - timedelta(days=days_recent)
    
    # Build filter mask
    mask = pd.Series([True] * len(df))
    
    if 'attr_ModifiedOnDateTime_dt' in df.columns:
        mask &= (df['attr_ModifiedOnDateTime_dt'] >= cutoff_date) | df['attr_ModifiedOnDateTime_dt'].isna()
    
    if 'poly_DateCurrent' in df.columns:
        mask &= (df['poly_DateCurrent'] >= cutoff_date) | df['poly_DateCurrent'].isna()
    
    # Don't filter out fires without containment date (still active)
    if 'attr_ContainmentDateTime' in df.columns:
        mask &= (df['attr_ContainmentDateTime'] >= cutoff_date) | df['attr_ContainmentDateTime'].isna()
    
    filtered_df = df[mask].copy()
    
    logger.info(f"Filtered to {len(filtered_df)} active fires (from {len(df)} total)")
    return filtered_df


def get_wildfires_near_location(
    lat: float,
    lon: float,
    radius_miles: float = 100.0,
    days_recent: int = 7
) -> List[WildfireResult]:
    """
    Get all wildfires within a specified radius of a location.
    
    Fetches active wildfire data and calculates distances to the query location.
    For wildfires with perimeter polygons, checks if the location is inside.
    
    Args:
        lat: Latitude of the query location (decimal degrees)
        lon: Longitude of the query location (decimal degrees)
        radius_miles: Maximum distance in miles to include (default: 100)
        days_recent: Only include fires modified within this many days (default: 7)
        
    Returns:
        List of WildfireResult objects sorted by distance (closest first)
        
    Example:
        >>> fires = get_wildfires_near_location(34.0522, -118.2437)  # LA
        >>> for f in fires:
        ...     print(f"{f.name}: {f.distance_miles:.1f} miles, {f.acres} acres")
    """
    results = []
    
    fires_df = fetch_active_wildfires(days_recent=days_recent)
    
    if fires_df.empty:
        logger.info("No active wildfires to process")
        return results
    
    for _, fire in fires_df.iterrows():
        try:
            # Calculate distance to fire
            distance, inside = _calculate_distance_to_fire(lat, lon, fire)
            
            if distance > radius_miles and not inside:
                continue
            
            # Get fire info
            fire_name = fire.get('poly_IncidentName', 'Unknown Fire')
            fire_id = fire.get('poly_IRWINID')
            acres = fire.get('attr_IncidentSize')
            
            # Determine size category
            size_category = None
            if acres is not None:
                try:
                    acres = float(acres)
                    size_category = WildfireSize.from_acres(acres)
                except (ValueError, TypeError):
                    acres = None
            
            # Get containment
            containment = fire.get('attr_PercentContained')
            if containment is not None:
                try:
                    containment = float(containment)
                except (ValueError, TypeError):
                    containment = None
            
            # Build severity string
            if size_category:
                severity = size_category.description
            elif acres:
                severity = f"{acres:,.0f} acres"
            else:
                severity = "Unknown size"
            
            if containment is not None:
                severity += f" ({containment:.0f}% contained)"
            
            # Get fire centroid for coordinates
            fire_lat, fire_lon = _get_fire_centroid(fire)
            
            result = WildfireResult(
                disaster_type=None,  # Set by __post_init__
                name=fire_name,
                distance_miles=0.0 if inside else distance,
                latitude=fire_lat,
                longitude=fire_lon,
                severity=severity,
                size_category=size_category,
                acres=acres,
                containment_percent=containment,
                inside_perimeter=inside,
                fire_id=fire_id,
                last_updated=fire.get('attr_ModifiedOnDateTime_dt'),
                details={
                    'fire_behavior': fire.get('attr_FireBehaviorGeneral'),
                    'discovery_date': fire.get('attr_FireDiscoveryDateTime'),
                    'cause': fire.get('attr_FireCause'),
                    'state': fire.get('attr_POOState'),
                    'county': fire.get('attr_POOCounty'),
                }
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing wildfire: {str(e)}")
            continue
    
    # Sort by distance
    results.sort(key=lambda x: x.distance_miles)
    
    logger.info(f"Found {len(results)} wildfires within {radius_miles} miles")
    return results


def _calculate_distance_to_fire(
    user_lat: float,
    user_lon: float,
    fire: pd.Series
) -> Tuple[float, bool]:
    """
    Calculate distance from a point to a fire perimeter.
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        fire: DataFrame row containing fire data and geometry
        
    Returns:
        Tuple of (distance_miles, is_inside_perimeter)
    """
    try:
        rings = fire.get('geometry_rings', [])
        
        if not rings:
            # No polygon geometry, return infinity
            return float('inf'), False
        
        # In ArcGIS geometry:
        # - rings[0] is the outer boundary
        # - rings[1:] are interior rings (holes - unburned areas)
        # A point is inside the fire perimeter if:
        # - It IS inside the outer boundary (rings[0])
        # - It is NOT inside any hole ring (rings[1:])
        
        inside_outer = False
        inside_hole = False
        min_distance = float('inf')
        
        for i, ring in enumerate(rings):
            if not ring:
                continue
                
            poly_points = np.array(ring)
            
            if len(poly_points) < 3:
                continue
            
            # Check if inside this ring
            ring_inside = is_point_in_polygon_vectorized(
                np.array([user_lon]),
                np.array([user_lat]),
                poly_points
            )
            
            if ring_inside[0]:
                if i == 0:
                    # Inside outer boundary
                    inside_outer = True
                else:
                    # Inside a hole (unburned area)
                    inside_hole = True
            
            # Calculate minimum distance to ring boundary
            distances = haversine_vectorized(
                user_lon,
                user_lat,
                poly_points[:, 0],
                poly_points[:, 1]
            )
            
            ring_min_distance = float(np.min(distances))
            min_distance = min(min_distance, ring_min_distance)
        
        # Point is inside fire perimeter only if inside outer boundary
        # AND not inside any hole
        inside = inside_outer and not inside_hole
        
        if inside:
            return 0.0, True
        
        return min_distance, False
        
    except Exception as e:
        logger.error(f"Error calculating fire distance: {str(e)}")
        return float('inf'), False


def _get_fire_centroid(fire: pd.Series) -> Tuple[float, float]:
    """
    Calculate the centroid of a fire perimeter.
    
    Args:
        fire: DataFrame row containing fire geometry
        
    Returns:
        Tuple of (latitude, longitude) for fire center
    """
    try:
        rings = fire.get('geometry_rings', [])
        
        if rings and rings[0]:
            poly_points = np.array(rings[0])
            centroid_lon = np.mean(poly_points[:, 0])
            centroid_lat = np.mean(poly_points[:, 1])
            return float(centroid_lat), float(centroid_lon)
        
        # Fallback to POO (Point of Origin) if available
        poo_lat = fire.get('attr_POOLatitude')
        poo_lon = fire.get('attr_POOLongitude')
        
        if poo_lat is not None and poo_lon is not None:
            return float(poo_lat), float(poo_lon)
        
        return 0.0, 0.0
        
    except Exception as e:
        logger.error(f"Error calculating fire centroid: {str(e)}")
        return 0.0, 0.0

