# Next-Generation River Longitudinal Profile Analysis System

## 1. Project Summary (High-Level)
This project introduces a next-generation, high-performance, and open-source system designed for the extraction and analysis of river longitudinal profiles, knickpoint detection, and slope-area analysis. Unlike existing tools such as LSDTopoTools, which rely heavily on CLI/file-based workflows and struggle with massive modern Digital Elevation Models (DEMs), this system leverages a Rust-based core engine bound to a native Python scientific API, topped with a modern web interface. It allows for multi-threaded raster processing, efficient memory access without full DEM loading, seamless integration into the GeoPandas/Rasterio ecosystems, and interactive geomorphic exploration, ultimately delivering an unmatched combination of speed, scalability, and usability.

## 2. Scientific Motivation
Traditional geomorphological analysis tools have failed to keep pace with the growing size of remote sensing datasets (e.g., high-resolution LiDAR and satellite-derived DEMs). Existing tools suffer from:
*   **Performance Bottlenecks:** Single-threaded processing and unoptimized memory handling make continental-scale or high-resolution DEM processing computationally prohibitive.
*   **Workflow Friction:** Heavy reliance on legacy C++ binaries with complex CLI inputs prevents fluid, exploratory science.
*   **Ecosystem Isolation:** Poor integration with the standard Python geospatial stack (e.g., NumPy, Rasterio, GeoPandas) forces data duplication and format conversions.
*   **Lack of Interactivity:** Geomorphological analysis relies heavily on iterative visual inspection (e.g., selecting channel heads, tuning smoothing parameters, identifying valid knickpoints), yet current tools lack modern GUI or web integration.

This system addresses these gaps by combining a low-level, memory-safe, and highly parallelized core (Rust) with the rich analytical ecosystem and rapid UI prototyping capabilities of Python, transforming river profile analysis from a batch-processing chore into an interactive, scalable exploration.

## 3. System Architecture Diagram (Textual Explanation)
The system is built on a robust 3-layer architecture:

*   **Layer 1: High-Performance Core Engine (Rust via PyO3)**
    *   **Memory Manager:** Uses memory-mapped files and chunking to avoid loading >10GB DEMs entirely into RAM.
    *   **Hydrology Compute Node:** Calculates D8/D∞ flow direction and flow accumulation using parallel, priority-queue-based algorithms.
    *   **Graph Constructor:** Extracts the river network and builds a directed acyclic graph (DAG) representing the channel topology.
    *   **Bindings:** PyO3 exposes these highly optimized Rust structures directly to Python as fast, zero-copy objects.

*   **Layer 2: Python Scientific API Layer (Python Orchestration)**
    *   **Data I/O Module:** Uses `rasterio` for raster bridging and `geopandas` for vector representations of extracted river lines and catchments.
    *   **Geomorphic Analysis Module:** Implements slope-area regressions, χ (chi) integral transformations, and knickpoint extraction using smoothing algorithms (Savitzky-Golay, B-Splines).
    *   **Scientific Integration:** Outputs NumPy arrays and Pandas DataFrames ready for machine learning or statistical pipelines.

*   **Layer 3: Web Application Layer (FastAPI + Streamlit/Dash)**
    *   **Backend (FastAPI):** Exposes REST/WebSocket endpoints to run compute-heavy extractions asynchronously without blocking the UI.
    *   **Frontend (Streamlit/Dash):** Provides an interactive dashboard where users can upload DEMs, visualize hillshades, click to define basin outlets, and interactively explore generated χ plots, elevation-distance profiles, and knickpoint distributions.

## 4. Core Algorithm Descriptions
*   **Flow Direction & Accumulation:** 
    *   *Algorithm:* A modified, parallelized priority-flood algorithm (e.g., Barnes et al., 2014) implemented in Rust. This handles depression filling/breaching and flow routing efficiently. By utilizing a lock-free queue or localized chunk processing, it achieves massive parallel speedups over traditional recursive or single-threaded O(N) methods.
*   **River Network Extraction (Graph Construction):**
    *   *Algorithm:* Once accumulation thresholds are met, the algorithm traces flow paths down-gradient, representing junctions as nodes and segments as edges in a Directed Acyclic Graph. This graph structure allows instantaneous downstream/upstream traversal required for χ analysis.
*   **χ (Chi) Transformation:**
    *   *Algorithm:* $\chi = \int (A_0 / A(x))^{m/n} dx$. Computed by traversing the river graph from base level (outlet) to headwaters. The Rust core computes cumulative drainage area $A(x)$ and distance $dx$, allowing Python to quickly vectorize the integral for varying $m/n$ concavity indices.
*   **Knickpoint Detection & Smoothing:**
    *   *Algorithm:* Raw DEM profiles are notoriously noisy. The Python layer applies a fast, vectorized Savitzky-Golay filter or a penalized spline regression to the elevation profile. Knickpoints are then identified using a localized peak detection on the second derivative of the smoothed elevation with respect to distance or χ.

## 5. Module-by-Module Breakdown
1.  **`georust_core` (Rust Library):**
    *   `src/io.rs`: Memory-mapped raster reading/chunking.
    *   `src/routing.rs`: Priority-flood, D8/Dinf flow directions.
    *   `src/network.rs`: Channel head identification, DAG extraction.
    *   `src/bindings.rs`: PyO3 Python interface.
2.  **`hydro_py` (Python Scientific API):**
    *   `hydro_py.read()`: Wraps `rasterio` to initialize the core.
    *   `hydro_py.extract_network(threshold)`: Returns a `GeoDataFrame` of streams.
    *   `hydro_py.profile()`: Computes distance, elevation, drainage area along paths.
    *   `hydro_py.analysis.chi()`: Computes χ transformations.
    *   `hydro_py.analysis.knickpoints()`: Applies smoothing and detects anomalies.
3.  **`hydro_web` (Interactive App):**
    *   `app.py`: Main Streamlit/Dash entry point.
    *   `components/map_view.py`: Leaflet/Folium integration for DEM/Network visualization.
    *   `components/plots.py`: Plotly integration for interactive slope-area and χ-elevation charts.

## 6. Technology Stack Justification
*   **Core - Rust & PyO3:** Rust is chosen over C++ for its strict memory safety guarantees, fearless concurrency (crucial for parallel raster processing), and modern build system (Cargo). PyO3 provides seamless, low-overhead bindings to Python, far easier to maintain than Cython or raw C-API extensions.
*   **API - Python (NumPy, Rasterio, GeoPandas):** Python is the lingua franca of scientific computing. By outputting standard DataFrames and Arrays, the tool instantly integrates with existing user workflows, unlike LSDTopoTools which traps data in proprietary or scattered text formats.
*   **Web - FastAPI & Streamlit/Dash:** Streamlit enables rapid development of highly interactive data apps with minimal frontend code. FastAPI provides a robust asynchronous backend to handle heavy compute tasks initiated by the UI, ensuring the interface remains responsive.

## 7. Performance Optimization Strategy
*   **Memory-Mapped I/O:** DEMs larger than system RAM are processed using OS-level memory mapping (mmap).
*   **Cache-Oblivious Traversal:** Raster processing algorithms (like flow routing) will use block-based or Hilbert-curve traversal patterns to maximize L1/L2 cache hits.
*   **Vectorization:** Analytical functions (smoothing, integrating) in the Python layer utilize NumPy/CuPy vectorized operations, pushing loops down to optimized C/C++ backends.
*   **Optional GPU Acceleration:** The Python API will feature CuPy fallbacks for highly parallel tasks like large-scale grid smoothing or convolution, automatically detecting CUDA availability.

## 8. Web Application Design
*   **Sidebar:** File upload/selection (GeoTIFF), parameter tuning (accumulation threshold, smoothing window, concavity index $m/n$).
*   **Main Dashboard - Top:** Interactive map (using `folium` or `deck.gl` via Streamlit) displaying the shaded relief and extracted colored river network. Users can click on any stream segment to select a basin.
*   **Main Dashboard - Bottom Left:** Interactive Plotly graph of Elevation vs. Distance from outlet. Includes toggles to show/hide detected knickpoints.
*   **Main Dashboard - Bottom Right:** Interactive Plotly graph of Elevation vs. χ. A slider allows real-time adjustment of the $m/n$ ratio to linearize the main stem profile.
*   **Export:** Buttons to download the network as GeoJSON and profiles as CSV.

## 9. Benchmarking and Evaluation Plan
To rigorously evaluate the system, we will benchmark against LSDTopoTools and ArcGIS/QGIS standard hydrology toolsets.
*   **Datasets:** A 30m SRTM DEM tile (small), a 10m NED tile (medium), and a 1m LiDAR DEM >10GB (large).
*   **Metrics:**
    1.  **Runtime Performance:** Total time from file read to network extraction. We expect the Rust core to outperform Python/QGIS and match or exceed LSDTopoTools through better multi-threading.
    2.  **Memory Usage:** Peak RAM consumption monitored via `mprof`. Our mmap strategy should keep peak memory significantly lower than in-memory tools.
    3.  **Accuracy:** Cross-validation of extracted river lengths, cumulative drainage areas, and knickpoint locations against LSDTopoTools to ensure scientific validity.
    4.  **Scalability:** Plotting runtime against DEM size ($N$ pixels) to demonstrate algorithmic complexity (aiming for $O(N)$ or $O(N \log N)$).

## 10. Research Paper Outline (Ready for Publication)
**Target Journal:** *Earth Surface Processes and Landforms (ESPL)* or *Computers & Geosciences*
*   **Title:** Next-Generation River Profile Extraction: A Scalable, Interactive, and Python-Native Architecture.
*   **Abstract:** Highlighting the limitations of current tools, the novel Rust/Python architecture, and the performance gains.
*   **1. Introduction:** The explosion of high-res topography data; the need for interactive geomorphology; limitations of legacy CLI tools (LSDTopoTools).
*   **2. System Architecture:** Detailing the 3-layer approach (Rust core, Python API, Web UI). Emphasizing memory-safe parallelism and zero-copy bindings.
*   **3. Core Algorithms:** Mathematical and computational description of the parallel priority-flood implementation and graph-based network extraction.
*   **4. Geomorphic Analysis Integration:** How χ-analysis and slope-area regressions are seamlessly integrated with standard Python data structures (GeoPandas).
*   **5. Performance Benchmarks:** Presentation of speed and memory scaling results against existing software using 1m LiDAR and 30m global datasets.
*   **6. Case Study:** A brief demonstration of the interactive web UI used to identify transient knickpoints in a tectonically active region.
*   **7. Conclusion & Future Work:** Open-source availability and potential for ML integration.

## 11. Step-by-Step Implementation Roadmap (MVP → Full System)
*   **Phase 1: Core Engine MVP (Weeks 1-4)**
    *   Set up Rust project (`cargo`) and PyO3 bindings.
    *   Implement memory-mapped raster reading.
    *   Implement single-threaded D8 flow direction and accumulation.
    *   Extract simple river networks to Python arrays.
*   **Phase 2: Scientific API & Parallelization (Weeks 5-8)**
    *   Upgrade Rust core to use parallel priority-flood algorithms.
    *   Build the graph topology constructor in Rust.
    *   Develop the `hydro_py` Python wrapper, integrating GeoPandas and Rasterio.
    *   Implement χ analysis, slope-area, and basic knickpoint detection.
*   **Phase 3: Web UI & Interactivity (Weeks 9-11)**
    *   Develop the FastAPI backend for asynchronous task handling.
    *   Build the Streamlit dashboard (map view, interactive Plotly charts).
    *   Wire UI parameters to the Python API.
*   **Phase 4: Optimization, Benchmarking & Release (Weeks 12-14)**
    *   Profile the Rust core; optimize cache access patterns.
    *   Implement optional CuPy GPU fallbacks in Python.
    *   Execute the formal benchmarking plan.
    *   Write documentation, CI/CD pipelines, and prepare the v1.0 open-source release.
