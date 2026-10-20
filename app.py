
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="EarthFlood",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 EarthFlood")
st.subheader("Flood Monitoring and Early Risk Assessment")
st.write(
    "Explore rainfall forecasts and identify locations "
    "that may need closer flood-risk monitoring."
)

st.info(
    "Research prototype only. This is not an official flood "
    "warning system. Follow local emergency authorities."
)

location = st.text_input(
    "Enter a city or town",
    value="Chennai"
)

if st.button("Check Rainfall", type="primary"):
    try:
        with st.spinner("Finding location..."):
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                },
                timeout=20
            )
            geo_response.raise_for_status()
            places = geo_response.json().get("results", [])

        if not places:
            st.error("Location not found. Try another city name.")
            st.stop()

        place = places[0]
        latitude = place["latitude"]
        longitude = place["longitude"]

        with st.spinner("Loading rainfall forecast..."):
            weather_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "precipitation",
                    "forecast_days": 3,
                    "timezone": "auto"
                },
                timeout=20
            )
            weather_response.raise_for_status()
            weather = weather_response.json()

        hourly = weather["hourly"]
        data = pd.DataFrame({
            "Time": pd.to_datetime(hourly["time"]),
            "Rainfall (mm)": hourly["precipitation"]
        })

        st.success(
            f"Forecast loaded for {place['name']}, "
            f"{place.get('country', '')}"
        )

        total_rain = float(data["Rainfall (mm)"].sum())
        peak_rain = float(data["Rainfall (mm)"].max())

        col1, col2, col3 = st.columns(3)
        col1.metric("Forecast period", "3 days")
        col2.metric("Forecast rainfall", f"{total_rain:.1f} mm")
        col3.metric("Peak hourly rainfall", f"{peak_rain:.1f} mm")

        st.subheader("📊 Rainfall Forecast")
        chart = px.line(
            data,
            x="Time",
            y="Rainfall (mm)",
            title="Hourly precipitation forecast"
        )
        st.plotly_chart(chart, use_container_width=True)

        st.subheader("📍 Selected Location")
        st.map(pd.DataFrame({
            "latitude": [latitude],
            "longitude": [longitude]
        }))

        st.subheader("📄 Forecast Data")
        st.dataframe(data, use_container_width=True)

        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download rainfall data (CSV)",
            data=csv,
            file_name="earthflood_rainfall.csv",
            mime="text/csv"
        )

        st.caption(
            "Rainfall alone cannot determine whether flooding "
            "will occur. This forecast is not a verified flood alert."
        )

    except requests.RequestException:
        st.error(
            "Could not retrieve live weather data. "
            "Please try again later."
        )
    except (KeyError, ValueError, TypeError):
        st.error("The weather service returned unexpected data.")
