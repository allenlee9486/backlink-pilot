---
name: "social-scout"
description: "监控 YouTube, X, Reddit 等社交信号及自动化发布外链。当需要捕捉早期情绪或进行 SEO 推广时使用。"
---

# Social Signal & Linker Scout

此模块负责捕捉社交媒体上的早期爆火信号，并包含自动化的 WP 外链发布工具。

## 核心脚本
- `src/monitors/social/real_scout.py`: 复刻 Ludusdex 逻辑，综合 YouTube/X/Reddit 信号。
- `src/monitors/social/youtube_scout.py`: 监控特定博主的更新频次。
- `src/monitors/social/wp_linker.py`: 自动化 WordPress 博客评论外链发布。

## 运行方式
```bash
python src/monitors/social/real_scout.py
python src/monitors/social/wp_linker.py
```

## 迁移说明
1. 复制 `src/monitors/social/` 目录。
2. 依赖 `playwright`，需运行 `playwright install chromium`。
3. 确保 Chrome 远程调试端口 9222 已开启（用于 `wp_linker`）。
