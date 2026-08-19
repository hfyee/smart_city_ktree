"""
Neo4j helper functions called by page scripts
"""
import json
import re
from pathlib import Path
from unittest import result
from db.connections import get_neo4j_driver
from db.utils import load, mask_name
from neo4j import Driver
import networkx as nx
from networkx.algorithms.community import louvain_communities

# ── Connect ───────────────────────────────────────────────────────────────
driver = get_neo4j_driver()
#print("Connected to Neo4j.")

# Create uniqueness constraints on a new database
def set_graph_constraints() -> None:
    ...

# ── CRUD operations ───────────────────────────────────────────────────────
def get_next_venue_id() -> str:
    ...

def get_next_organiser_id() -> str:
    ...

def get_next_event_id() -> str:
    ...

def create_venue(new_venue: dict) -> str:
    ...

def create_organiser(new_organiser: dict) -> str:
    ...

def create_event(new_event: dict) -> str:
    ...

def read_events(category: str, max_price: float) -> list[dict]:
    ...

def read_who_what_where(category: str, max_price: float) -> list[dict]:
    ...

def get_event_nodes_count() -> int:
    ...

def update_available_tickets(event_id: str, new_available_tickets: int) -> bool:
    ...

def delete_event(event_id: str) -> int:
    ...

# ── Booking related ───────────────────────────────────────────────────────
def get_next_booking_id() -> str:
    ...

def add_booking_relationship(new_booking: dict) -> bool:
    ...

def find_booking_info(user_id: str, event_id: str) -> list[dict]:
    ...

# ── Multi-hop traversal ───────────────────────────────────────────────────────
def find_events_by_organisers_at_same_venue(venue_name: str) -> list[dict]:
    ...

# ── Graph algo with NetworkX ─────────────────────────────────────────────────────
def run_cypher(cypher, params=None):
    ...
    
def build_network_graph() -> nx.Graph:
    ...

def community_detection(G: nx.Graph) -> list[set]:
    ...
