# utils/performance.py
import time
import streamlit as st
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        if "performance_log" not in st.session_state:
            st.session_state.performance_log = []

    def start_timer(self, operation_name: str):
        """Starts a timer for a specific operation."""
        return {"operation": operation_name, "start_time": time.perf_counter()}

    def end_timer(self, timer_data: dict):
        """Ends a timer and logs the performance data."""
        duration_ms = (time.perf_counter() - timer_data["start_time"]) * 1000
        log_entry = {
            "operation": timer_data["operation"],
            "duration_ms": duration_ms,
            "timestamp": datetime.now()
        }
        st.session_state.performance_log.append(log_entry)
        print(f"PERF_LOG: {log_entry['operation']} took {log_entry['duration_ms']:.2f} ms.")