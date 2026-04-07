"""
Elevation Module (Cloud-Native Edition).

Transforms local GeoDataFrames into Earth Engine objects, requests cloud computation
via the GEE Client, and parses the results back into local DataFrames.
"""
import json
import logging
import geopandas as gpd
import ee
from src.core.config import SpatialConfig
from src.extract.gee_client import GEEClient

logger = logging.getLogger(__name__)

class ElevationProcessor:
    def __init__(self, config: SpatialConfig, gee_client: GEEClient):
        self.config = config
        self.gee_client = gee_client

    def _gdf_to_ee_feature_collection(self, gdf: gpd.GeoDataFrame) -> ee.FeatureCollection:
        """Converts a local GeoDataFrame into a GEE Feature Collection."""
        gdf_wgs84 = gdf.to_crs(self.config.WGS84)
        geojson_dict = json.loads(gdf_wgs84.to_json())
        
        features = []
        for feature in geojson_dict['features']:
            geom = ee.Geometry(feature['geometry'])
            properties = feature['properties']
            features.append(ee.Feature(geom, properties))
            
        return ee.FeatureCollection(features)

    def process_elevation(self, tp_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Extracts Mean and Range elevation using Google Earth Engine (Task 4)."""
        logger.info("Orchestrating Cloud Elevation processing...")
        
        try:
            ee_fc = self._gdf_to_ee_feature_collection(tp_gdf)
            dem_image = self.gee_client.get_copernicus_dem()
            reduced_fc = self.gee_client.compute_zonal_stats(ee_fc, dem_image, scale=30)
            
            logger.info("Downloading computed statistical metadata from GEE...")
            result_dict = reduced_fc.getInfo()
            
            mean_vals = []
            range_vals = []
            
            for feature in result_dict['features']:
                props = feature['properties']
                mean_elev = round(props.get('mean', 0.0), 2)
                min_elev = props.get('min', 0.0)
                max_elev = props.get('max', 0.0)
                
                mean_vals.append(mean_elev)
                range_vals.append(round(max_elev - min_elev, 2))
                
            tp_gdf['elev_mean'] = mean_vals
            tp_gdf['elev_range'] = range_vals
            
        except Exception as e:
            logger.error(f"GEE Elevation enrichment failed: {e}")
            logger.warning("Falling back to 0.0 for elevation metrics.")
            tp_gdf['elev_mean'] = 0.0
            tp_gdf['elev_range'] = 0.0
            
        return tp_gdf