import requests
import pandas as pd
import json
import plotly.express as px




def build_soil_figs(lat, lon):

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
            "latitude":    lat,
            "longitude":   lon,
            "timezone":    "auto",
            "past_days": 7, 
            "forecast_days":7,
            "hourly":    ("soil_temperature_0cm",
                            "soil_temperature_6cm",
                            "soil_temperature_18cm",
                            "soil_temperature_54cm",
                            "soil_moisture_0_to_1cm",
                            "soil_moisture_1_to_3cm",
                            "soil_moisture_3_to_9cm",
                            "soil_moisture_9_to_27cm",
                            "soil_moisture_27_to_81cm"
                            )

    }
    response  = requests.get(url, params=params, timeout=500)
    data = response.json()
    cleaned_data = json.dumps(data, indent=2)
    result = pd.DataFrame(data["hourly"])
    result["time"] = pd.to_datetime(result["time"])


    depths = [0, 6, 18, 54]
    temp_cols = ["soil_temperature_0cm", "soil_temperature_6cm", 
                "soil_temperature_18cm", "soil_temperature_54cm"]

    df_melt = result.melt(
        id_vars=["time"],
        value_vars=temp_cols,
        var_name="Depth",
        value_name="Temperature"
    )
    df_melt["Depth"] = df_melt["Depth"].map({
        "soil_temperature_0cm": "0 cm",
        "soil_temperature_6cm": "6 cm",
        "soil_temperature_18cm": "18 cm",
        "soil_temperature_54cm": "54 cm"
    })
    fig_soil = px.imshow(
        result[temp_cols].T,             
        x=result["time"].dt.strftime("%b %d %H:%M"),   
        y=["0 cm (Surface)", "6 cm", "18 cm", "54 cm"],
        labels=dict(x="Time", y="Depth", color="Temp (°C)"),
        title="Soil Temperature Profile Over Time (°C) | Past 7 + Next 7 Days",
        color_continuous_scale="RdYlBu_r",   
        aspect="auto"
    )

    fig_soil.update_layout(
        template="plotly_white",
        height=520,
        width=1220,
        xaxis_title="Time",
        yaxis_title="Soil Depth",
        coloraxis_colorbar=dict(
            title="Temperature (°C)",
            thickness=20,
            len=0.8
        ),
        margin=dict(l=80, r=80, t=80, b=60)
    )
    fig_soil.update_xaxes(    
        tickangle=-45
        )



    moisture_cols = [
        "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm",
        "soil_moisture_3_to_9cm",
        "soil_moisture_9_to_27cm",
        "soil_moisture_27_to_81cm"
    ]



    fig_moisture = px.area(
        result,
        x="time",
        y=moisture_cols,
        title="Soil Moisture Profile at Different Depths | Past 7 + Next 7 Days",
        labels={"time": "Time", "value": "Soil Moisture (%)", "variable": "Depth"},
        color_discrete_sequence=["#1e88e5", "#42a5f5", "#81d4fa", "#b3e5fc", "#e1f5fe"],
        groupnorm="percent",         
    )

    fig_moisture.update_traces(
        line=dict(width=1.5),
        opacity=0.85
    )

    depth_labels = {
        "soil_moisture_0_to_1cm": "0–1 cm (Surface)",
        "soil_moisture_1_to_3cm": "1–3 cm",
        "soil_moisture_3_to_9cm": "3–9 cm",
        "soil_moisture_9_to_27cm": "9–27 cm",
        "soil_moisture_27_to_81cm": "27–81 cm (Deep)"
    }

    for trace in fig_moisture.data:
        trace.name = depth_labels.get(trace.name, trace.name)

    fig_moisture.update_layout(
        template="plotly_white",
        height=560,
        width=1220,
        xaxis_title="Time",
        yaxis_title="Soil Moisture (%)",
        legend=dict(title="Depth", orientation="v", y=1, x=1.02),
        margin=dict(l=60, r=100, t=90, b=60),
        hovermode="x unified"
    )

    return fig_soil, fig_moisture






"""
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Weather Dashboard",
            style={'textAlign': 'center', 'marginBottom': '40px'}),

    html.Div([
        html.Div([
            dcc.Graph(figure=fig_soil, style={'width': '100%'})
        ], style={'width': '48%'}),

    html.Div([
            dcc.Graph(figure=fig_moisture, style={'width': '100%'})
        ], style={'width': '48%'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '20px'}),


])
"""
