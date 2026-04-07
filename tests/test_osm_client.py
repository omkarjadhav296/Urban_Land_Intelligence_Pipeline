"""
Unit tests for the OSMClient Extraction module.

WHAT: Tests the Overpass API wrapper using Mocking.
WHY: Prevents tests from failing if the OpenStreetMap servers are temporarily down.
HOW: Intercepts the `osmnx.features_from_polygon` call using `pytest-mock`.
"""
from src.extract.osm_client import OSMClient
from shapely.geometry import Polygon

def test_fetch_infrastructure_success(mocker, spatial_config, mock_tp_wgs84):
    """Tests successful extraction and geometry filtering."""
    # Arrange
    client = OSMClient(spatial_config)
    boundary = mock_tp_wgs84.unary_union.convex_hull
    
    # Mock the OSMnx response to return a fake dataframe
    mock_ox = mocker.patch("src.extract.osm_client.ox.features_from_polygon")
    mock_ox.return_value = mock_tp_wgs84.copy() # Pretend our TP square is a building
    
    # Act
    result_gdf = client.fetch_infrastructure(boundary, "buildings")
    
    # Assert
    mock_ox.assert_called_once()
    assert not result_gdf.empty
    assert result_gdf.geometry.type.iloc[0] == "Polygon"

def test_fetch_infrastructure_failure_fallback(mocker, spatial_config, mock_tp_wgs84):
    """Ensures pipeline survives an OSM API outage by returning an empty GDF."""
    client = OSMClient(spatial_config)
    boundary = mock_tp_wgs84.unary_union.convex_hull
    
    # Force OSMnx to raise an exception
    mocker.patch("src.extract.osm_client.ox.features_from_polygon", side_effect=Exception("API Down"))
    
    # Act
    result_gdf = client.fetch_infrastructure(boundary, "roads")
    
    # Assert
    assert result_gdf.empty
    assert result_gdf.crs == spatial_config.WGS84