#!/usr/bin/env python3
"""
Steam 趋势数据采集
从 Steam Top Sellers 页面抓取当前热门游戏
"""

import sqlite3
import json
import urllib.request
import re
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "steam-trends.db"
STATS_URL = "https://store.steampowered.com/search/?filter=topsellers"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            game_id TEXT NOT NULL,
            name TEXT NOT NULL,
            players INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(timestamp)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS first_seen (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            first_date TEXT NOT NULL
        )
    """)
    conn.commit()

def fetch_steam_stats():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(STATS_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
    
    games = []
    # 提取 appid 和 title
    # 结构: data-ds-appid="730" ... <span class="title">Counter-Strike 2</span>
    matches = re.finditer(r'data-ds-appid="(\d+)".*?<span class="title">(.*?)</span>', content, re.DOTALL)
    for match in matches:
        game_id = match.group(1)
        name = match.group(2).strip()
        # 记录排名（Steam 搜索页是按排名排列的）
        games.append({"id": game_id, "name": name, "players": 0}) 
    
    return games

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] 开始采集 Steam 数据...")

    try:
        games = fetch_steam_stats()
    except Exception as e:
        print(f"[{ts}] ❌ Steam 采集失败: {e}")
        return

    if not games:
        print(f"[{ts}] ⚠️ 未抓取到数据，请检查页面结构是否变化")
        return

    print(f"[{ts}] 获取到 {len(games)} 个热门游戏")

    # 写入数据库
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    rows = [(g["id"], g["name"], g["players"], ts) for g in games]
    conn.executemany(
        "INSERT INTO snapshots (game_id, name, players, timestamp) VALUES (?, ?, ?, ?)",
        rows
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for g in games:
        conn.execute(
            "INSERT OR IGNORE INTO first_seen (game_id, name, first_date) VALUES (?, ?, ?)",
            (g["id"], g["name"], today)
        )

    conn.commit()
    conn.close()
    print(f"[{ts}] ✅ 成功写入 {len(rows)} 条 Steam 快照")

if __name__ == "__main__":
    main()
