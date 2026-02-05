import sys
import os

# Ensure scripts can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.rag_pipeline import retrieve

def test_retrieval_refinement():
    query = "What were the quarterly earnings for Wipro?"
    print(f"Testing Query: '{query}'")
    
    results = retrieve(query)
    
    print(f"\nRetrieved {len(results)} chunks.")
    
    # Check if any result is NOT Wipro
    irrelevant_count = 0
    for i, res in enumerate(results):
        source = res['source'].lower()
        print(f"Result {i+1}: {source}")
        if "wipro" not in source and "wipro" not in res['text'].lower():
            if "ibm" in source or "nike" in source:
                print(f"  [FAIL] Found irrelevant source: {source}")
                irrelevant_count += 1
    
    if irrelevant_count == 0:
        print("\n[SUCCESS] All results appear relevant to Wipro.")
    else:
        print(f"\n[WARNING] Found {irrelevant_count} irrelevant outcomes.")

if __name__ == "__main__":
    test_retrieval_refinement()
