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
NEO4J_PASSWORD = "NYP_EDM-ITG202"

# -----------------------------------------------------------------------------
# ChromaDB
# Path where ChromaDB stores its data. "./chromadb_store" keeps it inside
# the project folder. Change this if you want it stored elsewhere.
# -----------------------------------------------------------------------------
CHROMA_PATH       = "./chromadb_store"
CHROMA_COLLECTION = "smartcity_traffic_incidents"

# -----------------------------------------------------------------------------
# MongoDB
# -----------------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
MONGO_HOST = "localhost"
MONGO_PORT = "27017"
MONGO_DB_2  = "smartcity_us"
MONGO_DB  = "smartcity"
MONGO_AUTH_DB = "admin"
mongo_user_credentials = """[
    {"username": "hfyee", "password": "9108122d"},
    {"username": "tsteo", "password": "3897044t"},
    {"username": "mkao", "password": "6667044q"}
]"""
password_list = json.loads(mongo_user_credentials)
password_lookup = {user["username"]: user["password"] for user in password_list}
MONGO_USER = "hfyee"
MONGO_PASSWORD = password_lookup.get(MONGO_USER)