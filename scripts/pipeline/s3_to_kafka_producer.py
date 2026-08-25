"""
This script extracts objects (JSON, CSV, or Parquet) from your S3 bucket and streams individual records into the Kafka topic.
"""
import io
import json
import os
import boto3
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

# AWS & S3 Config
S3_BUCKET = os.getenv("S3_BUCKET")
session = boto3.Session(profile_name=os.getenv("AWS_PROFILE", "EDM_AWS_ROLE_01"))
s3_client = session.client("s3")

# Kafka Producer Config
producer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "client.id": "smartcity-s3-producer",
    "linger.ms": 10,
    "batch.num.messages": 1000,
    "queue.buffering.max.messages": 100000,
}
producer = Producer(producer_config)

# Map keyword substrings to dedicated Kafka topics
ROUTING_RULES = {
    "complaints": "smartcity-complaints",
    "traffic": "smartcity-traffic",
    "weather": "smartcity-weather"
}

TARGET_FILES = [
    "raw_data/singapore_citizen_complaints_2015_2025.json",
    "raw_data/lta_traffic_incidents_14hrs_15min.json",
    "raw_data/nea_realtime_weather_readings_14hrs.jsonl"
]

def resolve_topic(s3_key: str) -> str | None:
    """Determine the destination Kafka topic using keyword matching."""
    s3_key_lower = s3_key.lower()
    for keyword, topic_name in ROUTING_RULES.items():
        if keyword in s3_key_lower:
            return topic_name
    return None

def delivery_report(err, msg):
    if err is not None:
        print(f"[Delivery Failed] {msg.topic()}: {err}")

def publish_record(topic: str, record_data: dict | str):
    """Encodes and pushes a single record dictionary/string to Kafka."""
    payload = json.dumps(record_data) if isinstance(record_data, dict) else record_data
    
    # Handle queue buffer backpressure
    while True:
        try:
            producer.produce(
                topic=topic,
                value=payload.encode("utf-8"),
                callback=delivery_report
            )
            break
        except BufferError:
            # Buffer full: trigger callback events to clear queue
            producer.poll(0.1)

    # Regularly serve delivery report callbacks
    producer.poll(0)

def stream_s3_to_kafka(file_keys: list):
    """Fetch files from S3 and stream records according to file extension."""
    for key in file_keys:
        target_topic = resolve_topic(key)
        if not target_topic:
            print(f"Skipping '{key}': No matching Kafka topic route found.")
            continue

        print(f"\n[Processing] S3 File: {key} -> Kafka Topic: {target_topic}")

        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            body_stream = response["Body"]
            record_count = 0

            # 1. Handle JSON Lines format (.jsonl)
            if key.endswith(".jsonl"):
                for line in io.TextIOWrapper(body_stream, encoding="utf-8"):
                    clean_line = line.strip()
                    if clean_line:
                        publish_record(target_topic, clean_line)
                        record_count += 1

            # 2. Handle Standard JSON arrays / objects (.json)
            else:
                data = json.load(body_stream)
                
                # If root is a list, stream each item
                if isinstance(data, list):
                    for item in data:
                        publish_record(target_topic, item)
                        record_count += 1
                
                # If wrapped inside an envelope key (e.g., LTA DataMall 'value' or batch list)
                elif isinstance(data, dict):
                    records = data.get("value") or data.get("traffic_incidents") or [data]
                    for item in records:
                        publish_record(target_topic, item)
                        record_count += 1

            producer.flush()
            print(f"[Success] Streamed {record_count} individual records from {key}")

        except s3_client.exceptions.NoSuchKey:
            print(f"[Error] File not found in S3 bucket '{S3_BUCKET}': {key}")
        except Exception as e:
            print(f"[Error] Failed processing file {key}: {e}")

if __name__ == "__main__":
    stream_s3_to_kafka(TARGET_FILES)