import requests
from retry_requests import retry
import pandas as pd
import json
import plotly.express as px






def build_uv_fig(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "daily":("uv_index_max",
                    "uv_index_clear_sky_max"

                    ),
            "past_days": 7, 
            "forecast_days":10

            }

    response = requests.get(url, params=params, timeout=500)

    data = response.json()
    result = json.dumps(data, indent=2)
    cleaned_data = pd.DataFrame(data["daily"])
    cleaned_data["time"] = pd.to_datetime(cleaned_data["time"])


    fig_uv = px.bar(
        cleaned_data,
        x="time",
        y=["uv_index_max", "uv_index_clear_sky_max"],
        title="Daily Maximum UV Index | Past 7 + Next 10 Days",
        labels={"time": "Date", "value": "UV Index"},
        color_discrete_sequence=["#f57c00", "#ffb300"], 
        barmode="group"
    )

    fig_uv.update_traces(
        marker_line_color="white",
        marker_line_width=0.5,
        marker=dict(cornerradius=8)
    )

    fig_uv.data[0].name = "Actual Max UV Index"
    fig_uv.data[1].name = "Clear Sky Max UV Index"


    fig_uv.update_layout(
        template="plotly_white",
        height=520,
        width=610,
        xaxis_title="Date",
        yaxis_title="UV Index",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=40, t=100, b=60),
        xaxis=dict(tickformat="%b %d", showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False),
        bargap=0.2,
        bargroupgap=0.15
    )


    fig_uv.add_hrect(y0=0, y1=2, fillcolor="#4caf50", opacity=0.15, line_width=0, annotation_text="Low")
    fig_uv.add_hrect(y0=3, y1=5, fillcolor="#ffeb3b", opacity=0.2, line_width=0, annotation_text="Moderate")
    fig_uv.add_hrect(y0=6, y1=7, fillcolor="#ff9800", opacity=0.2, line_width=0, annotation_text="High")
    fig_uv.add_hrect(y0=8, y1=10, fillcolor="#f44336", opacity=0.2, line_width=0, annotation_text="Very High / Extreme")

    return fig_uv




"""
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Weather Dashboard",
            style={'textAlign': 'center', 'marginBottom': '40px'}),

    html.Div([
        html.Div([
            dcc.Graph(figure=fig_uv, style={'width': '100%'})
        ], style={'width': '48%'}),

])
])
"""


