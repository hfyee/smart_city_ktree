"""
MongoDB test script to check documents in a collection 
"""
import json
import pathlib
import config
from db.connections import get_mongo_client
from pymongo import ASCENDING, DESCENDING
from db.utils import mask_name
from pprint import pprint

client = get_mongo_client()
db = client[config.MONGO_DB] if client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")

complaints_collection = db["citizen_complaints"]
traffic_collection = db["traffic_sensors"]
weather_collection = db["weather_data"]

def get_complaint_by_id(event_id: str) -> list:
    """Reads events with optional filters. Returns a list of event documents."""
    query = {"complaint_id": event_id}
    return list(complaints_collection.find(query))

def get_last_complaint_id_wo_incr() -> str:
    """Returns the next complaint id without incrementing the counter."""
    counter = db.counters.find_one({"_id": "event_id"})
    seq_number = counter["seq"] if counter else 1
    return f"COMP_{seq_number:06d}"

if __name__ == '__main__':
    if True:
        print(f"Number of documents in complaints collection: {complaints_collection.count_documents({})}")
        print()
        print("Last document inserted:")
        cursor = complaints_collection.find({}).sort("complaint_id", DESCENDING).limit(1)
        for document in cursor:
            pprint(document)
            print()
        print()

    if False:
        cursor = users_collection.find({}).sort("user_id", DESCENDING).limit(2)

        # Iterate and mask the name field before displaying
        for doc in cursor:
            if "name" in doc:
                doc["name"] = mask_name(doc["name"])
            pprint(doc)
            print()

    if False:
        # Find all documents missing an event_id or where event_id is None
        bad_docs = list(complaints_collection.find({
            "$or": [
                {"complaint_id": None},
                {"complaint_id": {"$exists": False}}
            ]
        }))

        print(f"Found {len(bad_docs)} documents without a valid complaint_id.")

        if len(bad_docs) > 0:
            print("Documents without event_id:")
            for doc in bad_docs:
                pprint(doc)
            complaints_collection.delete_many({"$or": [{"event_id": None}, {"event_id": {"$exists": False}}]})
            print(f"Deleted {len(bad_docs)} documents without a valid event_id.")