"""
Quick verification script to check that the app and all dependencies are properly set up.

Run this before starting the Streamlit app to ensure everything is configured correctly.
"""

import sys
import os

def check_imports():
    """Check that all required packages are installed."""
    print("="*60)
    print("Checking Required Packages")
    print("="*60)
    
    required_packages = [
        ('streamlit', 'Streamlit framework'),
        ('leafmap.foliumap', 'Leafmap for interactive maps'),
        ('streamlit_folium', 'Streamlit-Folium integration'),
        ('ee', 'Google Earth Engine API'),
        ('folium', 'Folium mapping library'),
        ('pandas', 'Pandas data analysis'),
        ('numpy', 'NumPy numerical computing'),
        ('shapely', 'Shapely geometry library'),
        ('geojson', 'GeoJSON utilities'),
    ]
    
    all_ok = True
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {description:40s} - OK")
        except ImportError as e:
            print(f"❌ {description:40s} - MISSING")
            all_ok = False
    
    print()
    return all_ok

def check_files():
    """Check that required files exist."""
    print("="*60)
    print("Checking Required Files")
    print("="*60)
    
    required_files = [
        ('app.py', 'Main Streamlit application'),
        ('app_utils.py', 'Utility functions'),
        ('requirements.txt', 'Dependency list'),
        ('execution/grand_file.py', 'Core snow difference function'),
        ('Setup/gee_setup.py', 'Google Earth Engine setup'),
        ('functions/geolib.py', 'Geographic functions library'),
    ]
    
    all_ok = True
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"✅ {description:40s} - Found")
        else:
            print(f"❌ {description:40s} - NOT FOUND")
            all_ok = False
    
    print()
    return all_ok

def check_gee_auth():
    """Check Google Earth Engine authentication."""
    print("="*60)
    print("Checking Google Earth Engine")
    print("="*60)
    
    try:
        import ee
        try:
            # Try with a timeout to avoid hanging (cross-platform approach)
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
            
            def try_initialize():
                ee.Initialize()
                return True
            
            # Try to initialize with a 5-second timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(try_initialize)
                try:
                    future.result(timeout=5)
                    print("✅ Google Earth Engine - Authenticated and ready")
                    return True
                except FutureTimeoutError:
                    print("⚠️  Google Earth Engine - Authentication check timed out")
                    print("\nThe app will handle authentication when started.")
                    return False
                except Exception as e:
                    print("⚠️  Google Earth Engine - Not authenticated")
                    print("\nTo authenticate, run:")
                    print("    earthengine authenticate")
                    print("\nOr in Python:")
                    print("    python -c 'import ee; ee.Authenticate()'")
                    print("\nThe app will prompt for authentication when started.")
                    return False
        except Exception as e:
            print(f"⚠️  Google Earth Engine - {str(e)}")
            return False
    except ImportError:
        print("❌ Google Earth Engine API not installed")
        return False

def main():
    """Run all checks."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Snow Difference App - Setup Verification" + " "*8 + "║")
    print("╚" + "="*58 + "╝")
    print()
    
    imports_ok = check_imports()
    files_ok = check_files()
    gee_ok = check_gee_auth()
    
    print("="*60)
    print("Summary")
    print("="*60)
    
    if imports_ok and files_ok:
        print("✅ All required packages and files are present")
    else:
        print("❌ Some required components are missing")
        if not imports_ok:
            print("\n   Install missing packages with:")
            print("   pip install -r requirements.txt")
        return 1
    
    if gee_ok:
        print("✅ Google Earth Engine is ready")
    else:
        print("⚠️  Google Earth Engine needs authentication")
        print("   The app will guide you through authentication")
    
    print("\n" + "="*60)
    print("Ready to Start!")
    print("="*60)
    print("\nTo launch the app, run:")
    print("    streamlit run app.py")
    print("\nThe app will open in your browser at http://localhost:8501")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
