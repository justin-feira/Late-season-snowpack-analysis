"""
Helper utilities for the Streamlit app
"""
import ee
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple
import json


def convert_geojson_to_ee_geometry(geojson_data: Dict[str, Any]) -> Optional[ee.Geometry]:
    """
    Convert GeoJSON data to Earth Engine Geometry.
    
    Args:
        geojson_data: Dictionary containing GeoJSON geometry data
        
    Returns:
        ee.Geometry.Polygon object or None if conversion fails
        
    Example:
        >>> geojson = {
        ...     "type": "Polygon",
        ...     "coordinates": [[[-106.99, 39.08], [-106.71, 38.65], ...]]
        ... }
        >>> ee_geom = convert_geojson_to_ee_geometry(geojson)
    """
    try:
        if geojson_data is None:
            return None
            
        # Handle different GeoJSON structures
        if 'geometry' in geojson_data:
            geometry = geojson_data['geometry']
        elif 'type' in geojson_data:
            geometry = geojson_data
        else:
            return None
            
        # Convert to EE Geometry
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates']
            return ee.Geometry.Polygon(coords)
        elif geometry['type'] == 'MultiPolygon':
            # Take the first polygon if multiple
            coords = geometry['coordinates'][0]
            return ee.Geometry.Polygon(coords)
        else:
            return None
            
    except Exception as e:
        print(f"Error converting GeoJSON to EE Geometry: {e}")
        return None


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    """
    Validate that date range is logical.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if start_date >= end_date:
        return False, "End date must be after start date"
    
    # Check if dates are not too far in the future
    today = date.today()
    if end_date > today:
        return False, "End date cannot be in the future"
    
    # Check reasonable time range (Landsat 5 launched in 1984)
    if start_date.year < 1984:
        return False, "Start date cannot be before 1984 (Landsat 5 launch)"
    
    return True, ""


def validate_parameters(
    polygon_geometry: Optional[ee.Geometry],
    start_date_1: date,
    end_date_1: date,
    start_date_2: date,
    end_date_2: date,
    month: int,
    cloud_cover: int
) -> Tuple[bool, str]:
    """
    Validate all parameters before running analysis.
    
    Args:
        polygon_geometry: Earth Engine geometry for region
        start_date_1, end_date_1: First date range
        start_date_2, end_date_2: Second date range
        month: Month filter (1-12)
        cloud_cover: Cloud cover threshold (0-100)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check polygon
    if polygon_geometry is None:
        return False, "Please draw a polygon on the map to define your region of interest"
    
    # Validate first date range
    valid, msg = validate_date_range(start_date_1, end_date_1)
    if not valid:
        return False, f"Period 1: {msg}"
    
    # Validate second date range
    valid, msg = validate_date_range(start_date_2, end_date_2)
    if not valid:
        return False, f"Period 2: {msg}"
    
    # Note: Overlapping periods are allowed but not recommended for clearest comparison
    # Users can still proceed if they want to compare overlapping time ranges
    
    # Validate month
    if not 1 <= month <= 12:
        return False, "Month must be between 1 and 12"
    
    # Validate cloud cover
    if not 0 <= cloud_cover <= 100:
        return False, "Cloud cover must be between 0 and 100"
    
    return True, ""


def format_date_for_ee(d: date) -> str:
    """
    Format a date object as a string for Earth Engine.
    
    Args:
        d: Python date object
        
    Returns:
        Date string in 'YYYY-MM-DD' format
    """
    return d.strftime('%Y-%m-%d')


def suggest_landsat_collection(start_year: int, end_year: int) -> str:
    """
    Suggest appropriate Landsat collection based on date range.
    
    Args:
        start_year: Year to start
        end_year: Year to end
        
    Returns:
        Suggested Landsat collection ID
    """
    # Landsat 5: 1984-2012
    # Landsat 7: 1999-present (SLC failure after 2003)
    # Landsat 8: 2013-present
    # Landsat 9: 2021-present
    
    avg_year = (start_year + end_year) // 2
    
    if avg_year < 2000:
        return 'LANDSAT/LT05/C02/T1_L2'  # Landsat 5
    elif avg_year < 2013:
        return 'LANDSAT/LE07/C02/T1_L2'  # Landsat 7
    elif avg_year < 2021:
        return 'LANDSAT/LC08/C02/T1_L2'  # Landsat 8
    else:
        return 'LANDSAT/LC09/C02/T1_L2'  # Landsat 9


def get_month_name(month_number: int) -> str:
    """Get month name from number."""
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    if 1 <= month_number <= 12:
        return months[month_number - 1]
    return f"Month {month_number}"
