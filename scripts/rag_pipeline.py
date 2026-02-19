import faiss
import numpy as np
import json
import os
import requests
from sentence_transformers import SentenceTransformer

# Configuration
INDEX_FILE = os.getenv("INDEX_FILE", "faiss_index.bin")
METADATA_FILE = os.getenv("METADATA_FILE", "vector_metadata.json")
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Initialize models and data lazily
_model = None
_index = None
_metadata = None

def get_retrieval_assets():
    """Load and return retrieval models and metadata lazily."""
    global _model, _index, _metadata
    if _model is None:
        try:
            print("Loading retrieval models and data...")
            _model = SentenceTransformer(MODEL_NAME)
            if os.path.exists(INDEX_FILE):
                _index = faiss.read_index(INDEX_FILE)
            else:
                print(f"Warning: Index file {INDEX_FILE} not found.")
            
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    _metadata = json.load(f)
            else:
                print(f"Warning: Metadata file {METADATA_FILE} not found.")
        except Exception as e:
            print(f"Error loading retrieval assets: {e}")
    return _model, _index, _metadata

def retrieve(query, k=8):
    """Retrieve top-k relevant chunks for a query with keyword filtering and similarity scores."""
    model, index, metadata = get_retrieval_assets()
    if not model or not index or not metadata:
        return []

    # 1. Embed query
    query_vector = model.encode([query]).astype("float32")
    
    # 2. Search index (fetch more candidates to allow filtering)
    distances, indices = index.search(query_vector, k * 3)
    
    candidates = []
    # distances are squared L2 distances in FAISS by default if using IndexFlatL2
    # We want to convert them to a confidence score (0-1)
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(metadata):
            chunk = metadata[idx].copy()
            # Heuristic conversion: confidence = 1 / (1 + distance)
            chunk['score'] = float(1 / (1 + distances[0][i]))
            candidates.append(chunk)
    
    # 3. Post-Process: Filter by Company/Entity if detected
    query_lower = query.lower()
    known_entities = ["wipro", "ibm", "nike", "microsoft", "google", "amazon", "apple", "meta", "tesla"]
    active_entities = [ent for ent in known_entities if ent in query_lower]
    
    if active_entities:
        filtered_results = []
        for cand in candidates:
            text_lower = cand['text'].lower()
            source_lower = cand['source'].lower()
            if any(ent in text_lower or ent in source_lower for ent in active_entities):
                filtered_results.append(cand)
        
        if len(filtered_results) >= 1:
            return filtered_results[:k]
            
    return candidates[:k]

def calculate_self_eval(query, answer, context):
    """Ask LLM to evaluate accuracy and precision of its own answer."""
    eval_prompt = f"""### Task:
Evaluate the quality of the following RAG answer based on the provided context.

### Context:
{context}

### Question:
{query}

### Answer:
{answer}

### Instructions:
Rate the Accuracy (faithfulness to context) and Precision (relevance to question) on a scale of 0 to 1.
Output ONLY a JSON object like this: {{"accuracy": 0.95, "precision": 0.9}}

### Evaluation:
"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": eval_prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        eval_data = json.loads(result.get("response", "{}"))
        return eval_data.get("accuracy", 0.0), eval_data.get("precision", 0.0)
    except:
        return 0.5, 0.5 # Fallback

def generate_answer_with_metrics(query, context_chunks):
    """Generate answer and calculate metrics."""
    if not context_chunks:
        return "I couldn't find any relevant information.", [], 0, 0, 0

    # 1. Generate Answer
    context_text = "\n\n".join([f"Source: {c['source']}\nContent: {c['text']}" for c in context_chunks])
    prompt = f"""### Context:
{context_text}

### Question:
{query}

### Instructions:
Answer the question using ONLY the provided context. If the answer is not in the context, say "I don't have enough information to answer this."

### Answer:
"""
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        
        # 2. Calculate Confidence (Mean of top context scores)
        confidence = np.mean([c.get('score', 0) for c in context_chunks[:3]]) if context_chunks else 0
        
        # 3. Calculate Accuracy and Precision via self-reflection
        accuracy, precision = calculate_self_eval(query, answer, context_text[:2000]) # Truncate for eval speed
        
        return answer, context_chunks, float(accuracy), float(precision), float(confidence)
    except Exception as e:
        return f"Error: {str(e)}", [], 0, 0, 0

def generate_answer(query, context_chunks):
    """Legacy wrapper for backward compatibility."""
    answer, _, _, _, _ = generate_answer_with_metrics(query, context_chunks)
    return answer

def main():
    print("--- RAG Chatbot (FAISS + Ollama) ---")
    print("Type 'exit' to quit.")
    
    while True:
        query = input("\nUser: ")
        if query.lower() in ["exit", "quit"]:
            break
            
        print("Searching...")
        context = retrieve(query)
        
        if not context:
            print("Bot: No relevant information found.")
            continue
            
        print("Generating response...")
        answer = generate_answer(query, context)
        
        print(f"\nBot: {answer}")
        print("\nSources used:")
        for c in context:
            print(f"- {c['source']} (ID: {c['chunk_id']})")

if __name__ == "__main__":
    main()