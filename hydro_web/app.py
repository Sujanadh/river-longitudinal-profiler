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
        
    with col1:
        st.subheader("DEM Visualization")
        # Simple heatmap for DEM
        fig_dem = px.imshow(dem_data, color_continuous_scale='viridis', origin='lower')
        fig_dem.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig_dem, width='stretch')
        
    with col2:
        st.subheader("River Profile (Main Stem)")
        # For now, just show dummy data as we need full flow accumulation for profiles
        dist = np.linspace(0, dem_data.shape[1], 100)
        # Dummy profile following a diagonal
        elev = np.linspace(np.nanmax(dem_data), np.nanmin(dem_data), 100)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dist, y=elev, mode='lines', name='Elevation'))
        fig.update_layout(xaxis_title="Distance (pixels)", yaxis_title="Elevation (m)")
        st.plotly_chart(fig, width='stretch')

        st.subheader("Chi Plot")
        chi = dist * 0.5 
        fig_chi = go.Figure()
        fig_chi.add_trace(go.Scatter(x=chi, y=elev, mode='lines', name='Chi-Elevation'))
        fig_chi.update_layout(xaxis_title="χ (Chi)", yaxis_title="Elevation (m)")
        st.plotly_chart(fig_chi, width='stretch')
else:
    with col1:
        st.subheader("Map View")
        st.info("Upload a DEM to visualize the topography.")
        st.image("https://via.placeholder.com/800x600.png?text=Waiting+for+DEM+Upload")
    
    with col2:
        st.subheader("Analysis")
        st.info("Profiles will appear here after analysis.")
