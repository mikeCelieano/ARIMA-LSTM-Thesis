import streamlit as st
import psutil
import os
import gc   
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

def get_ram_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

if 'mem_history' not in st.session_state:
    st.session_state.mem_history = []

current_mem = get_ram_usage()
st.session_state.mem_history.append(current_mem)

if len(st.session_state.mem_history) > 20:
    st.session_state.mem_history.pop(0)

st.title("🖥️ System Monitor & Diagnostic")
st.info("This monitor helps track RAM server usage in real-time.")

st.subheader("📈 Memory Usage Trend")
st.line_chart(st.session_state.mem_history)

ram_percent = (current_mem / 1024) * 100

col1, col2 = st.columns(2)
with col1:
    st.metric(
        label="Current RAM Usage", 
        value=f"{current_mem:.2f} MB",
        delta=f"{(current_mem - st.session_state.mem_history[-2] if len(st.session_state.mem_history) > 1 else 0):.2f} MB",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Capacity Used", 
        value=f"{ram_percent:.1f} %",
        delta="Limit: 1024 MB",
        delta_color="off"
    )

st.divider()
st.subheader("🔍 Diagnostic Insights")

with st.expander("Why is the RAM usage high?"):
    st.write("""
    1. **Library Overhead:** Importing heavy libraries like `tensorflow`, `keras`, or `statsmodels` allocates a significant amount of permanent memory. These resources stay in the RAM to keep the model engines ready for execution.
    2. **Python Memory Management:** Python's garbage collector doesn't always return memory to the operating system immediately after a task is finished. It often holds onto that space for future operations to improve speed.
    3. **Cumulative Usage:** Since Streamlit runs as a single process, the memory usage reflects everything loaded across all sessions. You can track the impact of a specific page by monitoring the memory jump after navigating to it.
    """)

st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("Refresh Status", use_container_width=True):
        st.rerun()

with c2:
    if st.button("Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.toast("Streamlit Cache Cleaned!")

with c3:
    if st.button("Clear All Data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        gc.collect()
        st.toast("All data cleared! App reset to initial state.")
        st.rerun()