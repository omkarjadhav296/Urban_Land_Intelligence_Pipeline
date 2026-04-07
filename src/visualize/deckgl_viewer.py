"""
3D Visualization Engine.

Leverages Pydeck (Deck.GL) to extrude 2D polygons based on elevation attributes,
generating an interactive, self-contained HTML file without needing a backend server.
"""
import os
import logging
import geopandas as gpd
import pydeck as pdk

logger = logging.getLogger(__name__)

class Viewer3D:
    def __init__(self, config):
        self.config = config

    def generate_3d_viewer(self, gdf: gpd.GeoDataFrame, output_dir: str):
        """Generates an interactive 3D WebGL HTML viewer."""
        logger.info("Generating 3D HTML Viewer...")
        
        gdf_wgs84 = gdf.to_crs(self.config.WGS84)
        
        if gdf_wgs84.empty:
            logger.warning("Empty dataframe provided to 3D Viewer.")
            return
            
        centroid = gdf_wgs84.geometry.unary_union.centroid

        layer = pdk.Layer(
            "GeoJsonLayer",
            gdf_wgs84,
            opacity=0.8,
            stroked=True,
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation="elev_mean * 2",
            get_fill_color="[255, 255 - (elev_mean * 3), 150]",
            get_line_color=[255, 255, 255],
        )

        view_state = pdk.ViewState(
            latitude=centroid.y,
            longitude=centroid.x,
            zoom=15,
            pitch=45,
            bearing=0
        )

        r = pdk.Deck(
            layers=[layer], 
            initial_view_state=view_state,
            map_style=pdk.map_styles.SATELLITE
        )
        
        # THE FIX: Dynamically target the project root instead of data/output/
        project_root = os.getcwd()
        output_path = os.path.join(project_root, "index.html")
        
        r.to_html(output_path)
        logger.info(f"3D Viewer successfully saved to project root: {output_path}")