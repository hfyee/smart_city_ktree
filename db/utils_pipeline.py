"""
Cross-DB write and audit functions called by 'Pipeline' page
Based on template from HF's citybuzz project code
"""
from unittest import result
import json
import pathlib
import config
from db.utils import load, pseudonymise
from db.connections import get_mongo_client, get_neo4j_driver
from pymongo import ReturnDocument
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Store 1 (PRIMARY): MongoDB, system of record ---
mongo_client = get_mongo_client()
db = mongo_client[config.MONGO_DB] if mongo_client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")
mongo_complaints = db["citizen_complaints"]

# --- Store 2 (derived): ChromaDB, semantic layer --
chroma_client = chromadb.PersistentClient(path="./chromadb_store")
print("ChromaDB connected")

chroma_complaints = chroma_client.get_or_create_collection(
    name="citizen_complaints",
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
# Audit: compare the derived stores against the primary for citizen complaints
# Detects and repairs any drift.
# ---------------------------------------------------------------
def reconcile() -> dict:
    """Audit both derived stores against the primary; repair any drift."""
    mongo_ids  = {d["complaint_id"] for d in mongo_complaints.find({}, {"complaint_id": 1})}
    chroma_ids = set(chroma_complaints.get(include=[])["ids"])
    records, _, _ = neo4j_driver.execute_query("MATCH (c:Complaint) RETURN c.complaint_id AS id")
    neo4j_ids  = {r["id"] for r in records}

    report = {"checked": len(mongo_ids)}

    # --- vector layer vs primary ---
    print("Comparing vector layer vs primary...")
    missing = mongo_ids - chroma_ids

    if missing:
        print("Found in primary, not in derived")
        for eid in sorted(missing):
            write_vector(mongo_complaints.find_one({"complaint_id": eid}))
            report.setdefault("vector_repaired", []).append(eid)

    orphans = chroma_ids - mongo_ids

    if orphans:
        print("Found in derived, not in primary")
        chroma_complaints.delete(ids=list(orphans))
        report["vector_orphans_removed"] = sorted(orphans)

    # --- graph layer vs primary ---
    print("Comparing graph layer vs primary...")
    missing = mongo_ids - neo4j_ids

    if missing:
        print("Found in primary, not in derived")
        for eid in sorted(missing):
            write_graph(mongo_complaints.find_one({"complaint_id": eid}))
            report.setdefault("graph_repaired", []).append(eid)

    orphans = neo4j_ids - mongo_ids

    if orphans:
        print("Found in derived, not in primary")
        for eid in sorted(orphans):
            neo4j_driver.execute_query(
                "MATCH (e:Complaint {complaint_id: $id}) DETACH DELETE e", id=eid)
            report.setdefault("graph_orphans_removed", []).append(eid)

    return report

# ---------------------------------------------------------------
# Read from all 3 layers 
# 1. ChromaDB (catalogue) — which complaints, how similar: ranked entry-point IDs.
# 2. MongoDB (warehouse) — the authoritative record for each hit. 
# 3. Neo4j (map) — graph traversal for context per hit: what other complaints at the same locations.
# ---------------------------------------------------------------
def search_complaints(query_text: str, category: str, k: int = 3) -> list[dict]:
    """Three-layer read journey: vector → operational → graph."""
    # LAYER 1 — semantic entry points (vector store)
    query_embedding = model.encode(query_text).tolist()
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

    res = chroma_complaints.query(
        query_embeddings=[query_embedding], 
        where=where_clause,
        n_results=k
    )

    hit_ids = res["ids"][0]
    #print(f"ChromaDB: hit_ids: {hit_ids}")

    # LAYER 2 — authoritative records (operational store), ranking preserved
    docs = mongo_complaints.find({"complaint_id": {"$in": hit_ids}}, {"_id": 0})
    by_id = {d["complaint_id"]: d for d in docs}
    ordered = [by_id[i] for i in hit_ids if i in by_id]
    #print(f"MongoDB: ordered_ids: {ordered}")

    # LAYER 3 — graph context, one traversal per hit
    # HF: below cypher sample from ITG202/CityBuzz
    results = []
    for ev in ordered:
        records, _, _ = neo4j_driver.execute_query(
            """
            MATCH (e:Event {event_id: $event_id})-[:HELD_AT]->(v:Venue)
            OPTIONAL MATCH (v)<-[:HELD_AT]-(other:Event)
            WHERE other.event_id <> $event_id
            RETURN v.name AS venue, collect(other.title)[..3] AS also_at_venue
            """,
            event_id=ev["event_id"],
        )
        ctx = records[0] if records else {"venue": None, "also_at_venue": []}
        results.append({**ev, "venue_context": ctx["venue"],
                        "also_at_venue": ctx["also_at_venue"]})
    #print(f"Neo4j: no. of results: {len(results)}")
    return results  
