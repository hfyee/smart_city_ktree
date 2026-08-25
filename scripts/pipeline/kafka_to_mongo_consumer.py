"""
This script consumes messages from Kafka, applies validation/transformation rules, and performs batch upserts into MongoDB.
"""
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException
from pymongo import MongoClient, UpdateOne
import config
from db.connections import get_mongo_client
import time

load_dotenv()

# MongoDB Setup (Native Local Instance)
client = get_mongo_client()
db = client[config.MONGO_DB] if client else None

# Dedicated Collections
COLLECTIONS = {
    "smartcity-complaints": db["citizen_complaints"],
    "smartcity-traffic": db["traffic_incidents"],
    "smartcity-weather": db["weather_readings"]
}

# Kafka Consumer Setup
consumer_config = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'smartcity-etl-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}
consumer = Consumer(consumer_config)
consumer.subscribe(list(COLLECTIONS.keys()))

# --- Domain-Specific Transformers ---

def transform_complaint(record: dict) -> dict:
    return {
        "complaint_id": record.get("complaint_id"),
        "category": record.get("category"),
        "complaint_text": record.get("complaint_text"),
        "location": record.get("location"),
        "user_name": record.get("user_name"),
        "date_posted": record.get("date_posted"),
        "ingested_at": datetime.now(timezone.utc)
    }

def transform_traffic(record: dict) -> dict:
    doc = {
        "collection_number": record.get("collection_number"),
        "collection_time": datetime.strptime(record.get("collection_time"), "%Y-%m-%d %H:%M:%S"),
        "type": record.get("Type"), 
        "ingested_at": datetime.now(timezone.utc)
    }

    loc_data = record.get("location") or {}

    # Extract nested coordinates
    lon = loc_data.get("longitude")
    lat = loc_data.get("latitude")

    # Only attach GeoJSON Point if both values are valid floats/ints
    if lon is not None and lat is not None:
        try:
            doc["location"] = {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]  # GeoJSON format: [lon, lat]
            }
        except (ValueError, TypeError):
            pass # Leave location omitted if parsing fails

    return doc

def transform_weather(record: dict) -> dict:
    doc = {
        "station_id": record.get("station_id"),
        "station_name": record.get("station_name"),
        "weather_type": record.get("weather_type"),
        "value": record.get("value"),
        "reading_timestamp": datetime.fromisoformat(record.get("reading_timestamp")),
        "ingested_at": datetime.now(timezone.utc)
    }

    loc_data = record.get("location") or {}

    # Extract nested coordinates
    lon = loc_data.get("longitude")
    lat = loc_data.get("latitude")

    # Only attach GeoJSON Point if both values are valid floats/ints
    if lon is not None and lat is not None:
        try:
            doc["location"] = {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]  # GeoJSON format: [lon, lat]
            }
        except (ValueError, TypeError):
            pass # Leave location omitted if parsing fails

    return doc

TRANSFORMERS = {
    "smartcity-complaints": transform_complaint,
    "smartcity-traffic": transform_traffic,
    "smartcity-weather": transform_weather
}

# Define filter builders for each topic
FILTER_BUILDERS = {
    "smartcity-complaints": lambda doc: {
        "complaint_id": doc.get("complaint_id")
    },
    "smartcity-traffic": lambda doc: {
        "collection_time": doc.get("collection_time"),
        "message": doc.get("message")
    },
    "smartcity-weather": lambda doc: {
        "station_id": doc.get("station_id"),
        "weather_type": doc.get("weather_type"),
        "reading_timestamp": doc.get("reading_timestamp")
    }
}

# --- ETL Pipeline Execution ---

def flush_batches(batches: dict):
    """Execute bulk writes across all collections that have pending documents."""
    flushed_any = False
    for topic, batch in batches.items():
        if batch:
            COLLECTIONS[topic].bulk_write(batch)
            print(f"Persisted {len(batch)} records to {COLLECTIONS[topic].name}")
            batch.clear()
            flushed_any = True
    if flushed_any:
        consumer.commit()

def run_etl(batch_threshold=200, flush_interval_seconds=5.0):
    print("Smart City Consumer ETL running. Listening to topics...")
    batches = {topic: [] for topic in COLLECTIONS.keys()}
    last_flush_time = time.time()

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            current_time = time.time()

            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            topic = msg.topic()
            payload = json.loads(msg.value().decode('utf-8'))

            # Route to transformer
            transformer = TRANSFORMERS.get(topic)
            filter_builder = FILTER_BUILDERS.get(topic)

            if transformer and filter_builder:
                transformed_doc = transformer(payload)
                query_filter = filter_builder(transformed_doc)

                batches[topic].append(
                    UpdateOne(
                        filter=query_filter,
                        update={"$set": transformed_doc},
                        upsert=True
                    )
                )

            # Check Flush Condition 1: Size threshold exceeded
            size_triggered = any(len(b) >= batch_threshold for b in batches.values())

            # Check Flush Condition 2: Time interval exceeded (and there is buffered data)
            time_triggered = (current_time - last_flush_time >= flush_interval_seconds) and any(len(b) > 0 for b in batches.values())

            if size_triggered or time_triggered:
                flush_batches(batches)
                last_flush_time = current_time

    except KeyboardInterrupt:
        print("\nStopping ETL pipeline...")
    finally:
        flush_batches(batches)
        consumer.close()

if __name__ == "__main__":
    run_etl()