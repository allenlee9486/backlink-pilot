import subprocess
import json
import time
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
AGENT_BROWSER_EXE = "agent-browser"
PROFILE_PATH = r"d:\开发设计工具\jiankong_sitemap\.browser-profile"
# 指定本地 Chrome 可执行文件路径，确保使用本地浏览器环境
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DATA_DIR = Path(__file__).parent / "data" / "trends"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 词根列表 (全量)
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
    "creator", "maker", "builder", "constructor", "composer",
    "helper", "assistant", "agent", "advisor", "tool",
    "directory", "top", "Best", "list", "portal",
    "finder", "cataloger", "dashboard", "designer", "uploader",
    "example", "template", "sample", "pattern", "resources",
    "guide", "format", "model", "layout", "ideas",
    "starter", "enhancer", "downloader", "scraper", "crawler",
    "syncer", "translator", "converter", "optimizer", "modifier",
    "processor", "compiler", "analyzer", "evaluator", "calculator",
    "online", "checker", "humanizer", "tester", "scheduler",
    "planner", "manager", "tracker", "sender", "receiver",
    "responder", "recorder", "connector", "viewer", "monitor",
    "notifier", "verifier", "simulator", "comparator", "answer",
    "hint", "clue", "cheat", "solver", "extractor",
    "summarizer", "transcriber", "paraphaser", "writer", "image",
    "photo", "picture", "face", "emoji", "meme",
    "chart", "graph", "style", "filter", "text",
    "chat", "code", "video", "audio", "voice",
    "sound", "speech", "song", "music", "How to",
    "Ai Image Generator", "ai video generator", "prompt", "app", "apk",
    "ai detector", "hugging face", "ai checker", "password generator", "manager",
    "cursor", "manus", "mcp", "replicate", "fal",
    "windsurf", "openai", "claude", "figma",
    "bytedance", "gamma ai", "suno", "felo", "consensus ai",
    "chatgpt", "deepseek", "openrouter", "cluade", "gemini",
    "vibe coding", "Responder", "generator", "converter", "editor",
    "composer", "synthesizer", "transformer", "formatter", "analyzer",
    "extractor", "improver", "cleaner", "fixer", "validator",
    "tester", "organizer", "scheduler", "calculator", "counter",
    "automator", "bot", "wizard", "engine", "system",
    "tool", "detector", "scanner", "inspector", "explorer",
    "reader", "online", "web", "cloud", "service",
    "platform", "suite", "hub"
]

def run_cmd(args):
    """运行 agent-browser 命令并返回输出"""
    # 构造命令字符串
    base_cmd = [
        f'"{AGENT_BROWSER_EXE}"',
        f'--profile "{PROFILE_PATH}"',
        f'--executable-path "{CHROME_EXECUTABLE}"'
    ]
    
    cmd_str = " ".join(base_cmd) + " " + " ".join([f'"{a}"' if " " in a or "&" in a else a for a in args])
    print(f"Executing: {cmd_str}")
    
    try:
        # 在 Windows 上最稳健的方案：
        # 直接指定 encoding='utf-8' 并配合 errors='replace'
        # 这样 subprocess 内部的 _readerthread 在遇到无法解码的字符（如 GBK 字符）时
        # 会使用替代字符而不是抛出崩溃异常
        result = subprocess.run(
            cmd_str, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace',
            shell=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        return result.stdout
    except Exception as e:
        print(f"Subprocess Execution Exception: {e}")
        return ""

def get_rising_queries(keywords):
    """获取指定关键词（支持列表，最多5个）的飙升相关查询"""
    if isinstance(keywords, list):
        q_param = ",".join(keywords)
        display_name = ", ".join(keywords)
    else:
        q_param = keywords
        display_name = keywords

    print(f"🔍 搜索词根组: {display_name}")
    url = f"https://trends.google.com/trends/explore?date=now%207-d&q={q_param}&hl=en-US"
    run_cmd(["open", url])
    time.sleep(6)
    
    # 尝试点击 Cookie 确认按钮
    run_cmd(["click", "button:has-text('OK, got it')"])
    run_cmd(["scroll", "down", "2000"])
    time.sleep(3)
    
    # 尝试切换到 Rising (由于有多个词，页面会有多个 Related queries 模块)
    # 我们循环查找所有的 "Top" 下拉框并尝试点击切换到 "Rising"
    js_switch_rising = """
    (async () => {
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        const listboxes = Array.from(document.querySelectorAll('listbox, [role="listbox"], .widget-header-select'))
                               .filter(el => el.innerText.includes('Top'));
        
        for (const lb of listboxes) {
            lb.click();
            await sleep(800);
            const risingOpt = Array.from(document.querySelectorAll('[role="option"], .item, .select-option'))
                                   .find(opt => opt.innerText.includes('Rising'));
            if (risingOpt) {
                risingOpt.click();
                await sleep(1000);
            }
        }
    })()
    """
    run_cmd(["eval", js_switch_rising])
    time.sleep(6)
    
    # 使用 eval 提取所有文本
    js_script = """
    (() => {
        const results = [];
        function walk(root) {
            if (!root) return;
            // 查找包含趋势信息的元素
            const elements = root.querySelectorAll('.item, tr, .v-list-item, [role="link"], .widget-item');
            elements.forEach(el => {
                const t = el.innerText;
                // 寻找 'Breakout' 或百分比增长
                if (t && (t.includes('Breakout') || t.includes('%') || t.includes('+'))) {
                    results.push(t);
                }
            });
            const all = root.querySelectorAll('*');
            for (const el of all) {
                if (el.shadowRoot) walk(el.shadowRoot);
            }
        }
        walk(document);
        return JSON.stringify(results);
    })()
    """
    
    output = run_cmd(["eval", js_script])
    queries = []
    try:
        start_idx = output.find('[')
        end_idx = output.rfind(']')
        if start_idx != -1 and end_idx != -1:
            raw_list = json.loads(output[start_idx:end_idx+1])
            for item in raw_list:
                # 解析格式
                lines = [l.strip() for l in item.split("\n") if l.strip()]
                if len(lines) >= 2:
                    # 过滤掉纯数字序号
                    kw = lines[0]
                    if kw.isdigit() and len(lines) > 2:
                        kw = lines[1]
                    trend = lines[-1]
                    queries.append({"keyword": kw, "trend": trend})
                else:
                    parts = item.split(" ")
                    if len(parts) >= 3:
                        queries.append({"keyword": " ".join(parts[1:-1]), "trend": parts[-1]})
    except Exception as e:
        print(f"解析失败: {e}")
        
    # 去重
    unique_queries = list({q['keyword']: q for q in queries}.values())
    return unique_queries

def compare_with_gpts(keywords):
    """对比关键词与 gpts 的趋势"""
    if not keywords:
        return []
    
    # 4个一组对比
    winners = []
    for i in range(0, len(keywords), 4):
        batch = keywords[i:i+4]
        all_kw = batch + ["gpts"]
        print(f"📊 对比趋势: {', '.join(batch)} vs gpts")
        
        q = ",".join(all_kw)
        url = f"https://trends.google.com/trends/explore?date=now%207-d&q={q}&hl=en-US"
        run_cmd(["open", url])
        time.sleep(10)
        
        # 提取平均值
        js_script = """
        (() => {
            const values = Array.from(document.querySelectorAll('.user-set-value, .value'))
                            .filter(s => s.innerText.match(/^\\d+$/))
                            .map(n => parseInt(n.innerText));
            return JSON.stringify(values);
        })()
        """
        output = run_cmd(["eval", js_script])
        try:
            json_str = output.strip()
            if "[" in json_str:
                json_str = json_str[json_str.find("[") : json_str.rfind("]") + 1]
                averages = json.loads(json_str)
                
                if len(averages) >= len(all_kw):
                    gpts_avg = averages[-1]
                    for idx, kw in enumerate(batch):
                        kw_avg = averages[idx]
                        if kw_avg > gpts_avg:
                            winners.append({
                                "keyword": kw,
                                "avg": kw_avg,
                                "gpts_avg": gpts_avg,
                                "timestamp": datetime.now().isoformat()
                            })
                            print(f"  🔥 超过 gpts: {kw} ({kw_avg} > {gpts_avg})")
        except Exception as e:
            print(f"对比解析失败: {e}")
            
    return winners

def main():
    all_rising = []
    # 5个一组处理词根
    root_batches = [ROOT_WORDS[i:i + 5] for i in range(0, len(ROOT_WORDS), 5)]
    
    print(f"🚀 开始第一轮扫描: 处理 {len(ROOT_WORDS)} 个词根 (分为 {len(root_batches)} 组)...")
    for batch in root_batches:
        queries = get_rising_queries(batch)
        for q in queries:
            q['origin'] = ", ".join(batch)
            all_rising.append(q)
        time.sleep(2)
        
    # 第一轮去重
    unique_rising = list({q['keyword']: q for q in all_rising}.values())
    print(f"✅ 第一轮收集完成，共发现 {len(unique_rising)} 个独特飙升词")
    
    # 二级挖掘：检查发现的飙升词的“相关查询”
    print(f"🔍 开始二级挖掘: 检查所有飙升词的衍生词 (5个一组)...")
    all_secondary = []
    rising_keywords_list = [q['keyword'] for q in unique_rising]
    secondary_batches = [rising_keywords_list[i:i + 5] for i in range(0, len(rising_keywords_list), 5)]
    
    for batch in secondary_batches:
        secondary_queries = get_rising_queries(batch)
        for sq in secondary_queries:
            sq['origin'] = ", ".join(batch)
            all_secondary.append(sq)
        time.sleep(2)
        
    # 合并所有发现的词并去重
    total_candidates = list({q['keyword']: q for q in unique_rising + all_secondary}.values())
    candidate_keywords = [q['keyword'] for q in total_candidates]
    print(f"📈 最终候选词总数: {len(candidate_keywords)}，准备与 gpts 对比 (4个一组)...")
    
    # 与 gpts 对比 (4个词 + gpts = 5个上限)
    winners = compare_with_gpts(candidate_keywords)
    
    # 汇总结果
    final_report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_roots_scanned": len(ROOT_WORDS),
        "total_rising_found": len(unique_rising),
        "total_secondary_found": len(all_secondary),
        "winners_count": len(winners),
        "winners": winners
    }
    
    # 保存结果
    result_file = DATA_DIR / f"winners_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 任务完成！结果已保存至 {result_file}")
    
    # 生成 Markdown 报告
    report_md = f"# Google Trends 监控报告 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    report_md += f"## 概览\n- 扫描词根数: {len(ROOT_WORDS)}\n- 发现飙升词: {len(unique_rising)}\n- 胜出词数 (超过 gpts): {len(winners)}\n\n"
    report_md += "## 胜出关键词详情\n"
    report_md += "| 关键词 | 平均热度 | gpts平均热度 | 优势 |\n"
    report_md += "| --- | --- | --- | --- |\n"
    for w in winners:
        advantage = w['avg'] - w['gpts_avg']
        report_md += f"| {w['keyword']} | {w['avg']} | {w['gpts_avg']} | +{advantage} |\n"
    
    report_path = DATA_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"📝 Markdown 报告已生成: {report_path}")

    run_cmd(["close"])

if __name__ == "__main__":
    main()
