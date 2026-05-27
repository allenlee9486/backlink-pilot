---
name: "google-trends-analyzer"
description: "Analyzes Google Trends for specific root keywords and compares them against benchmarks (like GPTS). Invoke when user wants to validate market demand or find rising keywords."
---

# Google Trends Analyzer

This skill automates the process of checking keyword trends and identifying 'Winners' that exceed benchmark interest.

## Core Scripts
- [monitor_root_keywords.py](file:///d:/开发设计工具/jiankong_sitemap/monitor_root_keywords.py): Batch checks root keywords against a benchmark.
- [trends_analyzer.py](file:///d:/开发设计工具/jiankong_sitemap/monitors/lib/trends_analyzer.py): Library for handling pytrends logic.

## Usage
Run the analyzer with:
```bash
python monitor_root_keywords.py
```

## Setup in New Projects
1. Copy the script and the `monitors/lib/` directory.
2. Install dependencies: `pip install pytrends pandas`.
3. Configure your `ROOT_WORDS` and `benchmark` in the script.
