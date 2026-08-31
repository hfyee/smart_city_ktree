# ITG204_Project

The Smart City Knowledge Tree is a data product that unifies a number of heterogeneous smart-city datasets — LTA traffic incidents, NEA weather station readings, citizen complaints from Reddit forum, building energy consumption — into a single application for users to search traffic incidents, citizen complaints as well as to explore trends and potential relationships between weather and the other entities captured in this study.  

The solution is organised into four layers. An Ingestion layer batches raw source data from an AWS S3 data lake, in turn sourced from LTA and NEA’s IoT sensor feeds. A Processing layer, built on Apache Kafka, performs ETL and streams records to three purpose-built databases. The Serving Layer combines MongoDB as the operational store (time-series collections, secondary indexing, and 2dsphere-based proximity search), ChromaDB for semantic vector search over free-text citizen complaints and LTA traffic messages, and Neo4j as a twelve-label property graph enabling multi-hop traversal across traffic, weather, and energy entities. 
A Streamlit Application layer exposes these capabilities through a multipage dashboard.

```
smart_city_ktree
|-app.py
|-config.py
|-db
|   |-connections.py
|   |-utils_mongodb.py
|   |-utils_chromadb.py
|   |-utils_neo4j.py
|-scripts
|   |-mongodb
|   |-chromadb
|   |-neo4j
|   |-kafka
|       |-producer_s3_to_kafka.py
|       |-consumer_mongodb.py
|       |-consumer_chromadb.py
|       |-consumer_neo4j.py
|-pages
|   |-1_Operational_DB.py
|   |-2_Graph_Explorer.py
|   |-3_Semantic_Search.py
|   |-4_Kafka_ETL.py
```