"""
Core configuration module.
Uses frozen dataclasses to ensure CRS constants are immutable across the pipeline.
Handles dynamic environment variables for cloud authentication.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

BasicConfig = {
    'level': logging.INFO,
    'format': '%(asctime)s-[ %(levelname)s ]- [%(name)s]-%(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S'
}

logging.basicConfig(**BasicConfig)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
logger.info("Loading environment variables from .env file")
load_dotenv()

@dataclass(frozen=True)
class SpatialConfig:
    """Immutable configuration for CRS and spatial thresholds."""
    WGS84: str = "EPSG:4326"
    UTM_43N: str = "EPSG:32643"  # Standard UTM Zone for Ahmedabad, India
    ROAD_BUFFER_METERS: float = 10.0
    
    # Cloud Infrastructure Constants
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID")