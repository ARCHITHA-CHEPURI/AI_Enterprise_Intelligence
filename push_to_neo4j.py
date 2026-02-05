from neo4j import GraphDatabase
import json

# 🔐 CONNECTION DETAILS (THIS IS WHERE YOU PUT THEM)
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "neo4jkgraphs"   # <-- put the password you set

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def push_triples(triples):
    with driver.session() as session:
        for t in triples:
            session.run(
                f"""
                MERGE (s:Entity {{name: $subject}})
                MERGE (o:Entity {{name: $object}})
                MERGE (s)-[:{t['predicate']}]->(o)
                """,
                subject=t["subject"],
                object=t["object"]
            )

with open("refined_triples.json") as f:
    triples = json.load(f)

push_triples(triples)
driver.close()
