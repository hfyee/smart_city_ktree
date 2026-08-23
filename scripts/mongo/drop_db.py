"""
MongoDB script to drop database 
"""
import json
import config
from db.connections import get_mongo_client

# ── Connect ────────────────────────────────────────────────────────────────────
client = get_mongo_client()

if __name__ == '__main__':
    database_name = "smartcity"

    input(f"Warning: The entire database '{database_name}' will be deleted! Press Enter to continue ...")
    client.drop_database(database_name)
    print("Database dropped.")