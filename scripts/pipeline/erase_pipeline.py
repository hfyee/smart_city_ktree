"""
Pipeline script to drop all database records 
"""
import config
from db.utils import load, pseudonymise
from db.connections import get_mongo_client, get_neo4j_driver
from pymongo import ReturnDocument
import chromadb

# --- Store 1 (PRIMARY): MongoDB, system of record ---
mongo_client = get_mongo_client()
db = mongo_client[config.MONGO_DB] if mongo_client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")

# --- Store 2 (derived): ChromaDB, semantic layer --
chroma_client = chromadb.PersistentClient(path="./chromadb_store")
print("Connected to ChromaDB.")

# --- Store 3 (derived): Neo4j, relationship layer ---
neo4j_driver = get_neo4j_driver()
neo4j_driver.verify_connectivity()
print("Neo4j connected")
print()

if __name__ == '__main__':
    db["citizen_complaints"].drop()
    db["traffic_incidents"].drop()
    db["weather_readings"].drop()
    print("MongoDB collections cleared.")

    chroma_client.delete_collection("citizen_complaints")
    print("ChromaDB collection cleared.")

    neo4j_driver.execute_query("MATCH (n) DETACH DELETE n")
    print("Graph cleared.")
