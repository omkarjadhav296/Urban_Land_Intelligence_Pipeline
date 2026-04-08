"""
Geospatial Enrichment Layer.

Integrates open datasets (OpenStreetMap) with Town Planning (TP) schemes.
Performs topological overlay to classify Built vs. Vacant plots and 
detects infrastructural anomalies like Missing or Extra Roads.
"""
import logging
import geopandas as gpd
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SpatialEnricher:
    """Handles the integration of external vector datasets using spatial joins."""
    
    def __init__(self, config, osm_client):
        self.config = config
        self.osm_client = osm_client

    def enrich_with_osm(self, tp_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        TASK 2: Open Dataset Integration.
        Extracts roads and buildings, identifies built vs vacant plots, 
        and detects missing/extra roads using spatial heuristics.
        """
        logger.info("==================================================")
        logger.info("🏙️ TASK 2: OPEN DATASET INTEGRATION & ENRICHMENT")
        
        # 1. Fetch Contextual OSM Infrastructure using the WGS84 bounding box
        boundary_hull = tp_gdf.to_crs(self.config.WGS84).unary_union.convex_hull
        
        # We fetch 'all' to get both buildings and roads in one API call
        infra_gdf = self.osm_client.fetch_infrastructure(boundary_hull, infrastructure_type='all')
        
        if infra_gdf.empty:
            logger.warning("No OSM infrastructure found. Skipping enrichment.")
            tp_gdf['plot_status'] = 'Unknown'
            tp_gdf['road_anomaly'] = 'Unknown'
            return tp_gdf
            
        # Reproject OSM data to UTM for accurate metric spatial operations
        infra_gdf = infra_gdf.to_crs(self.config.UTM_43N)
        
        # 2. Extract Buildings and Roads into separate DataFrames
        buildings = infra_gdf[infra_gdf['building'].notna()]
        roads = infra_gdf[infra_gdf['highway'].notna()]
        
        logger.info(f"Extracted {len(buildings)} buildings and {len(roads)} road segments from OSM.")
        
        # 3. Building Integration (Identify Built vs Vacant)
        if not buildings.empty:
            # Spatial join: Which buildings intersect which TP plots?
            joined_bldgs = gpd.sjoin(buildings, tp_gdf[['geometry']], how='inner', predicate='intersects')
            bldg_counts = joined_bldgs.index_right.value_counts().rename('building_count')
            tp_gdf = tp_gdf.join(bldg_counts, how='left')
            tp_gdf['building_count'] = tp_gdf['building_count'].fillna(0).astype(int)
        else:
            tp_gdf['building_count'] = 0

        # Explicit Classification
        tp_gdf['is_built'] = tp_gdf['building_count'] > 0
        tp_gdf['plot_status'] = np.where(tp_gdf['is_built'], 'Built', 'Vacant')
        
        # 4. Road Integration (Calculate exact metric length of roads per plot)
        tp_gdf['road_length_m'] = 0.0
        
        if not roads.empty:
            try:
                # Topologically clip roads strictly to TP boundaries
                intersecting_roads = gpd.overlay(roads, tp_gdf[['geometry']].reset_index(), how='intersection')
                
                # Calculate exact metric length of the clipped road segments
                intersecting_roads['seg_length'] = intersecting_roads.geometry.length
                
                # Sum the road lengths grouped by the plot they fall into
                road_lengths = intersecting_roads.groupby('index')['seg_length'].sum()
                tp_gdf['road_length_m'] = tp_gdf.index.map(road_lengths).fillna(0.0)
            except Exception as e:
                logger.error(f"Failed to calculate precise road lengths: {e}")
        
        # 5. Detect Missing/Extra Roads (Anomaly Detection Heuristics)
        def detect_anomaly(row):
            # Built plot but basically zero road access (< 5 meters)
            if row['is_built'] and row['road_length_m'] < 5.0:
                return "Missing Road Access"
            # Vacant plot but has extensive road infrastructure running through it (> 50 meters)
            elif not row['is_built'] and row['road_length_m'] > 50.0:
                return "Extra/Unplanned Road"
            else:
                return "Adequate"

        tp_gdf['road_anomaly'] = tp_gdf.apply(detect_anomaly, axis=1)
        
        # --- DELIVERABLE: REPORTING ---
        built_count = tp_gdf['is_built'].sum()
        vacant_count = len(tp_gdf) - built_count
        missing_roads = (tp_gdf['road_anomaly'] == "Missing Road Access").sum()
        extra_roads = (tp_gdf['road_anomaly'] == "Extra/Unplanned Road").sum()
        
        logger.info(f"📊 Delivery Note: Identified {built_count} Built plots and {vacant_count} Vacant plots.")
        logger.info(f"⚠️ Anomalies Detected: {missing_roads} plots missing road access, {extra_roads} with extra/unplanned roads.")
        logger.info("==================================================")
        
        return tp_gdf