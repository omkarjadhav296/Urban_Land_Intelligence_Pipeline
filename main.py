"""
Urban Land Intelligence Orchestrator.

This is the main execution entry point. It wires together the Data Extraction,
Transformation, and Visualization layers using Dependency Injection.
"""
import os
import logging

from src.core.config import SpatialConfig
from src.core.spatial_utils import SpatialUtils
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
        
        # Optional Task 1: Affine Transformation for baseline correction
        # tp_utm = SpatialUtils.apply_affine_translation(tp_utm, x_offset=2.5, y_offset=1.2)
        
        # 2. Area Calculation (Task 6)
        tp_utm = self.geom_processor.calculate_accurate_area(tp_utm)
        tp_utm.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_area_corrected.geojson"), driver="GeoJSON")
        
        # 3. OSM Enrichment (Task 2)
        tp_enriched = self.enricher.enrich_with_osm(tp_utm)
        tp_enriched.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_enriched.geojson"), driver="GeoJSON")
        
        # 4. GEE Elevation Processing (Task 4)
        tp_elevation = self.elev_processor.process_elevation(tp_enriched)
        tp_elevation.to_crs(self.config.WGS84).to_file(os.path.join(self.output_dir, "tp_elevation.geojson"), driver="GeoJSON")
        
        # 5. 3D HTML Viewer (Task 5)
        self.viewer.generate_3d_viewer(tp_elevation, self.output_dir)
        
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    INPUT_TP = "data/input/tp_scheme.geojson"
    OUTPUT_DIR = "data/output/"
    
    if os.path.exists(INPUT_TP):
        pipeline = TPPipelineProcessor(INPUT_TP, OUTPUT_DIR)
        pipeline.run()
    else:
        logger.error(f"Input file not found at {INPUT_TP}. Please place your GeoJSON there.")