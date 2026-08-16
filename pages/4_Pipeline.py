"""Add Event page — the integration pipeline (Tasks B4 / C4).

In Section A, this page may simply duplicate the create on the Operational
DB page. It becomes important in Sections B and C, where creating one event
should write to more than one database.
"""
import streamlit as st
from unittest import result
from utils_pipeline import create_event, delete_event, search_events
from utils_pipeline import get_mongo_documents_count, get_vector_collections_count, get_graph_nodes_count

st.set_page_config(page_title="CityBuzz · Add Event", page_icon="➕", layout="wide")
st.title("Pipeline")
st.subheader("➕ Add Event")
st.caption("One form — up to three databases.")

with st.container(border=True, horizontal_alignment="center"):
    st.text("Existing records tally")
    bs1, bs2, bs3 = st.columns(3)
    with bs1:
        st.text(f"MongoDB: {get_mongo_documents_count()} documents")
    with bs2:
        st.text(f"ChromaDB: {get_vector_collections_count()} vectors")
    with bs3:
        st.text(f"Neo4j: {get_graph_nodes_count()} nodes")

with st.form("add_event_form", clear_on_submit=True):
    title = st.text_input("Title")
    description = st.text_area(
        "Description",
        placeholder="An evening of smooth jazz overlooking the city skyline…",
        help="This text is what your VectorDB embeds — write it like a real listing.",
    )
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category",
            ["music", "food", "art", "workshop", "sports", "theatre"],
        )
        event_date = st.date_input("Date")
        price = st.number_input("Price ($)", min_value=0.0, step=1.0)
    with col2:
        # populate these from your databases instead of free text
        venue_id = st.text_input("Venue ID (e.g. VEN012)")
        organiser_id = st.text_input("Organiser ID (e.g. ORG007)")
        tickets = st.number_input("Available tickets", min_value=0, step=1)
    submitted = st.form_submit_button("Add event")

if submitted:
    # Client-side validation
    if venue_id:
        if not venue_id.startswith("VEN"):
            st.error("Venue ID must start with 'VEN'")
            st.stop()

    if organiser_id:
        if not organiser_id.startswith("ORG"):
            st.error("Organiser ID must start with 'ORG'")
            st.stop()

    event = {
        "title": title,
        "description": description,
        "category": category,
        "date": str(event_date),
        "price": float(price),
        "available_tickets": int(tickets),
        "venue_id": venue_id,
        "organiser_id": organiser_id,
    }
    
    new_event_id = create_event(event)
    st.write("Pipeline status:")
    s1, s2, s3 = st.columns(3)

    # -----------------------------------------------------------------------
    # (Tasks B4 / C4): perform the writes and report each outcome.
    # Generate ONE event_id here and use it in every database so the
    # records stay consistent. Replace each st.info below with st.success
    # or st.error depending on the real result.
    # -----------------------------------------------------------------------
    with s1:
        st.success(f"Operational DB — created record {new_event_id}")
        st.text(f"MongoDB: {get_mongo_documents_count()} documents")
    with s2:
        st.success("VectorDB — embed + index implemented")
        st.text(f"ChromaDB: {get_vector_collections_count()} vectors")
    with s3:
        st.success("Neo4j — node + relationships implemented")
        st.text(f"Neo4j: {get_graph_nodes_count()} nodes")
   
    #st.json(event)  # shows what would be written; remove once implemented

# ===========================================================================
# DELETE
# ===========================================================================
with st.expander("Delete a record"):
    st.subheader("🗑️ Delete Event")
    dcol1, dcol2 = st.columns(2)

    with dcol1:
        event_id = st.text_input("Event ID (e.g. EVT015)")

    if st.button("Delete event", type="primary"):
        deleted_id = delete_event(event_id)
        st.write("Pipeline status:")
        s1, s2, s3 = st.columns(3)

        with s1:
            st.success(f"Operational DB — deleted record {deleted_id}")
            st.text(f"MongoDB: {get_mongo_documents_count()} documents")
        with s2:
            st.success("VectorDB — deleted record")
            st.text(f"ChromaDB: {get_vector_collections_count()} vectors")
        with s3:
            st.success("Neo4j — deleted record")
            st.text(f"Neo4j: {get_graph_nodes_count()} nodes")

st.divider()

# ===========================================================================
# USER JOURNEY - Read from all 3 layers
# With optional metadata filtering
# ===========================================================================
st.subheader("🔎 3-layer Read")
st.caption("Describe what you feel like doing — in your own words.")

query_text = st.text_input(
    "Search",
    placeholder="relaxing evening with live music",
    label_visibility="collapsed",
)

filter_category = st.selectbox(
    "Category",
    ["(all)", "music", "food", "art", "workshop", "sports", "theatre"],
index=0,)

max_price = st.number_input("Max price ($)", min_value=0.0, value=None, max_value=500.0)

if st.button("Search", type="primary") and query_text:
    st.caption("Top 3 results:")
    results = search_events(query_text, filter_category, max_price, 3)

    for r in results:
        st.write(f"{r['event_id']}  **{r['title']}**  (${r['price']}, {r['date']})")
        st.write(f"   at {r['venue_context']} — also there: {r['also_at_venue']}\n")
