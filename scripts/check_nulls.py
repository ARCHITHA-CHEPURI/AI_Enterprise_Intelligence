import json
import pandas as pd
from pathlib import Path

def count_nulls_recursive(data):
    count = 0
    if isinstance(data, dict):
        for v in data.values():
            count += count_nulls_recursive(v)
    elif isinstance(data, list):
        for i in data:
            count += count_nulls_recursive(i)
    elif data is None:
        count = 1
    return count

def check_nulls():
    file_path = Path(__file__).parent.parent / "ingested_data.json"
    if not file_path.exists():
        print("Data file not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Checking {len(data)} documents for Null/NaN values...")
    
    total_nulls = 0
    files_with_nulls = []

    for item in data:
        fname = item.get('filename', 'unknown')
        content = item.get('content')
        
        # Recursive check for None values
        null_count = count_nulls_recursive(content)
        
        if null_count > 0:
            total_nulls += null_count
            files_with_nulls.append(f"{fname} ({null_count} nulls)")

    if total_nulls == 0:
        print("VERIFIED: No Null values found.")
    else:
        print(f"FOUND {total_nulls} NULL VALUES in the following files:")
        for f in files_with_nulls:
            print(f" - {f}")

if __name__ == "__main__":
    check_nulls()
