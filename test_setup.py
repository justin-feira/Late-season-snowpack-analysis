"""
Test script to check gee_setup import
"""
import sys
print("Python path before adding Setup:")
for path in sys.path:
    print(f"  {path}")

sys.path.append('./Setup')
print("\nPython path after adding Setup:")
for path in sys.path:
    print(f"  {path}")

try:
    print("\nTrying to import gee_setup...")
    from gee_setup import *
    print("✅ Import successful!")
    
    print("\nTesting if packages are available:")
    print(f"ee available: {'ee' in globals()}")
    print(f"pd available: {'pd' in globals()}")
    print(f"plt available: {'plt' in globals()}")
    
    print("\nTrying to run setup_gee()...")
    result = setup_gee()
    print(f"Setup result: {result}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")