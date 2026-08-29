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
from db.utils_chromadb import semantic_search_traffic

def plot_complaints_piechart(data: list[dict]):
    """Renders a simplified Plotly pie chart directly in Streamlit."""
    if not data:
        st.warning("No complaint data to display.")
        return

    df = pd.DataFrame(data)
    
    fig = px.pie(
        df,
        names="category",
        values="complaints_count",
        title="Citizen Complaints by Category"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    
    st.plotly_chart(fig, width='stretch')

def plot_traffic_incidents_piechart(data: list[dict]):
    """Renders a simplified Plotly pie chart directly in Streamlit."""
    if not data:
        st.warning("No traffic incidents data to display.")
        return

    df = pd.DataFrame(data)
    
    fig = px.pie(
        df,
        names="type",
        values="incidents_count",
        title="Traffic Incidents by Type"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    st.plotly_chart(fig, width='stretch')


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
    
    st.plotly_chart(fig, width='stretch')
    

st.set_page_config(page_title="Smart City · Operational DB", page_icon="🗄️", layout="wide")
st.title("🗄️ MongoDB")
st.caption("Datasets from data.gov.sg & Reddit")

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

aggccol1, aggccol2 = st.columns(2)

with aggccol1:
    if len(rows) > 0:
        df = pd.DataFrame(rows)
        column_order = ["category", "complaints_count", "earliest_date", "latest_date"]
        df = df[column_order]
        # vertical offset to align with the piechart
        st.markdown('<div style="margin-top: 75px;"></div>', unsafe_allow_html=True)
        st.dataframe(df)

with aggccol2:
    plot_complaints_piechart(rows)
    
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

aggtcol1, aggtcol2 = st.columns(2)

with aggtcol1:
    if len(rows) > 0:
        df = pd.DataFrame(rows)
        column_order = ["collection_time", "type", "incidents_count"]
        df = df[column_order]
        # vertical offset to align with the piechart
        st.markdown('<div style="margin-top: 75px;"></div>', unsafe_allow_html=True)
        st.dataframe(df)

with aggtcol2:
    plot_traffic_incidents_piechart(rows)

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

    if incidents:
        df = pd.DataFrame(incidents)

        if "location" in df.columns:
            df["longitude"] = df["location"].apply(
                lambda x: x.get("coordinates", [None, None])[0] if isinstance(x, dict) else None
            )
            df["latitude"] = df["location"].apply(
                lambda x: x.get("coordinates", [None, None])[1] if isinstance(x, dict) else None
            )
            # Safely drop location
            df = df.drop(columns=["location"], errors="ignore")
        else:
            df["longitude"] = None
            df["latitude"] = None
            st.info("[Warning] No 'location' column in dataframe.")

        # Keep only the row with the latest collection_time for each unique combination of lon, lat, and message
        df = (
            df.sort_values("collection_time", ascending=False)
            .drop_duplicates(subset=["longitude", "latitude", "message"], keep="first")
            .reset_index(drop=True)
        )

        # Filter/reorder only columns that actually exist
        column_order = [col for col in ["collection_time", "longitude", "latitude", "message"] if col in df.columns]
        df = df[column_order]

        # Format numeric coordinates safely
        format_dict = {}
        if "latitude" in df.columns:
            format_dict["latitude"] = lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A"
        if "longitude" in df.columns:
            format_dict["longitude"] = lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A"

        st.dataframe(df.style.format(format_dict))
    else:
        st.info("No traffic incidents found for the selected type.")

    st.caption("Search rainfall within 3km of traffic incident")

    df_map = enrich_incidents_with_weather(incidents)
    # As incident collection_time are only 15 mins apart, keep only the latest record per unique location/message
    df_unique = df_map.sort_values("collection_time", ascending=False).drop_duplicates(
    subset=["latitude", "longitude", "message"]
)
    plot_incidents_map(df_map)

st.divider()

# ===========================================================================
# Hybrid Search
# ===========================================================================
st.subheader("Hybrid Search for traffic incidents")

st.caption("Ask about the current traffic situation — in your own words.")

query_text = st.text_input(
    "Search",
    placeholder="why is traffic slow on the PIE?",
    label_visibility="collapsed",
)

k = st.slider("Number of results", min_value=1, max_value=10, value=3)

if st.button("Search", key="hybrid_search_button") and query_text:
    with st.container(border=True):
        for i, (meta, dist, doc) in enumerate(semantic_search_traffic(query_text, incident_type, k), start=0):
            # Use .get() method with default value in case of any missing key
            type = meta.get('type', 'Uncategorized')
            latitude = meta.get('latitude', '')
            longitude = meta.get('longitude', '')
            description = doc

            st.subheader(type)
            st.caption(description)
            st.metric("Lat", f"{latitude:.4f}")
            st.metric("Lon", f"{longitude:.4f}")            
            st.metric("Distance", f"{dist:.4f}")
            st.divider()

