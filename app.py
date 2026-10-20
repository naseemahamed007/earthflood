
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# =====================================================
# MES FLOODSENSE — FLOOD & RAINFALL INTELLIGENCE
# =====================================================

st.set_page_config(
    page_title="MES FloodSense",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# MODERN COLOURFUL DESIGN
# =====================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at 5% 0%, #193e70 0%, transparent 35%),
        linear-gradient(140deg, #071525, #101b36 55%, #202044);
    color: #f2f6ff;
}
.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}
h1, h2, h3, p, label {
    color: #f2f6ff !important;
}
.hero {
    padding: 34px;
    border-radius: 26px;
    background: linear-gradient(115deg, #087eaa, #4f46e5 60%, #9333ea);
    border: 1px solid #7794ff;
    box-shadow: 0 15px 40px #0004;
    margin-bottom: 25px;
}
.hero-tag {
    color: #a7f3d0;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
}
.hero h1 {
    font-size: clamp(30px, 4vw, 48px);
    margin: 10px 0;
}
.hero p {
    color: #edf5ff !important;
    font-size: 16px;
}
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142944, #20294a);
    border: 1px solid #385477;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 8px 25px #0002;
}
div[data-testid="stMetricLabel"] {
    color: #c2d3ee !important;
}
div[data-testid="stMetricValue"] {
    color: #67e8f9 !important;
    font-weight: 800;
}
.stButton > button,
.stDownloadButton > button {
    border-radius: 12px;
    min-height: 44px;
    font-weight: 700;
    border: 1px solid #67e8f9;
    transition: 0.2s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #c4b5fd;
    color: #c4b5fd;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #09172b, #172544);
}
div[data-testid="stTabs"] button {
    font-weight: 700;
}
.footer {
    padding: 22px;
    margin-top: 28px;
    border-top: 1px solid #34445f;
    text-align: center;
    color: #b5c7e5;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# WEATHER DATA FUNCTION
# =====================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_weather(city, forecast_days):

    # Find the city
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=20
    )
    geo_response.raise_for_status()

    places = geo_response.json().get("results", [])

    if not places:
        return None

    place = places[0]

    # Get weather information
    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "rain,"
                "showers,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "hourly": (
                "precipitation,"
                "precipitation_probability,"
                "temperature_2m,"
                "wind_speed_10m"
            ),
            "forecast_days": forecast_days,
            "timezone": "auto"
        },
        timeout=25
    )
    weather_response.raise_for_status()

    return place, weather_response.json()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("## 🌊 MES FloodSense")
    st.caption("Environmental intelligence dashboard")
    st.divider()

    city = st.text_input(
        "📍 Search a city or town",
        value="Chennai",
        placeholder="For example, Chennai"
    )

    forecast_days = st.selectbox(
        "📅 Forecast duration",
        [1, 3, 7],
        index=1,
        format_func=lambda n: (
            f"{n} day" if n == 1 else f"{n} days"
        )
    )

    refresh = st.button(
        "🔄 Refresh weather data",
        use_container_width=True
    )

    if refresh:
        get_weather.clear()

    st.divider()

    st.markdown("### 📡 Data source")
    st.caption("Open-Meteo public weather API")
    st.caption("Forecast and current weather estimates")
    st.caption("Cached for up to 10 minutes")

    st.divider()

    st.markdown("### ⚠️ Important")
    st.caption(
        "Weather forecasts cannot confirm flooding at "
        "street level. Follow official warnings."
    )


# =====================================================
# HEADER
# =====================================================

st.markdown("""
<div class="hero">
    <div class="hero-tag">MES • ENVIRONMENTAL RESEARCH</div>
    <h1>🌊 MES FloodSense</h1>
    <p>
        Explore rainfall patterns, weather conditions and forecasts
        through an interactive environmental monitoring dashboard.
    </p>
    <div>
        🌦️ Weather intelligence &nbsp; • &nbsp;
        📊 Interactive analytics &nbsp; • &nbsp;
        🗺️ Location explorer
    </div>
</div>
""", unsafe_allow_html=True)

st.info(
    "MES FloodSense is a research prototype. Weather forecasts "
    "are verified flood observations."
)


# =====================================================
# INPUT VALIDATION AND DATA LOADING
# =====================================================

if not city.strip():
    st.warning("Enter a city or town in the sidebar.")
    st.stop()

try:
    with st.spinner("🌐 Loading the latest available weather data..."):
        result = get_weather(city.strip(), forecast_days)

    if result is None:
        st.error(
            "Location not found. Check the spelling or try another city."
        )
        st.stop()

    place, weather = result

    current = weather.get("current", {})
    hourly = weather.get("hourly", {})

    if not current or not hourly:
        st.error("The weather service returned incomplete data.")
        st.stop()

    df = pd.DataFrame({
        "Time": pd.to_datetime(hourly["time"]),
        "Rainfall (mm)": hourly["precipitation"],
        "Rain probability (%)": hourly["precipitation_probability"],
        "Temperature (°C)": hourly["temperature_2m"],
        "Wind speed (km/h)": hourly["wind_speed_10m"]
    })

except requests.RequestException:
    st.error(
        "Unable to connect to the weather service. "
        "Check your connection and click Refresh weather data."
    )
    st.stop()

except (KeyError, ValueError, TypeError):
    st.error(
        "The weather service returned unexpected data. Please try again."
    )
    st.stop()


# =====================================================
# LOCATION AND DATA TIMESTAMP
# =====================================================

st.markdown(
    f"### 📍 {place['name']}, {place.get('country', '')}"
)

st.caption(
    f"Weather API timestamp: {current.get('time', 'Not supplied')} "
    f" · Timezone: {weather.get('timezone', 'Not supplied')}"
)

st.caption(
    "The timestamp is supplied by the weather service. "
    "It does not guarantee a live physical sensor measurement."
)


# =====================================================
# CURRENT WEATHER CARDS
# =====================================================

st.markdown("### ⚡ Current weather estimates")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🌡️ Temperature",
    f"{current.get('temperature_2m', '—')} °C"
)

c2.metric(
    "💧 Humidity",
    f"{current.get('relative_humidity_2m', '—')}%"
)

c3.metric(
    "🌧️ Precipitation",
    f"{current.get('precipitation', '—')} mm"
)

c4.metric(
    "💨 Wind speed",
    f"{current.get('wind_speed_10m', '—')} km/h"
)


# =====================================================
# FORECAST SUMMARY
# =====================================================

st.markdown("### 📈 Forecast overview")

s1, s2, s3 = st.columns(3)

s1.metric(
    "Forecast duration",
    f"{forecast_days} day" if forecast_days == 1
    else f"{forecast_days} days"
)

s2.metric(
    "Total forecast rainfall",
    f"{df['Rainfall (mm)'].sum():.1f} mm"
)

s3.metric(
    "Peak hourly rainfall",
    f"{df['Rainfall (mm)'].max():.1f} mm"
)

st.caption(
    "Total rainfall is the sum of the forecast's hourly precipitation "
    "values. It is not a flood-risk score."
)


# =====================================================
# INTERACTIVE CHART EXPLORER
# =====================================================

st.markdown("### 📊 Interactive weather explorer")

chart_choice = st.selectbox(
    "Choose a data layer",
    [
        "Rainfall (mm)",
        "Rain probability (%)",
        "Temperature (°C)",
        "Wind speed (km/h)"
    ]
)

max_hours = len(df)

hours_to_show = st.slider(
    "Choose how many forecast hours to display",
    min_value=1,
    max_value=max_hours,
    value=min(48, max_hours),
    step=1
)

chart_df = df.head(hours_to_show)

chart_colours = {
    "Rainfall (mm)": "#22d3ee",
    "Rain probability (%)": "#a78bfa",
    "Temperature (°C)": "#fb923c",
    "Wind speed (km/h)": "#4ade80"
}

fig = px.area(
    chart_df,
    x="Time",
    y=chart_choice,
    title=f"{chart_choice} forecast",
    template="plotly_dark",
    color_discrete_sequence=[chart_colours[chart_choice]]
)

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12,25,48,0.6)",
    font_color="#eef6ff",
    title_font_size=22,
    margin=dict(l=15, r=15, t=60, b=15),
    hovermode="x unified"
)

fig.update_traces(
    line=dict(width=3),
    fillcolor="rgba(34,211,238,0.16)"
)

if chart_choice == "Rain probability (%)":
    fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, use_container_width=True)


# =====================================================
# MAP, DATA TABLE AND PROJECT INFORMATION
# =====================================================

map_tab, data_tab, about_tab = st.tabs([
    "🗺️ Location map",
    "📄 Forecast data",
    "ℹ️ About MES FloodSense"
])

with map_tab:

    st.markdown("#### 🌍 Selected monitoring location")

    map_data = pd.DataFrame({
        "latitude": [place["latitude"]],
        "longitude": [place["longitude"]]
    })

    st.map(map_data)

    st.caption(
        "The map marks the searched city. It does not show "
        "verified flood boundaries or street-level water levels."
    )


with data_tab:

    st.markdown("#### Hourly forecast data")

    st.dataframe(
        chart_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download forecast data (CSV)",
        data=chart_df.to_csv(index=False).encode("utf-8"),
        file_name="MES_FloodSense_forecast.csv",
        mime="text/csv",
        use_container_width=True
    )


with about_tab:

    st.markdown("#### 🌍 About the project")

    st.write(
        "MES FloodSense is a software research prototype designed "
        "to explore weather forecasts and rainfall information."
    )

    st.write("**Weather provider:** Open-Meteo")
    st.write("**Technology:** Python, Streamlit, Pandas and Plotly")
    st.write("**Cost:** Uses public weather API access without a paid API key.")

    st.warning(
        "This version does not include verified river gauges, "
        "street-level flood sensors or an official flood-warning feed."
    )


# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    <strong>🌊 MES FloodSense</strong><br>
    Environmental awareness through data.<br><br>
    Research prototype · an official flood-warning system
</div>
""", unsafe_allow_html=True)
