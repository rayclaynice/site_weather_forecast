import requests
from retry_requests import retry
import pandas as pd
import json
import datetime
import plotly.express as px
from dash import Dash, html,dcc





def build_wind_block_figs(lat, lon):
    today =pd.Timestamp.now().normalize()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "hourly":("wind_speed_10m",
                    "wind_speed_80m",
                    "wind_speed_120m",
                    "wind_speed_180m",
                    "wind_direction_10m",
                    "wind_direction_80m",
                    "wind_direction_120m",
                    "wind_direction_180m",
                    "wind_gusts_10m",
                    "surface_pressure",
                    "cloud_cover",
                    "visibility"

                    ),
            "past_days": 3, 
            "forecast_days":7

            }

    response = requests.get(url, params=params, timeout=500)

    data = response.json()
    result = json.dumps(data, indent=2)
    cleaned_data = pd.DataFrame(data["hourly"])
    cleaned_data["time"] = pd.to_datetime(cleaned_data["time"])


    wind_speed_cols = ["wind_speed_10m", "wind_speed_80m", "wind_speed_120m", "wind_speed_180m"]

    fig_wind = px.line(
        cleaned_data,
        x="time",
        y=wind_speed_cols,
        title="Wind Speed at Different Heights (km/h) | Past 3 + Next 7 Days",
        labels={"time": "Date", "value": "Wind Speed (km/h)"},
        color_discrete_sequence=["#1e88e5", "#42a5f5", "#81d4fa", "#b3e5fc"],
        render_mode="svg"
    )

    fig_wind.update_traces(line=dict(width=2.5, shape="spline"))

    # Clean names
    height_names = {
        "wind_speed_10m": "10 m (Surface)",
        "wind_speed_80m": "80 m",
        "wind_speed_120m": "120 m",
        "wind_speed_180m": "180 m"
    }
    fig_wind.add_annotation(
        text="Wind speed usually increases with height",
        xref="paper", yref="paper",
        x=0.02, y=0.95,
        showarrow=False,
        font=dict(size=13, color="#d32f2f")
    )
    for trace in fig_wind.data:
        trace.name = height_names.get(trace.name, trace.name)

    fig_wind.update_layout(
        template="plotly_white",
        height=520,
        width=610,
        legend_title="Height",
        hovermode="x unified"
    )

    #win gust

    fig_gusts = px.bar(
        cleaned_data,
        x="time",
        y="wind_gusts_10m",
        title="Wind Gusts at 10m (km/h) | Past 3 + Next 7 Days",
        labels={"time": "Date", "wind_gusts_10m": "Wind Gust Speed (km/h)"},
        color_discrete_sequence=["#ef5350"]  
    )

    fig_gusts.update_traces(
        marker_line_color="white",
        marker_line_width=0.4,
        marker=dict(cornerradius=8)
    )

    fig_gusts.update_layout(
        template="plotly_white",
        height=480,
        width=610,
        xaxis_title="Date",
        yaxis_title="Wind Gust Speed (km/h)",
        margin=dict(l=60, r=40, t=90, b=60),
        xaxis=dict(tickformat="%b %d", showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )


    fig_gusts.add_hline(
        y=40, 
        line_dash="dash", 
        line_color="#d32f2f", 
        annotation_text="High Risk (40 km/h)",
        annotation_position="top right"
    )

    #surface pressure
    fig_pressure = px.line(
        cleaned_data,
        x="time",
        y="surface_pressure",
        title="Surface Atmospheric Pressure",
        labels={"time": "Date", "surface_pressure": "Pressure (hPa)"},
        color_discrete_sequence=["#7b1fa2"],
        render_mode="svg"
    )

    fig_pressure.update_traces(
        line=dict(width=3, shape="spline")
    )

    fig_pressure.update_layout(
        template="plotly_white",
        height=460,
        width=610,
        xaxis_title="",
        yaxis_title="Pressure (hPa)",
        margin=dict(l=70, r=40, t=80, b=60),
        title_font_size=20
    )



    #cloud cover

    fig_cloud = px.bar(
        cleaned_data,
        x="time",
        y="cloud_cover",
        title="Cloud Cover",
        labels={"time": "Date", "cloud_cover": "Cloud Cover (%)"},
        color_discrete_sequence=["#546e7a"]
    )

    fig_cloud.update_traces(
        marker=dict(cornerradius=10, line=dict(width=0.5, color="white"))
    )

    fig_cloud.update_layout(
        template="plotly_white",
        height=460,
        width=610,
        xaxis_title="",
        yaxis_title="Cloud Cover (%)",
        title_font_size=20
    )



    #visibility
    fig_visibility = px.line(
        cleaned_data,
        x="time",
        y="visibility",
        title="Visibility",
        labels={"time": "Date", "visibility": "Visibility (km)"},
        color_discrete_sequence=["#00897b"],
        render_mode="svg"
    )

    fig_visibility.update_traces(line=dict(width=3, shape="spline"))

    fig_visibility.update_layout(
        template="plotly_white",
        height=460,
        width=610,
        xaxis_title="Date",
        yaxis_title="Visibility (km)",
        title_font_size=20
    )

    # Add low visibility warning line
    fig_visibility.add_hline(y=5000, line_dash="dash", line_color="#f57c00",
                            annotation_text="Low Visibility (<5km)", annotation_position="bottom right")


    return fig_cloud, fig_gusts, fig_pressure, fig_visibility, fig_wind







