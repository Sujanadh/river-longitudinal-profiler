import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import rasterio
from io import BytesIO
from hydro_py.core import RiverProfiler, chi_analysis
import plotly.express as px

st.set_page_config(page_title="River Profiler Next-Gen", layout="wide")

st.title("🌊 River Longitudinal Profile Analyzer")

def compute_shaded_relief(dem, azimuth=315, angle_altitude=45):
    azimuth = np.deg2rad(azimuth)
    altitude = np.deg2rad(angle_altitude)
    x, y = np.gradient(dem)
    slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
    aspect = np.arctan2(-x, y)
    shaded = np.sin(altitude) * np.sin(slope) + \
             np.cos(altitude) * np.cos(slope) * \
             np.cos(azimuth - aspect)
    return shaded

with st.sidebar:
    st.header("1. Input Data")
    dem_file = st.file_uploader("Upload DEM (GeoTIFF)", type=["tif", "tiff"])
    st.header("2. Extraction Settings")
    acc_threshold = st.number_input("Network Threshold (pixels)", value=1000)
    mn_ratio = st.slider("m/n Concavity Ratio", 0.1, 0.9, 0.45)
    st.header("3. Profile Selection")
    r_start = st.number_input("Start Row (Headwater)", value=0)
    c_start = st.number_input("Start Col (Headwater)", value=0)

if dem_file is not None:
    # Processing
    with st.spinner("🚀 Running High-Performance Geomorphic Engine..."):
        profiler = RiverProfiler(dem_file)
        filled, accumulation = profiler.compute_flow_accumulation()
        shaded = compute_shaded_relief(filled)
        network = np.where(accumulation > acc_threshold, 1, 0)

    # LAYOUT: Map Section
    st.header("🗺️ Geospatial Analysis")
    map_tabs = st.tabs(["Accumulation", "Drainage Network", "Shaded Relief"])
    
    with map_tabs[0]:
        st.subheader("Flow Accumulation (Log Scale)")
        fig_acc = px.imshow(np.log10(accumulation + 1), color_continuous_scale='blues', origin='lower')
        fig_acc.update_layout(height=600)
        st.plotly_chart(fig_acc, width='stretch')
        st.caption("Darker blue indicates larger drainage area.")

    with map_tabs[1]:
        st.subheader("Extracted Drainage Network")
        fig_net = px.imshow(network, color_continuous_scale='Greys', origin='lower')
        fig_net.update_layout(height=600)
        st.plotly_chart(fig_net, width='stretch')
        st.caption(f"Network extracted using threshold > {acc_threshold} pixels.")

    with map_tabs[2]:
        st.subheader("Shaded Relief (Filled DEM)")
        fig_shade = px.imshow(shaded, color_continuous_scale='gray', origin='lower')
        fig_shade.update_layout(height=600)
        st.plotly_chart(fig_shade, width='stretch')
        st.caption("Topography processed for hydrologic consistency.")

    # LAYOUT: Profile Section
    st.divider()
    st.header("📈 Longitudinal Profile Analysis")
    
    if st.button("🚀 Extract & Analyze Profile"):
        try:
            with st.spinner("Extracting path and computing integrals..."):
                dist, elev, acc = profiler.extract_profile(r_start, c_start)
                chi = chi_analysis(dist, acc, mn_ratio=mn_ratio)
            
            p_col1, p_col2 = st.columns(2)
            
            with p_col1:
                st.subheader("Elevation Profile")
                fig_elev = go.Figure()
                fig_elev.add_trace(go.Scatter(x=dist, y=elev, mode='lines', line=dict(color='brown', width=3)))
                fig_elev.update_layout(xaxis_title="Distance (m)", yaxis_title="Elevation (m)", height=450)
                st.plotly_chart(fig_elev, width='stretch')
                
            with p_col2:
                st.subheader("Chi ($\chi$) Transformation")
                fig_chi = go.Figure()
                fig_chi.add_trace(go.Scatter(x=chi, y=elev, mode='lines', line=dict(color='blue', width=3)))
                fig_chi.update_layout(xaxis_title="$\chi$", yaxis_title="Elevation (m)", height=450)
                st.plotly_chart(fig_chi, width='stretch')
                
            st.success(f"Profile extracted successfully! Length: {len(dist)} nodes.")
        except Exception as e:
            st.error(f"Error extracting profile: {e}. Ensure coordinates are within the DEM bounds.")
    else:
        st.info("💡 Tip: Identify a headwater pixel from the maps above, enter its Row/Col in the sidebar, and click 'Extract & Analyze Profile'.")

else:
    st.info("👋 Welcome! Please upload a GeoTIFF DEM file in the sidebar to begin.")
    st.image("https://via.placeholder.com/1200x400.png?text=Waiting+for+Topographic+Data", width=1200)
