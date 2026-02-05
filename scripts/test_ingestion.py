import os
import json
import shutil
import pandas as pd
from data_ingestion import DataIngestor
from pathlib import Path

def test_pipeline():
    # Setup test environment
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    # Create dummy files
    # 1. CSV
    df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
    df.to_csv(test_dir / "test.csv", index=False)
    
    # 2. JSON
    with open(test_dir / "test.json", "w") as f:
        json.dump({"key": "value", "list": [1, 2, 3]}, f)

    # 3. Email (.eml)
    eml_content = b"""From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 20 Jan 2025 10:00:00 -0500

This is a test email body.
"""
    with open(test_dir / "test.eml", "wb") as f:
        f.write(eml_content)
    
    # Initialize Ingestor (no DB arg needed now)
    ingestor = DataIngestor()
    
    print("Running ingestion on test data...")
    ingestor.ingest_directory(test_dir)
    
    # Verify JSON output
    output_file = Path("ingested_data.json")
    if output_file.exists():
        with open(output_file, "r") as f:
            data = json.load(f)
        
        print(f"\nFound {len(data)} documents in JSON output:")
        for item in data:
            print(f" - {item.get('filename')} ({item.get('file_type')})")
        
        # Verify content
        assert len(data) >= 3, "Should have ingested csv, json, and email"
        types = [item['file_type'] for item in data]
        assert 'csv' in types
        assert 'json' in types
        assert 'email' in types
        
        print("\nStructure Verification Passed!")
    else:
        print("Output file not found!")
        exit(1)

    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print("\nTest Complete!")

if __name__ == "__main__":
    test_pipeline()
