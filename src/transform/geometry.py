"""
Geometry Transformation Module.

Manages coordinate reference system (CRS) projections and executes mathematical 
area calculations to ensure strict metric accuracy.
"""
import logging
import geopandas as gpd

logger = logging.getLogger(__name__)

class GeometryProcessor:
    def __init__(self, config):
        self.config = config

    def load_and_project(self, filepath: str) -> gpd.GeoDataFrame:
        """Loads spatial data and strictly projects it to the local UTM zone."""
        logger.info(f"Loading data from {filepath}")
        gdf = gpd.read_file(filepath, engine="pyogrio")
        
        if gdf.crs != self.config.UTM_43N:
            logger.info(f"Projecting data from {gdf.crs} to {self.config.UTM_43N}")
            gdf = gdf.to_crs(self.config.UTM_43N)
            
        return gdf

    def calculate_accurate_area(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculates accurate plot area in square meters (Task 6)."""
        logger.info("Calculating metric plot area...")
        
        if gdf.crs.is_geographic:
            raise ValueError("Cannot calculate area on Geographic CRS. Project to UTM first.")
            
        result_gdf = gdf.copy()
        result_gdf['area_sqm'] = result_gdf.geometry.area.round(2)
        return result_gdf