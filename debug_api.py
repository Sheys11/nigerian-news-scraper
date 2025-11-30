import sqlite3

def inspect_db():
    conn = sqlite3.connect("nigerian_news.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check schema
    cursor.execute("PRAGMA table_info(tweets)")
    columns = cursor.fetchall()
    print("Columns in DB:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")
        
    # Check row keys
    cursor.execute("SELECT * FROM tweets LIMIT 1")
    row = cursor.fetchone()
    if row:
        print("\nRow keys:")
        print(row.keys())
    else:
        print("\nNo rows found")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
