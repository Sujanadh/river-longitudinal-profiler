import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

def create_synthetic_dem(path="test_dem.tif", size=200):
    """
    Creates a synthetic tilted-plane DEM with a valley for testing.
    """
    x = np.linspace(0, 10, size)
    y = np.linspace(0, 10, size)
    X, Y = np.meshgrid(x, y)
    
    # Tilted plane: higher in the NE, lower in the SW
    dem = 100 - (X + Y)
    
    # Add a valley in the middle to force a river
    valley = 5 * np.exp(-((X - Y)**2) / 0.5)
    dem -= valley
    
    # Add a knickpoint (a step in the valley)
    dem[size//2:, size//2:] -= 10
    
    # Add some noise
    dem += np.random.normal(0, 0.1, dem.shape)

    # Save as GeoTIFF
    transform = from_origin(0, 10, 0.05, 0.05)
    with rasterio.open(
        path, 'w', driver='GTiff',
        height=dem.shape[0], width=dem.shape[1],
        count=1, dtype='float32',
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(dem.astype(np.float32), 1)
    
    print(f"Synthetic DEM created at {path}")
    return path

if __name__ == "__main__":
    create_synthetic_dem()
