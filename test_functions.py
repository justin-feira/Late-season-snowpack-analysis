"""
Example of how to use the functions package
"""

# Step 1: Set up GEE environment first
import sys
sys.path.append('./Setup')
from gee_setup import *

# Initialize GEE
setup_gee()

# Step 2: Import functions from the functions package
from functions import add_ee_layer, create_map, get_image_collection_info

# Or import everything:
# from functions import *

# Step 3: Use the functions
print("Testing function imports...")

# Test create_map function
try:
    # Add the ee layer method to folium maps
    folium.Map.add_ee_layer = add_ee_layer
    
    # Create a test map
    test_map = create_map(center=[37.7749, -122.4194], zoom=10)
    print("✅ create_map function works!")
    
    # Test collection info function
    if ee is not None:
        collection = get_image_collection_info('LANDSAT/LC08/C02/T1_L2', '2023-01-01', '2023-12-31')
        print("✅ get_image_collection_info function works!")
    
except Exception as e:
    print(f"❌ Error testing functions: {e}")

print("\n=== Usage Instructions ===")
print("1. First run GEE setup:")
print("   from gee_setup import *")
print("   setup_gee()")
print("2. Then import functions:")
print("   from functions import *")
print("3. Add EE layer method to folium:")
print("   folium.Map.add_ee_layer = add_ee_layer")
print("4. Use the functions normally!")