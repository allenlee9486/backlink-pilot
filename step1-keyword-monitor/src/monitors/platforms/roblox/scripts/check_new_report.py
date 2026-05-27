import sqlite3
from pathlib import Path

DB_PATH = Path("monitors/roblox/data/roblox-trends.db")

def check_games(ids):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    for gid in ids:
        cursor.execute("SELECT name, created_at, first_date FROM first_seen WHERE game_id=?", (gid,))
        row = cursor.fetchone()
        if row:
            print(f"ID: {gid}, Created: {row[1]}, First: {row[2]}")
        else:
            print(f"ID: {gid} not found.")
    conn.close()

if __name__ == "__main__":
    check_games(["136066387156306", "125579556815131", "88207898227053", "128469876423260", "139054513518556"])
