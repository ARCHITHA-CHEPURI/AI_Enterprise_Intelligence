import faiss
import numpy as np
import json
import os

def setup_vector_db():
    print("Loading embeddings and chunks...")
    
    embeddings_file = "embeddings.npy"
    chunks_file = "processed_chunks.json"
    
    if not os.path.exists(embeddings_file) or not os.path.exists(chunks_file):
        print("Error: Missing embeddings.npy or processed_chunks.json. Please run the embedding generation pipeline first.")
        return

    # Load embeddings
    embeddings = np.load(embeddings_file).astype("float32")
    
    # Load chunks (for metadata)
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if len(embeddings) != len(chunks):
        print(f"Warning: Number of embeddings ({len(embeddings)}) does not match number of chunks ({len(chunks)})!")

    # Get dimension
    dimension = embeddings.shape[1]
    print(f"Embedding dimension: {dimension}")
    print(f"Total vectors: {len(embeddings)}")

    # Create IndexFlatL2 (Exact search using L2 distance)
    index = faiss.IndexFlatL2(dimension)
    
    # Add embeddings to index
    print("Adding vectors to FAISS index...")
    index.add(embeddings)
    
    # Save index
    index_file = "faiss_index.bin"
    faiss.write_index(index, index_file)
    print(f"FAISS index saved to {index_file}")

    # Save metadata for mapping
    # We save only the ID and source to keep the file small, 
    # as retrieved indices from FAISS will map to this list.
    metadata = []
    for chunk in chunks:
        metadata.append({
            "chunk_id": chunk.get("chunk_id"),
            "source": chunk.get("source"),
            "text": chunk.get("text") # Keeping text for easy retrieval in RAG phase
        })
    
    metadata_file = "vector_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to {metadata_file}")
    print("Vector database setup completed successfully!")

if __name__ == "__main__":
    setup_vector_db()
