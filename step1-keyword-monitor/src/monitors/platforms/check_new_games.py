import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import sys
import io

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

NEW_GAME_PAGES = [
    "https://y8.com/new/games",
    "https://poki.com/en/new",
    "https://www.addictinggames.com/new-games",
    "https://html5games.com/All-Games",
    "https://www.onlinegames.io/new-games/",
    "https://www.twoplayergames.org/",
    "https://www.crazygames.com/new"
]

def check_new_pages():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"\n🚀 Checking Specific 'New Games' Pages - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    for url in NEW_GAME_PAGES:
        try:
            logging.info(f"Fetching {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 简单统计页面链接数，实际可根据各站结构精准提取
                links = soup.find_all('a')
                print(f"✅ {url.split('//')[1].split('/')[0]}: Found {len(links)} potential game links")
            else:
                logging.error(f"Failed to fetch {url}: Status {response.status_code}")
        except Exception as e:
            logging.error(f"Error checking {url}: {e}")

if __name__ == "__main__":
    check_new_pages()
