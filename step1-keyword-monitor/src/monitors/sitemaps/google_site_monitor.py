import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re
import logging
from urllib.parse import quote
import random
import os
import sys
import io

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class GameSiteMonitor:
    def __init__(self, sites_file="game_sites.txt"):
        """
        初始化监控器
        :param sites_file: 包含游戏网站列表的文本文件
        """
        self.sites = self._load_sites(sites_file)
        self.headers = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
        ]
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('site_monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging

    def _load_sites(self, filename):
        """加载网站列表"""
        if not os.path.exists(filename):
            self.logger.error(f"Sites file {filename} not found!")
            return []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            self.logger.error(f"Error loading sites: {e}")
            return []

    def build_google_search_url(self, site, time_range):
        """
        构建Google搜索URL
        :param site: 网站域名
        :param time_range: 时间范围('24h' or '1w')
        """
        base_url = "https://www.google.com/search"
        tbs = 'qdr:d' if time_range == '24h' else 'qdr:w'
        
        query = f'site:{site}'
        params = {
            'q': query,
            'tbs': tbs,
            'num': 50  # 抓取前50条
        }
        
        query_string = '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()])
        return f"{base_url}?{query_string}"

    def extract_search_results(self, html_content):
        """
        从Google搜索结果页面提取信息
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # Google 搜索结果通常在 div.g 中
        for result in soup.select('div.g'):
            try:
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    url = link_elem['href']
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    game_name = self.clean_game_name(title)
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'game_name': game_name
                    })
            except Exception as e:
                continue
                
        return results

    def clean_game_name(self, title):
        """
        从标题中智能提取游戏名称
        """
        # 1. 处理常见的分割符
        name = title.split(' - ')[0].split(' | ')[0].split(' : ')[0]
        
        # 2. 移除常见的SEO后缀
        junk_keywords = [
            'Play Online', 'Free Game', 'Download', 'Guide', 'Walkthrough', 
            'Wiki', 'Codes', 'Review', 'Cheat', 'Hack', 'Mod', 'APK', 
            '攻略', '下载', '免费', '官网', '评测'
        ]
        for kw in junk_keywords:
            name = re.sub(rf'\b{kw}\b', '', name, flags=re.IGNORECASE)
        
        # 3. 提取符号内的内容 (如 《游戏名》)
        brackets = [
            (r'《(.+?)》', 1),
            (r'【(.+?)】', 1),
            (r'\[(.+?)\]', 1),
            (r'"(.+?)"', 1)
        ]
        for pattern, group in brackets:
            match = re.search(pattern, name)
            if match:
                return match.group(group).strip()
        
        return name.strip()

    def run(self):
        """执行监控流程"""
        if not self.sites:
            self.logger.warning("No sites to monitor. Exiting.")
            return

        all_data = []
        for site in self.sites:
            for period in ['24h', '1w']:
                self.logger.info(f"Checking {site} for new pages in last {period}...")
                url = self.build_google_search_url(site, period)
                
                try:
                    # 模拟随机请求间隔
                    time.sleep(random.uniform(3, 7))
                    resp = requests.get(url, headers=random.choice(self.headers), timeout=15)
                    
                    if resp.status_code == 200:
                        items = self.extract_search_results(resp.text)
                        for item in items:
                            item.update({
                                'source_site': site,
                                'time_range': period,
                                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                        all_data.extend(items)
                        self.logger.info(f"Successfully found {len(items)} new pages on {site}")
                    elif resp.status_code == 429:
                        self.logger.error("Rate limit hit (429). Suggest using a proxy or longer delays.")
                        break
                except Exception as e:
                    self.logger.error(f"Failed to crawl {site}: {e}")

        if all_data:
            df = pd.DataFrame(all_data)
            # 移除重复项 (基于URL)
            df = df.drop_duplicates(subset=['url'])
            
            filename = f'new_game_pages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"Monitoring complete. Report saved to {filename}")
            
            # 同时生成一个简要统计
            print("\n" + "="*30)
            print("NEW GAMES DISCOVERY REPORT")
            print("="*30)
            print(f"Total New Pages Found: {len(df)}")
            print("\nTop Active Sites:")
            print(df['source_site'].value_counts().head())
            print("="*30)
        else:
            self.logger.info("No new pages detected in this run.")

if __name__ == "__main__":
    monitor = GameSiteMonitor()
    monitor.run()
