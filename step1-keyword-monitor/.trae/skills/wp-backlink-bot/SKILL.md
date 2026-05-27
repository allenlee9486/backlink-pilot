---
name: "wp-backlink-bot"
description: "Automates posting comments with backlinks to WordPress and Blogger sites. Invoke when user wants to build SEO backlinks for a specific URL."
---

# WP Backlink Bot

This skill uses Playwright to automate commenting on relevant blogs, including smart comment generation and backlink injection.

## Core Scripts
- [wp_linker.py](file:///d:/开发设计工具/jiankong_sitemap/monitors/wp_linker.py): Main automation script using Playwright.

## Usage
Ensure Chrome is running with remote debugging:
```bash
# Start Chrome
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug"

# Run Linker
python monitors/wp_linker.py
```

## Setup in New Projects
1. Copy `wp_linker.py` and create a `monitors/data/` directory for history.
2. Install dependencies: `pip install playwright`.
3. Run `playwright install chromium`.
4. Update `USER_INFO` and `TARGET_URLS` in the script.
