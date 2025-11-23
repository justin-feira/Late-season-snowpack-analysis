"""
Generate a simple architecture diagram for the app
"""

print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                  Snow Difference Analyzer - App Architecture                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE (app.py)                         │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Interactive  │  │ Date Picker  │  │  Parameter   │  │ Run Analysis │   │
│  │     Map      │  │   Widgets    │  │   Controls   │  │    Button    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                  │                  │            │
└─────────┼─────────────────┼──────────────────┼──────────────────┼────────────┘
          │                 │                  │                  │
          └─────────────────┴──────────────────┴──────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │   VALIDATION & CONVERSION       │
                    │      (app_utils.py)             │
                    │                                 │
                    │  • GeoJSON → EE Geometry       │
                    │  • Date validation             │
                    │  • Parameter validation        │
                    │  • Landsat collection suggest  │
                    └────────────┬────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────────┐
                    │   CORE ANALYSIS ENGINE          │
                    │  (execution/grand_file.py)      │
                    │                                 │
                    │  snow_difference_map()          │
                    │  • Load Landsat collections    │
                    │  • Apply cloud masking         │
                    │  • Calculate NDSI              │
                    │  • Create difference maps      │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌───────────────────┐   ┌───────────────────────┐
        │  GOOGLE EARTH     │   │   HELPER FUNCTIONS    │
        │    ENGINE API     │   │  (functions/geolib.py) │
        │                   │   │                        │
        │  • Image fetch    │   │  • NDSI calculation    │
        │  • Processing     │   │  • Cloud masking       │
        │  • Rendering      │   │  • Compositing         │
        └───────────────────┘   └────────────────────────┘
                    │
                    ▼
        ┌────────────────────────────┐
        │   OUTPUT VISUALIZATION     │
        │    (Folium Map HTML)       │
        │                            │
        │  • Historical NDSI layer   │
        │  • Recent NDSI layer       │
        │  • Difference layer        │
        │  • Interactive toggles     │
        └────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUPPORTING FILES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  requirements.txt       → Dependencies list                                 │
│  test_app_utils.py      → Unit tests (19 tests)                            │
│  verify_setup.py        → Setup verification script                         │
│  .gitignore             → Git exclusions                                    │
│  IMPLEMENTATION_SUMMARY.md → Complete documentation                         │
│  readme.md              → User guide and installation instructions          │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                                DATA FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. User draws polygon on map                                               │
│         ↓                                                                    │
│  2. User selects dates and parameters                                       │
│         ↓                                                                    │
│  3. User clicks "Run Analysis"                                              │
│         ↓                                                                    │
│  4. App validates all inputs (app_utils)                                    │
│         ↓                                                                    │
│  5. GeoJSON polygon → EE Geometry conversion                                │
│         ↓                                                                    │
│  6. Call snow_difference_map() with parameters                              │
│         ↓                                                                    │
│  7. Fetch & process Landsat imagery from GEE                                │
│         ↓                                                                    │
│  8. Generate Folium map with 3 layers                                       │
│         ↓                                                                    │
│  9. Save as HTML file                                                       │
│         ↓                                                                    │
│  10. Display in Streamlit app                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
""")
