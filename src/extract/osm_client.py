"""
OpenStreetMap API Client.

Wraps OSMnx to dynamically fetch vector infrastructure topology (Roads, Buildings) 
using the Overpass API. Enforces strict typing and error handling.
"""
import logging
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

class OSMClient:
    def __init__(self, config):
        self.config = config
        ox.settings.log_console = False
        ox.settings.use_cache = True

    def fetch_infrastructure(self, boundary_polygon: Polygon, infrastructure_type: str) -> gpd.GeoDataFrame:
        """Fetches infrastructure from OSM within a WGS84 polygon boundary."""
        logger.info(f"Extracting OSM {infrastructure_type} topology...")
        
        try:
            # Inject appropriate Overpass API tags based on requested type
            if infrastructure_type == 'buildings':
                tags = {'building': True}
            elif infrastructure_type == 'roads':
                tags = {'highway': True}
            elif infrastructure_type == 'all':
                tags = {'building': True, 'highway': True}
            else:
                raise ValueError(f"Invalid infrastructure type: {infrastructure_type}")

            # Execute spatial extraction
            gdf = ox.features_from_polygon(boundary_polygon, tags)
            
            # Filter geometries to enforce topological purity
            if infrastructure_type == 'buildings':
                gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            elif infrastructure_type == 'roads':
                gdf = gdf[gdf.geometry.type.isin(['LineString', 'MultiLineString'])]
            # Note: For 'all', we inherently keep both Polygons (buildings) and LineStrings (roads)
                
            logger.info(f"Successfully extracted {len(gdf)} {infrastructure_type} features.")
            return gdf

        except Exception as e:
            logger.error(f"Failed to fetch {infrastructure_type} from OSM: {e}")
            # Fallback to an empty, properly-projected dataframe to prevent pipeline crashes
            return gpd.GeoDataFrame(geometry=[], crs=self.config.WGS84)