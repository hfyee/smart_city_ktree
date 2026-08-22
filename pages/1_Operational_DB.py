"""Operational DB page — your third database (Task A1)."""

from unittest import result

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db.utils_mongodb import (
    get_traffic_on_weather_days, 
    get_weather_cursor,
    get_citizen_complaints,
    aggregate_citizen_complaints_by_category
)

st.set_page_config(page_title="Smart City · Operational DB", page_icon="🗄️", layout="wide")
st.title("🗄️ Operational DB")
st.caption("MongoDB")

st.header("POLITEMall dataset")
# ===========================================================================
# Aggregation pipeline with $group stage
# ===========================================================================
st.subheader("Aggregation of complaints by category")

filter_priority = st.selectbox(
    "Match by priority",
    ["(all)", "Low", "Medium", "High"],
)

rows = aggregate_citizen_complaints_by_category(filter_priority)

if len(rows) > 0:
    df = pd.DataFrame(rows)
    column_order = ["category", "complaints_count", "earliest_date", "latest_date"]
    df = df[column_order]
    st.dataframe(df)

st.subheader("Search citizen complaint records")

ccol1, ccol2 = st.columns(2)
with ccol1:
    year = st.radio("Pick a year:", ["2024", "2025"], key="complaint_year_radio")
    st.write("You selected:", year)
with ccol2:
    complaint_category = st.selectbox(
        "Complaint category",
        ["Noise", "Traffic", "Roads", "Lighting", "Trash", "Parks"],
    )
    complaint_priority = st.selectbox(
        "Select the priority",
        ["Low", "Medium", "High"],
    )

if st.button("Search", key="complaint_search_button"):
    rows = get_citizen_complaints(year=year, category=complaint_category, priority=complaint_priority)
    if len(rows) > 0:
        df = pd.DataFrame(rows)
        column_order = ["date_submitted", "area", "complaint_text", 
                        "status", "contact_info"]
        df = df[column_order]
        st.dataframe(df.style.format({"contact_info": lambda val: str(val)[:12]}))

st.divider()

# ===========================================================================
# Multipanel weather boxplot
# ===========================================================================
st.subheader("Weather data boxplot")

cursor = get_weather_cursor()
df = pd.DataFrame(list(cursor))

# 3. Configure 2x2 Subplot Grid
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 10))
sns.set_theme(style="whitegrid")

# Define traffic-impacting features, colors, and axis titles
features = [
    ("visibility_km", "Visibility (km)", "#4C72B0", axes[0, 0]),
    ("precipitation_mm", "Precipitation (mm)", "#55A868", axes[0, 1]),
    ("wind_speed_kmh", "Wind Speed (km/h)", "#C44E52", axes[1, 0]),
    ("temperature_celsius", "Temperature (°C)", "#8172B3", axes[1, 1])
]

# 4. Generate individual boxplots
for col, label, color, ax in features:
    sns.boxplot(
        y=df[col],
        ax=ax,
        color=color,
        width=0.4,
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.5},
        notch=True  # Highlights median confidence interval
    )
    ax.set_title(f"Distribution of {label}", fontsize=12, fontweight="bold")
    ax.set_ylabel(label, fontsize=10)
    ax.set_xlabel("")

plt.suptitle("Weather Conditions Affecting Road Traffic & Hazard Risks", fontsize=15, y=0.98)
plt.tight_layout()
# Render directly in Streamlit instead of plt.show()
st.pyplot(fig)

st.divider()

# ===========================================================================
# READ — results area with at least one filter
# ===========================================================================
st.subheader("Search weather and traffic records")
st.caption("Matching weather days and high-congestion traffic")

year = st.radio("Pick a year:", ["2024", "2025"], key="weather_year_radio")
st.write("You selected:", year)

fcol1, fcol2 = st.columns(2)
with fcol1:
    wind_speed = st.slider("Select wind speed (km/h) >=", min_value=0, max_value=50, value=36)
    temperature = st.slider("Select temperature (celsius) <=", min_value=-10, max_value=40, value=4)
with fcol2:
    precipitation = st.slider("Select precipitation (mm) >=", min_value=0, max_value=20, value=14)
    visibility = st.slider("Select visibility (km) <=", min_value=2, max_value=20, value=6)

if st.button("Search", key="weather_search_button"):
#    rows = get_days_with_this_weather(year=year, wind_speed=wind_speed, temperature=temperature, 
#                                      precipitation=precipitation, visibility=visibility)
#    if len(rows) > 0:
#        df = pd.DataFrame(rows)
#        column_order = ["recorded_at", "station_id", "visibility_km", 
#                        "precipitation_mm", "wind_speed_kmh", "temperature_celsius"]
#        df = df[column_order]
#        st.dataframe(df.style.format({"recorded_at": lambda val: str(val)[:10], 
#                                      "precipitation_mm": "{:.2f}",
#                                      "temperature_celsius": "{:.1f}"}))

    merged_rows = get_traffic_on_weather_days(year=year, wind_speed=wind_speed, temperature=temperature, 
                                      precipitation=precipitation, visibility=visibility)
    if len(merged_rows) > 0:
        df_merged = pd.DataFrame(merged_rows)
        st.dataframe(df_merged.style.format({"recorded_at": lambda val: str(val)[:10], 
                                      "precipitation_mm": "{:.2f}",
                                      "temperature_celsius": "{:.1f}"}))

#st.divider()
#st.header("CRUD operations")
#st.caption("Akan datang!")
## ===========================================================================
## CREATE — input form
## ===========================================================================
#with st.expander("Add a record"):
#    ...
#
## ===========================================================================
## UPDATE / DELETE
## ===========================================================================
#with st.expander("Update / Delete a record"):
#    ...
#
#st.divider()
