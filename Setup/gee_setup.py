"""
Google Earth Engine utilities and setup functions
"""
# Try importing packages with error handling
try:
    import ee
    print("✅ earthengine-api imported successfully")
except ImportError:
    print("❌ earthengine-api not found. Install with: conda install -c conda-forge earthengine-api")
    ee = None

try:
    import folium
    print("✅ folium imported successfully")
except ImportError:
    print("❌ folium not found. Install with: conda install -c conda-forge folium")
    folium = None

try:
    import pandas as pd
    print("✅ pandas imported successfully")
except ImportError:
    print("❌ pandas not found. Install with: conda install -c conda-forge pandas")
    pd = None

try:
    import numpy as np
    print("✅ numpy imported successfully")
except ImportError:
    print("❌ numpy not found. Install with: conda install -c conda-forge numpy")
    np = None

try:
    import matplotlib.pyplot as plt
    print("✅ matplotlib imported successfully")
except ImportError:
    print("❌ matplotlib not found. Install with: conda install -c conda-forge matplotlib")
    plt = None

try:
    import seaborn as sns
    print("✅ seaborn imported successfully")
except ImportError:
    print("❌ seaborn not found. Install with: conda install -c conda-forge seaborn")
    sns = None

try:
    from IPython.display import Image, display
    print("✅ IPython display imported successfully")
except ImportError:
    print("❌ IPython not found. Install with: conda install -c conda-forge ipython")
    Image = None
    display = None

import json
print("✅ json imported successfully (built-in)")

def initialize_gee():
    """Initialize Google Earth Engine"""
    if ee is None:
        print("❌ Cannot initialize GEE - earthengine-api not installed")
        print("Make sure you're in the gee-env conda environment:")
        print("  conda activate gee-env")
        return False
        
    try:
        ee.Initialize()
        print("Google Earth Engine initialized successfully!")
        print(f"EE version: {ee.__version__}")
        return True
    except Exception as e:
        print(f"Initialization failed: {e}")
        print("Run authentication first: ee.Authenticate()")
        return False

def setup_gee():
    """Setup matplotlib and initialize GEE"""
    # Set up matplotlib if available
    if plt is not None and sns is not None:
        plt.rcParams['figure.figsize'] = (12, 8)
        sns.set_style("whitegrid")
        print("✅ Matplotlib configured")
    else:
        print("❌ Matplotlib/Seaborn not available - skipping setup")
    
    # Initialize GEE
    return initialize_gee()

# Define what gets imported with "from gee_setup import *"
__all__ = [
    'ee', 'folium', 'pd', 'np', 'plt', 'sns', 'Image', 'display', 'json',
    'initialize_gee', 'setup_gee', 'check_environment', 'quick_setup'
]

def check_environment():
    """Check if we're in the right conda environment"""
    import os
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'No conda environment active')
    print(f"Current environment: {conda_env}")
    
    if conda_env != 'gee-env':
        print("⚠️  WARNING: You're not in the 'gee-env' environment!")
        print("   Activate it with: conda activate gee-env")
        return False
    return True

def quick_setup():
    """One-line setup function"""
    print("=== GEE Quick Setup ===")
    env_ok = check_environment()
    if env_ok:
        return setup_gee()
    return False

print("GEE utilities loaded successfully!")
print("Use quick_setup() for one-line initialization")