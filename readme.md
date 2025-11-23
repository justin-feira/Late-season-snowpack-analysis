# Snow Difference Map

This repository provides the function `snow_difference_map`, which allows users to analyze changes in snow cover within a given polygon between two time periods using Landsat satellite data.

## Quick Start

### Setup
```python
# Initialize Google Earth Engine and import required packages
import sys
sys.path.append('./Setup')
from gee_setup import *
setup_gee()

# Import the snow analysis function
from grand_file import snow_difference_map
```

### Basic Usage
```python
# Define your study area (Rocky Mountains example)
aoi = ee.Geometry.Polygon([[
    [-106.99065650552905, 39.088354116315266],
    [-106.71050513834155, 38.652122067998306], 
    [-106.14470923990405, 38.596331654032184],
    [-106.40838111490405, 39.21189167999414],
    [-106.99065650552905, 39.088354116315266]
]])

# Create snow change analysis map
snow_map = snow_difference_map(aoi)
snow_map
```
**DISCLAIMER**: the default usage is set with the default parameters used by my personal project, so for any other usage, other parameters must be additionally specified. See below.
Additionally, cloud masking is automatically performed by the function. 
### Usage with All Parameters
```python
# Custom analysis with full parameter control
comprehensive_map = snow_difference_map(
    region_polygon=aoi,                                      # Study area polygon
    date_range_1=ee.DateRange('1985-01-01', '1995-01-01'), # Historical period
    date_range_2=ee.DateRange('2018-01-01', '2023-01-01'), # Recent period
    collection_1='LANDSAT/LT05/C02/T1_L2',                 # Landsat 5 (historical)
    collection_2='LANDSAT/LC08/C02/T1_L2',                 # Landsat 8 (recent)
    month_int=5,                                            # May (1-12)
    cloud_cover=15,                                         # Max 15% clouds
    clip_to_region=True,                                    # Clip to polygon
    # Custom visualization parameters available for ndsi_vis, snow_vis, diff_vis
)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `region_polygon` | *Required* | Earth Engine Geometry polygon defining study area |
| `date_range_1` | `1990-2000` | Historical time period for comparison |
| `date_range_2` | `2015-2025` | Recent time period for comparison |
| `collection_1` | `Landsat 5` | Satellite collection for historical data |
| `collection_2` | `Landsat 8` | Satellite collection for recent data |
| `month_int` | `6` (June) | Month filter for seasonal analysis (1-12) |
| `cloud_cover` | `10` | Maximum cloud cover percentage (0-100) |
| `clip_to_region` | `False` | Clip output images to polygon bounds |

## Output

The function returns an interactive Folium map with three toggleable layers:
- **Historical NDSI Average** - Snow conditions from the earlier period
- **Recent NDSI Average** - Snow conditions from the later period  
- **NDSI Difference** - Change detection (red = snow increase, blue = snow decrease)

The map is automatically saved as `'snow_difference_analysis.html'` for sharing and offline viewing.

## What is NDSI?

NDSI (Normalized Difference Snow Index) is calculated from Landsat satellite bands to identify snow-covered areas. Values range from -1 to 1, where higher values indicate snow presence and lower values indicate bare ground or water.

### NDSI Formula

```
NDSI = (Green - SWIR) / (Green + SWIR)
```

**For Landsat satellites:**
- **Landsat 5/7**: `NDSI = (Band 2 - Band 5) / (Band 2 + Band 5)`
- **Landsat 8/9**: `NDSI = (Band 3 - Band 6) / (Band 3 + Band 6)`

Where:
- **Green** = Visible green light band (0.52-0.60 μm)
- **SWIR** = Short-wave infrared band (1.55-1.75 μm)

### Interpretation
- **NDSI > 0.4**: Typically indicates snow cover
- **NDSI 0.0 to 0.4**: Mixed pixels or thin snow
- **NDSI < 0.0**: Bare ground, vegetation, or water

Snow has high reflectance in the visible spectrum but low reflectance in the short-wave infrared, making this ratio effective for snow detection.