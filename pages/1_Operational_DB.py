"""Operational DB page — MongoDB."""

from unittest import result
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from db.utils import mask_except_last_four
from db.utils_mongodb import (
    get_citizen_complaints,
    aggregate_citizen_complaints_by_category,
    aggregate_traffic_incidents_by_type,
    get_traffic_incidents,
    enrich_incidents_with_weather
)

def plot_incidents_map(df: pd.DataFrame):
    """Renders an interactive map of incidents and nearby weather."""
    if df.empty:
        print("No data to plot.")
        return

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="message",
        hover_data={
            "collection_time": True,
            "nearby_weather": True,
            "latitude": False,
            "longitude": False
        },
        zoom=10.8,
        center={"lat": 1.3521, "lon": 103.8198},  # Singapore center
        mapbox_style="open-street-map",
        title="Traffic Incidents & Nearby Weather Conditions"
    )

    fig.update_traces(marker=dict(size=12, color="red"))
    fig.update_layout(margin=dict(r=0, t=40, l=0, b=0))
    
    st.plotly_chart(fig, use_container_width=True)
    

st.set_page_config(page_title="Smart City · Operational DB", page_icon="🗄️", layout="wide")
st.title("🗄️ MongoDB")
st.caption("Dataset from data.gov.sg & Reddit")

st.header("Singapore context")
# ===========================================================================
# Aggregation pipeline with $group stage
# ===========================================================================
st.subheader("Aggregation of complaints by category")

ycol1, ycol2 = st.columns(2)
with ycol1:
    year = st.slider("Select year", min_value=2015, max_value=2025, value=2022)
with ycol2:
    st.text("")

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
    column_order = ["collection_time", "type", "incidents_count"]
    df = df[column_order]
    st.dataframe(df)

# ===========================================================================
# READ — results area with at least one filter
# ===========================================================================
st.subheader("Search traffic incident records")

tcol1, tcol2 = st.columns(2)
with tcol1:
    incident_type = st.selectbox(
        "Incident type",
        ["Accident", "Heavy Traffic", "Roadwork", "Vehicle breakdown", "Obstacle"],
    )
with tcol2:
    st.text("")

if st.button("Search", key="incident_search_button"):
    incidents = get_traffic_incidents(type=incident_type)

    if len(incidents) > 0:
        df = pd.DataFrame(incidents)

    # Extract coordinates out of the nested dictionary into distinct columns
    df["longitude"] = df["location"].apply(lambda x: x["coordinates"][0] if isinstance(x, dict) else None)
    df["latitude"] = df["location"].apply(lambda x: x["coordinates"][1] if isinstance(x, dict) else None)
    
    # Drop the raw nested dict column
    df = df.drop(columns=["location"])

    column_order = ["collection_time", "longitude", "latitude", "message"]
    df = df[column_order]
    st.dataframe(
        df.style.format({
            "latitude": "{:.4f}",
            "longitude": "{:.4f}"
        })
    )

    st.caption("Search rainfall within 3km of a traffic incident")

    df_map = enrich_incidents_with_weather(incidents)
    # As incident collection_time are only 15 mins apart, keep only the latest record per unique location/message
    df_unique = df_map.sort_values("collection_time", ascending=False).drop_duplicates(
    subset=["latitude", "longitude", "message"]
)
    plot_incidents_map(df_map)

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
