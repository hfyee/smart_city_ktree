"""
Database connection helpers — CityBuzz template.

All connection logic lives here so pages can share it. Streamlit re-runs
page scripts on every interaction, so clients are wrapped in
@st.cache_resource to create them once per session.

Edit config.py (in the project root) to set your credentials.
"""
import streamlit as st
import sys
import os
import urllib.parse
from pymongo import MongoClient

# Make config.py importable from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

@st.cache_resource
def get_mongo_client():
    """Return a connected MongoDB client, or None on failure."""    
    user = urllib.parse.quote_plus(config.MONGO_USER)
    pwd = urllib.parse.quote_plus(config.MONGO_PASSWORD)
    
    uri = (
        f"mongodb://{user}:{pwd}@"
        f"{config.MONGO_HOST}:{config.MONGO_PORT}/{config.MONGO_DB}?"
        f"authSource={getattr(config, 'MONGO_AUTH_DB', 'admin')}"
    )
    
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    # Force a network call to verify credentials and server reachability immediately
    client.admin.command("ping")
    return client

def get_mongo_db():
    """Return the citybuzz database handle, or None if not connected."""
    client = get_mongo_client()
    return client[config.MONGO_DB] if client else None


@st.cache_resource
def get_neo4j_driver():
    """Return a connected Neo4j driver, or None on failure."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        return driver
    except Exception as e:
        st.error(f"Neo4j connection failed: {e}")
        return None


@st.cache_resource
def get_chroma_collection():
    """Return the ChromaDB collection, or None on failure."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        return client.get_or_create_collection(config.CHROMA_COLLECTION)
    except Exception as e:
        st.error(f"ChromaDB connection failed: {e}")
        return None


@st.cache_resource
def get_embedding_model():
    """Return the sentence-transformers embedding model.

    Loading takes a few seconds the first time — caching means it only
    happens once per session.
    """
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        st.error(f"Embedding model failed to load: {e}")
        return None
