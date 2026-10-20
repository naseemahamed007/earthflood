
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="EarthFlood | Monitoring",
    page_icon="🌍",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #071827 0%, #0b2132 100%);
    color: #eef7ff;
}
.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1, h2, h3, p, label {
    color: #eef7ff !important;
}
.hero {
    padding: 28px;
    border: 1px solid #24475c;
    border-radius: 22px;
    background: linear-gradient(120deg, #10364a, #102539);
    margin-bottom: 24px;
}
.eyebrow {
    color: #53e0c0;
    font-size: 13px;
    letter-spacing: 2px;
    font-weight: 700;
}
.small-muted {
    color: #a9c2d2;
    font-size: 14px;
}
div[data-testid="stMetric"] {
    background: #102b3e;
    border: 1px solid #24475c;
    border-radius: 16px;
    padding: 18px;
}
div[data-testid="stMetricLabel"] {
    color: #b6ccda !important;
}
div[data-testid="stMetricValue"] {
    color: #53e0c0 !important;
}
.stButton > button {
    border-radius: 12px;
    border: 1px solid #53e0c0;
    background: #53e0c0;
    color: #06212b;
    font-weight: 700;
    min-height: 44px;
}
section[data-testid="stSidebar"] {
    background: #091d2c;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div class="hero">
    <div class="eyebrow">EARTHFLOOD • ENVIRONMENTAL MONITORING</div>
    <h1>🌍 Flood & Rainfall Intelligence</h1>
    <p>Explore current weather conditions and rainfall forecasts
    to support early awareness and further investigation.</p>
    <div class="small-muted">Research prototype · Public weather data</div>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## 🌍 EarthFlood")
    st.caption("Monitoring dashboard")
    city = st.text_input("Location", value="Chennai")
    st.caption("Try Chennai, Mumbai, Delhi or Bengaluru.")
    refresh = st.button("↻ Refresh weather data", use_container_width=True)
    st.divider()
    st.caption("DATA LIMITATION")
    st.write(
        "Weather conditions are model-derived. "
        "They do not confirm flooding at street level."
    )

if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
if "weather_city" not in st.session_state:
    st.session_state.weather_city = ""

# Load automatically the first time, or when refreshing/changing city.
should_load = (
    st.session_state.weather_data is None
    or st.session_state.weather_city.lower() != city.strip().lower()
    or refresh
)

if not city.strip():
    st.warning("Enter a city or town in the sidebar.")
    st.stop()

if should_load:
    try:
        with st.spinner("Loading the latest available weather data..."):
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": city.strip(),
                    "count": 1,
                    "language": "en",
                    "format": "json"
                },
                timeout=20
            )
            geo.raise_for_status()
            places = geo.json().get("results", [])

            if not places:
                st.error("Location not found. Try a different city name.")
                st.stop()

            place = places[0]
            lat = place["latitude"]
            lon = place["longitude"]

            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "apparent_temperature,precipitation,rain,"
                        "showers,weather_code,wind_speed_10m"
                    ),
                    "hourly": (
                        "precipitation,precipitation_probability,"
                        "temperature_2m,wind_speed_10m"
                    ),
                    "forecast_days": 3,
                    "timezone": "auto"
                },
                timeout=25
            )
            response.raise_for_status()
            weather = response.json()

            st.session_state.weather_data = {
                "place": place,
                "weather": weather
            }
            st.session_state.weather_city = city.strip()

    except requests.RequestException:
        st.error(
            "Weather data could not be reached. Check your internet "
            "connection and press Refresh weather data."
        )
        st.stop()

saved = st.session_state.weather_data
place = saved["place"]
weather = saved["weather"]
current = weather.get("current", {})
hourly = weather.get("hourly", {})

if not current or not hourly:
    st.error("The weather service returned incomplete data. Please refresh.")
    st.stop()

# ---------- DATA ----------
df = pd.DataFrame({
    "Time": pd.to_datetime(hourly["time"]),
    "Rainfall (mm)": hourly["precipitation"],
    "Rain probability (%)": hourly["precipitation_probability"],
    "Temperature (°C)": hourly["temperature_2m"],
    "Wind speed (km/h)": hourly["wind_speed_10m"]
})

current_time = pd.to_datetime(current["time"])
forecast_end = df["Time"].max()

st.markdown(f"### 📍 {place['name']}, {place.get('country', '')}")
st.caption(
    f"Weather data timestamp: {current_time} · "
    f"Forecast ends: {forecast_end} · "
    f"Timezone: {weather.get('timezone', 'local time')}"
)

st.info(
    "This timestamp is the weather service's reported current-data time, "
    "not a guarantee that a physical sensor measured conditions at that time."
)

# ---------- CURRENT CONDITIONS ----------
st.markdown("### Current weather conditions")
a, b, c, d = st.columns(4)

a.metric(
    "Temperature",
    f"{current.get('temperature_2m', '—')} °C",
    help="Weather-model-based current condition"
)
b.metric(
    "Humidity",
    f"{current.get('relative_humidity_2m', '—')}%",
)
c.metric(
    "Precipitation",
    f"{current.get('precipitation', '—')} mm",
    help="Current precipitation estimate reported by the API"
)
d.metric(
    "Wind speed",
    f"{current.get('wind_speed_10m', '—')} km/h",
)

st.caption(
    "These measurements are not a flood-risk score or an official warning."
)

# ---------- CHARTS ----------
st.markdown("### 📊 Rainfall outlook")

tab1, tab2, tab3 = st.tabs([
    "Rainfall",
    "Rain probability",
    "Temperature"
])

with tab1:
    fig = px.area(
        df,
        x="Time",
        y="Rainfall (mm)",
        title="Hourly rainfall forecast",
        template="plotly_dark"
    )
    fig.update_traces(line_color="#53e0c0", fillcolor="rgba(83,224,192,0.18)")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=55, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.line(
        df,
        x="Time",
        y="Rain probability (%)",
        title="Forecast probability of precipitation",
        template="plotly_dark"
    )
    fig.update_traces(line_color="#69aef5", line_width=3)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=55, b=10),
        yaxis=dict(range=[0, 100])
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.line(
        df,
        x="Time",
        y="Temperature (°C)",
        title="Forecast temperature",
        template="plotly_dark"
    )
    fig.update_traces(line_color="#ffbf69", line_width=3)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=55, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- MAP ----------
st.markdown("### 🗺️ Monitoring location")
st.map(pd.DataFrame({
    "latitude": [place["latitude"]],
    "longitude": [place["longitude"]]
}))

# ---------- DATA TABLE / EXPORT ----------
with st.expander("View forecast data"):
    st.dataframe(df, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download forecast data (CSV)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="earthflood_forecast.csv",
    mime="text/csv"
)

st.divider()
st.caption(
    "EarthFlood is a research prototype, not an emergency service. "
    "Rainfall alone cannot reliably predict flooding. Use official "
    "weather, flood and emergency alerts for safety decisions."
)
