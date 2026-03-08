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
        type TEXT,
        lat REAL DEFAULT 0.0,
        lng REAL DEFAULT 0.0
    )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn

def add_discovery(description: str, type: str, embedding: list[float], lat: float = 0.0, lng: float = 0.0):
    conn = get_connection()
    c = conn.cursor()
    # Insert metadata
    c.execute('INSERT INTO discovery_metadata (description, type, lat, lng) VALUES (?, ?, ?, ?)', (description, type, lat, lng))
    discovery_id = c.lastrowid
    
    # Insert embedding into vector table
    # Requires packing the float array into bytes if using sqlite-vec, but let's assume we can insert JSON/list for simple sqlite-vec usage depending on version,
    # Actually, sqlite-vec uses `vec_f32` typically or we can use the helper function. Assumes json serialization or binary here.
    # We will use simple placeholders for this hackathon skeleton
    import json
    # In sqlite-vec, embedding should be a blob, let's just insert as string for mock purposes unless we strictly serialize floats as bytes.
    # For a real implementation, we use struct.pack
    import struct
    embedding_blob = struct.pack(f"{len(embedding)}f", *embedding)
    
    c.execute('INSERT INTO memories (id, embedding) VALUES (?, ?)', (discovery_id, embedding_blob))
    conn.commit()
    conn.close()
    return discovery_id

def get_all_discoveries():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, timestamp, description, type, lat, lng FROM discovery_metadata ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    print("Database Initialized with sqlite-vec extensions.")
