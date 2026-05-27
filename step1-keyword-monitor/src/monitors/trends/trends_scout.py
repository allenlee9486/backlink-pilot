import asyncio
import json
import os
import sys
import io
import urllib.parse
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
CHROME_DEBUG_URL = "http://127.0.0.1:9222"
DATA_DIR = Path(__file__).parent / "data" / "trends"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 词根列表 (从用户输入中提取)
ROOT_WORDS = [
    "Translator", "Generator", "Example", "Convert", "Online", 
    "Downloader", "Maker", "Creator", "Editor", "Processor", 
    "Designer", "Compiler", "Analyzer", "Evaluator", "Sender", 
    "Receiver", "Interpreter", "Uploader", "Calculator", "Sample", 
    "Template", "Format", "Builder", "Scheme", "Pattern", 
    "Checker", "Detector", "Scraper", "Manager", "Explorer", 
    "Dashboard", "Planner", "Tracker", "Recorder", "Optimizer", 
    "Scheduler", "Converter", "Viewer", "Extractor", "Monitor", 
    "Notifier", "Verifier", "Simulator", "Assistant", "Constructor", 
    "Comparator", "Navigator", "Syncer", "Connector", "Cataloger",
    "helper", "agent", "advisor", "tool", "directory", "top", "Best", "list", "portal",
    "finder", "guide", "model", "layout", "ideas", "starter", "enhancer", "crawler",
    "modifier", "humanizer", "tester", "responder", "answer", "hint", "clue", "cheat", "solver",
    "summarizer", "transcriber", "paraphaser", "writer", "image", "photo", "picture", "face", "emoji", "meme",
    "chart", "graph", "style", "filter", "text", "chat", "code", "video", "audio", "voice",
    "sound", "speech", "song", "music", "How to", "Ai Image Generator", "ai video generator", "prompt", "app", "apk",
    "ai detector", "hugging face", "ai checker", "password generator", "cursor", "manus", "mcp", "replicate", "fal",
    "windsurf", "openai", "claude", "figma", "bytedance", "gamma ai", "suno", "felo", "consensus ai",
    "chatgpt", "deepseek", "openrouter", "gemini", "vibe coding", "synthesizer", "transformer", "formatter",
    "improver", "cleaner", "fixer", "validator", "organizer", "counter", "automator", "bot", "wizard", "engine",
    "system", "scanner", "inspector", "reader", "web", "cloud", "service", "platform", "suite", "hub"
]

async def fetch_rising_keywords_batch(browser_context, words, is_root=True):
    """批量抓取多个词的相关查询飙升词"""
    label = "词根" if is_root else "关键词"
    print(f"🔍 正在 Google Trends 批量搜索{label}: {', '.join(words)}...")
    
    page = None
    try:
        # 优先使用现有页面，避免 createTarget 协议错误
        if browser_context.pages:
            page = browser_context.pages[0]
        else:
            page = await browser_context.new_page()
    except Exception as e:
        print(f"  ⚠️ 无法创建新页面，尝试重新获取: {e}")
        # 再次尝试，或者如果已经有页面了就用现有的
        await asyncio.sleep(2)
        if browser_context.pages:
            page = browser_context.pages[0]
        else:
            raise e

    all_rising_words = []
    
    try:
        # 构建批量 Trends URL (全球, 过去7天)
        encoded_words = ",".join([urllib.parse.quote(w) for w in words])
        url = f"https://trends.google.com/trends/explore?date=now%207-d&q={encoded_words}&hl=en"
        
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(15) 
        
        # 自动滚动以触发加载
        await page.mouse.wheel(0, 3000)
        await asyncio.sleep(5)
        
        # 批量抓取每个词对应的 "Related queries" 卡片
        rising_data = await page.evaluate('''() => {
            const results = [];
            // Google Trends 结果都在 shadow DOM 或特定的 widget 标签中
            const allItems = Array.from(document.querySelectorAll('.item, .v-list-item, tr'));
            
            allItems.forEach(item => {
                const text = item.innerText;
                if (text && (text.includes('Breakout') || text.includes('%'))) {
                    // 向上查找所属的 widget 标题
                    const widget = item.closest('widget');
                    const title = widget ? widget.querySelector('.widget-title')?.innerText : "Unknown";
                    
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                    if (lines.length >= 1) {
                        results.push({
                            keyword: lines[0],
                            trend: lines.length > 1 ? lines[1] : 'Breakout',
                            widgetTitle: title
                        });
                    }
                }
            });
            return results;
        }''')
        
        for item in rising_data:
            # 根据 widgetTitle 匹配词根
            matched_origin = words[0] # 默认
            widget_title = item.get('widgetTitle') or ""
            for w in words:
                if w.lower() in widget_title.lower():
                    matched_origin = w
                    break
                    
            all_rising_words.append({
                "origin": matched_origin,
                "keyword": item['keyword'],
                "trend": item['trend'],
                "timestamp": datetime.now().isoformat()
            })
            
        print(f"  ✅ 发现 {len(all_rising_words)} 个飙升词")
    except Exception as e:
        print(f"  ❌ 批量抓取 {words} 失败: {e}")
    finally:
        # 如果是复用的页面，不要关闭它，否则后续步骤会没页面用
        if page and len(browser_context.pages) > 1:
            await page.close()
        
    return all_rising_words

async def compare_batch_with_gpts(browser_context, keywords, benchmark="gpts"):
    """批量对比 4 个关键词与 gpts 的热度趋势"""
    if not keywords:
        return []
    
    # 限制最多 4 个关键词 + 1 个基准词
    test_keywords = keywords[:4]
    all_keywords = test_keywords + [benchmark]
    
    print(f"📊 批量对比趋势: {', '.join(test_keywords)} vs {benchmark}...")
    
    page = None
    try:
        if browser_context.pages:
            page = browser_context.pages[0]
        else:
            page = await browser_context.new_page()
    except Exception as e:
        print(f"  ⚠️ 对比环节无法创建页面: {e}")
        if browser_context.pages:
            page = browser_context.pages[0]
        else:
            return []

    winners = []
    
    try:
        q = urllib.parse.quote(",".join(all_keywords))
        url = f"https://trends.google.com/trends/explore?date=now%207-d&q={q}&hl=en"
        
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(10)
        
        # 尝试获取平均热度数值
        averages = await page.evaluate('''() => {
            // 1. 尝试从图例项中提取数值 (Google Trends 常见结构)
            const legendItems = Array.from(document.querySelectorAll('.legend-item, .legend-item-container'));
            if (legendItems.length > 0) {
                const vals = legendItems.map(item => {
                    const valText = item.querySelector('.legend-item-value, .value, .user-set-value')?.innerText || "";
                    return parseInt(valText.replace(/[^0-9]/g, '')) || 0;
                });
                if (vals.some(v => v > 0)) return vals;
            }
            
            // 2. 尝试获取所有显示出来的数字
            const elements = Array.from(document.querySelectorAll('.user-set-value, .value'))
                                .filter(s => s.innerText.match(/^\\d+$/));
            let nums = elements.map(n => parseInt(n.innerText));
            
            if (nums.length === 0) {
                // 备选方案：获取所有 span 中的纯数字
                const spans = Array.from(document.querySelectorAll('span'))
                    .filter(s => /^\\d+$/.test(s.innerText.trim()));
                nums = spans.map(s => parseInt(s.innerText.trim()));
            }
            return nums;
        }''')
        
        print(f"  DEBUG: 提取到的数值: {averages}")
        
        if len(averages) >= len(all_keywords):
            # 基准词 (gpts) 通常在最后
            benchmark_idx = len(test_keywords)
            benchmark_avg = averages[benchmark_idx]
            
            for i, kw in enumerate(test_keywords):
                kw_avg = averages[i]
                if kw_avg > benchmark_avg:
                    winners.append({
                        "keyword": kw,
                        "avg": kw_avg,
                        "benchmark_avg": benchmark_avg
                    })
                    print(f"  🔥 爆款预警! {kw} ({kw_avg}) > {benchmark} ({benchmark_avg})")
                else:
                    print(f"  ⚪ {kw} ({kw_avg}) <= {benchmark} ({benchmark_avg})")
        elif len(averages) >= 2:
            # 如果提取的数值不完整，但至少有 2 个，尝试对比第一个词和最后一个词（假设是基准）
            last_val = averages[-1]
            for i in range(min(len(test_keywords), len(averages) - 1)):
                if averages[i] > last_val:
                    winners.append({
                        "keyword": test_keywords[i],
                        "avg": averages[i],
                        "benchmark_avg": last_val
                    })
                    print(f"  🔥 爆款预警 (部分匹配)! {test_keywords[i]} ({averages[i]}) > {benchmark} ({last_val})")
        else:
            print(f"  ⚠️ 数据提取失败，未能获取到足够的对比数值")
        
    except Exception as e:
        print(f"  ❌ 批量对比失败: {e}")
    finally:
        if page and len(browser_context.pages) > 1:
            await page.close()
        
    return winners

async def main():
    async with async_playwright() as p:
        try:
            print(f"🔗 正在连接到本地 Chrome ({CHROME_DEBUG_URL})...")
            browser = await p.chromium.connect_over_cdp(CHROME_DEBUG_URL)
            context = browser.contexts[0]
            
            # 第一阶段：词根批量扫描
            all_first_round = []
            batch_size = 5
            max_roots = 20 # 可以根据需要调整
            for i in range(0, min(len(ROOT_WORDS), max_roots), batch_size):
                batch = ROOT_WORDS[i:i+batch_size]
                words = await fetch_rising_keywords_batch(context, batch, is_root=True)
                all_first_round.extend(words)
                await asyncio.sleep(5)
            
            # 第二阶段：深入挖掘 - 检查发现的飙升词的“相关查询”
            print(f"🔍 开始二级挖掘，共 {len(all_first_round)} 个一级飙升词...")
            all_second_round = []
            unique_first_round = list(set([w['keyword'] for w in all_first_round]))
            
            # 只对前 15 个独特的一级飙升词进行二级挖掘，避免任务过长
            for word in unique_first_round[:15]:
                second_words = await fetch_rising_keywords_batch(context, [word], is_root=False)
                all_second_round.extend(second_words)
                await asyncio.sleep(3)
            
            # 汇总所有发现的关键词
            all_discovered_words = list(set(
                [w['keyword'] for w in all_first_round] + 
                [w['keyword'] for w in all_second_round]
            ))
            
            # 保存所有中间结果
            raw_path = DATA_DIR / f"raw_rising_{datetime.now().strftime('%Y%m%d')}.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump({
                    "first_round": all_first_round,
                    "second_round": all_second_round,
                    "all_unique_count": len(all_discovered_words)
                }, f, ensure_ascii=False, indent=2)
            
            # 第三阶段：批量对比趋势 (4个一组 + gpts)
            print(f"📈 开始批量对比趋势，共 {len(all_discovered_words)} 个候选词...")
            final_winners = []
            
            # 每次取 4 个词 + 基准词 "GPTs" 进行对比
            # 用户特别提到：在对比这 4 个词的时候，也可以查看这些词的“相关查询”是否有飙升
            for i in range(0, min(len(all_discovered_words), 40), 4):
                batch = all_discovered_words[i:i+4]
                
                # 1. 批量对比
                winners = await compare_batch_with_gpts(context, batch, benchmark="gpts")
                final_winners.extend(winners)
                
                # 2. 深入挖掘：在对比页顺便抓取这 4 个词的相关查询（如果存在）
                # 这能进一步发现更深层的飙升词
                try:
                    # 已经在对比页了，直接抓取
                    deep_words = await fetch_rising_keywords_batch(context, batch, is_root=False)
                    if deep_words:
                        # 发现深层词后，立即与 gpts 进行 1v1 对比
                        for dw in deep_words:
                            kw = dw['keyword']
                            # 1v1 对比
                            is_hotter = await compare_batch_with_gpts(context, [kw], benchmark="gpts")
                            if is_hotter:
                                final_winners.extend(is_hotter)
                except:
                    pass
                    
                await asyncio.sleep(5)
                
            # 保存最终胜出者
            winner_path = DATA_DIR / f"winners_{datetime.now().strftime('%Y%m%d')}.json"
            with open(winner_path, "w", encoding="utf-8") as f:
                json.dump(final_winners, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 扫描任务全部完成。结果已保存。")
            print(f"🏆 最终胜出词数: {len(final_winners)}")
            
        except Exception as e:
            print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
