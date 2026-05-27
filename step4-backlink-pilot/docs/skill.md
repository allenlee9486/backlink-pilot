---
name: backlink-pilot
description: 自动化外链提交工具，支持目录站、Awesome 列表、搜索引擎和博客评论批量提交。
disable-auto-invoke: true
---

# Backlink Pilot Skills

一个为独立开发者设计的自动化外链建设工具集。配置一次产品信息，即可多渠道分发。

## 1. 快速安装 (Setup)

在一个干净的目录下，运行以下步骤：

```bash
# 1. 克隆并安装依赖
git clone https://github.com/s87343472/backlink-pilot.git
cd backlink-pilot
npm install

# 2. 安装浏览器引擎 (推荐使用 bb-browser)
npm install -g bb-browser
npx playwright install chromium

# 3. 初始化配置
cp config.example.yaml config.yaml
```

## 2. 核心配置 (Configuration)

编辑 `config.yaml` 填入你的网站信息：
- **product**: 名称、URL、描述、分类等。
- **browser.engine**: 设置为 `bb` 以连接本地已登录的 Chrome 浏览器（绕过验证码和登录的关键）。

## 3. 运行指南 (How to Run)

### A. 批量博客评论外链 (最快获取外链)
```bash
# 确保已启动 bb-browser (如果使用 engine: bb)
bb-browser open about:blank

# 执行批量提交 (建议 limit 设置为 5-10 以防封禁)
node src/batch-submit.js --limit 5 --engine bb
```

### B. 提交到特定目录站
```bash
# 提交到 targets.yaml 中收录的站点
node src/cli.js submit futuretools --engine bb

# 提交到任意 URL (使用通用适配器)
node src/cli.js submit https://example.com/submit --engine bb
```

### C. 搜索引擎收录 (IndexNow)
```bash
node src/cli.js indexnow https://your-site.com/new-page
```

### D. 查看状态
```bash
node src/cli.js status
```

## 4. 关键注意事项 (Constraints & Tips)

- **Windows 兼容性**: 本项目已优化 Windows 环境，请确保使用 `bb-browser.cmd` 或在脚本中保持 `engine: bb` 配置。
- **浏览器状态**: 使用 `engine: bb` 时，必须保持由 `bb-browser` 打开的 Chrome 窗口处于开启状态。
- **验证码处理**: 如果程序卡在验证码，直接在打开的 Chrome 窗口中手动点击，程序会自动检测并继续。
- **避免惩罚**: 每天提交数量建议控制在 5-10 个，不同站点间隔 1-3 分钟。
- **Base64 编码**: 内部逻辑已支持 Base64 编码传输 JS，解决了 Windows 命令行引号冲突问题。
