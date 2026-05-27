---
name: "master-monitor-orchestrator"
description: "The central control system that runs all monitoring tasks, collects data, and generates a summary report. Invoke when user wants to run the full monitoring pipeline."
---

# Master Monitor Orchestrator

This skill acts as the brain of the monitoring system, coordinating data collection across platforms and generating human-readable reports.

## Core Scripts
- [hourly_master_monitor.py](file:///d:/开发设计工具/jiankong_sitemap/hourly_master_monitor.py): The main entry point for the hourly run.
- [collect_all.py](file:///d:/开发设计工具/jiankong_sitemap/monitors/collect_all.py): Orchestrates data collection from Roblox, Steam, etc.
- [report_all.py](file:///d:/开发设计工具/jiankong_sitemap/monitors/report_all.py): Generates the `LATEST_SUMMARY.md` report.

## Usage
Run the full pipeline:
```bash
python hourly_master_monitor.py
```

## Setup in New Projects
1. Copy all scripts and maintain the directory structure.
2. Ensure `requirements.txt` dependencies are installed.
3. Set up a Windows Scheduled Task using `scheduler_windows.py` if needed.
