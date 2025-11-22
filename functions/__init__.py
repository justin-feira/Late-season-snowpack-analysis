"""
Functions package for Late Season Snowpack Analysis

This package contains utility functions for Google Earth Engine analysis,
visualization, and geospatial operations.

Usage:
    # From notebooks in execution/ directory:
    import sys
    sys.path.append('../functions')
    from geolib import count_images_by_year, image_count, count_images_by_week
    
    # Or import all functions:
    from functions import *
"""

try:
    # Import all functions from geolib
    from .geolib import (
        add_ee_layer,
        create_map,
        get_image_collection_info,
        ndsi_l5,
        ndsi_l9,
        mask_clouds_landsat,
        count_images_by_year,
        image_count,
        count_images_by_week
    )
    
    # Make functions available at package level
    __all__ = [
        'add_ee_layer',
        'create_map', 
        'get_image_collection_info',
        'ndsi_l5',
        'ndsi_l9', 
        'mask_clouds_landsat',
        'count_images_by_year',
        'image_count',
        'count_images_by_week'
    ]
    
except ImportError as e:
    print(f"Warning: Could not import all functions - {e}")
    print("Try importing directly from geolib: from geolib import function_name")