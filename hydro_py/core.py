import numpy as np
import rasterio
from typing import Tuple
import georust_core

class RiverProfiler:
    """
    Main API class for River Longitudinal Profile analysis.
    Wraps the georust_core engine.
    """
    def __init__(self, dem_path: str):
        self.dem_path = dem_path
        with rasterio.open(dem_path) as src:
            self.dem = src.read(1).astype(np.float32)
            self.transform = src.transform
            self.crs = src.crs

    def compute_flow_accumulation(self):
        """
        Fills depressions and computes flow accumulation.
        """
        filled = georust_core.fill_depressions(self.dem)
        accumulation = georust_core.compute_accumulation(filled)
        return filled, accumulation

    def get_profile(self, x: float, y: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (distance, elevation) for a river profile starting at (x, y).
        """
        # Placeholder
        return np.array([0, 10, 20]), np.array([100, 95, 90])

def chi_analysis(distance: np.ndarray, area: np.ndarray, mn_ratio: float = 0.45) -> np.ndarray:
    """
    Computes the Chi integral: Integral of (A0/A)^mn dx
    """
    a0 = 1.0 # Reference area
    integrand = (a0 / area) ** mn_ratio
    return np.cumsum(integrand * np.gradient(distance))
