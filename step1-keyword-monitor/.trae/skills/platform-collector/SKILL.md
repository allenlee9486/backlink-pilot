---
name: "platform-collector"
description: "从 Roblox, Steam, CrazyGames 等平台采集热门游戏、在线人数及新游列表。当需要分析平台实时热度时使用。"
---

# Platform Data Collector

此模块负责从各大垂直游戏平台抓取实时数据，特别是并发在线人数（CCU）。

## 核心脚本
- `src/monitors/platforms/collect_all.py`: 调度所有平台的采集任务。
- `src/monitors/platforms/roblox/scripts/collect.py`: 采集 Roblox Top 1000 游戏及并发。
- `src/monitors/platforms/steam/scripts/collect.py`: 采集 Steam 畅销榜。
- `src/monitors/platforms/check_new_games.py`: 快速扫描大站“最新上架”页面。

## 运行方式
```bash
python src/monitors/platforms/collect_all.py
```

## 迁移说明
1. 复制 `src/monitors/platforms/` 目录。
2. 确保 `src/utils/discovery.py` 已存在。
3. 需要 `sqlite3` 环境（Python 自带）用于存储快照。
