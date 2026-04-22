import numpy as np
import georust_core
from hydro_py.core import chi_analysis

def test_rust_core():
    print("Testing Rust Core...")
    res = georust_core.sum_as_string(5, 7)
    print(f"5 + 7 as string: {res}")
    assert res == "12"

    dem = np.random.rand(10, 10).astype(np.float32)
    flow_dir = georust_core.compute_flow_direction(dem)
    print("Flow direction computation successful.")
    print(f"Flow Dir Shape: {flow_dir.shape}")
    assert flow_dir.shape == (10, 10)

def test_chi_analysis():
    print("Testing Chi Analysis...")
    dist = np.array([0, 10, 20, 30], dtype=np.float32)
    area = np.array([100, 80, 60, 40], dtype=np.float32)
    chi = chi_analysis(dist, area)
    print(f"Chi values: {chi}")
    assert len(chi) == 4

if __name__ == "__main__":
    test_rust_core()
    test_chi_analysis()
    print("All builds and integrations verified!")
