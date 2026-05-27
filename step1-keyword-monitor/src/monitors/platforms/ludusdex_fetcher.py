import asyncio
import sys
import io
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def fetch_ludusdex():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # 1. 首先抓取 Weekly 列表页，获取所有子文章链接
            print("Fetching Weekly list...")
            await page.goto("https://ludusdex.com/weekly/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2)
            
            weekly_links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(href => href.includes('ludusdex.com/weekly/') && href !== 'https://ludusdex.com/weekly/');
            }''')
            
            # 去重
            weekly_links = list(set(weekly_links))[:5] # 先取前5篇分析逻辑
            print(f"Found {len(weekly_links)} weekly articles. Analyzing first 5...")
            
            urls_to_fetch = [
                "https://ludusdex.com/blog/",
                "https://ludusdex.com/guide/",
                "https://ludusdex.com/radar/"
            ] + weekly_links
            
            results = {}
            for url in urls_to_fetch:
                print(f"Fetching {url}...")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3)
                    data = await page.evaluate('''() => {
                        // 尝试抓取正文内容
                        const article = document.querySelector('article') || document.querySelector('main') || document.body;
                        return {
                            title: document.title,
                            content: article.innerText.slice(0, 10000),
                            html: article.innerHTML.slice(0, 5000) // 用于分析结构
                        };
                    }''')
                    results[url] = data
                except Exception as e:
                    print(f"  Failed to fetch {url}: {e}")
                
            import json
            with open("ludusdex_analysis.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            await browser.close()
            print("Done! Results saved to ludusdex_analysis.json")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_ludusdex())
