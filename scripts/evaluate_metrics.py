
import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer

# Configuration
INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "vector_metadata.json"
GT_FILE = "evaluation_gt.json"
REPORT_FILE = "evaluation_report.md"
MODEL_NAME = "all-MiniLM-L6-v2"
K = 5

def evaluate():
    print("--- Starting Retrieval Evaluation ---")
    
    # 1. Load Resources
    print("Loading resources...")
    if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE) or not os.path.exists(GT_FILE):
        print(f"Error: Missing validation files. Ensure {INDEX_FILE}, {METADATA_FILE}, and {GT_FILE} exist.")
        return

    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    with open(GT_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    model = SentenceTransformer(MODEL_NAME)
    
    # 2. Evaluate
    results = []
    total_queries = len(ground_truth)
    total_accuracy = 0
    total_precision = 0

    print(f"Evaluating {total_queries} queries with K={K}...")
    
    report_lines = []
    report_lines.append(f"# Evaluation Report (Retrieval Only)\n")
    report_lines.append(f"**Evaluation Mode**: Retrieval Accuracy Analysis")
    report_lines.append(f"**Metric K**: {K}\n")
    report_lines.append("| Query | Expected Source | Top-K Found | Accuracy | Precision@K |")
    report_lines.append("|---|---|---|---|---|")

    for entry in ground_truth:
        query = entry["query"]
        expected_source = entry["expected_source"]
        
        # Search
        query_vector = model.encode([query]).astype("float32")
        distances, indices = index.search(query_vector, K)
        
        # Analyze Results
        retrieved_sources = []
        relevant_hits = 0
        
        for idx in indices[0]:
            if idx != -1 and idx < len(metadata):
                chunk = metadata[idx]
                r_source = chunk.get("source", "Unknown") 
                # Handle potential full paths in source by taking basename if needed, 
                # but dataset seems to use basenames. We'll use strict string check first.
                if os.path.basename(r_source) == expected_source:
                    relevant_hits += 1
                retrieved_sources.append(os.path.basename(r_source))
        
        # Metrics for this query
        is_correct = any(expected_source in src for src in retrieved_sources) # Loose check for match
        accuracy = 1 if is_correct else 0
        precision = relevant_hits / K
        
        total_accuracy += accuracy
        total_precision += precision
        
        # Format for table
        found_sources_str = "<br>".join(retrieved_sources[:3]) + ("..." if len(retrieved_sources)>3 else "")
        status_icon = "✅" if is_correct else "❌"
        
        report_lines.append(f"| {query} | `{expected_source}` | {found_sources_str} | {status_icon} | {precision:.2f} |")
        
        print(f"Query: {query} -> Accuracy: {accuracy}, Precision: {precision:.2f}")

    # 3. Calculate Aggregates
    avg_accuracy = (total_accuracy / total_queries) * 100
    avg_precision = total_precision / total_queries
    
    summary = f"\n### Aggregate Metrics\n- **Mean Top-{K} Accuracy**: {avg_accuracy:.2f}%\n- **Mean Precision@{K}**: {avg_precision:.4f}\n"
    report_lines.append(summary)
    
    # 4. Save Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print("\n--- Evaluation Complete ---")
    print(f"Mean Accuracy: {avg_accuracy:.2f}%")
    print(f"Mean Precision: {avg_precision:.4f}")
    print(f"Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    evaluate()
