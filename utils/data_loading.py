import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
import logging
logging.getLogger('fastf1').setLevel(logging.ERROR)

def get_available_years():
    """Get list of available years for F1 data"""
    current_year = datetime.now().year
    return list(range(2018, current_year + 1))

def get_race_schedule(year):
    """Get race schedule for a given year"""
    try:
        schedule = ff1.get_event_schedule(year)
        races = schedule[schedule['EventFormat'] != 'testing'].copy()
        return races[['EventName', 'Location', 'Country', 'EventDate']].to_dict('records')
    except Exception as e:
        st.error(f"Error loading race schedule for {year}: {str(e)}")
        return []

def load_race_data(year, race_name):
    """Load race session data without caching"""
    try:
        with st.spinner(f"Loading {race_name} {year} race data..."):
            session = ff1.get_session(year, race_name, 'R')
            session.load()
            return session
    except Exception as e:
        st.error(f"Error loading race data: {str(e)}")
        return None

def get_driver_list(session):
    """Extract available drivers from a race session"""
    if session is None:
        return []
    
    try:
        drivers = session.drivers
        driver_info = []
        
        for driver in drivers:
            driver_data = session.get_driver(driver)
            driver_number = getattr(driver_data, 'DriverNumber', driver)
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

def get_lap_data(session, drivers):
    """Get lap data for selected drivers"""
    if session is None or not drivers:
        return pd.DataFrame()
    
    try:
        if isinstance(drivers[0], dict):
            driver_abbreviations = [d['abbreviation'] for d in drivers]
        else:
            driver_abbreviations = drivers
            
        laps = session.laps.pick_drivers(driver_abbreviations)
        
        if laps.empty:
            return pd.DataFrame()
        
        laps = laps.copy()
        laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
        laps['Position'] = laps['Position'].astype('Int64')
        
        def calculate_tyre_age(driver_laps):
            driver_laps = driver_laps.copy()
            driver_laps['TyreAge'] = 0
            current_compound = None
            stint_start = 0
            
            for idx, row in driver_laps.iterrows():
                if current_compound != row['Compound']:
                    current_compound = row['Compound']
                    stint_start = row['LapNumber']
                
                driver_laps.loc[idx, 'TyreAge'] = row['LapNumber'] - stint_start + 1
                    
            return driver_laps
        
        combined_laps = laps.groupby('Driver', group_keys=False).apply(calculate_tyre_age)
        
        return combined_laps.reset_index(drop=True)
    
    except Exception as e:
        st.error(f"Error processing lap data: {str(e)}")
        return pd.DataFrame()

def get_telemetry_data(session, drivers, lap_number=None):
    """Get telemetry data for selected drivers"""
    if session is None or not drivers:
        return pd.DataFrame()
    
    try:
        # Handle both dict format and string format for drivers
        if isinstance(drivers[0], dict):
            driver_abbreviations = [d['abbreviation'] for d in drivers]
        else:
            driver_abbreviations = drivers
            
        telemetry_data = []
        
        for driver in driver_abbreviations:
            try:
                if lap_number:
                    lap = session.laps.pick_driver(driver).pick_lap(lap_number)
                else:
                    lap = session.laps.pick_driver(driver).pick_fastest()
                
                if lap is not None and not lap.empty:
                    telemetry = lap.get_telemetry()
                    if not telemetry.empty:
                        telemetry['Driver'] = driver
                        telemetry['LapNumber'] = lap['LapNumber']
                        telemetry_data.append(telemetry)
            except Exception as driver_e:
                st.warning(f"Error processing telemetry for driver {driver}: {str(driver_e)}")
                continue
        
        if telemetry_data:
            return pd.concat(telemetry_data, ignore_index=True)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading telemetry data: {str(e)}")
        return pd.DataFrame()

def get_strategy_data(session, selected_drivers=None):
    """Get tyre strategy data for selected drivers"""
    if session is None:
        return pd.DataFrame()
    
    try:
        laps = session.laps
        if laps.empty:
            return pd.DataFrame()
        
        strategy_data = []
        
        if selected_drivers:
            driver_abbreviations = [d['abbreviation'] if isinstance(d, dict) else d for d in selected_drivers]
        else:
            driver_abbreviations = session.drivers
        
        for driver in driver_abbreviations:
            try:
                driver_laps = laps.pick_driver(driver)
                if driver_laps.empty:
                    continue
                    
                compounds = driver_laps['Compound'].dropna().unique()
                
                for compound in compounds:
                    compound_laps = driver_laps[driver_laps['Compound'] == compound]
                    if not compound_laps.empty:
                        start_lap = compound_laps['LapNumber'].min()
                        end_lap = compound_laps['LapNumber'].max()
                        stint_length = len(compound_laps)
                        
                        strategy_data.append({
                            'Driver': driver,
                            'Compound': compound,
                            'StartLap': start_lap,
                            'EndLap': end_lap,
                            'StintLength': stint_length
                        })
            except Exception as driver_e:
                st.warning(f"Error processing strategy data for driver {driver}: {str(driver_e)}")
                continue
        
        return pd.DataFrame(strategy_data)
        
    except Exception as e:
        st.error(f"Error processing strategy data: {str(e)}")
        return pd.DataFrame()

def get_race_results(session):
    """Get race results"""
    if session is None:
        return pd.DataFrame()
    
    try:
        results = session.results
        if results.empty:
            return pd.DataFrame()
        
        # Clean and format results
        results = results.copy()
        results['Position'] = results['Position'].astype('Int64')
        results['GridPosition'] = results['GridPosition'].astype('Int64')
        
        return results[['Position', 'Abbreviation', 'DriverNumber', 'BroadcastName', 
                       'TeamName', 'Time', 'Status', 'Points', 'GridPosition']]
        
    except Exception as e:
        st.error(f"Error loading race results: {str(e)}")
        return pd.DataFrame()

def get_session_info(session):
    """Get session information"""
    if session is None:
        return {}
    
    try:
        return {
            'event_name': session.event.EventName,
            'location': session.event.Location,
            'country': session.event.Country,
            'date': session.event.EventDate.strftime('%Y-%m-%d'),
            'session_type': session.name,
            'track_length': getattr(session.event, 'TrackLength', 'Unknown'),
            'total_laps': len(session.laps['LapNumber'].unique()) if not session.laps.empty else 0
        }
    except Exception as e:
        st.error(f"Error getting session info: {str(e)}")
        return {}

def format_lap_time(seconds):
    """Format lap time in seconds to MM:SS.mmm format"""
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    
    try:
        minutes = int(seconds // 60)
        seconds_remainder = seconds % 60
        return f"{minutes}:{seconds_remainder:06.3f}"
    except:
        return "N/A"
