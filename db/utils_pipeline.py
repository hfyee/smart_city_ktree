"""
Cross-DB write functions called by 'Add Event' page
Assumes that the primary store is already seeded with venue and vendor data 
NB. driver.execute_query() returns an EagerResult object, which does not have a .single() method
"""
from unittest import result
import json
import pathlib
import config
from utils import load, pseudonymise
from db.connections import get_mongo_client
from pymongo import ReturnDocument
from db.connections import get_neo4j_driver
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Store 1 (PRIMARY): MongoDB, system of record ---
mongo_client = get_mongo_client()
db = mongo_client[config.MONGO_DB] if mongo_client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")
mongo_events = db["events"]

# --- Store 2 (derived): ChromaDB, semantic layer --
chroma_client = chromadb.PersistentClient(path="./chromadb_store")
print("ChromaDB connected")

chroma_events = chroma_client.get_or_create_collection(
    name="citybuzz_events",
    configuration={"hnsw": {"space": "cosine"}}
)
print("ChromaDB collection ready")

# --- Store 3 (derived): Neo4j, relationship layer ---
neo4j_driver = get_neo4j_driver()
neo4j_driver.verify_connectivity()
print("Neo4j connected")

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Ready. Output dimensions: {model.get_sentence_embedding_dimension()}")

# Lookup dictionaries for denormalisation
# In a production system, they would be retrieved from separate db collections
venues = load("venues.json")
venues.extend(load("venues_new.json"))
organisers = load("organisers.json")
organisers.extend(load("organisers_new.json"))
venue_map = {v["venue_id"]: v for v in venues}
organiser_map = {o["organiser_id"]: o for o in organisers}

def get_next_event_id() -> str:
    ...

# ── CRUD operations ────────────────────────────────────────────
# ---------------------------------------------------------------
# One writer per store
# ---------------------------------------------------------------
def write_operational(new_event: dict, new_event_id: str) -> None:
    ...

def write_vector(new_event: dict, new_event_id: str) -> None:
    ...

def write_graph(new_event: dict, new_event_id: str) -> None:
    ...

def get_mongo_documents_count() -> int:
    ...

def get_vector_collections_count() -> int:
    ...

def get_graph_nodes_count() -> int:
    ...
    
# ---------------------------------------------------------------
# Cross-DB write
# ---------------------------------------------------------------
def create_event(new_event: dict) -> str:
    ...

# ---------------------------------------------------------------
# Cross-DB delete
# ---------------------------------------------------------------
def delete_event(event_id: str) -> str:
    ...

# ---------------------------------------------------------------
# Audit: compare the derived stores against the primary
# Detects and repairs any drift.
# ---------------------------------------------------------------
def reconcile() -> dict:
    ...

# ---------------------------------------------------------------
# Read from all 3 layers 
# 1. ChromaDB (catalogue) — which events, how similar: ranked entry-point IDs.
# 2. MongoDB (warehouse) — the authoritative record for each hit. 
# 3. Neo4j (map) — graph traversal for context per hit: what other events at the venue.
# ---------------------------------------------------------------
def search_events(query_text: str, category: str, max_price: float, k: int = 3) -> list[dict]:
    ...
    