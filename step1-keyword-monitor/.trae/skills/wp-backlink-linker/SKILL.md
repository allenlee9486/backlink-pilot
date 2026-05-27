---
name: "wp-backlink-linker"
description: "自动化在 WordPress 博客评论区发布外链。支持 AI 走心评论与锚文本注入。"
---

# WP Backlink Linker Skill

## 1. Skill 用途 (Purpose)
本 Skill 旨在通过自动化手段在 WordPress (WP) 及 Blogger 站点的评论区发布包含高质量锚文本的外链。通过 AI 生成的相关性评论降低被识别为 Spam 的风险，实现自动化的 SEO 外链建设。

## 2. Skill 内容 (Content)
- **核心定义**：负责识别用户需要进行外链建设的意图，并根据提供的 URL 列表执行自动评论。
- **触发条件**：用户提供博客链接列表并要求“发外链”、“自动评论”或“推广网站”时。
- **角色定义**：SEO 专家 & 自动化营销专家。
- **核心工作流**：
    1.  解析目标 URL，判断站点类型。
    2.  读取文章内容，调用 AI 生成定制化评论。
    3.  自动处理登录逻辑（优先谷歌登录）。
    4.  执行表单填充与外链注入（Website 字段 + 评论锚文本）。
    5.  记录发布结果，执行域名去重。

## 3. 交付要求 (Delivery Requirements)
- 每次任务完成后必须输出详细的 JSON 报告，包含成功、失败及跳过的链接。
- 评论内容必须包含 `<a href="...">` 形式的 HTML 锚文本。
- 必须确保同一个域名不重复发布。

## 4. 禁用事项与规则 (Prohibitions)
- **禁止**：直接发送无实际意义的硬广内容。
- **禁止**：在高频验证码拦截的站点进行暴力尝试。
- **规则**：两次评论之间必须有至少 30-60 秒的随机间隔。

## 5. 目录引导
- **参考规范**：见 [References/Standard.md](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/wp-backlink-linker/References/Standard.md)
- **物料资源**：见 [Assets/Templates.json](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/wp-backlink-linker/Assets/Templates.json)
- **自动化脚本**：见 [Scripts/linker.py](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/extracted_skills/wp-backlink-linker/Scripts/linker.py)
