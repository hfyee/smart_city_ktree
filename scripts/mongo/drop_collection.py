"""
MongoDB script to drop collection 
"""
import json
import config
from db.connections import get_mongo_client

# ── Connect ────────────────────────────────────────────────────────────────────
client = get_mongo_client()
db = client[config.MONGO_DB] if client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")

if __name__ == '__main__':
    collections = db.list_collection_names()
    print(collections)

    input("Warning: All collections will be deleted! Press Enter to continue ...")
    for col in ["citizen_complaints", "traffic_incidents", "weather_readings"]:
        db[col].drop()
    print("Existing collections dropped.")
