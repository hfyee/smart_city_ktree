"""Operational DB page — MongoDB."""

from unittest import result

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db.utils import mask_except_last_four
from db.utils_mongodb import (
    get_traffic_on_weather_days, 
    get_citizen_complaints,
    aggregate_citizen_complaints_by_category,
    aggregate_traffic_incidents_by_type
)

st.set_page_config(page_title="Smart City · Operational DB", page_icon="🗄️", layout="wide")
st.title("🗄️ Operational DB")
st.caption("MongoDB")

st.header("data.gov.sg dataset")
# ===========================================================================
# Aggregation pipeline with $group stage
# ===========================================================================
st.subheader("Aggregation of complaints by category")

year = st.slider("Select year", min_value=2015, max_value=2025, value=2022)

rows = aggregate_citizen_complaints_by_category(str(year))

if len(rows) > 0:
    df = pd.DataFrame(rows)
    column_order = ["category", "complaints_count", "earliest_date", "latest_date"]
    df = df[column_order]
    st.dataframe(df)

# ===========================================================================
# READ — results area with at least one filter
# ===========================================================================
st.subheader("Search citizen complaint records")

ccol1, ccol2 = st.columns(2)
with ccol1:
    complaint_category = st.selectbox(
        "Complaint category",
        ["Adverse Weather", "Traffic Congestion", "Municipal Services", "Infrastructure"],
    )
with ccol2:
    st.text("")

if st.button("Search", key="complaint_search_button"):
    rows = get_citizen_complaints(year=year, category=complaint_category)

    # Mask user_name before returning
    for row in rows:
        if "user_name" in row and row["user_name"]:
            row["user_name"] = mask_except_last_four(row["user_name"])

    if len(rows) > 0:
        df = pd.DataFrame(rows)
        column_order = ["date_posted", "location", "complaint_text", "user_name"]
        df = df[column_order]
        st.dataframe(df)

st.divider()

# ===========================================================================
# Aggregation of traffic incidents
# ===========================================================================
st.subheader("Aggregation of traffic incidents by type")

rows = aggregate_traffic_incidents_by_type(year=2026)

if len(rows) > 0:
    df = pd.DataFrame(rows)
    column_order = ["collection_time", "incident_type", "incidents_count"]
    df = df[column_order]
    st.dataframe(df)

st.subheader("Correlating weather with traffic incidents")
st.caption("Search weather within 3km of a traffic incident")

fcol1, fcol2 = st.columns(2)
with fcol1:
    wind_speed = st.slider("Select wind speed (km/h) >=", min_value=0, max_value=50, value=36)
    temperature = st.slider("Select temperature (celsius) <=", min_value=-10, max_value=40, value=4)
with fcol2:
    precipitation = st.slider("Select precipitation (mm) >=", min_value=0, max_value=20, value=14)
    visibility = st.slider("Select visibility (km) <=", min_value=2, max_value=20, value=6)

if st.button("Search", key="weather_search_button"):
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
