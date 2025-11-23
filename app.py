"""
Interactive Streamlit App for Snow Difference Analysis

This app provides a user-friendly interface for analyzing changes in snow cover
between two time periods using satellite data from Google Earth Engine.
"""

import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap
from datetime import date, datetime
import sys
import os

# Add paths for imports
sys.path.append('./Setup')
sys.path.append('./execution')
sys.path.append('./functions')

from gee_setup import setup_gee
from grand_file import snow_difference_map
from app_utils import (
    convert_geojson_to_ee_geometry,
    validate_parameters,
    format_date_for_ee,
    suggest_landsat_collection,
    get_month_name
)

# Page configuration
st.set_page_config(
    page_title="Snow Difference Analyzer",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_earth_engine():
    """Initialize Google Earth Engine (cached to run only once)."""
    try:
        # Try to initialize without authentication
        ee.Initialize()
        return True, "Google Earth Engine initialized successfully!"
    except Exception as e:
        try:
            # If that fails, try authenticating
            ee.Authenticate()
            ee.Initialize()
            return True, "Google Earth Engine authenticated and initialized!"
        except Exception as e2:
            return False, f"Failed to initialize Google Earth Engine: {str(e2)}"


def create_map_with_drawing():
    """Create an interactive map with polygon drawing capability."""
    # Create a leafmap Map with drawing controls
    m = leafmap.Map(
        center=[40, -100],  # Center of USA
        zoom=4,
        draw_control=True,
        measure_control=False,
        fullscreen_control=True,
        attribution_control=True
    )
    
    # Configure drawing options to only allow polygons
    m.add_basemap("OpenStreetMap")
    
    return m


def main():
    """Main application function."""
    
    # Header
    st.markdown('<p class="main-header">❄️ Snow Difference Analyzer</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Welcome!</strong> This tool helps you analyze changes in snow cover between two time periods 
    using Landsat satellite data. Draw a polygon on the map, select your parameters, and run the analysis.
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Google Earth Engine
    with st.spinner("Initializing Google Earth Engine..."):
        gee_initialized, gee_message = initialize_earth_engine()
    
    if not gee_initialized:
        st.markdown(f'<div class="error-box">{gee_message}</div>', unsafe_allow_html=True)
        st.stop()
    else:
        st.success(gee_message)
    
    # Create two columns: map on left, controls on right
    col_map, col_controls = st.columns([2, 1])
    
    with col_map:
        st.subheader("📍 Step 1: Draw Your Region of Interest")
        st.info("Use the polygon tool (⬠) in the map toolbar to draw your region. Click to add points, double-click to finish.")
        
        # Create and display the map
        m = create_map_with_drawing()
        map_data = st_folium(m, width=700, height=500)
    
    # Extract polygon from map
    drawn_polygon = None
    ee_geometry = None
    
    if map_data and map_data.get("last_active_drawing"):
        drawn_polygon = map_data["last_active_drawing"]
        ee_geometry = convert_geojson_to_ee_geometry(drawn_polygon)
        
        if ee_geometry:
            st.success("✅ Polygon captured successfully!")
        else:
            st.warning("⚠️ Could not process the drawn polygon. Please try drawing again.")
    elif map_data and map_data.get("all_drawings") and len(map_data["all_drawings"]) > 0:
        # Try to get the last drawing
        drawn_polygon = map_data["all_drawings"][-1]
        ee_geometry = convert_geojson_to_ee_geometry(drawn_polygon)
        
        if ee_geometry:
            st.success("✅ Polygon captured successfully!")
    
    with col_controls:
        st.subheader("⚙️ Step 2: Configure Parameters")
        
        # Date range inputs
        st.markdown("**📅 Historical Period (Period 1)**")
        col1, col2 = st.columns(2)
        with col1:
            start_date_1 = st.date_input(
                "Start Date",
                value=date(1990, 1, 1),
                min_value=date(1984, 1, 1),
                max_value=date.today(),
                key="start_1"
            )
        with col2:
            end_date_1 = st.date_input(
                "End Date",
                value=date(2000, 1, 1),
                min_value=date(1984, 1, 1),
                max_value=date.today(),
                key="end_1"
            )
        
        st.markdown("**📅 Recent Period (Period 2)**")
        col3, col4 = st.columns(2)
        with col3:
            start_date_2 = st.date_input(
                "Start Date",
                value=date(2015, 1, 1),
                min_value=date(1984, 1, 1),
                max_value=date.today(),
                key="start_2"
            )
        with col4:
            end_date_2 = st.date_input(
                "End Date",
                value=date(2024, 1, 1),
                min_value=date(1984, 1, 1),
                max_value=date.today(),
                key="end_2"
            )
        
        st.markdown("---")
        
        # Month selector
        month = st.slider(
            "🗓️ Month Filter",
            min_value=1,
            max_value=12,
            value=6,
            help="Select the month to analyze (1=January, 12=December)"
        )
        st.caption(f"Selected: {get_month_name(month)}")
        
        # Cloud cover threshold
        cloud_cover = st.slider(
            "☁️ Max Cloud Cover (%)",
            min_value=0,
            max_value=100,
            value=10,
            help="Maximum cloud cover percentage allowed in images"
        )
        
        # Clip to region
        clip_to_region = st.checkbox(
            "✂️ Clip to Region",
            value=False,
            help="Clip output images to polygon bounds"
        )
        
        st.markdown("---")
        
        # Advanced options (collapsible)
        with st.expander("🔧 Advanced Options"):
            st.info("Landsat collections are automatically suggested based on your date ranges.")
            
            # Suggest collections
            collection_1 = suggest_landsat_collection(start_date_1.year, end_date_1.year)
            collection_2 = suggest_landsat_collection(start_date_2.year, end_date_2.year)
            
            collection_1 = st.text_input(
                "Period 1 Landsat Collection",
                value=collection_1,
                help="Earth Engine collection ID for historical period"
            )
            
            collection_2 = st.text_input(
                "Period 2 Landsat Collection",
                value=collection_2,
                help="Earth Engine collection ID for recent period"
            )
        
        st.markdown("---")
        
        # Run button
        run_analysis = st.button(
            "🚀 Run Snow Difference Analysis",
            type="primary",
            use_container_width=True
        )
    
    # Process analysis when button is clicked
    if run_analysis:
        # Validate all parameters
        is_valid, error_msg = validate_parameters(
            ee_geometry,
            start_date_1,
            end_date_1,
            start_date_2,
            end_date_2,
            month,
            cloud_cover
        )
        
        if not is_valid:
            st.markdown(f'<div class="error-box"><strong>Validation Error:</strong> {error_msg}</div>', 
                       unsafe_allow_html=True)
        else:
            # Run the analysis
            with st.spinner("🔄 Running analysis... This may take a minute or two."):
                try:
                    # Create date ranges for EE
                    date_range_1 = ee.DateRange(
                        format_date_for_ee(start_date_1),
                        format_date_for_ee(end_date_1)
                    )
                    date_range_2 = ee.DateRange(
                        format_date_for_ee(start_date_2),
                        format_date_for_ee(end_date_2)
                    )
                    
                    # Call the snow difference function
                    result_map = snow_difference_map(
                        region_polygon=ee_geometry,
                        date_range_1=date_range_1,
                        date_range_2=date_range_2,
                        collection_1=collection_1,
                        collection_2=collection_2,
                        month_int=month,
                        cloud_cover=cloud_cover,
                        clip_to_region=clip_to_region
                    )
                    
                    st.markdown('<div class="success-box"><strong>✅ Analysis Complete!</strong></div>', 
                               unsafe_allow_html=True)
                    
                    # Display the result
                    st.subheader("📊 Results")
                    
                    # Show analysis parameters
                    with st.expander("📋 Analysis Parameters Used", expanded=False):
                        st.write(f"**Region:** Custom polygon with {len(drawn_polygon.get('geometry', {}).get('coordinates', [[]])[0])} vertices")
                        st.write(f"**Period 1:** {start_date_1} to {end_date_1}")
                        st.write(f"**Period 2:** {start_date_2} to {end_date_2}")
                        st.write(f"**Month:** {get_month_name(month)}")
                        st.write(f"**Cloud Cover Threshold:** {cloud_cover}%")
                        st.write(f"**Collection 1:** {collection_1}")
                        st.write(f"**Collection 2:** {collection_2}")
                    
                    # Display the map
                    st.info("The map has been saved as 'snow_difference_analysis.html' in the current directory.")
                    
                    # Try to read and display the saved HTML
                    try:
                        with open('snow_difference_analysis.html', 'r') as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=600, scrolling=True)
                    except FileNotFoundError:
                        st.warning("Could not display the map. Please check the 'snow_difference_analysis.html' file.")
                    
                    # Interpretation guide
                    with st.expander("📖 How to Interpret the Results"):
                        st.markdown("""
                        **Map Layers:**
                        - **NDSI Early Period Average**: Snow conditions during the historical period
                        - **NDSI Recent Period Average**: Snow conditions during the recent period
                        - **NDSI Difference (Recent - Early)**: Change in snow cover
                        
                        **Color Interpretation:**
                        - **Blue/Purple**: Increase in snow cover (more snow in recent period)
                        - **White/Gray**: No significant change
                        - **Red/Yellow**: Decrease in snow cover (less snow in recent period)
                        
                        **NDSI Values:**
                        - Values > 0.4 typically indicate snow cover
                        - Values 0.0 to 0.4 indicate mixed pixels or thin snow
                        - Values < 0.0 indicate bare ground, vegetation, or water
                        """)
                    
                except Exception as e:
                    st.markdown(f'<div class="error-box"><strong>Error during analysis:</strong> {str(e)}</div>', 
                               unsafe_allow_html=True)
                    st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>Snow Difference Analyzer | Powered by Google Earth Engine & Landsat Data</p>
    <p>For more information, see the <a href="readme.md">README</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
