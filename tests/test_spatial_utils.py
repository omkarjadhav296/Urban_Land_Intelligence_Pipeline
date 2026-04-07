"""
Unit tests for the SpatialUtils module.

WHAT: Tests the mathematical affine translations.
WHY: Ensures that our basemap alignment corrections (Task 1) physically shift
     the geometry arrays by the exact metric offsets requested.
HOW: Uses pytest.approx to handle minor floating-point precision differences 
     inherent in low-level spatial C-libraries.
"""
import pytest
from src.core.spatial_utils import SpatialUtils

def test_apply_affine_translation(mock_tp_utm):
    """Verifies that the polygon is shifted positively on the X and Y axes."""
    
    # Arrange
    x_shift = 10.0
    y_shift = 5.0
    original_centroid = mock_tp_utm.geometry.iloc[0].centroid
    
    # Act
    shifted_gdf = SpatialUtils.apply_affine_translation(
        mock_tp_utm, x_offset=x_shift, y_offset=y_shift
    )
    shifted_centroid = shifted_gdf.geometry.iloc[0].centroid
    
    # Assert
    # Check that the new centroid is exactly 10m East and 5m North.
    # We use pytest.approx because floating point spatial math can yield tiny fractions (e.g., 10.0000000002)
    assert shifted_centroid.x == pytest.approx(original_centroid.x + x_shift)
    assert shifted_centroid.y == pytest.approx(original_centroid.y + y_shift)