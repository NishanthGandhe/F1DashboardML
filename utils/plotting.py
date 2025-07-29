"""
Plotting utilities for F1BeginnerProject
Creates interactive Plotly visualizations for F1 data analysis
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import streamlit as st

# F1 team colors for consistent visualization
TEAM_COLORS = {
    'Red Bull Racing': '#0600EF',
    'Mercedes': '#00D2BE', 
    'Ferrari': '#DC143C',
    'McLaren': '#FF8700',
    'Alpine': '#0090FF',
    'Aston Martin': '#006F62',
    'Williams': '#005AFF',
    'AlphaTauri': '#2B4562',
    'Alfa Romeo': '#900000',
    'Haas': '#FFFFFF'
}

# Tyre compound colors
TYRE_COLORS = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFF200', 
    'HARD': '#EBEBEB',
    'INTERMEDIATE': '#43B02A',
    'WET': '#0067AD'
}

def get_driver_color(team_name, driver_idx=0):
    """Get color for a driver based on team, with slight variations for teammates"""
    base_color = TEAM_COLORS.get(team_name, f'#{hash(team_name) % 0xFFFFFF:06x}')
    
    # For teammates, slightly modify the base color
    if driver_idx > 0:
        # Make second driver slightly darker/lighter
        if base_color.startswith('#'):
            hex_color = base_color[1:]
            rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            # Darken by 20%
            rgb = [max(0, int(c * 0.8)) for c in rgb]
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    return base_color

def plot_pace_comparison(lap_data, title="Lap Time Comparison"):
    """Create an interactive lap time comparison chart"""
    if lap_data.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    drivers = lap_data['Driver'].unique()
    team_driver_count = {}
    
    for driver in drivers:
        driver_laps = lap_data[lap_data['Driver'] == driver].copy()
        team = driver_laps['Team'].iloc[0]
        
        # Track how many drivers from this team we've seen
        driver_idx = team_driver_count.get(team, 0)
        team_driver_count[team] = driver_idx + 1
        
        color = get_driver_color(team, driver_idx)
        
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['LapTimeSeconds'],
            mode='lines+markers',
            name=f"{driver}",  # Fixed: Use driver abbreviation only
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>" +
                "Lap: %{x}<br>" +
                "Time: %{customdata[0]}<br>" +
                "Compound: %{customdata[1]}<br>" +
                "Tyre Age: %{customdata[2]}<br>" +
                "<extra></extra>"
            ),
            customdata=np.column_stack((
                driver_laps.apply(lambda row: f"{int(row['LapTimeSeconds']//60)}:{row['LapTimeSeconds']%60:06.3f}", axis=1),
                driver_laps['Compound'],
                driver_laps['TyreAge'] if 'TyreAge' in driver_laps.columns else ['N/A'] * len(driver_laps)
            ))
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode='closest',
        showlegend=True,
        height=600,
        template='plotly_white'
    )
    
    return fig

def plot_tyre_strategy(strategy_data, title="Tyre Strategy Comparison"):
    """Create a visualization of tyre strategies"""
    if strategy_data.empty:
        return go.Figure()
    
    # Debug: Check what columns are available
    print(f"Strategy data columns: {strategy_data.columns.tolist()}")
    
    # Check for required columns
    required_columns = ['Driver', 'Compound']
    lap_column = None
    
    # Find the lap number column (could be 'LapNumber' or 'Lap')
    if 'LapNumber' in strategy_data.columns:
        lap_column = 'LapNumber'
    elif 'Lap' in strategy_data.columns:
        lap_column = 'Lap'
    else:
        st.error("No lap number column found in strategy data")
        return go.Figure()
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in strategy_data.columns]
    if missing_columns:
        st.error(f"Missing columns in strategy data: {missing_columns}")
        return go.Figure()
    
    fig = go.Figure()
    
    drivers = strategy_data['Driver'].unique()
    y_positions = list(range(len(drivers)))
    
    for idx, driver in enumerate(drivers):
        driver_laps = strategy_data[strategy_data['Driver'] == driver].copy()
        
        if driver_laps.empty:
            continue
        
        # Group consecutive laps with same compound
        stints = []
        current_stint = {
            'compound': driver_laps.iloc[0]['Compound'],
            'start_lap': driver_laps.iloc[0][lap_column],  # Use the found lap column
            'end_lap': driver_laps.iloc[0][lap_column]
        }
        
        for _, lap in driver_laps.iterrows():
            if lap['Compound'] == current_stint['compound']:
                current_stint['end_lap'] = lap[lap_column]
            else:
                stints.append(current_stint.copy())
                current_stint = {
                    'compound': lap['Compound'],
                    'start_lap': lap[lap_column],
                    'end_lap': lap[lap_column]
                }
        stints.append(current_stint)
        
        # Plot each stint
        for stint in stints:
            fig.add_trace(go.Scatter(
                x=[stint['start_lap'], stint['end_lap']],
                y=[idx, idx],
                mode='lines',
                line=dict(
                    color=TYRE_COLORS.get(stint['compound'], '#808080'),
                    width=20
                ),
                name=f"{driver} - {stint['compound']}",
                showlegend=False,
                hovertemplate=(
                    f"<b>{driver}</b><br>" +
                    f"Compound: {stint['compound']}<br>" +
                    f"Laps: {stint['start_lap']}-{stint['end_lap']}<br>" +
                    f"Stint Length: {stint['end_lap'] - stint['start_lap'] + 1} laps<br>" +
                    "<extra></extra>"
                )
            ))
    
    # Add legend for compounds
    for compound, color in TYRE_COLORS.items():
        if compound in strategy_data['Compound'].values:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color=color, width=10),
                name=compound,
                showlegend=True
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Lap Number",
        yaxis=dict(
            tickmode='array',
            tickvals=y_positions,
            ticktext=[driver for driver in drivers],
            title="Driver"
        ),
        height=max(400, len(drivers) * 60),
        template='plotly_white',
        hovermode='closest'
    )
    
    return fig

def plot_telemetry_comparison(telemetry_data_dict, lap_number, title="Telemetry Comparison"):
    """Create telemetry comparison plots for multiple drivers"""
    if not telemetry_data_dict:
        return go.Figure()
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Speed (km/h)', 'Throttle (%)', 'Brake', 'Gear'),
        specs=[[{"secondary_y": False}] for _ in range(4)]
    )
    
    colors = px.colors.qualitative.Set1
    
    for idx, (driver, telemetry) in enumerate(telemetry_data_dict.items()):
        if telemetry.empty:
            continue
            
        color = colors[idx % len(colors)]
        
        # Speed
        fig.add_trace(
            go.Scatter(
                x=telemetry['DistanceKm'],
                y=telemetry['Speed'],
                name=f"{driver} Speed",
                line=dict(color=color),
                legendgroup=driver,
            ),
            row=1, col=1
        )
        
        # Throttle
        fig.add_trace(
            go.Scatter(
                x=telemetry['DistanceKm'],
                y=telemetry['Throttle'],
                name=f"{driver} Throttle",
                line=dict(color=color),
                legendgroup=driver,
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Brake
        fig.add_trace(
            go.Scatter(
                x=telemetry['DistanceKm'],
                y=telemetry['Brake'],
                name=f"{driver} Brake",
                line=dict(color=color),
                legendgroup=driver,
                showlegend=False
            ),
            row=3, col=1
        )
        
        # Gear
        fig.add_trace(
            go.Scatter(
                x=telemetry['DistanceKm'],
                y=telemetry['nGear'],
                name=f"{driver} Gear",
                line=dict(color=color),
                legendgroup=driver,
                showlegend=False
            ),
            row=4, col=1
        )
    
    fig.update_layout(
        title=f"{title} - Lap {lap_number}",
        height=800,
        template='plotly_white',
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Distance (km)", row=4, col=1)
    
    return fig

def plot_position_changes(lap_data, title="Position Changes Throughout Race"):
    """Plot how driver positions change throughout the race"""
    if lap_data.empty or 'Position' not in lap_data.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    drivers = lap_data['Driver'].unique()
    team_driver_count = {}
    
    for driver in drivers:
        driver_laps = lap_data[lap_data['Driver'] == driver].copy()
        if driver_laps.empty:
            continue
            
        team = driver_laps['Team'].iloc[0]
        driver_idx = team_driver_count.get(team, 0)
        team_driver_count[team] = driver_idx + 1
        
        color = get_driver_color(team, driver_idx)
        
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['Position'],
            mode='lines+markers',
            name=f"{driver}",  # Fixed: Use driver abbreviation only
            line=dict(color=color, width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Lap Number",
        yaxis_title="Position",
        yaxis=dict(autorange="reversed"),  # Position 1 at top
        hovermode='closest',
        showlegend=True,
        height=600,
        template='plotly_white'
    )
    
    return fig

def plot_gap_analysis(lap_data, reference_driver=None, title="Gap to Leader Analysis"):
    """Plot gap to leader or reference driver"""
    if lap_data.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # If no reference driver specified, use the race leader
    if reference_driver is None:
        # Find who was leading most laps
        if 'Position' in lap_data.columns:
            leader_counts = lap_data[lap_data['Position'] == 1]['Driver'].value_counts()
            reference_driver = leader_counts.index[0] if not leader_counts.empty else lap_data['Driver'].iloc[0]
    
    drivers = lap_data['Driver'].unique()
    team_driver_count = {}
    
    for driver in drivers:
        if driver == reference_driver:
            continue
            
        driver_laps = lap_data[lap_data['Driver'] == driver].copy()
        ref_laps = lap_data[lap_data['Driver'] == reference_driver].copy()
        
        # Calculate gap for each lap
        gaps = []
        lap_numbers = []
        
        for lap_num in driver_laps['LapNumber'].unique():
            driver_lap = driver_laps[driver_laps['LapNumber'] == lap_num]
            ref_lap = ref_laps[ref_laps['LapNumber'] == lap_num]
            
            if not driver_lap.empty and not ref_lap.empty:
                gap = driver_lap['LapTimeSeconds'].iloc[0] - ref_lap['LapTimeSeconds'].iloc[0]
                gaps.append(gap)
                lap_numbers.append(lap_num)
        
        if gaps:
            team = driver_laps['Team'].iloc[0]
            driver_idx = team_driver_count.get(team, 0)
            team_driver_count[team] = driver_idx + 1
            
            color = get_driver_color(team, driver_idx)
            
            fig.add_trace(go.Scatter(
                x=lap_numbers,
                y=gaps,
                mode='lines+markers',
                name=f"{driver}",  # Fixed: Use driver abbreviation only
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))
    
    # Add reference line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                  annotation_text=f"Reference: {reference_driver}")
    
    fig.update_layout(
        title=title,
        xaxis_title="Lap Number", 
        yaxis_title="Gap (seconds)",
        hovermode='closest',
        showlegend=True,
        height=600,
        template='plotly_white'
    )
    
    return fig

def create_summary_metrics(lap_data, session_info):
    """Create summary metrics for race analysis using available FastF1 columns"""
    
    try:
        if lap_data.empty:
            return {}
        
        metrics = {}
        
        # Get fastest lap
        fastest_lap_idx = lap_data['LapTimeSeconds'].idxmin()
        fastest_lap = lap_data.loc[fastest_lap_idx]
        
        # Use available driver information - FastF1 uses 'Driver' not 'DriverName'
        driver_code = 'Unknown'
        if 'Driver' in fastest_lap.index:
            driver_code = fastest_lap['Driver']
        elif 'Abbreviation' in fastest_lap.index:
            driver_code = fastest_lap['Abbreviation']
        
        metrics['fastest_lap'] = {
            'driver': driver_code,
            'time': f"{int(fastest_lap['LapTimeSeconds']//60)}:{fastest_lap['LapTimeSeconds']%60:06.3f}",
            'lap': int(fastest_lap['LapNumber']) if 'LapNumber' in fastest_lap.index else 'N/A'
        }
        
        # Calculate average lap times per driver
        if 'Driver' in lap_data.columns:
            avg_times = lap_data.groupby('Driver')['LapTimeSeconds'].mean()
            if not avg_times.empty:
                fastest_avg_driver = avg_times.idxmin()
                fastest_avg_time = avg_times.min()
                
                metrics['fastest_average'] = {
                    'driver': fastest_avg_driver,
                    'time': f"{int(fastest_avg_time//60)}:{fastest_avg_time%60:06.3f}"
                }
        
        # Calculate consistency (standard deviation)
        if 'Driver' in lap_data.columns:
            std_times = lap_data.groupby('Driver')['LapTimeSeconds'].std()
            if not std_times.empty:
                most_consistent_driver = std_times.idxmin()
                consistency_value = std_times.min()
                
                metrics['most_consistent'] = {
                    'driver': most_consistent_driver,
                    'std_dev': f"{consistency_value:.3f}s"
                }
        
        # Race information
        if session_info:
            metrics['race_info'] = {
                'total_laps': session_info.get('total_laps', 'N/A'),
                'event_name': session_info.get('event_name', 'Unknown'),
                'date': session_info.get('date', 'Unknown')
            }
        
        return metrics
        
    except Exception as e:
        # Import here to avoid circular imports
        import streamlit as st
        st.error(f"Error creating summary metrics: {str(e)}")
        return {}