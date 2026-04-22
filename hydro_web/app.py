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
        profiler = RiverProfiler(dem_file) # Re-init with file
        filled, accumulation = profiler.compute_flow_accumulation()
        
    with col1:
        st.subheader("River Network")
        # Find the point with maximum accumulation (the outlet) to find the longest river
        max_idx = np.unravel_index(np.argmax(accumulation), accumulation.shape)
        
        # Display accumulation (log scale)
        fig_acc = px.imshow(np.log10(accumulation + 1), color_continuous_scale='blues', origin='lower')
        st.plotly_chart(fig_acc, width='stretch')
        st.caption(f"Flow Accumulation. Max accumulation at: {max_idx}")
        
    with col2:
        st.subheader("Main Stem Analysis")
        # Extract the profile starting from a high accumulation point (main stem)
        # For simplicity, we'll pick the pixel with max accumulation and trace "upstream" 
        # is hard, so we just pick the outlet and show the profile if we have a way to 
        # select a headwater. For now, let's allow user to input a point.
        
        st.write("Extracting longest river profile...")
        # To get a good profile, we need a headwater point. 
        # Let's find a point with high accumulation and trace it.
        # For the demo, we'll just pick a point with high accumulation but not the absolute max.
        
        dist, elev, acc = profiler.extract_profile(0, 0) # Dummy start
        
        # Better: let user choose coordinates
        r_start = st.number_input("Start Row", 0, accumulation.shape[0]-1, 0)
        c_start = st.number_input("Start Col", 0, accumulation.shape[1]-1, 0)
        
        if st.button("Extract Profile"):
            dist, elev, acc = profiler.extract_profile(r_start, c_start)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dist, y=elev, mode='lines', name='Elevation'))
            fig.update_layout(xaxis_title="Distance (m)", yaxis_title="Elevation (m)")
            st.plotly_chart(fig, width='stretch')

            st.subheader("Chi Plot")
            chi = chi_analysis(dist, acc, mn_ratio=mn_ratio)
            fig_chi = go.Figure()
            fig_chi.add_trace(go.Scatter(x=chi, y=elev, mode='lines', name='Chi-Elevation'))
            fig_chi.update_layout(xaxis_title="χ (Chi)", yaxis_title="Elevation (m)")
            st.plotly_chart(fig_chi, width='stretch')
        else:
            st.info("Select a headwater point (Row/Col) and click Extract Profile.")
else:
    with col1:
        st.subheader("Map View")
        st.info("Upload a DEM to visualize the topography.")
        st.image("https://via.placeholder.com/800x600.png?text=Waiting+for+DEM+Upload")
    
    with col2:
        st.subheader("Analysis")
        st.info("Profiles will appear here after analysis.")
