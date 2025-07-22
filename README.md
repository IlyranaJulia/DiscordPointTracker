# Discord Points Bot

一个强大的Discord积分管理机器人，支持现代斜杠命令和网页管理面板。

## 功能特点

- 🔗 **现代斜杠命令系统** - 完全支持Discord最新的斜杠命令接口
- 📊 **积分管理系统** - 完整的用户积分跟踪和管理
- 🏆 **排行榜功能** - 实时显示用户积分排名
- 📧 **邮件提交系统** - 简化的邮件提交流程，无需用户验证
- 🎛️ **网页管理面板** - 管理员可通过网页界面管理积分
- 💾 **SQLite数据库** - 轻量级持久化数据存储

## 斜杠命令

- `/pipihelp` - 显示所有可用命令
- `/mypoints` - 查看自己的积分
- `/pointsboard` - 查看积分排行榜
- `/submitemail` - 提交订单邮箱地址
- `/updateemail` - 更新已提交的邮箱
- `/myemail` - 查看邮箱提交状态
- `/status` - 查看机器人状态（管理员）

## 快速开始

1. 克隆仓库
```bash
git clone <repository-url>
cd discord-points-bot
```

2. 安装依赖
```bash
pip install discord.py aiosqlite flask python-dotenv
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 BOT_TOKEN
```

4. 运行机器人
```bash
python bot.py
```

## 部署

支持多种部署方式：

- **Fly.io部署** - 参考 `FLY_DEPLOYMENT_GUIDE.md`
- **Docker部署** - 使用提供的 `Dockerfile`
- **本地运行** - 直接运行 `python bot.py`

## 技术架构

- **Python 3.11+**
- **discord.py 2.5+** - Discord API库
- **aiosqlite** - 异步SQLite数据库
- **Flask** - 网页管理面板
- **python-dotenv** - 环境变量管理

## 文件结构

```
├── bot.py                  # 主机器人文件
├── database.py            # 数据库管理
├── config.py              # 配置管理
├── order_processor.py     # 订单处理逻辑
├── pyproject.toml         # 项目依赖
├── fly.toml              # Fly.io配置
├── Dockerfile            # Docker配置
└── README.md             # 项目说明
```

## 许可证

MIT License# DiscordPointTracker
