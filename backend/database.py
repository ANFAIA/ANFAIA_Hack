import sqlite3
import sqlite_vec
import os

DB_PATH = "omnibot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    
    # Example Vector Table representing the Discovery Events
    conn.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS memories USING vec0(
        id INTEGER PRIMARY KEY,
        embedding FLOAT[768] -- Assuming 768-d Gemini context embedding
    )
    ''')
    
    # Accompanying Metadata Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS discovery_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        type TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database Initialized with sqlite-vec extensions.")
