"""Graph Explorer page — Neo4j (Task A2)."""

import streamlit as st
from db.utils import load
from db.utils_neo4j import create_venue, create_organiser, create_event
from db.utils_neo4j import read_who_what_where, update_available_tickets, delete_event
from db.utils_neo4j import add_booking_relationship, find_booking_info
from db.utils_neo4j import find_events_by_organisers_at_same_venue
from db.utils_neo4j import build_network_graph, community_detection
import networkx as nx
import pandas as pd

st.set_page_config(page_title="Smart City · Graph Explorer", page_icon="🕸️", layout="wide")
st.title("🕸️ Graph Explorer")
st.caption("Backed by Neo4j — relationships between events, venues, and organisers.")

# ===========================================================================
# CREATE — input form
# ===========================================================================
st.subheader("Events")

with st.expander("Add a venue record"):
    with st.form("create_venue_form", clear_on_submit=True):
        venue_type = st.selectbox(
            "Type",
            ["indoor", "outdoor"],
        )
        venue_name = st.text_input("Name")
        venue_address = st.text_input("Address")
        venue_neighbourhood = st.text_input("Neighbourhood")
        venue_capacity = st.number_input("Capacity", min_value=100, step=20)
        # venue_id is auto-generated
        #venue_id = st.text_input("Venue ID")
        submitted = st.form_submit_button("Create")

    if submitted:
        record = {
            "name": venue_name,
            "type": venue_type,
            "capacity": int(venue_capacity),
            "address": venue_address,
            "neighbourhood": venue_neighbourhood,
            #"venue_id": venue_id,
        }
        #st.json(record)  # shows what would be inserted; remove once implemented
        new_id = create_venue(record)
        st.success(f"Created record {new_id}")

with st.expander("Add an organiser record"):
    with st.form("create_organiser_form", clear_on_submit=True):
        organiser_specialisation = st.selectbox(
            "Specialisation",
            ["art_theatre",  "digital_art", "performing_arts", "theatre_performance",
            "heritage_culture", "heritage_food",
            "food", "food_innovation", "food_sustainability", 
            "sports_fitness", "fitness_wellness", "running_endurance", 
            "maker_workshops", "workshops_education", "tech_coding", 
            "children_family", "outdoor_nature",
            "music", "music_entertainment", 
            "nightlife_events"]
        )
        organiser_name = st.text_input("Name")
        organiser_email = st.text_input("Email")
        organiser_phone = st.text_input("Phone")
        organiser_founded_year = st.number_input("Year", min_value=1900, step=1)
        # organiser_id is auto-generated
        #organiser_id = st.text_input("Organiser ID")
        submitted = st.form_submit_button("Create")

    if submitted:
        record = {
            "name": organiser_name,
            "email": organiser_email,
            "phone": organiser_phone,
            "specialisation": organiser_specialisation,
            "founded_year": int(organiser_founded_year),
            #"organiser_id": organiser_id,
        }
        #st.json(record)  # shows what would be inserted; remove once implemented
        new_id = create_organiser(record)
        st.success(f"Created record {new_id}")

with st.expander("Add an event record"):
    with st.form("create_event_form", clear_on_submit=True):
        event_category = st.selectbox(
            "Category",
            ["music", "food", "art", "workshop", "sports", "theatre"],
        )
        event_title = st.text_input("Title")
        event_date = st.date_input("Date")
        event_time = st.time_input("Time", value=None)
        event_price = st.number_input("Price ($)", min_value=0.0, step=0.01)
        event_tickets = st.number_input("Available tickets", min_value=0, step=1)
        event_description = st.text_area("Description", height=100)
        venue_id = st.text_input("Venue ID")
        organiser_id = st.text_input("Organiser ID")
        tags = st.text_input("Tags (comma-separated)")
        submitted = st.form_submit_button("Create")

    if submitted:
        record = {
            "title": event_title,
            "category": event_category,
            "date": str(event_date),
            "time": str(event_time.strftime("%H:%M")),
            "price": float(event_price),
            "available_tickets": int(event_tickets),
            "description": event_description,
            "venue_id": venue_id,
            "organiser_id": organiser_id,
            "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        }
        #st.json(record)  # shows what would be inserted; remove once implemented
        new_id = create_event(record)
        st.success(f"Created record {new_id}")

# ===========================================================================
# UPDATE / DELETE
# ===========================================================================
with st.expander("Update / Delete an event"):
    record_id = st.text_input("Event ID")
    ucol1, ucol2 = st.columns(2)
    with ucol1:
        new_available_tickets = st.number_input("New available tickets", min_value=0, step=1, key="upd_available_tix")
        new_available_tickets = int(new_available_tickets)
        if st.button("Update available ticket count"):
            result = update_available_tickets(record_id, new_available_tickets)
            if result:
                st.success(f"Updated available tickets for event ID: {record_id} to {new_available_tickets}")
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
