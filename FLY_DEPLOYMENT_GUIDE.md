# Fly.io部署指南 - Discord积分机器人

本指南将帮助你将Discord积分机器人部署到Fly.io实现24/7在线运行。

## 更新内容 (2025-07-22)
- ✅ 移除SendGrid依赖，简化部署
- ✅ 优化内存配置 (1GB)
- ✅ 添加持久化存储卷
- ✅ 斜杠命令系统完全正常工作

## 前置要求

1. **Fly.io账户** - 在 https://fly.io 注册
2. **Fly CLI工具** - 安装 flyctl
3. **Discord Bot Token** - 从Discord开发者门户获取

## 部署步骤

### 1. 安装Fly CLI
```bash
# Windows
iwr https://fly.io/install.ps1 -useb | iex

# macOS/Linux
curl -L https://fly.io/install.sh | sh
```

### 2. 登录Fly.io
```bash
fly auth login
```

### 3. 准备项目文件
确保以下文件已准备：
- `bot.py` - 主机器人程序
- `fly.toml` - Fly.io配置（已优化）
- `Dockerfile` - Docker配置
- `deploy_requirements.txt` - 依赖列表（已移除sendgrid）

### 4. 创建Fly应用
```bash
fly apps create discord-points-bot
```

### 5. 创建持久化存储卷
```bash
fly volumes create discord_bot_data --region sjc --size 1
```

### 6. 设置环境变量
```bash
fly secrets set BOT_TOKEN="你的_discord_bot_token"
```

### 7. 部署应用
```bash
fly deploy
```

## 配置说明

### fly.toml 优化配置
```toml
app = "discord-points-bot"
primary_region = "sjc"

[env]
  PORT = "5000"
  PYTHONUNBUFFERED = "1"

[http_services]
  internal_port = 5000
  auto_stop_machines = false    # 保持24/7在线
  auto_start_machines = true
  min_machines_running = 1      # 最少1台机器运行
  max_machines_running = 2      # 最多2台机器

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024             # 1GB内存，足够运行机器人

[mount]
  source = "discord_bot_data"   # 持久化存储
  destination = "/data"
```

### 关键优化
- **内存增加到1GB** - 确保机器人稳定运行
- **禁用自动停止** - 保证24/7在线
- **持久化存储** - SQLite数据库不会丢失
- **健康检查** - 自动检测机器人状态

## 监控和维护

### 查看日志
```bash
fly logs
```

### 查看应用状态
```bash
fly status
```

### 重启应用
```bash
fly apps restart discord-points-bot
```

### 扩展资源（如需要）
```bash
fly scale memory 2048    # 增加到2GB内存
fly scale count 2        # 运行2个实例
```

## 成本估算

基本配置（1GB内存，1个实例）：
- 约 $5-10/月
- 包含充足的CPU和网络流量
- 持久化存储额外费用很低

## 故障排除

### 常见问题

1. **机器人离线**
   ```bash
   fly logs --app discord-points-bot
   ```

2. **数据库问题**
   - 检查存储卷是否正确挂载
   - 确认数据库路径 `/data/points.db`

3. **内存不足**
   ```bash
   fly scale memory 2048
   ```

4. **Token错误**
   ```bash
   fly secrets set BOT_TOKEN="新的_token"
   ```

## 功能确认

部署后，机器人应该支持：
- ✅ 7个斜杠命令：/pipihelp, /mypoints, /pointsboard等
- ✅ 网页管理面板 (https://your-app.fly.dev)
- ✅ SQLite数据库持久化
- ✅ 24/7在线运行
- ✅ 简化的邮件提交（无需SendGrid验证）

部署完成后，你的Discord机器人将在Fly.io上24/7运行！