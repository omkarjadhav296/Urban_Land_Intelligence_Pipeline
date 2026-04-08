"""
Geospatial Transformation Layer.

Handles loading, standardizing, area calculation, and automated
spatial alignment (auto-snapping) of Town Planning (TP) polygons.
"""
import logging
import numpy as np
import geopandas as gpd
from shapely.ops import nearest_points
from src.core.spatial_utils import SpatialUtils

logger = logging.getLogger(__name__)

class GeometryProcessor:
    """Enterprise processor for geometric and topological transformations."""
    
    def __init__(self, config):
        self.config = config

    def load_and_project(self, filepath: str) -> gpd.GeoDataFrame:
        """
        Loads a spatial file and standardizes it to the local UTM projection
        for accurate metric operations.
        """
        logger.info(f"Loading and projecting spatial data from: {filepath}")
        
        # Using pyogrio as the high-performance C-engine (bypassing Fiona errors)
        gdf = gpd.read_file(filepath, engine="pyogrio")
        
        if gdf.crs is None:
            logger.warning("No CRS found. Assuming WGS84 (EPSG:4326).")
            gdf.set_crs(self.config.WGS84, inplace=True)
            
        return gdf.to_crs(self.config.UTM_43N)

    def calculate_accurate_area(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculates precise physical area in square meters."""
        logger.info("Calculating precise geodesic areas...")
        gdf = gdf.copy()
        gdf['area_sqm'] = gdf.geometry.area
        return gdf

    def validate_and_align(self, tp_gdf: gpd.GeoDataFrame, reference_roads: gpd.GeoDataFrame, tolerance_m: float = 2.5) -> tuple[gpd.GeoDataFrame, dict]:
        """
        TASK 1: Automated Spatial Validation & Alignment.
        
        Computes the mathematical Positional Accuracy between TP boundaries and 
        real-world road networks. Applies dynamic geometric correction if misaligned.
        """
        logger.info("==================================================")
        logger.info("🛠️ TASK 1: SPATIAL VALIDATION & ALIGNMENT")
        
        if reference_roads.empty:
            logger.warning("No reference roads provided. Skipping alignment validation.")
            return tp_gdf, {"status": "skipped", "mean_error_m": None}

        # 1. Ensure projection parity (must be metric for distance math)
        if reference_roads.crs != tp_gdf.crs:
            reference_roads = reference_roads.to_crs(tp_gdf.crs)
            
        # 2. Extract linear boundaries from the TP polygons
        tp_boundaries = tp_gdf.copy()
        tp_boundaries.geometry = tp_boundaries.geometry.boundary
        
        # 3. Create a monolithic spatial union of roads for high-performance indexing
        road_union = reference_roads.geometry.unary_union
        
        distances = []
        dx_list = []
        dy_list = []
        
        # 4. Compute Positional Accuracy (Nearest Neighbor Projection)
        for geom in tp_boundaries.geometry:
            if geom is None or geom.is_empty:
                continue
            
            # Find the absolute closest coordinate pair between plot edge and road centerline
            p1, p2 = nearest_points(geom, road_union) # p1 is on TP, p2 is on Road
            dist = p1.distance(p2)
            
            # Filter: Only evaluate edges reasonably close to roads (< 30m) 
            # to avoid skewing data with deep internal plots
            if dist < 30.0:  
                distances.append(dist)
                dx_list.append(p2.x - p1.x)
                dy_list.append(p2.y - p1.y)

        # 5. Generate the Delivery Note (Positional Accuracy)
        if not distances:
            logger.warning("Could not calculate spatial alignment (no roads within range).")
            return tp_gdf, {"status": "failed", "mean_error_m": None}
            
        mean_error = np.mean(distances)
        median_dx = np.median(dx_list)
        median_dy = np.median(dy_list)
        
        report = {
            "status": "validated",
            "mean_positional_error_m": round(mean_error, 2),
            "max_error_m": round(np.max(distances), 2),
            "correction_applied": False,
            "shift_vector": {"dx": 0.0, "dy": 0.0}
        }
        
        # --- DELIVERABLE: SHORT NOTE ON POSITIONAL ACCURACY ---
        logger.info(f"📊 Delivery Note: Mean Positional Accuracy is {mean_error:.2f} meters.")
        logger.info(f"📊 Maximum observed deviation is {np.max(distances):.2f} meters.")
        
        # 6. Apply Dynamic Correction
        corrected_gdf = tp_gdf.copy()
        if mean_error > tolerance_m:
            logger.warning(f"⚠️ Misalignment exceeds {tolerance_m}m tolerance. Applying auto-correction...")
            
            # Snap the TP scheme to the road baseline using the computed median vector
            corrected_gdf = SpatialUtils.apply_affine_translation(
                corrected_gdf, 
                x_offset=median_dx, 
                y_offset=median_dy
            )
            
            report["correction_applied"] = True
            report["shift_vector"] = {"dx": round(median_dx, 2), "dy": round(median_dy, 2)}
            logger.info(f"✅ Auto-Correction Applied: Shifted X by {median_dx:.2f}m, Y by {median_dy:.2f}m")
        else:
            logger.info("✅ Spatial alignment is within acceptable tolerances. No correction applied.")
            
        logger.info("==================================================")
        return corrected_gdf, report