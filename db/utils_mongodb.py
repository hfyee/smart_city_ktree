"""
MongoDB helper functions called by page scripts
"""
from unittest import result
import json
import pathlib
import config
from db.utils import load, pseudonymise
from db.connections import get_mongo_client
from pymongo import ReturnDocument
from pymongo.cursor import Cursor
from typing import Any
from collections import defaultdict
from datetime import datetime
 
# ── Connect ───────────────────────────────────────────────────────────────
client = get_mongo_client()
db = client[config.MONGO_DB] if client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")
complaints_col = db["citizen_complaints"]
weather_col = db["weather_readings"]
traffic_col = db["traffic_incidents"]

# Build lookup dictionaries for denormalisation

# ── Aggregation ──────────────────────────────────────────────────────────
# Recommended order: $match, $lookup, $unwind, $group
def aggregate_citizen_complaints_by_category(year) -> list[dict]:
    """Analyzes the complaints documents using aggregation pipeline."""
    pipeline = []

    pipeline.append({
        "$match": {
            "date_posted": {"$regex": f"^{year}"}
        }
    })

    pipeline.extend([
        { "$group": {
            "_id": "$category",
            "complaints_count": { "$sum": 1 },
            "earliest_date": { "$min": "$date_posted" },
            "latest_date": { "$max": "$date_posted" }
        }},
        { "$sort":  { "complaints_count": -1 } },
        { "$limit": 10 },
        {"$project": {
            "category": "$_id", # map _id back to category
            "complaints_count": 1,
            "earliest_date": 1,
            "latest_date": 1,
            "_id": 0
        }}
    ])

    return list(complaints_col.aggregate(pipeline))

# Recommended order: $match, $lookup, $unwind, $group
def aggregate_traffic_incidents_by_type(year: int) -> list[dict]:
    """Analyzes the traffic incident documents using aggregation pipeline."""
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    pipeline = []

    pipeline.append({
        "$match": {
            "collection_time": {
                "$gte": start_date,
                "$lt": end_date
            }
        }
    })

    pipeline.extend([
        { "$group": {
            "_id": "$incident_type",
            "incidents_count": { "$sum": 1 },
            "collection_time": { "$max": "$collection_time" }
        }},
        { "$sort":  { "incidents_count": -1 } },
        { "$limit": 10 },
        {"$project": {
            "incident_type": "$_id", # map _id back to incident_type
            "incidents_count": 1,
            "collection_time": 1,
            "_id": 0
        }}
    ])

    return list(traffic_col.aggregate(pipeline))

# ── Read operations ───────────────────────────────────────────────────────
def get_citizen_complaints(year: str, category: str) -> list:
    query = {}
    if category:
        query["category"] = category
    if year:
        query["date_posted"] = {"$regex": f"^{year}"}
    
    complaint_projection = {
        "date_posted": 1, "complaint_text": 1, "location": 1, 
        "user_name": 1, "_id": 0
    }
    result = list(
        complaints_col.find(query, complaint_projection)
        .sort("date_posted", -1)
        .limit(200)
    )

    return result

def get_days_with_this_weather(year: str, wind_speed: float, temperature: float,
                               precipitation: float, visibility: float) -> list:
    """Returns a list of weather documents matching the given filters."""
    query = {}
    if wind_speed:
        query["wind_speed_kmh"] = {"$gt": wind_speed}
    if temperature:
        query["temperature_celsius"] = {"$lt": temperature}
    if precipitation:
        query["precipitation_mm"] = {"$gt": precipitation}
    if visibility:
        query["visibility_km"] = {"$lt": visibility}
    if year:
        query["recorded_at"] = {"$regex": f"^{year}"}
    
    result = list(
        weather_col.find(query, {
        "station_id": 1, "recorded_at": 1, 
        "wind_speed_kmh": 1, "temperature_celsius": 1, 
        "precipitation_mm": 1, "visibility_km": 1,
        "_id": 0})
        .sort("recorded_at", -1)
        .limit(500)
    )

    return result

def get_traffic_on_weather_days(year: str, wind_speed: float, temperature: float,
                               precipitation: float, visibility: float) -> list:
    """Returns a flattened row (weather, traffic) pair that matches the given filters."""
    query = {}
    if wind_speed:
        query["wind_speed_kmh"] = {"$gt": wind_speed}
    if temperature:
        query["temperature_celsius"] = {"$lt": temperature}
    if precipitation:
        query["precipitation_mm"] = {"$gt": precipitation}
    if visibility:
        query["visibility_km"] = {"$lt": visibility}
    if year:
        query["recorded_at"] = {"$regex": f"^{year}"}
    
    weather_projection = {
        "station_id": 1, "recorded_at": 1,
        "wind_speed_kmh": 1, "temperature_celsius": 1,
        "precipitation_mm": 1, "visibility_km": 1,
        "_id": 0
    }
    dates_with_this_weather = list(
        weather_col.find(query, weather_projection)
        .sort("recorded_at", -1)
    )
    # Calendar dates to match traffic_col against
    weather_dates = {
        datetime.fromisoformat(doc["recorded_at"]).date().isoformat()
        for doc in dates_with_this_weather
    }

    # Traffic query
    traffic_projection = {
        "sensor_id": 1, "timestamp": 1,
        "congestion_level": 1, "avg_speed_kmh": 1,
        "road_segment": 1, "weather_condition": 1,
        "_id": 0
    }
    traffic_query = {
        "$and": [
            {"$expr": {"$in": [{"$substrCP": ["$timestamp", 0, 10]}, list(weather_dates)]}},
            {"congestion_level": {"$in": ["High"]}},
            {"weather_condition": {"$nin": [None, ""]}} # exclude null and empty strings
        ]
    }
    traffic_results = list(
        traffic_col.find(traffic_query, traffic_projection)
        .sort("timestamp", -1)
        .limit(500)
    )

    # Group traffic docs by calendar date
    traffic_by_date = defaultdict(list)
    for doc in traffic_results:
        day = doc["timestamp"][:10]
        traffic_by_date[day].append(doc)

    # Flatten into one row per (weather, traffic) pair sharing a calendar day
    merged_rows = []
    for weather_doc in dates_with_this_weather:
        day = datetime.fromisoformat(weather_doc["recorded_at"]).date().isoformat()
        weather_row = {"date": day, **weather_doc}

        ## inner join
        for traffic_doc in traffic_by_date.get(day, []):
            row = dict(weather_row)
            row.update({f"traffic_{k}": v for k, v in traffic_doc.items() if k != "timestamp"})
            merged_rows.append(row)

    return merged_rows

def find_weather_near_traffic_incident():
    incident_coords = [103.89022888218133, 1.400674358412916]

    nearby_rainfall = collection.find({
        "weather_type": "rainfall",
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": incident_coords
                },
                "$maxDistance": 3000  # meters
            }
        }
    }).limit(5)