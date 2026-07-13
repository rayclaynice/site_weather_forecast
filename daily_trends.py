import requests
from retry_requests import retry
import pandas as pd
import json
import datetime
import plotly.express as px
from dash import Dash, html,dcc




def build_precip_fig(lat, lon):
    today =pd.Timestamp.now().normalize()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "daily":("rain_sum",
                    "showers_sum",
                    "snowfall_sum",
                    "precipitation_sum",
                    ),
            "past_days": 30, 
            "forecast_days":16

            }

    response = requests.get(url, params=params, timeout=500)

    data = response.json()
    result = json.dumps(data, indent=2)
    cleaned_data = pd.DataFrame(data["daily"])

    fig_precip = px.bar(
        cleaned_data,
        x="time",
        y=["rain_sum", "showers_sum", "snowfall_sum"],
        title="Daily Rain, Showers & Snowfall (mm) | Past 30 + Next 16 Days",
        labels={"time": "Date", "value": "mm"}, 
        color_discrete_sequence=["#1565c0", "#42a5f5", "#81d4fa"],
        barmode="group"   
    )

    fig_precip.update_traces(
        marker_line_color="rgba(255,255,255,0.6)",
        marker_line_width=0.9,
        marker=dict(cornerradius=10)  
    )

    fig_precip.data[0].name = "Rain"
    fig_precip.data[1].name = "Showers"
    fig_precip.data[2].name = "Snowfall"

    fig_precip.update_layout(
        template="plotly_white",
        height=550,
        width=1220,
        xaxis_title="Date",
        yaxis_title="Amount (mm)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=13)
        ),
        margin=dict(l=60, r=40, t=100, b=60),
        xaxis=dict(tickformat="%b %d", showgrid=False),
        yaxis=dict(
            showgrid=False,   
            zeroline=False
        ),
        bargap=0.2,
        bargroupgap=0.15
    )

    return fig_precip

"""
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Weather Dashboard",
            style={'textAlign': 'center', 'marginBottom': '40px'}),

    html.Div([
        html.Div([
            dcc.Graph(figure=fig_precip, style={'width': '100%'})
        ], style={'width': '48%'}),

])
])
"""

