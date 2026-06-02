# metrics.py
import time
import logging
from functools import wraps
import streamlit as st

# Configure logging for production environments
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def profile_performance(func):
    """Decorator to measure and log function execution time (Observability)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        exec_time_ms = (end_time - start_time) * 1000
        logging.info(f"[PROFILER] {func.__name__} executed in {exec_time_ms:.3f} ms")
        
        # Store metrics in Streamlit session state to display in UI if needed
        if 'health_metrics' not in st.session_state:
            st.session_state.health_metrics = {}
        st.session_state.health_metrics[func.__name__] = exec_time_ms
        
        return result
    return wrapper