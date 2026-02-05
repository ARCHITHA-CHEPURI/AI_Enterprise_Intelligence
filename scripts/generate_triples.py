import json
from pathlib import Path

# Configuration
INPUT_FILE = Path(__file__).parent.parent / "relationship_extraction_output.json"
OUTPUT_FILE = Path(__file__).parent.parent / "refined_triples.json"

def main():
    print(f"Reading refined relationships from {INPUT_FILE}...")
    
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    triples = []
    
    for doc in data:
        doc_id = doc.get("document_id")
        relationships = doc.get("relationships", [])
        
        for rel in relationships:
            triples.append({
                "source_document": doc_id,
                "subject": rel["subject"],
                "predicate": rel["predicate"],
                "object": rel["object"]
            })

    print(f"Extracted {len(triples)} triples.")
    print(f"Saving to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(triples, f, indent=4)
        
    print("Success. Triples generation complete.")

if __name__ == "__main__":
    main()
