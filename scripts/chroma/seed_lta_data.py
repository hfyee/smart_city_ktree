"""
VectorDB Seed Script (ChromaDB)
"""
import json
import pathlib
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
CHROMA_PATH     = "./chromadb_store"        # local persistence directory
COLLECTION_NAME = "traffic_incidents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"       # 384-dim; fast and accurate for short texts

DATA_DIR = pathlib.Path(__file__).parent / "../../data"

def load(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nBuilding new LTA traffic incidents collection...")
traffic_incidents = load("lta_traffic_incidents_14hrs_15min.json")

# ── Initialise ChromaDB client ────────────────────────────────────────────────
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Drop and recreate collection for a clean seed (remove this block to upsert only)
try:
    client.delete_collection(COLLECTION_NAME)
    print(f"  Existing collection '{COLLECTION_NAME}' dropped.")
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}      # cosine distance for text similarity
)
print(f"  Collection '{COLLECTION_NAME}' created.")

# Flatten documents, metadata, and IDs
documents = []
metadatas = []
ids = []

for batch_idx, batch in enumerate(traffic_incidents):
    collection_no = batch.get("collection_number")
    collection_time = batch.get("collection_time", "")
    
    for inc_idx, incident in enumerate(batch.get("traffic_incidents", [])):
        # Unique ID per incident
        doc_id = f"col_{collection_no}_inc_{inc_idx}"
        
        # Text to be embedded
        doc_text = incident.get("Message", "")
        
        # Flattened metadata (Chroma requires primitive types)
        metadata = {
            "collection_number": collection_no,
            "collection_time": collection_time,
            "type": incident.get("Type", ""),
            "latitude": float(incident.get("Latitude", 0.0)),
            "longitude": float(incident.get("Longitude", 0.0))
        }
        
        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(doc_id)

print(f"  Loading embedding model: {EMBEDDING_MODEL} ...")
model = SentenceTransformer(EMBEDDING_MODEL)
embeddings = model.encode(documents, show_progress_bar=True).tolist()

# Upsert into ChromaDB
collection.upsert(
    ids=ids,    
    documents=documents,
    embeddings=embeddings,    
    metadatas=metadatas,
)

print(f"\nDone. {collection.count()} documents indexed in '{COLLECTION_NAME}'.")

# ── Quick smoke test ──────────────────────────────────────────────────────────
s1 = "Slow moving traffic along PIE"
print(f"\nSample query: {s1}")
query_embedding = model.encode([s1]).tolist()
results = collection.query(
    query_embeddings=query_embedding,
    n_results=3,
    include=["documents", "metadatas", "distances"],
)
for i, (doc, meta, dist) in enumerate(zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0],
)):
    print(f"  {i+1}. [{meta['collection_time']}] {meta['type']}   {doc}   (distance: {dist:.4f})")
