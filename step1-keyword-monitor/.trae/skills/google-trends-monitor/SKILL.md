---
name: "google-trends-monitor"
description: "自动化监控 Google Trends 飙升词并进行 GPTs 对比分析。适用于市场调研与选品。"
---

# Google Trends Monitor Skill

## 1. Skill 用途 (Purpose)
本 Skill 旨在通过自动化脚本监控全球范围内的 Google Trends 飙升关键词，并通过与基准词（如 GPTs）的热度对比，识别具有真实爆发潜力的“蓝海”关键词，为 SEO 套利和新项目选品提供数据支持。

## 2. Skill 内容 (Content)
- **核心定义**：负责识别用户进行趋势调研的意图，并分发任务至自动化脚本。
- **触发条件**：用户提到“监控趋势”、“寻找新词”、“分析 Google Trends”或“对比 GPTs 热度”时。
- **角色定义**：高级市场分析师 & 自动化数据专家。
- **核心工作流**：
    1.  调用 `Scripts/monitor.py` 执行词根扫描。
    2.  提取“Rising”与“Breakout”查询。
    3.  执行 4+1 批量热度对比。
    4.  生成分析报告并输出胜出关键词。

## 3. 交付要求 (Delivery Requirements)
- 输出结果必须包含关键词的平均热度数值。
- 必须明确标注哪些词的趋势超过了 GPTs。
- 报告需以 Markdown 格式呈现，包含趋势描述和建议操作。

## 4. 禁用事项与规则 (Prohibitions)
- **禁止**：在未开启 Chrome 9222 调试端口的情况下尝试运行。
- **禁止**：直接输出无数据的关键词。
- **规则**：所有数据必须基于过去 7 天的全球（Worldwide）维度。

## 5. 目录引导
- **参考规范**：见 [References/Standard.md](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/google-trends-monitor/References/Standard.md)
- **物料资源**：见 [Assets/RootWords.json](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/google-trends-monitor/Assets/RootWords.json)
- **自动化脚本**：见 [Scripts/monitor.py](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/google-trends-monitor/Scripts/monitor.py)
