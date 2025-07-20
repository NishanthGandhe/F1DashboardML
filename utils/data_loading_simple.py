import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Simple, deployment-friendly cache setup
try:
    # Try to create cache directory
    cache_dir = 'cache'
    os.makedirs(cache_dir, exist_ok=True)
    ff1.Cache.enable_cache(cache_dir)
    cache_enabled = True
    print("✅ FastF1 cache enabled")
except Exception as e:
    # If cache fails, continue without it
    cache_enabled = False
    print(f"⚠️ FastF1 cache disabled: {e}")

@st.cache_data
def get_available_years():
    """Get list of available years for F1 data"""
    current_year = datetime.now().year
    # FastF1 typically has data from 2018 onwards with good coverage
    return list(range(2018, current_year + 1))
