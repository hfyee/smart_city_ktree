"""
MongoDB helper functions called by page scripts
"""
from unittest import result
import json
import pathlib
import config
from db.utils import load, pseudonymise
from db.connections import get_mongo_client
from pymongo import ReturnDocument
 
# ── Connect ───────────────────────────────────────────────────────────────
client = get_mongo_client()
db = client[config.MONGO_DB] if client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB}'.")

# Build lookup dictionaries for denormalisation
#venues     = load("venues.json")
#organisers = load("organisers.json")
#venue_map     = {v["venue_id"]: v for v in venues}
#organiser_map = {o["organiser_id"]: o for o in organisers}

# ── CRUD operations ───────────────────────────────────────────────────────
# Auto-increment event_id
# Run separate script init_event_id_counter.py during setup to initialize the counter
def get_next_event_id() -> str:
    """Increments the counter and returns the formatted ID (e.g., 'EVT101')."""
    counter = db.counters.find_one_and_update(
        filter={"_id": "event_id"},
        update={"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    seq_number = counter["seq"]    
    # Format with prefix and 3-digit padding (e.g., 101 -> 'EVT101', 9 -> 'EVT009')
    return f"EVT{seq_number:03d}"

def create_event(new_event: dict) -> str:
    """Inserts one event document. Called from the Streamlit 'Add Event' form.""" 
    e = {
        "title":            new_event["title"],
        "description":      new_event["description"],
        "category":         new_event["category"],
        "date":             new_event["date"],
        "time":             new_event["time"],
        "price":            float(new_event["price"]),
        "available_tickets": int(new_event["available_tickets"]),
        "tags":            new_event["tags"],
    }
    e["event_id"] = get_next_event_id()

    v = venue_map.get(new_event["venue_id"], {})
    venue_data = {
        "venue_id":  v.get("venue_id"),
        "name":      v.get("name"),
        "address":   v.get("address"),
        "type":      v.get("type"),
        "neighbourhood": v.get("neighbourhood"),
    }
    e["venue"] = venue_data

    o = organiser_map.get(new_event["organiser_id"], {})
    organiser_data = {
        "organiser_id": o.get("organiser_id"),
        "name":         o.get("name"),
        "email":        o.get("email"),
    }
    e["organiser"] = organiser_data

    result = db.events.insert_one(e)
    #print(f"Inserted event with ID: {e['event_id']}")
    return str(result.inserted_id)

def read_events(filter_category: str, max_price: float) -> list:
    """Reads events with optional filters. Returns a list of event documents."""
    query = {}
    if filter_category and filter_category != "(all)":
        query["category"] = filter_category
    if max_price is not None:
        query["price"] = {"$lte": max_price}
    
    events = list(db.events.find(query))
    return events

def get_documents_count() -> int:
    return db.events.count_documents({})

def update_event_price(event_id: str, new_price: float) -> bool:
    """Update the price of an event document by event_id. Returns True if updated, False if not found."""
    result = db.events.update_one({"event_id": event_id}, {"$set": {"price": new_price}})
    if result.modified_count > 0:
        #print(f"Updated price for event ID: {event_id} to {new_price}")
        return True
    else:
        #print(f"No event found with ID: {event_id} or price unchanged.")
        return False
    
def update_event(event_id: str, **kwargs) -> bool:
    """Updates specified fields for a given event_id using $set. Returns True if successful, False otherwise."""
    # Ensure at least one field was passed to update
    if not kwargs:
        print("No fields provided for update.")
        return False

    # Execute update_one using $set with the kwargs dictionary
    result = db.events.update_one(
        filter={"event_id": event_id},
        update={"$set": kwargs}
    )

    if result.modified_count > 0:
        #print(f"Updated event {event_id}!")
        return True
    else:
        #print(f"No event found with ID: {event_id} or field values unchanged.")
        return False
    
def delete_event(event_id: str) -> bool:
    """Delete one event document by event_id. Returns True if successful, False otherwise."""
    result = db.events.delete_one({"event_id": event_id})
    if result.deleted_count > 0:
        #print(f"Deleted event with ID: {event_id}")
        return True
    else:
        #print(f"No event found with ID: {event_id}")
        return False

def get_next_user_id() -> str:
    """
    Increments the counter and returns the formatted ID (e.g., 'USR002').
    """
    counter = db.counters_user.find_one_and_update(
        filter={"_id": "user_id"},
        update={"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    seq_number = counter["seq"]
    
    # Format with prefix and 3-digit padding (e.g., 101 -> 'EVT101', 9 -> 'EVT009')
    return f"USR{seq_number:03d}"

def create_user(new_user: dict) -> str:
    """Inserts one user document. Stores a hash of the email address instead of the raw value.""" 
    u = {
        "name":       new_user["name"],
        "email":      pseudonymise(new_user["email"]),
        "join_date":  new_user["join_date"],
        "interests":  new_user["interests"],
    }
    u["user_id"] = get_next_user_id()

    result = db.users.insert_one(u)
    #print(f"Inserted user with ID: {u['user_id']}")
    return str(result.inserted_id)

def aggregate_events_by_category() -> list[dict]:
    """Analyzes the event documents using aggregation pipeline."""
    pipeline = [
        { "$group": {
            "_id": "$category",
            "events_count": { "$sum": 1 },
            "total_available_tickets": { "$sum": "$available_tickets" },
            "avg_price": { "$avg": "$price" }
        }},
        { "$sort":  { "avg_price": -1 } },
        { "$limit": 10 },
        {"$project": {
            "category": "$_id", # map _id back to category
            "events_count": 1,
            "total_available_tickets": 1,
            "avg_price": 1,
            "_id": 0
        }}
    ]
    return list(db.events.aggregate(pipeline))
