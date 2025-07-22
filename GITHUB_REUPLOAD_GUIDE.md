# GitHub重新上传指南

## 当前文件状态

已清理的核心文件：
- `bot.py` - 主机器人程序（斜杠命令系统）
- `database.py` - 数据库管理
- `config.py` - 配置管理  
- `order_processor.py` - 订单处理逻辑
- `pyproject.toml` - 项目依赖（已移除sendgrid）
- `deploy_requirements.txt` - 部署依赖（已清理）
- `fly.toml` - Fly.io配置（已优化）
- `Dockerfile` - Docker配置（已优化）
- `README.md` - 中文项目说明
- `.env.example` - 环境变量模板
- `.gitignore` - Git忽略文件
- `FLY_DEPLOYMENT_GUIDE.md` - 完整部署指南

## 上传方法

### 方法1: GitHub网页界面上传（推荐）

1. **创建新仓库**
   - 访问 https://github.com/new
   - 仓库名：`discord-points-bot`
   - 选择 Public 或 Private
   - 不要勾选 "Add a README file"（我们已有）

2. **上传文件**
   - 在空仓库页面，点击 "uploading an existing file"
   - 拖拽以下文件到页面：
     * bot.py
     * database.py
     * config.py
     * order_processor.py
     * pyproject.toml
     * deploy_requirements.txt
     * fly.toml
     * Dockerfile
     * README.md
     * .env.example
     * FLY_DEPLOYMENT_GUIDE.md
     * GITHUB_REUPLOAD_GUIDE.md

3. **提交更改**
   ```
   Commit message: ✨ Discord积分机器人 - 优化版本
   
   描述：
   - 完整的斜杠命令系统 (/pipihelp, /mypoints, /pointsboard等)
   - 移除SendGrid依赖，简化邮件处理
   - 优化Fly.io部署配置（1GB内存，持久化存储）
   - 24/7在线运行配置
   - 网页管理面板
   - SQLite数据库持久化
   ```

### 方法2: Git命令行

如果你熟悉Git命令：
```bash
# 在本地项目目录
git init
git add .
git commit -m "✨ Discord积分机器人 - 优化版本"
git branch -M main
git remote add origin https://github.com/你的用户名/discord-points-bot.git
git push -u origin main
```

## 部署到Fly.io

上传到GitHub后，可以直接部署：

```bash
# 克隆你的仓库
git clone https://github.com/你的用户名/discord-points-bot.git
cd discord-points-bot

# 登录Fly.io
fly auth login

# 创建应用
fly apps create discord-points-bot

# 创建持久化存储
fly volumes create discord_bot_data --region sjc --size 1

# 设置机器人Token
fly secrets set BOT_TOKEN="你的Discord机器人token"

# 部署
fly deploy
```

## 功能确认

✅ 7个斜杠命令正常工作
✅ 网页管理面板（端口5000）
✅ SQLite数据库持久化
✅ 无SendGrid依赖
✅ Fly.io 24/7部署就绪

代码已经完全清理并优化，可以直接上传使用！