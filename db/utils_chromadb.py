"""
ChromaDB helper functions called by page scripts
"""
from unittest import result
import json
import pathlib
import config
from utils import load
import re

import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Connect ───────────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chromadb_store")

collection = client.get_or_create_collection(
    name="citybuzz_events",
    configuration={"hnsw": {"space": "cosine"}}
)

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Ready. Output dimensions: {model.get_sentence_embedding_dimension()}")

# ── CRUD operations ───────────────────────────────────────────────────────
def get_next_event_id() -> str:
    ...
    
def add_event(e: dict) -> str:
    ...
    
def search_events(query_text: str, category: str, max_price: float, k: int = 5) -> list[dict]:
    ...

def get_vector_collections_count() -> int:
    return collection.count()

def update_event_description(event_id: str, new_description: str) -> bool:
    ...

def delete_event(event_id: str) -> int:
    ...