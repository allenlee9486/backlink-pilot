# Indie Hacker SEO SOP (标准作业程序)

这是一个完整的独立开发 SEO 自动化工作流，分为四个核心阶段：

## 📂 目录结构

### [Step 1: 监控新词 (Keyword Monitoring)](./step1-keyword-monitor/)
- **用途**：实时监控行业热词、竞争对手动向及蓝海关键词。
- **状态**：待导入。

### [Step 2: 自动化建站 (Site Builder)](./step2-site-builder/)
- **用途**：根据关键词自动生成 SEO 友好的内容或专题页面。
- **状态**：待完成。

### [Step 3: 自动化部署 (Deployment)](./step3-deployment/)
- **用途**：一键将生成的站点部署到 Vercel/Netlify/Cloudflare Pages。
- **状态**：待完成。

### [Step 4: 自动化发外链 (Backlink Pilot)](./step4-backlink-pilot/)
- **用途**：将部署好的站点提交到 250+ 目录站、Awesome 列表及博客评论区。
- **状态**：**已就绪**。

---

## 🚀 快速开始 (Step 4)

目前发外链流程已完全就绪，运行方法：

```powershell
# 1. 进入对应流程目录
cd step4-backlink-pilot

# 2. 启动浏览器连接
bb-browser open about:blank

# 3. 运行提交脚本
node src/batch-submit.js --limit 5 --engine bb
```

---
*注：本 SOP 旨在实现从发现机会到获取流量的全自动化。*
