"""
VectorDB Seed Script (ChromaDB)
"""
import json
import pathlib
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
CHROMA_PATH     = "./chromadb_store"        # local persistence directory
COLLECTION_NAME = "citizen_complaints"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"       # 384-dim; fast and accurate for short texts

DATA_DIR = pathlib.Path(__file__).parent / "../../data"

def load(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nBuilding new Reddit citizen complaints collection...")
citizen_complaints = load("singapore_citizen_complaints_2015_2025_v2.json")

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

# ── Generate embeddings ────────────────────────────────────────────────────────
print(f"  Loading embedding model: {EMBEDDING_MODEL} ...")
model = SentenceTransformer(EMBEDDING_MODEL)

documents  = [c["complaint_text"] for c in citizen_complaints]
ids        = [c["complaint_id"] for c in citizen_complaints]
metadatas  = [
    {
        "complaint_id":  c["complaint_id"],
        "category":      c["category"],
        "date_posted":   c["date_posted"],
        "location":      c["location"],
        "user_name":     c["user_name"],
        #"tags":         ", ".join(e["tags"]),   # ChromaDB metadata must be str/int/float
    }
    for c in citizen_complaints
]

print(f"  Generating embeddings for {len(documents)} events...")
embeddings = model.encode(documents, show_progress_bar=True).tolist()

# ── Add to collection ─────────────────────────────────────────────────────────
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
)

print(f"\nDone. {collection.count()} documents indexed in '{COLLECTION_NAME}'.")

# ── Quick smoke test ──────────────────────────────────────────────────────────
s1 = "heavy rain and flooded carparks"
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
    print(f"  {i+1}. [{meta['complaint_id']}] {meta['category']}   {doc}   (distance: {dist:.4f})")
