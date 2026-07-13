import requests
from dash import Dash, dcc, html, Input, Output, State, no_update
from kpis import fetch_current, kpi_card, wind_direction, weather_codes
from temperature_trends import build_temperature_figs     
from daily_trends import build_precip_fig             
from soil_conditions import build_soil_figs             
from wind_speed import build_wind_block_figs          
from visibility import build_uv_fig            
from correlations import build_correlation_figs  

# GEOCODING FUNCTIONS
def get_coordinates(city_name):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city_name, "count": 1}
    )
    results = r.json().get("results")
    if not results:
        return None, None
    return results[0]["latitude"], results[0]["longitude"]

def reverse_geocode(lat, lon):
    try:
        r = requests.get(
            "https://api.bigdatacloud.net/data/reverse-geocode-client",
            params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
            timeout=10
        )
        data = r.json()
        parts = [data.get("city") or data.get("locality"), data.get("principalSubdivision"), data.get("countryName")]
        label = ", ".join(p for p in parts if p)
        return label or None
    except requests.RequestException:
        return None

def search_cities(query):
    if not query or len(query) < 2:
        return []
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": query, "count": 5}
    )
    results = r.json().get("results", [])
    options = []
    for res in results:
        parts = [res["name"], res.get("admin1", ""), res["country"]]
        label = ", ".join(p for p in parts if p)
        value = f"{res['latitude']},{res['longitude']}"
        options.append({"label": label, "value": value})
    return options

COLORS = {
    "bg": "#f4f6f8",
    "card_bg": "#ffffff",
    "text": "#1f2937",
    "subtext": "#6b7280",
    "accent": "#3498db",
}

CHART_HEIGHT = 420

app = Dash(__name__)

def normalize_height(fig_obj):
    fig_obj.update_layout(height=CHART_HEIGHT, margin=dict(l=50, r=30, t=60, b=40))
    return fig_obj

def section_header(title, subtitle=None):
    return html.Div([
        html.H2(title, style={
            "fontSize": "22px", "color": COLORS["text"], "marginBottom": "4px",
            "borderLeft": f"5px solid {COLORS['accent']}", "paddingLeft": "12px"
        }),
        html.P(subtitle, style={
            "fontSize": "13px", "color": COLORS["subtext"], "marginTop": "0",
            "paddingLeft": "17px"
        }) if subtitle else None
    ], style={"marginTop": "55px", "marginBottom": "20px"})

def chart_card(fig_obj):
    return html.Div(
        dcc.Graph(figure=normalize_height(fig_obj), style={"width": "100%"}),
        style={
            "backgroundColor": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "10px",
            "boxShadow": "0 1px 6px rgba(0,0,0,0.08)",
        }
    )

def two_col_row(fig_a, fig_b):
    return html.Div([
        html.Div(chart_card(fig_a), style={"width": "48%"}),
        html.Div(chart_card(fig_b), style={"width": "48%"}),
    ], style={"display": "flex", "justifyContent": "center", "gap": "20px"})

def full_row(fig_a):
    return html.Div(chart_card(fig_a), style={"width": "97%", "margin": "20px auto"})

# ====================== HEADER ======================
header = html.Div([
    html.Div([
        html.H1("Site Weather Analytics Dashboard", style={'fontSize': '32px', 'fontWeight': '700', 'color': '#1e3a8a', 'marginBottom': '6px', 'letterSpacing': '-0.5px'}),
        html.P("Weather, soil & storm risk overview for construction planning", style={'fontSize': '15px', 'color': '#64748b', 'margin': '0'})
    ], style={'textAlign': 'center', 'paddingTop': '10px'}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id="city-input",
                placeholder="🔍 Search for a city...",
                searchable=True,
                clearable=True,
                style={'width': '230px', 'borderRadius': '10px'}
            )
        ]),
        html.Div([
            html.Label("Longitude", style={'fontSize': '12px', 'color': '#94a3b8', 'display': 'block', 'marginBottom': '4px'}),
            dcc.Input(id="lon-input", type="number", value=7.0,
                      style={'padding': '9px 12px', 'borderRadius': '10px', 'border': '1px solid #e2e8f0', 'width': '100px'})
        ]),
        html.Div([
            html.Label("Latitude", style={'fontSize': '12px', 'color': '#94a3b8', 'display': 'block', 'marginBottom': '4px'}),
            dcc.Input(id="lat-input", type="number", value=4.8,
                      style={'padding': '9px 12px', 'borderRadius': '10px', 'border': '1px solid #e2e8f0', 'width': '100px'})
        ]),
        html.Div([
            html.Label("Ready?", style={'fontSize': '12px', 'color': '#94a3b8', 'display': 'block', 'marginBottom': '4px', 'textAlign': 'center'}),
            html.Button(
                "🌤️  Update Dashboard",
                id="submit-btn", n_clicks=0,
                style={
                    'padding': '10px 22px', 'backgroundColor': '#2563eb', 'color': 'white',
                    'border': 'none', 'borderRadius': '999px', 'fontWeight': '600',
                    'fontSize': '14px', 'cursor': 'pointer',
                    'boxShadow': '0 4px 10px rgba(37,99,235,0.35)',
                    'transition': 'transform 0.15s ease'
                }
            )
        ]),
    ], style={'display': 'flex', 'gap': '14px', 'justifyContent': 'center', 'alignItems': 'flex-end', 'marginTop': '26px', 'flexWrap': 'wrap'}),

    html.Div(id="location-label", style={'textAlign': 'center', 'marginTop': '14px', 'fontSize': '13px', 'color': '#64748b'})
], style={'backgroundColor': 'white', 'padding': '28px 0 36px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.06)', 'marginBottom': '40px', 'borderRadius': '16px'})

# ====================== LAYOUT ======================
app.layout = html.Div([
    header,
    dcc.Loading(
        id="loading",
        type="circle",
        children=html.Div(id="dashboard-body")
    )
], style={'backgroundColor': COLORS["bg"], 'padding': '30px', 'maxWidth': '1300px', 'margin': '0 auto'})


# ====================== AUTOCOMPLETE CALLBACK ======================
@app.callback(
    Output("city-input", "options"),
    Input("city-input", "search_value")
)
def update_city_options(search_value):
    if not search_value or len(search_value) < 2:
        return no_update
    return search_cities(search_value)


# ====================== MAIN CALLBACK ======================
@app.callback(
    Output("location-label", "children"),
    Output("dashboard-body", "children"),
    Output("lat-input", "value"),
    Output("lon-input", "value"),
    Input("submit-btn", "n_clicks"),
    State("city-input", "value"),
    State("city-input", "options"),
    State("lat-input", "value"),
    State("lon-input", "value"),
)
def update_dashboard(n_clicks, city_value, city_options, lat, lon):
    city_label = None
    if city_value:
        try:
            lat, lon = map(float, city_value.split(","))
            match = next((o for o in (city_options or []) if o["value"] == city_value), None)
            city_label = match["label"] if match else None
        except (ValueError, TypeError):
            pass

    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return "Please enter a valid latitude/longitude or select a city.", html.Div(), lat, lon
    if not city_label:
        city_label = reverse_geocode(lat, lon)

    label = f"Showing data for: {city_label + ' — ' if city_label else ''}({lat:.2f}, {lon:.2f})"

    current = fetch_current(lat, lon)
    fig, fig2, fig3 = build_temperature_figs(lat, lon)
    fig_precip = build_precip_fig(lat, lon)
    fig_soil, fig_moisture = build_soil_figs(lat, lon)
    fig_wind, fig_gusts, fig_pressure, fig_cloud, fig_visibility = build_wind_block_figs(lat, lon)
    fig_uv = build_uv_fig(lat, lon)
    fig_lag, fig_storm = build_correlation_figs(lat, lon)

    kpi_row = html.Div(
        [
            kpi_card("Temperature", current["temperature_2m"], " °C"),
            kpi_card("Humidity", current["relative_humidity_2m"], "%"),
            kpi_card("Wind Speed", current["wind_speed_10m"], " km/h"),
            kpi_card("Wind Direction", wind_direction(current["wind_direction_10m"])),
            kpi_card("Weather", weather_codes[current["weather_code"]]),
            kpi_card("Surface Pressure", current["surface_pressure"], " hPa"),
            kpi_card("Rain", current["rain"], " mm"),
            kpi_card("Showers", current["showers"], " mm"),
            kpi_card("Precipitation", current["precipitation"], " mm"),
        ],
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "justifyContent": "center"}
    )

    body = html.Div([

        section_header("Current Weather", "Right-now snapshot at the site"),
        kpi_row,

        section_header("Temperature Trends & Extremes",
                        "Daily min/max temperature | full trend across past and forecast days"),
        full_row(fig),
        two_col_row(fig2, fig3),

        section_header("Soil Conditions",
                        "Soil temperature and moisture across depths | foundation & excavation planning"),
        full_row(fig_soil),
        full_row(fig_moisture),

        section_header("Precipitation & Water",
                        "Daily rainfall trend | scheduling pours, roofing, and site access"),
        full_row(fig_precip),

        section_header("Wind",
                        "Wind speed and gusts | crane, scaffolding & material safety"),
        two_col_row(fig_wind, fig_gusts),

        section_header("Atmospheric Pressure & Storm Risk",
                        "Pressure drops and cloud cover as early storm indicators"),
        two_col_row(fig_pressure, fig_cloud),

        section_header("Sun & Visibility",
                        "UV exposure and visibility conditions for outdoor work"),
        two_col_row(fig_uv, fig_visibility),

        section_header("Correlations & Risk Signals",
                        "Combined patterns: moisture lag, freeze-thaw, and storm early-warning"),
        two_col_row(fig_lag, fig_storm),

        html.Div(style={"height": "60px"})
    ])

    return label, body, lat, lon


if __name__ == "__main__":
    app.run(debug=True)