# Late Season Snowpack Analysis

This repository provides tools for analyzing changes in snow cover between two time periods using Landsat satellite data and Google Earth Engine. The main function `snow_difference_map` creates interactive maps showing snow cover differences within user-defined regions.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/justin-feira/Late-season-snowpack-analysis.git
   cd Late-season-snowpack-analysis
   ```

2. **Create conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate gee-env
   ```

3. **Authenticate with Google Earth Engine:**
   ```bash
   earthengine authenticate
   ```

## Usage

### Initialize Environment
```python
import sys
sys.path.append('./Setup')
from gee_setup import *
setup_gee()

# Import the analysis function
sys.path.append('./execution')
from grand_file import snow_difference_map
```

### Basic Analysis
```python
import ee

# Define study area polygon
aoi = ee.Geometry.Polygon([[
    [-106.99065650552905, 39.088354116315266],
    [-106.71050513834155, 38.652122067998306], 
    [-106.14470923990405, 38.596331654032184],
    [-106.40838111490405, 39.21189167999414],
    [-106.99065650552905, 39.088354116315266]
]])

# Create snow difference map
snow_map = snow_difference_map(aoi)
```

### Advanced Usage
```python
# Full parameter control
snow_map = snow_difference_map(
    region_polygon=aoi,
    date_range_1=ee.DateRange('1990-01-01', '2000-01-01'),
    date_range_2=ee.DateRange('2015-01-01', '2025-01-01'),
    collection_1='LANDSAT/LT05/C02/T1_L2',
    collection_2='LANDSAT/LC08/C02/T1_L2',
    month_int=6,
    cloud_cover=10,
    clip_to_region=False,
    output_folder='outputs',
    output_filename='my_analysis',
    output_format='html'
)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `region_polygon` | Required | Earth Engine Geometry polygon defining study area |
| `date_range_1` | `1990-2000` | Historical time period for comparison |
| `date_range_2` | `2015-2025` | Recent time period for comparison |
| `collection_1` | `LANDSAT/LT05/C02/T1_L2` | Satellite collection for historical data |
| `collection_2` | `LANDSAT/LC08/C02/T1_L2` | Satellite collection for recent data |
| `month_int` | `6` | Month filter for seasonal analysis (1-12) |
| `cloud_cover` | `10` | Maximum cloud cover percentage (0-100) |
| `clip_to_region` | `False` | Clip output images to polygon bounds |
| `output_folder` | `outputs` | Output folder for map file |
| `output_filename` | `snow_difference_analysis` | Output filename without extension |
| `output_format` | `tiff` | Output format (tiff, png, jpg, html) |

## Output

The function creates high-quality analysis outputs in multiple formats:

### Static Images (Default: TIFF)
- **Three-panel visualization** showing historical, recent, and difference maps
- **High resolution** (300 DPI) suitable for publications
- **Geographic coordinates** and region boundaries
- **Formats available**: TIFF (uncompressed), PNG, JPG

### Interactive Maps (HTML)
- **Folium-based** interactive web maps with layer controls
- **Three toggleable layers**: Historical NDSI, Recent NDSI, NDSI Difference
- **Zoom and pan** capabilities for detailed exploration

### Data Interpretation
- **Historical NDSI Average** - Snow conditions from the earlier period
- **Recent NDSI Average** - Snow conditions from the later period  
- **NDSI Difference** - Change detection (red = snow increase, blue = snow decrease)

All outputs are automatically saved to the specified output folder with persistent file formats.

## NDSI Explanation

NDSI (Normalized Difference Snow Index) identifies snow-covered areas using Landsat satellite bands. Values range from -1 to 1, where higher values indicate snow presence. Snow is bright in the visible spectrum, but dark in infrared, so a normalized difference of green and short wave infrared easily identifies snow covered areas from space.

### Formula

```
NDSI = (Green - SWIR) / (Green + SWIR)
```

### Band Implementation

- **Landsat 5/7**: `NDSI = (Band 2 - Band 5) / (Band 2 + Band 5)`
- **Landsat 8/9**: `NDSI = (Band 3 - Band 6) / (Band 3 + Band 6)`

Where:

- **Green** = Visible green light band (0.52-0.60 μm)
- **SWIR** = Short-wave infrared band (1.55-1.75 μm)

### Interpretation

- **NDSI > 0.4**: Typically indicates snow cover
- **NDSI 0.0 to 0.4**: Mixed pixels or thin snow
- **NDSI < 0.0**: Bare ground, vegetation, or water

Snow has high reflectance in visible light but low reflectance in short-wave infrared, making this ratio effective for snow detection.

## Repository Structure

```
Late-season-snowpack-analysis/
├── Setup/              # Google Earth Engine initialization
├── functions/          # Core analysis functions
├── execution/          # Main analysis scripts and notebooks
├── environment.yml     # Conda environment specification
└── requirements.txt    # Python package dependencies
```

## License

This project is open source.