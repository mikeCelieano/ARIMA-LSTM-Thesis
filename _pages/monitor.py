import streamlit as st
import psutil
import os
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

def get_ram_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

st.title("🖥️ System Monitor")
st.divider()

ram_mb = get_ram_usage()
ram_percent = (ram_mb / 1024) * 100

st.metric(
    label="RAM Usage", 
    value=f"{ram_mb:.2f} MB",
    delta=f"{ram_percent:.1f}% from limit",
    delta_color="inverse" if ram_mb > 800 else "normal"
)

if st.button("Refresh Data"):
    st.rerun()

if st.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache clean succeeded!")