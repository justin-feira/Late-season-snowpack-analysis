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
    output_folder = 'outputs',                        # Output folder for map file
    output_filename = 'snow_difference_analysis',     # Output filename (no extension)
    output_format = 'tiff',                           # Output format ('tiff', 'png', 'jpg', 'html')
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

    # Check if collections have any images
    size_a = collection_a.size()
    size_b = collection_b.size()
    
    # Get actual counts to validate
    count_a = size_a.getInfo()
    count_b = size_b.getInfo()
    
    if count_a == 0:
        raise ValueError(f"No images found for period 1 ({date_range_1.start().getInfo()['value']} to {date_range_1.end().getInfo()['value']}) with current filters. Try increasing cloud cover threshold or expanding date range.")
    
    if count_b == 0:
        raise ValueError(f"No images found for period 2 ({date_range_2.start().getInfo()['value']} to {date_range_2.end().getInfo()['value']}) with current filters. Try increasing cloud cover threshold or expanding date range.")
    
    print(f"Found {count_a} images for period 1 and {count_b} images for period 2")

    # apply cloud mask and NDSI calculation
    collection_a_ndsi = collection_a.map(mask_clouds_landsat).map(ndsi_l5)
    collection_b_ndsi = collection_b.map(mask_clouds_landsat).map(ndsi_l9)

    # calculate yearly weighted average with all available data
    try:
        weighted_avg_a = create_weighted_average(collection_a_ndsi)
        weighted_avg_b = create_weighted_average(collection_b_ndsi)
        
        # Validate that the averages have the NDSI band
        bands_a = weighted_avg_a.bandNames().getInfo()
        bands_b = weighted_avg_b.bandNames().getInfo()
        
        if 'NDSI' not in bands_a:
            raise ValueError(f"Period 1 average image missing NDSI band. Available bands: {bands_a}")
        if 'NDSI' not in bands_b:
            raise ValueError(f"Period 2 average image missing NDSI band. Available bands: {bands_b}")
            
    except Exception as e:
        raise ValueError(f"Error creating weighted averages: {str(e)}")

    # calculate difference with error handling
    try:
        difference_image = weighted_avg_b.select('NDSI').subtract(weighted_avg_a.select('NDSI')).rename('NDSI_Difference')
    except Exception as e:
        raise ValueError(f"Error calculating NDSI difference: {str(e)}")

    # clip images to region if requested
    if clip_to_region:
        weighted_avg_a = weighted_avg_a.clip(region_polygon)
        weighted_avg_b = weighted_avg_b.clip(region_polygon)
        difference_image = difference_image.clip(region_polygon)

    # create folium map with error handling for large polygons
    try:
        polygon_center = region_polygon.centroid().coordinates().getInfo()[::-1]  # reverse for folium
    except Exception as e:
        # Fallback for very large polygons that might timeout
        print(f"Warning: Could not compute polygon centroid, using default center: {str(e)}")
        polygon_center = [40, -100]  # Default center
    
    # Adjust zoom based on polygon size
    try:
        bounds = region_polygon.bounds().getInfo()
        coords = bounds['coordinates'][0]
        lat_range = abs(coords[2][1] - coords[0][1])
        lon_range = abs(coords[1][0] - coords[0][0])
        max_range = max(lat_range, lon_range)
        
        if max_range > 100:  # Very large area
            zoom_start = 2
        elif max_range > 50:  # Large area
            zoom_start = 3
        elif max_range > 20:  # Medium area
            zoom_start = 4
        elif max_range > 5:   # Small-medium area
            zoom_start = 6
        else:                 # Small area
            zoom_start = 8
    except:
        zoom_start = 2  # Safe default for large areas
    
    m = folium.Map(location=polygon_center, zoom_start=zoom_start)

    # add layers to map
    add_ee_layer(m, weighted_avg_a.select('NDSI'), ndsi_vis, f'NDSI Early Period Average')
    add_ee_layer(m, weighted_avg_b.select('NDSI'), ndsi_vis, f'NDSI Recent Period Average')
    add_ee_layer(m, difference_image, diff_vis, 'NDSI Difference (Recent - Early)')

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Create output path with specified filename and format
    output_path = os.path.join(output_folder, f"{output_filename}.{output_format}")
    
    # Save map based on output format
    if output_format.lower() == 'html':
        m.save(output_path)
        print(f"Saved interactive HTML map: {output_path}")
    elif output_format.lower() in ['png', 'jpg', 'jpeg', 'tiff']:
        # Create static image using matplotlib
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from matplotlib.colors import ListedColormap, Normalize
            from matplotlib.patches import Polygon as mpl_Polygon
            
            # Get region bounds for plotting
            bounds = region_polygon.bounds().getInfo()
            coords = bounds['coordinates'][0]
            min_lon, min_lat = coords[0]
            max_lon, max_lat = coords[2]
            
            # Create figure with subplots
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle(f'Snow Difference Analysis - {get_month_name(month_int)}', fontsize=16)
            
            # Define extent for all plots
            extent = [min_lon, max_lon, min_lat, max_lat]
            
            # Get thumbnail images from Earth Engine
            try:
                # Period 1 NDSI
                ndsi1_url = weighted_avg_a.select('NDSI').getThumbUrl({
                    'min': ndsi_vis['min'], 'max': ndsi_vis['max'],
                    'palette': ndsi_vis['palette'],
                    'region': region_polygon,
                    'dimensions': 512
                })
                
                # Period 2 NDSI  
                ndsi2_url = weighted_avg_b.select('NDSI').getThumbUrl({
                    'min': ndsi_vis['min'], 'max': ndsi_vis['max'],
                    'palette': ndsi_vis['palette'],
                    'region': region_polygon,
                    'dimensions': 512
                })
                
                # Difference
                diff_url = difference_image.getThumbUrl({
                    'min': diff_vis['min'], 'max': diff_vis['max'],
                    'palette': diff_vis['palette'],
                    'region': region_polygon,
                    'dimensions': 512
                })
                
                # Download and display images
                import requests
                from PIL import Image
                
                # Get images
                img1 = Image.open(requests.get(ndsi1_url, stream=True).raw)
                img2 = Image.open(requests.get(ndsi2_url, stream=True).raw)
                img3 = Image.open(requests.get(diff_url, stream=True).raw)
                
                # Plot images
                axes[0].imshow(img1, extent=extent)
                axes[0].set_title('Historical NDSI Average')
                axes[0].set_xlabel('Longitude')
                axes[0].set_ylabel('Latitude')
                
                axes[1].imshow(img2, extent=extent)
                axes[1].set_title('Recent NDSI Average')
                axes[1].set_xlabel('Longitude')
                axes[1].set_ylabel('')
                
                axes[2].imshow(img3, extent=extent)
                axes[2].set_title('NDSI Difference (Recent - Historical)')
                axes[2].set_xlabel('Longitude')
                axes[2].set_ylabel('')
                
                # Add region outline to all plots
                region_coords = region_polygon.coordinates().getInfo()[0]
                for ax in axes:
                    polygon = mpl_Polygon(region_coords, fill=False, edgecolor='red', linewidth=2)
                    ax.add_patch(polygon)
                    ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                # Save with specified format
                if output_format.lower() == 'tiff':
                    plt.savefig(output_path, format='tiff', dpi=300, bbox_inches='tight')
                else:
                    plt.savefig(output_path, format=output_format.lower(), dpi=300, bbox_inches='tight')
                
                plt.close()
                print(f"Saved static image: {output_path}")
                
            except Exception as thumb_error:
                print(f"Earth Engine thumbnail export failed: {thumb_error}")
                # Fallback: save as HTML
                output_path = os.path.join(output_folder, f"{output_filename}.html")
                m.save(output_path)
                print(f"Fallback: Saved as HTML instead: {output_path}")
                
        except ImportError as e:
            print(f"Missing dependencies for image export: {e}")
            print("Installing: pip install matplotlib pillow requests")
            # Fallback to HTML
            output_path = os.path.join(output_folder, f"{output_filename}.html")
            m.save(output_path)
            print(f"Fallback: Saved as HTML: {output_path}")
            
        except Exception as e:
            print(f"Error creating static image: {e}")
            # Fallback to HTML
            output_path = os.path.join(output_folder, f"{output_filename}.html")
            m.save(output_path)
            print(f"Fallback: Saved as HTML: {output_path}")
    else:
        # Default to HTML for unsupported formats
        output_path = os.path.join(output_folder, f"{output_filename}.html")
        m.save(output_path)
        print(f"Unsupported format, saved as HTML: {output_path}")
    
    return m

