"""
Shared Pytest Fixtures for the Spatial ETL Pipeline.

WHAT: Defines reusable spatial configurations and in-memory mock datasets.
WHY: Prevents code duplication across test files and ensures tests run 
     in milliseconds without requiring disk I/O or real data.
HOW: Uses geopandas to create synthetic 10x10 degree polygons over Ahmedabad.
"""
import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from src.core.config import SpatialConfig

@pytest.fixture
def spatial_config() -> SpatialConfig:
    """Provides a fresh, immutable instance of the spatial configuration."""
    return SpatialConfig()

@pytest.fixture
def mock_tp_wgs84() -> gpd.GeoDataFrame:
    """
    Creates a synthetic TP scheme GeoDataFrame in WGS84 (EPSG:4326).
    Represents a simple square bounding box over Gujarat, India.
    """
    poly = Polygon([(72.0, 23.0), (72.1, 23.0), (72.1, 23.1), (72.0, 23.1), (72.0, 23.0)])
    gdf = gpd.GeoDataFrame(
        {"plot_id": [1], "owner": ["Test Owner"]}, 
        geometry=[poly], 
        crs="EPSG:4326"
    )
    return gdf

@pytest.fixture
def mock_tp_utm(mock_tp_wgs84, spatial_config) -> gpd.GeoDataFrame:
    """
    Provides the mock TP scheme pre-projected to UTM 43N (EPSG:32643) 
    for accurate metric testing.
    """
    return mock_tp_wgs84.to_crs(spatial_config.UTM_43N)

@pytest.fixture
def empty_gdf_wgs84() -> gpd.GeoDataFrame:
    """Provides an empty GeoDataFrame to test edge cases and error handling."""
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")