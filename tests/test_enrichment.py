"""
Unit tests for SpatialEnricher module.

WHAT: Tests R-Tree Spatial Indexing and Topological Overlays.
WHY: Ensures 'is_built' boolean flags and 'road_anomaly' heuristics behave 
     correctly when external features topologically intersect the TP plots.
"""
from src.transform.enrichment import SpatialEnricher
import geopandas as gpd

def test_enrich_with_osm_matches(mocker, spatial_config, mock_tp_utm, mock_tp_wgs84):
    """Tests the scenario where a building and road intersect the plot."""
    # Arrange
    mock_osm_client = mocker.MagicMock()
    
    # Inject requisite OSM tag columns into our mock infrastructure
    fake_infra_wgs84 = mock_tp_wgs84.copy()
    fake_infra_wgs84['building'] = 'yes'
    fake_infra_wgs84['highway'] = 'residential'
    
    # Instruct the mock client to return this synthetic dataset
    mock_osm_client.fetch_infrastructure.return_value = fake_infra_wgs84
    
    enricher = SpatialEnricher(spatial_config, mock_osm_client)
    
    # Act
    enriched_gdf = enricher.enrich_with_osm(mock_tp_utm)
    
    # Assert new schema attributes from Task 2 exist
    assert "is_built" in enriched_gdf.columns
    assert "plot_status" in enriched_gdf.columns
    assert "road_anomaly" in enriched_gdf.columns
    assert "road_length_m" in enriched_gdf.columns
    
    # Since the mock infrastructure overlaps the mock plot perfectly, it should be tagged as Built
    assert enriched_gdf.iloc[0]["is_built"] == True
    assert enriched_gdf.iloc[0]["plot_status"] == "Built"

def test_enrich_with_osm_empty_infrastructure(mocker, spatial_config, mock_tp_utm, empty_gdf_wgs84):
    """Tests the edge case where no OSM data exists in the area."""
    mock_osm_client = mocker.MagicMock()
    mock_osm_client.fetch_infrastructure.return_value = empty_gdf_wgs84
    
    enricher = SpatialEnricher(spatial_config, mock_osm_client)
    enriched_gdf = enricher.enrich_with_osm(mock_tp_utm)
    
    # Assert fallbacks are applied gracefully without crashing the pipeline
    assert enriched_gdf.iloc[0]["plot_status"] == "Unknown"
    assert enriched_gdf.iloc[0]["road_anomaly"] == "Unknown"
    assert "is_built" not in enriched_gdf.columns