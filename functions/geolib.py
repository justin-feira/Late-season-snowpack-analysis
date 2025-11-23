import sys
import pandas as pd
sys.path.append('./Setup')
from gee_setup import *
setup_gee()

def add_ee_layer(self, ee_image_object, vis_params, name):
    """Add a method for displaying Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True
    ).add_to(self)


def create_map(center=[0, 0], zoom=2):
    """Create a folium map with Earth Engine layer support."""
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
    return m

def get_image_collection_info(collection_name, start_date='2020-01-01', end_date='2023-12-31'):
    """Get basic information about an Earth Engine ImageCollection."""
    try:
        collection = ee.ImageCollection(collection_name).filterDate(start_date, end_date)
        size = collection.size().getInfo()
        first_image = ee.Image(collection.first())
        bands = first_image.bandNames().getInfo()
        
        print(f"Collection: {collection_name}")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Number of images: {size}")
        print(f"Bands available: {bands}")
        
        return collection
    except Exception as e:
        print(f"Error accessing collection {collection_name}: {e}")
        return None
    

def ndsi_l5(image):
    """Calculate NDSI for Landsat 5/7 (Green=B2, SWIR=B5)"""
    ndsi = image.normalizedDifference(['SR_B2', 'SR_B5']).rename('NDSI')
    snow_mask = ndsi.gt(0.4).And(image.select('SR_B2').gt(1100)).rename('snow_cover')
    return image.addBands([ndsi, snow_mask])

def ndsi_l9(image):
    """Calculate NDSI for Landsat 8/9 (Green=B3, SWIR=B6)"""
    ndsi = image.normalizedDifference(['SR_B3', 'SR_B6']).rename('NDSI')
    snow_mask = ndsi.gt(0.4).And(image.select('SR_B3').gt(1100)).rename('snow_cover')
    return image.addBands([ndsi, snow_mask])

def mask_clouds_landsat(image):
   
    qa = image.select('QA_PIXEL')
    
    # Correct bit assignments for Landsat Collection 2
    cloud_bit_mask = (1 << 3)        # Bit 3: Cloud
    cloud_shadow_bit_mask = (1 << 4)  # Bit 4: Cloud Shadow
    cirrus_bit_mask = (1 << 2)       # Bit 2: Cirrus (L8/L9)
    
    # Clear conditions = all these bits should be 0
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0) \
             .And(qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0)) \
             .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    
    return image.updateMask(mask)

## view the number of images available in each individual year, along with each individual week

def count_images_by_year(collection):
    def year_count(year):
        start = ee.Date.fromYMD(year, 1, 1)
        end = start.advance(1, 'year')
        count = collection.filterDate(start, end).size()
        return ee.Feature(None, {'year': year, 'image_count': count})
    
    years = ee.List.sequence(1980, 2025)
    counts = years.map(year_count)
    return ee.FeatureCollection(counts)

def image_count(collection, start_year, end_year):
    counts = []
    for year in range(start_year, end_year + 1):
        start = ee.Date.fromYMD(year, 1, 1)
        end = start.advance(1, 'year')
        count = collection.filterDate(start, end).size().getInfo()
        counts.append({'year': year, 'image_count': count})
    return pd.DataFrame(counts)
## add a week function to further identify time frame with most images
def count_images_by_week(collection, year):
    def week_count(week):
        start = ee.Date.fromYMD(year, 1, 1).advance(week, 'week')
        end = start.advance(1, 'week')
        count = collection.filterDate(start, end).size()
        return ee.Feature(None, {'week': week, 'image_count': count})
    
    weeks = ee.List.sequence(0, 51)
    counts = weeks.map(week_count)
    return ee.FeatureCollection(counts)



def yearly_composite(year, collection):
    year_images = collection.filter(ee.Filter.calendarRange(year, year, 'year'))
    count = year_images.size()
    composite = year_images.mean()
    return composite.set('year', year).set('image_count', count)

def create_weighted_average(collection) -> ee.Image:
    years = collection.aggregate_array('system:time_start') \
    .map(lambda date: ee.Date(date) \
    .get('year')).distinct().sort()

    ## list of yearly_composite objects
    yearly_composites = []
    for year in years.getInfo():
        yearly_composites.append(yearly_composite(year, collection))

    ## convert list back into image collection
    composite_collection = ee.ImageCollection.fromImages(yearly_composites)

    ## average the yearly composites
    return composite_collection.mean()
    

def add_ee_layer(folium_map, ee_image, vis_params, name, show=True):
    """
    Add an Earth Engine image to a Folium map
    
    Args:
        folium_map: Folium map object
        ee_image: Earth Engine image
        vis_params: Visualization parameters dict
        name: Layer name for the map
        show: Whether layer is visible by default
    """
    map_id_dict = ee_image.getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
        show=show
    ).add_to(folium_map)
    
    return folium_map

