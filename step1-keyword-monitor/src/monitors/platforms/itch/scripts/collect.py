#!/usr/bin/env python3
"""
itch.io 趋势数据采集
抓取 itch.io 首页的热门游戏（Popular Games）
"""

import sqlite3
import json
import urllib.request
import re
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "itch.db"
URL = "https://itch.io/games"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            game_id TEXT NOT NULL,
            name TEXT NOT NULL,
            link TEXT NOT NULL,
            author TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(timestamp)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS first_seen (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            author TEXT NOT NULL,
            first_date TEXT NOT NULL
        )
    """)
    conn.commit()

def fetch_itch_popular():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
    
    games = []
    # 提取游戏数据
    # <div class="game_cell" data-game_id="12345">
    # ... <div class="game_title"><a ...>Game Name</a></div>
    # ... <div class="game_author"><a ...>Author</a></div>
    
    # 匹配每一个游戏单元格
    cells = re.findall(r'<div class="game_cell"[^>]*data-game_id="(\d+)"[^>]*>(.*?)</div>\s*</div>\s*</div>', content, re.DOTALL)
    
    # 如果上面的正则没匹配到，换个更宽松的
    if not cells:
        # 匹配标题和链接，顺便带上 ID
        matches = re.finditer(r'data-game_id="(\d+)".*?<div class="game_title">\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<div class="game_author">\s*<a[^>]*>(.*?)</a>', content, re.DOTALL)
        for m in matches:
            games.append({
                "id": m.group(1),
                "link": m.group(2),
                "name": m.group(3).strip(),
                "author": m.group(4).strip()
            })
    else:
        for game_id, inner_html in cells:
            title_match = re.search(r'<div class="game_title">\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', inner_html, re.DOTALL)
            author_match = re.search(r'<div class="game_author">\s*<a[^>]*>(.*?)</a>', inner_html, re.DOTALL)
            
            if title_match:
                link = title_match.group(1)
                name = title_match.group(2).strip()
                author = author_match.group(1).strip() if author_match else "Unknown"
                games.append({"id": game_id, "name": name, "link": link, "author": author})
            
    return games

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] 开始采集 itch.io 数据...")

    try:
        games = fetch_itch_popular()
    except Exception as e:
        print(f"[{ts}] ❌ itch.io 采集失败: {e}")
        return

    if not games:
        print(f"[{ts}] ⚠️ 未抓取到热门游戏数据")
        return

    print(f"[{ts}] 获取到 {len(games)} 个热门游戏")

    # 写入数据库
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    rows = [(g["id"], g["name"], g["link"], g["author"], ts) for g in games]
    conn.executemany(
        "INSERT INTO snapshots (game_id, name, link, author, timestamp) VALUES (?, ?, ?, ?, ?)",
        rows
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for g in games:
        conn.execute(
            "INSERT OR IGNORE INTO first_seen (game_id, name, author, first_date) VALUES (?, ?, ?, ?)",
            (g["id"], g["name"], g["author"], today)
        )

    conn.commit()
    conn.close()
    print(f"[{ts}] ✅ 成功写入 {len(rows)} 条 itch.io 快照")

if __name__ == "__main__":
    main()
