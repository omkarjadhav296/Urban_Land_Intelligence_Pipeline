"""
Spatial Enrichment Transformation.

Applies high-performance R-Tree spatial joins (Point-in-Polygon, Intersects) 
to attribute open-source intelligence to the core TP scheme data.
"""
import logging
import geopandas as gpd
from src.core.config import SpatialConfig
from src.extract.osm_client import OSMClient

logger = logging.getLogger(__name__)

class SpatialEnricher:
    def __init__(self, config: SpatialConfig, osm_client: OSMClient):
        self.config = config
        self.osm_client = osm_client

    def enrich_with_osm(self, tp_utm: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Executes Task 2: Enriches TP plots with `is_built` and `road_access` attributes."""
        logger.info("Starting OSM Spatial Enrichment (R-Tree Intersects)...")
        
        tp_wgs84 = tp_utm.to_crs(self.config.WGS84)
        boundary_hull = tp_wgs84.unary_union.convex_hull

        buildings_wgs = self.osm_client.fetch_infrastructure(boundary_hull, 'buildings')
        roads_wgs = self.osm_client.fetch_infrastructure(boundary_hull, 'roads')

        result_gdf = tp_utm.copy()
        
        # Process 'is_built' status
        if not buildings_wgs.empty:
            buildings_utm = buildings_wgs.to_crs(self.config.UTM_43N)
            built_plots = gpd.sjoin(result_gdf, buildings_utm, how="inner", predicate="intersects")
            built_indices = built_plots.index.unique()
            result_gdf['is_built'] = result_gdf.index.isin(built_indices)
        else:
            result_gdf['is_built'] = False
            
        # Process 'road_access' status (10m Buffer)
        if not roads_wgs.empty:
            roads_utm = roads_wgs.to_crs(self.config.UTM_43N)
            roads_buffered = roads_utm.copy()
            roads_buffered.geometry = roads_buffered.geometry.buffer(self.config.ROAD_BUFFER_METERS)
            
            access_plots = gpd.sjoin(result_gdf, roads_buffered, how="inner", predicate="intersects")
            access_indices = access_plots.index.unique()
            result_gdf['road_access'] = result_gdf.index.isin(access_indices)
        else:
            result_gdf['road_access'] = False

        logger.info("OSM Enrichment complete.")
        return result_gdf