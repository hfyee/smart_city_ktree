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
weather_col = db["weather_data"]
traffic_col = db["traffic_sensors"]

# Build lookup dictionaries for denormalisation
#venues     = load("venues.json")
#organisers = load("organisers.json")
#venue_map     = {v["venue_id"]: v for v in venues}
#organiser_map = {o["organiser_id"]: o for o in organisers}

# ── Read operations ───────────────────────────────────────────────────────
def get_citizen_complaints(year: str, category: str, priority: str) -> list:
    query = {}
    if category:
        query["category"] = category
    if priority:
        query["priority"] = priority
    if year:
        query["date_submitted"] = {"$regex": f"^{year}"}
    
    complaint_projection = {
        "date_submitted": 1, "complaint_text": 1, "area": 1, 
        "status":1, "contact_info": 1, "_id": 0
    }
    result = list(
        complaints_col.find(query, complaint_projection)
        .sort("date_submitted", -1)
        .limit(500)
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

# Recommended order: $match, $lookup, $unwind, $group
def aggregate_citizen_complaints_by_category(filter_priority) -> list[dict]:
    """Analyzes the event documents using aggregation pipeline."""
    pipeline = []

    # Only attach the $match stage if filter_priority is not "(all)"
    if filter_priority != "(all)":
        pipeline.append({
            "$match": {
                "priority": filter_priority
            }
        })

    pipeline.extend([
        { "$group": {
            "_id": "$category",
            "complaints_count": { "$sum": 1 },
            "earliest_date": { "$min": "$date_submitted" },
            "latest_date": { "$max": "$date_submitted" }
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

def get_weather_cursor() -> Cursor[dict[str, Any]]:
    """Returns weather data for visual plot on frontend."""
    weather_col = db["weather_data"]

    # 2. Project only relevant traffic-weather fields
    projection = {
        "_id": 0,
        "visibility_km": 1,
        "precipitation_mm": 1,
        "wind_speed_kmh": 1,
        "temperature_celsius": 1,
    }

    # Fetch non-null documents
    cursor = weather_col.find(
        {"visibility_km": {"$exists": True, "$ne": None}}, 
        projection
    )

    return cursor
