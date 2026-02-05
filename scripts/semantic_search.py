# MILESTONE-3: SEMANTIC SEARCH IMPLEMENTATION

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# STEP 1: LOAD FAISS INDEX
# --------------------------------------------------

faiss_index = faiss.read_index("faiss_index.bin")
print("FAISS index loaded")

# --------------------------------------------------
# STEP 2: LOAD METADATA
# --------------------------------------------------

with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print("Metadata loaded")

# --------------------------------------------------
# STEP 3: LOAD EMBEDDING MODEL
# --------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded")

# --------------------------------------------------
# STEP 4: SEMANTIC SEARCH FUNCTION
# --------------------------------------------------

def semantic_search(query, top_k=3):
    query_embedding = model.encode([query]).astype("float32")
    distances, indices = faiss_index.search(query_embedding, top_k)

    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(metadata):
            results.append({
                "chunk_index": int(idx),
                "metadata": metadata[idx]
            })

    return results


# --------------------------------------------------
# STEP 5: TEST SEARCH
# --------------------------------------------------

if __name__ == "__main__":
    query = "senior employee with high income and many years at company?"
    # Since our data is HR/Employee focused based on previous files, 
    # let's try a query relevant to the actual data if possible, 
    # but I'll stick to the user's sample as well.
    sample_queries = [
        "senior employee with high income and many years at company",
        "Who is Aarav Sharma?",
        "Details about employee attrition"
    ]

    for q in sample_queries:
        print(f"\nSearching for: {q}")
        results = semantic_search(q)

        print("\nSemantic Search Results:\n")
        for i, res in enumerate(results, 1):
            print(f"Result {i}:")
            print("Chunk Index:", res["chunk_index"])
            print("Metadata:", res["metadata"])
            print("-" * 40)
