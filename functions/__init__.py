"""
Functions package for Late Season Snowpack Analysis

This package contains utility functions for Google Earth Engine analysis,
visualization, and geospatial operations.
"""

# Import all functions from geolib
from .geolib import (
    add_ee_layer,
    create_map,
    get_image_collection_info
)

# Make functions available at package level
__all__ = [
    'add_ee_layer',
    'create_map', 
    'get_image_collection_info'
]