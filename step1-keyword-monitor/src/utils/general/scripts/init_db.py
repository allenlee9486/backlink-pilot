import sqlite3
import os
from pathlib import Path

def init_db():
    db_path = Path("monitors/general/data/general.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create first_seen table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS first_seen (
        game_id TEXT PRIMARY KEY,
        name TEXT,
        first_date TEXT,
        category TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Initialized {db_path}")

if __name__ == "__main__":
    init_db()
