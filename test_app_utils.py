"""
Unit tests for app_utils module
"""
import unittest
from datetime import date
import sys
import os

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ee module for testing without GEE initialization
class MockEEGeometry:
    """Mock Earth Engine Geometry for testing."""
    def __init__(self, coords):
        self.coords = coords
    
    @staticmethod
    def Polygon(coords):
        return MockEEGeometry(coords)

sys.modules['ee'] = type('ee', (), {
    'Geometry': MockEEGeometry,
    'DateRange': lambda start, end: (start, end)
})()

from app_utils import (
    validate_date_range,
    validate_parameters,
    format_date_for_ee,
    suggest_landsat_collection,
    get_month_name,
    convert_geojson_to_ee_geometry
)


class TestDateValidation(unittest.TestCase):
    """Test date validation functions."""
    
    def test_valid_date_range(self):
        """Test valid date range."""
        start = date(2000, 1, 1)
        end = date(2010, 1, 1)
        is_valid, msg = validate_date_range(start, end)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")
    
    def test_end_before_start(self):
        """Test that end date before start date is invalid."""
        start = date(2010, 1, 1)
        end = date(2000, 1, 1)
        is_valid, msg = validate_date_range(start, end)
        self.assertFalse(is_valid)
        self.assertIn("after", msg.lower())
    
    def test_same_dates(self):
        """Test that same start and end date is invalid."""
        d = date(2000, 1, 1)
        is_valid, msg = validate_date_range(d, d)
        self.assertFalse(is_valid)
    
    def test_future_date(self):
        """Test that future dates are rejected."""
        from datetime import timedelta
        start = date.today()
        end = date.today() + timedelta(days=365)
        is_valid, msg = validate_date_range(start, end)
        self.assertFalse(is_valid)
        self.assertIn("future", msg.lower())
    
    def test_date_before_landsat(self):
        """Test that dates before Landsat 5 are rejected."""
        start = date(1980, 1, 1)
        end = date(1990, 1, 1)
        is_valid, msg = validate_date_range(start, end)
        self.assertFalse(is_valid)
        self.assertIn("1984", msg)


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation functions."""
    
    def test_valid_parameters(self):
        """Test valid parameter set."""
        mock_geometry = MockEEGeometry.Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]])
        is_valid, msg = validate_parameters(
            mock_geometry,
            date(1990, 1, 1),
            date(2000, 1, 1),
            date(2010, 1, 1),
            date(2020, 1, 1),
            6,  # June
            10  # 10% cloud cover
        )
        self.assertTrue(is_valid)
    
    def test_missing_polygon(self):
        """Test that missing polygon is caught."""
        is_valid, msg = validate_parameters(
            None,
            date(1990, 1, 1),
            date(2000, 1, 1),
            date(2010, 1, 1),
            date(2020, 1, 1),
            6,
            10
        )
        self.assertFalse(is_valid)
        self.assertIn("polygon", msg.lower())
    
    def test_invalid_month(self):
        """Test that invalid month is caught."""
        mock_geometry = MockEEGeometry.Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]])
        is_valid, msg = validate_parameters(
            mock_geometry,
            date(1990, 1, 1),
            date(2000, 1, 1),
            date(2010, 1, 1),
            date(2020, 1, 1),
            13,  # Invalid month
            10
        )
        self.assertFalse(is_valid)
        self.assertIn("month", msg.lower())
    
    def test_invalid_cloud_cover(self):
        """Test that invalid cloud cover is caught."""
        mock_geometry = MockEEGeometry.Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]])
        is_valid, msg = validate_parameters(
            mock_geometry,
            date(1990, 1, 1),
            date(2000, 1, 1),
            date(2010, 1, 1),
            date(2020, 1, 1),
            6,
            150  # Invalid cloud cover > 100
        )
        self.assertFalse(is_valid)
        self.assertIn("cloud", msg.lower())


class TestFormatting(unittest.TestCase):
    """Test formatting functions."""
    
    def test_format_date_for_ee(self):
        """Test date formatting for Earth Engine."""
        d = date(2020, 5, 15)
        formatted = format_date_for_ee(d)
        self.assertEqual(formatted, '2020-05-15')
    
    def test_get_month_name(self):
        """Test month name retrieval."""
        self.assertEqual(get_month_name(1), 'January')
        self.assertEqual(get_month_name(6), 'June')
        self.assertEqual(get_month_name(12), 'December')
        self.assertIn("Month", get_month_name(13))  # Invalid month


class TestLandsatSuggestion(unittest.TestCase):
    """Test Landsat collection suggestion."""
    
    def test_suggest_landsat_5(self):
        """Test that Landsat 5 is suggested for 1990s."""
        collection = suggest_landsat_collection(1990, 1995)
        self.assertIn('LT05', collection)
    
    def test_suggest_landsat_7(self):
        """Test that Landsat 7 is suggested for early 2000s."""
        collection = suggest_landsat_collection(2000, 2010)
        self.assertIn('LE07', collection)
    
    def test_suggest_landsat_8(self):
        """Test that Landsat 8 is suggested for 2015."""
        collection = suggest_landsat_collection(2013, 2020)
        self.assertIn('LC08', collection)
    
    def test_suggest_landsat_9(self):
        """Test that Landsat 9 is suggested for recent years."""
        collection = suggest_landsat_collection(2021, 2024)
        self.assertIn('LC09', collection)


class TestGeoJSONConversion(unittest.TestCase):
    """Test GeoJSON to EE Geometry conversion."""
    
    def test_polygon_conversion(self):
        """Test basic polygon conversion."""
        geojson = {
            "type": "Polygon",
            "coordinates": [[[-106.99, 39.08], [-106.71, 38.65], [-106.14, 38.59], [-106.99, 39.08]]]
        }
        result = convert_geojson_to_ee_geometry(geojson)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, MockEEGeometry)
    
    def test_feature_geometry(self):
        """Test conversion with Feature wrapper."""
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-106.99, 39.08], [-106.71, 38.65], [-106.14, 38.59], [-106.99, 39.08]]]
            }
        }
        result = convert_geojson_to_ee_geometry(geojson)
        self.assertIsNotNone(result)
    
    def test_none_input(self):
        """Test that None input returns None."""
        result = convert_geojson_to_ee_geometry(None)
        self.assertIsNone(result)
    
    def test_multipolygon_conversion(self):
        """Test MultiPolygon conversion (should take first polygon)."""
        geojson = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[-106.99, 39.08], [-106.71, 38.65], [-106.14, 38.59], [-106.99, 39.08]]],
                [[[-105.99, 38.08], [-105.71, 37.65], [-105.14, 37.59], [-105.99, 38.08]]]
            ]
        }
        result = convert_geojson_to_ee_geometry(geojson)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
