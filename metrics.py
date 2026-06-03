# metrics.py
import time
import streamlit as st

def profile_performance(func):
    """
    Advanced Decorator to measure execution time of functions.
    Injects telemetry directly into Streamlit's session state.
    """
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time_ms = (end_time - start_time) * 1000
        
        # Initialize logs if not present
        if 'telemetry_logs' not in st.session_state:
            st.session_state.telemetry_logs = {}
            
        # Store execution time for the specific function
        st.session_state.telemetry_logs[func.__name__] = {
            "execution_time_ms": elapsed_time_ms,
            "args": f"Type: {args[0] if len(args)>0 else 'N/A'}"
        }
        return result
    return wrapper
