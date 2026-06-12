# metrics.py

# metrics.py

import time
from functools import wraps

import streamlit as st


def profile_performance(func):
    """
    Performance profiling decorator.

    Features:
    - Preserves original function metadata (@wraps)
    - Exception-safe timing collection
    - Streamlit session-state telemetry logging
    - Compatible with Streamlit caching decorators
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        start_time = time.perf_counter()

        success = True
        error_message = None

        try:
            result = func(*args, **kwargs)
            return result

        except Exception as exc:
            success = False
            error_message = str(exc)
            raise

        finally:

            elapsed_time_ms = (
                time.perf_counter() - start_time
            ) * 1000

            if "telemetry_logs" not in st.session_state:
                st.session_state.telemetry_logs = {}

            st.session_state.telemetry_logs[func.__name__] = {
                "execution_time_ms": round(
                    elapsed_time_ms,
                    3
                ),
                "success": success,
                "error": error_message,
                "timestamp": time.time(),
            }

    return wrapper
