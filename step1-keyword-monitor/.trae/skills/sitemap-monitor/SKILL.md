---
name: "sitemap-monitor"
description: "监控竞争对手和行业大站的 Sitemap 及索引状态。当需要发现新页面或监控对手动态时使用。"
---

# Sitemap & Indexing Monitor

此模块负责监控目标站点的 `sitemap.xml` 和谷歌索引状态，第一时间捕捉新增页面。

## 核心脚本
- `src/monitors/sitemaps/check_sitemaps.py`: 监控各大站（Poki, CrazyGames 等）的 Sitemap 新增 URL。
- `src/monitors/sitemaps/google_site_monitor.py`: 监控特定站点在谷歌上的索引收录情况。

## 运行方式
```bash
python src/monitors/sitemaps/check_sitemaps.py
python src/monitors/sitemaps/google_site_monitor.py
```

## 迁移说明
1. 复制 `src/monitors/sitemaps/` 目录。
2. 确保 `src/utils/sitemap_parser.py` 已存在。
3. 在新项目中安装 `requests` 和 `beautifulsoup4`。
