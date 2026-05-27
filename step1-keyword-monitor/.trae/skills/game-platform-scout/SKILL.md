---
name: "game-platform-scout"
description: "Monitors sitemaps and 'new games' pages of major gaming platforms (Poki, CrazyGames, Y8, etc.). Invoke when user wants to discover newly released games or monitor platform updates."
---

# Game Platform Scout

This skill monitors major gaming platforms to discover new content as soon as it's published.

## Core Scripts
- [check_sitemaps.py](file:///d:/开发设计工具/jiankong_sitemap/monitors/check_sitemaps.py): Scans `robots.txt` and `sitemap.xml` for new entries.
- [check_new_games.py](file:///d:/开发设计工具/jiankong_sitemap/check_new_games.py): Scrapes 'New Games' pages for immediate signals.

## Usage
Run the following command to scan all configured platforms:
```bash
python monitors/check_sitemaps.py
python check_new_games.py
```

## Setup in New Projects
1. Copy the scripts to a `monitors/` directory.
2. Install dependencies: `pip install requests beautifulsoup4`.
3. Update the `TARGET_URLS` in each script as needed.
