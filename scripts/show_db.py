import sqlite3
import pandas as pd
from pathlib import Path

def show_database_content():
    db_path = Path(__file__).parent.parent / "ingestion.db"
    
    if not db_path.exists():
        print("Database not found!")
        return

    conn = sqlite3.connect(db_path)
    
    # query to get the summary
    query = "SELECT id, filename, file_type, ingested_at FROM ingested_documents"
    
    try:
        df = pd.read_sql_query(query, conn)
        
        print(f"\n--- Database Content: {db_path.name} ---")
        print(f"Total Records: {len(df)}\n")
        
        # Adjust display options for better visibility in terminal
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.colheader_justify', 'left')

        print(df)
        print("\n" + "="*50)
        print("NOTE: 'content' and 'metadata' columns are hidden from this summary view")
        print("because they contain large JSON strings.")
        print("="*50)
        
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_database_content()
