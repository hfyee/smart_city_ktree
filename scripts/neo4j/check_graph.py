"""
Neo4j test script to read node relationships
"""
from db.connections import get_neo4j_driver
import pandas as pd

driver = get_neo4j_driver()

def print_nodes_and_props():
    query = """
        MATCH (n)
        RETURN labels(n) AS Labels, properties(n) AS Properties
        LIMIT 100
    """
    with driver.session() as session:
        result = session.run(query)

        for record in result:
            print(type(record))
            print(record)

def print_graph_incl_relationships():
    query = """
        MATCH (n)-[r]->(m) 
        RETURN n, r, m 
        LIMIT 100
    """

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            print(type(record))
            print(record)


if __name__ == '__main__':
    if False:
        print(f"Print the entire graph incl. relationsips:")
        print_graph_incl_relationships()
        print()

    if True:
        print(f"Print all nodes and properties:")
        print_nodes_and_props()
        print()
