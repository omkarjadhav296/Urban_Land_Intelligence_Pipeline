"""
Urban Land Intelligence Orchestrator.

This is the main execution entry point. It wires together the Data Extraction,
Transformation, and Visualization layers using Dependency Injection.
"""
import os
import logging
import geopandas as gpd

from src.core.config import SpatialConfig
from src.transform.geometry import GeometryProcessor
from src.extract.osm_client import OSMClient
from src.extract.gee_client import GEEClient
from src.transform.enrichment import SpatialEnricher
from src.transform.elevation import ElevationProcessor
from src.visualize.deckgl_viewer import Viewer3D

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("TP_Orchestrator")

class TPPipelineProcessor:
    def __init__(self, input_geojson: str, output_dir: str):
        self.input_geojson = input_geojson
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Dependency Injection
        self.config = SpatialConfig()
        self.geom_processor = GeometryProcessor(self.config)
        self.osm_client = OSMClient(self.config)
        self.gee_client = GEEClient(project_id=self.config.GCP_PROJECT_ID) 
        self.enricher = SpatialEnricher(self.config, self.osm_client)
        self.elev_processor = ElevationProcessor(self.config, self.gee_client)
        self.viewer = Viewer3D(self.config)

    def run(self):
        logger.info("==================================================")
        logger.info("🚀 STARTING CLOUD-NATIVE TP LAND INTELLIGENCE PIPELINE")
        logger.info("==================================================")
        
        # 1. Ingestion & Projection (WGS84 -> UTM 43N)
        tp_utm = self.geom_processor.load_and_project(self.input_geojson)
        
        # --- TASK 1: Automated Validation & Alignment ---
        logger.info("Fetching real-world OSM context (Roads & Buildings)...")
        boundary_hull = tp_utm.to_crs(self.config.WGS84).unary_union.convex_hull
        raw_infra = self.osm_client.fetch_infrastructure(boundary_hull, infrastructure_type='all')
        
        reference_roads = gpd.GeoDataFrame()
        reference_buildings = gpd.GeoDataFrame()
        
        if not raw_infra.empty:
            if 'highway' in raw_infra.columns:
                reference_roads = raw_infra[raw_infra['highway'].notna()]
            if 'building' in raw_infra.columns:
                reference_buildings = raw_infra[raw_infra['building'].notna()]
                
            if not reference_roads.empty:
                tp_utm, alignment_report = self.geom_processor.validate_and_align(tp_utm, reference_roads, tolerance_m=2.5)
            else:
                logger.warning("OSM roads unavailable. Skipping auto-alignment.")
        
        # 2. Area Calculation (Task 6)
        tp_utm = self.geom_processor.calculate_accurate_area(tp_utm)
        tp_utm.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_area_corrected.geojson"), driver="GeoJSON")
        
        # 3. OSM Enrichment (Task 2 - Built vs Vacant)
        tp_enriched = self.enricher.enrich_with_osm(tp_utm)
        tp_enriched.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_enriched.geojson"), driver="GeoJSON")
        
        # 4. GEE Elevation Processing (Task 4)
        tp_elevation = self.elev_processor.process_elevation(tp_enriched)
        tp_elevation.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_elevation.geojson"), driver="GeoJSON")
        
        # 5. Advanced WebGIS Dashboard (Task 5)
        project_root = "."
        
        # Pass TP Plots, Roads, AND Buildings to the 3D Engine
        self.viewer.generate_3d_viewer(tp_elevation, reference_roads, reference_buildings, project_root)
        
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    INPUT_TP = "data/input/tp_scheme.geojson"
    OUTPUT_DIR = "data/output/"
    
    if os.path.exists(INPUT_TP):
        pipeline = TPPipelineProcessor(INPUT_TP, OUTPUT_DIR)
        pipeline.run()
    else:
        logger.error(f"Input file not found at {INPUT_TP}. Please place your GeoJSON there.")