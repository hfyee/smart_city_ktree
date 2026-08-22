"""
SmartCity — MongoDB Seed Script
================================
Populates three MongoDB collections in the 'citybuzz' database:
  - events
  - users
  - bookings

Requirements:
    pip install pymongo

Usage:
    python seed_mongodb.py

Assumes MongoDB running locally on mongodb://localhost:27017 (default).
"""
import json
import pathlib
import config
from db.connections import get_mongo_client
from pymongo import ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import DuplicateKeyError, ConnectionFailure, OperationFailure
from db.utils import pseudonymise

# ── Load data ─────────────────────────────────────────────────────────────────
DATA_DIR = pathlib.Path(__file__).parent / "../../data"

def load(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

citizen_complaints = load("smart_city_dataset_citizen_complaints.json")
traffic_sensors = load("smart_city_dataset_traffic_sensors.json")
weather_data = load("smart_city_dataset_weather_data.json")

# Build lookup dictionaries for denormalisation


# ── Connect ───────────────────────────────────────────────────────────────────
try:
    client = get_mongo_client()
    db = client[config.MONGO_DB]
    print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")
except ConnectionFailure:
    print("Failed to connect to MongoDB server.")
except OperationFailure as e:
    print(f"Authentication or RBAC permission error: {e.details}")

# ── Drop existing collections for a clean seed ───────────────────────────────
for col in ["citizen_complaints", "traffic_sensors", "weather_data"]:
    db[col].drop()
print("  Existing collections dropped.")

# ── Collection: citizen complaints ─────────────────────────────────────────────────────────
# MongoDB documents are normalised: nothing is embedded currently
complaints_col = db["citizen_complaints"]
complaints_col.create_index([("complaint_id", ASCENDING)], unique=True)
complaints_col.create_index([("date_submitted", DESCENDING)])
complaints_col.create_index([("category", ASCENDING), ("area", ASCENDING)])
complaints_col.create_index([("priority", ASCENDING), ("status", ASCENDING)])

complaint_docs = []

for c in citizen_complaints:
    doc = {
        "complaint_id": c["complaint_id"],
        "date_submitted": c["date_submitted"],
        "complaint_text": c["complaint_text"],
        "category": c["category"],
        "status": c["status"],
        "priority": c["priority"],
        "area": c["area"],
        "contact_info": pseudonymise(c["contact_info"]) # store a hash instead of the raw email for privacy
    }
    complaint_docs.append(doc)

#complaints_col.insert_many(complaint_docs)
#print(f"  Citizen complaint docs inserted: {complaints_col.count_documents({})}")

# Build bulk upsert operations using the unique compound key
operations = [
    UpdateOne(
        filter={
            "complaint_id": doc["complaint_id"]
        },
        update={"$set": doc},
        upsert=True
    )
    for doc in complaint_docs
]

# Execute the bulk upsert
# With ordered=False, MongoDB is free to reorder and execute the operations in parallel or in arbitrary batches
if operations:
    result = complaints_col.bulk_write(operations, ordered=False)
    print(f"Upserted citizen complaint docs: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")

# ── Collection: traffic sensors ──────────────────────────────────────────────────────────
traffic_col = db["traffic_sensors"]
traffic_col.create_index([("timestamp", DESCENDING), ("sensor_id", ASCENDING)], unique=True)
traffic_col.create_index([("weather_condition", ASCENDING)])
complaints_col.create_index([("road_segment", ASCENDING), ("congestion_level", ASCENDING)])
complaints_col.create_index([("vehicle_count", ASCENDING), ("avg_speed_kmh", ASCENDING)])

#traffic_col.insert_many(traffic_sensors)
#print(f"  Traffic sensor docs inserted: {traffic_col.count_documents({})}")

# Build bulk upsert operations using the unique compound key
operations = [
    UpdateOne(
        filter={
            "timestamp": doc["timestamp"],
            "sensor_id": doc["sensor_id"]
        },
        update={"$set": doc},
        upsert=True
    )
    for doc in traffic_sensors
]

# Execute the bulk upsert
if operations:
    result = traffic_col.bulk_write(operations, ordered=False)
    print(f"Upserted traffic sensor docs: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")

# ── Collection: weather ───────────────────────────────────────────────────────
weather_col = db["weather_data"]
weather_col.create_index([("recorded_at", DESCENDING), ("station_id", ASCENDING)], unique=True)
weather_col.create_index([("temperature_celsius", ASCENDING), ("humidity_percent", ASCENDING)])
weather_col.create_index([("pressure_hpa", ASCENDING), ("wind_speed_kmh", ASCENDING)])
weather_col.create_index([("precipitation_mm", ASCENDING), ("visibility_km", ASCENDING)])

#weather_col.insert_many(weather_data)
#print(f"  Weather sensor docs inserted: {weather_col.count_documents({})}")

# Build bulk upsert operations using the unique compound key
operations = [
    UpdateOne(
        filter={
            "recorded_at": doc["recorded_at"],
            "station_id": doc["station_id"]
        },
        update={"$set": doc},
        upsert=True
    )
    for doc in weather_data
]

# Execute the bulk upsert
if operations:
    result = weather_col.bulk_write(operations, ordered=False)
    print(f"Upserted weather sensor docs: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")


# ── Smoke test — find any docs with missing or null id ────────────────────────
print ("\nSmoke test - complaints missing a valid complaint_id.")

bad_docs = list(complaints_col.find({
    "$or": [
        {"complaint_id": None},
        {"complaint_id": {"$exists": False}}
    ]
}))

print(f"Found {len(bad_docs)} docs without a valid complaint_id.")

# ── Smoke test — aggregation pipeline ─────────────────────────────────────────
print("\nSmoke test — complaints per category:")

pipeline = [
    { "$group": {
        "_id": "$category",
        "complaints_count": { "$sum": 1 }
    }},
    { "$sort":  { "complaints_count": -1 } },
    { "$limit": 10 },
    {"$project": {
        "category": "$_id", # map _id back to category
        "complaints_count": 1,
        "_id": 0
    }}
]

for r in complaints_col.aggregate(pipeline):
    print(f"  {r['category']}: {r['complaints_count']} complaints received")
# ──

client.close()
print("\nDone. MongoDB seeding complete.")
