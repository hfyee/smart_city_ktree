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
from typing import Any
from collections import defaultdict
from datetime import datetime
import pandas as pd
 
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
            "_id": "$type",
            "incidents_count": { "$sum": 1 },
            "collection_time": { "$max": "$collection_time" }
        }},
        { "$sort":  { "incidents_count": -1 } },
        { "$limit": 10 },
        {"$project": {
            "type": "$_id", # map _id back to type
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

def get_traffic_incidents(type: str) -> list:
    """Queries traffic incident documents that matches the given filter. Returns a list."""
    traffic_query = {
        "type": type,
        "location.coordinates": {"$exists": True, "$ne": None}
    }

    traffic_projection = {
        "collection_time": 1,
        "location.coordinates": 1, "message": 1,
        "_id": 0
    }

    result = list(traffic_col.find(traffic_query, traffic_projection)
        .sort("collection_time", -1)
        .limit(10)
    )

    return result

def find_weather_near_traffic_incident(incident_coords: list[float], 
                                       weather_type: str = "rainfall", 
                                       max_distance_m: int = 3000) -> list[dict[str, Any]]:
    """Finds weather readings within a radius of given coordinates [lon, lat]."""
    nearby_weather = weather_col.find({
        #"weather_type": weather_type,
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": incident_coords
                },
                "$maxDistance": max_distance_m
            }
        }
    }).limit(1)  # Get the closest reading
    
    return list(nearby_weather)

def enrich_incidents_with_weather(incidents: list[dict]) -> pd.DataFrame:
    """Pairs each incident with its nearest weather observation."""
    plot_data = []
    columns = ["collection_time", "latitude", "longitude", "message", "nearby_weather"]

    for inc in incidents:
        # Extract [lon, lat] from the nested dictionary
        coords = inc.get("location", {}).get("coordinates", [])
        if not coords or len(coords) < 2:
            continue        
        lon, lat = coords[0], coords[1]
        
        # Query nearest weather reading
        # Create the 2dsphere index on the weather_readings collection needed for $near query
        weather_col.create_index([("location", "2dsphere")])
        weather_records = find_weather_near_traffic_incident(coords)
        
        # Format weather details if found
        if weather_records:
            w = weather_records[0]
            weather_desc = f"{w.get('weather_type', 'N/A')}: {w.get('value', 'N/A')} ({w.get('station_name', 'Unknown')})"
        else:
            weather_desc = "No weather station in range"

        plot_data.append({
            "collection_time": inc.get("collection_time"),
            "latitude": lat,
            "longitude": lon,
            "message": inc.get("message"),
            "nearby_weather": weather_desc
        })

    # Return empty DataFrame with predefined columns if no records matched
    if not plot_data:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(plot_data)
