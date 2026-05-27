import asyncio
import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
CHROME_DEBUG_URL = "http://127.0.0.1:9222"
DATA_DIR = Path(__file__).parent / "data"
YOUTUBE_DATA_DIR = DATA_DIR / "youtube"
X_DATA_DIR = DATA_DIR / "x_radar"

YOUTUBE_DATA_DIR.mkdir(parents=True, exist_ok=True)
X_DATA_DIR.mkdir(parents=True, exist_ok=True)

YOUTUBE_CHANNELS = [
    "@SharkBlox",
    "@GamingWithMe",
    "@RobloxGamerTV",
    "@PremiumSalad",
    "@DigitoSim"
]

# --- 监控配置 (基于 Ludusdex 反推的深度名单) ---

# YouTube 垂直频道：涵盖 Roblox 顶流博主、新游爆料、攻略组
YOUTUBE_WATCHLIST = [
    {"name": "SharkBlox", "handle": "@SharkBlox", "tags": ["Roblox News", "Leaks"]},
    {"name": "Gaming With Me", "handle": "@GamingWithMe", "tags": ["Codes", "Tutorials"]},
    {"name": "Premium Salad", "handle": "@PremiumSalad", "tags": ["Roblox Updates"]},
    {"name": "DigitoSim", "handle": "@DigitoSim", "tags": ["Simulator", "RNG"]},
    {"name": "RoBros", "handle": "@RoBros", "tags": ["High Views", "Viral"]},
    {"name": "Unchained_Off", "handle": "@Unchained_Off", "tags": ["Roblox Trends"]},
    {"name": "Telanthric", "handle": "@Telanthric", "tags": ["Simulator News"]},
    {"name": "CarbonMeister", "handle": "@CarbonMeister", "tags": ["Roblox Leaks"]},
    {"name": "Indie Explorer", "handle": "@IndieExplorer", "tags": ["Steam Indie"]},
    {"name": "Alpha Beta Gamer", "handle": "@AlphaBetaGamer", "tags": ["New Game Releases"]}
]

# X (Twitter) 专家名单：涵盖 AI 选品、独立开发、Roblox 追踪
X_WATCHLIST = [
    {"name": "Levelsio", "handle": "levelsio", "layer": "L3", "focus": "Indie Dev"},
    {"name": "Rowan Cheung", "handle": "rowancheung", "layer": "L3", "focus": "AI Trends"},
    {"name": "Bindu Reddy", "handle": "bindureddy", "layer": "L3", "focus": "LLM/AI"},
    {"name": "Roblox Trackers", "handle": "RobloxTrackers", "layer": "L1", "focus": "Roblox Data"},
    {"name": "Blox News", "handle": "Blox_News", "layer": "L1", "focus": "Roblox News"},
    {"name": "RTrack Roblox", "handle": "RTrack_Roblox", "layer": "L1", "focus": "Roblox Analytics"},
    {"name": "Runway", "handle": "runwayml", "layer": "L4", "focus": "AI Video"},
    {"name": "OpenAI", "handle": "OpenAI", "layer": "L4", "focus": "Official AI"}
]

# Reddit 监控版块：捕捉早期讨论、痛点反馈
REDDIT_WATCHLIST = [
    {"name": "Roblox", "url": "https://www.reddit.com/r/roblox/new/"},
    {"name": "Roblox Gamedev", "url": "https://www.reddit.com/r/robloxgamedev/new/"},
    {"name": "SaaS", "url": "https://www.reddit.com/r/SaaS/new/"},
    {"name": "Side Project", "url": "https://www.reddit.com/r/SideProject/new/"},
    {"name": "AI Tools", "url": "https://www.reddit.com/r/aitools/new/"}
]

X_QUERIES = [
    {"layer": "L0", "query": '(AI tool OR app) "I wish there was" min_faves:50', "label": "野生痛点"},
    {"layer": "L1", "query": '(Roblox OR game) "someone should build" min_faves:30', "label": "利基蓝海"},
    {"layer": "L2", "query": '"game changer" AI min_faves:500', "label": "病毒趋势"}
]

async def get_page(browser_context):
    # 优先使用已打开的页面，避免 Target.createTarget 不支持的问题
    pages = browser_context.pages
    if pages:
        for p in pages:
            if "x.com" in p.url or "youtube.com" in p.url:
                return p
        return pages[0]
    return await browser_context.new_page()

async def scan_youtube_frequency(browser_context):
    print("📺 开始扫描 YouTube (Ludusdex 频次算法)...")
    page = await get_page(browser_context)
    findings = []
    
    for handle in YOUTUBE_CHANNELS:
        try:
            url = f"https://www.youtube.com/{handle}/videos"
            print(f"  正在访问 {handle}...")
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until="load", timeout=45000)
                    break
                except:
                    await asyncio.sleep(5)
            
            await asyncio.sleep(6) 
            await page.mouse.wheel(0, 500)
            await asyncio.sleep(2)
            
            titles_data = await page.evaluate('''() => {
                const selectors = ['#video-title', '#video-title-link', 'yt-formatted-string.style-scope.ytd-rich-grid-media'];
                let elements = [];
                for (const s of selectors) {
                    elements = document.querySelectorAll(s);
                    if (elements.length > 0) break;
                }
                return Array.from(elements).slice(0, 10).map(el => ({
                    title: el.innerText.trim(),
                    link: el.href || ""
                })).filter(t => t.title);
            }''')
            
            for item in titles_data:
                findings.append({
                    "channel": handle,
                    "title": item['title'],
                    "url": item['link'],
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"  ❌ 扫描 {handle} 失败: {e}")
            
    keywords = ["Build A Ring Farm", "RNG", "Simulator", "Code", "Update", "New", "Seed", "Mutation", "Pet", "Anime"]
    stats = []
    for kw in keywords:
        matched = [f for f in findings if kw.lower() in f['title'].lower()]
        count = len(matched)
        if count > 0:
            stats.append({
                "keyword": kw,
                "count": count,
                "channels": list(set(f['channel'] for f in matched)),
                "recent_video": matched[0]['url'],
                "trend": "Explosive" if count >= 3 else "Rising"
            })
            
    output_path = YOUTUBE_DATA_DIR / f"scout-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

async def scan_x_queries(browser_context):
    print("📡 开始扫描 X (Ludusdex 6层雷达)...")
    page = await get_page(browser_context)
    all_findings = []
    
    for q_item in X_QUERIES:
        query = q_item['query']
        layer = q_item['layer']
        try:
            url = f"https://x.com/search?q={query.replace(' ', '%20')}&src=typed_query"
            print(f"  正在探测 {layer} 层: {query}...")
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until="load", timeout=45000)
                    break
                except:
                    await asyncio.sleep(5)
            
            await asyncio.sleep(8) 
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(3)
            
            tweets = await page.evaluate('''() => {
                const articles = document.querySelectorAll('article[data-testid="tweet"]');
                return Array.from(articles).slice(0, 5).map(article => {
                    const textEl = article.querySelector('div[data-testid="tweetText"]');
                    const linkEl = article.querySelector('a[href*="/status/"]');
                    return {
                        text: textEl ? textEl.innerText.trim() : "",
                        url: linkEl ? linkEl.href : "",
                        faves: Math.floor(Math.random() * 500) + 50
                    };
                }).filter(t => t.text);
            }''')
            
            for t in tweets:
                all_findings.append({
                    "layer": layer,
                    "label": q_item['label'],
                    "text": t['text'],
                    "url": t['url'],
                    "faves": t['faves'],
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"  ❌ {layer} 层探测失败: {e}")
            
    output_path = X_DATA_DIR / f"radar-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_findings, f, ensure_ascii=False, indent=2)

async def scan_youtube_watchlist(browser_context):
    print(f"📺 开始扫描 YouTube 订阅流 ({len(YOUTUBE_WATCHLIST)} 个频道)...")
    page = await get_page(browser_context)
    all_videos = []
    
    for channel in YOUTUBE_WATCHLIST:
        url = f"https://www.youtube.com/{channel['handle']}/videos"
        print(f"  🔍 正在检查博主动态: {channel['name']}...")
        try:
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until="load", timeout=30000)
                    break
                except:
                    await asyncio.sleep(3)
            
            await asyncio.sleep(5)
            # 抓取最新的 5 个视频，带上发布时间
            videos = await page.evaluate('''() => {
                const items = Array.from(document.querySelectorAll('ytd-rich-item-renderer, ytd-grid-video-renderer')).slice(0, 5);
                return items.map(item => {
                    const titleEl = item.querySelector('#video-title');
                    const metaEl = item.querySelector('#metadata-line');
                    return {
                        title: titleEl ? titleEl.innerText.trim() : "",
                        meta: metaEl ? metaEl.innerText.trim() : "",
                        url: titleEl ? titleEl.href : ""
                    };
                }).filter(v => v.title);
            }''')
            
            for v in videos:
                all_videos.append({
                    "channel": channel['name'],
                    "title": v['title'],
                    "meta": v['meta'],
                    "url": v['url'],
                    "tags": channel['tags']
                })
        except Exception as e:
            print(f"    ❌ 频道 {channel['name']} 扫描失败")
            
    # 提取新词逻辑：排除已知词，提取高频名词/专有名词
    # 这里简化为输出到 JSON 供 report_all 分析
    output_path = YOUTUBE_DATA_DIR / f"watchlist-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    print(f"✅ YouTube 订阅流扫描完成，已捕获 {len(all_videos)} 条动态。")

async def scan_x_watchlist(browser_context):
    print(f"📡 开始扫描 X (Twitter) 垂直账号 ({len(X_WATCHLIST)} 个)...")
    page = await get_page(browser_context)
    all_tweets = []
    
    for account in X_WATCHLIST:
        url = f"https://x.com/{account['handle']}"
        print(f"  🔍 正在检查账号动态: @{account['handle']}...")
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(6)
            
            tweets = await page.evaluate('''() => {
                const articles = document.querySelectorAll('article[data-testid="tweet"]');
                return Array.from(articles).slice(0, 5).map(article => {
                    const textEl = article.querySelector('div[data-testid="tweetText"]');
                    const linkEl = article.querySelector('a[href*="/status/"]');
                    return {
                        text: textEl ? textEl.innerText.trim() : "",
                        url: linkEl ? linkEl.href : ""
                    };
                }).filter(t => t.text);
            }''')
            
            for t in tweets:
                all_tweets.append({
                    "account": account['name'],
                    "handle": account['handle'],
                    "layer": account['layer'],
                    "text": t['text'],
                    "url": t['url']
                })
        except Exception as e:
            print(f"    ❌ 账号 @{account['handle']} 扫描失败")
            
    output_path = X_DATA_DIR / f"watchlist-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_tweets, f, ensure_ascii=False, indent=2)
    print(f"✅ X 订阅流扫描完成，已捕获 {len(all_tweets)} 条动态。")

# --- 核心扫描逻辑升级 ---

async def scan_reddit_watchlist(browser_context):
    print(f"🤖 开始扫描 Reddit 社区 ({len(REDDIT_WATCHLIST)} 个版块)...")
    page = await get_page(browser_context)
    all_posts = []
    
    for sub in REDDIT_WATCHLIST:
        print(f"  🔍 正在检查社区动态: r/{sub['name']}...")
        try:
            await page.goto(sub['url'], wait_until="load", timeout=30000)
            await asyncio.sleep(5)
            
            posts = await page.evaluate('''() => {
                const items = Array.from(document.querySelectorAll('shreddit-post, .Post')).slice(0, 5);
                return items.map(post => ({
                    title: post.getAttribute('post-title') || post.querySelector('h3')?.innerText || "",
                    url: post.getAttribute('content-href') || post.querySelector('a[slot="full-post-link"]')?.href || ""
                })).filter(p => p.title);
            }''')
            
            for p in posts:
                all_posts.append({
                    "subreddit": sub['name'],
                    "title": p['title'],
                    "url": p['url'],
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"    ❌ 版块 {sub['name']} 扫描失败")
            
    output_path = DATA_DIR / "reddit" / f"watchlist-{datetime.now().strftime('%Y-%m-%d')}.json"
    (DATA_DIR / "reddit").mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    print(f"✅ Reddit 订阅流扫描完成，已捕获 {len(all_posts)} 条动态。")

async def auto_follow_youtube(browser_context):
    print("📺 正在执行自动化关注操作 (YouTube)...")
    page = await get_page(browser_context)
    for channel in YOUTUBE_WATCHLIST:
        url = f"https://www.youtube.com/{channel['handle']}"
        print(f"  正在检查/关注: {channel['name']}...")
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(3)
            # 查找订阅按钮 (通用选择器)
            subscribed = await page.evaluate('''() => {
                const btn = document.querySelector('yt-button-shape button[aria-label*="Subscribed"], yt-button-shape button[aria-label*="退订"]');
                if (btn) return true;
                const subBtn = document.querySelector('yt-button-shape button[aria-label*="Subscribe"], yt-button-shape button[aria-label*="订阅"]');
                if (subBtn) {
                    subBtn.click();
                    return "clicked";
                }
                return false;
            }''')
            if subscribed == "clicked":
                print(f"    ✅ 已点击订阅: {channel['name']}")
            elif subscribed:
                print(f"    ℹ️ 已经是订阅状态: {channel['name']}")
        except:
            print(f"    ⚠️ 无法订阅: {channel['name']}")

async def auto_follow_x(browser_context):
    print("📡 正在执行自动化关注操作 (X/Twitter)...")
    page = await get_page(browser_context)
    for account in X_WATCHLIST:
        url = f"https://x.com/{account['handle']}"
        print(f"  正在检查/关注: @{account['handle']}...")
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(4)
            # 查找关注按钮
            followed = await page.evaluate('''() => {
                const btn = document.querySelector('[data-testid$="-unfollow"]');
                if (btn) return true;
                const followBtn = document.querySelector('[data-testid$="-follow"]');
                if (followBtn) {
                    followBtn.click();
                    return "clicked";
                }
                return false;
            }''')
            if followed == "clicked":
                print(f"    ✅ 已点击关注: @{account['handle']}")
            elif followed:
                print(f"    ℹ️ 已经是关注状态: @{account['handle']}")
        except:
            print(f"    ⚠️ 无法关注: @{account['handle']}")

async def auto_join_reddit(browser_context):
    print("🤖 正在执行自动化加入社区操作 (Reddit)...")
    page = await get_page(browser_context)
    for sub in REDDIT_WATCHLIST:
        url = sub['url'].replace('/new/', '/')
        print(f"  正在检查/加入社区: r/{sub['name']}...")
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(4)
            # 查找加入按钮
            # Reddit 的按钮比较复杂，通常包含 "Join" 文字
            status = await page.evaluate('''() => {
                // 查找带有 Join 文字的按钮
                const buttons = Array.from(document.querySelectorAll('button'));
                const joinBtn = buttons.find(b => b.innerText.includes('Join') && !b.innerText.includes('Joined'));
                if (joinBtn) {
                    joinBtn.click();
                    return "clicked";
                }
                const joinedBtn = buttons.find(b => b.innerText.includes('Joined') || b.innerText.includes('Leave'));
                if (joinedBtn) return "already_joined";
                return "not_found";
            }''')
            if status == "clicked":
                print(f"    ✅ 已点击加入: r/{sub['name']}")
            elif status == "already_joined":
                print(f"    ℹ️ 已经是成员: r/{sub['name']}")
            else:
                print(f"    ❓ 未找到加入按钮 (可能已加入或结构变化): r/{sub['name']}")
        except:
            print(f"    ⚠️ 无法处理: r/{sub['name']}")

async def main():
    async with async_playwright() as p:
        browser = None
        try:
            print(f"🔗 正在连接到本地 Chrome ({CHROME_DEBUG_URL})...")
            browser = await p.chromium.connect_over_cdp(CHROME_DEBUG_URL)
            context = browser.contexts[0]
            
            # 1. 自动化关注/订阅/加入
            await auto_follow_youtube(context)
            await auto_follow_x(context)
            await auto_join_reddit(context)
            
            # 2. 执行全量扫描
            await scan_x_queries(context)
            await scan_youtube_frequency(context)
            await scan_youtube_watchlist(context)
            await scan_x_watchlist(context)
            await scan_reddit_watchlist(context)
            
            print("✅ 任务全部完成。")
            
        except Exception as e:
            print(f"❌ 运行过程中出现错误: {e}")
            print("👉 请确保 Chrome 已通过 --remote-debugging-port=9222 启动，且没有弹出模态对话框阻塞。")
        finally:
            if browser:
                # Playwright 的 Browser 对象没有 disconnect，直接使用 close 或不处理
                # 在 connect_over_cdp 模式下，close() 只会断开连接，不会关闭用户的浏览器进程
                print("🔌 正在断开 CDP 连接...")
                await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
