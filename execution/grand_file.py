import ee
import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import Image, display
import json
import sys
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
    """Create a folium map showing NDSI difference between two date ranges.
    
 def snow_difference_map(
    region_polygon,                                    # REQUIRED: ee.Geometry.Polygon
    date_range_1 = ee.DateRange('1990-01-01', '2000-01-01'),  # Early period
    date_range_2 = ee.DateRange('2015-01-01', '2025-01-01'),  # Recent period  
    collection_1 = 'LANDSAT/LT05/C02/T1_L2',         # Landsat 5 (historical)
    collection_2 = 'LANDSAT/LC08/C02/T1_L2',         # Landsat 8 (recent)
    month_int = 6,                                    # Month filter (1-12)
    cloud_cover = 10,                                 # Max cloud % (0-100)
    clip_to_region = False,                           # Clip to polygon bounds
    ndsi_vis = {...},                                 # NDSI visualization
    snow_vis = {...},                                 # Binary snow visualization  
    diff_vis = {...}                                  # Difference visualization
)
    """
    
    # load and process first collection (landsat 5)
    collection_a = ee.ImageCollection(collection_1) \
        .filterDate(date_range_1) \
    .filterBounds(region_polygon) \
    .filter(ee.Filter.calendarRange(month_int, month_int, 'month')) \
    .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover))
    # landsat 9
    collection_b = ee.ImageCollection(collection_2) \
        .filterDate(date_range_2) \
        .filterBounds(region_polygon) \
    .filter(ee.Filter.calendarRange(month_int, month_int, 'month')) \
    .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover))

    # apply cloud mask and NDSI calculation
    collection_a_ndsi = collection_a.map(mask_clouds_landsat).map(ndsi_l5)
    collection_b_ndsi = collection_b.map(mask_clouds_landsat).map(ndsi_l9)

    # calculate yearly weighted average with all available data
    weighted_avg_a = create_weighted_average(collection_a_ndsi)
    weighted_avg_b = create_weighted_average(collection_b_ndsi)

    # calculate difference
    difference_image = weighted_avg_b.select('NDSI').subtract(weighted_avg_a.select('NDSI')).rename('NDSI_Difference')

    # clip images to region if requested
    if clip_to_region:
        weighted_avg_a = weighted_avg_a.clip(region_polygon)
        weighted_avg_b = weighted_avg_b.clip(region_polygon)
        difference_image = difference_image.clip(region_polygon)
        print("🔲 Images clipped to polygon bounds")

    # create folium map
    polygon_center = region_polygon.centroid().coordinates().getInfo()[::-1]  # reverse for folium
    m = folium.Map(location=polygon_center, zoom_start=8)

    # add layers to map
    add_ee_layer(m, weighted_avg_a.select('NDSI'), ndsi_vis, f'NDSI Early Period Average')
    add_ee_layer(m, weighted_avg_b.select('NDSI'), ndsi_vis, f'NDSI Recent Period Average')
    add_ee_layer(m, difference_image, diff_vis, 'NDSI Difference (Recent - Early)')

    # Add layer control and save map
    folium.LayerControl().add_to(m)
    m.save('snow_difference_analysis.html')
    print("✅ Interactive map saved as 'snow_difference_analysis.html'")
    
    return m

