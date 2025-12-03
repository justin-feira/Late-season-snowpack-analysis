import ee
import folium
import os
import sys
import requests

# Setup Earth Engine
sys.path.append('../Setup')
from gee_setup import *
setup_gee()

# Import analysis functions
sys.path.append('../functions')
from geolib import (
    mask_clouds_landsat,
    ndsi_l5,
    ndsi_l9,
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
    
    # Calculate area to determine optimal export resolution
    bounds = region_polygon.bounds().getInfo()
    coords = bounds['coordinates'][0]
    lat_range = abs(coords[2][1] - coords[0][1])
    lon_range = abs(coords[1][0] - coords[0][0])
    area_sq_deg = lat_range * lon_range
    
    # Set resolution based on area size (avoids 50MB export limit)
    if area_sq_deg > 25:
        scale, max_pixels = 500, int(1e7)
    elif area_sq_deg > 10:
        scale, max_pixels = 250, int(5e7)
    elif area_sq_deg > 1:
        scale, max_pixels = 120, int(1e8)
    else:
        scale, max_pixels = 30, int(1e9)
    
    print(f"Area: {area_sq_deg:.1f} sq deg, Resolution: {scale}m")

    def export_image(image, filepath, scale, max_pixels, visualize=False, vis_params=None):
        """Export a single image with error handling and fallback resolution."""
        try:
            if visualize and vis_params:
                export_image = image.visualize(**vis_params)
            else:
                export_image = image
            
            url = export_image.getDownloadURL({
                'region': region_polygon,
                'scale': scale,
                'crs': crs,
                'format': 'GeoTIFF' if filepath.endswith('.tiff') else output_format.upper(),
                'maxPixels': max_pixels
            })
            
            response = requests.get(url)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True, scale
            
        except Exception as e:
            if "must be less than or equal to" in str(e) and scale < 1000:
                # Retry with double resolution
                return export_image(image, filepath, scale * 2, max_pixels // 4, visualize, vis_params)
            return False, str(e)
    
    # Export individual layers (50MB limit applies to direct exports only, not HTML maps)
    if export_by_layer and output_format.lower() in ['tiff', 'png', 'jpg']:
        layers = [
            (weighted_avg_a.select('NDSI'), f"{output_filename}_historical", ndsi_vis),
            (weighted_avg_b.select('NDSI'), f"{output_filename}_recent", ndsi_vis),
            (difference_image, f"{output_filename}_difference", diff_vis)
        ]
        
        for image, name, vis_params in layers:
            if output_format.lower() == 'tiff':
                # Create output folders
                raw_folder = os.path.join(output_folder, 'raw_data')
                vis_folder = os.path.join(output_folder, 'visualized')
                os.makedirs(raw_folder, exist_ok=True)
                os.makedirs(vis_folder, exist_ok=True)
                
                # Export raw data (actual NDSI values)
                raw_path = os.path.join(raw_folder, f"{name}_raw.tiff")
                success, result = export_image(image, raw_path, scale, max_pixels)
                if success:
                    print(f"Raw data exported: {raw_path} ({result}m)")
                else:
                    print(f"Raw export failed: {result}")
                
                # Export visualized data (RGB colored)
                vis_path = os.path.join(vis_folder, f"{name}_visualized.tiff")
                success, result = export_image(image, vis_path, scale, max_pixels, True, vis_params)
                if success:
                    print(f"Visualized exported: {vis_path} ({result}m)")
                else:
                    print(f"Visualized export failed: {result}")
            
            else:
                # For PNG/JPG, export only visualized version
                export_path = os.path.join(output_folder, f"{name}.{output_format}")
                success, result = export_image(image, export_path, scale, max_pixels, True, vis_params)
                if success:
                    print(f"Exported: {export_path} ({result}m)")
                else:
                    print(f"Export failed: {result}")
    
    # Create interactive map (HTML maps have no size limits)
    try:
        center = region_polygon.centroid().coordinates().getInfo()[::-1]
        zoom = 8 if area_sq_deg < 1 else 6 if area_sq_deg < 10 else 4
        
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Add all layers to map
        add_ee_layer(m, weighted_avg_a.select('NDSI'), ndsi_vis, 'Historical NDSI')
        add_ee_layer(m, weighted_avg_b.select('NDSI'), ndsi_vis, 'Recent NDSI')
        add_ee_layer(m, difference_image, diff_vis, 'NDSI Difference')
        folium.LayerControl().add_to(m)
        
        # Save HTML map
        if output_format.lower() == 'html' or export_by_layer:
            html_path = os.path.join(output_folder, f"{output_filename}.html")
            m.save(html_path)
            print(f"Interactive map saved: {html_path}")
        
        return m
    
    except Exception as e:
        print(f"Map creation failed: {str(e)}")
        return folium.Map(location=[0, 0], zoom_start=2)

