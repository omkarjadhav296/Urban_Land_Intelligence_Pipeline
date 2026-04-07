"""
Unit tests for SpatialEnricher module.

WHAT: Tests R-Tree Spatial Indexing and Topological Joins.
WHY: Ensures 'is_built' and 'road_access' boolean logic behaves correctly when
     features intersect or miss.
"""
from src.transform.enrichment import SpatialEnricher
from shapely.geometry import Polygon
import geopandas as gpd

def test_enrich_with_osm_matches(mocker, spatial_config, mock_tp_utm, mock_tp_wgs84):
    """Tests the scenario where a building and road intersect the plot."""
    # Arrange
    mock_osm_client = mocker.MagicMock()
    
    # Create fake building/road directly on top of our mock TP plot
    fake_infra_wgs84 = mock_tp_wgs84.copy()
    
    # Instruct the mock client to return this fake infrastructure
    mock_osm_client.fetch_infrastructure.return_value = fake_infra_wgs84
    
    enricher = SpatialEnricher(spatial_config, mock_osm_client)
    
    # Act
    enriched_gdf = enricher.enrich_with_osm(mock_tp_utm)
    
    # Assert
    assert "is_built" in enriched_gdf.columns
    assert "road_access" in enriched_gdf.columns
    # Because the mock infrastructure overlaps the mock plot perfectly, these should be True
    assert enriched_gdf.iloc[0]["is_built"] == True
    assert enriched_gdf.iloc[0]["road_access"] == True

def test_enrich_with_osm_empty_infrastructure(mocker, spatial_config, mock_tp_utm, empty_gdf_wgs84):
    """Tests the edge case where no OSM data exists in the area."""
    mock_osm_client = mocker.MagicMock()
    mock_osm_client.fetch_infrastructure.return_value = empty_gdf_wgs84
    
    enricher = SpatialEnricher(spatial_config, mock_osm_client)
    enriched_gdf = enricher.enrich_with_osm(mock_tp_utm)
    
    # Assert fallbacks are applied correctly
    assert enriched_gdf.iloc[0]["is_built"] == False
    assert enriched_gdf.iloc[0]["road_access"] == False