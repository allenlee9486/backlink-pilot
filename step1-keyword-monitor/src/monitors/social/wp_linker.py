import asyncio
import json
import os
import sys
import io
import random
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
CHROME_DEBUG_URL = "http://127.0.0.1:9222"
HISTORY_FILE = Path(__file__).parent / "data" / "wp_linker_history.json"
USER_INFO = {
    "name": "buildaringfarm",
    "email": "roivikash516@gmail.com",
    "website": "https://buildaringfarm.xyz"
}

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False, indent=2)

TARGET_URLS = [
    "https://www.readunwritten.com/2026/03/04/finally-chose-myself-needs/",
    "https://loveandmarriageblog.com/how-to-save-10000-in-a-year-27-40-rule/#comment-757500",
    "https://www.fivereasonssports.com/voices/mateos-hoop-diary-the-heats-quest-for-the-sixth-seed-and-other-nba-notes/",
    "https://video.assens.dk/osterbo-i-assens-kommune",
    "https://www.nudeandhappy.com/2025/12/21/slow-work-revolution-redefining-success-and-pace/#comment-18424",
    "https://kolimi.org/%E0%B0%A4%E0%B1%86%E0%B0%B2%E0%B0%82%E0%B0%97%E0%B0%BE%E0%B0%A3-%E0%B0%89%E0%B0%A6%E0%B1%8D%E0%B0%AF%E0%B0%AE-%E0%B0%AA%E0%B0%BE%E0%B0%9F%E0%B0%B2%E0%B1%81/",
    "https://beneaththetangles.com/2025/10/13/first-impression-one-punch-man-season-3/",
    "https://www.weirdsciencedccomics.com/2025/10/absolute-superman-12-review.html",
    "https://www.airingmylaundry.com/2025/07/satuli-canteen-in-animal-kingdom-is.html",
    "https://www.itsfilmedthere.com/",
    "https://mummyfever.co.uk/fatjoe-who-should-sign-up-and-why/",
    "https://www.totschooling.net/2017/09/halloween-color-by-number.html",
    "https://vitamagazine.com/2024/02/18/where-to-find-the-clearest-warmest-water-in-the-world/",
    "https://deungdutjai.com/2010/01/18/%E0%B9%80%E0%B8%A5%E0%B9%88%E0%B8%99%E0%B8%82%E0%B8%AD%E0%B8%87%E0%B8%AA%E0%B8%B9%E0%B8%87-len-kong-soong-big-ass/",
    "https://thesocietypages.org/socimages/2023/07/11/them-ms-sexualized-media-and-emphasized-femininity/",
    "https://brownbagteacher.com/number-talks-how-and-why/",
    "https://momsavesmoney.net/how-to-make-smores-in-the-air-fryer/",
    "https://www.home-adda.com/brigade-northridge/",
    "https://www.dinnerwithjulie.com/2017/11/01/jasons-grandmas-hour-buns/",
    "https://webinar.gea.com/pet-food-tech-day-01-flexible",
    "https://www.unexpectedelegance.com/read-tape-measure-non-mathematical-mind/#comment-195820",
    "http://old.burczymiwbrzuchu.pl/2018/07/tarta-z-borowkami-i-beza.html?sc=1751333819444#c2186173797139604994",
    "https://www.unoriginalmom.com/25-free-halloween-cut-files/#comment-887361",
    "https://portfolio.newschool.edu/zacharyfernandez/2020/11/15/girl-innovators-fun-home-book-review/#comment-188",
    "https://sites.williams.edu/srd4/methods-exercises/methods-exercise-6/?unapproved=1506&moderation-hash=69f899534cff9776a8609444d7ac7fd1#comment-1506",
    "https://sites.suffolk.edu/connormulcahy/2014/02/28/solar-energy-lab/photo-8-2/#comment-405731",
    "https://terminklick.stuve.fau.de/poll/0jYfQ8qDcN/",
    "https://edottosgd.sanita.puglia.it/knowledgetree/action.php?kt_path_info=ktcore.actions.document.discussion&fDocumentId=16801&fThreadId=2300&action=viewThread",
    "http://www15420ui.sakura.ne.jp/snapnote/diary/class/20081129_02.htm#wb",
    "https://www.techbang.com/posts/115915-ezcast?comment_page=1",
    "https://calibeautysupply.de/blog/best-leather-bags",
    "https://dunapodanslair.blogs.fr/index.html",
    "https://www.simonsaysstampblog.com/blog/make-tons-of-tags-with-our-limited-edition-holiday-tag-kit-while-supplies-last/comment-page-1/#comment-975569",
    "https://webkit.dti.ne.jp/bbs1/mekahouse/mekag/"
]

# 评论模板库 (支持 HTML 锚文本)
LINK_TAG = '<a href="https://buildaringfarm.xyz/">buildaringfarm</a>'
COMMENT_TEMPLATES = [
    "I really enjoyed reading this article about {topic}. It provided some great insights. By the way, for those interested in similar topics, I've found " + LINK_TAG + " to be a very helpful resource.",
    "This post on {topic} is very well-written. I've been researching this lately and found some great info over at " + LINK_TAG + " as well. Thanks for sharing!",
    "Great content! {topic} is such an interesting subject. I actually bookmarked this and also " + LINK_TAG + " for my daily reading. Keep up the good work!",
    "Thanks for the detailed breakdown of {topic}. It's clear you've put a lot of thought into this. I've been following " + LINK_TAG + " for similar updates, and your post fits right in!",
    "I found this article very helpful. {topic} can be a complex area, but you've explained it very clearly. I've been looking for more info like this and " + LINK_TAG + " has some great pointers too."
]

async def get_page(browser_context):
    pages = browser_context.pages
    if pages:
        return pages[0]
    return await browser_context.new_page()

async def generate_smart_comment(page):
    """根据页面标题和内容生成走心评论"""
    try:
        title = await page.title()
        # 简单清洗标题作为 topic
        topic = title.split('|')[0].split('-')[0].strip()
        template = random.choice(COMMENT_TEMPLATES)
        return template.format(topic=topic)
    except:
        return "Thanks for sharing this great article. I found it very informative and well-written!"

async def handle_google_login(page):
    """尝试点击页面上的谷歌登录按钮"""
    google_selectors = [
        'button:has-text("Google")',
        'a:has-text("Google")',
        '[data-provider="google"]',
        '.login-google',
        '#google-login'
    ]
    for selector in google_selectors:
        try:
            btn = await page.query_selector(selector)
            if btn:
                print(f"  🔑 发现谷歌登录按钮，正在尝试点击...")
                await btn.click()
                await asyncio.sleep(5) # 等待登录跳转或弹出
                return True
        except: pass
    return False

async def post_comment(browser_context, url, history):
    # 提取域名进行去重检查
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    if domain in history:
        print(f"  ⏭️ 跳过已处理域名: {domain}")
        return {"url": url, "status": "skipped", "reason": "Domain already processed"}

    print(f"🚀 正在处理: {url}")
    page = await browser_context.new_page()
    result = {"url": url, "status": "failed", "reason": ""}
    
    try:
        # 1. 访问页面
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(5)
        
        # 检查是否需要登录
        login_required = await page.evaluate('''() => {
            const text = document.body.innerText.toLowerCase();
            return text.includes("log in to post") || text.includes("must be logged in");
        }''')
        
        if login_required:
            print("  🔒 页面提示需要登录...")
            if await handle_google_login(page):
                print("  ✅ 尝试执行谷歌登录流程...")
                # 这里假设用户已经在本地 Chrome 登录了谷歌，点击后会自动完成或弹出
                await asyncio.sleep(5)
            else:
                print("  ❌ 需要登录但未找到谷歌登录方式。")
                result["reason"] = "Login required but no Google login found"
                await page.close()
                return result

        # 2. 生成评论
        comment_text = await generate_smart_comment(page)
        print(f"  📝 生成评论: {comment_text[:50]}...")
        
        # 3. 定位评论表单
        # 兼容 WordPress, Blogger/Blogspot 等多种平台
        form_selectors = {
            "author": 'input[name="author"], #author, input[name="authorName"]',
            "email": 'input[name="email"], #email, input[name="authorEmail"]',
            "url": 'input[name="url"], #url, input[name="authorUrl"]',
            "comment": 'textarea[name="comment"], #comment, textarea[name="commentBody"]',
            "submit": '#submit, #comment-submit, .submit, #comment-post, .comment-submit'
        }
        
        # 特殊处理 Blogger (通常在 iframe 中)
        blogger_iframe = await page.query_selector('#comment-editor')
        target_frame = page
        if blogger_iframe:
            print("  ℹ️ 检测到 Blogger 评论框，正在尝试进入 iframe...")
            frame_element = await blogger_iframe.content_frame()
            if frame_element:
                target_frame = frame_element
        
        # 检查是否存在表单
        comment_area = await target_frame.query_selector(form_selectors["comment"])
        if not comment_area:
            print("  ⚠️ 未找到评论框，可能评论已关闭或需要特定权限。")
            result["reason"] = "No comment area found"
            await page.close()
            return result

        # 4. 填写表单
        try:
            # 填入姓名
            author_input = await target_frame.query_selector(form_selectors["author"])
            if author_input: await author_input.fill(USER_INFO["name"])
            
            # 填入邮箱
            email_input = await target_frame.query_selector(form_selectors["email"])
            if email_input: await email_input.fill(USER_INFO["email"])
            
            # 填入网址 (核心外链位)
            url_input = await target_frame.query_selector(form_selectors["url"])
            if url_input: await url_input.fill(USER_INFO["website"])
            
            # 填入评论内容
            await comment_area.fill(comment_text)
            
            # 5. 提交
            print("  🖱️ 正在提交评论...")
            submit_btn = await target_frame.query_selector(form_selectors["submit"])
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(8) # 等待提交结果
                
                # 检查是否提交成功
                content = await page.content()
                success_indicators = [
                    "awaiting moderation", 
                    "Your comment was posted", 
                    "success", 
                    "thank you for your comment",
                    "comment-form-post-message"
                ]
                
                if any(ind in content.lower() for ind in success_indicators):
                    print("  ✅ 评论发布成功（或进入审核队列）")
                    result["status"] = "success"
                    history.add(domain) # 只有成功才记录
                else:
                    print("  ❓ 提交动作已执行，但未检测到明确的成功反馈。")
                    result["status"] = "uncertain"
            else:
                print("  ❌ 未找到提交按钮。")
                result["reason"] = "No submit button found"
        except Exception as e:
            print(f"  ❌ 填写/提交过程出错: {e}")
            result["reason"] = str(e)
            
    except Exception as e:
        print(f"  ❌ 访问失败: {e}")
        result["reason"] = str(e)
    finally:
        await page.close()
        
    return result

async def main():
    async with async_playwright() as p:
        browser = None
        try:
            print(f"🔗 正在连接到本地 Chrome ({CHROME_DEBUG_URL})... ")
            browser = await p.chromium.connect_over_cdp(CHROME_DEBUG_URL)
            context = browser.contexts[0]
            
            history = load_history()
            print(f"  📂 已加载历史记录: {len(history)} 个域名")
            
            all_results = []
            for url in TARGET_URLS:
                res = await post_comment(context, url, history)
                all_results.append(res)
                if res["status"] == "success":
                    save_history(history) # 实时保存
                
                if res["status"] != "skipped":
                    wait_time = random.randint(30, 60)
                    print(f"  💤 等待 {wait_time} 秒后继续...")
                    await asyncio.sleep(wait_time)
            
            # 记录结果
            report_path = Path(__file__).parent / "data" / "wp_linker_report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 任务完成！报告已保存至 {report_path}")
            
        except Exception as e:
            print(f"❌ 运行失败: {e}")
        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
