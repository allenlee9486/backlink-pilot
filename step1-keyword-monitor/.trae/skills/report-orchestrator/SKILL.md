---
name: "report-orchestrator"
description: "调度全平台监控任务并生成汇总情报报告。当需要获取最终商业决策建议时使用。"
---

# Report Orchestrator

此模块是整个系统的“大脑”，负责调度所有子模块并将碎片信号拼凑成完整的商业报告。

## 核心脚本
- `src/core/hourly_master_monitor.py`: 每小时运行一次的全平台调度器。
- `src/core/report_all.py`: 情报汇总与 Markdown 报告生成器。

## 运行方式
```bash
python src/core/hourly_master_monitor.py
```

## 迁移说明
1. 复制 `src/core/` 目录。
2. 确保 `data/raw/` 和 `data/reports/` 目录结构已创建。
3. 此模块依赖于其他所有 `src/monitors/` 下的子模块。
