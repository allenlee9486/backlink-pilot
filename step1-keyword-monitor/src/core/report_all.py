import sqlite3
import json
import os
import sys
import io
import subprocess
import urllib.request
import time
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 强制设置标准输出为 UTF-8，解决 Windows 上的 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 确保可以导入 utils 模块
CORE_DIR = Path(__file__).parent
PROJECT_ROOT = CORE_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.utils.discovery import discover_crazygames_new, discover_itch_new, discover_steam_new, discover_custom_sites
from src.monitors.trends.trends_analyzer import TrendsAnalyzer

# --- 数据读取函数 ---

def load_youtube_scout():
    """读取 YouTube 频次扫描结果"""
    scout_dir = PROJECT_ROOT / "data" / "raw" / "youtube"
    latest_file = None
    if scout_dir.exists():
        files = sorted(scout_dir.glob("scout-*.json"), reverse=True)
        if files:
            latest_file = files[0]
            
    if latest_file:
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def load_x_radar():
    """读取 X 需求雷达结果"""
    radar_dir = PROJECT_ROOT / "data" / "raw" / "x_radar"
    latest_file = None
    if radar_dir.exists():
        files = sorted(radar_dir.glob("radar-*.json"), reverse=True)
        if files:
            latest_file = files[0]
            
    if latest_file:
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def load_trends_winners():
    """读取 Google Trends 胜出词"""
    trends_dir = PROJECT_ROOT / "data" / "raw" / "trends"
    latest_file = None
    if trends_dir.exists():
        files = sorted(trends_dir.glob("winners_agent_*.json"), reverse=True)
        if files:
            latest_file = files[0]
            
    if latest_file:
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"winners": []}

# --- Roblox 分析逻辑 (Ludusdex 级) ---

def get_db_connection(platform):
    db_map = {
        "roblox": PROJECT_ROOT / "src" / "monitors" / "platforms" / "roblox" / "data" / "roblox-trends.db",
        "steam": PROJECT_ROOT / "src" / "monitors" / "platforms" / "steam" / "data" / "steam-trends.db",
        "crazygames": PROJECT_ROOT / "src" / "monitors" / "platforms" / "crazygames" / "data" / "crazygames.db",
        "itch": PROJECT_ROOT / "src" / "monitors" / "platforms" / "itch" / "data" / "itch.db",
    }
    path = db_map.get(platform)
    if path and path.exists():
        return sqlite3.connect(str(path))
    return None

def analyze_roblox():
    conn = get_db_connection("roblox")
    if not conn: return "❌ 数据库未找到", []
    
    try:
        q = """
        SELECT 
            s.game_id, s.name, s.players, f.created_at, f.genre, f.rating
        FROM snapshots s
        JOIN first_seen f ON s.game_id = f.game_id
        WHERE s.timestamp = (SELECT MAX(timestamp) FROM snapshots)
        ORDER BY s.players DESC
        """
        rows = conn.execute(q).fetchall()
        
        gold_candidates = []
        display_lines = []
        
        now_utc = datetime.now(timezone.utc)
        
        for gid, name, players, created_at, genre, rating in rows:
            is_gold = False
            age = None
            if created_at:
                try:
                    fd = datetime.strptime(created_at.split('T')[0], "%Y-%m-%d").date()
                    age = (now_utc.date() - fd).days
                    if age <= 180 and players >= 10000 and (rating is None or rating >= 90):
                        if genre:
                            targets = ["Simulator", "Tycoon", "Tower Defense", "RPG", "Strategy", "Fighting", "Incremental"]
                            for t in targets:
                                if t.lower() in genre.lower():
                                    is_gold = True
                                    break
                except: pass
            
            if is_gold:
                gold_candidates.append({
                    "name": name,
                    "url": f"https://www.roblox.com/games/{gid}",
                    "platform": "roblox",
                    "score": 100,
                    "badge": f"🏆 黄金候选 (并发 {players:,} | {age}d)",
                    "reason": f"高并发 ({players:,}) + 高评分 ({rating}%) + 核心品类 ({genre})"
                })
            
            if len(display_lines) < 10:
                display_lines.append(f"- **[{name}](https://www.roblox.com/games/{gid})**: {players:,} 在线 ({'🏆 黄金' if is_gold else '活跃'})")
        
        conn.close()
        return "\n".join(display_lines), gold_candidates
    except Exception as e:
        return f"⚠️ 分析错误: {e}", []

# --- 主报告生成逻辑 (复刻 Ludusdex 风格) ---

def get_domain_suggestions(keyword):
    """根据热词生成域名建议"""
    clean_kw = re.sub(r'[^a-zA-Z0-9]', '', keyword).lower()
    return [f"{clean_kw}codes.xyz", f"{clean_kw}tips.net", f"get{clean_kw}.org"]

def main():
    print("🚀 启动 Ludusdex 复刻版情报收集系统...")
    
    # --- 数据读取函数 ---

def load_youtube_watchlist():
    """读取 YouTube 订阅流动态"""
    scout_dir = Path(__file__).parent / "data" / "youtube"
    latest_file = None
    if scout_dir.exists():
        files = sorted(scout_dir.glob("watchlist-*.json"), reverse=True)
        if files:
            latest_file = files[0]
            
    if latest_file:
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def load_x_watchlist():
    """读取 X 订阅流动态"""
    radar_dir = Path(__file__).parent / "data" / "x_radar"
    latest_file = None
    if radar_dir.exists():
        files = sorted(radar_dir.glob("watchlist-*.json"), reverse=True)
        if files:
            latest_file = files[0]
            
    if latest_file:
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def extract_new_keywords(youtube_feed, x_feed):
    """从订阅流中提取新词信号"""
    new_signals = []
    # 简单的关键词提取逻辑：寻找包含 "NEW", "Update", "Game", "Release" 等字眼的标题
    patterns = [r"\[NEW\]\s*(.*)", r"New\s*(.*)\s*Game", r"(.*)\s*Update", r"(.*)\s*is here"]
    
    seen_keywords = set(["Build A Ring Farm", "Slime RNG", "Sailor Piece"])
    
    for v in youtube_feed:
        title = v['title']
        for p in patterns:
            match = re.search(p, title, re.IGNORECASE)
            if match:
                kw = match.group(1).strip()
                if kw and kw not in seen_keywords and len(kw) > 3:
                    new_signals.append({
                        "name": kw,
                        "platform": "YouTube",
                        "source": v['channel'],
                        "reason": f"博主动态发现: {title}",
                        "url": v['url']
                    })
                    seen_keywords.add(kw)
    
    return new_signals

def main():
    print("🚀 启动 Ludusdex 复刻版情报收集系统...")
    
    # 1. 运行 Roblox 分析
    roblox_data, recommendations = analyze_roblox()
    
    # 2. 读取 YouTube 和 X 实时信号 (Search + Watchlist)
    youtube_findings = load_youtube_scout()
    x_findings = load_x_radar()
    yt_watchlist = load_youtube_watchlist()
    x_watchlist = load_x_watchlist()
    trends_findings = load_trends_winners()
    
    # 3. 提取博主动态中的新词
    new_watchlist_signals = extract_new_keywords(yt_watchlist, x_watchlist)
    
    now = datetime.now()
    report_md = f"""# 🦌 七鹿式·趋势雷达 (v5 Watchlist Edition) | {now.strftime('%Y-%m-%d %H:%M')} UTC

🔥 {len(recommendations)} 个黄金信号 · {len(new_watchlist_signals)} 个博主动态新词 · {len(trends_findings.get('winners', []))} 个谷歌飙升词 · 24h 自动化扫描

## 🚀 核心套利信号 (基于 6 维评分法)
"""
    
    if not recommendations and not new_watchlist_signals and not trends_findings.get('winners'):
        report_md += "\n✨ 本次扫描暂未发现符合“黄金标准”的新爆款。大盘平稳，建议继续监控。\n"
    else:
        # 合并黄金信号、博主新词和趋势词
        combined = recommendations[:3]
        for s in new_watchlist_signals[:3]:
            combined.append({
                "name": s['name'],
                "platform": s['platform'],
                "badge": "🌟 博主首发",
                "reason": s['reason'],
                "url": s['url']
            })
        
        for w in trends_findings.get('winners', [])[:3]:
            combined.append({
                "name": w['keyword'],
                "platform": "Google Trends",
                "badge": "🔥 飙升过 GPTS",
                "reason": f"热度 {w['avg']} (GPTS: {w['gpts_avg']})",
                "url": f"https://trends.google.com/trends/explore?date=now%207-d&q={w['keyword']}"
            })

        for i, rec in enumerate(combined, 1):
            domains = get_domain_suggestions(rec['name'])
            report_md += f"""
### #{i} {rec['name']}
{rec.get('badge', '💎 黄金候选')}

- **平台**: {rec['platform'].upper()}
- **套利逻辑**: {rec.get('reason', '博主动态/高并发增长')}
- **域名建议**: `{" / ".join(domains)}`
- **[查看原帖/链接]({rec['url']})**
"""

    report_md += f"""
---

## 📺 YouTube 博主动态监控 (Watchlist)
> 监控 SharkBlox, Gaming With Me 等 6 个核心频道的 Feed。

"""
    if not yt_watchlist:
        report_md += "⚠️ YouTube 订阅流扫描暂无数据。\n"
    else:
        for v in yt_watchlist[:10]:
            report_md += f"- **[{v['channel']}]** {v['title']} ({v['meta']}) | [观看]({v['url']})\n"

    report_md += f"""
---

## 🔍 X (Twitter) 专家动态监控 (Watchlist)
> 监控 @levelsio, @rowancheung 等 5 个垂直领域专家的动态。

"""
    if not x_watchlist:
        report_md += "⚠️ X 订阅流扫描暂无数据。\n"
    else:
        for t in x_watchlist[:8]:
            report_md += f"- **[@{t['handle']}]** {t['text'][:120]}... | [查看]({t['url']})\n"

    report_md += f"""
---

## � Google Trends 飙升榜 (vs GPTS)
> 扫描 {trends_findings.get('total_roots_scanned', 0)} 个词根，监控过去 7 天全球趋势。

"""
    if not trends_findings.get('winners'):
        report_md += "✨ 暂未发现热度超过 GPTS 的新飙升词。\n"
    else:
        for w in trends_findings['winners'][:10]:
            diff = w['avg'] - w['gpts_avg']
            report_md += f"- **{w['keyword']}**: 热度 {w['avg']} (比 GPTS 高 {diff}) | [趋势图](https://trends.google.com/trends/explore?date=now%207-d&q={w['keyword']},gpts)\n"

    report_md += f"""
---

## �📊 平台实时数据汇总

### 🎮 Roblox 黄金名单 (并发>10K & <180d)
{roblox_data}

### 📺 YouTube 频次排行 (200+ 频道)
"""
    if not youtube_findings:
        report_md += "✨ YouTube 扫描数据同步中...\n"
    else:
        for item in youtube_findings[:8]:
            report_md += f"- **{item['keyword']}**: 24h 提及 {item['count']} 次 | [最新视频]({item.get('recent_video', '#')})\n"

    report_md += f"""
---
## 💡 Ludusdex 专家洞察 (v4)
1. **流量盲点**: {'发现 ' + recommendations[0]['name'] if recommendations else '目前没有符合 180 天黄金期的新爆款'}。建议关注 X 探测到的长尾需求。
2. **SEO 策略**: 针对 X 探测到的 \"{x_findings[0]['text'][:20] if x_findings else '新需求'}\"，建议立即注册域名并建立 PAA (People Also Ask) 页面。

*报告生成: Sitebuilder Monitor v4 (Ludusdex Clone) | 数据基准: {now.strftime('%Y-%m-%d')}*
"""

    latest_file = PROJECT_ROOT / "data" / "reports" / "LATEST_SUMMARY.md"
    latest_file.parent.mkdir(parents=True, exist_ok=True)
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    print(f"✅ 报告已生成至 {latest_file}")

if __name__ == "__main__":
    main()
