"""
Data loading utilities for F1BeginnerProject
Handles all FastF1 interactions with proper caching for performance
"""

import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
from datetime import datetime

# Enable FastF1 caching for better performance
ff1.Cache.enable_cache('cache')

@st.cache_data
def get_available_years():
    """Get list of available years for F1 data"""
    current_year = datetime.now().year
    # FastF1 typically has data from 2018 onwards with good coverage
    return list(range(2018, current_year + 1))

@st.cache_data
def get_race_schedule(year):
    """Get race schedule for a given year"""
    try:
        schedule = ff1.get_event_schedule(year)
        # Filter for actual race events (exclude testing, etc.)
        races = schedule[schedule['EventFormat'] != 'testing'].copy()
        return races[['EventName', 'Location', 'Country', 'EventDate']].to_dict('records')
    except Exception as e:
        st.error(f"Error loading race schedule for {year}: {str(e)}")
        return []

@st.cache_data
def load_race_data(year, race_name):
    """Load race session data with caching"""
    try:
        with st.spinner(f"Loading {race_name} {year} race data..."):
            session = ff1.get_session(year, race_name, 'R')
            session.load()
            return session
    except Exception as e:
        st.error(f"Error loading race data: {str(e)}")
        return None

@st.cache_data
def get_driver_list(_session):
    """Extract available drivers from a race session"""
    if _session is None:
        return []
    
    try:
        drivers = _session.drivers
        driver_info = []
        
        for driver in drivers:
            driver_data = _session.get_driver(driver)
            driver_number = getattr(driver_data, 'DriverNumber', driver)  # Fallback to abbreviation if number not available
            driver_info.append({
                'abbreviation': driver,
                'driver_number': driver_number,
                'full_name': f"{driver_data['FirstName']} {driver_data['LastName']}",
                'team': driver_data['TeamName']
            })
        
        return sorted(driver_info, key=lambda x: x['full_name'])
    except Exception as e:
        st.error(f"Error extracting driver information: {str(e)}")
        return []

@st.cache_data
def get_lap_data(_session, drivers):
    """Get lap data for selected drivers"""
    if _session is None or not drivers:
        return pd.DataFrame()
    
    try:
        laps_data = []
        
        for driver in drivers:
            driver_laps = _session.laps.pick_drivers(driver)
            if not driver_laps.empty:
                # Add driver info to each lap
                driver_laps_copy = driver_laps.copy()
                driver_laps_copy['Driver'] = driver
                driver_laps_copy['DriverName'] = f"{_session.get_driver(driver)['FirstName']} {_session.get_driver(driver)['LastName']}"
                driver_laps_copy['Team'] = _session.get_driver(driver)['TeamName']
                laps_data.append(driver_laps_copy)
        
        if laps_data:
            combined_laps = pd.concat(laps_data, ignore_index=True)
            
            # Clean and prepare data
            combined_laps = combined_laps.dropna(subset=['LapTime'])
            combined_laps['LapTimeSeconds'] = combined_laps['LapTime'].dt.total_seconds()
            
            # Add additional useful columns
            combined_laps['IsPersonalBest'] = combined_laps.groupby('Driver')['LapTimeSeconds'].transform(lambda x: x == x.min())
            combined_laps['GapToFastest'] = combined_laps['LapTimeSeconds'] - combined_laps['LapTimeSeconds'].min()
            
            # Calculate tyre age for each driver
            def calculate_tyre_age(driver_data):
                driver_data = driver_data.copy()
                driver_data['TyreAge'] = 0
                current_age = 0
                previous_compound = None
                
                for idx, row in driver_data.iterrows():
                    if pd.isna(row['Compound']) or previous_compound != row['Compound']:
                        current_age = 1
                    else:
                        current_age += 1
                    
                    driver_data.at[idx, 'TyreAge'] = current_age
                    previous_compound = row['Compound']
                
                return driver_data
            
            # Apply tyre age calculation for each driver
            combined_laps = combined_laps.groupby('Driver', group_keys=False).apply(calculate_tyre_age)
            
            # Reset index to ensure clean DataFrame structure
            combined_laps = combined_laps.reset_index(drop=True)
            
            return combined_laps
        
    except Exception as e:
        st.error(f"Error processing lap data: {str(e)}")
    
    return pd.DataFrame()

@st.cache_data
def get_telemetry_data(_session, driver, lap_number):
    """Get telemetry data for a specific driver and lap"""
    if _session is None:
        return pd.DataFrame()
    
    try:
        driver_laps = _session.laps.pick_drivers(driver)
        if lap_number > len(driver_laps):
            return pd.DataFrame()
        
        lap = driver_laps.iloc[lap_number - 1]
        telemetry = lap.get_car_data()
        
        if not telemetry.empty:
            # Add useful calculated fields only if Distance column exists
            if 'Distance' in telemetry.columns:
                telemetry['DistanceKm'] = telemetry['Distance'] / 1000
            else:
                # If Distance is not available, create a synthetic distance based on time
                if 'Time' in telemetry.columns:
                    telemetry['DistanceKm'] = telemetry.index * 0.01  # Rough approximation
                else:
                    telemetry['DistanceKm'] = telemetry.index * 0.01
            return telemetry
        
    except Exception as e:
        st.error(f"Error loading telemetry data: {str(e)}")
    
    return pd.DataFrame()

@st.cache_data
def get_strategy_data(_session, drivers):
    """Get pit stop and tyre strategy data"""
    if _session is None or not drivers:
        return pd.DataFrame()
    
    try:
        strategy_data = []
        
        for driver in drivers:
            driver_laps = _session.laps.pick_drivers(driver)
            if not driver_laps.empty:
                # Get tyre compound information
                driver_laps_copy = driver_laps.copy()
                driver_laps_copy['Driver'] = driver
                driver_laps_copy['DriverName'] = f"{_session.get_driver(driver)['FirstName']} {_session.get_driver(driver)['LastName']}"
                
                # Calculate tyre age
                driver_laps_copy['TyreAge'] = 0
                current_age = 0
                previous_compound = None
                
                for idx, row in driver_laps_copy.iterrows():
                    if previous_compound != row['Compound']:
                        current_age = 1
                    else:
                        current_age += 1
                    
                    driver_laps_copy.at[idx, 'TyreAge'] = current_age
                    previous_compound = row['Compound']
                
                strategy_data.append(driver_laps_copy)
        
        if strategy_data:
            return pd.concat(strategy_data, ignore_index=True)
            
    except Exception as e:
        st.error(f"Error processing strategy data: {str(e)}")
    
    return pd.DataFrame()

@st.cache_data  
def get_race_results(_session):
    """Get final race results"""
    if _session is None:
        return pd.DataFrame()
    
    try:
        results = _session.results
        if not results.empty:
            # Add readable driver names
            for idx, row in results.iterrows():
                driver_info = _session.get_driver(row['Abbreviation'])
                results.at[idx, 'DriverName'] = f"{driver_info['FirstName']} {driver_info['LastName']}"
        
        return results
    except Exception as e:
        st.error(f"Error loading race results: {str(e)}")
        return pd.DataFrame()

def format_lap_time(seconds):
    """Convert lap time in seconds to MM:SS.mmm format"""
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:06.3f}"

def get_session_info(_session):
    """Extract key information about the race session"""
    if _session is None:
        return {}
    
    try:
        info = {
            'event_name': _session.event['EventName'],
            'location': _session.event['Location'],
            'country': _session.event['Country'], 
            'date': _session.event['EventDate'].strftime('%Y-%m-%d'),
            'circuit': _session.event['EventName'],
            'total_laps': len(_session.laps['LapNumber'].unique()) if not _session.laps.empty else 0,
            'weather': getattr(_session, 'weather_data', None)
        }
        return info
    except Exception as e:
        st.error(f"Error extracting session info: {str(e)}")
        return {}
