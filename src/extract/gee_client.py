"""
Google Earth Engine (GEE) API Client.

Abstracts the authentication and raw cloud compute capabilities of Earth Engine.
Enforces separation of concerns by keeping vendor-specific API calls out of the
business logic layers.
"""
import logging
import ee

logger = logging.getLogger(__name__)

class GEEClient:
    """Enterprise client for Google Earth Engine integration."""
    
    def __init__(self, project_id: str = None):
        """Initializes the Earth Engine environment."""
        try:
            logger.info("Initializing Google Earth Engine Client...")
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            logger.info("GEE Initialization Successful.")
        except Exception as e:
            logger.error(f"GEE Initialization failed. Run 'earthengine authenticate'. Error: {e}")
            raise RuntimeError("Earth Engine Auth failed.") from e

    def get_copernicus_dem(self) -> ee.Image:
        """Fetches the Copernicus 30m Global DEM."""
        return ee.Image('COPERNICUS/DEM/GLO30')

    def compute_zonal_stats(self, feature_collection: ee.FeatureCollection, image: ee.Image, scale: int = 30) -> ee.FeatureCollection:
        """Pushes the zonal statistics computation down to Google's servers."""
        logger.info("Dispatching Zonal Statistics computation to Google Cloud...")
        
        reducer = ee.Reducer.mean().combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True
        )
        
        reduced_fc = image.reduceRegions(
            collection=feature_collection,
            reducer=reducer,
            scale=scale,
            crs='EPSG:4326'
        )
        return reduced_fc