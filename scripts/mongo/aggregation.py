"""
MongoDB script for aggregation
Aggregation processes documents through a pipeline of stages to transform and compute results directly on the database server.
"""
import json
import pathlib
import config
from db.connections import get_mongo_client

client = get_mongo_client()
db = client[config.MONGO_DB_2] if client else None
print(f"Connected to MongoDB. Using database '{config.MONGO_DB_2}'.")

# Recommended order: $match, $lookup, $unwind, $group
def aggregate_citizen_complaints_by_category() -> list[dict]:
    """Analyzes the event documents using aggregation pipeline."""
    complaints_col = db["citizen_complaints"]
    pipeline = [
        #{ "$match": { 
        #    "priority": "Medium"
        #}}
        { "$group": {
            "_id": "$category",
            "complaints_count": { "$sum": 1 },
            "earliest_date": { "$min": "$date_submitted" },
            "latest_date": { "$max": "$date_submitted" }
        }},
        { "$sort":  { "complaints_count": -1 } },
        { "$limit": 10 },
        {"$project": {
            "category": "$_id", # map _id back to category
            "complaints_count": 1,
            "earliest_date": 1,
            "latest_date": 1,
            "_id": 0
        }}
    ]
    return list(complaints_col.aggregate(pipeline))

if __name__ == '__main__':
    print("Category|Complaints Count|Earliest Date|Latest Date")
    for r in aggregate_citizen_complaints_by_category():
        print(f"  {r['category']}:  {r['complaints_count']}   {r['earliest_date']}   {r['latest_date']}")
