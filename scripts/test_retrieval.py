import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

def test_retrieval():
    print("Loading index and model...")
    index = faiss.read_index("faiss_index.bin")
    with open("vector_metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    queries = [
        "What is the join date of Aarav Sharma?",
        "Tell me about Nike Jordan products on discount.",
        "Who is Rohan Mehta?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        query_vector = model.encode([query]).astype("float32")
        distances, indices = index.search(query_vector, 3)
        
        print("Results:")
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk = metadata[idx]
                print(f"[{i+1}] Source: {chunk['source']} | ID: {chunk['chunk_id']}")
                print(f"    Text: {chunk['text'][:200]}...")

if __name__ == "__main__":
    test_retrieval()
