import numpy as np
import rasterio
from typing import Tuple
import georust_core

class RiverProfiler:
    """
    Main API class for River Longitudinal Profile analysis.
    Wraps the georust_core engine.
    """
    def __init__(self, dem_source):
        self.dem_source = dem_source
        with rasterio.open(dem_source) as src:
            self.dem = src.read(1).astype(np.float32)
            self.transform = src.transform
            self.crs = src.crs

    def compute_flow_accumulation(self):
        """
        Fills depressions and computes flow accumulation.
        """
        self.filled = georust_core.fill_depressions(self.dem)
        self.fdir = georust_core.compute_flow_direction(self.filled)
        self.accumulation = georust_core.compute_accumulation_from_fdir(self.fdir)
        return self.filled, self.accumulation

    def extract_profile(self, start_r: int, start_c: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts distance, elevation, and drainage area along a path.
        """
        path = georust_core.trace_path(self.fdir, start_r, start_c)
        rows, cols = zip(*path)
        
        elevations = self.filled[rows, cols]
        accumulations = self.accumulation[rows, cols]
        
        # Compute cumulative distance (simplified as 1 unit per pixel for now)
        # In a real system, we would use the geotransform for true meters
        distances = np.arange(len(path)) * 30.0 # Assuming 30m pixels
        
        return distances, elevations, accumulations

    def get_profile(self, x: float, y: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (distance, elevation) for a river profile starting at (x, y).
        """
        # Placeholder
        return np.array([0, 10, 20]), np.array([100, 95, 90])

from scipy.signal import savgol_filter

def chi_analysis(distance: np.ndarray, area: np.ndarray, mn_ratio: float = 0.45) -> np.ndarray:
    """
    Computes the Chi integral: Integral of (A0/A)^mn dx
    """
    a0 = 1.0 # Reference area
    # Use trapz for better integration
    integrand = (a0 / area) ** mn_ratio
    return np.concatenate(([0], np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(distance))))

def slope_area_analysis(distance: np.ndarray, elevation: np.ndarray, area: np.ndarray, window_size: int = 11):
    """
    Computes slope and area for log-log analysis.
    """
    # Smooth elevation to get better slope
    if len(elevation) > window_size:
        smoothed_elev = savgol_filter(elevation, window_size, 3)
    else:
        smoothed_elev = elevation
        
    slope = np.abs(np.gradient(smoothed_elev, distance))
    # Avoid zero slope for log plots
    slope[slope <= 0] = 1e-6
    return area, slope

def detect_knickpoints(distance: np.ndarray, elevation: np.ndarray, window_size: int = 21, threshold: float = 2.0):
    """
    Identifies knickpoints based on the second derivative of elevation (curvature).
    """
    if len(elevation) < window_size:
        return np.array([])
        
    smoothed = savgol_filter(elevation, window_size, 3)
    # Curvature (roughly d2z/dx2)
    curvature = np.gradient(np.gradient(smoothed, distance), distance)
    
    # Identify indices where curvature is significantly high
    # (Simplified peak detection)
    kp_indices = []
    for i in range(1, len(curvature) - 1):
        if curvature[i] > curvature[i-1] and curvature[i] > curvature[i+1] and curvature[i] > threshold * np.std(curvature):
            kp_indices.append(i)
            
    return np.array(kp_indices)
