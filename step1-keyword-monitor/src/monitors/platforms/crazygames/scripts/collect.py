#!/usr/bin/env python3
"""
CrazyGames 新游戏采集
抓取 CrazyGames 的 'New Games' 列表
"""

import sqlite3
import json
import urllib.request
import re
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "crazygames.db"
URL = "https://www.crazygames.com/new"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            game_id TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            category TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(timestamp)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS first_seen (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            first_date TEXT NOT NULL
        )
    """)
    conn.commit()

def fetch_new_games():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
    
    # 提取 __NEXT_DATA__ JSON
    match = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find __NEXT_DATA__ script tag")
    
    data = json.loads(match.group(1))
    
    # 尝试多种路径获取游戏列表
    games_list = []
    try:
        # 路径 1
        raw_data = data['props']['pageProps']['data']['games']
        if isinstance(raw_data, list):
            games_list = raw_data
        elif isinstance(raw_data, dict) and 'items' in raw_data:
            games_list = raw_data['items']
    except (KeyError, TypeError):
        try:
            # 路径 2
            raw_data = data['props']['pageProps']['games']
            if isinstance(raw_data, list):
                games_list = raw_data
            elif isinstance(raw_data, dict) and 'items' in raw_data:
                games_list = raw_data['items']
        except (KeyError, TypeError):
            print("⚠️ Could not find games list in expected JSON paths")
    
    results = []
    for g in games_list:
        if not isinstance(g, dict):
            continue
            
        # 过滤掉非游戏对象
        if 'slug' not in g:
            continue
            
        results.append({
            "id": str(g.get('id', '')),
            "name": g.get('name', 'Unknown'),
            "slug": g.get('slug', ''),
            "category": g.get('categoryName', 'Unknown')
        })
    return results

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] 开始采集 CrazyGames 新游戏...")

    try:
        games = fetch_new_games()
    except Exception as e:
        print(f"[{ts}] ❌ CrazyGames 采集失败: {e}")
        return

    if not games:
        print(f"[{ts}] ⚠️ 未抓取到新游戏数据")
        return

    print(f"[{ts}] 获取到 {len(games)} 个新游戏")

    # 写入数据库
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    rows = [(g["id"], g["name"], g["slug"], g["category"], ts) for g in games]
    conn.executemany(
        "INSERT INTO snapshots (game_id, name, slug, category, timestamp) VALUES (?, ?, ?, ?, ?)",
        rows
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for g in games:
        conn.execute(
            "INSERT OR IGNORE INTO first_seen (game_id, name, category, first_date) VALUES (?, ?, ?, ?)",
            (g["id"], g["name"], g["category"], today)
        )

    conn.commit()
    conn.close()
    print(f"[{ts}] ✅ 成功写入 {len(rows)} 条 CrazyGames 快照")

if __name__ == "__main__":
    main()
