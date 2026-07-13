import requests
from retry_requests import retry
import pandas as pd
import json
import plotly.express as px
from dash import Dash, html,dcc








def build_temperature_figs(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "daily":(
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "apparent_temperature_max",
                        "apparent_temperature_min",
                        "sunrise",
                        "sunset",
                        "daylight_duration",
                        "sunshine_duration"
                    ),
            "past_days": 7, 
            "forecast_days":7

            }

    response = requests.get(url, params=params, timeout=500)

    data = response.json()
    result = json.dumps(data, indent=2)
    daily_df = pd.DataFrame(data["daily"])
    daily_df["daylight_duration"] = (daily_df["daylight_duration"]/3600).round(2)
    daily_df["sunshine_duration"] = (daily_df["sunshine_duration"]/3600).round(2)
    daily_df["sunrise"] = pd.to_datetime(daily_df["sunrise"]).dt.strftime("%H:%M")
    daily_df["sunset"] = pd.to_datetime(daily_df["sunset"]).dt.strftime("%H:%M")
    daily_df["freeze_thaw"] = (daily_df["temperature_2m_min"] < 0) & (daily_df["temperature_2m_max"] > 0)
    freeze_thaw_count = daily_df["freeze_thaw"].sum()
    daily_df["time"] = pd.to_datetime(daily_df["time"])






    fig = px.line(
        daily_df,
        x="time",
        y=["temperature_2m_min", "temperature_2m_max"],
        color_discrete_sequence=["#3498db", "#3D4F7C"],  
        labels={
            "time": "Date",
            "value": "Temperature (°C)",
            "variable": ""
        }
    )


    fig.update_traces(
        line=dict(width=2, shape="spline"),     
        mode="lines+markers",
        marker=dict(
            size=7,
            symbol="circle",
            line=dict(width=1.5, color="white")     
        ),
        hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %d}<br>%{y}°C<extra></extra>"
    )


    fig.data[1].fill = "tonexty"
    fig.data[1].fillcolor = "rgba(199, 210, 227, 0.35)"


    fig.data[0].name = "Min Temp"
    fig.data[1].name = "Max Temp"

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="7-Day Temperature Trend",
            font=dict(size=22, color="#1f2937", family="Arial"),
            x=0.5
        ),
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        height=500,
        width=1220,
        margin=dict(l=60, r=40, t=90, b=50),
        hovermode="x unified",                  
        xaxis=dict(
            showgrid=False,
            tickformat="%b %d"
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False
        )
    )





    # Daily sunlight duration
    fig2 = px.bar(
        daily_df,
        x="time",
        y=["daylight_duration", "sunshine_duration"],
        title="Daily Daylight vs Sunshine Duration",
        labels={"time": "Date", "value": "Hours", "variable": ""},  
        color_discrete_sequence=["#3D4F7C", "#C7D2E3"],  
        barmode="group"
    )

    # Make daylight wider/base and sunshine on top with better visibility
    fig2.update_traces(
        marker_line_color="white",
        marker_line_width=0.8,
        opacity=0.95,
        selector=dict(name="daylight_duration"),
        marker=dict(
        cornerradius=12,     
        line=dict(width=0.5)
        )  
    )

    fig2.update_traces(
        opacity=0.85,
        marker_line_width=0.5,
        selector=dict(name="sunshine_duration"),
        marker=dict(
        cornerradius=12,     
        line=dict(width=0.5)
        )  
        
    )

    # Rename traces
    fig2.data[0].name = "Daylight Duration"
    fig2.data[1].name = "Actual Sunshine Duration"

    fig2.update_layout(
        template="plotly_white",
        height=520,
        width=610,
        xaxis_title="Date",
        yaxis_title="Hours per Day",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=40, t=90, b=50),
        xaxis=dict(tickformat="%b %d", showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )





    fig3 = px.bar(
        daily_df,
        x="time",
        y="temperature_2m_max",                    
        title=f"Freeze-Thaw Cycles ({daily_df['freeze_thaw'].sum()} days)",
        labels={"time": "Date", "temperature_2m_max": "Max Temperature (°C)"},
        color=daily_df["freeze_thaw"].map({True: "Freeze-Thaw Day", False: "Normal Day"}),
        color_discrete_map={
            "Freeze-Thaw Day": "#e74c3c",      
            "Normal Day": "#b0bec5"          
        },
        text=daily_df["freeze_thaw"].map({True: "FT", False: ""})  
    )

    fig3.update_traces(
        marker_line_color="white",
        marker_line_width=0.5,
        textposition="outside",
        marker=dict(
        cornerradius=12,     
        line=dict(width=0.5)
        ) 
    )

    fig3.update_layout(
        template="plotly_white",
        height=520,
        width=610,
        xaxis_title="Date",
        yaxis_title="Max Temperature (°C)",
        legend_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=50, r=40, t=90, b=50),
        xaxis=dict(tickformat="%b %d", showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )

    return fig, fig2, fig3




"""
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Weather Dashboard",
            style={'textAlign': 'center', 'marginBottom': '40px'}),

    html.Div([
        html.Div([
            dcc.Graph(figure=fig, style={'width': '100%'})
        ], style={'width': '48%'}),

        html.Div([
            dcc.Graph(figure=fig2, style={'width': '100%'})
        ], style={'width': '48%'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '20px'}),

    html.Div([
        dcc.Graph(figure=fig3, style={'width': '100%'})
    ], style={'width': '96%', 'margin': '20px auto 0'})
])
"""






