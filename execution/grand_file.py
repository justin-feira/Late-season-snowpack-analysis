import ee
import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import Image, display
import json
import sys
import os

def get_month_name(month_int):
    """Convert month number to month name."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return months[month_int - 1] if 1 <= month_int <= 12 else 'Unknown'
sys.path.append('../Setup')  # Go up one level to reach Setup folder
from gee_setup import *
setup_gee()

sys.path.append('../functions')
from geolib import (
    count_images_by_year, 
    image_count, 
    count_images_by_week,
    mask_clouds_landsat,
    ndsi_l5,
    ndsi_l9,
    yearly_composite,
    create_weighted_average,
    add_ee_layer
)

def snow_difference_map(region_polygon, 
                        date_range_1=ee.DateRange('1990-01-01', '2000-01-01'), 
                        date_range_2=ee.DateRange('2015-01-01', '2025-01-01'), 
                        collection_1='LANDSAT/LT05/C02/T1_L2', 
                        collection_2='LANDSAT/LC08/C02/T1_L2',
                        month_int=6,
                        cloud_cover=10,
                        clip_to_region=False,
                        output_folder='outputs',
                        output_filename='snow_difference_analysis',
                        output_format='tiff',
                        export_by_layer=True,
                        ndsi_vis= {
                            'min': -0.5,
                            'max': 1.0,
                            'palette': ['red', 'yellow', 'green', 'blue', 'purple']
                        },
                        snow_vis= {
                            'min': 0,
                            'max': 1,
                            'palette': ['brown', 'white']
                        },
                        diff_vis={
                            'min': -0.5,
                            'max': 0.5,
                            'palette': ['red', 'white', 'blue']
                        }          
                        ):
    """Create snow difference analysis maps with individual layer exports.
    
    Parameters:
    - region_polygon: ee.Geometry defining study area
    - date_range_1/2: Historical and recent time periods
    - collection_1/2: Landsat collections for each period
    - month_int: Month filter (1-12)
    - cloud_cover: Maximum cloud cover percentage (0-100)
    - clip_to_region: Clip outputs to polygon bounds
    - output_folder: Output directory
    - output_filename: Base filename (no extension)
    - output_format: File format ('tiff', 'png', 'jpg', 'html')
    - export_by_layer: Export each layer as separate file (default: True)
    
    Returns: Folium map object
    """
    
    # Process collections
    collection_a = ee.ImageCollection(collection_1) \
        .filterDate(date_range_1) \
        .filterBounds(region_polygon) \
        .filter(ee.Filter.calendarRange(month_int, month_int, 'month')) \
        .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover))
    
    collection_b = ee.ImageCollection(collection_2) \
        .filterDate(date_range_2) \
        .filterBounds(region_polygon) \
        .filter(ee.Filter.calendarRange(month_int, month_int, 'month')) \
        .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover))

    # Apply cloud mask and NDSI calculation
    collection_a_ndsi = collection_a.map(mask_clouds_landsat).map(ndsi_l5)
    collection_b_ndsi = collection_b.map(mask_clouds_landsat).map(ndsi_l9)

    # Calculate weighted averages
    weighted_avg_a = create_weighted_average(collection_a_ndsi)
    weighted_avg_b = create_weighted_average(collection_b_ndsi)

    # Calculate difference
    difference_image = weighted_avg_b.select('NDSI').subtract(weighted_avg_a.select('NDSI')).rename('NDSI_Difference')

    # Clip images to region if requested
    if clip_to_region:
        weighted_avg_a = weighted_avg_a.clip(region_polygon)
        weighted_avg_b = weighted_avg_b.clip(region_polygon)
        difference_image = difference_image.clip(region_polygon)

    # Create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define spatial reference (Web Mercator for consistency)
    crs = 'EPSG:3857'
    
    # Calculate appropriate scale based on region size
    bounds = region_polygon.bounds().getInfo()
    coords = bounds['coordinates'][0]
    lat_range = abs(coords[2][1] - coords[0][1])
    lon_range = abs(coords[1][0] - coords[0][0])
    max_range = max(lat_range, lon_range)
    
    if max_range > 20:
        scale = 1000  # 1km for large areas
    elif max_range > 5:
        scale = 500   # 500m for medium areas
    else:
        scale = 250   # 250m for small areas

    # Export individual layers with spatial reference
    if export_by_layer and output_format.lower() in ['tiff', 'png', 'jpg']:
        import requests
        
        layers = [
            (weighted_avg_a.select('NDSI'), f"{output_filename}_historical"),
            (weighted_avg_b.select('NDSI'), f"{output_filename}_recent"),
            (difference_image, f"{output_filename}_difference")
        ]
        
        for image, name in layers:
            export_path = os.path.join(output_folder, f"{name}.{output_format}")
            
            # Get download URL with spatial reference
            url = image.getDownloadURL({
                'region': region_polygon,
                'scale': scale,
                'crs': crs,
                'format': 'GeoTIFF' if output_format.lower() == 'tiff' else output_format.upper()
            })
            
            # Download and save
            response = requests.get(url)
            with open(export_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Exported: {export_path} (CRS: {crs}, Scale: {scale}m)")
    
    # Create folium map
    polygon_center = region_polygon.centroid().coordinates().getInfo()[::-1]
    zoom_start = 8 if max_range < 5 else 6 if max_range < 20 else 4
    
    m = folium.Map(location=polygon_center, zoom_start=zoom_start)
    
    # Add layers to map
    add_ee_layer(m, weighted_avg_a.select('NDSI'), ndsi_vis, 'Historical NDSI')
    add_ee_layer(m, weighted_avg_b.select('NDSI'), ndsi_vis, 'Recent NDSI')
    add_ee_layer(m, difference_image, diff_vis, 'NDSI Difference')
    
    folium.LayerControl().add_to(m)
    
    # Save HTML map if requested or as default with layer export
    if output_format.lower() == 'html' or export_by_layer:
        html_path = os.path.join(output_folder, f"{output_filename}.html")
        m.save(html_path)
        print(f"Saved interactive map: {html_path}")
    
    return m

