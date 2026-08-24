"""
SmartCity — MongoDB Seed Script
================================
Populates 4 MongoDB collections in the 'smartcity' database:
  - citizen_complaints
  - traffic_incidents
  - weather_readings
  - water_sensors
"""
import json
import pathlib
import config
from db.connections import get_mongo_client
from pymongo import ASCENDING, DESCENDING, UpdateOne, GEOSPHERE
from pymongo.errors import DuplicateKeyError, ConnectionFailure, OperationFailure
from datetime import datetime

# ── Load data ─────────────────────────────────────────────────────────────────
DATA_DIR = pathlib.Path(__file__).parent / "../../data"

def load(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

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
for col in ["citizen_complaints", "traffic_incidents", "weather_readings", "water_sensors"]:
    db[col].drop()
print("  Existing collections dropped.")


# ── Collection: citizen complaints ─────────────────────────────────────────────────────────
print("\nBuilding new Reddit citizen complaints collection...")
raw_citizen_complaints = load("singapore_citizen_complaints_2015_2025.json")

# Create indexes
complaints_col = db["citizen_complaints"]
complaints_col.create_index([("complaint_id", ASCENDING)], unique=True)
complaints_col.create_index([
    ("category", ASCENDING), ("location", ASCENDING), 
    ("complaint_text", ASCENDING), ("date_posted", DESCENDING)
])
complaints_col.create_index([
    ("user_name", ASCENDING), ("category", ASCENDING), 
    ("location", ASCENDING), ("date_posted", DESCENDING)
])

# no contact info to be pseudonymised before storage
# Build bulk upsert operations using the unique key
operations = [
    UpdateOne(
        filter={
            "complaint_id": doc["complaint_id"]
        },
        update={"$set": doc},
        upsert=True
    )
    for doc in raw_citizen_complaints
]

# Execute the bulk upsert
# With ordered=False, MongoDB is free to reorder and execute the operations in parallel or in arbitrary batches
if operations:
    result = complaints_col.bulk_write(operations, ordered=False)
    print(f"Upserted citizen complaint docs: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")


# ── Collection: traffic incidents  ──────────────────────────────────────────────────────────
print("\nBuilding new LTA traffic incidents collection...")
raw_traffic_incidents = load("lta_traffic_incidents_14hrs_15min.json")

# Create indexes
traffic_col = db["traffic_incidents"]
# single-field unique index on collection_time will cause Obstacle and 'Vehicle breakdown' records to be dropped!
traffic_col.create_index([("collection_time", DESCENDING), ("message", ASCENDING)], unique=True)
# Allows spatial queries on location alone, or combined with any other filters
traffic_col.create_index([("location", "2dsphere")])
traffic_col.create_index([
    ("type", ASCENDING), ("location", "2dsphere"), 
    ("message", ASCENDING), ("collection_time", DESCENDING)
])

# Transform the nested array structure into flattened documents
flattened_incidents = []

for batch in raw_traffic_incidents:
    # Parse timestamp to native BSON Date
    parsed_time = datetime.strptime(batch["collection_time"], "%Y-%m-%d %H:%M:%S")
    batch_num = batch["collection_number"]

    for incident in batch.get("traffic_incidents", []):
        flattened_incidents.append({
            "collection_number": batch_num,
            "collection_time": parsed_time,
            "type": incident.get("Type"),
            "location": {
                "type": "Point",
                # GeoJSON is [lon, lat]
                "coordinates": [incident.get("Longitude"), incident.get("Latitude")]
            },
            "message": incident.get("Message")
        })

if flattened_incidents:
    # Build bulk upsert operations using the unique compound key
    operations = [
        UpdateOne(
            filter={
                "collection_time": doc["collection_time"],
                "message": doc["message"]
            },
            update={"$set": doc},
            upsert=True
        )
        for doc in flattened_incidents
    ]

    # Execute the bulk upsert
    if operations:
        result = traffic_col.bulk_write(operations, ordered=False)
        print(f"Upserted traffic sensor docs: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")


# ── Collection: weather readings ───────────────────────────────────────────────────────
print("\nBuilding new NEA weather readings collection...")
#raw_weather_readings = load("nea_realtime_weather_readings_14hrs.jsonl")

# Create indexes
weather_col = db["weather_readings"]
weather_col.create_index([
    ("station_id", ASCENDING), ("weather_type", ASCENDING), 
    ("reading_timestamp", DESCENDING), ], unique=True)
# Allows spatial queries on location alone, or combined with any other filters
weather_col.create_index([("location", "2dsphere")])
# Optimised for finding all sensor readings across the island by type and time
weather_col.create_index([
    ("weather_type", ASCENDING), ("location", "2dsphere"),
    ("reading_timestamp", DESCENDING)
])

# Transform location object into GeoJSON, and convert timestamp ISO-8601 strings into BSON Dates.
weather_docs = []

with open("./data/nea_realtime_weather_readings_14hrs.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        doc = json.loads(line)

        # Convert location to valid GeoJSON Point [lon, lat]
        # Parse ISO timestamp strings to native BSON datetime
        cleaned_doc = {
            "station_id": doc["station_id"],
            "station_name": doc["station_name"],
            "weather_type": doc["weather_type"],
            "value": doc["value"],
            "reading_timestamp": datetime.fromisoformat(doc["reading_timestamp"]),
            "location": {
                "type": "Point",
                "coordinates": [float(doc["longitude"]), float(doc["latitude"])]
            }
        }
        weather_docs.append(cleaned_doc)

# Bulk insert
if weather_docs:
    # Build bulk upsert operations using the unique key
    operations = [
        UpdateOne(
            filter={
                "station_id": doc["station_id"],
                "weather_type": doc["weather_type"],
                "reading_timestamp": doc["reading_timestamp"]
            },
            update={"$set": doc},
            upsert=True
        )
        for doc in weather_docs
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
