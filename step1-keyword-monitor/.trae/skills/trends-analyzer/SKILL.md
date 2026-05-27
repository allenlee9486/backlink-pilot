---
name: "trends-analyzer"
description: "通过 Google Trends 验证词根爆发潜力。当需要筛选 'Winner' 关键词或验证搜索热度时使用。"
---

# Google Trends Analyzer

此模块通过 Google Trends 接口（结合 agent-browser）验证关键词的真实爆发潜力。

## 核心脚本
- `src/monitors/trends/monitor_root_keywords.py`: 批量验证词根热度。
- `src/monitors/trends/trends_agent_scout_v2.py`: 使用 agent-browser 自动化获取趋势数据。
- `src/monitors/trends/trends_analyzer.py`: 趋势分析核心逻辑。

## 运行方式
```bash
python src/monitors/trends/monitor_root_keywords.py
```

## 迁移说明
1. 复制 `src/monitors/trends/` 目录。
2. 确保已安装并配置 `agent-browser` 及其 Profile。
3. 依赖 `pandas` 和 `pytrends`。
