#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import requests
from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.express as px

# Reusing existing functions from Task 1-7
def fetch_iss_tle():
    """Fetch ISS TLE data from CelesTrak"""
    url = "https://celestrak.org/NORAD/elements/stations.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split('\n')
        for i, line in enumerate(lines):
            if 'ISS' in line.upper() or 'ZARYA' in line.upper():
                if i + 2 < len(lines):
                    return lines[i+1].strip(), lines[i+2].strip()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching TLE data: {e}")
        return None

def get_current_iss_position(tle_line1, tle_line2):
    """Get current ISS position using Skyfield"""
    ts = load.timescale()
    satellite = EarthSatellite(tle_line1, tle_line2, 'ISS (ZARYA)', ts)
    t = ts.now()
    geocentric = satellite.at(t)
    subpoint = geocentric.subpoint()
    return {
        'latitude': subpoint.latitude.degrees,
        'longitude': subpoint.longitude.degrees,
        'altitude': subpoint.elevation.km,
        'timestamp': t.utc_datetime()
    }
def main():
    st.set_page_config(page_title="ISS Tracker", page_icon="🛰️", layout="wide")
    
    st.title("🛰️ International Space Station Tracker")
    st.markdown("""
    Real-time tracking of the International Space Station (ISS) using TLE data from CelesTrak.
    The position updates every 10 seconds.
    """)
    
    # Initialize session state for tracking data
    if 'tracking_data' not in st.session_state:
        st.session_state.tracking_data = pd.DataFrame(columns=['timestamp', 'latitude', 'longitude', 'altitude'])
    
    # Create layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live ISS Position")
        map_placeholder = st.empty()
        
    with col2:
        st.subheader("Current Telemetry")
        telemetry_placeholder = st.empty()
        st.subheader("Recent Positions")
        table_placeholder = st.empty()
    
    # Add a toggle for auto-update
    auto_update = st.sidebar.checkbox("Auto-update", True, help="Automatically update position every 10 seconds")
    update_freq = st.sidebar.slider("Update frequency (seconds)", 5, 60, 10)
    
    # Add a button for manual update
    if st.sidebar.button("Update Now"):
        update_position(map_placeholder, telemetry_placeholder, table_placeholder)
    
    # Main update loop
    while auto_update:
        update_position(map_placeholder, telemetry_placeholder, table_placeholder)
        time.sleep(update_freq)
        
def update_position(map_placeholder, telemetry_placeholder, table_placeholder):
    """Update the dashboard with current ISS position"""
    tle_data = fetch_iss_tle()
    if tle_data:
        line1, line2 = tle_data
        position = get_current_iss_position(line1, line2)
        
        # Add to tracking history
        new_row = pd.DataFrame([{
            'timestamp': position['timestamp'],
            'latitude': position['latitude'],
            'longitude': position['longitude'],
            'altitude': position['altitude']
        }])
        st.session_state.tracking_data = pd.concat(
            [st.session_state.tracking_data, new_row]
        ).drop_duplicates().tail(20)  # Keep last 20 positions
        
        # Update map
        fig = px.scatter_geo(
            st.session_state.tracking_data,
            lat='latitude',
            lon='longitude',
            hover_name='timestamp',
            projection='natural earth',
            title='ISS Ground Track'
        )
        fig.update_traces(
            marker=dict(size=12, color='red'),
            line=dict(color='red', width=2)
        )
        fig.update_geos(
            showland=True, landcolor="lightgray",
            showocean=True, oceancolor="azure",
            showcountries=True
        )
        map_placeholder.plotly_chart(fig, use_container_width=True)
        
        # Update telemetry
        telemetry_placeholder.markdown(f"""
        - **Latitude**: {position['latitude']:.4f}°
        - **Longitude**: {position['longitude']:.4f}°
        - **Altitude**: {position['altitude']:.1f} km
        - **Last Update**: {position['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}
        """)
        
        # Update table
        table_placeholder.dataframe(
            st.session_state.tracking_data.sort_values('timestamp', ascending=False),
            hide_index=True,
            column_config={
                "timestamp": "Timestamp",
                "latitude": "Latitude",
                "longitude": "Longitude",
                "altitude": "Altitude (km)"
            }
        )

if __name__ == "__main__":
    main()


# In[ ]:




