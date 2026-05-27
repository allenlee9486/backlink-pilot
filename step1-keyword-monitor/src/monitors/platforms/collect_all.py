#!/usr/bin/env python3
"""
多平台监控总控脚本
依次调用各个平台的采集脚本
"""

import subprocess
import sys
import os
import io
from pathlib import Path
from datetime import datetime, timezone

# 强制设置标准输出为 UTF-8，解决 Windows 上的 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MONITORS_DIR = Path(__file__).parent

SCRIPTS = [
    MONITORS_DIR / "roblox" / "scripts" / "collect.py",
    MONITORS_DIR / "steam" / "scripts" / "collect.py",
    MONITORS_DIR / "crazygames" / "scripts" / "collect.py",
    MONITORS_DIR / "itch" / "scripts" / "collect.py",
]

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] === 开始全平台数据采集 ===")
    
    for script in SCRIPTS:
        if not script.exists():
            print(f"⚠️ 跳过不存在的脚本: {script}")
            continue
            
        print(f"\n🚀 正在运行: {script.parent.parent.name} 采集...")
        try:
            # 运行脚本并捕获输出
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                cwd=str(script.parent.parent),
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            print(result.stdout)
            if result.stderr:
                print(f"❌ 错误信息:\n{result.stderr}")
        except Exception as e:
            print(f"❌ 运行脚本 {script} 时发生异常: {e}")

    print(f"\n[{ts}] === 全平台采集任务完成 ===")

if __name__ == "__main__":
    main()
