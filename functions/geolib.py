import sys
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