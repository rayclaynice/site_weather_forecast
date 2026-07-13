import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, html,dcc
from plotly.subplots import make_subplots




def build_correlation_figs(lat, lon):

    archive_url = "https://archive-api.open-meteo.com/v1/archive"
    archive_params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2021-07-01",
        "end_date": "2025-07-31",
        "daily": "rain_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "auto"
    }
    archive_response = requests.get(archive_url, params=archive_params, timeout=500)
    archive_data = archive_response.json()
    archive_df = pd.DataFrame(archive_data["daily"])
    archive_df["time"] = pd.to_datetime(archive_df["time"])
    archive_df["freeze_thaw"] = (archive_df["temperature_2m_min"] < 0) & (archive_df["temperature_2m_max"] > 0)




    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        "latitude": lon,
        "longitude": lat,
        "timezone": "auto",
        "hourly": (
            "rain,soil_moisture_0_1cm,"
            "soil_temperature_0cm,"
            "wind_gusts_10m,surface_pressure"
        ),
        "past_days": 30,
        "forecast_days": 16
    }
    forecast_response = requests.get(forecast_url, params=forecast_params, timeout=500)
    forecast_data = forecast_response.json()
    hourly_df = pd.DataFrame(forecast_data["hourly"])
    hourly_df["time"] = pd.to_datetime(hourly_df["time"])
    hourly_df["freeze_thaw"] = (hourly_df["soil_temperature_0cm"] < 0) & (hourly_df["soil_temperature_0cm"] > -5)






    fig_lag = go.Figure()

    fig_lag.add_trace(go.Bar(
        x=hourly_df["time"], 
        y=hourly_df.get("rain", 0),
        name="Rainfall",
        opacity=0.7,
        marker_color="#42a5f5",
        marker=dict(cornerradius=6)
    ))

    fig_lag.add_trace(go.Scatter(
        x=hourly_df["time"], 
        y=hourly_df["soil_moisture_0_1cm"],
        name="Soil Moisture 0-1cm (%)",
        line=dict(color="#1e88e5", width=3)
    ))

    fig_lag.update_layout(
        template="plotly_white",
        title="Soil Moisture Response to Rainfall (Lag Effect)",
        height=520,
        width=610,
        xaxis_title="Date",
        yaxis_title="Value",
        legend=dict(orientation="h", y=1.02, x=0.5),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )




    fig_storm = make_subplots(rows=2, cols=1, 
                        subplot_titles=("Wind Gusts (km/h)", "Surface Pressure (hPa)"),
                        vertical_spacing=0.12)

    # Wind Gusts
    fig_storm.add_trace(go.Scatter(
        x=hourly_df["time"], 
        y=hourly_df["wind_gusts_10m"],
        name="Wind Gusts",
        line=dict(color="#ef5350", width=2.5)
    ), row=1, col=1)

    # Pressure
    fig_storm.add_trace(go.Scatter(
        x=hourly_df["time"], 
        y=hourly_df["surface_pressure"],
        name="Surface Pressure",
        line=dict(color="#8e24aa", width=2.5)
    ), row=2, col=1)

    fig_storm.update_layout(
        template="plotly_white",
        height=700,
        width=610,
        title="Wind Gusts vs Surface Pressure Drop (Storm Early Warning)",
        showlegend=False,
        margin=dict(l=60, r=40, t=100, b=60),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False),
        yaxis2=dict(showgrid=False, zeroline=False)  
    )

    fig_storm.update_yaxes(title="Wind Gusts (km/h)", row=1, col=1)
    fig_storm.update_yaxes(title="Surface Pressure (hPa)", row=2, col=1)

    fig_storm.add_hline(y=45, line_dash="dash", line_color="red", row=1, col=1,
                annotation_text="High Risk >45 km/h")
    
    return fig_lag, fig_storm








"""
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Weather Dashboard",
            style={'textAlign': 'center', 'marginBottom': '40px'}),

    html.Div([
        html.Div([
            dcc.Graph(figure=fig_lag, style={'width': '100%'})
        ], style={'width': '48%'}),
    html.Div([
            dcc.Graph(figure=fig_storm, style={'width': '100%'})
        ], style={'width': '48%'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '20px'}),


])


"""