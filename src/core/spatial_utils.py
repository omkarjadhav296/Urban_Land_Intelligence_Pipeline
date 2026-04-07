"""
Spatial Utilities Module.

Provides decoupled, low-level geometric operations such as affine transformations
to correct datum shifts and positional alignment errors (Task 1).
"""
import logging
import geopandas as gpd
from shapely import affinity

logger = logging.getLogger(__name__)

class SpatialUtils:
    @staticmethod
    def apply_affine_translation(gdf: gpd.GeoDataFrame, x_offset: float, y_offset: float) -> gpd.GeoDataFrame:
        """
        Applies a 2D affine translation to correct positional inaccuracies.
        
        Args:
            gdf: The GeoDataFrame to be shifted (must be in a projected CRS like UTM).
            x_offset: The shift in the X direction (meters).
            y_offset: The shift in the Y direction (meters).
        """
        if gdf.crs.is_geographic:
            logger.warning("Applying affine translation on geographic CRS (WGS84). Offsets will be in degrees!")
        else:
            logger.info(f"Applying Affine Correction: X_shift={x_offset}m, Y_shift={y_offset}m")

        shifted_gdf = gdf.copy()
        shifted_gdf.geometry = shifted_gdf.geometry.apply(
            lambda geom: affinity.translate(geom, xoff=x_offset, yoff=y_offset)
        )
        return shifted_gdf