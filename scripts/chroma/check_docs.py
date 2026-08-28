"""
ChromaDB test script to check documents in a collection 
"""
from unittest import result

import chromadb
from pprint import pprint
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chromadb_store")

complaints_col = client.get_collection(
    name="citizen_complaints",
)
traffic_col = client.get_collection(
    name="traffic_incidents",
)

model = SentenceTransformer("all-MiniLM-L6-v2")

# collection.get() method does not natively support sorting or descending ordering.
def get_event_by_id(event_id: str) -> dict:
    """Query collection using metadata filter alone."""
    result = complaints_col.get(
        ids=[event_id],
    )

    return result["metadatas"][0] if result["metadatas"] else None

def get_event_by_title(event_title: str) -> list[dict]:
    """Query collection using metadata filter alone."""
    result = complaints_col.get(
        where={"title": {"$eq": event_title}},
        #where_document={"$contains": event_title},
        limit=3
    )

    return result["metadatas"] if result["metadatas"] else None

def get_last_record_info() -> dict:
    chroma_ids = set(complaints_col.get(include=[])["ids"])
    last_value = sorted(chroma_ids)[-1]
    print (f"Highest event id: {last_value}")

    return(get_event_by_id(last_value))


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

if __name__ == '__main__':
    print(f"Citizen Complaints collection count: {complaints_col.count()}")
    print(f"Traffic Incidents collection count: {traffic_col.count()}")
    print()

    if True:
        print(f"Fetching document for the last event_id...")
        pprint(get_last_record_info())
        print()
    
    if True:
        s1 = "heavy rain and flooded carparks"
        print(f"\nSample query: {s1}")
        print()
        for i, (meta, dist, doc) in enumerate(semantic_search_complaints(s1, "(all)")):
            print(f"  {i+1}. {meta['complaint_id']} {meta['category']}   {doc}   (distance: {dist:.4f})")
        print()

    if False:
        event_title = "Hiroshi Sugimoto: Form Is Emptiness"
        #event_title = "hawker"
        print(f"Fetching document for event_title '{event_title}'...")
        cursor = get_event_by_title(event_title)
        if cursor:
            for doc in cursor:
                pprint(doc)
                print()
