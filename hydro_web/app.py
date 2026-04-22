import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import rasterio
from io import BytesIO
from hydro_py.core import RiverProfiler
import plotly.express as px

st.set_page_config(page_title="River Profiler Next-Gen", layout="wide")

st.title("🌊 River Longitudinal Profile Analyzer")

with st.sidebar:
    st.header("Parameters")
    dem_file = st.file_uploader("Upload DEM (GeoTIFF)", type=["tif", "tiff"])
    acc_threshold = st.number_input("Accumulation Threshold", value=1000)
    mn_ratio = st.slider("m/n Concavity Ratio", 0.1, 0.9, 0.45)

col1, col2 = st.columns([1, 1])

if dem_file is not None:
    # Read the uploaded file
    with rasterio.open(dem_file) as src:
        dem_data = src.read(1).astype(np.float32)
        # Handle nodata if present
        dem_data[dem_data == src.nodata] = np.nan
        
    # Initialize profiler
    # Note: RiverProfiler currently takes a path, but we can pass the data
    # For now, let's use the Rust functions directly in the UI for speed
    import georust_core
    
    with st.spinner("Processing Hydrology (Rust Core)..."):
        filled = georust_core.fill_depressions(dem_data)
        accumulation = georust_core.compute_accumulation(filled)
        
    with col1:
        st.subheader("River Network")
        # Mask accumulation for network extraction
        network = np.where(accumulation > acc_threshold, 1, 0)
        
        # Display accumulation (log scale for better visibility)
        fig_acc = px.imshow(np.log10(accumulation + 1), color_continuous_scale='blues', origin='lower')
        # Overlay network if possible or just show network
        fig_net = px.imshow(network, color_continuous_scale='Greys', origin='lower', opacity=0.5)
        
        st.plotly_chart(fig_acc, width='stretch')
        st.caption("Flow Accumulation (Log10 scale)")
        
    with col2:
        st.subheader("Topography (Filled)")
        fig_dem = px.imshow(filled, color_continuous_scale='viridis', origin='lower')
        st.plotly_chart(fig_dem, width='stretch')
        
        st.info("Accumulation computed. Network extraction complete.")
else:
    with col1:
        st.subheader("Map View")
        st.info("Upload a DEM to visualize the topography.")
        st.image("https://via.placeholder.com/800x600.png?text=Waiting+for+DEM+Upload")
    
    with col2:
        st.subheader("Analysis")
        st.info("Profiles will appear here after analysis.")
