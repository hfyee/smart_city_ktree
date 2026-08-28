"""
ChromaDB helper functions called by page scripts
"""
from unittest import result
import json
import pathlib
import config
from db.utils import load
import re

import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Connect ───────────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chromadb_store")

complaints_col = client.get_or_create_collection(
    name="citizen_complaints",
    configuration={"hnsw": {"space": "cosine"}}
)

traffic_col = client.get_or_create_collection(
    name="traffic_incidents",
    configuration={"hnsw": {"space": "cosine"}}
)

weather_col = client.get_or_create_collection(
    name="weather_readings",
    configuration={"hnsw": {"space": "cosine"}}
)

KNOWN_TYPES = [
    "Accident",
    "Vehicle breakdown",
    "Roadwork",
    "Obstacle",
    "Heavy Traffic"
]

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Ready. Output dimensions: {model.get_sentence_embedding_dimension()}")

def semantic_search_complaints(query_text: str, category: str, k: int = 5) -> list[dict]:
    """Embeds the query_text with optional metadata filters and returns the top-k nearesr events."""
    filters = []  
    if category and category != "(all)":
        filters.append({"category": {"$eq": category}})

    # Construct the 'where' clause depending on how many filters are active
    if len(filters) == 0:
        where_clause = None
    elif len(filters) == 1:
        where_clause = filters[0]
    else:
        where_clause = {"$and": filters}

    result = complaints_col.query(
        query_embeddings=[model.encode(query_text).tolist()],
        where=where_clause,
        n_results=k
    )

    return list(zip(result["metadatas"][0], result["distances"][0], result["documents"][0]))

def semantic_search_traffic(query_text: str, incident_type: str, k: int = 5) -> list[dict]:
    """Embeds the query_text with optional metadata filters and returns the top-k nearest incidents."""
    filters = []  
    if incident_type and incident_type != "(all)":
        filters.append({"type": {"$eq": incident_type}})

    # Construct the 'where' clause depending on how many filters are active
    if len(filters) == 0:
        where_clause = None
    elif len(filters) == 1:
        where_clause = filters[0]
    else:
        where_clause = {"$and": filters}

    results = traffic_col.query(
        query_embeddings=[model.encode(query_text).tolist()],
        where=where_clause,
        n_results=k
    )

    return list(zip(result["metadatas"][0], results["distances"][0], results["documents"][0]))

def semantic_search_traffic_2(query_text: str, k: int = 5) -> list[dict]:
    """Embeds the query_text and returns the top-k nearest incidents."""
    # Case-insensitive search for any known type present in query_text
    matched_types = [
        t for t in KNOWN_TYPES 
        if re.search(r'\b' + re.escape(t) + r'\b', query_text, re.IGNORECASE)
    ]

    # Construct 'where' clause dynamically
    where_filter = None
    if len(matched_types) == 1:
        where_filter = {"type": matched_types[0]}
    elif len(matched_types) > 1:
        where_filter = {"type": {"$in": matched_types}}

    results = traffic_col.query(
        query_embeddings=[model.encode(query_text).tolist()],
        where=where_filter,
        n_results=k
    )

    return list(zip(results["metadatas"][0], result["distances"][0], results["documents"][0]))