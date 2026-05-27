
import time
import random
import os
import sys
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# 强制设置标准输出为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加 monitors/lib 到路径以导入 TrendsAnalyzer
sys.path.append(str(Path(__file__).parent))
from monitors.lib.trends_analyzer import TrendsAnalyzer

class RootKeywordMonitor:
    def __init__(self, keywords_file='root_keywords.txt'):
        self.analyzer = TrendsAnalyzer()
        self.keywords_file = keywords_file
        self.winners_file = f"root_trends_winners.csv"
        self.status_file = "keyword_monitor_status.csv"
        self.keywords = self._load_keywords()
        self.status_df = self._load_status()

    def _load_keywords(self):
        if not os.path.exists(self.keywords_file):
            return []
        with open(self.keywords_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def _load_status(self):
        if os.path.exists(self.status_file):
            return pd.read_csv(self.status_file)
        else:
            return pd.DataFrame({'keyword': self.keywords, 'status': 'pending', 'last_check': ''})

    def analyze_batch(self, batch_size=5):
        print(f"--- Root Keyword Monitoring Batch (Size: {batch_size}) ---")
        
        pending = self.status_df[self.status_df['status'] == 'pending']
        if pending.empty:
            print("All keywords processed.")
            return

        batch = pending.head(batch_size)
        
        for idx, row in batch.iterrows():
            kw = row['keyword']
            print(f"Checking: {kw}...", end="", flush=True)
            
            # 1. Check 7 days
            res_7d = self.analyzer.compare_with_benchmark(kw)
            
            if res_7d:
                if res_7d['exceeded']:
                    print(" [WINNER 7D]", end="")
                    # 2. Verify 30 days
                    res_30d = self._verify_30d(kw)
                    if res_30d and res_30d['exceeded']:
                        print(" [SOLID 30D]")
                        self._save_winner(kw, res_7d, res_30d, "Solid Trend")
                    else:
                        print(" [Spiky]")
                        self._save_winner(kw, res_7d, res_30d, "Short Burst")
                else:
                    print(" [Below]")
                
                # Update status
                self.status_df.at[idx, 'status'] = 'done'
                self.status_df.at[idx, 'last_check'] = datetime.now().strftime('%Y-%m-%d')
            else:
                print(" [Error/RateLimit]")
                # If error, maybe don't mark as done to retry later
                time.sleep(60) # Longer sleep on error
            
            self.status_df.to_csv(self.status_file, index=False)
            time.sleep(random.uniform(15, 30)) # Conservative delay

    def _save_winner(self, kw, res_7d, res_30d, status):
        new_winner = {
            "keyword": kw,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "latest_7d": res_7d['latest_keyword'],
            "avg_7d": res_7d['avg_keyword'],
            "avg_30d": res_30d['avg_keyword'] if res_30d else 0,
            "status": status
        }
        
        if os.path.exists(self.winners_file):
            winners_df = pd.read_csv(self.winners_file)
            winners_df = pd.concat([winners_df, pd.DataFrame([new_winner])], ignore_index=True)
        else:
            winners_df = pd.DataFrame([new_winner])
        
        winners_df.to_csv(self.winners_file, index=False, encoding='utf-8-sig')

    def _verify_30d(self, keyword):
        kw_list = [self.analyzer.benchmark, keyword]
        try:
            self.analyzer.pytrends.build_payload(kw_list, cat=0, timeframe='today 1-m', geo='', gprop='')
            df = self.analyzer.pytrends.interest_over_time()
            if df.empty: return None
            if 'isPartial' in df.columns: df = df.drop(columns=['isPartial'])
            return {"avg_keyword": round(float(df[keyword].mean()), 2), "exceeded": any(df[keyword] > df[self.analyzer.benchmark])}
        except:
            return None

if __name__ == "__main__":
    monitor = RootKeywordMonitor()
    # 每次运行处理 5 个，防止被封
    monitor.analyze_batch(batch_size=3)
