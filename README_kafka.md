# Kafka ETL ingestion from S3 bucket
// check your AWS credentials in .env file

Step 1:
// start Kafka container from docker-compose.yml
docker compose up -d
docker ps
docker logs -f kafka-local

Step 2:
Start the producer script (s3_to_kafka_producer.py) first, and then run the consumer script (kafka_to_mongo_consumer.py) in a separate terminal.

Step 3:
Run scripts/mongo/check_docs.py to verify the collections are really upserted.

# Misc

## Delete the topics 
// The producer messages will not lost. Unlike traditional in-memory message brokers, 
Kafka is a distributed commit log. Once the producer script finishes executing and flushes the records, Kafka persists those messages directly to disk on the broker.

docker exec -it kafka-local /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic smartcity-complaints
docker exec -it kafka-local /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic smartcity-traffic
docker exec -it kafka-local /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic smartcity-weather