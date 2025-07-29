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
import matplotlib.pyplot as plt
import matplotlib as mpl

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
    
    if driver_idx > 0:
        if base_color.startswith('#'):
            hex_color = base_color[1:]
            rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            rgb = [max(0, int(c * 0.8)) for c in rgb]
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    return base_color

def plot_pace_comparison(lap_data, title="Lap Time Comparison"):
    """Create an interactive lap time comparison chart"""
    if lap_data.empty:
        return go.Figure()
    
    valid_lap_data = lap_data.dropna(subset=['LapTimeSeconds']).copy()
    
    if valid_lap_data.empty:
        st.warning("No valid lap time data available for pace comparison")
        return go.Figure()
    
    fig = go.Figure()
    
    drivers = valid_lap_data['Driver'].unique()
    team_driver_count = {}
    
    def format_lap_time_safe(seconds):
        """Safely format lap time, handling NaN values"""
        try:
            if pd.isna(seconds) or seconds <= 0:
                return "N/A"
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}:{remaining_seconds:06.3f}"
        except (ValueError, TypeError):
            return "N/A"
    
    for driver in drivers:
        driver_laps = valid_lap_data[valid_lap_data['Driver'] == driver].copy()
        
        driver_laps = driver_laps.dropna(subset=['LapTimeSeconds'])
        
        if driver_laps.empty:
            continue  
            
        team = driver_laps['Team'].iloc[0] if 'Team' in driver_laps.columns else 'Unknown'
        
        driver_idx = team_driver_count.get(team, 0)
        team_driver_count[team] = driver_idx + 1
        
        color = get_driver_color(team, driver_idx)
        
        formatted_times = []
        compounds = []
        tyre_ages = []
        
        for _, row in driver_laps.iterrows():
            formatted_times.append(format_lap_time_safe(row['LapTimeSeconds']))
            
            compounds.append(row.get('Compound', 'Unknown'))
            
            if 'TyreAge' in driver_laps.columns:
                tyre_age = row.get('TyreAge', 'N/A')
                tyre_ages.append(str(tyre_age) if pd.notna(tyre_age) else 'N/A')
            else:
                tyre_ages.append('N/A')
        
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['LapTimeSeconds'],
            mode='lines+markers',
            name=f"{driver}", 
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
                formatted_times,
                compounds,
                tyre_ages
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
    
    required_columns = ['Driver', 'Compound']
    
    if 'StartLap' not in strategy_data.columns or 'EndLap' not in strategy_data.columns:
        st.error("StartLap and EndLap columns not found in strategy data")
        return go.Figure()
    
    missing_columns = [col for col in required_columns if col not in strategy_data.columns]
    if missing_columns:
        st.error(f"Missing columns in strategy data: {missing_columns}")
        return go.Figure()
    
    fig = go.Figure()
    
    drivers = strategy_data['Driver'].unique()
    y_positions = list(range(len(drivers)))
    
    for idx, driver in enumerate(drivers):
        driver_stints = strategy_data[strategy_data['Driver'] == driver].copy()
        
        if driver_stints.empty:
            continue
        
        for _, stint in driver_stints.iterrows():
            fig.add_trace(go.Scatter(
                x=[stint['StartLap'], stint['EndLap']],
                y=[idx, idx],
                mode='lines',
                line=dict(
                    color=TYRE_COLORS.get(stint['Compound'], '#808080'),
                    width=20
                ),
                name=f"{driver} - {stint['Compound']}",
                showlegend=False,
                hovertemplate=(
                    f"<b>{driver}</b><br>" +
                    f"Compound: {stint['Compound']}<br>" +
                    f"Laps: {stint['StartLap']}-{stint['EndLap']}<br>" +
                    f"Stint Length: {stint.get('StintLength', stint['EndLap'] - stint['StartLap'] + 1)} laps<br>" +
                    "<extra></extra>"
                )
            ))
    
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
    
    for driver, telemetry in telemetry_data_dict.items():
        print(f"Telemetry columns for {driver}: {telemetry.columns.tolist()}")
        break 
    
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
        
        distance_col = None
        if 'Distance' in telemetry.columns:
            distance_col = 'Distance'
            distance_data = telemetry['Distance'] / 1000 
        elif 'DistanceKm' in telemetry.columns:
            distance_col = 'DistanceKm'
            distance_data = telemetry['DistanceKm']
        else:
            distance_data = pd.Series(range(len(telemetry))) * 0.01 
            st.warning(f"No distance column found for {driver}, using approximation")
        
        required_cols = ['Speed', 'Throttle', 'Brake', 'nGear']
        missing_cols = [col for col in required_cols if col not in telemetry.columns]
        
        if missing_cols:
            st.warning(f"Missing telemetry columns for {driver}: {missing_cols}")
            continue
        
        fig.add_trace(
            go.Scatter(
                x=distance_data,
                y=telemetry['Speed'],
                name=f"{driver} Speed",
                line=dict(color=color),
                legendgroup=driver,
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=distance_data,
                y=telemetry['Throttle'],
                name=f"{driver} Throttle",
                line=dict(color=color),
                legendgroup=driver,
                showlegend=False
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=distance_data,
                y=telemetry['Brake'],
                name=f"{driver} Brake",
                line=dict(color=color),
                legendgroup=driver,
                showlegend=False
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=distance_data,
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
            name=f"{driver}", 
            line=dict(color=color, width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Lap Number",
        yaxis_title="Position",
        yaxis=dict(autorange="reversed"),  
        hovermode='closest',
        showlegend=True,
        height=600,
        template='plotly_white'
    )
    
    return fig

def plot_gap_analysis(lap_data, reference_driver=None, title="Gap to Leader Analysis"):
    """Plot gap to leader or reference driver"""
    if lap_data.empty:
        st.warning("No lap data available for gap analysis")
        return go.Figure()
        
    required_columns = ['Driver', 'LapNumber']
    missing_columns = [col for col in required_columns if col not in lap_data.columns]
    
    if missing_columns:
        st.warning(f"Gap analysis requires columns: {missing_columns}")
        return go.Figure()
    
    time_col = None
    if 'LapTimeSeconds' in lap_data.columns:
        time_col = 'LapTimeSeconds'
    elif 'LapTime' in lap_data.columns:
        time_col = 'LapTime'
        if lap_data[time_col].dtype == 'object':
            try:
                lap_data = lap_data.copy()
                lap_data['LapTimeSeconds'] = lap_data[time_col].apply(
                    lambda x: x.total_seconds() if hasattr(x, 'total_seconds') else float(x)
                )
                time_col = 'LapTimeSeconds'
            except:
                st.warning("Could not convert lap times to seconds")
                return go.Figure()
    else:
        st.warning("No lap time column found for gap analysis")
        return go.Figure()
    
    fig = go.Figure()
    
    available_drivers = lap_data['Driver'].unique()
    
    if reference_driver is None or reference_driver not in available_drivers:
        if 'Position' in lap_data.columns:
            valid_positions = lap_data.dropna(subset=['Position'])
            if not valid_positions.empty:
                leader_counts = valid_positions[valid_positions['Position'] == 1]['Driver'].value_counts()
                reference_driver = leader_counts.index[0] if not leader_counts.empty else available_drivers[0]
            else:
                avg_times = lap_data.groupby('Driver')[time_col].mean()
                reference_driver = avg_times.idxmin()
        else:
            avg_times = lap_data.groupby('Driver')[time_col].mean()
            reference_driver = avg_times.idxmin()
        
        if reference_driver not in available_drivers:
            reference_driver = available_drivers[0]
        
        st.info(f"Reference driver adjusted to: {reference_driver} (available in data)")
    
    if len(available_drivers) > 10:
        st.info(f"Using reference driver: {reference_driver}")
    
    team_driver_count = {}
    drivers_plotted = 0
    
    for driver in available_drivers:
        if driver == reference_driver:
            continue
            
        driver_laps = lap_data[lap_data['Driver'] == driver].copy()
        ref_laps = lap_data[lap_data['Driver'] == reference_driver].copy()
        
        if driver_laps.empty or ref_laps.empty:
            continue
        
        gaps = []
        lap_numbers = []
        cumulative_gap = 0
        
        for lap_num in sorted(driver_laps['LapNumber'].unique()):
            driver_lap = driver_laps[driver_laps['LapNumber'] == lap_num]
            ref_lap = ref_laps[ref_laps['LapNumber'] == lap_num]
            
            if not driver_lap.empty and not ref_lap.empty:
                lap_gap = driver_lap[time_col].iloc[0] - ref_lap[time_col].iloc[0]
                cumulative_gap += lap_gap
                gaps.append(cumulative_gap)
                lap_numbers.append(lap_num)
        
        if gaps and len(gaps) > 1: 
            team = driver_laps['Team'].iloc[0] if 'Team' in driver_laps.columns else 'Unknown'
            driver_idx = team_driver_count.get(team, 0)
            team_driver_count[team] = driver_idx + 1
            
            color = get_driver_color(team, driver_idx)
            
            fig.add_trace(go.Scatter(
                x=lap_numbers,
                y=gaps,
                mode='lines+markers',
                name=f"{driver}",
                line=dict(color=color, width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{driver}</b><br>Lap: %{{x}}<br>Gap: %{{y:.2f}}s<extra></extra>"
            ))
            drivers_plotted += 1
    
    if drivers_plotted > 0:
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                      annotation_text=f"Reference: {reference_driver}")
        
        fig.update_layout(
            title=title,
            xaxis_title="Lap Number", 
            yaxis_title="Cumulative Gap (seconds)",
            hovermode='closest',
            showlegend=True,
            height=600,
            template='plotly_white'
        )
    else:
        st.warning(f"No valid gap data found for comparison with {reference_driver}")
        fig.add_annotation(
            text=f"No gap data available<br>Reference driver: {reference_driver}<br>Available drivers: {available_drivers.tolist()}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title=title,
            xaxis_title="Lap Number", 
            yaxis_title="Cumulative Gap (seconds)",
            height=400,
            template='plotly_white'
        )
    
    return fig

def create_summary_metrics(lap_data, session_info):
    """Create summary metrics for race analysis using available FastF1 columns"""
    
    try:
        if lap_data.empty:
            return {}
        
        if 'LapTimeSeconds' not in lap_data.columns:
            st.error("LapTimeSeconds column not found in lap data")
            return {}
        
        valid_laps = lap_data.dropna(subset=['LapTimeSeconds'])
        
        if valid_laps.empty:
            st.warning("No valid lap times found for summary metrics")
            return {}
        
        metrics = {}
        
        fastest_lap_idx = valid_laps['LapTimeSeconds'].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        
        driver_code = 'Unknown'
        if 'Driver' in fastest_lap.index:
            driver_code = fastest_lap['Driver']
        elif 'Abbreviation' in fastest_lap.index:
            driver_code = fastest_lap['Abbreviation']
        
        lap_number = 'N/A'
        if 'LapNumber' in fastest_lap.index:
            lap_number = int(fastest_lap['LapNumber'])
        elif 'Lap' in fastest_lap.index:
            lap_number = int(fastest_lap['Lap'])
        
        def format_time_safe(seconds):
            """Safely format time handling NaN"""
            if pd.isna(seconds):
                return "N/A"
            try:
                return f"{int(seconds//60)}:{seconds%60:06.3f}"
            except (ValueError, TypeError):
                return "N/A"
        
        metrics['fastest_lap'] = {
            'driver': driver_code,
            'time': format_time_safe(fastest_lap['LapTimeSeconds']),
            'lap': lap_number
        }
        
        if 'Driver' in valid_laps.columns:
            avg_times = valid_laps.groupby('Driver')['LapTimeSeconds'].mean()
            if not avg_times.empty:
                fastest_avg_driver = avg_times.idxmin()
                fastest_avg_time = avg_times.min()
                
                metrics['fastest_average'] = {
                    'driver': fastest_avg_driver,
                    'time': format_time_safe(fastest_avg_time)
                }
        
        if 'Driver' in valid_laps.columns:
            std_times = valid_laps.groupby('Driver')['LapTimeSeconds'].std()
            if not std_times.empty:
                most_consistent_driver = std_times.idxmin()
                consistency_value = std_times.min()
                
                metrics['most_consistent'] = {
                    'driver': most_consistent_driver,
                    'std_dev': f"{consistency_value:.3f}s" if not pd.isna(consistency_value) else "N/A"
                }
        
        if session_info:
            metrics['race_info'] = {
                'total_laps': session_info.get('total_laps', 'N/A'),
                'event_name': session_info.get('event_name', 'Unknown'),
                'date': session_info.get('date', 'Unknown')
            }
        
        return metrics
        
    except Exception as e:
        import streamlit as st
        st.error(f"Error creating summary metrics: {str(e)}")
        print(f"Error in create_summary_metrics: {str(e)}")
        return {}

def plot_track_speed_map(session, driver, title="Track Speed Map"):
    """
    Create a track speed visualization showing speed variations around the circuit
    
    Args:
        session: FastF1 session object
        driver: Driver abbreviation (e.g., 'HAM', 'VER')
        title: Chart title
        
    Returns:
        matplotlib figure object for Streamlit display
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        from matplotlib.collections import LineCollection
        
        driver_laps = session.laps.pick_drivers(driver)
        if driver_laps.empty:
            st.warning(f"No lap data available for driver {driver}")
            return None
            
        fastest_lap = driver_laps.pick_fastest()
        if fastest_lap.empty:
            st.warning(f"No fastest lap found for driver {driver}")
            return None
        
        telemetry = fastest_lap.get_telemetry()
        if telemetry.empty:
            st.warning(f"No telemetry data available for driver {driver}")
            return None
        
        required_cols = ['X', 'Y', 'Speed']
        missing_cols = [col for col in required_cols if col not in telemetry.columns]
        if missing_cols:
            st.warning(f"Missing telemetry columns: {missing_cols}")
            return None
        
        x = telemetry['X'].values
        y = telemetry['Y'].values  
        speed = telemetry['Speed'].values
        
        valid_indices = ~(np.isnan(x) | np.isnan(y) | np.isnan(speed))
        x = x[valid_indices]
        y = y[valid_indices]
        speed = speed[valid_indices]
        
        if len(x) < 2:
            st.warning(f"Insufficient valid telemetry points for driver {driver}")
            return None
        
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        fig.suptitle(title, size=16, weight='bold')
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        ax.plot(x, y, color='black', linestyle='-', linewidth=8, zorder=0, alpha=0.3)
        
        colormap = plt.cm.plasma
        norm = plt.Normalize(speed.min(), speed.max())
        
        lc = LineCollection(segments[:-1], cmap=colormap, norm=norm,
                           linestyle='-', linewidth=4, alpha=0.8)
        lc.set_array(speed[:-1]) 
        
        line = ax.add_collection(lc)
        
        cbar = plt.colorbar(line, ax=ax, orientation='horizontal', 
                           pad=0.1, shrink=0.8, aspect=40)
        cbar.set_label('Speed (km/h)', fontsize=12, weight='bold')
        cbar.ax.tick_params(labelsize=10)
        
        ax.text(0.02, 0.98, f'Driver: {driver}', transform=ax.transAxes,
                fontsize=12, weight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.text(0.02, 0.92, f'Max Speed: {speed.max():.1f} km/h', transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.text(0.02, 0.86, f'Min Speed: {speed.min():.1f} km/h', transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.text(0.02, 0.80, f'Avg Speed: {speed.mean():.1f} km/h', transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating track speed map: {str(e)}")
        print(f"Error in plot_track_speed_map: {str(e)}")
        return None