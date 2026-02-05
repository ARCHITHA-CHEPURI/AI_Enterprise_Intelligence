import faiss
import numpy as np
import json
import os
import requests
import spacy
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "vector_metadata.json"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3.2:1b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Neo4j Details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4jkgraphs"

# Load Spacy for Entity Extraction from Query
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------
print("Initializing Hybrid RAG Components...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
faiss_index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    vector_metadata = json.load(f)

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --------------------------------------------------
# STEP 1: GRAPH RETRIEVAL (Neo4j)
# --------------------------------------------------
def get_graph_context(query_entities):
    """
    Query Neo4j for relationships involving the extracted entities.
    """
    if not query_entities:
        return ""
    
    facts = []
    with neo4j_driver.session() as session:
        for entity in query_entities:
            # Query for direct relationships
            result = session.run(
                "MATCH (s:Entity)-[r]->(o:Entity) "
                "WHERE s.name =~ $entity OR o.name =~ $entity "
                "RETURN s.name as subject, type(r) as predicate, o.name as object LIMIT 10",
                entity=f"(?i).*{entity}.*"
            )
            for record in result:
                facts.append(f"- {record['subject']} {record['predicate']} {record['object']}")
    
    if facts:
        print(f"Found {len(facts)} facts in Knowledge Graph.")
        return "\nKnowledge Graph Facts:\n" + "\n".join(set(facts))
    return ""

# --------------------------------------------------
# STEP 2: VECTOR RETRIEVAL (FAISS)
# --------------------------------------------------
def get_vector_context(query, k=5):
    """
    Retrieve top-k relevant chunks from FAISS.
    """
    query_vector = embedding_model.encode([query]).astype("float32")
    distances, indices = faiss_index.search(query_vector, k)
    
    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(vector_metadata):
            results.append(vector_metadata[idx]['text'])
    
    return "\nSemantic Search Context:\n" + "\n\n".join(results)

# --------------------------------------------------
# STEP 3: HYBRID SEARCH & GENERATION
# --------------------------------------------------
def extract_entities(query):
    """Extract potential entities from the query."""
    doc = nlp(query)
    # Extract Proper Nouns, Nouns and recognized Entities
    entities = [ent.text for ent in doc.ents]
    entities.extend([token.text for token in doc if token.pos_ in ["PROPN", "NOUN"] and not token.is_stop])
    return list(set(entities))

def generate_answer(query):
    # 1. Extract Entities
    entities = extract_entities(query)
    print(f"Extracted Entities: {entities}")

    # 2. Get Context from both sources
    graph_context = get_graph_context(entities)
    vector_context = get_vector_context(query)
    
    combined_context = f"{graph_context}\n\n{vector_context}"
    
    # 3. Build Prompt
    prompt = f"""### Context:
{combined_context}

### Question:
{query}

### Instructions:
Answer the question using the provided Knowledge Graph facts and Semantic Search context. 
If the information is not present, be honest and say you don't know. 
Prioritize accuracy based on the facts provided.

### Answer:
"""
    
    # 4. Generate with Ollama
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    print("Generating hybrid answer...")
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print("--- Hybrid KG + RAG Chatbot Activated ---")
    print("Type 'exit' to quit.")
    
    try:
        while True:
            user_query = input("\nUser: ")
            if user_query.lower() in ["exit", "quit"]:
                break
            
            answer = generate_answer(user_query)
            print(f"\nBot: {answer}")
    finally:
        neo4j_driver.close()

if __name__ == "__main__":
    main()
