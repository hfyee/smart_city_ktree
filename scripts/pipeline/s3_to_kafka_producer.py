"""
This script extracts objects (JSON, CSV, or Parquet) from your S3 bucket and streams individual records into the Kafka topic.
"""
import json
import os
import boto3
from confluent_kafka import Producer
from dotenv import load_dotenv
import config

# Reads the key-value pairs from .env and adds them to environment variables
load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "ap-southeast-1")
aws_s3_bucket = os.getenv("S3_BUCKET")

# AWS & S3 Config
S3_BUCKET = aws_s3_bucket
S3_PREFIX = "raw_data/"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Kafka Producer Config
producer_config = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'client.id': 'smartcity-s3-producer',
    'linger.ms': 10,
    'batch.num.messages': 1000
}
producer = Producer(producer_config)

# Map S3 prefix keywords to dedicated Kafka topics
ROUTING_RULES = {
    "complaints/": "smartcity-complaints",
    "traffic/": "smartcity-traffic",
    "weather/": "smartcity-weather"
}

# Explicit list of specific S3 files to process
TARGET_FILES = [
    "smart-city/complaints/complaints_2026_08.json",
    "smart-city/traffic/traffic_sensor_junction_01.json",
    "smart-city/weather/weather_station_cbd.json"
]

def resolve_topic(s3_key: str) -> str:
    """Determine the destination Kafka topic from the S3 file path."""
    for prefix_key, topic_name in ROUTING_RULES.items():
        if prefix_key in s3_key:
            return topic_name
    return None

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record to {msg.topic()}: {err}")

def stream_s3_to_kafka(file_keys: list):
    """Fetch exact S3 files and stream each line as a Kafka message."""
    for key in file_keys:
        target_topic = resolve_topic(key)
        if not target_topic:
            print(f"Skipping '{key}': No matching Kafka topic route found.")
            continue

        print(f"\n[Processing] S3 File: {key} -> Kafka Topic: {target_topic}")
        
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            lines = response['Body'].read().decode('utf-8').splitlines()

            record_count = 0
            for line in lines:
                clean_line = line.strip()
                if clean_line:
                    producer.produce(
                        topic=target_topic,
                        value=clean_line.encode('utf-8'),
                        callback=delivery_report
                    )
                    record_count += 1
            
            # Flush batch per file to ensure all messages are delivered
            producer.flush()
            print(f"[Success] Streamed {record_count} records from {key}")

        except s3_client.exceptions.NoSuchKey:
            print(f"[Error] File not found in S3: {key}")
        except Exception as e:
            print(f"[Error] Failed processing file {key}: {e}")

if __name__ == "__main__":
    stream_s3_to_kafka(TARGET_FILES)