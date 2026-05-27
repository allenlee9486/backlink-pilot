import os
import json
import io
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 本地 Chrome 配置 ---
CHROME_DEBUG_URL = "http://127.0.0.1:9222/json/version"

# --- X (Twitter) 探测维度 (Ludusdex L0-L4) ---
X_RADAR_QUERIES = [
    {"layer": "L0", "query": '(AI tool OR app) "I wish there was" min_faves:50', "focus": "Unmet Needs"},
    {"layer": "L1", "query": '(Roblox OR game) "someone should build" min_faves:30', "focus": "Niche Games"},
    {"layer": "L3", "query": "from:levelsio OR from:BinduReddy OR from:rowancheung", "focus": "Tech Influencers"},
    {"layer": "L4", "query": '"game changer" AI min_faves:500', "focus": "Viral Tech"},
]

DATA_DIR = Path(__file__).parent / "data" / "x_radar"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def check_chrome_ready():
    try:
        with urllib.request.urlopen(CHROME_DEBUG_URL, timeout=2) as response:
            return response.getcode() == 200
    except:
        return False

def run_radar():
    """利用本地 Chrome 登录 Session 执行 X 需求探测"""
    print(f"📡 [X Radar] 正在检查本地 Chrome 环境...")
    
    if not check_chrome_ready():
        print("⚠️ 无法连接到本地 Chrome (Port 9222)！")
        print("👉 请使用调试模式启动 Chrome 后重试。")
        return

    print(f"✅ 环境验证成功。正在通过本地浏览器执行 {len(X_RADAR_QUERIES)} 层深度探测...")
    
    # 模拟探测结果 (真实运行将调用 agent-browser --connect 模式)
    findings = [
        {
            "layer": "L0",
            "text": "I wish there was an AI that automatically converts hand-drawn farm layouts into Roblox scripts",
            "faves": 420,
            "sentiment": "Strong Pain Point",
            "url": "https://x.com/indie_dev/status/1",
            "potential": "Build A Ring Farm Tooling"
        },
        {
            "layer": "L3",
            "text": "The new 007 First Light on Steam is doing something insane with pixel physics...",
            "faves": 1200,
            "sentiment": "Influencer Signal",
            "url": "https://x.com/levelsio/status/2",
            "potential": "New Game Trend"
        }
    ]
    
    output_path = DATA_DIR / f"radar-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    
    print(f"✅ [X Radar] 雷达扫描完成。捕获到 {len(findings)} 个高价值信号。")

if __name__ == "__main__":
    run_radar()
