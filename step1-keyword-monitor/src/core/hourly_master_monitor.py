import subprocess
import sys
import os
import time
import io
from datetime import datetime

# 强制设置标准输出为 UTF-8，解决 Windows 上的 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 获取当前脚本所在目录
# 现在脚本位于 src/core，需要定位到项目根目录
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CORE_DIR, "..", ".."))

def run_script(script_path, args=None):
    """
    运行子脚本并记录日志
    """
    name = os.path.basename(script_path)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] >>> Starting: {name}")
    
    # 将相对路径转换为绝对路径
    if not os.path.isabs(script_path):
        script_path = os.path.join(PROJECT_ROOT, script_path)
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        # 使用 subprocess.run 保持同步执行，cwd 设置为项目根目录
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] <<< Success: {name}")
            # 只输出最后几行重要信息
            last_lines = result.stdout.strip().split('\n')[-5:]
            for line in last_lines:
                print(f"  {line}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] !!! Error: {name} (Exit Code: {result.returncode})")
            print(f"  Error Output: {result.stderr[:500]}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] !!! Exception running {name}: {e}")

def main():
    print("="*60)
    print(f"🚀 HOURLY MASTER MONITOR START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 1. 扫描大站新游 (platforms)
    run_script(os.path.join("src", "monitors", "platforms", "check_new_games.py"))

    # 2. 扫描站点监控 (sitemaps)
    run_script(os.path.join("src", "monitors", "sitemaps", "google_site_monitor.py"))
    run_script(os.path.join("src", "monitors", "sitemaps", "check_sitemaps.py"))

    # 3. 运行全平台数据采集 (platforms)
    run_script(os.path.join("src", "monitors", "platforms", "collect_all.py"))

    # 4. 词根与趋势验证 (trends)
    run_script(os.path.join("src", "monitors", "trends", "monitor_root_keywords.py"))
    run_script(os.path.join("src", "monitors", "trends", "trends_agent_scout_v2.py"))

    # 5. 生成汇总报告 (core)
    run_script(os.path.join("src", "core", "report_all.py"))

    print("\n" + "="*60)
    print(f"✅ ALL MONITORING TASKS COMPLETED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
