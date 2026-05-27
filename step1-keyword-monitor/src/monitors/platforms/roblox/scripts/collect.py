#!/usr/bin/env python3
"""
Roblox 趋势数据采集 — 每小时运行
调用 Rolimons API，将游戏在线数据写入 SQLite
只在榜单更新时段运行，且只在人数变化时写入
"""

import sqlite3
import json
import urllib.request
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "roblox-trends.db"
API_URL = "https://api.rolimons.com/games/v1/gamelist"

# 补充元数据的 API (Roblox 官方)
ROBLOX_API_URL = "https://games.roblox.com/v1/games?universeIds="

# 变化阈值：人数变化超过5%才写入
CHANGE_THRESHOLD = 0.05


def is_in_update_window():
    """检查当前是否在榜单更新时段（北京时间）"""
    now = datetime.now(timezone.utc)
    bj_hour = (now.hour + 8) % 24
    bj_min = now.minute
    t = bj_hour * 60 + bj_min
    
    # 00:30-03:10 或 17:40-20:30
    w1 = (0 * 60 + 30) <= t < (3 * 60 + 10)
    w2 = (17 * 60 + 40) <= t < (20 * 60 + 30)
    return w1 or w2


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            game_id TEXT NOT NULL,
            name TEXT NOT NULL,
            players INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_ts 
        ON snapshots(timestamp)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_game_ts 
        ON snapshots(game_id, timestamp)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS first_seen (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            first_date TEXT NOT NULL,
            created_at TEXT,
            genre TEXT,
            rating REAL
        )
    """)
    conn.commit()


def fetch_rolimons():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if not data.get("success"):
        raise ValueError("API returned success=false")
    return data


def fetch_roblox_metadata(universe_ids):
    """从 Roblox 官方 API 获取游戏元数据（类型、创建时间、评分）"""
    if not universe_ids:
        return {}
    
    ids_str = ",".join(map(str, universe_ids))
    url = f"{ROBLOX_API_URL}{ids_str}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            metadata = {}
            for game in data.get("data", []):
                u_id = str(game.get("universeId"))
                # 评分计算：(upvotes / (upvotes + downvotes)) * 100
                up = game.get("upVotes", 0)
                down = game.get("downVotes", 0)
                total = up + down
                rating = (up / total * 100) if total > 0 else 0
                
                metadata[u_id] = {
                    "created_at": game.get("created"),
                    "genre": game.get("genre"),
                    "rating": round(rating, 2)
                }
            return metadata
    except Exception as e:
        print(f"⚠️ 抓取 Roblox 元数据失败: {e}")
        return {}


def get_last_snapshot(conn):
    """获取每个游戏的最新快照"""
    cursor = conn.execute("""
        SELECT game_id, players 
        FROM snapshots 
        WHERE timestamp = (SELECT MAX(timestamp) FROM snapshots)
    """)
    return {row[0]: row[1] for row in cursor.fetchall()}


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 时间窗口检查已移除 - 全天候采集，依赖 diff 检查避免数据膨胀
    # if not is_in_update_window():
    #     print(f"[{ts}] ⏸️  不在更新时段，跳过采集")
    #     sys.exit(0)
    
    print(f"[{ts}] 开始采集...")

    # 采集
    try:
        data = fetch_rolimons()
    except Exception as e:
        print(f"[{ts}] ❌ API 请求失败: {e}")
        sys.exit(1)

    games = data.get("games", {})
    game_count = len(games)
    print(f"[{ts}] 获取到 {game_count} 个游戏")

    # 写入 SQLite
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    # 获取上次快照
    last_snapshot = get_last_snapshot(conn)
    
    # 只写入有变化的游戏
    rows = []
    new_games = []
    changed_games = []
    
    for game_id, info in games.items():
        name = info[0] if isinstance(info, list) else info.get("name", "")
        players = info[1] if isinstance(info, list) else info.get("players", 0)
        
        # 新游戏或人数变化 >5%
        if game_id not in last_snapshot:
            rows.append((game_id, name, players, ts))
            new_games.append(name)
        else:
            last_players = last_snapshot[game_id]
            if last_players == 0:
                change_pct = 1.0 if players > 0 else 0.0
            else:
                change_pct = abs(players - last_players) / last_players
            
            if change_pct >= CHANGE_THRESHOLD:
                rows.append((game_id, name, players, ts))
                changed_games.append((name, last_players, players, change_pct))

    if rows:
        conn.executemany(
            "INSERT INTO snapshots (game_id, name, players, timestamp) VALUES (?, ?, ?, ?)",
            rows
        )

    # 更新 first_seen
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for game_id, info in games.items():
        name = info[0] if isinstance(info, list) else info.get("name", "")
        conn.execute(
            "INSERT OR IGNORE INTO first_seen (game_id, name, first_date) VALUES (?, ?, ?)",
            (game_id, name, today)
        )

    conn.commit()

    # 获取需要更新元数据的新游戏
    new_game_ids = [row[0] for row in conn.execute("SELECT game_id FROM first_seen WHERE created_at IS NULL").fetchall()]
    
    # 分批获取元数据 (Roblox API 限制每批 100 个)
    if new_game_ids:
        print(f"[{ts}] 正在为 {len(new_game_ids)} 个游戏补全元数据...")
        for i in range(0, len(new_game_ids), 100):
            batch = new_game_ids[i:i+100]
            meta_batch = fetch_roblox_metadata(batch)
            for gid, m in meta_batch.items():
                conn.execute("UPDATE first_seen SET created_at = ?, genre = ?, rating = ? WHERE game_id = ?", 
                             (m['created_at'], m['genre'], m['rating'], gid))
            conn.commit()
            time.sleep(0.5) # 稍微慢一点，避免被限流

    # 统计
    total_first_seen = conn.execute("SELECT COUNT(*) FROM first_seen").fetchone()[0]
    total_snapshots = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    conn.close()

    print(f"[{ts}] ✅ 写入 {len(rows)} 条快照（新游戏 {len(new_games)}，变化 {len(changed_games)}，跳过 {game_count - len(rows)}）")
    print(f"[{ts}] 📊 数据库: {total_snapshots} 条快照, {total_first_seen} 个游戏")


if __name__ == "__main__":
    main()
