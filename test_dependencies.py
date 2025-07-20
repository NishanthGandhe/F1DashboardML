#!/usr/bin/env python3
"""
Test script to verify all requirements are properly installed
"""

print("🧪 Testing F1 Analysis Platform Dependencies...")
print("=" * 50)

# Test core dependencies
try:
    import streamlit
    print(f"✅ Streamlit: {streamlit.__version__}")
except ImportError as e:
    print(f"❌ Streamlit: {e}")

try:
    import fastf1
    print(f"✅ FastF1: {fastf1.__version__}")
except ImportError as e:
    print(f"❌ FastF1: {e}")

try:
    import pandas
    print(f"✅ Pandas: {pandas.__version__}")
except ImportError as e:
    print(f"❌ Pandas: {e}")

try:
    import numpy
    print(f"✅ NumPy: {numpy.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import plotly
    print(f"✅ Plotly: {plotly.__version__}")
except ImportError as e:
    print(f"❌ Plotly: {e}")

try:
    import sklearn
    print(f"✅ Scikit-learn: {sklearn.__version__}")
except ImportError as e:
    print(f"❌ Scikit-learn: {e}")

try:
    import lightgbm
    print(f"✅ LightGBM: {lightgbm.__version__}")
except ImportError as e:
    print(f"❌ LightGBM: {e}")

try:
    import joblib
    print(f"✅ Joblib: {joblib.__version__}")
except ImportError as e:
    print(f"❌ Joblib: {e}")

try:
    import matplotlib
    print(f"✅ Matplotlib: {matplotlib.__version__}")
except ImportError as e:
    print(f"❌ Matplotlib: {e}")

try:
    import seaborn
    print(f"✅ Seaborn: {seaborn.__version__}")
except ImportError as e:
    print(f"❌ Seaborn: {e}")

try:
    import requests
    print(f"✅ Requests: {requests.__version__}")
except ImportError as e:
    print(f"❌ Requests: {e}")

try:
    import scipy
    print(f"✅ SciPy: {scipy.__version__}")
except ImportError as e:
    print(f"❌ SciPy: {e}")

# Test application imports
print("\n" + "=" * 50)
print("🔍 Testing Application Modules...")
print("=" * 50)

try:
    from utils.data_loading import get_session_data, get_lap_data
    print("✅ utils.data_loading imported successfully")
except ImportError as e:
    print(f"❌ utils.data_loading: {e}")

try:
    from utils.plotting import plot_pace_comparison, plot_gap_analysis
    print("✅ utils.plotting imported successfully")
except ImportError as e:
    print(f"❌ utils.plotting: {e}")

print("\n" + "=" * 50)
print("🎯 Dependency Test Complete!")
print("=" * 50)
