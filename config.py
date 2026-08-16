# =============================================================================
# Smart City IoT — Database Configuration
# =============================================================================
# Fill in your connection details below before running the app.
# Do NOT commit this file with real passwords if you push to a public repo.
# =============================================================================
import json

# -----------------------------------------------------------------------------
# Neo4j
# Default bolt port is 7687. Username is almost always "neo4j".
# Password is what you set when you first connected to Neo4j.
# -----------------------------------------------------------------------------
NEO4J_URI      = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "xxx"

# -----------------------------------------------------------------------------
# ChromaDB
# Path where ChromaDB stores its data. "./chromadb_store" keeps it inside
# the project folder. Change this if you want it stored elsewhere.
# -----------------------------------------------------------------------------
CHROMA_PATH       = "./chromadb_store"
#CHROMA_COLLECTION = "citybuzz_events"

# -----------------------------------------------------------------------------
# MongoDB
# -----------------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
MONGO_HOST = "localhost"
MONGO_PORT = "27017"
MONGO_DB  = "smartcity"
MONGO_AUTH_DB = "admin"
# RBAC
mongo_user_credentials = """[
    {"username": "xxx", "password": "xxx"},
    {"username": "yyy", "password": "yyy"},
    {"username": "zzz", "password": "zzz"}
]"""
password_list = json.loads(mongo_user_credentials)
password_lookup = {user["username"]: user["password"] for user in password_list}
MONGO_USER = "xxx"
MONGO_PASSWORD = password_lookup.get(MONGO_USER)
