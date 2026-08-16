"""Semantic Search page — VectorDB (Task A3)."""

import streamlit as st
from db.utils_chromadb import add_event, search_events
from db.utils_chromadb import update_event_description, delete_event

st.set_page_config(page_title="Smart City · Semantic Search", page_icon="🔎", layout="wide")
st.title("🔎 Semantic Search")

# ===========================================================================
# CREATE — input form
# ===========================================================================
with st.expander("Add an event description for embedding"):
    with st.form("add_event_form", clear_on_submit=True):
        category = st.selectbox(
            "Category",
            ["music", "food", "art", "workshop", "sports", "theatre"],
        index=0,)
        title = st.text_input("Title")
        event_date = st.date_input("Date")
        price = st.number_input("Price ($)", min_value=0.0, step=0.01)
        description = st.text_area("Description", height=100)
        tags = st.text_input("Tags (comma-separated)")
        submitted = st.form_submit_button("Add")

    if submitted:
        record = {
            "title": title,
            "category": category,
            "date": str(event_date),
            # format time as HH:MM string without seconds for storage
            "price": float(price),
            "description": description,
            "tags": tags
        }
        #st.json(record)  # shows what would be inserted; remove once implemented
        new_id = add_event(record)
        st.success(f"Added record {new_id}")

st.divider()

# ===========================================================================
# Hybrid Search
# ===========================================================================
st.subheader("Hybrid Search for events")

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

k = st.slider("Number of results", min_value=1, max_value=10, value=5)

    # ---------------------------------------------------------------------------
    # Section B note: hybrid search adds metadata filters alongside the vector
    # query (e.g. category, price, availability). Add the filter widgets here
    # when you implement it.
    # ---------------------------------------------------------------------------

if st.button("Search", type="primary") and query_text:
    # -----------------------------------------------------------------------
    # (Task A3): embed the query text and run a k-NN search against
    # your collection.
    #
    # Render each hit as a card: title, category, price, and the matching
    # description text. st.container(border=True) works well for cards.
    with st.container(border=True):
        for i, (meta, dist, doc) in enumerate(search_events(query_text, filter_category, max_price, k), start=0):
            # Use .get() method with default value in case of any missing key
            title = meta.get('title', 'Untitled')
            category = meta.get('category', 'Uncategorized')
            date = meta.get('date', 'N/A')
            price = meta.get('price', 0)
            #description = doc[:200]
            description = doc

            #st.write(f"#{i+1} dist={dist:.4f} title={title} | category={category} | price=${price:.2f} | description={description}")
            st.subheader(title)
            st.metric("Category", category)
            st.metric(label="Price", value=price, format="dollar")
            st.caption(description)
            st.metric("Distance", f"{dist:.4f}")
            st.divider()

    # -----------------------------------------------------------------------

st.divider()

# ===========================================================================
# UPDATE / DELETE
# ===========================================================================
with st.expander("Update / Delete an event"):
    record_id = st.text_input("Event ID")
    ucol1, ucol2 = st.columns(2)
    with ucol1:
        new_description = st.text_area("Description", height=100)
        if st.button("Re-embed"):
            result = update_event_description(record_id, new_description)
            if result:
                st.success(f"Re-embedded event with ID: {record_id}")
            else:
                st.error(f"No event found with ID: {record_id}")


    with ucol2:
        if st.button("Delete record", type="primary"):
            result = delete_event(record_id)
            st.write(f"Deleted record with id: {record_id}")
