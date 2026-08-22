"""
CityBuzz — Streamlit Frontend Template
Advanced Data Management · Assignment 1

This is the provided frontend skeleton. It runs as-is, but every database
operation is a placeholder: your job is to replace the marked TODO blocks
with calls to your own functions.

Run it with:
    streamlit run app.py

Project structure:
    app.py                  <- this file (Home page)
    pages/                  <- one page per database layer + the pipeline page
    db/connections.py       <- put your database connection code here
    requirements.txt        <- add your drivers; pin versions before submission
"""

import streamlit as st
from PIL import Image
from db.connections import get_mongo_client, get_neo4j_driver, get_chroma_collection

# Initialize session state
st.session_state["mongo_user"] = ""
st.session_state["mongo_password"] = ""

img = Image.open("pages/images/smart-city.png")

st.set_page_config(page_title="KTree", page_icon="🎟️", layout="wide")
col1, col2 = st.columns([1, 10])

with col1:
        st.image(img, width='content')

with col2:
    st.title("Smart City Knowledge Tree Project")
    st.caption("Brought to you by Group 1.")

st.markdown(
    """
Use the sidebar to navigate:

| Page | Database layer |
|---|---|
| Operational DB | MongoDB |
| Graph Explorer | Neo4j |
| Semantic Search | ChromaDB |
| Pipeline | All three (integration pipeline) |
"""
)

with st.sidebar:
    with st.form("mongo_login_form", clear_on_submit=True):
        mongo_user_input = st.text_input("MongoDB username")
        mongo_password_input = st.text_input("MongoDB password", type="password")
        submitted = st.form_submit_button("Enter")

st.divider()
st.subheader("Connection status")

col1, col2, col3 = st.columns(3)
with col1:
    if submitted:
        st.session_state["mongo_user"] = mongo_user_input
        st.session_state["mongo_password"] = mongo_password_input
        if get_mongo_client() is not None:
            st.success("Operational DB — connected")
        else:
            st.error("Operational DB — not connected")
with col2:
    if get_neo4j_driver() is not None:
        st.success("Neo4j — connected")
    else:
        st.error("Neo4j — not connected")
with col3:
    if get_chroma_collection() is not None:
        st.success("VectorDB — connected")
    else:
        st.error("VectorDB — not connected")

#st.info(
#    "Reminder: all CRUD operations must run through your own application code. "
#    "The provided seed scripts are for initial data loading only."
#)
