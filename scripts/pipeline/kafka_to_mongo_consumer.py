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

load_dotenv()

# MongoDB Setup (Native Local Instance)
MONGO_URI = os.getenv(config.MONGO_URI, "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["smart_city"]

# Dedicated Collections
COLLECTIONS = {
    "smartcity-complaints": db["citizen_complaints"],
    "smartcity-traffic": db["traffic_sensors"],
    "smartcity-weather": db["weather_data"]
}

# Kafka Consumer Setup
consumer_config = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'smartcity-etl-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}
consumer = Consumer(consumer_config)
consumer.subscribe(list(COLLECTIONS.keys()))

# --- Domain-Specific Transformers ---

def transform_complaint(record: dict) -> dict:
    return {
        "_id": record.get("complaint_id"),
        "category": record.get("category", "GENERAL").upper(),
        "description": record.get("description", ""),
        "status": record.get("status", "OPEN").upper(),
        "neighborhood": record.get("neighborhood"),
        "priority_score": int(record.get("priority_score", 1)),
        "reported_at": record.get("timestamp"),
        "ingested_at": datetime.now(timezone.utc)
    }

def transform_traffic(record: dict) -> dict:
    return {
        "_id": f"{record.get('sensor_id')}_{record.get('timestamp')}",
        "sensor_id": record.get("sensor_id"),
        "junction_name": record.get("junction_name"),
        "vehicle_count": int(record.get("vehicle_count", 0)),
        "avg_speed_kmh": float(record.get("avg_speed_kmh", 0.0)),
        "congestion_level": record.get("congestion_level", "LOW"),
        "recorded_at": record.get("timestamp"),
        "ingested_at": datetime.now(timezone.utc)
    }

def transform_weather(record: dict) -> dict:
    return {
        "_id": f"{record.get('station_id')}_{record.get('timestamp')}",
        "station_id": record.get("station_id"),
        "temperature_c": float(record.get("temperature_c", 0.0)),
        "humidity_pct": float(record.get("humidity_pct", 0.0)),
        "precipitation_mm": float(record.get("precipitation_mm", 0.0)),
        "recorded_at": record.get("timestamp"),
        "ingested_at": datetime.now(timezone.utc)
    }

TRANSFORMERS = {
    "smartcity-complaints": transform_complaint,
    "smartcity-traffic": transform_traffic,
    "smartcity-weather": transform_weather
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

def run_etl(batch_threshold=200):
    print("Smart City Consumer ETL running. Listening to topics...")
    batches = {topic: [] for topic in COLLECTIONS.keys()}

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            topic = msg.topic()
            payload = json.loads(msg.value().decode('utf-8'))

            # Route to transformer and prepare upsert
            transformer = TRANSFORMERS.get(topic)
            if transformer:
                transformed_doc = transformer(payload)
                batches[topic].append(
                    UpdateOne(
                        {"_id": transformed_doc["_id"]},
                        {"$set": transformed_doc},
                        upsert=True
                    )
                )

            # Flush when any individual batch exceeds threshold
            if any(len(b) >= batch_threshold for b in batches.values()):
                flush_batches(batches)

    except KeyboardInterrupt:
        print("\nStopping ETL pipeline...")
    finally:
        flush_batches(batches)
        consumer.close()

if __name__ == "__main__":
    run_etl()