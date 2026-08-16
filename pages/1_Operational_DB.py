"""Operational DB page — your third database (Task A1)."""

from unittest import result

import streamlit as st
from db.utils_mongodb import create_event, read_events, update_event_price, delete_event
from db.utils_mongodb import aggregate_events_by_category
import pandas as pd

st.set_page_config(page_title="Smart City · Operational DB", page_icon="🗄️", layout="wide")
st.title("🗄️ Operational DB")
st.caption(
    "This page is backed by YOUR chosen third database. "
    "Update the caption to say which one, and why, once you have decided."
)

# ===========================================================================
# CREATE — input form
# ===========================================================================
st.subheader("Add an event record")

with st.form("create_form", clear_on_submit=True):
    category = st.selectbox(
        "Category",
        ["music", "food", "art", "workshop", "sports", "theatre"],
    )
    title = st.text_input("Title")
    event_date = st.date_input("Date")
    event_time = st.time_input("Time", value=None)
    price = st.number_input("Price ($)", min_value=0.0, step=0.01)
    tickets = st.number_input("Available tickets", min_value=0, step=1)
    description = st.text_area("Description", height=100)
    venue_id = st.text_input("Venue ID")
    organiser_id = st.text_input("Organiser ID")
    tags = st.text_input("Tags (comma-separated)")
    submitted = st.form_submit_button("Create")

if submitted:
    record = {
        "title": title,
        "category": category,
        "date": str(event_date),
        # format time as HH:MM string without seconds for storage
        "time": str(event_time.strftime("%H:%M")),
        "price": float(price),
        "available_tickets": int(tickets),
        "description": description,
        "venue_id": venue_id,
        "organiser_id": organiser_id,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
    }
    #st.json(record)  # shows what would be inserted; remove once implemented
    new_id = create_event(record)
    st.success(f"Created record {new_id}")

st.divider()

# ===========================================================================
# READ — results area with at least one filter
# ===========================================================================
st.subheader("Browse records")

fcol1, fcol2 = st.columns(2)
with fcol1:
    filter_category = st.selectbox(
        "Filter by category",
        ["(all)", "music", "food", "art", "workshop", "sports", "theatre"],
    )
with fcol2:
    max_price = st.number_input("Max price ($)", min_value=0.0, value=50.0, step=5.0)

if st.button("Search"):
    rows = read_events(filter_category, float(max_price))
    st.dataframe(rows)

st.divider()

# ===========================================================================
# UPDATE / DELETE
# ===========================================================================
with st.expander("Update / Delete a record"):
    record_id = st.text_input("Record ID")
    ucol1, ucol2 = st.columns(2)
    with ucol1:
        new_price = st.number_input("New price ($)", min_value=0.0, step=1.0, key="upd_price")
        if st.button("Update price"):
            result = update_event_price(record_id, new_price)
            if result:
                st.success(f"Updated price for event ID: {record_id} to {new_price}")
            else:
                st.error(f"No event found with ID: {record_id} or price unchanged.")
    with ucol2:
        if st.button("Delete record", type="primary"):
            result = delete_event(record_id)
            if result:
                st.success(f"Deleted event with ID: {record_id}")
            else:
                st.error(f"No event found with ID: {record_id}")

st.divider()

# ===========================================================================
# Aggregation pipeline with $group stage
# ===========================================================================
st.subheader("Aggregation by event category")

rows = aggregate_events_by_category()
