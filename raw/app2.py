import requests
from dash import Dash, dcc, html, Input, Output, State

# Each of these modules must now expose a FUNCTION (not pre-built figures)
# that takes (lat, lon) and returns the figure(s). See the conversion
# pattern in module_conversion_example.py for how to update each module.
from kpis import fetch_current, kpi_card, wind_direction, weather_codes
from temperature_trends import build_temperature_figs      # returns fig, fig2, fig3
from daily_trends import build_precip_fig                  # returns fig_precip
from soil_conditions import build_soil_figs                # returns fig_soil, fig_moisture
from wind_speed import build_wind_block_figs                # returns fig_wind, fig_gusts, fig_pressure, fig_cloud, fig_visibility
from visibility import build_uv_fig                         # returns fig_uv
from correlations import build_correlation_figs             # returns fig_lag, fig_storm


# ============================================================
# GEOCODING
# ============================================================

def get_coordinates(city_name):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city_name, "count": 1}
    )
    results = r.json().get("results")
    if not results:
        return None, None
    return results[0]["latitude"], results[0]["longitude"]


def search_cities(query):
    """Returns up to 5 matching cities as dropdown options for autocomplete."""
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


# ============================================================
# STYLE CONSTANTS
# ============================================================

COLORS = {
    "bg": "#f4f6f8",
    "card_bg": "#ffffff",
    "text": "#1f2937",
    "subtext": "#6b7280",
    "accent": "#3498db",
}

CHART_HEIGHT = 420

app = Dash(__name__)


# ============================================================
# LAYOUT HELPERS
# ============================================================

def normalize_height(fig_obj):
    fig_obj.update_layout(height=CHART_HEIGHT, margin=dict(l=50, r=30, t=60, b=40))
    return fig_obj


def section_header(title, subtitle=None):
    return html.Div([
        html.H2(title, style={
            "fontSize": "22px", "color": COLORS["text"], "marginBottom": "4px",
            "borderLeft": f"5px solid {COLORS['accent']}", "paddingLeft": "12px",
            "fontFamily": "Arial"
        }),
        html.P(subtitle, style={
            "fontSize": "13px", "color": COLORS["subtext"], "marginTop": "0",
            "paddingLeft": "17px", "fontFamily": "Arial"
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
    return html.Div(
        chart_card(fig_a),
        style={"width": "97%", "margin": "20px auto"}
    )


# ============================================================
# STATIC PAGE SHELL — headers, input controls, empty output slot
# ============================================================

app.layout = html.Div([

    html.Div([
        html.H1("Site Weather Analytics Dashboard",
                style={"textAlign": "center", "marginBottom": "6px",
                       "color": COLORS["text"], "fontFamily": "Arial"}),
        html.P("Weather, soil & storm risk overview for construction planning",
               style={"textAlign": "center", "color": COLORS["subtext"],
                      "marginTop": "0", "fontFamily": "Arial"})
    ], style={"padding": "30px 0", "borderBottom": "1px solid #e5e7eb", "marginBottom": "10px"}),

    # ---- Location controls ----
    html.Div([
        html.Div([
            html.Label("City", style={"fontSize": "12px", "color": COLORS["subtext"],
                                       "marginBottom": "4px", "display": "block"}),
            dcc.Dropdown(
                id="city-input",
                options=[],
                placeholder="Start typing a city...",
                searchable=True,
                clearable=True,
                style={"width": "220px", "borderRadius": "6px"}
            ),
        ]),
        html.Div([
            html.Label("Longitude", style={"fontSize": "12px", "color": COLORS["subtext"],
                                            "marginBottom": "4px", "display": "block"}),
            dcc.Input(id="lon-input", type="number", placeholder="Longitude", value=7.0,
                       style={"padding": "8px 10px", "borderRadius": "6px",
                              "border": "1px solid #d1d5db", "width": "110px"}),
        ]),
        html.Div([
            html.Label("Latitude", style={"fontSize": "12px", "color": COLORS["subtext"],
                                           "marginBottom": "4px", "display": "block"}),
            dcc.Input(id="lat-input", type="number", placeholder="Latitude", value=4.8,
                       style={"padding": "8px 10px", "borderRadius": "6px",
                              "border": "1px solid #d1d5db", "width": "110px"}),
        ]),
        html.Div([
            html.Label(" ", style={"fontSize": "12px", "marginBottom": "4px", "display": "block"}),
            html.Button("Update Dashboard", id="submit-btn", n_clicks=0,
                        style={"padding": "9px 20px", "backgroundColor": COLORS["accent"],
                               "color": "white", "border": "none", "borderRadius": "6px",
                               "cursor": "pointer", "fontWeight": "600"}),
        ]),
    ], style={
        "display": "flex", "justifyContent": "center", "alignItems": "flex-end",
        "gap": "14px", "marginBottom": "6px", "flexWrap": "wrap"
    }),

    html.Div(id="location-label",
              style={"textAlign": "center", "color": COLORS["subtext"], "marginBottom": "20px"}),

    # ---- Output region — filled entirely by the callback ----
    dcc.Loading(html.Div(id="dashboard-body"), type="circle"),

], style={
    "backgroundColor": COLORS["bg"],
    "padding": "30px",
    "maxWidth": "1300px",
    "margin": "0 auto",
    "fontFamily": "Arial"
})


# ============================================================
# AUTOCOMPLETE CALLBACK — populates city dropdown options as user types
# ============================================================

@app.callback(
    Output("city-input", "options"),
    Input("city-input", "search_value")
)
def update_city_options(search_value):
    return search_cities(search_value)


# ============================================================
# MAIN CALLBACK — rebuilds every section on button click
# ============================================================

@app.callback(
    Output("location-label", "children"),
    Output("dashboard-body", "children"),
    Input("submit-btn", "n_clicks"),
    State("city-input", "value"),
    State("city-input", "options"),
    State("lat-input", "value"),
    State("lon-input", "value"),
)
def update_dashboard(n_clicks, city_value, city_options, lat, lon):
    city_label = None

    # city_value looks like "4.8,7.0" — set as the dropdown option's "value"
    if city_value:
        try:
            lat, lon = map(float, city_value.split(","))
            match = next((o for o in (city_options or []) if o["value"] == city_value), None)
            city_label = match["label"] if match else None
        except (ValueError, TypeError):
            pass

    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return "Please enter a valid latitude/longitude or select a city.", html.Div()

    label = f"Showing data for: {city_label + ' — ' if city_label else ''}({lat:.2f}, {lon:.2f})"

    # ---- Fetch + build everything fresh for this lat/lon ----
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

    return label, body


if __name__ == "__main__":
    app.run(debug=True)