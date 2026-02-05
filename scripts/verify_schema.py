import json
from pathlib import Path

def verify_schema():
    file_path = Path(__file__).parent.parent / "ingested_data.json"
    if not file_path.exists():
        print("Data file not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Checking schema for {len(data)} documents...\n")
    
    seen_types = set()
    unified_keys = {'filename', 'file_type', 'content', 'metadata'}
    
    for item in data:
        ftype = item.get('file_type')
        if ftype not in seen_types:
            keys = set(item.keys())
            # Ingested_at might be present or not depending on old/new runs, primarily check core schema
            # Let's filter to core keys
            core_keys = {k for k in keys if k in unified_keys}
            
            print(f"File Type: {ftype.upper()}")
            print(f" - Example File: {item.get('filename')}")
            print(f" - Keys Found: {sorted(list(keys))}")
            
            if unified_keys.issubset(keys):
                print(f" -> VERIFIED: Contains unified structure {sorted(list(unified_keys))}")
            else:
                print(f" -> FAILED: Missing keys {unified_keys - keys}")
            print("-" * 40)
            seen_types.add(ftype)

if __name__ == "__main__":
    verify_schema()
