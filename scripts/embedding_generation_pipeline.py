import json
import numpy as np
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
INPUT_FILE = "ingested_data.json"
OUTPUT_CHUNKS_FILE = "processed_chunks.json"
OUTPUT_EMBEDDINGS_FILE = "embeddings.npy"
MODEL_NAME = "all-MiniLM-L6-v2"

# --------------------------------------------------
# STEP 1: LOAD AND PREPROCESS DATA
# --------------------------------------------------
def preprocess_content(entry):
    """
    Converts raw entry content into a clean text string for chunking.
    """
    file_type = entry.get("file_type", "unknown")
    content = entry.get("content")
    
    if content is None:
        return ""

    # If content is a string, check if it's a stringified JSON
    if isinstance(content, str):
        content_stripped = content.strip()
        if (content_stripped.startswith('[') and content_stripped.endswith(']')) or \
           (content_stripped.startswith('{') and content_stripped.endswith('}')):
            try:
                import json as json_lib
                content = json_lib.loads(content_stripped)
            except:
                # Not valid JSON, treat as regular string
                pass

    if isinstance(content, list):
        # Handle lists (like CSV rows or JSON arrays of objects)
        sentences = []
        for item in content:
            if isinstance(item, dict):
                # Filter out nulls and join parts
                parts = [f"{k}: {v}" for k, v in item.items() if v is not None and str(v).strip() != ""]
                if parts:
                    sentences.append(", ".join(parts) + ".")
            elif isinstance(item, str):
                sentences.append(item)
            else:
                sentences.append(str(item))
        return " ".join(sentences)
    
    elif isinstance(content, dict):
        # Join all string values for dictionaries (like emails or JSON objects)
        parts = []
        for k, v in content.items():
            if v is not None and str(v).strip() != "":
                parts.append(f"{k}: {v}")
        return ". ".join(parts) + "."
    
    elif isinstance(content, str):
        return content
    
    return str(content)

def load_data(path):
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return []
    
    print(f"Loading data from {path}...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} documents.")
    return data

# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------
def main():
    # 1. Load Data
    documents = load_data(INPUT_FILE)
    if not documents:
        return

    # 2. Text Preparation & Chunking
    print("Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    all_chunk_metadata = []
    texts_to_embed = []

    for doc in documents:
        filename = doc.get("filename", "unknown")
        print(f"Processing {filename}...")
        raw_text = preprocess_content(doc)
        
        if not raw_text.strip():
            continue
            
        chunks = text_splitter.split_text(raw_text)
        
        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"{filename}_chunk_{idx}"
            all_chunk_metadata.append({
                "chunk_id": chunk_id,
                "source": filename,
                "text": chunk_text
            })
            texts_to_embed.append(chunk_text)

    print(f"Total chunks created: {len(texts_to_embed)}")

    if not texts_to_embed:
        print("No text found to embed.")
        return

    # 3. Load Model
    print(f"Loading embedding model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    # 4. Generate Embeddings
    print("Generating embeddings (this may take a while)...")
    embeddings = model.encode(
        texts_to_embed,
        show_progress_bar=True
    )
    embeddings = np.array(embeddings)
    print("Embedding generation completed.")
    print("Embedding shape:", embeddings.shape)

    # 5. Save Results
    print(f"Saving chunks to {OUTPUT_CHUNKS_FILE}...")
    with open(OUTPUT_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunk_metadata, f, indent=2)

    print(f"Saving embeddings to {OUTPUT_EMBEDDINGS_FILE}...")
    np.save(OUTPUT_EMBEDDINGS_FILE, embeddings)

    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
