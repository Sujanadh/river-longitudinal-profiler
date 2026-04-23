import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import rasterio
from io import BytesIO
from hydro_py.core import RiverProfiler, chi_analysis, slope_area_analysis, detect_knickpoints
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
    st.header("4. Analysis Parameters")
    kp_threshold = st.slider("Knickpoint Sensitivity", 0.5, 5.0, 2.0)

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

    with map_tabs[1]:
        st.subheader("Extracted Drainage Network")
        fig_net = px.imshow(network, color_continuous_scale='Greys', origin='lower')
        fig_net.update_layout(height=600)
        st.plotly_chart(fig_net, width='stretch')

    with map_tabs[2]:
        st.subheader("Shaded Relief (Filled DEM)")
        fig_shade = px.imshow(shaded, color_continuous_scale='gray', origin='lower')
        fig_shade.update_layout(height=600)
        st.plotly_chart(fig_shade, width='stretch')

    # LAYOUT: Profile Section
    st.divider()
    st.header("📈 Geomorphic Profile Analysis")
    
    if st.button("🚀 Extract & Analyze Profile"):
        try:
            with st.spinner("Extracting path and computing geomorphic metrics..."):
                dist, elev, acc = profiler.extract_profile(r_start, c_start)
                chi = chi_analysis(dist, acc, mn_ratio=mn_ratio)
                area, slope = slope_area_analysis(dist, elev, acc)
                kp_indices = detect_knickpoints(dist, elev, threshold=kp_threshold)
            
            p_col1, p_col2 = st.columns(2)
            
            with p_col1:
                st.subheader("Elevation Profile & Knickpoints")
                fig_elev = go.Figure()
                fig_elev.add_trace(go.Scatter(x=dist, y=elev, mode='lines', name='Profile', line=dict(color='brown', width=3)))
                if len(kp_indices) > 0:
                    fig_elev.add_trace(go.Scatter(
                        x=dist[kp_indices], y=elev[kp_indices], 
                        mode='markers', name='Knickpoints',
                        marker=dict(color='red', size=12, symbol='x')
                    ))
                fig_elev.update_layout(xaxis_title="Distance (m)", yaxis_title="Elevation (m)", height=450)
                st.plotly_chart(fig_elev, width='stretch')
                
            with p_col2:
                st.subheader("Chi ($\chi$) Transformation")
                fig_chi = go.Figure()
                fig_chi.add_trace(go.Scatter(x=chi, y=elev, mode='lines', name='$\chi$ Plot', line=dict(color='blue', width=3)))
                if len(kp_indices) > 0:
                    fig_chi.add_trace(go.Scatter(
                        x=chi[kp_indices], y=elev[kp_indices], 
                        mode='markers', name='Knickpoints',
                        marker=dict(color='red', size=12, symbol='x')
                    ))
                fig_chi.update_layout(xaxis_title="$\chi$", yaxis_title="Elevation (m)", height=450)
                st.plotly_chart(fig_chi, width='stretch')

            st.divider()
            sa_col1, sa_col2 = st.columns(2)
            with sa_col1:
                st.subheader("Slope-Area Analysis (Log-Log)")
                fig_sa = px.scatter(x=area, y=slope, log_x=True, log_y=True, labels={'x':'Area', 'y':'Slope'})
                fig_sa.update_traces(marker=dict(color='green', opacity=0.5))
                fig_sa.update_layout(height=450)
                st.plotly_chart(fig_sa, width='stretch')
                
            with sa_col2:
                st.subheader("Geomorphic Data Summary")
                summary_df = pd.DataFrame({
                    "Total Length (m)": [dist[-1]],
                    "Max Elevation (m)": [np.max(elev)],
                    "Min Elevation (m)": [np.min(elev)],
                    "Knickpoints Detected": [len(kp_indices)]
                })
                st.table(summary_df)
                
            st.success(f"Full analysis complete!")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Identify headwater coordinates from the maps and click 'Extract & Analyze Profile'.")
else:
    st.info("Upload a GeoTIFF DEM file to begin.")
